import cv2
import time
import os
import numpy as np
from camera import CameraHandler

def test_take_photo():
    """
    Test capturing a photo and saving it to disk.
    """
    print("\n--- Testing: Photo Capture ---")
    handler = CameraHandler()
    filename = "test_photo.jpg"
    
    if handler.capture_to_file(filename):
        if os.path.exists(filename):
            print(f"✅ Success! Photo saved at {filename} ({os.path.getsize(filename)} bytes)")
        else:
            print("❌ Error: capture_to_file returned True but file does not exist.")
    else:
        print("❌ Error: capture_to_file failed.")
    
    handler.release()

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

def test_terminal_stream(duration=10):
    """
    Test streaming camera output to terminal using ASCII art.
    """
    print("\n--- Testing: Terminal ASCII Stream ---")
    print(f"Starting ASCII stream for {duration} seconds...")
    print("Press Ctrl+C to stop.")
    time.sleep(1.5)
    
    handler = CameraHandler()
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            frame = handler.capture_frame()
            if frame is not None:
                ascii_art = frame_to_ascii(frame)
                # Clear terminal: Use \033[2J to clear plus \033[H to home
                print("\033[2J\033[H", end="")
                print(ascii_art)
                print(f"Time: {int(time.time() - start_time)}s / {duration}s | Camera: OK")
                time.sleep(0.05)
            else:
                print("\r⚠️  Frame dropped...", end="")
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        handler.release()
        print("\n--- ASCII Stream Finished ---")

if __name__ == "__main__":
    print("Camera Testing Tool")
    print("1. Take a test photo")
    print("2. Run terminal ASCII stream (5 sec)")
    print("3. Both")
    
    choice = input("Select an option (1/2/3): ")
    
    if choice == '1':
        test_take_photo()
    elif choice == '2':
        test_terminal_stream()
    elif choice == '3':
        test_take_photo()
        test_terminal_stream()
    else:
        print("Invalid choice.")
