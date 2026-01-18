#!/usr/bin/env python
"""Test imports for topic_modeling"""

import sys
print(f"Python: {sys.executable}")
print(f"Path: {sys.path}")

try:
    import bertopic
    print(f"BERTopic: {bertopic.__version__}")
except Exception as e:
    print(f"BERTopic error: {e}")

try:
    from sklearn.feature_extraction.text import CountVectorizer
    print("sklearn CountVectorizer: OK")
except Exception as e:
    print(f"sklearn error: {e}")

try:
    from rolebox_social.topic_modeling import TweetTopicModeler
    print("TweetTopicModeler: OK")
except Exception as e:
    print(f"TweetTopicModeler error: {e}")
    import traceback
    traceback.print_exc()
