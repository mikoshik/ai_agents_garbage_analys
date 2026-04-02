import os
from models import LlamaProcessor

def test_single_image():
    # Путь к изображению в папке animations
    image_path = "animations/image.png"
    
    if not os.path.exists(image_path):
        print(f"❌ Ошибка: Файл {image_path} не найден!")
        return

    print(f"🚀 Загружаем изображение: {image_path}")
    
    # Инициализация процессора (модели подгрузятся из текущей папки)
    try:
        processor = LlamaProcessor()
        
        print("🧠 Анализируем изображение...")
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            
        # Можно передать свой промпт, если нужно
        result = processor.process_image(image_bytes)
        
        print("\n" + "="*30)
        print(f"🤖 ОТВЕТ НЕЙРОСЕТИ: {result}")
        print("="*30)
        
    except Exception as e:
        print(f"❌ Произошла ошибка при инициализации или обработке: {e}")

if __name__ == "__main__":
    test_single_image()
