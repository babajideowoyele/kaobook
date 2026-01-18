"""
Field Mapping and Sub-Region Detection.

Identifies field structure through community detection
and characterizes sub-regions through content analysis.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, Counter
import numpy as np
import re

from .curation import CoCurationNetwork


@dataclass
class SubRegion:
    """
    A sub-region of the field identified through community detection.
    """
    id: int
    label: str
    members: List[str]
    size: int

    # Characteristic content
    top_terms: List[Tuple[str, float]]  # (term, tf-idf score)
    languages: Dict[str, int]  # language -> count

    # Network properties
    internal_density: float
    external_connections: int
    modularity_contribution: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'label': self.label,
            'members': self.members,
            'size': self.size,
            'top_terms': [{'term': t, 'score': s} for t, s in self.top_terms],
            'languages': self.languages,
            'internal_density': self.internal_density,
            'external_connections': self.external_connections,
            'modularity_contribution': self.modularity_contribution,
        }


class FieldNetwork:
    """
    Field network with sub-region structure.
    """

    def __init__(self, network: CoCurationNetwork):
        self.network = network
        self.communities: Dict[str, int] = {}  # node -> community ID
        self.sub_regions: List[SubRegion] = []

    def detect_communities(self, method: str = 'louvain') -> Dict[str, int]:
        """
        Detect communities using specified method.

        Parameters
        ----------
        method : str
            Detection method: 'louvain' or 'label_propagation'

        Returns
        -------
        dict
            Mapping from node to community ID
        """
        if method == 'louvain':
            self.communities = self._louvain()
        else:
            self.communities = self._label_propagation()

        return self.communities

    def _louvain(self) -> Dict[str, int]:
        """Louvain community detection."""
        adj, nodes = self.network.to_adjacency_matrix()
        n = len(nodes)

        if n == 0:
            return {}

        communities = {node: i for i, node in enumerate(nodes)}
        node_idx = {node: i for i, node in enumerate(nodes)}

        m = adj.sum() / 2
        if m == 0:
            return communities

        degrees = adj.sum(axis=1)

        improved = True
        max_iter = 100
        iteration = 0

        while improved and iteration < max_iter:
            improved = False
            iteration += 1

            for node in nodes:
                i = node_idx[node]
                current_comm = communities[node]

                neighbor_comms = set()
                for j in range(n):
                    if adj[i, j] > 0:
                        neighbor_comms.add(communities[nodes[j]])

                best_comm = current_comm
                best_delta = 0

                for comm in neighbor_comms:
                    if comm == current_comm:
                        continue

                    k_i_in = 0
                    k_i_out = 0
                    sum_in = 0
                    sum_out = 0

                    for other_node, other_comm in communities.items():
                        j = node_idx[other_node]
                        if other_comm == current_comm:
                            k_i_in += adj[i, j]
                            sum_in += degrees[j]
                        elif other_comm == comm:
                            k_i_out += adj[i, j]
                            sum_out += degrees[j]

                    delta = (k_i_out - k_i_in) / m - degrees[i] * (sum_out - sum_in) / (2 * m * m)

                    if delta > best_delta:
                        best_delta = delta
                        best_comm = comm

                if best_comm != current_comm:
                    communities[node] = best_comm
                    improved = True

        unique_comms = sorted(set(communities.values()))
        comm_map = {c: i for i, c in enumerate(unique_comms)}
        return {node: comm_map[comm] for node, comm in communities.items()}

    def _label_propagation(self) -> Dict[str, int]:
        """Label propagation clustering."""
        nodes = list(self.network.nodes)
        labels = {node: i for i, node in enumerate(nodes)}

        neighbors = defaultdict(lambda: defaultdict(float))
        for (u1, u2), weight in self.network.edges.items():
            neighbors[u1][u2] = weight
            neighbors[u2][u1] = weight

        changed = True
        max_iter = 50
        iteration = 0

        while changed and iteration < max_iter:
            changed = False
            iteration += 1

            for node in nodes:
                if not neighbors[node]:
                    continue

                label_weights = defaultdict(float)
                for neighbor, weight in neighbors[node].items():
                    label_weights[labels[neighbor]] += weight

                if label_weights:
                    best_label = max(label_weights, key=label_weights.get)
                    if best_label != labels[node]:
                        labels[node] = best_label
                        changed = True

        unique = sorted(set(labels.values()))
        label_map = {l: i for i, l in enumerate(unique)}
        return {node: label_map[labels[node]] for node in labels}

    def build_sub_regions(self, bios: Dict[str, str] = None) -> List[SubRegion]:
        """
        Build SubRegion objects from detected communities.

        Parameters
        ----------
        bios : dict, optional
            Mapping from username to bio text for content analysis

        Returns
        -------
        list
            List of SubRegion objects
        """
        if not self.communities:
            self.detect_communities()

        bios = bios or {}

        # Group by community
        comm_members = defaultdict(list)
        for node, comm in self.communities.items():
            comm_members[comm].append(node)

        self.sub_regions = []

        for comm_id, members in comm_members.items():
            # Content analysis
            member_bios = [bios.get(m, '') for m in members]
            top_terms = self._extract_top_terms(member_bios)
            languages = self._detect_languages(member_bios)

            # Network properties
            internal_edges = 0
            external_edges = 0

            for (u1, u2), weight in self.network.edges.items():
                u1_in = u1 in members
                u2_in = u2 in members

                if u1_in and u2_in:
                    internal_edges += 1
                elif u1_in or u2_in:
                    external_edges += 1

            max_internal = len(members) * (len(members) - 1) / 2
            density = internal_edges / max_internal if max_internal > 0 else 0

            # Generate label from top terms
            label = self._generate_label(top_terms)

            sub_region = SubRegion(
                id=comm_id,
                label=label,
                members=members,
                size=len(members),
                top_terms=top_terms[:10],
                languages=languages,
                internal_density=density,
                external_connections=external_edges,
                modularity_contribution=0.0,  # Computed separately
            )
            self.sub_regions.append(sub_region)

        return self.sub_regions

    def _extract_top_terms(self, texts: List[str], n_terms: int = 20) -> List[Tuple[str, float]]:
        """Extract top terms using TF-IDF-like scoring."""
        # Tokenize
        all_terms = []
        doc_terms = []

        for text in texts:
            text = text.lower()
            # Simple tokenization
            tokens = re.findall(r'\b[a-z]{3,}\b', text)
            # Remove common stop words
            stopwords = {'the', 'and', 'for', 'with', 'our', 'are', 'that', 'this',
                        'from', 'have', 'has', 'was', 'were', 'will', 'been', 'being',
                        'you', 'your', 'they', 'their', 'what', 'which', 'who', 'how'}
            tokens = [t for t in tokens if t not in stopwords]
            all_terms.extend(tokens)
            doc_terms.append(set(tokens))

        if not all_terms:
            return []

        # Term frequency
        tf = Counter(all_terms)

        # Document frequency
        df = defaultdict(int)
        for terms in doc_terms:
            for term in terms:
                df[term] += 1

        # TF-IDF-like score
        n_docs = len(texts)
        scores = {}
        for term, freq in tf.items():
            idf = np.log(n_docs / (df[term] + 1)) + 1
            scores[term] = freq * idf

        sorted_terms = sorted(scores.items(), key=lambda x: -x[1])
        return sorted_terms[:n_terms]

    def _detect_languages(self, texts: List[str]) -> Dict[str, int]:
        """Simple language detection based on common words."""
        lang_counts = defaultdict(int)

        # Simple heuristics
        de_words = {'und', 'der', 'die', 'das', 'ist', 'für', 'mit'}
        fr_words = {'et', 'le', 'la', 'les', 'de', 'du', 'des', 'pour'}
        es_words = {'de', 'el', 'la', 'los', 'las', 'para', 'con'}

        for text in texts:
            words = set(text.lower().split())

            if words & de_words:
                lang_counts['de'] += 1
            elif words & fr_words:
                lang_counts['fr'] += 1
            elif words & es_words:
                lang_counts['es'] += 1
            else:
                lang_counts['en'] += 1

        return dict(lang_counts)

    def _generate_label(self, top_terms: List[Tuple[str, float]]) -> str:
        """Generate human-readable label from top terms."""
        if not top_terms:
            return "Unknown"

        # Use top 2-3 terms
        label_terms = [t[0].title() for t in top_terms[:2]]
        return " & ".join(label_terms)

    def to_dict(self) -> Dict[str, Any]:
        """Export field to dictionary."""
        return {
            'network': self.network.to_dict(),
            'communities': self.communities,
            'sub_regions': [sr.to_dict() for sr in self.sub_regions],
            'n_sub_regions': len(self.sub_regions),
        }


class FieldMapper:
    """
    Maps innovation intermediary field from seed accounts.

    Implements the full six-step procedure:
    1. Seed selection
    2. Network discovery
    3. Denoising
    4. Network merging
    5. Visualization (external)
    6. Sub-region identification
    """

    def __init__(
        self,
        min_co_classification: int = 3,
        denoise_threshold: float = 0.5,
    ):
        self.min_k = min_co_classification
        self.denoise_threshold = denoise_threshold
        self.seed_networks: Dict[str, CoCurationNetwork] = {}
        self.merged_network: Optional[CoCurationNetwork] = None
        self.field: Optional[FieldNetwork] = None

    def map_field(
        self,
        seed_accounts: List[str],
        collector,  # ListCollector
        bios: Dict[str, str] = None,
    ) -> FieldNetwork:
        """
        Map field from seed accounts.

        Parameters
        ----------
        seed_accounts : list
            List of seed account usernames
        collector : ListCollector
            Collector with list membership data
        bios : dict, optional
            User bios for content analysis

        Returns
        -------
        FieldNetwork
            Mapped field with sub-regions
        """
        # Step 2-3: Discover and denoise per-seed networks
        for seed in seed_accounts:
            users = collector.expand_from_seed(seed)

            network = CoCurationNetwork(min_weight=self.min_k)
            network.build_from_collector(collector, users)

            # Denoise
            network = network.denoise_random_walk(
                seed,
                threshold=self.denoise_threshold
            )

            self.seed_networks[seed] = network

        # Step 4: Merge networks
        self.merged_network = CoCurationNetwork.merge(
            list(self.seed_networks.values())
        )

        # Step 6: Detect sub-regions
        self.field = FieldNetwork(self.merged_network)
        self.field.detect_communities()
        self.field.build_sub_regions(bios)

        return self.field

    def get_statistics(self) -> Dict[str, Any]:
        """Get field mapping statistics."""
        if not self.merged_network:
            return {}

        return {
            'n_seeds': len(self.seed_networks),
            'seed_network_sizes': {
                seed: net.get_statistics()['n_nodes']
                for seed, net in self.seed_networks.items()
            },
            'merged_network': self.merged_network.get_statistics(),
            'n_sub_regions': len(self.field.sub_regions) if self.field else 0,
        }
