"""
RoleDNA: Python Discourse Network Analysis

A Python reimplementation of Philip Leifeld's Discourse Network Analyzer (DNA).
Provides network computation, matrix operations, and analysis tools for
discourse network methodology.

Full implementation: https://github.com/babajideowoyele/dna (python branch)
"""

__version__ = "0.1.0"

from .models.statement import Statement, StatementData
from .analysis.network import (
    NetworkConfig,
    Aggregation,
    Normalization,
    compute_network,
    compute_actor_congruence_network,
    compute_actor_conflict_network,
    compute_affiliation_network,
)
from .analysis.matrix import Matrix

__all__ = [
    "Statement",
    "StatementData",
    "NetworkConfig",
    "Aggregation",
    "Normalization",
    "Matrix",
    "compute_network",
    "compute_actor_congruence_network",
    "compute_actor_conflict_network",
    "compute_affiliation_network",
]
