"""
Social Curation Field Mapping Pipeline
======================================

Complete implementation of the Schiffer et al. methodology for field identification
using social curation (Twitter list co-classification).

References:
- Schiffer et al. "Identifying and mapping fields with social curation"
- Java implementation: https://github.com/seinecle/FieldIdentifier
- Python seed expansion: https://github.com/MohamedBnbm/seed_expansion
- Text mining: https://github.com/seinecle/TextMiningOnCommunities

This implementation provides:
1. Seed selection and validation
2. Two-ring network expansion
3. Random walk denoising
4. Network merging across seeds
5. Community detection (Louvain)
6. Sub-region characterization via text mining (TF-IDF)
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Any
import numpy as np

# Optional imports
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("Warning: networkx not installed. pip install networkx")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: sklearn not installed. pip install scikit-learn")


# =============================================================================
# CONFIGURATION
# =============================================================================

# EIT KIC seed accounts for field mapping
EIT_SEEDS = [
    {'username': '@EIT_EU', 'type': 'Institutional', 'description': 'EIT Central'},
    {'username': '@ClimateKIC', 'type': 'Climate', 'description': 'Climate-KIC'},
    {'username': '@EIT_Digital', 'type': 'Digital', 'description': 'EIT Digital'},
    {'username': '@InnoEnergyEU', 'type': 'Energy', 'description': 'InnoEnergy'},
    {'username': '@EITHealth', 'type': 'Health', 'description': 'EIT Health'},
    {'username': '@EIT_Food', 'type': 'Food', 'description': 'EIT Food'},
    {'username': '@EITUrbanMob', 'type': 'Urban', 'description': 'EIT Urban Mobility'},
    {'username': '@EITRawMaterials', 'type': 'RawMaterials', 'description': 'EIT RawMaterials'},
]

# Default parameters
DEFAULT_MIN_K = 3  # Minimum co-classifications to establish connection
DEFAULT_MAX_LIST_SIZE = 500  # Filter out large lists (likely bot-generated)
DEFAULT_MAX_LISTS_PER_USER = 100  # Cap on lists per user
DEFAULT_MAX_RING1 = 10000  # Maximum users in ring 1
DEFAULT_MAX_RING2 = 100000  # Maximum users in ring 2


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Actor:
    """An actor (Twitter account) in the field."""
    username: str
    display_name: str = ""
    bio: str = ""
    followers: int = 0
    list_memberships: int = 0
    actor_type: str = ""  # individual, organization, media, etc.
    language: str = "en"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'username': self.username,
            'display_name': self.display_name,
            'bio': self.bio,
            'followers': self.followers,
            'list_memberships': self.list_memberships,
            'actor_type': self.actor_type,
            'language': self.language,
        }


@dataclass
class SubRegion:
    """A detected sub-region (community) in the field."""
    id: int
    label: str
    actors: List[str]
    size: int
    internal_density: float
    external_connections: int
    top_terms: List[Tuple[str, float]]  # (term, tfidf_score)
    languages: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'label': self.label,
            'size': self.size,
            'internal_density': self.internal_density,
            'external_connections': self.external_connections,
            'top_terms': [{'term': t, 'score': s} for t, s in self.top_terms],
            'languages': self.languages,
            'field_share': self.size / max(1, sum(1 for _ in self.actors)),
        }


# =============================================================================
# MENTION-BASED CO-CLASSIFICATION
# =============================================================================

class MentionCoClassifier:
    """
    Builds co-classification network from mention data.

    Since we don't have Twitter list data, we use mentions as a proxy:
    - Two actors are "co-classified" if they are mentioned together in tweets
    - The weight is the number of tweets where both are mentioned

    This captures "perceived relatedness" through co-mention patterns.
    """

    def __init__(self, min_co_mentions: int = 3):
        self.min_k = min_co_mentions
        self.actor_mentions: Dict[str, Set[str]] = defaultdict(set)  # tweet_id -> mentioned actors
        self.mention_counts: Dict[str, int] = Counter()
        self.co_mention_counts: Dict[Tuple[str, str], int] = Counter()
        self.actor_bios: Dict[str, str] = {}

    def add_tweet(self, tweet_id: str, mentions: List[str], author: str = None):
        """Add a tweet's mentions to build co-classification."""
        mentions_clean = [m.lower() for m in mentions if m]

        # Count individual mentions
        for m in mentions_clean:
            self.mention_counts[m] += 1

        # Count co-mentions (pairs mentioned in same tweet)
        mentions_sorted = sorted(set(mentions_clean))
        for i, m1 in enumerate(mentions_sorted):
            for m2 in mentions_sorted[i+1:]:
                key = (m1, m2)
                self.co_mention_counts[key] += 1

    def add_actor_bio(self, username: str, bio: str):
        """Store actor bio for text mining."""
        self.actor_bios[username.lower()] = bio

    def get_co_classifications(self, username: str) -> Dict[str, int]:
        """Get co-classification counts for a user."""
        username = username.lower()
        co_class = {}

        for (u1, u2), count in self.co_mention_counts.items():
            if u1 == username:
                co_class[u2] = count
            elif u2 == username:
                co_class[u1] = count

        return {u: c for u, c in co_class.items() if c >= self.min_k}

    def build_network(self, min_weight: int = None) -> 'nx.Graph':
        """Build NetworkX graph from co-classification data."""
        if not HAS_NETWORKX:
            raise ImportError("networkx required")

        min_w = min_weight or self.min_k
        G = nx.Graph()

        # Add nodes with mention count as attribute
        for actor, count in self.mention_counts.items():
            G.add_node(actor, mentions=count, bio=self.actor_bios.get(actor, ''))

        # Add edges with co-mention weight
        for (u1, u2), weight in self.co_mention_counts.items():
            if weight >= min_w:
                G.add_edge(u1, u2, weight=weight)

        return G


# =============================================================================
# TEXT MINING ON COMMUNITIES
# =============================================================================

class CommunityTextMiner:
    """
    Extracts characteristic terms for each community using TF-IDF.

    Based on: https://github.com/seinecle/TextMiningOnCommunities

    For each community:
    1. Concatenate all actor bios
    2. Compute TF-IDF against all communities
    3. Extract top terms that distinguish this community
    """

    def __init__(self, max_features: int = 1000, ngram_range: Tuple[int, int] = (1, 2)):
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.vectorizer = None
        self.tfidf_matrix = None
        self.feature_names = None

    def extract_terms(
        self,
        communities: List[Set[str]],
        actor_bios: Dict[str, str],
        top_n: int = 20,
        stopwords: Set[str] = None
    ) -> List[List[Tuple[str, float]]]:
        """
        Extract top terms for each community.

        Args:
            communities: List of sets, each containing actor usernames
            actor_bios: Dict mapping username to bio text
            top_n: Number of top terms to return per community
            stopwords: Additional stopwords to filter

        Returns:
            List of (term, score) tuples for each community
        """
        if not HAS_SKLEARN:
            # Fallback: simple word frequency
            return self._extract_terms_simple(communities, actor_bios, top_n)

        # Build document for each community (concatenated bios)
        documents = []
        for comm in communities:
            comm_text = ' '.join(
                actor_bios.get(actor.lower(), '')
                for actor in comm
            )
            documents.append(comm_text)

        if not any(documents):
            return [[] for _ in communities]

        # Configure TF-IDF
        stop_words = list(stopwords) if stopwords else 'english'
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            stop_words=stop_words,
            min_df=1,
            max_df=0.9,
        )

        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(documents)
            self.feature_names = self.vectorizer.get_feature_names_out()
        except ValueError:
            # Empty vocabulary
            return [[] for _ in communities]

        # Extract top terms for each community
        results = []
        for i in range(len(communities)):
            row = self.tfidf_matrix[i].toarray().flatten()
            top_indices = row.argsort()[-top_n:][::-1]
            terms = [
                (self.feature_names[idx], float(row[idx]))
                for idx in top_indices
                if row[idx] > 0
            ]
            results.append(terms)

        return results

    def _extract_terms_simple(
        self,
        communities: List[Set[str]],
        actor_bios: Dict[str, str],
        top_n: int
    ) -> List[List[Tuple[str, float]]]:
        """Simple word frequency fallback without sklearn."""
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
            'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he', 'him', 'his',
            'she', 'her', 'it', 'its', 'they', 'them', 'their', 'this', 'that',
            'these', 'those', 'what', 'which', 'who', 'whom', 'whose',
        }

        results = []
        for comm in communities:
            word_counts = Counter()
            for actor in comm:
                bio = actor_bios.get(actor.lower(), '')
                words = re.findall(r'\b[a-z]{3,}\b', bio.lower())
                word_counts.update(w for w in words if w not in stopwords)

            total = sum(word_counts.values()) or 1
            terms = [
                (word, count / total)
                for word, count in word_counts.most_common(top_n)
            ]
            results.append(terms)

        return results


# =============================================================================
# FIELD MAPPING PIPELINE
# =============================================================================

class FieldMapper:
    """
    Complete field mapping pipeline following Schiffer et al.

    Six-step procedure:
    1. Seed selection
    2. Network discovery (two-ring expansion)
    3. Denoising (random walk filtering)
    4. Network merging
    5. Visualization
    6. Sub-region identification
    """

    def __init__(
        self,
        min_k: int = DEFAULT_MIN_K,
        max_ring1: int = DEFAULT_MAX_RING1,
        max_ring2: int = DEFAULT_MAX_RING2,
    ):
        self.min_k = min_k
        self.max_ring1 = max_ring1
        self.max_ring2 = max_ring2

        self.seeds: List[Dict] = []
        self.co_classifier: Optional[MentionCoClassifier] = None
        self.network: Optional['nx.Graph'] = None
        self.communities: List[Set[str]] = []
        self.sub_regions: List[SubRegion] = []
        self.text_miner = CommunityTextMiner()

    def set_seeds(self, seeds: List[Dict]):
        """Set seed accounts for field discovery."""
        self.seeds = seeds
        print(f"Set {len(seeds)} seed accounts:")
        for s in seeds:
            print(f"  - {s['username']}: {s.get('description', '')}")

    def load_mention_data(self, tweets_df, bio_column: str = None):
        """
        Load mention data from DataFrame.

        Args:
            tweets_df: DataFrame with Tweet text and optionally bio info
            bio_column: Column containing user bios (if available)
        """
        print("Building co-classification from mention data...")

        self.co_classifier = MentionCoClassifier(min_co_mentions=self.min_k)

        for idx, row in tweets_df.iterrows():
            tweet_text = row.get('Tweet', row.get('text', ''))
            if not tweet_text:
                continue

            # Extract mentions
            mentions = re.findall(r'@(\w+)', str(tweet_text))
            mentions = ['@' + m.lower() for m in mentions]

            # Get author
            author = row.get('User Screen Name', row.get('user', ''))
            if author and not author.startswith('@'):
                author = '@' + author.lower()

            # Add to co-classifier
            self.co_classifier.add_tweet(str(idx), mentions, author)

            # Store bio if available
            if bio_column and bio_column in row:
                bio = row[bio_column]
                if author and bio:
                    self.co_classifier.add_actor_bio(author, str(bio))

        print(f"  Actors: {len(self.co_classifier.mention_counts):,}")
        print(f"  Co-mention pairs: {len(self.co_classifier.co_mention_counts):,}")

    def expand_from_seeds(self) -> Set[str]:
        """
        Step 2: Two-ring expansion from each seed.

        For each seed:
        - Ring 1: All actors co-classified with seed (>= min_k times)
        - Ring 2: All actors co-classified with Ring 1 actors
        """
        if not self.co_classifier:
            raise ValueError("Load mention data first")

        all_actors = set()
        seed_networks = {}

        for seed in self.seeds:
            username = seed['username'].lower()
            print(f"\nExpanding from {seed['username']}...")

            # Ring 1: Direct co-classifications
            ring1_counts = self.co_classifier.get_co_classifications(username)
            ring1 = set(ring1_counts.keys())

            # Cap ring 1 size
            if len(ring1) > self.max_ring1:
                sorted_users = sorted(ring1_counts.items(), key=lambda x: -x[1])
                ring1 = {u for u, _ in sorted_users[:self.max_ring1]}

            print(f"  Ring 1: {len(ring1)} actors")

            # Ring 2: Co-classifications of ring 1
            ring2 = set()
            for r1_user in ring1:
                r2_counts = self.co_classifier.get_co_classifications(r1_user)
                for user, count in r2_counts.items():
                    if user not in ring1 and user != username:
                        ring2.add(user)
                        if len(ring2) >= self.max_ring2:
                            break
                if len(ring2) >= self.max_ring2:
                    break

            print(f"  Ring 2: {len(ring2)} actors")

            seed_network = {username} | ring1 | ring2
            seed_networks[username] = seed_network
            all_actors |= seed_network

        print(f"\nTotal actors across all seeds: {len(all_actors):,}")
        return all_actors

    def build_network(self, actors: Set[str] = None):
        """
        Step 4: Build merged network.

        Creates NetworkX graph with co-classification edges.
        """
        if not HAS_NETWORKX:
            raise ImportError("networkx required")

        print("\nBuilding network...")

        # Build from co-classifier
        full_network = self.co_classifier.build_network(min_weight=self.min_k)

        # Filter to specified actors if provided
        if actors:
            self.network = full_network.subgraph(
                [n for n in full_network.nodes() if n in actors]
            ).copy()
        else:
            self.network = full_network

        print(f"  Nodes: {self.network.number_of_nodes():,}")
        print(f"  Edges: {self.network.number_of_edges():,}")
        print(f"  Density: {nx.density(self.network):.6f}")

    def denoise_random_walk(
        self,
        n_walks: int = 1000,
        walk_length: int = 2,
        threshold: float = 0.5
    ):
        """
        Step 3: Denoise network using random walks.

        Retains actors through which relational "traffic" flows,
        removing tangentially connected nodes.
        """
        if not self.network:
            raise ValueError("Build network first")

        print(f"\nDenoising with random walks...")
        print(f"  Walks: {n_walks}, Length: {walk_length}, Threshold: {threshold}")

        # Perform random walks from each seed
        visit_counts = Counter()

        for seed in self.seeds:
            username = seed['username'].lower()
            if username not in self.network:
                continue

            for _ in range(n_walks):
                current = username
                for _ in range(walk_length):
                    neighbors = list(self.network.neighbors(current))
                    if not neighbors:
                        break

                    # Weight by edge weight
                    weights = [
                        self.network[current][n].get('weight', 1)
                        for n in neighbors
                    ]
                    total = sum(weights)
                    probs = [w / total for w in weights]

                    current = np.random.choice(neighbors, p=probs)
                    visit_counts[current] += 1

        if not visit_counts:
            return

        # Filter by threshold
        avg_visits = np.mean(list(visit_counts.values()))
        retained = set(s['username'].lower() for s in self.seeds)
        retained |= {
            node for node, count in visit_counts.items()
            if count >= threshold * avg_visits
        }

        original_size = self.network.number_of_nodes()
        self.network = self.network.subgraph(retained).copy()

        print(f"  Retained: {self.network.number_of_nodes():,} / {original_size:,}")

    def detect_communities(self, resolution: float = 1.0):
        """
        Step 6: Detect sub-regions using Louvain algorithm.
        """
        if not self.network:
            raise ValueError("Build network first")

        print(f"\nDetecting communities (resolution={resolution})...")

        from networkx.algorithms.community import louvain_communities

        communities = louvain_communities(
            self.network,
            weight='weight',
            resolution=resolution,
            seed=42
        )

        self.communities = [set(c) for c in communities]

        # Compute modularity
        modularity = nx.algorithms.community.modularity(
            self.network, self.communities, weight='weight'
        )

        print(f"  Found {len(self.communities)} communities")
        print(f"  Modularity: {modularity:.4f}")

        # Sort by size
        self.communities.sort(key=len, reverse=True)

        sizes = [len(c) for c in self.communities[:10]]
        print(f"  Top 10 sizes: {sizes}")

        return modularity

    def characterize_sub_regions(self, top_terms: int = 15):
        """
        Extract characteristic terms for each sub-region.
        """
        if not self.communities:
            raise ValueError("Detect communities first")

        print(f"\nCharacterizing {len(self.communities)} sub-regions...")

        # Get actor bios
        actor_bios = self.co_classifier.actor_bios if self.co_classifier else {}

        # Extract terms using TF-IDF
        community_terms = self.text_miner.extract_terms(
            self.communities,
            actor_bios,
            top_n=top_terms
        )

        # Build SubRegion objects
        self.sub_regions = []
        for i, (comm, terms) in enumerate(zip(self.communities, community_terms)):
            # Compute internal density
            subgraph = self.network.subgraph(comm)
            n = len(comm)
            max_edges = n * (n - 1) / 2
            internal_density = subgraph.number_of_edges() / max_edges if max_edges > 0 else 0

            # Count external connections
            external = 0
            for node in comm:
                for neighbor in self.network.neighbors(node):
                    if neighbor not in comm:
                        external += 1

            # Detect languages from bios
            languages = Counter()
            for actor in comm:
                bio = actor_bios.get(actor, '')
                # Simple language detection by common words
                if any(w in bio.lower() for w in ['der', 'und', 'für', 'bei']):
                    languages['de'] += 1
                elif any(w in bio.lower() for w in ['le', 'la', 'les', 'pour', 'avec']):
                    languages['fr'] += 1
                elif any(w in bio.lower() for w in ['el', 'la', 'los', 'para', 'con']):
                    languages['es'] += 1
                elif any(w in bio.lower() for w in ['het', 'van', 'voor', 'met']):
                    languages['nl'] += 1
                else:
                    languages['en'] += 1

            # Generate label from top terms
            label_terms = [t for t, _ in terms[:3] if t]
            label = ' / '.join(label_terms) if label_terms else f"Community_{i}"

            sub_region = SubRegion(
                id=i,
                label=label,
                actors=list(comm),
                size=len(comm),
                internal_density=internal_density,
                external_connections=external,
                top_terms=terms,
                languages=dict(languages),
            )
            self.sub_regions.append(sub_region)

            if i < 10:  # Print top 10
                print(f"\n  [{i}] {label} (n={len(comm)})")
                print(f"      Density: {internal_density:.4f}, External: {external}")
                if terms:
                    term_str = ', '.join(t for t, _ in terms[:5])
                    print(f"      Terms: {term_str}")

    def export_results(self, output_dir: Path) -> Dict[str, Any]:
        """Export all results to JSON files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {
            'metadata': {
                'n_seeds': len(self.seeds),
                'min_k': self.min_k,
                'seeds': self.seeds,
            },
            'network': {
                'n_nodes': self.network.number_of_nodes() if self.network else 0,
                'n_edges': self.network.number_of_edges() if self.network else 0,
                'density': nx.density(self.network) if self.network else 0,
            },
            'communities': {
                'n_communities': len(self.communities),
                'sizes': [len(c) for c in self.communities],
            },
            'sub_regions': [sr.to_dict() for sr in self.sub_regions],
        }

        # Save main results
        with open(output_dir / 'field_mapping_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)

        # Save network as GraphML
        if self.network and HAS_NETWORKX:
            nx.write_graphml(self.network, output_dir / 'co_classification_network.graphml')

        # Save sub-region details
        with open(output_dir / 'sub_regions.json', 'w', encoding='utf-8') as f:
            json.dump([sr.to_dict() for sr in self.sub_regions], f, indent=2)

        print(f"\nResults exported to {output_dir}")
        return results


# =============================================================================
# MAIN PIPELINE RUNNER
# =============================================================================

def run_field_mapping(
    tweets_df,
    seeds: List[Dict] = None,
    output_dir: Path = None,
    min_k: int = DEFAULT_MIN_K,
    denoise: bool = True,
    resolution: float = 1.0,
) -> FieldMapper:
    """
    Run complete field mapping pipeline.

    Args:
        tweets_df: DataFrame with Tweet text
        seeds: List of seed account dicts (default: EIT seeds)
        output_dir: Directory for output files
        min_k: Minimum co-classifications for connection
        denoise: Whether to apply random walk denoising
        resolution: Louvain resolution parameter

    Returns:
        FieldMapper instance with results
    """
    print("=" * 60)
    print("FIELD MAPPING PIPELINE")
    print("=" * 60)

    mapper = FieldMapper(min_k=min_k)

    # Step 1: Set seeds
    mapper.set_seeds(seeds or EIT_SEEDS)

    # Step 2: Load data and expand
    mapper.load_mention_data(tweets_df)
    actors = mapper.expand_from_seeds()

    # Step 4: Build network
    mapper.build_network(actors)

    # Step 3: Denoise (optional)
    if denoise:
        mapper.denoise_random_walk()

    # Step 6: Detect communities
    mapper.detect_communities(resolution=resolution)

    # Characterize sub-regions
    mapper.characterize_sub_regions()

    # Export results
    if output_dir:
        mapper.export_results(output_dir)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    return mapper


if __name__ == "__main__":
    # Example usage
    print("Field Mapping Pipeline")
    print("Run with: from field_mapping import run_field_mapping")
