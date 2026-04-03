import os
import multiprocessing

# --- AUTO DETECTION ---
IS_PI = os.path.exists('/proc/device-tree/model')

if IS_PI:
    # 🍓 RASPBERRY PI 4 SETTINGS (Optimized for 2GB RAM)
    print("🌿 Environment: Raspberry Pi detected. Using optimized mobile settings.")
    LLM_THREADS = 4        
    LLM_CTX = 1024         # Minimum for Moondream2 to save RAM
    CAMERA_INDEX = 0       
    MODEL_PATH = "moondream2-q4_k.gguf"
    MMPROJ_PATH = "moondream2-mmproj-f16.gguf"
else:
    # 💻 PC / WSL SETTINGS (Higher performance)
    print("💻 Environment: PC / WSL detected. Using high-performance settings.")
    # Tip: Use 'nproc' in your terminal to see your core count
    LLM_THREADS = multiprocessing.cpu_count() // 2  # Use half of available threads by default
    LLM_CTX = 4096        # Larger context window for faster/better text
    CAMERA_INDEX = 0       # Change to 1 or 2 if you have multiple cameras on PC
    MODEL_PATH = "moondream2-q4_k.gguf"
    MMPROJ_PATH = "moondream2-mmproj-f16.gguf"

# --- COMMON SETTINGS ---
TEMPERATURE = 0.1      # Stable response for classification
MAX_TOKENS = 512       # Maximum length of the AI answer
CAMERA_WIDTH = 1280    
CAMERA_HEIGHT = 720    
CAMERA_WARMUP_FRAMES = 5 

# Default prompt for waste classification
DEFAULT_PROMPT = "Describe the object held in the person's hand with as much detail as possible. Identify its physical characteristics: material (plastic, metal, organic, glass, etc.), color, shape, texture, and any visible text or branding. Finally, classify what type of waste this is (plastic, organic, battery, or other) and explain your reasoning."
