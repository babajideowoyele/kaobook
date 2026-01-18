#!/usr/bin/env python
"""Simple test for imports"""

import sys
print(f"Python: {sys.executable}", flush=True)

# Try torch first - this often fails with DLL issues
print("Testing torch...", flush=True)
try:
    import torch
    print(f"torch: {torch.__version__}", flush=True)
except Exception as e:
    print(f"torch error: {type(e).__name__}: {e}", flush=True)

print("Testing pandas...", flush=True)
try:
    import pandas as pd
    print(f"pandas: {pd.__version__}", flush=True)
except Exception as e:
    print(f"pandas error: {type(e).__name__}: {e}", flush=True)

print("Testing sklearn...", flush=True)
try:
    from sklearn.feature_extraction.text import CountVectorizer
    print("sklearn CountVectorizer: OK", flush=True)
except Exception as e:
    print(f"sklearn error: {type(e).__name__}: {e}", flush=True)

print("All done!", flush=True)
