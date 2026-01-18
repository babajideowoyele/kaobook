"""
Co-occurrence Network and Clustering for Visual Register Analysis.

Builds co-occurrence networks from visual coding data and applies
community detection to identify characteristic visual configurations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import numpy as np

from .coding import VisualCoding, VisualCorpus


@dataclass
class CooccurrenceEdge:
    """Edge in co-occurrence network."""
    source: str
    target: str
    weight: float
    category_source: str  # e.g., 'participant', 'process', 'contact'
    category_target: str


class CooccurrenceNetwork:
    """
    Co-occurrence network of visual coding elements.

    Nodes are coding categories (participant types, process types, etc.)
    Edges connect categories that appear together in the same visual.
    """

    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: List[CooccurrenceEdge] = []
        self.node_categories: Dict[str, str] = {}  # node -> category
        self.edge_weights: Dict[Tuple[str, str], float] = defaultdict(float)

    def build_from_corpus(self, corpus: VisualCorpus):
        """Build network from visual corpus."""
        for coding in corpus.codings:
            elements = self._extract_elements(coding)
            self._add_cooccurrences(elements)

        # Convert to edge list
        self.edges = [
            CooccurrenceEdge(
                source=src,
                target=tgt,
                weight=weight,
                category_source=self.node_categories.get(src, 'unknown'),
                category_target=self.node_categories.get(tgt, 'unknown'),
            )
            for (src, tgt), weight in self.edge_weights.items()
        ]

    def _extract_elements(self, coding: VisualCoding) -> List[Tuple[str, str]]:
        """Extract all coded elements from a visual."""
        elements = []

        # Ideational
        for p in coding.ideational.participants:
            elements.append((p.value, 'participant'))
            self.nodes.add(p.value)
            self.node_categories[p.value] = 'participant'

        for p in coding.ideational.processes:
            elements.append((p.value, 'process'))
            self.nodes.add(p.value)
            self.node_categories[p.value] = 'process'

        if coding.ideational.setting:
            elements.append((coding.ideational.setting.value, 'setting'))
            self.nodes.add(coding.ideational.setting.value)
            self.node_categories[coding.ideational.setting.value] = 'setting'

        # Interpersonal
        elements.append((coding.interpersonal.contact.value, 'contact'))
        self.nodes.add(coding.interpersonal.contact.value)
        self.node_categories[coding.interpersonal.contact.value] = 'contact'

        elements.append((coding.interpersonal.distance.value, 'distance'))
        self.nodes.add(coding.interpersonal.distance.value)
        self.node_categories[coding.interpersonal.distance.value] = 'distance'

        elements.append((coding.interpersonal.vertical_angle.value, 'angle'))
        self.nodes.add(coding.interpersonal.vertical_angle.value)
        self.node_categories[coding.interpersonal.vertical_angle.value] = 'angle'

        elements.append((coding.interpersonal.coding_orientation.value, 'orientation'))
        self.nodes.add(coding.interpersonal.coding_orientation.value)
        self.node_categories[coding.interpersonal.coding_orientation.value] = 'orientation'

        return elements

    def _add_cooccurrences(self, elements: List[Tuple[str, str]]):
        """Add co-occurrence edges for all pairs of elements."""
        for i, (elem1, cat1) in enumerate(elements):
            for j, (elem2, cat2) in enumerate(elements):
                if i >= j:
                    continue

                # Create canonical edge key
                key = tuple(sorted([elem1, elem2]))
                self.edge_weights[key] += 1.0

    def to_adjacency_matrix(self) -> Tuple[np.ndarray, List[str]]:
        """Convert to adjacency matrix."""
        nodes = sorted(self.nodes)
        node_idx = {n: i for i, n in enumerate(nodes)}
        n = len(nodes)

        adj = np.zeros((n, n))
        for (src, tgt), weight in self.edge_weights.items():
            if src in node_idx and tgt in node_idx:
                i, j = node_idx[src], node_idx[tgt]
                adj[i, j] = weight
                adj[j, i] = weight

        return adj, nodes

    def get_statistics(self) -> Dict[str, Any]:
        """Compute network statistics."""
        return {
            'n_nodes': len(self.nodes),
            'n_edges': len(self.edges),
            'total_weight': sum(e.weight for e in self.edges),
            'nodes_by_category': self._count_by_category(),
        }

    def _count_by_category(self) -> Dict[str, int]:
        """Count nodes by category."""
        counts = defaultdict(int)
        for node, cat in self.node_categories.items():
            counts[cat] += 1
        return dict(counts)

    def to_dict(self) -> Dict[str, Any]:
        """Export network to dictionary."""
        return {
            'nodes': [
                {'id': n, 'category': self.node_categories.get(n, 'unknown')}
                for n in self.nodes
            ],
            'edges': [
                {
                    'source': e.source,
                    'target': e.target,
                    'weight': e.weight,
                }
                for e in self.edges
            ],
            'statistics': self.get_statistics(),
        }


class GazeClusterer:
    """
    Clusters visual codings to identify emergent gazes.

    Uses modularity-based community detection on the
    co-occurrence network.
    """

    def __init__(self, network: CooccurrenceNetwork):
        self.network = network
        self.communities: Dict[str, int] = {}

    def cluster(self, method: str = 'louvain') -> Dict[str, int]:
        """
        Cluster network nodes into communities.

        Parameters
        ----------
        method : str
            Clustering method: 'louvain' or 'label_propagation'

        Returns
        -------
        dict
            Mapping from node to community ID
        """
        if method == 'louvain':
            self.communities = self._louvain_clustering()
        else:
            self.communities = self._label_propagation()

        return self.communities

    def _louvain_clustering(self) -> Dict[str, int]:
        """Louvain community detection."""
        adj, nodes = self.network.to_adjacency_matrix()
        n = len(nodes)

        if n == 0:
            return {}

        # Initialize each node in its own community
        communities = {node: i for i, node in enumerate(nodes)}
        node_idx = {node: i for i, node in enumerate(nodes)}

        # Total edge weight
        m = adj.sum() / 2
        if m == 0:
            return communities

        # Node strengths
        strengths = adj.sum(axis=1)

        # Greedy optimization
        improved = True
        max_iter = 50
        iteration = 0

        while improved and iteration < max_iter:
            improved = False
            iteration += 1

            for node in nodes:
                i = node_idx[node]
                current_comm = communities[node]

                # Find neighboring communities
                neighbor_comms = set()
                for j in range(n):
                    if adj[i, j] > 0:
                        neighbor_comms.add(communities[nodes[j]])

                # Try moving to each neighbor community
                best_comm = current_comm
                best_delta = 0

                for comm in neighbor_comms:
                    if comm == current_comm:
                        continue

                    delta = self._modularity_delta(
                        i, current_comm, comm,
                        adj, strengths, m,
                        communities, nodes, node_idx
                    )

                    if delta > best_delta:
                        best_delta = delta
                        best_comm = comm

                if best_comm != current_comm:
                    communities[node] = best_comm
                    improved = True

        # Renumber to be contiguous
        unique_comms = sorted(set(communities.values()))
        comm_map = {c: i for i, c in enumerate(unique_comms)}
        return {node: comm_map[comm] for node, comm in communities.items()}

    def _modularity_delta(
        self, i: int, old_comm: int, new_comm: int,
        adj: np.ndarray, strengths: np.ndarray, m: float,
        communities: Dict[str, int], nodes: List[str],
        node_idx: Dict[str, int]
    ) -> float:
        """Compute modularity change from moving node i."""
        # Connections to old and new communities
        k_i_old = 0
        k_i_new = 0
        sum_old = 0
        sum_new = 0

        for node, comm in communities.items():
            j = node_idx[node]
            if comm == old_comm:
                k_i_old += adj[i, j]
                sum_old += strengths[j]
            elif comm == new_comm:
                k_i_new += adj[i, j]
                sum_new += strengths[j]

        # Modularity delta
        delta = (k_i_new - k_i_old) / m - strengths[i] * (sum_new - sum_old) / (2 * m * m)
        return delta

    def _label_propagation(self) -> Dict[str, int]:
        """Simple label propagation clustering."""
        nodes = list(self.network.nodes)
        labels = {node: i for i, node in enumerate(nodes)}

        # Build neighbor weights
        neighbors = defaultdict(lambda: defaultdict(float))
        for (src, tgt), weight in self.network.edge_weights.items():
            neighbors[src][tgt] = weight
            neighbors[tgt][src] = weight

        # Iterate
        changed = True
        max_iter = 50
        iteration = 0

        while changed and iteration < max_iter:
            changed = False
            iteration += 1

            for node in nodes:
                if not neighbors[node]:
                    continue

                # Count neighbor labels weighted
                label_weights = defaultdict(float)
                for neighbor, weight in neighbors[node].items():
                    label_weights[labels[neighbor]] += weight

                if label_weights:
                    best_label = max(label_weights, key=label_weights.get)
                    if best_label != labels[node]:
                        labels[node] = best_label
                        changed = True

        # Renumber
        unique = sorted(set(labels.values()))
        label_map = {l: i for i, l in enumerate(unique)}
        return {node: label_map[labels[node]] for node in labels}

    def get_community_profiles(self) -> Dict[int, Dict[str, Any]]:
        """Get profile of each community."""
        if not self.communities:
            return {}

        # Group nodes by community
        comm_nodes = defaultdict(list)
        for node, comm in self.communities.items():
            comm_nodes[comm].append(node)

        profiles = {}
        for comm_id, nodes in comm_nodes.items():
            # Categorize nodes
            categories = defaultdict(list)
            for node in nodes:
                cat = self.network.node_categories.get(node, 'unknown')
                categories[cat].append(node)

            profiles[comm_id] = {
                'n_nodes': len(nodes),
                'nodes': nodes,
                'by_category': dict(categories),
            }

        return profiles
