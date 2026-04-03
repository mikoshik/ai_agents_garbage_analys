import base64
import os
from llama_cpp import Llama, LlamaGrammar
from llama_cpp.llama_chat_format import MoondreamChatHandler
from pydantic import BaseModel
from typing import Optional, Type, Dict, Any
from config import *
import json

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
            logits_all=False,
            verbose=False # Прячем системные логи
        )

    def process_image(self, image_data: bytes, prompt: str = DEFAULT_PROMPT, grammar: Optional[LlamaGrammar] = None) -> str:
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
                max_tokens=MAX_TOKENS,
                grammar=grammar
            )

            result_text = response["choices"][0]["message"]["content"]
            if isinstance(result_text, str):
                result_text = result_text.strip()
            return result_text
            
        except Exception as e:
            return f"Error processing image: {str(e)}"

    def detect_object(self, image_data: bytes, pydantic_class: Type[BaseModel], max_retries: int = 5) -> BaseModel:
        """
        Processes image and returns a validated Pydantic object.
        If initial validation fails, it performs a fast text-only repair attempt.
        """
        schema = pydantic_class.model_json_schema()
        shema_dump = json.dumps(schema)
        grammar = LlamaGrammar.from_json_schema(shema_dump)
        
        # 1. Initial attempt with IMAGE (Slow)
        prompt = f"Identify the object in the image and provide information in JSON format matching this schema: {schema['title']}"
        response_text = self.process_image(image_data, prompt=prompt, grammar=grammar)
        
        for attempt in range(max_retries + 1):
            try:
                data = json.loads(response_text)
                return pydantic_class.model_validate(data)
            except Exception as e:
                if attempt < max_retries:
                    print(f"⚠️ Validation attempt {attempt+1} failed: {e}. Starting FAST REPAIR (text-only)...")
                    
                    # 2. Repair attempt with TEXT ONLY (Fast)
                    # Use chat context for better instruction following
                    repair_messages = [
                        {"role": "system", "content": "You are a JSON correction assistant. You must provide valid JSON strictly following the schema. Do not leave required fields empty."},
                        {"role": "user", "content": f"The previous JSON output for this object was invalid: {response_text}\n\nError: {str(e)}\n\nPlease fix the JSON and provide a detailed description. Schema: {schema['title']}"}
                    ]
                    
                    repair_response = self.llm.create_chat_completion(
                        messages=repair_messages,
                        grammar=grammar,
                        max_tokens=MAX_TOKENS,
                        temperature=0.2
                    )
                    response_text = repair_response["choices"][0]["message"]["content"].strip()
                else:
                    print(f"⚠️ Final attempt failed. Raw output: {response_text}")
                    raise e

# Usage example (commented out)
# if __name__ == "__main__":
#     processor = LlamaProcessor()
#     with open("test.jpg", "rb") as f:
#         print(processor.process_image(f.read()))
