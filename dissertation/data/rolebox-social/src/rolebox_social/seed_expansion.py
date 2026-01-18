"""
Seed Expansion for Field Identification
========================================

Python implementation of the Benabdelkrim et al. (2020) methodology for field
identification using Twitter list co-classification (social curation).

Reference:
    Benabdelkrim, M., Levallois, C., Savinien, J., & Robardet, C. (2020).
    Opening Fields: A Methodological Contribution to the Identification of
    Heterogeneous Actors in Unbounded Relational Orders.
    M@n@gement, 23(1), 4-18.
    https://doi.org/10.37725/mgmt.v23.4245

Based on:
- Java: https://github.com/seinecle/FieldIdentifier (unavailable)
- Python: https://github.com/MohamedBnbm/seed_expansion
- Text Mining: https://github.com/seinecle/TextMiningOnCommunities

This implementation adapts the methodology to work with:
1. Twitter list co-membership (original approach)
2. Mention co-occurrence (proxy when list data unavailable)

The six-step procedure (Benabdelkrim et al., 2020):
1. Seed selection - Domain experts identify core field accounts
2. Network discovery - Two-ring expansion from seeds via co-classification
3. Denoising - Random walk filtering to remove peripheral nodes
4. Network merging - Combine seed-specific networks
5. Visualization - Force-directed layout (ForceAtlas2)
6. Sub-region identification - Louvain community detection + text mining
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Any, Callable
import numpy as np

# Optional imports
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.feature_extraction.text import CountVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_CONFIG = {
    'min_k': 3,                    # Min co-classifications for edge
    'max_list_size': 500,          # Filter large lists (bot-generated)
    'max_lists_per_user': 100,     # Cap lists per user
    'max_ring1': 10000,            # Max users in ring 1
    'max_ring2': 100000,           # Max users in ring 2
    'random_walk_steps': 2,        # Steps for denoising random walk
    'random_walk_iterations': 1000, # Number of random walks
    'random_walk_threshold': 0.5,  # Threshold for node retention
    'louvain_resolution': 1.0,     # Community detection resolution
    'top_terms_per_community': 20, # Terms to extract per community
    'ngram_range': (1, 3),         # N-gram range for text mining
    'minority_language_threshold': 0.15,  # Filter minority languages
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SeedAccount:
    """A seed account for field expansion."""
    username: str
    user_id: str = ""
    account_type: str = ""  # institutional, thematic, cross-cutting
    description: str = ""
    ring1_size: int = 0
    ring2_size: int = 0

    def to_dict(self) -> Dict:
        return {
            'username': self.username,
            'user_id': self.user_id,
            'type': self.account_type,
            'description': self.description,
            'ring1_size': self.ring1_size,
            'ring2_size': self.ring2_size,
        }


@dataclass
class FieldNetwork:
    """Network representing a discovered field."""
    nodes: Set[str] = field(default_factory=set)
    edges: Dict[Tuple[str, str], int] = field(default_factory=dict)
    node_attributes: Dict[str, Dict] = field(default_factory=dict)

    def add_node(self, node_id: str, attributes: Dict = None):
        self.nodes.add(node_id)
        if attributes:
            self.node_attributes[node_id] = attributes

    def add_edge(self, u: str, v: str, weight: int):
        key = tuple(sorted([u, v]))
        self.edges[key] = max(self.edges.get(key, 0), weight)
        self.nodes.add(u)
        self.nodes.add(v)

    def to_networkx(self) -> 'nx.Graph':
        if not HAS_NETWORKX:
            raise ImportError("networkx required")
        G = nx.Graph()
        for node in self.nodes:
            G.add_node(node, **self.node_attributes.get(node, {}))
        for (u, v), weight in self.edges.items():
            G.add_edge(u, v, weight=weight)
        return G


@dataclass
class SubRegion:
    """A detected sub-region in the field."""
    id: int
    label: str
    members: Set[str]
    size: int
    internal_density: float
    external_ties: int
    top_terms: List[Tuple[str, float]]
    top_terms_relative: List[Tuple[str, float]]  # Relative frequency
    languages: Dict[str, int]
    seed_affiliation: str = ""

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'label': self.label,
            'size': self.size,
            'internal_density': self.internal_density,
            'external_ties': self.external_ties,
            'top_terms': [{'term': t, 'score': s} for t, s in self.top_terms[:10]],
            'top_terms_relative': [{'term': t, 'score': s} for t, s in self.top_terms_relative[:10]],
            'languages': self.languages,
            'seed_affiliation': self.seed_affiliation,
        }


# =============================================================================
# CO-CLASSIFICATION DATA SOURCES
# =============================================================================

class CoClassificationSource:
    """Abstract base for co-classification data sources."""

    def get_co_classifications(self, user_id: str) -> Dict[str, int]:
        """Get users co-classified with given user and counts."""
        raise NotImplementedError

    def get_user_lists(self, user_id: str) -> Set[str]:
        """Get lists containing user."""
        raise NotImplementedError

    def get_list_members(self, list_id: str) -> Set[str]:
        """Get members of a list."""
        raise NotImplementedError


class MentionBasedCoClassification(CoClassificationSource):
    """
    Co-classification based on mention co-occurrence.

    When two users are mentioned in the same tweet, they are
    considered "co-classified" by the tweet author.

    This is a proxy for list co-membership when list data is unavailable.
    """

    def __init__(self, min_co_mentions: int = 3):
        self.min_k = min_co_mentions
        self.user_tweets: Dict[str, Set[str]] = defaultdict(set)  # user -> tweets mentioning them
        self.tweet_mentions: Dict[str, Set[str]] = defaultdict(set)  # tweet -> users mentioned
        self.user_bios: Dict[str, str] = {}
        self.mention_counts: Counter = Counter()

    def add_tweet(self, tweet_id: str, mentions: List[str], author: str = None):
        """Add a tweet's mentions."""
        mentions_clean = [m.lower() if m.startswith('@') else '@' + m.lower()
                         for m in mentions if m]

        for m in mentions_clean:
            self.user_tweets[m].add(tweet_id)
            self.mention_counts[m] += 1

        self.tweet_mentions[tweet_id] = set(mentions_clean)

    def add_user_bio(self, username: str, bio: str):
        """Store user bio for text mining."""
        username = username.lower() if username.startswith('@') else '@' + username.lower()
        self.user_bios[username] = bio

    def get_co_classifications(self, user_id: str) -> Dict[str, int]:
        """Get co-mentioned users and counts."""
        user_id = user_id.lower()
        if not user_id.startswith('@'):
            user_id = '@' + user_id

        co_mentions = Counter()

        # For each tweet mentioning this user
        for tweet_id in self.user_tweets.get(user_id, set()):
            # Count other users mentioned in same tweet
            for other_user in self.tweet_mentions[tweet_id]:
                if other_user != user_id:
                    co_mentions[other_user] += 1

        # Filter by minimum threshold
        return {u: c for u, c in co_mentions.items() if c >= self.min_k}

    def get_user_lists(self, user_id: str) -> Set[str]:
        """Get 'lists' (tweets) containing user."""
        user_id = user_id.lower()
        if not user_id.startswith('@'):
            user_id = '@' + user_id
        return self.user_tweets.get(user_id, set())

    def get_list_members(self, list_id: str) -> Set[str]:
        """Get members of a 'list' (tweet)."""
        return self.tweet_mentions.get(list_id, set())

    def get_statistics(self) -> Dict:
        """Get data source statistics."""
        return {
            'n_users': len(self.user_tweets),
            'n_tweets': len(self.tweet_mentions),
            'n_bios': len(self.user_bios),
            'top_mentioned': self.mention_counts.most_common(20),
        }


# =============================================================================
# TEXT MINING
# =============================================================================

class CommunityTextMiner:
    """
    Extract characteristic terms for each community.

    Implements the approach from TextMiningOnCommunities:
    1. Collect text (bios) for each community
    2. Extract n-grams
    3. Compute TF-IDF and relative frequencies
    4. Identify distinguishing terms
    """

    def __init__(
        self,
        ngram_range: Tuple[int, int] = (1, 3),
        max_features: int = 5000,
        min_df: int = 2,
        max_df: float = 0.8,
    ):
        self.ngram_range = ngram_range
        self.max_features = max_features
        self.min_df = min_df
        self.max_df = max_df

        # Stopwords for multiple languages
        self.stopwords = self._get_multilingual_stopwords()

    def _get_multilingual_stopwords(self) -> Set[str]:
        """Get stopwords for EN, DE, FR, ES, NL."""
        stopwords = {
            # English
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'him', 'his',
            'she', 'her', 'it', 'its', 'they', 'them', 'their', 'this', 'that',
            'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'how', 'why',
            'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
            'very', 'just', 'also', 'now', 'here', 'there', 'then', 'once',
            # German
            'der', 'die', 'das', 'ein', 'eine', 'und', 'ist', 'sind', 'war', 'waren',
            'für', 'auf', 'mit', 'von', 'bei', 'zu', 'nach', 'aus', 'über', 'unter',
            'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'mein', 'dein', 'sein',
            # French
            'le', 'la', 'les', 'un', 'une', 'des', 'et', 'est', 'sont', 'pour',
            'sur', 'avec', 'dans', 'par', 'qui', 'que', 'ce', 'cette', 'ces',
            'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'mon', 'ton',
            # Spanish
            'el', 'la', 'los', 'las', 'un', 'una', 'y', 'es', 'son', 'para',
            'en', 'con', 'por', 'que', 'del', 'al', 'como', 'más', 'pero',
            # Dutch
            'de', 'het', 'een', 'en', 'van', 'in', 'op', 'te', 'dat', 'die',
            'voor', 'met', 'zijn', 'naar', 'ook', 'als', 'aan', 'er', 'maar',
            # Common Twitter/Bio terms
            'rt', 'via', 'amp', 'http', 'https', 'www', 'com', 'co', 'org',
            'twitter', 'tweet', 'follow', 'follower', 'following', 'account',
            'view', 'views', 'opinion', 'opinions', 'own', 'personal',
        }
        return stopwords

    def extract_community_terms(
        self,
        communities: List[Set[str]],
        user_bios: Dict[str, str],
        top_n: int = 20,
    ) -> Tuple[List[List[Tuple[str, float]]], List[List[Tuple[str, float]]]]:
        """
        Extract top terms for each community.

        Returns:
            Tuple of (absolute_terms, relative_terms) per community
        """
        if not HAS_SKLEARN:
            return self._extract_simple(communities, user_bios, top_n)

        # Build document per community
        documents = []
        for comm in communities:
            text = ' '.join(
                user_bios.get(user.lower(), '')
                for user in comm
            )
            # Clean text
            text = re.sub(r'http\S+', '', text)  # Remove URLs
            text = re.sub(r'@\w+', '', text)  # Remove @mentions
            text = re.sub(r'#(\w+)', r'\1', text)  # Keep hashtag text
            text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
            text = text.lower()
            documents.append(text)

        if not any(d.strip() for d in documents):
            return ([[] for _ in communities], [[] for _ in communities])

        # TF-IDF vectorization
        try:
            vectorizer = TfidfVectorizer(
                ngram_range=self.ngram_range,
                max_features=self.max_features,
                min_df=self.min_df,
                max_df=self.max_df,
                stop_words=list(self.stopwords),
            )
            tfidf_matrix = vectorizer.fit_transform(documents)
            feature_names = vectorizer.get_feature_names_out()
        except ValueError:
            return ([[] for _ in communities], [[] for _ in communities])

        # Extract absolute TF-IDF scores
        absolute_terms = []
        for i in range(len(communities)):
            row = tfidf_matrix[i].toarray().flatten()
            top_idx = row.argsort()[-top_n:][::-1]
            terms = [(feature_names[j], float(row[j])) for j in top_idx if row[j] > 0]
            absolute_terms.append(terms)

        # Compute relative frequencies (distinguish from other communities)
        # Relative freq = term_freq_in_community / term_freq_total
        total_freqs = np.array(tfidf_matrix.sum(axis=0)).flatten()

        relative_terms = []
        for i in range(len(communities)):
            row = tfidf_matrix[i].toarray().flatten()
            # Relative frequency: how distinctive is term for this community?
            with np.errstate(divide='ignore', invalid='ignore'):
                rel_freq = np.where(total_freqs > 0, row / total_freqs * len(communities), 0)
            top_idx = rel_freq.argsort()[-top_n:][::-1]
            terms = [(feature_names[j], float(rel_freq[j])) for j in top_idx if rel_freq[j] > 0 and row[j] > 0]
            relative_terms.append(terms)

        return (absolute_terms, relative_terms)

    def _extract_simple(
        self,
        communities: List[Set[str]],
        user_bios: Dict[str, str],
        top_n: int,
    ) -> Tuple[List[List[Tuple[str, float]]], List[List[Tuple[str, float]]]]:
        """Simple fallback without sklearn."""
        results = []
        for comm in communities:
            word_counts = Counter()
            for user in comm:
                bio = user_bios.get(user.lower(), '')
                words = re.findall(r'\b[a-z]{3,}\b', bio.lower())
                word_counts.update(w for w in words if w not in self.stopwords)

            total = sum(word_counts.values()) or 1
            terms = [(w, c / total) for w, c in word_counts.most_common(top_n)]
            results.append(terms)

        return (results, results)

    def detect_language(self, text: str) -> str:
        """Simple language detection based on common words."""
        text_lower = text.lower()

        lang_indicators = {
            'de': ['der', 'und', 'für', 'bei', 'mit', 'ist', 'sind'],
            'fr': ['le', 'la', 'les', 'pour', 'avec', 'dans', 'est'],
            'es': ['el', 'la', 'los', 'para', 'con', 'del', 'que'],
            'nl': ['het', 'van', 'voor', 'met', 'naar', 'ook', 'zijn'],
        }

        scores = {lang: 0 for lang in lang_indicators}
        for lang, words in lang_indicators.items():
            for word in words:
                if f' {word} ' in f' {text_lower} ':
                    scores[lang] += 1

        best_lang = max(scores, key=scores.get)
        return best_lang if scores[best_lang] >= 2 else 'en'


# =============================================================================
# SEED EXPANSION ALGORITHM
# =============================================================================

class SeedExpander:
    """
    Implements the seed expansion algorithm for field discovery.

    Two-ring expansion:
    - Ring 1: Users co-classified with seed (>= min_k times)
    - Ring 2: Users co-classified with Ring 1 members

    Then applies random walk denoising to retain core field members.
    """

    def __init__(
        self,
        data_source: CoClassificationSource,
        config: Dict = None,
    ):
        self.data = data_source
        self.config = {**DEFAULT_CONFIG, **(config or {})}

    def expand_single_seed(
        self,
        seed: SeedAccount,
    ) -> Tuple[FieldNetwork, Dict[str, float]]:
        """
        Expand from a single seed account.

        Returns:
            Tuple of (network, node_intensities)
        """
        print(f"Expanding from {seed.username}...")

        min_k = self.config['min_k']
        max_ring1 = self.config['max_ring1']
        max_ring2 = self.config['max_ring2']

        # Get Ring 1: direct co-classifications
        ring1_counts = self.data.get_co_classifications(seed.username)
        ring1 = set(ring1_counts.keys())

        # Cap Ring 1 size
        if len(ring1) > max_ring1:
            sorted_users = sorted(ring1_counts.items(), key=lambda x: -x[1])
            ring1 = {u for u, _ in sorted_users[:max_ring1]}

        seed.ring1_size = len(ring1)
        print(f"  Ring 1: {len(ring1)} users")

        # Get Ring 2: co-classifications of Ring 1 members
        ring2 = set()
        ring2_counts = {}

        for r1_user in ring1:
            r2_cc = self.data.get_co_classifications(r1_user)
            for user, count in r2_cc.items():
                if user not in ring1 and user != seed.username:
                    ring2.add(user)
                    ring2_counts[user] = ring2_counts.get(user, 0) + count
                    if len(ring2) >= max_ring2:
                        break
            if len(ring2) >= max_ring2:
                break

        seed.ring2_size = len(ring2)
        print(f"  Ring 2: {len(ring2)} users")

        # Build network with all users
        all_users = {seed.username} | ring1 | ring2
        network = FieldNetwork()

        for user in all_users:
            network.add_node(user)

        # Add edges from co-classification counts
        for user in all_users:
            cc = self.data.get_co_classifications(user)
            for other, weight in cc.items():
                if other in all_users and weight >= min_k:
                    network.add_edge(user, other, weight)

        print(f"  Network: {len(network.nodes)} nodes, {len(network.edges)} edges")

        # Compute node intensities via random walk
        intensities = self._compute_intensities(network, seed.username)

        return network, intensities

    def _compute_intensities(
        self,
        network: FieldNetwork,
        seed: str,
    ) -> Dict[str, float]:
        """
        Compute node intensities via random walk from seed.

        Intensity = normalized visit frequency during random walks.
        """
        if not HAS_NETWORKX:
            return {n: 1.0 for n in network.nodes}

        G = network.to_networkx()
        if seed not in G:
            return {n: 1.0 for n in network.nodes}

        n_walks = self.config['random_walk_iterations']
        walk_length = self.config['random_walk_steps']

        visit_counts = Counter()

        for _ in range(n_walks):
            current = seed
            for _ in range(walk_length):
                neighbors = list(G.neighbors(current))
                if not neighbors:
                    break

                # Weight by edge weight
                weights = [G[current][n].get('weight', 1) for n in neighbors]
                total = sum(weights)
                probs = [w / total for w in weights]

                current = np.random.choice(neighbors, p=probs)
                visit_counts[current] += 1

        if not visit_counts:
            return {n: 1.0 for n in network.nodes}

        # Normalize: (count - mean) / std
        counts = np.array(list(visit_counts.values()))
        mean, std = counts.mean(), counts.std() or 1.0

        intensities = {}
        for node in network.nodes:
            count = visit_counts.get(node, 0)
            intensities[node] = (count - mean) / std if count > 0 else -mean / std

        return intensities

    def denoise_network(
        self,
        network: FieldNetwork,
        intensities: Dict[str, float],
        seeds: List[str],
    ) -> FieldNetwork:
        """
        Remove low-intensity nodes from network.

        Retains nodes with intensity > threshold * mean intensity.
        """
        threshold = self.config['random_walk_threshold']

        # Always retain seeds
        retained = set(s.lower() for s in seeds)

        # Retain nodes above threshold
        if intensities:
            mean_intensity = np.mean([i for i in intensities.values() if i > 0])
            retained |= {
                node for node, intensity in intensities.items()
                if intensity >= threshold * mean_intensity
            }
        else:
            retained = network.nodes

        # Build filtered network
        denoised = FieldNetwork()
        for node in retained:
            if node in network.node_attributes:
                denoised.add_node(node, network.node_attributes[node])
            else:
                denoised.add_node(node)

        for (u, v), weight in network.edges.items():
            if u in retained and v in retained:
                denoised.add_edge(u, v, weight)

        print(f"  Denoised: {len(denoised.nodes)}/{len(network.nodes)} nodes retained")

        return denoised


# =============================================================================
# FIELD MAPPER (MAIN PIPELINE)
# =============================================================================

class FieldIdentifier:
    """
    Complete field identification pipeline.

    Implements the full 6-step Benabdelkrim et al. (2020) methodology:
    1. Seed selection
    2. Network discovery (two-ring expansion)
    3. Denoising (random walk filtering)
    4. Network merging
    5. Visualization (network export)
    6. Sub-region identification (Louvain + text mining)
    """

    def __init__(self, config: Dict = None):
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.seeds: List[SeedAccount] = []
        self.data_source: Optional[CoClassificationSource] = None
        self.network: Optional[FieldNetwork] = None
        self.communities: List[Set[str]] = []
        self.sub_regions: List[SubRegion] = []
        self.text_miner = CommunityTextMiner(
            ngram_range=self.config['ngram_range'],
        )

    def set_seeds(self, seeds: List[Dict]):
        """Set seed accounts for field identification."""
        self.seeds = [
            SeedAccount(
                username=s['username'],
                user_id=s.get('user_id', ''),
                account_type=s.get('type', ''),
                description=s.get('description', ''),
            )
            for s in seeds
        ]
        print(f"Configured {len(self.seeds)} seed accounts")

    def set_data_source(self, source: CoClassificationSource):
        """Set the co-classification data source."""
        self.data_source = source
        stats = source.get_statistics()
        print(f"Data source: {stats.get('n_users', 0)} users, {stats.get('n_tweets', 0)} tweets")

    def run_expansion(self, denoise: bool = True) -> FieldNetwork:
        """
        Run seed expansion to discover field network.

        Args:
            denoise: Whether to apply random walk denoising

        Returns:
            Merged field network
        """
        if not self.data_source:
            raise ValueError("Set data source first")
        if not self.seeds:
            raise ValueError("Set seeds first")

        expander = SeedExpander(self.data_source, self.config)

        # Expand from each seed
        seed_networks = []
        seed_intensities = []

        for seed in self.seeds:
            net, intensities = expander.expand_single_seed(seed)
            seed_networks.append(net)
            seed_intensities.append(intensities)

        # Merge networks
        print("\nMerging seed networks...")
        merged = FieldNetwork()
        merged_intensities = {}

        for net, intensities in zip(seed_networks, seed_intensities):
            for node in net.nodes:
                if node in net.node_attributes:
                    merged.add_node(node, net.node_attributes[node])
                else:
                    merged.add_node(node)

                # Combine intensities
                if node in intensities:
                    merged_intensities[node] = merged_intensities.get(node, 0) + intensities[node]

            for (u, v), weight in net.edges.items():
                merged.add_edge(u, v, weight)

        print(f"Merged network: {len(merged.nodes)} nodes, {len(merged.edges)} edges")

        # Denoise if requested
        if denoise:
            print("\nDenoising network...")
            seed_usernames = [s.username for s in self.seeds]
            merged = expander.denoise_network(merged, merged_intensities, seed_usernames)

        self.network = merged
        return merged

    def detect_communities(self, resolution: float = None) -> List[Set[str]]:
        """
        Detect sub-regions using Louvain algorithm.
        """
        if not self.network:
            raise ValueError("Run expansion first")
        if not HAS_NETWORKX:
            raise ImportError("networkx required")

        resolution = resolution or self.config['louvain_resolution']

        print(f"\nDetecting communities (resolution={resolution})...")

        G = self.network.to_networkx()

        from networkx.algorithms.community import louvain_communities

        communities = louvain_communities(
            G, weight='weight', resolution=resolution, seed=42
        )

        self.communities = [set(c) for c in communities]
        self.communities.sort(key=len, reverse=True)

        # Compute modularity
        modularity = nx.algorithms.community.modularity(
            G, self.communities, weight='weight'
        )

        print(f"Found {len(self.communities)} communities")
        print(f"Modularity: {modularity:.4f}")
        print(f"Largest communities: {[len(c) for c in self.communities[:10]]}")

        return self.communities

    def characterize_regions(self) -> List[SubRegion]:
        """
        Characterize each sub-region with text mining.
        """
        if not self.communities:
            raise ValueError("Detect communities first")

        print("\nCharacterizing sub-regions...")

        # Get user bios from data source
        user_bios = {}
        if isinstance(self.data_source, MentionBasedCoClassification):
            user_bios = self.data_source.user_bios

        # Extract terms
        top_n = self.config['top_terms_per_community']
        absolute_terms, relative_terms = self.text_miner.extract_community_terms(
            self.communities, user_bios, top_n
        )

        # Build SubRegion objects
        G = self.network.to_networkx() if HAS_NETWORKX else None

        self.sub_regions = []
        for i, (comm, abs_terms, rel_terms) in enumerate(
            zip(self.communities, absolute_terms, relative_terms)
        ):
            # Compute internal density
            if G:
                subgraph = G.subgraph(comm)
                n = len(comm)
                max_edges = n * (n - 1) / 2
                internal_density = subgraph.number_of_edges() / max_edges if max_edges > 0 else 0

                # Count external ties
                external = sum(
                    1 for node in comm
                    for neighbor in G.neighbors(node)
                    if neighbor not in comm
                )
            else:
                internal_density = 0
                external = 0

            # Detect languages
            languages = Counter()
            for user in comm:
                bio = user_bios.get(user, '')
                lang = self.text_miner.detect_language(bio)
                languages[lang] += 1

            # Determine seed affiliation
            seed_affiliation = ""
            for seed in self.seeds:
                if seed.username.lower() in {u.lower() for u in comm}:
                    seed_affiliation = seed.description or seed.username
                    break

            # Generate label from top terms
            label_terms = [t for t, _ in abs_terms[:3]]
            label = ' / '.join(label_terms) if label_terms else f"Community_{i}"

            region = SubRegion(
                id=i,
                label=label,
                members=comm,
                size=len(comm),
                internal_density=internal_density,
                external_ties=external,
                top_terms=abs_terms,
                top_terms_relative=rel_terms,
                languages=dict(languages),
                seed_affiliation=seed_affiliation,
            )
            self.sub_regions.append(region)

            if i < 10:
                print(f"\n[{i}] {label} (n={len(comm)})")
                if seed_affiliation:
                    print(f"    Seed: {seed_affiliation}")
                print(f"    Density: {internal_density:.4f}, External: {external}")
                if rel_terms:
                    print(f"    Distinctive: {', '.join(t for t, _ in rel_terms[:5])}")

        return self.sub_regions

    def export_results(self, output_dir: Path) -> Dict:
        """Export all results to files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {
            'metadata': {
                'config': self.config,
                'n_seeds': len(self.seeds),
                'seeds': [s.to_dict() for s in self.seeds],
            },
            'network': {
                'n_nodes': len(self.network.nodes) if self.network else 0,
                'n_edges': len(self.network.edges) if self.network else 0,
            },
            'communities': {
                'n_communities': len(self.communities),
                'sizes': [len(c) for c in self.communities],
                'modularity': 0,  # Will be set if computed
            },
            'sub_regions': [sr.to_dict() for sr in self.sub_regions],
        }

        # Compute modularity
        if self.network and HAS_NETWORKX and self.communities:
            try:
                G = self.network.to_networkx()
                if G.number_of_edges() > 0:
                    results['communities']['modularity'] = nx.algorithms.community.modularity(
                        G, self.communities, weight='weight'
                    )
            except (ZeroDivisionError, ValueError):
                pass  # Skip modularity if network is too sparse

        # Save main results
        with open(output_dir / 'field_identification_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)

        # Save network
        if self.network and HAS_NETWORKX:
            G = self.network.to_networkx()
            nx.write_graphml(G, output_dir / 'field_network.graphml')

        # Save sub-regions
        with open(output_dir / 'sub_regions_detailed.json', 'w', encoding='utf-8') as f:
            detailed = []
            for sr in self.sub_regions:
                d = sr.to_dict()
                d['members'] = list(sr.members)[:100]  # Sample
                detailed.append(d)
            json.dump(detailed, f, indent=2)

        print(f"\nResults exported to {output_dir}")
        return results


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_field_identification(
    tweets_df,
    seeds: List[Dict],
    output_dir: Path = None,
    min_k: int = 3,
    denoise: bool = True,
    resolution: float = 1.0,
) -> FieldIdentifier:
    """
    Run complete field identification pipeline.

    Args:
        tweets_df: DataFrame with Tweet text
        seeds: List of seed account dicts
        output_dir: Output directory
        min_k: Minimum co-mentions for connection
        denoise: Apply random walk denoising
        resolution: Louvain resolution

    Returns:
        FieldIdentifier instance with results
    """
    print("=" * 60)
    print("FIELD IDENTIFICATION PIPELINE")
    print("=" * 60)

    # Build data source from tweets
    print("\nBuilding co-classification data...")
    data_source = MentionBasedCoClassification(min_co_mentions=min_k)

    for idx, row in tweets_df.iterrows():
        tweet_text = row.get('Tweet', row.get('text', ''))
        if not tweet_text:
            continue

        mentions = re.findall(r'@(\w+)', str(tweet_text))
        data_source.add_tweet(str(idx), mentions)

    print(f"  {len(data_source.user_tweets)} users")
    print(f"  {len(data_source.tweet_mentions)} tweets")

    # Run pipeline
    identifier = FieldIdentifier({'min_k': min_k, 'louvain_resolution': resolution})
    identifier.set_seeds(seeds)
    identifier.set_data_source(data_source)

    identifier.run_expansion(denoise=denoise)
    identifier.detect_communities()
    identifier.characterize_regions()

    if output_dir:
        identifier.export_results(output_dir)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    return identifier


if __name__ == "__main__":
    print("Seed Expansion for Field Identification")
    print("Usage: from seed_expansion import run_field_identification")
