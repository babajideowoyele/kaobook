"""
Social Curation and Co-Classification Network Construction.

Implements Twitter list co-classification for field discovery
following Schiffer et al. methodology.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import numpy as np


@dataclass
class TwitterAccount:
    """
    A Twitter account with profile information.
    """
    username: str
    display_name: str
    bio: str = ""
    followers_count: int = 0
    following_count: int = 0
    list_count: int = 0
    verified: bool = False

    # Derived attributes
    actor_type: str = ""  # individual, organization, media, etc.
    language: str = "en"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'username': self.username,
            'display_name': self.display_name,
            'bio': self.bio,
            'followers_count': self.followers_count,
            'following_count': self.following_count,
            'list_count': self.list_count,
            'verified': self.verified,
            'actor_type': self.actor_type,
            'language': self.language,
        }


@dataclass
class TwitterList:
    """
    A Twitter list with membership information.
    """
    list_id: str
    name: str
    description: str
    owner_username: str
    member_count: int
    members: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'list_id': self.list_id,
            'name': self.name,
            'description': self.description,
            'owner_username': self.owner_username,
            'member_count': self.member_count,
            'members': self.members,
        }


class ListCollector:
    """
    Collects Twitter list memberships for field discovery.

    Implements the six-step procedure:
    1. Seed selection
    2. Network discovery (two-ring expansion)
    3. Denoising (random walk filtering)
    4. Network merging
    5. Visualization
    6. Sub-region identification
    """

    def __init__(
        self,
        min_co_classification: int = 3,
        max_list_size: int = 500,
        max_lists_per_user: int = 100,
    ):
        self.min_k = min_co_classification
        self.max_list_size = max_list_size
        self.max_lists_per_user = max_lists_per_user

        self.accounts: Dict[str, TwitterAccount] = {}
        self.lists: Dict[str, TwitterList] = {}
        self.user_lists: Dict[str, Set[str]] = defaultdict(set)

    def add_account(self, account: TwitterAccount):
        """Add an account to the collection."""
        self.accounts[account.username] = account

    def add_list(self, twitter_list: TwitterList):
        """Add a list and update memberships."""
        if twitter_list.member_count > self.max_list_size:
            return

        self.lists[twitter_list.list_id] = twitter_list
        for member in twitter_list.members:
            self.user_lists[member].add(twitter_list.list_id)

    def get_co_classifications(self, username: str) -> Dict[str, int]:
        """Get co-classification counts for a user."""
        user_list_ids = self.user_lists.get(username, set())
        co_class_counts = defaultdict(int)

        for list_id in user_list_ids:
            if list_id not in self.lists:
                continue
            for member in self.lists[list_id].members:
                if member != username:
                    co_class_counts[member] += 1

        return dict(co_class_counts)

    def expand_from_seed(
        self,
        seed_username: str,
        max_ring1: int = 10000,
        max_ring2: int = 100000,
    ) -> Set[str]:
        """Expand network from a seed account."""
        ring1_counts = self.get_co_classifications(seed_username)
        ring1 = {u for u, count in ring1_counts.items() if count >= self.min_k}

        if len(ring1) > max_ring1:
            sorted_users = sorted(ring1_counts.items(), key=lambda x: -x[1])
            ring1 = {u for u, _ in sorted_users[:max_ring1] if ring1_counts[u] >= self.min_k}

        ring2 = set()
        for r1_user in ring1:
            r2_counts = self.get_co_classifications(r1_user)
            for user, count in r2_counts.items():
                if count >= self.min_k and user not in ring1:
                    ring2.add(user)
                    if len(ring2) >= max_ring2:
                        break

        return {seed_username} | ring1 | ring2


class CoCurationNetwork:
    """
    Network of actors connected by co-classification.
    """

    def __init__(self, min_weight: int = 3):
        self.min_weight = min_weight
        self.nodes: Set[str] = set()
        self.edges: Dict[Tuple[str, str], int] = {}
        self.node_attributes: Dict[str, Dict[str, Any]] = {}

    def add_node(self, username: str, attributes: Optional[Dict[str, Any]] = None):
        """Add a node with optional attributes."""
        self.nodes.add(username)
        if attributes:
            self.node_attributes[username] = attributes

    def add_edge(self, user1: str, user2: str, weight: int):
        """Add or update an edge."""
        if weight < self.min_weight:
            return
        self.nodes.add(user1)
        self.nodes.add(user2)
        key = tuple(sorted([user1, user2]))
        self.edges[key] = max(self.edges.get(key, 0), weight)

    def build_from_collector(self, collector: ListCollector, users: Set[str]):
        """Build network from collector for specified users."""
        for username in users:
            if username in collector.accounts:
                self.add_node(username, collector.accounts[username].to_dict())
            else:
                self.add_node(username)

        for user1 in users:
            co_class = collector.get_co_classifications(user1)
            for user2, count in co_class.items():
                if user2 in users and count >= self.min_weight:
                    self.add_edge(user1, user2, count)

    def denoise_random_walk(
        self,
        seed: str,
        n_walks: int = 1000,
        walk_length: int = 2,
        threshold: float = 0.5,
    ) -> 'CoCurationNetwork':
        """Denoise network using random walks."""
        if seed not in self.nodes:
            return self

        neighbors = defaultdict(list)
        for (u1, u2), weight in self.edges.items():
            neighbors[u1].append((u2, weight))
            neighbors[u2].append((u1, weight))

        visit_counts = defaultdict(int)
        for _ in range(n_walks):
            current = seed
            for _ in range(walk_length):
                if not neighbors[current]:
                    break
                neighs = neighbors[current]
                weights = [w for _, w in neighs]
                total = sum(weights)
                probs = [w / total for w in weights]

                r = np.random.random()
                cumsum = 0
                for (neigh, _), p in zip(neighs, probs):
                    cumsum += p
                    if r <= cumsum:
                        current = neigh
                        break
                visit_counts[current] += 1

        if not visit_counts:
            return self

        avg_visits = np.mean(list(visit_counts.values()))
        retained = {seed} | {
            node for node, count in visit_counts.items()
            if count >= threshold * avg_visits
        }

        filtered = CoCurationNetwork(min_weight=self.min_weight)
        for node in retained:
            if node in self.node_attributes:
                filtered.add_node(node, self.node_attributes[node])
            else:
                filtered.add_node(node)

        for (u1, u2), weight in self.edges.items():
            if u1 in retained and u2 in retained:
                filtered.add_edge(u1, u2, weight)

        return filtered

    def to_adjacency_matrix(self) -> Tuple[np.ndarray, List[str]]:
        """Convert to adjacency matrix."""
        nodes = sorted(self.nodes)
        node_idx = {n: i for i, n in enumerate(nodes)}
        n = len(nodes)
        adj = np.zeros((n, n))
        for (u1, u2), weight in self.edges.items():
            i, j = node_idx[u1], node_idx[u2]
            adj[i, j] = weight
            adj[j, i] = weight
        return adj, nodes

    def get_statistics(self) -> Dict[str, Any]:
        """Compute network statistics."""
        if not self.nodes:
            return {}

        n_nodes = len(self.nodes)
        n_edges = len(self.edges)
        max_edges = n_nodes * (n_nodes - 1) / 2

        degrees = defaultdict(int)
        for (u1, u2), _ in self.edges.items():
            degrees[u1] += 1
            degrees[u2] += 1

        degree_values = list(degrees.values()) if degrees else [0]

        return {
            'n_nodes': n_nodes,
            'n_edges': n_edges,
            'density': n_edges / max_edges if max_edges > 0 else 0,
            'avg_degree': np.mean(degree_values),
            'max_degree': max(degree_values),
            'total_weight': sum(self.edges.values()),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Export network to dictionary."""
        return {
            'nodes': [{'id': n, **self.node_attributes.get(n, {})} for n in self.nodes],
            'edges': [{'source': e[0], 'target': e[1], 'weight': w} for e, w in self.edges.items()],
            'statistics': self.get_statistics(),
        }

    @classmethod
    def merge(cls, networks: List['CoCurationNetwork']) -> 'CoCurationNetwork':
        """Merge multiple networks."""
        merged = cls(min_weight=min(n.min_weight for n in networks))
        for net in networks:
            for node in net.nodes:
                if node in net.node_attributes:
                    merged.add_node(node, net.node_attributes[node])
                else:
                    merged.add_node(node)
            for (u1, u2), weight in net.edges.items():
                merged.add_edge(u1, u2, weight)
        return merged
