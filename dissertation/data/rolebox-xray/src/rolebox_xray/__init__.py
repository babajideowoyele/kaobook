"""
RoleBox-Xray: Scientific Literature & Bibliometric Pipeline

This module provides a thin wrapper around the METAFRASIA/role_xray package,
adapted for the RoleBox multimodal cartography framework.

Full implementation: https://github.com/arenabox/METAFRASIA
"""

__version__ = "0.1.0"

# Re-export from METAFRASIA role_xray if available
try:
    from role_xray import TopicModeler, TextProcessor, NetworkAnalyzer
    from role_xray.analysis import TemporalAnalyzer, CoherenceEvaluator
    from role_xray.visualization import TopicVisualizer, NetworkVisualizer

    HAS_ROLE_XRAY = True
except ImportError:
    HAS_ROLE_XRAY = False

    # Provide stub classes for documentation
    class TopicModeler:
        """Topic modeling with BERTopic. Install role_xray for full functionality."""
        pass

    class TextProcessor:
        """Text preprocessing. Install role_xray for full functionality."""
        pass

    class NetworkAnalyzer:
        """Network analysis. Install role_xray for full functionality."""
        pass


def check_installation():
    """Check if METAFRASIA/role_xray is properly installed."""
    if not HAS_ROLE_XRAY:
        print("Warning: role_xray not installed.")
        print("For full functionality, install from METAFRASIA:")
        print("  pip install -e /path/to/METAFRASIA")
        return False
    return True
