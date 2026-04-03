import os
import json
import uuid
from datetime import datetime
from models import LlamaProcessor
from schemas import WasteClassification

# Ensure directories exist
os.makedirs("assets", exist_ok=True)
os.makedirs("scans", exist_ok=True)

def run_automated_scan(image_source_path):
    """
    Runs a scan on an existing image, moves it to assets with a UUID,
    and records the structured AI result.
    """
    print(f"🚀 Processing: {image_source_path}")
    
    if not os.path.exists(image_source_path):
        print(f"❌ Error: {image_source_path} not found.")
        return

    # 1. Prepare UUID and Paths
    scan_id = str(uuid.uuid4())
    target_image_path = f"assets/{scan_id}.jpg"
    
    # Read image
    with open(image_source_path, "rb") as f:
        image_bytes = f.read()
    
    # Save a copy to assets
    with open(target_image_path, "wb") as f:
        f.write(image_bytes)

    # 2. Initialize Model
    processor = LlamaProcessor()

    # 3. Analyze
    print("🔍 AI Analysis in progress...")
    try:
        result = processor.detect_object(image_bytes, WasteClassification)
        
        # 4. Save metadata
        scan_data = {
            "id": scan_id,
            "timestamp": datetime.now().isoformat(),
            "image": target_image_path,
            "result": result.model_dump()
        }
        
        json_path = f"scans/{scan_id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(scan_data, f, indent=4, ensure_ascii=False)
            
        print(f"✅ Success! ID: {scan_id}")
        print(f"📸 Image archived: {target_image_path}")
        print(f"📄 Result saved: {json_path}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    import sys
    
    # Priority 1: Command line argument (python run_scan.py image.jpg)
    if len(sys.argv) > 1:
        target_image = sys.argv[1]
    else:
        # Priority 2: Look in root, then in assets/
        potential_files = ["last_scan.jpg", "assets/last_scan.jpg", "assets/image.png"]
        target_image = None
        for f in potential_files:
            if os.path.exists(f):
                target_image = f
                break
    
    if target_image and os.path.exists(target_image):
        run_automated_scan(target_image)
    else:
        print("❌ Error: No valid image found to scan.")
        print("💡 Usage: python run_scan.py <path_to_image>")
