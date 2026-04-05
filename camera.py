import cv2
import time
from config import *

class CameraHandler:
    """
    Class for managing USB camera on Raspberry Pi / PC.
    Handles frame capture and data preparation for the model.
    Uses a background thread to prevent buffer buildup.
    """
    def __init__(self, camera_index=CAMERA_INDEX, width=CAMERA_WIDTH, height=CAMERA_HEIGHT):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None
        
        self.latest_frame = None
        self.is_running = False
        self.thread = None

    def __repr__(self):
        return f"CameraHandler(index={self.camera_index}, resolution={self.width}x{self.height}, fourcc={CAMERA_FOURCC})"

    def _open_camera(self):
        """Internal method to open camera connection and start capture thread."""
        if self.cap is None or not self.cap.isOpened():
            import threading
            # Use CAP_V4L2 backend explicitly
            self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            
            # Use format from config.py
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*CAMERA_FOURCC))
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            # Устанавливаем FPS из конфига
            self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Limit buffer
            
            # Give the camera time to initialize the sensor
            time.sleep(1.0)
            
            if not self.cap.isOpened():
                raise ConnectionError(f"❌ Error: Could not open camera at /dev/video{self.camera_index}")
            
            # Warm-up frames for auto-exposure happen only once when opening
            for _ in range(CAMERA_WARMUP_FRAMES):
                ret, frame = self.cap.read()
                if ret:
                    self.latest_frame = frame
            
            # Start background thread to keep buffer empty and get newest frames instantly
            self.is_running = True
            self.thread = threading.Thread(target=self._update_loop, daemon=True)
            self.thread.start()

    def _update_loop(self):
        """Continuously reads frames to prevent buffer buildup and freezing."""
        while self.is_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.latest_frame = frame
            else:
                time.sleep(0.01)

    def _crop_center(self, frame):
        """Crops the center of the frame based on CAMERA_CROP_FACTOR."""
        h, w = frame.shape[:2]
        new_w = int(w * CAMERA_CROP_FACTOR)
        new_h = int(h * CAMERA_CROP_FACTOR)
        
        start_x = (w - new_w) // 2
        start_y = (h - new_h) // 2
        
        return frame[start_y:start_y+new_h, start_x:start_x+new_w]

    def capture_frame(self):
        """
        Retrieves the latest available frame from the background thread and crops it.
        """
        self._open_camera()
        
        # Wait a tiny bit just in case the thread hasn't grab the first frame yet
        timeout = 2.0
        start_time = time.time()
        while self.latest_frame is None and (time.time() - start_time) < timeout:
            time.sleep(0.05)
            
        if self.latest_frame is None:
            print("⚠️ Error: Frame not captured")
            return None
            
        # Crop to center for better detail
        cropped_frame = self._crop_center(self.latest_frame)
        return cropped_frame

    def capture_to_bytes(self):
        """
        Captures a frame and converts it to bytes with maximum quality.
        """
        frame = self.capture_frame()
        if frame is None:
            return None
            
        # Convert to JPG with maximum quality (100)
        success, encoded_image = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        if not success:
            return None
            
        return encoded_image.tobytes()

    def capture_to_file(self, filename="last_capture.jpg"):
        """Captures a frame and saves it to disk."""
        frame = self.capture_frame()
        if frame is not None:
            cv2.imwrite(filename, frame)
            print(f"📸 Image saved: {filename}")
            return True
        return False

    def release(self):
        """Releases the camera resource and stops the thread."""
        self.is_running = False
        if self.thread is not None:
            self.thread.join(timeout=1.0)
            self.thread = None
            
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __del__(self):
        """Auto-release resources on object deletion."""
        self.release()
