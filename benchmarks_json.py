import os
import time
import psutil
from models import LlamaProcessor
from schemas import WasteClassification

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024) # MB

def run_benchmark():
    print("📊 STARTING BENCHMARKS: TEXT vs JSON/GRAMMAR\n")
    
    # Init processor
    processor = LlamaProcessor()
    
    image_path = "assets/image.png"
    if not os.path.exists(image_path):
        # Fallback to last_scan.jpg
        image_path = "last_scan.jpg"
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    print(f"Memory base: {get_memory_usage():.2f} MB")

    # TEST 1: Plain Text (Standard)
    print("\n--- TEST 1: Plain Text Prompt (Traditional) ---")
    start_time = time.time()
    res1 = processor.process_image(image_bytes, "Describe what is in this image briefly.")
    end_time = time.time()
    mem1 = get_memory_usage()
    print(f"Time: {end_time - start_time:.2f}s")
    print(f"Memory: {mem1:.2f} MB")
    print(f"Result: {res1[:50]}...")

    # TEST 2: Structured JSON (With Grammar)
    print("\n--- TEST 2: Structured JSON (With Pydantic & Grammar) ---")
    start_time = time.time()
    res2 = processor.detect_object(image_bytes, WasteClassification)
    end_time = time.time()
    mem2 = get_memory_usage()
    print(f"Time: {end_time - start_time:.2f}s")
    print(f"Memory: {mem2:.2f} MB")
    print(f"Result (Object Name): {res2.item_name}")

    # TEST 3: Pure Text Repair (Simulated)
    print("\n--- TEST 3: Text-only 'Repair' Pass (No Image Re-encoding) ---")
    start_time = time.time()
    # We call low level completion to simulate repair pass time
    # This is what happens if pydantic validation fails
    schema = WasteClassification.model_json_schema()
    from llama_cpp import LlamaGrammar
    import json
    grammar = LlamaGrammar.from_json_schema(json.dumps(schema))
    
    repair_prompt = f"Fix this JSON string:\n\n{res2.model_dump_json()}\n\nValid JSON:"
    repair_res = processor.llm.create_completion(
        prompt=repair_prompt,
        grammar=grammar,
        max_tokens=200
    )
    end_time = time.time()
    print(f"Repair Time: {end_time - start_time:.2f}s")
    print(f"Memory: {get_memory_usage():.2f} MB")

    print("\n" + "="*40)
    print(f"TEXT-ONLY vs JSON overhead: {mem2 - mem1:.2f} MB")
    print(f"Repair speed boost vs Image pass: {(end_time - start_time) / (end_time - start_time):.2f}x (simulated)")
    print("="*40)

if __name__ == "__main__":
    run_benchmark()
