import os
import json
import sys
from schemas import ObjectDetection, WasteClassification
from models import LlamaProcessor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_json_output():
    # Initialize processor
    processor = LlamaProcessor()
    
    # Path to test image
    image_path = "assets/image.png"
    
    if not os.path.exists(image_path):
        print(f"❌ Error: {image_path} not found!")
        return

    print(f"🔍 Analyzing {image_path} with JSON grammar...")
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    
    try:
        # Detect object using structured class
        result = processor.detect_object(image_bytes, WasteClassification)
        
        print("\n✅ Success! Structured result:")
        print(f"Item: {result.item_name}")
        print(f"Material: {result.material}")
        print(f"Category: {result.category}")
        print(f"Description: {result.description}")
        
        # Also print as raw JSON
        print(f"\nRaw JSON: {result.model_dump_json(indent=2)}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    test_json_output()
