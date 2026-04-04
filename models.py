import base64
import os
import json
import time
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel
from config import *

# Optional imports for local/cloud
try:
    from llama_cpp import Llama, LlamaGrammar
    from llama_cpp.llama_chat_format import MoondreamChatHandler
except ImportError:
    pass

try:
    import openai
except ImportError:
    pass

class LlamaProcessor:
    """
    Processor that handles both local Moondream2 (via llama.cpp) 
    and Cloud GPT-4o-mini (via OpenAI API).
    """
    def __init__(self, model_path=MODEL_PATH, mmproj_path=MMPROJ_PATH):
        self.is_local = (LOCAL_MODEL == 1)
        
        if self.is_local:
            print("🤖 Initializing LOCAL model (Moondream2)...")
            if not os.path.exists(model_path) or not os.path.exists(mmproj_path):
                print(f"⚠️ Warning: Model files not found! Expected {model_path} and {mmproj_path}")
            
            self.chat_handler = MoondreamChatHandler(clip_model_path=mmproj_path)
            self.llm = Llama(
                model_path=model_path,
                chat_handler=self.chat_handler,
                n_ctx=LLM_CTX,
                n_threads=LLM_THREADS,
                logits_all=False,
                verbose=False
            )
        else:
            print(f"☁️ Initializing CLOUD model ({CLOUD_MODEL_NAME})...")
            if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_OPENAI_API_KEY":
                print("❌ ERROR: OpenAI API Key is missing in config.py!")
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def process_image(self, image_data: bytes, prompt: str = DEFAULT_PROMPT, grammar: Optional[Any] = None) -> str:
        """
        Processes image through either local LLM or OpenAI API.
        """
        try:
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            if self.is_local:
                image_uri = f"data:image/jpeg;base64,{base64_image}"
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
                return response["choices"][0]["message"]["content"].strip()
            
            else:
                # OpenAI Cloud Path
                response = self.client.chat.completions.create(
                    model=CLOUD_MODEL_NAME,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                                }
                            ],
                        }
                    ],
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            return f"Error processing image: {str(e)}"

    def detect_object(self, image_data: bytes, pydantic_class: Type[BaseModel], max_retries: int = 3) -> BaseModel:
        """
        Processes image and returns a validated Pydantic object.
        """
        schema = pydantic_class.model_json_schema()
        
        if self.is_local:
            from llama_cpp import LlamaGrammar
            grammar = LlamaGrammar.from_json_schema(json.dumps(schema))
            prompt = f"Identify the object in the image and provide information in JSON format matching this schema: {schema['title']}"
            response_text = self.process_image(image_data, prompt=prompt, grammar=grammar)
        else:
            # Cloud path uses 'json_object' response format or just clear instructions
            prompt = (
                f"Identify the object in the image and provide information in JSON format strictly matching this schema: {json.dumps(schema)}\n"
                "Return valid JSON only."
            )
            # OpenAI structured output is better, but for simplicity we use json_mode
            try:
                base64_image = base64.b64encode(image_data).decode('utf-8')
                response = self.client.beta.chat.completions.parse(
                    model=CLOUD_MODEL_NAME,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ],
                        }
                    ],
                    response_format=pydantic_class,
                )
                return response.choices[0].message.parsed
            except Exception as e:
                # Fallback to manual parsing if .parse() fails or older API
                print(f"⚠️ Cloud parse failed, trying manual: {e}")
                response_text = self.process_image(image_data, prompt=prompt)

        # Fallback manual parsing (used for Local or if Cloud parse fails)
        for attempt in range(max_retries + 1):
            try:
                # Clean response text from markdown code blocks if any
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                data = json.loads(response_text)
                return pydantic_class.model_validate(data)
            except Exception as e:
                if attempt < max_retries:
                    print(f"⚠️ Validation failed (Attempt {attempt+1}): {e}. Retrying...")
                    time.sleep(1)
                    # Re-ask if it's cloud, or just retry if local
                    if not self.is_local:
                        response_text = self.process_image(image_data, prompt=prompt + f"\nFix this error: {e}")
                else:
                    raise e

# Usage example (commented out)
# if __name__ == "__main__":
#     processor = LlamaProcessor()
#     with open("test.jpg", "rb") as f:
#         print(processor.process_image(f.read()))
