"""
Topic Modeling with BERTopic
============================

Advanced topic modeling for field characterization using BERTopic.

BERTopic combines:
- Sentence embeddings (SBERT/sentence-transformers)
- UMAP dimensionality reduction
- HDBSCAN clustering
- c-TF-IDF for topic representation

This module provides:
1. Community-level topic extraction from user bios
2. Document-level topic assignment
3. Interactive visualizations (topic hierarchy, document map, etc.)

References:
- BERTopic: https://maartengr.github.io/BERTopic/
- Paper: Grootendorst, M. (2022). BERTopic: Neural topic modeling with a class-based TF-IDF procedure.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set, Any
from collections import defaultdict, Counter
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Try imports
try:
    from bertopic import BERTopic
    HAS_BERTOPIC = True
except ImportError:
    HAS_BERTOPIC = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# =============================================================================
# PREPROCESSING
# =============================================================================

def preprocess_bio(text: str) -> str:
    """Clean and preprocess a user bio for topic modeling."""
    if not text:
        return ""

    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)

    # Remove @mentions
    text = re.sub(r'@\w+', '', text)

    # Keep hashtag text
    text = re.sub(r'#(\w+)', r'\1', text)

    # Remove special characters but keep spaces
    text = re.sub(r'[^\w\s]', ' ', text)

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text.strip()


def prepare_documents(
    user_bios: Dict[str, str],
    min_length: int = 10,
) -> Tuple[List[str], List[str]]:
    """
    Prepare documents for topic modeling.

    Args:
        user_bios: Mapping of usernames to bio text
        min_length: Minimum character length to include

    Returns:
        Tuple of (document texts, corresponding usernames)
    """
    documents = []
    usernames = []

    for username, bio in user_bios.items():
        cleaned = preprocess_bio(bio)
        if len(cleaned) >= min_length:
            documents.append(cleaned)
            usernames.append(username)

    return documents, usernames


# =============================================================================
# BERTOPIC WRAPPER
# =============================================================================

class FieldTopicModeler:
    """
    Topic modeling for field characterization using BERTopic.

    Provides:
    - Topic extraction from user bios
    - Community-level topic aggregation
    - Visualization generation
    """

    def __init__(
        self,
        language: str = "multilingual",
        n_topics: int = None,  # Auto-detect if None
        min_topic_size: int = 10,
        embedding_model: str = None,
    ):
        """
        Initialize topic modeler.

        Args:
            language: Language for stopwords ("english", "multilingual")
            n_topics: Number of topics (None for auto-detection)
            min_topic_size: Minimum documents per topic
            embedding_model: Sentence transformer model name
        """
        if not HAS_BERTOPIC:
            raise ImportError(
                "BERTopic required. Install with: pip install bertopic"
            )

        self.language = language
        self.n_topics = n_topics
        self.min_topic_size = min_topic_size

        # Default embedding model based on language
        if embedding_model is None:
            if language == "multilingual":
                embedding_model = "paraphrase-multilingual-MiniLM-L12-v2"
            else:
                embedding_model = "all-MiniLM-L6-v2"

        self.embedding_model = embedding_model

        # Initialize BERTopic
        self._init_model()

        # Results storage
        self.topics = None
        self.probs = None
        self.documents = None
        self.usernames = None
        self.topic_info = None

    def _init_model(self):
        """Initialize BERTopic model with configuration."""
        from bertopic import BERTopic

        # Use sentence-transformers for embeddings
        try:
            from sentence_transformers import SentenceTransformer
            embedding_model = SentenceTransformer(self.embedding_model)
        except ImportError:
            embedding_model = self.embedding_model

        # Create BERTopic model
        self.model = BERTopic(
            language=self.language if self.language != "multilingual" else "english",
            embedding_model=embedding_model,
            nr_topics=self.n_topics,
            min_topic_size=self.min_topic_size,
            calculate_probabilities=True,
            verbose=False,
        )

    def fit(
        self,
        user_bios: Dict[str, str],
        min_bio_length: int = 20,
    ) -> 'FieldTopicModeler':
        """
        Fit topic model on user bios.

        Args:
            user_bios: Mapping of usernames to bio text
            min_bio_length: Minimum bio length to include

        Returns:
            self
        """
        print("Preparing documents...")
        self.documents, self.usernames = prepare_documents(
            user_bios, min_length=min_bio_length
        )

        if len(self.documents) < self.min_topic_size * 2:
            raise ValueError(
                f"Not enough documents ({len(self.documents)}) for topic modeling. "
                f"Need at least {self.min_topic_size * 2}."
            )

        print(f"Fitting BERTopic on {len(self.documents)} documents...")
        self.topics, self.probs = self.model.fit_transform(self.documents)

        self.topic_info = self.model.get_topic_info()
        n_topics = len(self.topic_info) - 1  # Exclude outlier topic -1

        print(f"Found {n_topics} topics")

        return self

    def get_topic_info(self) -> 'pd.DataFrame':
        """Get topic information DataFrame."""
        return self.model.get_topic_info()

    def get_document_topics(self) -> List[Dict]:
        """Get topic assignments for all documents."""
        results = []
        for i, (doc, username, topic) in enumerate(
            zip(self.documents, self.usernames, self.topics)
        ):
            prob = self.probs[i].max() if self.probs is not None else 0

            # Get topic words
            if topic >= 0:
                topic_words = [w for w, _ in self.model.get_topic(topic)[:5]]
            else:
                topic_words = []

            results.append({
                'username': username,
                'document': doc[:100] + '...' if len(doc) > 100 else doc,
                'topic': topic,
                'probability': float(prob),
                'topic_words': topic_words,
            })

        return results

    def get_community_topics(
        self,
        communities: Dict[str, int],
    ) -> Dict[int, Dict]:
        """
        Aggregate topics by community.

        Args:
            communities: Mapping of usernames to community indices

        Returns:
            Dict mapping community indices to topic distributions
        """
        community_topics = defaultdict(lambda: defaultdict(int))

        for username, topic in zip(self.usernames, self.topics):
            username_lower = username.lower()
            if username_lower in communities:
                comm = communities[username_lower]
                community_topics[comm][topic] += 1

        # Compute statistics per community
        results = {}
        for comm, topic_counts in community_topics.items():
            total = sum(topic_counts.values())

            # Sort topics by count
            sorted_topics = sorted(
                topic_counts.items(),
                key=lambda x: -x[1]
            )

            # Get top topics with words
            top_topics = []
            for topic_id, count in sorted_topics[:5]:
                if topic_id >= 0:
                    topic_words = [w for w, _ in self.model.get_topic(topic_id)[:5]]
                    top_topics.append({
                        'topic_id': topic_id,
                        'count': count,
                        'proportion': count / total,
                        'words': topic_words,
                    })

            results[comm] = {
                'n_documents': total,
                'n_topics': len(topic_counts),
                'top_topics': top_topics,
                'dominant_topic': sorted_topics[0][0] if sorted_topics else -1,
            }

        return results


# =============================================================================
# VISUALIZATION
# =============================================================================

class TopicVisualizer:
    """Generate BERTopic visualizations."""

    def __init__(self, model: FieldTopicModeler, output_dir: Path):
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_all_visualizations(self):
        """Generate and save all available visualizations."""
        print(f"\nGenerating topic visualizations in {self.output_dir}...")

        visualizations = [
            ('topics_barchart', self._save_topics_barchart),
            ('topics_heatmap', self._save_topic_heatmap),
            ('topics_hierarchy', self._save_topic_hierarchy),
            ('documents_map', self._save_documents_map),
            ('topics_similarity', self._save_topic_similarity),
        ]

        for name, func in visualizations:
            try:
                func()
            except Exception as e:
                print(f"  Warning: Could not generate {name}: {e}")

    def _save_topics_barchart(self):
        """Save topic word barchart."""
        fig = self.model.model.visualize_barchart(top_n_topics=15, n_words=8)
        path = self.output_dir / "topics_barchart.html"
        fig.write_html(str(path))
        print(f"  Saved: {path.name}")

    def _save_topic_heatmap(self):
        """Save topic similarity heatmap."""
        fig = self.model.model.visualize_heatmap(n_clusters=10)
        path = self.output_dir / "topics_heatmap.html"
        fig.write_html(str(path))
        print(f"  Saved: {path.name}")

    def _save_topic_hierarchy(self):
        """Save hierarchical topic clustering."""
        fig = self.model.model.visualize_hierarchy(top_n_topics=30)
        path = self.output_dir / "topics_hierarchy.html"
        fig.write_html(str(path))
        print(f"  Saved: {path.name}")

    def _save_documents_map(self):
        """Save 2D document embedding map."""
        fig = self.model.model.visualize_documents(
            self.model.documents,
            hide_annotations=True,
            hide_document_hover=False,
        )
        path = self.output_dir / "documents_map.html"
        fig.write_html(str(path))
        print(f"  Saved: {path.name}")

    def _save_topic_similarity(self):
        """Save inter-topic distance map."""
        fig = self.model.model.visualize_topics()
        path = self.output_dir / "topics_similarity.html"
        fig.write_html(str(path))
        print(f"  Saved: {path.name}")


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def run_topic_modeling(
    user_bios: Dict[str, str],
    communities: Dict[str, int] = None,
    output_dir: Path = None,
    n_topics: int = None,
    language: str = "multilingual",
) -> Dict:
    """
    Run complete topic modeling pipeline.

    Args:
        user_bios: Mapping of usernames to bio text
        communities: Optional community assignments
        output_dir: Directory for outputs
        n_topics: Number of topics (None for auto)
        language: Language setting

    Returns:
        Dict with topic modeling results
    """
    print("=" * 60)
    print("TOPIC MODELING WITH BERTOPIC")
    print("=" * 60)

    # Initialize modeler
    modeler = FieldTopicModeler(
        language=language,
        n_topics=n_topics,
        min_topic_size=5,
    )

    # Fit model
    modeler.fit(user_bios, min_bio_length=15)

    # Get results
    topic_info = modeler.get_topic_info()
    doc_topics = modeler.get_document_topics()

    results = {
        'n_documents': len(modeler.documents),
        'n_topics': len(topic_info) - 1,
        'topic_info': topic_info.to_dict() if HAS_PANDAS else {},
        'document_topics': doc_topics[:100],  # Sample
    }

    # Community-level analysis if available
    if communities:
        comm_topics = modeler.get_community_topics(communities)
        results['community_topics'] = {
            str(k): v for k, v in comm_topics.items()
        }

        print(f"\nTop topics per community:")
        for comm_id, data in sorted(comm_topics.items())[:10]:
            if data['top_topics']:
                top = data['top_topics'][0]
                words = ', '.join(top['words'][:3])
                print(f"  Community {comm_id}: {words} ({top['proportion']:.1%})")

    # Generate visualizations
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save results JSON
        with open(output_dir / 'topic_modeling_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)

        # Generate visualizations
        viz = TopicVisualizer(modeler, output_dir / 'visualizations')
        viz.save_all_visualizations()

    print("\n" + "=" * 60)
    print("TOPIC MODELING COMPLETE")
    print("=" * 60)

    return results


# =============================================================================
# TWEET CORPUS TOPIC MODELING (with Quantized LLMs)
# =============================================================================

def load_twitter_corpus(data_dir: Path, sample_size: int = None) -> 'pd.DataFrame':
    """
    Load and consolidate all EIT Twitter data from TweetBinder Excel exports.

    Args:
        data_dir: Path to data/raw directory
        sample_size: Optional limit on number of tweets to load

    Returns:
        DataFrame with columns: User, Date, Tweet, etc.
    """
    import glob
    from tqdm import tqdm

    excel_pattern = str(data_dir / "twitter_extracted" / "Raw_Twitter_Data (TweetBinder)" / "Tweetbinder*" / "*.xlsx")
    files = glob.glob(excel_pattern)

    if not files:
        raise FileNotFoundError(f"No Excel files found matching: {excel_pattern}")

    dfs = []
    for f in tqdm(files, desc="Loading Excel files"):
        try:
            df = pd.read_excel(f, sheet_name='Tweets')
            df['source_file'] = Path(f).name
            dfs.append(df)
        except Exception as e:
            print(f"Warning: Could not read {f}: {e}")

    corpus = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(corpus):,} tweets from {len(files)} files")

    # Clean and deduplicate
    corpus = corpus.dropna(subset=['Tweet'])
    corpus = corpus.drop_duplicates(subset=['Tweet'])
    print(f"After deduplication: {len(corpus):,} unique tweets")

    if sample_size and len(corpus) > sample_size:
        corpus = corpus.sample(n=sample_size, random_state=42)
        print(f"Sampled to {len(corpus):,} tweets")

    return corpus


def preprocess_tweet(text: str) -> str:
    """Clean a tweet for topic modeling."""
    if not isinstance(text, str):
        return ""

    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove RT prefix
    text = re.sub(r'^RT\s*@\w+:\s*', '', text)
    # Keep @mentions but remove the @ symbol
    text = re.sub(r'@(\w+)', r'\1', text)
    # Keep hashtag text
    text = re.sub(r'#(\w+)', r'\1', text)
    # Normalize whitespace
    text = ' '.join(text.split())

    return text.strip()


class TweetTopicModeler:
    """
    BERTopic for Twitter corpus with optional LLM-based topic labeling.

    Extends the standard BERTopic pipeline with:
    - GPU acceleration (cuML UMAP/HDBSCAN if available)
    - Quantized LLM for interpretable topic labels
    - DataMapPlot visualization
    """

    def __init__(
        self,
        embedding_model: str = "BAAI/bge-small-en-v1.5",
        min_cluster_size: int = 100,
        use_gpu: bool = False,
        llm_model_path: str = None,
    ):
        """
        Initialize tweet topic modeler.

        Args:
            embedding_model: SentenceTransformer model name
            min_cluster_size: Minimum cluster size for HDBSCAN
            use_gpu: Use GPU-accelerated UMAP/HDBSCAN (requires cuML)
            llm_model_path: Path to quantized LLM (e.g., .gguf file)
        """
        if not HAS_BERTOPIC:
            raise ImportError("BERTopic required. Install with: pip install bertopic")

        self.embedding_model_name = embedding_model
        self.min_cluster_size = min_cluster_size
        self.use_gpu = use_gpu
        self.llm_model_path = llm_model_path

        # Results
        self.model = None
        self.topics = None
        self.probs = None
        self.embeddings = None
        self.reduced_embeddings = None
        self.documents = None

    def _get_umap_model(self, n_components: int = 5):
        """Get UMAP model, GPU-accelerated if available."""
        if self.use_gpu:
            try:
                from cuml.manifold import UMAP
                print("Using GPU-accelerated UMAP (cuML)")
            except ImportError:
                print("cuML not available, using CPU UMAP")
                from umap import UMAP
        else:
            from umap import UMAP

        return UMAP(
            n_neighbors=15,
            n_components=n_components,
            min_dist=0.0,
            metric='cosine',
            random_state=42
        )

    def _get_hdbscan_model(self):
        """Get HDBSCAN model, GPU-accelerated if available."""
        if self.use_gpu:
            try:
                from cuml.cluster import HDBSCAN
                print("Using GPU-accelerated HDBSCAN (cuML)")
            except ImportError:
                print("cuML not available, using CPU HDBSCAN")
                from hdbscan import HDBSCAN
        else:
            from hdbscan import HDBSCAN

        return HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            metric='euclidean',
            cluster_selection_method='eom',
            prediction_data=True
        )

    def _get_representation_models(self):
        """Get representation models for topic labeling."""
        from bertopic.representation import KeyBERTInspired

        representations = {"KeyBERT": KeyBERTInspired()}

        if self.llm_model_path:
            try:
                from llama_cpp import Llama
                from bertopic.representation import LlamaCPP

                print(f"Loading quantized LLM from {self.llm_model_path}")
                llm = Llama(
                    model_path=self.llm_model_path,
                    n_gpu_layers=-1,
                    n_ctx=4096,
                    stop=["Q:", "\n"],
                    verbose=False
                )

                prompt = """Q:
I have a topic about European innovation and sustainability transitions that contains the following documents:
[DOCUMENTS]

The topic is described by the following keywords: '[KEYWORDS]'.

Based on the above information, give a short descriptive label (max 5 words) for this topic.
A:
"""
                representations["LLM"] = LlamaCPP(llm, prompt=prompt)
                print("LLM representation model loaded")

            except Exception as e:
                print(f"Could not load LLM: {e}. Using KeyBERT only.")

        return representations

    def fit(self, tweets: List[str]) -> 'TweetTopicModeler':
        """
        Fit topic model on tweets.

        Args:
            tweets: List of raw tweet texts

        Returns:
            self
        """
        from bertopic import BERTopic
        from sentence_transformers import SentenceTransformer
        from sklearn.feature_extraction.text import CountVectorizer

        # Preprocess
        print("Preprocessing tweets...")
        self.documents = [preprocess_tweet(t) for t in tweets]
        self.documents = [d for d in self.documents if len(d) > 10]
        print(f"After filtering: {len(self.documents):,} documents")

        # Embeddings
        print(f"Loading embedding model: {self.embedding_model_name}")
        embedding_model = SentenceTransformer(self.embedding_model_name)

        print("Computing embeddings...")
        self.embeddings = embedding_model.encode(
            self.documents,
            show_progress_bar=True,
            batch_size=32
        )

        # 2D embeddings for visualization
        print("Computing 2D embeddings for visualization...")
        vis_umap = self._get_umap_model(n_components=2)
        self.reduced_embeddings = vis_umap.fit_transform(self.embeddings)

        # CountVectorizer with stopword removal for cleaner topic representations
        vectorizer_model = CountVectorizer(
            stop_words='english',
            min_df=2,
            ngram_range=(1, 2)  # Include bigrams for richer topics
        )

        # Build BERTopic
        print("Training BERTopic model...")
        self.model = BERTopic(
            embedding_model=embedding_model,
            umap_model=self._get_umap_model(n_components=5),
            hdbscan_model=self._get_hdbscan_model(),
            vectorizer_model=vectorizer_model,
            representation_model=self._get_representation_models(),
            top_n_words=10,
            verbose=True
        )

        self.topics, self.probs = self.model.fit_transform(
            self.documents,
            self.embeddings
        )

        # Summary
        topic_info = self.model.get_topic_info()
        n_topics = len(topic_info) - 1
        n_outliers = sum(1 for t in self.topics if t == -1)

        print(f"\nFound {n_topics} topics")
        print(f"Outlier documents: {n_outliers:,} ({100*n_outliers/len(self.documents):.1f}%)")

        return self

    def get_topic_info(self) -> 'pd.DataFrame':
        """Get topic information."""
        return self.model.get_topic_info()

    def save(self, output_dir: Path):
        """Save model and results."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Topic info
        self.model.get_topic_info().to_csv(output_dir / "topic_info.csv", index=False)

        # Document assignments
        doc_topics = pd.DataFrame({
            'document': self.documents,
            'topic': self.topics,
        })
        doc_topics.to_csv(output_dir / "document_topics.csv", index=False)

        # Embeddings
        np.save(output_dir / "embeddings_2d.npy", self.reduced_embeddings)

        # Model (safetensors format)
        self.model.save(output_dir / "bertopic_model", serialization="safetensors")

        print(f"Saved to {output_dir}")

    def visualize_datamapplot(self, output_path: Path = None):
        """Create DataMapPlot visualization."""
        try:
            import datamapplot
        except ImportError:
            print("datamapplot not installed. Install with: pip install datamapplot")
            return None

        topic_info = self.model.get_topic_info()
        topic_labels = dict(zip(topic_info['Topic'], topic_info['Name']))
        all_labels = [
            topic_labels.get(t, "Outliers") if t != -1 else "Outliers"
            for t in self.topics
        ]

        fig = datamapplot.create_plot(
            self.reduced_embeddings,
            all_labels,
            label_font_size=9,
            title="EIT Twitter - Topic Map",
            sub_title="Topics discovered with BERTopic",
            label_wrap_width=20,
            use_medoids=True,
        )

        if output_path:
            fig.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"Saved visualization to {output_path}")

        return fig


def run_tweet_topic_modeling(
    data_dir: Path,
    output_dir: Path,
    sample_size: int = None,
    min_cluster_size: int = 100,
    use_gpu: bool = False,
    llm_model_path: str = None,
) -> Dict:
    """
    Run complete tweet topic modeling pipeline.

    Args:
        data_dir: Path to data/raw directory with Twitter exports
        output_dir: Output directory
        sample_size: Optional sample size
        min_cluster_size: HDBSCAN min cluster size
        use_gpu: Use GPU acceleration
        llm_model_path: Path to quantized LLM for labeling

    Returns:
        Dict with results
    """
    print("=" * 60)
    print("TWEET TOPIC MODELING WITH BERTOPIC")
    print("=" * 60)

    # Load corpus
    corpus = load_twitter_corpus(data_dir, sample_size)

    # Run modeling
    modeler = TweetTopicModeler(
        min_cluster_size=min_cluster_size,
        use_gpu=use_gpu,
        llm_model_path=llm_model_path,
    )
    modeler.fit(corpus['Tweet'].tolist())

    # Save
    output_dir = Path(output_dir)
    modeler.save(output_dir)

    # Visualize
    modeler.visualize_datamapplot(output_dir / "topic_map.png")

    # Summary
    topic_info = modeler.get_topic_info()
    print("\n" + "=" * 60)
    print("TOP TOPICS")
    print("=" * 60)
    for _, row in topic_info.head(15).iterrows():
        if row['Topic'] != -1:
            print(f"Topic {row['Topic']:3d} ({row['Count']:5d} docs): {row['Name']}")

    return {
        'n_documents': len(modeler.documents),
        'n_topics': len(topic_info) - 1,
        'topic_info': topic_info.to_dict(),
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI entry point for topic modeling."""
    import argparse

    parser = argparse.ArgumentParser(description="Topic Modeling with BERTopic")
    parser.add_argument("--mode", choices=["bios", "tweets"], default="bios",
                        help="Mode: 'bios' for user bios, 'tweets' for tweet corpus")
    parser.add_argument("--data-dir", type=Path, default=None,
                        help="Data directory (for tweets mode)")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Output directory")
    parser.add_argument("--sample", type=int, default=None,
                        help="Sample size")
    parser.add_argument("--min-cluster-size", type=int, default=100,
                        help="Minimum cluster size for HDBSCAN")
    parser.add_argument("--gpu", action="store_true",
                        help="Use GPU acceleration")
    parser.add_argument("--llm-model", type=str, default=None,
                        help="Path to quantized LLM (.gguf)")

    args = parser.parse_args()

    if not HAS_BERTOPIC:
        print("BERTopic not installed. Install with:")
        print("  pip install bertopic sentence-transformers umap-learn hdbscan")
        print()
        print("For GPU acceleration:")
        print("  pip install cudf-cu12 cuml-cu12 --extra-index-url=https://pypi.nvidia.com")
        print()
        print("For LLM labeling:")
        print("  pip install llama-cpp-python")
    elif args.mode == "tweets":
        if args.data_dir is None:
            args.data_dir = Path(__file__).parent.parent.parent / "data" / "raw"
        if args.output_dir is None:
            args.output_dir = Path(__file__).parent.parent.parent / "data" / "outputs" / "topics"

        run_tweet_topic_modeling(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            sample_size=args.sample,
            min_cluster_size=args.min_cluster_size,
            use_gpu=args.gpu,
            llm_model_path=args.llm_model,
        )
    else:
        print("Usage examples:")
        print()
        print("  # Topic modeling on user bios")
        print("  from topic_modeling import run_topic_modeling")
        print("  results = run_topic_modeling(user_bios, output_dir='./topics/')")
        print()
        print("  # Topic modeling on tweet corpus")
        print("  python -m rolebox_social.topic_modeling --mode tweets")
        print("  python -m rolebox_social.topic_modeling --mode tweets --gpu --sample 10000")


if __name__ == "__main__":
    main()
