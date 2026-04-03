import sys
import time
import threading
import os, cv2
from camera import CameraHandler
from models import LlamaProcessor
from config import *

def progress_bar(stop_event, expected_time=600):
    """
    Beautiful progress bar that runs while the model is processing.
    Fills up to 99% based on 'expected_time', and jumps to 100% when stop_event is set.
    """
    start_time = time.time()
    bar_length = 50
    
    # Animation frames for the spinner
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    idx = 0
    
    print("\n   🧠 AI is thinking...")
    
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        progress = min(elapsed / expected_time, 0.99)
        
        filled = int(progress * bar_length)
        # Use smooth block characters for better aesthetics
        bar = "█" * filled + "░" * (bar_length - filled)
        
        percent = int(progress * 100)
        s = spinner[idx % len(spinner)]
        idx += 1
        
        # ANSI Escape codes for colors: \033[94m is light blue, \033[0m is reset
        sys.stdout.write(f"\r   {s}  \033[94m[{bar}]\033[0m {percent}% | Elapsed: {int(elapsed)}s ")
        sys.stdout.flush()
        time.sleep(0.1)
    
    # Final state when processing is done
    total_time = int(time.time() - start_time)
    sys.stdout.write(f"\r   ✨ \033[92m[{'█' * bar_length}]\033[0m 100% | Total time: {total_time}s         \n")
    sys.stdout.flush()

def frame_to_ascii(frame, width=100):
    """
    Converts a frame to ASCII art string with normalization for brightness.
    """
    # Resize for terminal
    height = int(frame.shape[0] * (width / frame.shape[1]) * 0.4)
    resized_frame = cv2.resize(frame, (width, height))
    
    # Gray scale
    gray = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
     
    # Normalize brightness to see something even in low light
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    
    chars = [" ", ".", ":", "-", "=", "+", "*", "#", "%", "@"]
    ascii_str = ""
    for row in gray:
        for pixel in row:
            # Fix overflow by using int() explicitly
            idx = int(int(pixel) * (len(chars) - 1) // 255)
            ascii_str += chars[idx]
        ascii_str += "\n"
    return ascii_str

def main():
    # Clear screen for better start
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("\033[1;96m")
    print("="*60)
    print("        🌿 ECO-AGENT: AI WASTE CLASSIFICATION 🌿")
    print("="*60)
    print("\033[0m")
    
    try:
        print("🔗 Initializing hardware sensors...")
        camera = CameraHandler()
        
        print("🧬 Loading Moondream2 Vision Model (this may take 30-60s)...")
        model = LlamaProcessor()
        
        print("\033[92m✅ All systems online. Ready for scan.\033[0m")
        
        while True:
            print("\n" + "="*60)
            print("📸 Press \033[1m[ENTER]\033[0m to capture | \033[1m[q + ENTER]\033[0m to exit")
            
            cmd = input().strip().lower()
            if cmd == 'q':
                break
                
            # Countdown before capture
            for i in range(2, 0, -1):
                sys.stdout.write(f"\r📸 Get ready! Capturing in {i}... ")
                sys.stdout.flush()
                time.sleep(1)
            print("\r📸 CLICK!                      ")

            # 1. Capture Image
            # Capture raw frame to show preview before sending
            frame = camera.capture_frame()
            if frame is None:
                print("❌ Error: Camera capture failed.")
                continue
            
            # Show ASCII Preview
            print("\n--- CAPTURED AREA PREVIEW (CROPPED) ---")
            print(frame_to_ascii(frame, width=60))
            print("---------------------------------------")

            image_bytes = camera.capture_to_bytes()
            if image_bytes is None:
                print("❌ Error: Converting image to bytes failed.")
                continue

            # Save for debugging
            with open("last_scan.jpg", "wb") as f:
                f.write(image_bytes)

            # 2. Start Model Processing with Progress Tracking
            stop_event = threading.Event()
            result_container = {"text": "Processing failed."}
            
            def model_task():
                try:
                    response = model.process_image(image_bytes)
                    result_container["text"] = response
                finally:
                    stop_event.set()
            
            bar_thread = threading.Thread(target=progress_bar, args=(stop_event, 600))
            task_thread = threading.Thread(target=model_task)
            
            bar_thread.start()
            task_thread.start()
            
            task_thread.join()
            stop_event.set()
            bar_thread.join()
            
            # 3. Display Results in a stylized box
            result = result_container["text"]
            print("\n" + "╔" + "═"*58 + "╗")
            print("║" + " " * 23 + "🔍 AI ANALYSIS" + " " * 21 + "║")
            print("╠" + "═"*58 + "╣")
            
            import textwrap
            wrapped = textwrap.fill(result, width=54)
            for line in wrapped.split('\n'):
                print(f"║  {line.ljust(54)}  ║")
                
            print("╚" + "═"*58 + "╝\n")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down Eco-Agent...")
    except Exception as e:
        print(f"\n🔥 Critical System Failure: {e}")
    finally:
        print("♻️ Releasing hardware resources...")
        # Resources are released by __del__ in CameraHandler if needed

if __name__ == "__main__":
    main()
