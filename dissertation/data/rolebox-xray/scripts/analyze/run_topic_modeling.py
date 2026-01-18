#!/usr/bin/env python3
"""
Topic Modeling Pipeline for RoleBox-Xray

Performs BERTopic analysis on scientific literature corpus.
Can run standalone or use full METAFRASIA/role_xray implementation.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np


def load_corpus(input_path: Path) -> pd.DataFrame:
    """Load article corpus from CSV or JSON."""
    if input_path.suffix == ".csv":
        return pd.read_csv(input_path)
    elif input_path.suffix == ".json":
        with open(input_path) as f:
            data = json.load(f)
        return pd.DataFrame(data.values())
    else:
        raise ValueError(f"Unsupported format: {input_path.suffix}")


def run_topic_modeling(docs: list, min_cluster_size: int = 30):
    """Run BERTopic on documents."""
    try:
        from bertopic import BERTopic
        from sentence_transformers import SentenceTransformer

        # Initialize models
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        topic_model = BERTopic(
            embedding_model=embedding_model,
            min_topic_size=min_cluster_size,
            verbose=True
        )

        # Fit model
        topics, probs = topic_model.fit_transform(docs)

        return topic_model, topics, probs

    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install bertopic sentence-transformers")
        return None, None, None


def export_results(
    topic_model,
    topics: list,
    df: pd.DataFrame,
    output_dir: Path
):
    """Export topic modeling results."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Topic info
    topic_info = topic_model.get_topic_info()
    topic_info.to_csv(output_dir / "topic_info.csv", index=False)

    # Document-topic mapping
    df["topic"] = topics
    df.to_csv(output_dir / "documents_with_topics.csv", index=False)

    # Topic visualization (HTML)
    try:
        fig = topic_model.visualize_topics()
        fig.write_html(output_dir / "topic_visualization.html")
    except Exception as e:
        print(f"Could not generate visualization: {e}")

    print(f"Results exported to {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Run topic modeling on corpus")
    parser.add_argument("input", type=Path, help="Input CSV or JSON file")
    parser.add_argument("--output", type=Path, default=Path("outputs"),
                        help="Output directory")
    parser.add_argument("--text-column", default="abstract",
                        help="Column containing text to analyze")
    parser.add_argument("--min-cluster", type=int, default=30,
                        help="Minimum cluster size for BERTopic")

    args = parser.parse_args()

    print(f"Loading corpus from {args.input}")
    df = load_corpus(args.input)
    print(f"Loaded {len(df)} documents")

    # Get text column
    if args.text_column not in df.columns:
        print(f"Column '{args.text_column}' not found. Available: {df.columns.tolist()}")
        return

    docs = df[args.text_column].fillna("").tolist()

    print("Running topic modeling...")
    topic_model, topics, probs = run_topic_modeling(docs, args.min_cluster)

    if topic_model is not None:
        export_results(topic_model, topics, df, args.output)
        print("Done!")


if __name__ == "__main__":
    main()
