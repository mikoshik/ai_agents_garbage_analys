import os

# --- MODEL SETTINGS ---
# Use .gguf for llama-cpp-python
MODEL_PATH = "moondream2-q4_k.gguf"
MMPROJ_PATH = "moondream2-mmproj-f16.gguf"

# Performance settings (optimized for Raspberry Pi 4 by default)
LLM_THREADS = 4        # Threads to use (4 cores on Pi 4)
LLM_CTX = 1200         # Context window (smaller = less RAM)
TEMPERATURE = 0.1      # Stable response for classification
MAX_TOKENS = 512       # Maximum length of the AI answer

# --- CAMERA SETTINGS ---
CAMERA_INDEX = 0       # /dev/video0 on Pi
CAMERA_WIDTH = 1280    # Standard HD resolution
CAMERA_HEIGHT = 720    # Standard HD resolution
CAMERA_WARMUP_FRAMES = 5 # Frames to skip for auto-exposure

# --- APP LOGIC ---
# Default prompt for waste classification
DEFAULT_PROMPT = "Describe the object held in the person's hand with as much detail as possible. Identify its physical characteristics: material (plastic, metal, organic, glass, etc.), color, shape, texture, and any visible text or branding. Finally, classify what type of waste this is (plastic, organic, battery, or other) and explain your reasoning."

# Environment check: help you know where you are running
IS_PI = os.path.exists('/proc/device-tree/model') # True if running on a real Pi
if IS_PI:
    print("🌿 Config: Running on Raspberry Pi detected.")
else:
    # Optional PC overrides
    # LLM_THREADS = 8 
    # LLM_CTX = 2048
    print("💻 Config: Running on PC (or non-Pi environment).")
