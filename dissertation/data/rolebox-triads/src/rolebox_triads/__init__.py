"""
RoleBox Triads - Triad visualization framework for multimodal role constellation cartography.

This package provides tools for visualizing organizational positions in ternary space
across four triad types:
- Role Modalities: Claimed vs Attributed vs Enacted
- Powell Framework: Associational vs Scientific vs Managerial
- Actor Types: Conforming vs Interfacing vs Bridging
- Multi-actor Perspective: State vs Market vs Community (Avelino & Wittmayer 2015)
"""

from rolebox_triads.core.triad_config import (
    TriadType,
    TriadAxis,
    TriadConfig,
    get_role_modalities_config,
    get_powell_framework_config,
    get_actor_types_config,
    get_multi_actor_perspective_config,
    get_config_for_type,
)
from rolebox_triads.core.normalizer import TriadNormalizer, OrganizationTriadPosition, NetworkEdge
from rolebox_triads.core.data_loader import RoleBoxDataLoader
from rolebox_triads.visualization.html_generator import TriadHTMLGenerator

__version__ = "0.1.0"

__all__ = [
    # Core types
    "TriadType",
    "TriadAxis",
    "TriadConfig",
    "TriadNormalizer",
    "OrganizationTriadPosition",
    "NetworkEdge",
    "RoleBoxDataLoader",
    # Config getters
    "get_role_modalities_config",
    "get_powell_framework_config",
    "get_actor_types_config",
    "get_multi_actor_perspective_config",
    "get_config_for_type",
    # Visualization
    "TriadHTMLGenerator",
]
