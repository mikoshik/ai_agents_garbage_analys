import time
import resource
import os
import sys

# Добавляем родительскую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import LlamaProcessor

def get_perf_metrics():
    """Returns current RAM usage (in MB) and CPU time (in sec)."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    ram_mb = usage.ru_maxrss / 1024  # ru_maxrss is in KB on Linux
    cpu_time = usage.ru_utime + usage.ru_stime # User + System time
    return ram_mb, cpu_time

def test_single_image():
    # Путь к изображению в папке animations
    image_path = "animations/image.png"
    
    if not os.path.exists(image_path):
        print(f"❌ Error: File {image_path} not found!")
        return

    print(f"🚀 Loading image: {image_path}")
    
    try:
        # 1. Record start metrics
        start_time = time.perf_counter()
        ram_start, cpu_start = get_perf_metrics()
        
        print("🧠 Initializing model...")
        processor = LlamaProcessor()
        
        print("📸 Analyzing image...")
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            
        result = processor.process_image(image_bytes)
        
        # 2. Record finish metrics
        end_time = time.perf_counter()
        ram_end, cpu_end = get_perf_metrics()
        
        duration = end_time - start_time
        cpu_usage_total = cpu_end - cpu_start
        # Calculate threads and load
        num_threads = processor.llm.n_threads
        avg_cpu_load = (cpu_usage_total / duration) * 100 if duration > 0 else 0
        
        print("\n" + "═"*40)
        print("📊 EXECUTION STATISTICS:")
        print(f"⏱️  Total Time:    {duration:.2f} sec")
        print(f"💻 CPU Time Use:  {cpu_usage_total:.2f} sec")
        print(f"⚡ Avg. CPU Load: {avg_cpu_load:.1f}% ({num_threads} threads)")
        print(f"📟 Max RAM RSS:   {ram_end:.1f} MB")
        print("═"*40)
        print(f"🤖 AI RESPONSE:\n{result}")
        print("═"*40)
        
    except Exception as e:
        print(f"❌ An error occurred during initialization or processing: {e}")

if __name__ == "__main__":
    test_single_image()
