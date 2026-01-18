"""
Network analysis for topic and author networks.

Provides centrality metrics, community detection, and network export.
Adapted from METAFRASIA/role_xray for standalone use.
"""

from __future__ import annotations

from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import collections
import logging

import numpy as np
import pandas as pd
import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class NetworkConfig:
    """Configuration for network analysis."""
    min_edge_weight: int = 1
    centrality_metrics: List[str] = None
    community_algorithm: str = 'louvain'
    normalize_weights: bool = True

    def __post_init__(self):
        if self.centrality_metrics is None:
            self.centrality_metrics = [
                'degree', 'betweenness', 'closeness', 'eigenvector', 'clustering'
            ]


class NetworkAnalyzer:
    """
    Analyze topic co-occurrence and author collaboration networks.

    Example:
        >>> analyzer = NetworkAnalyzer()
        >>> analyzer.build_from_topics(topics, documents)
        >>> centrality = analyzer.compute_centrality()
        >>> analyzer.export_pajek("network.net")
    """

    def __init__(self, config: Optional[NetworkConfig] = None):
        self.config = config or NetworkConfig()
        self._graph = None
        self._topic_labels = None

    @property
    def graph(self) -> nx.Graph:
        """Get the network graph."""
        if self._graph is None:
            raise ValueError("Network not built yet. Call build_from_topics first.")
        return self._graph

    def build_from_topics(
        self,
        topics: List[int],
        doc_ids: Optional[List[str]] = None,
        topic_labels: Optional[Dict[int, str]] = None
    ) -> 'NetworkAnalyzer':
        """Build topic co-occurrence network."""
        logger.info("Building topic co-occurrence network...")
        self._topic_labels = topic_labels or {}

        if doc_ids is not None:
            doc_topics = collections.defaultdict(set)
            for topic, doc_id in zip(topics, doc_ids):
                if topic != -1:
                    doc_topics[doc_id].add(topic)
        else:
            doc_topics = {i: {t} for i, t in enumerate(topics) if t != -1}

        cooccurrence = collections.Counter()
        for topics_set in doc_topics.values():
            topics_list = sorted(topics_set)
            for i, t1 in enumerate(topics_list):
                for t2 in topics_list[i + 1:]:
                    cooccurrence[(t1, t2)] += 1

        self._graph = nx.Graph()

        all_topics = set()
        for t1, t2 in cooccurrence.keys():
            all_topics.add(t1)
            all_topics.add(t2)

        for topic in all_topics:
            label = self._topic_labels.get(topic, f"Topic_{topic}")
            self._graph.add_node(topic, label=label)

        for (t1, t2), weight in cooccurrence.items():
            if weight >= self.config.min_edge_weight:
                self._graph.add_edge(t1, t2, weight=weight)

        logger.info(
            f"Built network with {self._graph.number_of_nodes()} nodes "
            f"and {self._graph.number_of_edges()} edges"
        )
        return self

    def build_from_authors(
        self,
        author_lists: List[List[str]],
        communities: Optional[Dict[str, str]] = None
    ) -> 'NetworkAnalyzer':
        """Build author collaboration network."""
        logger.info("Building author collaboration network...")
        self._graph = nx.Graph()
        collaboration_count = collections.Counter()

        for authors in author_lists:
            authors = sorted(set(authors))
            for i, a1 in enumerate(authors):
                for a2 in authors[i + 1:]:
                    collaboration_count[(a1, a2)] += 1

        all_authors = set()
        for a1, a2 in collaboration_count.keys():
            all_authors.add(a1)
            all_authors.add(a2)

        for author in all_authors:
            community = communities.get(author, 'unknown') if communities else 'unknown'
            self._graph.add_node(author, community=community)

        for (a1, a2), weight in collaboration_count.items():
            if weight >= self.config.min_edge_weight:
                self._graph.add_edge(a1, a2, weight=weight)

        logger.info(
            f"Built network with {self._graph.number_of_nodes()} authors "
            f"and {self._graph.number_of_edges()} collaborations"
        )
        return self

    def compute_centrality(self) -> pd.DataFrame:
        """Compute centrality metrics for all nodes."""
        logger.info("Computing centrality metrics...")

        if self.graph.number_of_nodes() == 0:
            return pd.DataFrame(columns=['node', 'degree_centrality'])

        results = {'node': list(self.graph.nodes())}

        if 'degree' in self.config.centrality_metrics:
            degree = dict(self.graph.degree(weight='weight'))
            results['degree_centrality'] = [degree[n] for n in results['node']]

        if 'betweenness' in self.config.centrality_metrics:
            betweenness = nx.betweenness_centrality(self.graph, weight='weight')
            results['betweenness_centrality'] = [betweenness[n] for n in results['node']]

        if 'closeness' in self.config.centrality_metrics:
            closeness = nx.closeness_centrality(self.graph)
            results['closeness_centrality'] = [closeness[n] for n in results['node']]

        if 'eigenvector' in self.config.centrality_metrics:
            try:
                eigenvector = nx.eigenvector_centrality(self.graph, max_iter=1000, weight='weight')
                results['eigenvector_centrality'] = [eigenvector[n] for n in results['node']]
            except nx.PowerIterationFailedConvergence:
                logger.warning("Eigenvector centrality did not converge")
                results['eigenvector_centrality'] = [0] * len(results['node'])

        if 'clustering' in self.config.centrality_metrics:
            clustering = nx.clustering(self.graph, weight='weight')
            results['clustering_coefficient'] = [clustering[n] for n in results['node']]

        df = pd.DataFrame(results)
        if self._topic_labels:
            df['label'] = df['node'].map(lambda x: self._topic_labels.get(x, f"Topic_{x}"))

        return df.sort_values('degree_centrality', ascending=False)

    def detect_communities(self) -> Dict[Any, int]:
        """Detect communities in the network."""
        if self.graph.number_of_nodes() == 0:
            return {}

        if self.config.community_algorithm == 'louvain':
            try:
                import community as community_louvain
                communities = community_louvain.best_partition(self.graph)
            except ImportError:
                logger.warning("python-louvain not installed, using label propagation")
                communities = self._label_propagation_communities()
        else:
            communities = self._label_propagation_communities()

        return communities

    def _label_propagation_communities(self) -> Dict[Any, int]:
        """Fallback community detection."""
        communities_gen = nx.algorithms.community.label_propagation_communities(self.graph)
        communities = {}
        for i, community in enumerate(communities_gen):
            for node in community:
                communities[node] = i
        return communities

    def get_network_stats(self) -> dict:
        """Get overall network statistics."""
        n_nodes = self.graph.number_of_nodes()
        n_edges = self.graph.number_of_edges()

        if n_nodes == 0:
            return {'nodes': 0, 'edges': 0, 'density': 0.0}

        return {
            'nodes': n_nodes,
            'edges': n_edges,
            'density': nx.density(self.graph),
            'avg_degree': sum(dict(self.graph.degree()).values()) / n_nodes,
            'avg_clustering': nx.average_clustering(self.graph),
            'is_connected': nx.is_connected(self.graph),
            'n_components': nx.number_connected_components(self.graph),
        }

    def export_pajek(self, path: str):
        """Export network in Pajek format."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        node_to_id = {node: i + 1 for i, node in enumerate(self.graph.nodes())}

        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"*Vertices {self.graph.number_of_nodes()}\n")
            for node in self.graph.nodes():
                label = self._topic_labels.get(node, str(node))
                f.write(f'{node_to_id[node]} "{label}"\n')

            f.write(f"*Edges\n")
            for u, v, data in self.graph.edges(data=True):
                weight = data.get('weight', 1)
                f.write(f"{node_to_id[u]} {node_to_id[v]} {weight}\n")

        logger.info(f"Exported Pajek network to {path}")
