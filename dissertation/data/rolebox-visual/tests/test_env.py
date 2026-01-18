#!/usr/bin/env python
"""Test rolebox-visual environment"""

import sys
print(f"Python: {sys.executable}")

# Test torch
import torch
print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA device: {torch.cuda.get_device_name(0)}")

# Test transformers
from transformers import AutoProcessor, AutoModelForCausalLM
print("Transformers: OK")

# Test other packages
import pandas as pd
import numpy as np
from PIL import Image
print(f"Pandas: {pd.__version__}")
print(f"NumPy: {np.__version__}")
print("Pillow: OK")

print("\nAll imports successful!")
