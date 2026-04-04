import sys
import time
import threading
import os, cv2
import uuid
import json
from datetime import datetime
from camera import CameraHandler
from models import LlamaProcessor
from schemas import WasteClassification
from config import *

# Ensure directories exist
os.makedirs("assets", exist_ok=True)
os.makedirs("scans", exist_ok=True)

def progress_bar(stop_event, expected_time=60):
    """
    Beautiful progress bar that runs while the model is processing.
    """
    start_time = time.time()
    bar_length = 50
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    
    print("\n   🧠 AI is thinking (JSON Analysis)...")
    
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        progress = min(elapsed / expected_time, 0.99)
        filled = int(progress * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        percent = int(progress * 100)
        s = spinner[idx % len(spinner)]
        idx += 1
        sys.stdout.write(f"\r   {s}  \033[94m[{bar}]\033[0m {percent}% | Elapsed: {int(elapsed)}s ")
        sys.stdout.flush()
        time.sleep(0.1)
    
    total_time = int(time.time() - start_time)
    sys.stdout.write(f"\r   ✨ \033[92m[{'█' * bar_length}]\033[0m 100% | Total time: {total_time}s         \n")
    sys.stdout.flush()

def frame_to_ascii(frame, width=100):
    # ... (keeps existing frame_to_ascii logic)
    height = int(frame.shape[0] * (width / frame.shape[1]) * 0.4)
    resized_frame = cv2.resize(frame, (width, height))
    gray = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    chars = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"]
    ascii_str = ""
    for row in gray:
        for pixel in row:
            idx = int(int(pixel) * (len(chars) - 1) // 255)
            ascii_str += chars[idx]
        ascii_str += "\n"
    return ascii_str

import multiprocessing
import subprocess

def start_dashboard_server():
    """Starts the dashboard server in a separate process."""
    try:
        # Launch using subprocess to keep it isolated
        subprocess.Popen([sys.executable, "server.py"], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        print("🚀 Dashboard server started automatically at http://localhost:8060")
    except Exception as e:
        print(f"⚠️ Failed to start dashboard server: {e}")

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\033[1;96m" + "="*60 + "\n        🌿 ECO-AGENT: AI WASTE CLASSIFICATION 🌿\n" + "="*60 + "\033[0m")
    
    start_dashboard_server()
    
    try:
        print("🔗 Initializing sensors...")
        camera = CameraHandler()
        print("🧬 Loading Vision Model...")
        model = LlamaProcessor()
        print("\033[92m✅ Online.\033[0m")
        
        while True:
            print("\n" + "="*60)
            print("📸 Press [ENTER] to capture | [q + ENTER] to exit")
            if input().strip().lower() == 'q': break
                
            # 1. Capture Image
            frame = camera.capture_frame()
            if frame is None: continue
            
            print("\n--- CAPTURED AREA PREVIEW ---")
            print(frame_to_ascii(frame, width=60))
            
            image_bytes = camera.capture_to_bytes()
            if not image_bytes: continue

            # 2. Generate UUID and save image
            scan_id = str(uuid.uuid4())
            image_path = f"assets/{scan_id}.jpg"
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            
            # 3. Analyze with detect_object (JSON)
            stop_event = threading.Event()
            result_container = {"data": None, "error": None}
            
            import psutil
            mem_start = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
            time_start = time.time()

            def model_task():
                try:
                    result_container["data"] = model.detect_object(image_bytes, WasteClassification)
                except Exception as e:
                    result_container["error"] = str(e)
                finally:
                    stop_event.set()
            
            threading.Thread(target=progress_bar, args=(stop_event, 40)).start()
            task_thread = threading.Thread(target=model_task)
            task_thread.start()
            task_thread.join()
            
            # 4. Save and Display
            if result_container["data"]:
                res = result_container["data"]
                time_elapsed = time.time() - time_start
                mem_end = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

                # Save results JSON
                scan_data = {
                    "id": scan_id,
                    "timestamp": datetime.now().isoformat(),
                    "image": image_path,
                    "metadata": {
                        "time_sec": round(time_elapsed, 2),
                        "memory_mb": round(mem_end, 2),
                        "memory_delta_mb": round(max(0, mem_end - mem_start), 2)
                    },
                    "result": res.model_dump()
                }
                with open(f"scans/{scan_id}.json", "w") as f:
                    json.dump(scan_data, f, indent=4)
                
                # Stylized box
                print("\n" + "╔" + "═"*58 + "╗")
                print("║" + f"  ID: {scan_id[:8]}...".ljust(56) + "  ║")
                print("╠" + "═"*58 + "╣")
                print(f"║  ITEM: {res.item_name.upper().ljust(52)}  ║")
                print(f"║  MATERIAL: {res.material.ljust(48)}  ║")
                print(f"║  CATEGORY: {res.category.ljust(48)}  ║")
                print("╠" + "═"*58 + "╣")
                import textwrap
                wrapped = textwrap.fill(f"DESC: {res.description}", width=54)
                for line in wrapped.split('\n'):
                    print(f"║  {line.ljust(54)}  ║")
                print("╚" + "═"*58 + "╝\n")
            else:
                print(f"❌ Analysis failed: {result_container['error']}")
                
    except Exception as e: print(f"\n🔥 Error: {e}")
    finally:
        print("♻️ Releasing resources...")

if __name__ == "__main__":
    main()
