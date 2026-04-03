import cv2
import time
import sys
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

# Добавляем родительскую директорию в путь, чтобы видеть camera.py и config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from camera import CameraHandler
from config import CAMERA_CROP_FACTOR

# Временный обработчик для стриминга MJPEG
class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            
            try:
                while True:
                    # Захватываем кадр (без кропа для удобства настройки)
                    frame = camera.capture_frame()
                    if frame is None:
                        continue
                        
                    # Кодируем в JPG
                    _, encoded_image = cv2.imencode('.jpg', frame)
                    
                    # Отправляем кадр как часть MJPEG потока
                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', len(encoded_image))
                    self.end_headers()
                    self.wfile.write(encoded_image.tobytes())
                    self.wfile.write(b'\r\n')
            except Exception as e:
                print(f"Стрим остановлен: {e}")
        else:
            self.send_error(404)

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Позволяет серверу обрабатывать несколько соединений одновременно."""
    pass

if __name__ == '__main__':
    print("🚀 Запуск видео-стрима для настройки камеры...")
    camera = CameraHandler()
    
    # Для настройки камеры лучше видеть полную картинку без кропа
    # Временно переопределим кроп
    from config import CAMERA_CROP_FACTOR
    camera._crop_center = lambda x: x # Отключаем кроп для стрима
    
    server = ThreadedHTTPServer(('0.0.0.0', 8000), StreamingHandler)
    print(f"✅ Стрим доступен по адресу: http://192.168.100.191:8000/")
    print("Нажми Ctrl+C, чтобы остановить.")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        camera.release()
