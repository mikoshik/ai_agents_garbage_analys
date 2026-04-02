import base64
import os
from llama_cpp import Llama
from llama_cpp.llama_chat_format import MoondreamChatHandler

class LlamaProcessor:
    """
    Класс-обертка для llama.cpp, работающий с мультимодальной моделью moondream2.
    Принимает байты изображения и возвращает текстовое описание/категорию.
    """
    def __init__(self, model_path="moondream2-q4_k.gguf", mmproj_path="moondream2-mmproj-f16.gguf"):
        # Проверка наличия файлов моделей
        if not os.path.exists(model_path) or not os.path.exists(mmproj_path):
            print(f"⚠️ Внимание: Файлы моделей не найдены! Ожидались {model_path} и {mmproj_path}")
        
        # Специальный ChatHandler для Moondream2 (важно!)
        self.chat_handler = MoondreamChatHandler(clip_model_path=mmproj_path)
        
        # Инициализация модели. 
        # n_threads=4 идеален для Raspberry Pi 4.
        # n_ctx=2048 достаточно для анализа фото.
        self.llm = Llama(
            model_path=model_path,
            chat_handler=self.chat_handler,
            n_ctx=2048,
            n_threads=4,
            logits_all=False
        )

    def process_image(self, image_data: bytes, prompt: str = "Describe the object held in the person's hand with as much detail as possible. Identify its physical characteristics: material (plastic, metal, organic, glass, etc.), color, shape, texture, and any visible text or branding. Finally, classify what type of waste this is (plastic, organic, battery, or other) and explain your reasoning.") -> str:
        """
        Принимает байты изображения, конвертирует в Data URI и прогоняет через нейросеть.
        """
        try:
            # Конвертация байтов в base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            image_uri = f"data:image/jpeg;base64,{base64_image}"

            # Формируем запрос для Moondream2/Llava
            response = self.llm.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": image_uri}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                temperature=0.1, # Для стабильности ответа при категоризации
                max_tokens=512   # Ограничение по длине ответа
            )

            result_text = response["choices"][0]["message"]["content"].strip().lower()
            return result_text
            
        except Exception as e:
            return f"Error processing image: {str(e)}"

# Пример использования (закомментировано)
# if __name__ == "__main__":
#     processor = LlamaProcessor()
#     with open("test.jpg", "rb") as f:
#         print(processor.process_image(f.read()))
