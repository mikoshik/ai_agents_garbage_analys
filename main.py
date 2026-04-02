import cv2
import time
import subprocess
import os

# --- КОНФИГУРАЦИЯ ---
MODEL_PATH = "moondream2-q4_k.gguf"
MMPROJ_PATH = "moondream2-mmproj-f16.gguf"
LLAMA_CLI = "./llama.cpp/build/bin/llava-cli"
TEMP_IMAGE = "current_waste.jpg"

# Пути к видео-анимациям (снимите свои или используйте заглушки)
ANIMATIONS = {
    "plastic": "animations/plastic.mp4",
    "organic": "animations/organic.mp4",
    "battery": "animations/battery.mp4",
    "unknown": "animations/error.mp4"
}

def play_animation(category):
    """
    Запускает анимацию с помощью ffplay во весь экран.
    Если файла нет, просто пишет текст.
    """
    video_path = ANIMATIONS.get(category, ANIMATIONS["unknown"])
    print(f"🎬 Воспроизвожу анимацию для: {category}")
    
    if os.path.exists(video_path):
        # -fs: полноэкранный режим, -autoexit: закрыть окно после окончания
        subprocess.Popen(["ffplay", "-fs", "-autoexit", "-nodisp", video_path])
    else:
        print(f"⚠️ Файл {video_path} не найден! Вывод на экран...")
        # Если нет видео, можно вывести картинку или текст поверх OpenCV окна

def analyze_image(image_path):
    """
    Вызов нейросети moondream2 через llama.cpp (llava-cli)
    """
    print("🧠 Анализ изображения...")
    prompt = "Analyze the object being held in the hand. Describe its material, color, and shape in detail. Determine whether it is plastic, organic, or battery waste, and explain why. Be thorough in your description."
    
    # -c 2048: контекстное окно, --temp: температура для точности
    cmd = [
        LLAMA_CLI,
        "-m", MODEL_PATH,
        "--mmproj", MMPROJ_PATH,
        "--image", image_path,
        "-p", prompt,
        "-c", "2048",
        "--temp", "0.1"
    ]
    
    try:
        # Запускаем и перехватываем вывод
        result = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8').strip().lower()
        print(f"🤖 Нейросеть ответила: {result}")
        
        # Простая фильтрация результата
        if "plastic" in result: return "plastic"
        if "organic" in result: return "organic"
        if "battery" in result: return "battery"
        return "unknown"
    except Exception as e:
        print(f"❌ Ошибка вызова llama.cpp: {e}")
        return "unknown"

def main():
    # Создаем папку для анимаций, если её нет
    if not os.path.exists("animations"):
        os.makedirs("animations")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Камера не найдена!")
        return

    # Подготовка детектора движения
    fgbg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=60, detectShadows=True)
    
    is_motion = False
    last_motion_time = time.time()
    wait_after_motion = 3.0 # Ждем 3 сек покоя перед анализом

    print("🛰️ Система СОРТИРОВЩИК запущена. Жду движения у камеры...")

    while True:
        ret, frame = cap.read()
        if not ret: break

        # 1. Анализируем маску движения
        fgmask = fgbg.apply(frame)
        motion_pixels = cv2.countNonZero(fgmask)

        # Порог срабатывания (подберите под освещение)
        if motion_pixels > 6000:
            is_motion = True
            last_motion_time = time.time()
            cv2.putText(frame, "MOTION DETECTED", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # 2. Если движение прекратилось — запускаем нейросеть
        if is_motion and (time.time() - last_motion_time > wait_after_motion):
            print("🚀 Объект неподвижен. Делаем снимок и анализируем!")
            cv2.imwrite(TEMP_IMAGE, frame)
            
            category = analyze_image(TEMP_IMAGE)
            play_animation(category)
            
            # Сброс и задержка, чтобы пользователь успел убрать мусор
            is_motion = False
            time.sleep(7)
            print("\n🔄 Жду следующий объект...")

        # Отображение (для отладки)
        cv2.imshow('Sorter Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
