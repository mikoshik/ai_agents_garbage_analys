import cv2
import time
from config import *

class CameraHandler:
    """
    Class for managing USB camera on Raspberry Pi / PC.
    Handles frame capture and data preparation for the model.
    """
    def __init__(self, camera_index=CAMERA_INDEX, width=CAMERA_WIDTH, height=CAMERA_HEIGHT):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None

    def _open_camera(self):
        """Internal method to open camera connection."""
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(self.camera_index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            
            # Give the camera time to initialize the sensor
            time.sleep(1.0)
            
            if not self.cap.isOpened():
                raise ConnectionError(f"❌ Error: Could not open camera at /dev/video{self.camera_index}")

    def capture_frame(self):
        """
        Captures one frame from the camera.
        Returns: numpy array (image) or None.
        """
        self._open_camera()
        
        # Warm-up frames for auto-exposure
        for _ in range(CAMERA_WARMUP_FRAMES):
            self.cap.read()
            
        ret, frame = self.cap.read()
        
        if not ret:
            print("⚠️ Error: Frame not captured")
            return None
            
        return frame

    def capture_to_bytes(self):
        """
        Captures a frame and converts it to bytes (JPG format).
        Convenient for direct passing to LlamaProcessor.
        """
        frame = self.capture_frame()
        if frame is None:
            return None
            
        # Convert to JPG
        success, encoded_image = cv2.imencode('.jpg', frame)
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
        """Releases the camera resource."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def __del__(self):
        """Auto-release resources on object deletion."""
        self.release()
