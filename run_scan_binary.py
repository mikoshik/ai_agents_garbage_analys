import os
import json
import uuid
import time
from datetime import datetime
from models import LlamaProcessor
from schemas import WasteClassification

# Ensure directories exist
os.makedirs("assets", exist_ok=True)
os.makedirs("scans", exist_ok=True)

def run_automated_scan_binary(image_bytes: bytes):
    """
    Runs a scan on image bytes, saves it to assets with a UUID,
    and records the structured AI result.
    """
    # 1. Prepare UUID and Paths
    scan_id = str(uuid.uuid4())
    target_image_path = f"assets/{scan_id}.jpg"
    
    print(f"🚀 Processing new binary image, saving to: {target_image_path}")

    # Save a copy to assets
    with open(target_image_path, "wb") as f:
        f.write(image_bytes)

    # 2. Initialize Model
    import psutil
    mem_start = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    processor = LlamaProcessor()

    # 3. Analyze
    print("🔍 AI Analysis in progress...")
    time_start = time.time()
    try:
        result = processor.detect_object(image_bytes, WasteClassification)
        time_elapsed = time.time() - time_start
        mem_end = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        
        # 4. Save metadata
        scan_data = {
            "id": scan_id,
            "timestamp": datetime.now().isoformat(),
            "image": target_image_path,
            "metadata": {
                "time_sec": round(time_elapsed, 2),
                "memory_mb": round(mem_end, 2),
                "memory_delta_mb": round(max(0, mem_end - mem_start), 2)
            },
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
