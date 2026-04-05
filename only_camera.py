import sys
import time
import os
import cv2
import urllib.request
import urllib.error
from camera import CameraHandler

# Server URL - can be overridden via command-line argument
SERVER_URL = "http://localhost:8060/api/upload"

def frame_to_ascii(frame, width=100):
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

def main():
    target_url = sys.argv[1] if len(sys.argv) > 1 else SERVER_URL
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\033[1;96m" + "="*60 + f"\n        🌿 ECO-AGENT: CAMERA CLIENT 🌿\n        Server endpoint: {target_url}\n" + "="*60 + "\033[0m")
    
    try:
        print("🔗 Initializing sensors...")
        camera = CameraHandler()
        print("\033[92m✅ Online. Ready to capture and send.\033[0m")
        
        while True:
            print("\n" + "="*60)
            print("📸 Press [ENTER] to capture | [q + ENTER] to exit")
            if input().strip().lower() == 'q': break
                
            # 1. Capture Image
            frame = camera.capture_frame()
            if frame is None: 
                print("❌ Failed to capture frame.")
                continue
            
            print("\n--- CAPTURED AREA PREVIEW ---")
            print(frame_to_ascii(frame, width=60))
            
            image_bytes = camera.capture_to_bytes()
            if not image_bytes: 
                print("❌ Failed to encode frame.")
                continue

            # 2. Upload to server
            print(f"📤 Uploading image to {target_url}...")
            
            req = urllib.request.Request(target_url, data=image_bytes, headers={'Content-Type': 'image/jpeg'}, method='POST')
            try:
                time_start = time.time()
                with urllib.request.urlopen(req) as response:
                    response_data = response.read().decode('utf-8')
                    time_elapsed = time.time() - time_start
                    print(f"✅ Image uploaded successfully in {round(time_elapsed, 2)}s!")
                    print(f"   Server response: {response_data}")
            except urllib.error.URLError as e:
                print(f"❌ Connection failed: {e}")
                print("💡 Ensure the server is running and the URL is correct.")
                
    except Exception as e: 
        print(f"\n🔥 Error: {e}")
    finally:
        print("♻️ Releasing resources...")

if __name__ == "__main__":
    main()
