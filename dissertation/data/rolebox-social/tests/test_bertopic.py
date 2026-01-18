#!/usr/bin/env python
"""Test BERTopic import"""

import sys
print(f"Python: {sys.executable}", flush=True)

print("Testing sentence-transformers...", flush=True)
try:
    from sentence_transformers import SentenceTransformer
    print("sentence_transformers: OK", flush=True)
except Exception as e:
    print(f"sentence_transformers error: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Testing bertopic...", flush=True)
try:
    from bertopic import BERTopic
    print("bertopic: OK", flush=True)
except Exception as e:
    print(f"bertopic error: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("All imports OK!", flush=True)
