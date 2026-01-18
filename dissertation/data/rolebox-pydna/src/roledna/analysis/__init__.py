"""Analysis modules for RoleDNA."""

from .matrix import Matrix
from .network import (
    NetworkConfig,
    Aggregation,
    Normalization,
    DuplicateHandling,
    compute_network,
    compute_actor_congruence_network,
    compute_actor_conflict_network,
    compute_affiliation_network,
)

__all__ = [
    "Matrix",
    "NetworkConfig",
    "Aggregation",
    "Normalization",
    "DuplicateHandling",
    "compute_network",
    "compute_actor_congruence_network",
    "compute_actor_conflict_network",
    "compute_affiliation_network",
]
