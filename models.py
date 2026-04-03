import base64
import os
from llama_cpp import Llama
from llama_cpp.llama_chat_format import MoondreamChatHandler
from config import *

class LlamaProcessor:
    """
    Wrapper class for llama.cpp, working with the moondream2 multimodal model.
    Takes image bytes and returns a text description/category.
    """
    def __init__(self, model_path=MODEL_PATH, mmproj_path=MMPROJ_PATH):
        # Check if model files exist
        if not os.path.exists(model_path) or not os.path.exists(mmproj_path):
            print(f"⚠️ Warning: Model files not found! Expected {model_path} and {mmproj_path}")
        
        # Special ChatHandler for Moondream2 (important!)
        self.chat_handler = MoondreamChatHandler(clip_model_path=mmproj_path)
        
        # Initialize model with config parameters
        self.llm = Llama(
            model_path=model_path,
            chat_handler=self.chat_handler,
            n_ctx=LLM_CTX,
            n_threads=LLM_THREADS,
            logits_all=False
        )

    def process_image(self, image_data: bytes, prompt: str = DEFAULT_PROMPT) -> str:
        """
        Takes image bytes, converts to Data URI and processes through the neural network.
        """
        try:
            # Convert bytes to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            image_uri = f"data:image/jpeg;base64,{base64_image}"

            # Form request for Moondream2/Llava
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
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )

            result_text = response["choices"][0]["message"]["content"].strip().lower()
            return result_text
            
        except Exception as e:
            return f"Error processing image: {str(e)}"

# Usage example (commented out)
# if __name__ == "__main__":
#     processor = LlamaProcessor()
#     with open("test.jpg", "rb") as f:
#         print(processor.process_image(f.read()))
