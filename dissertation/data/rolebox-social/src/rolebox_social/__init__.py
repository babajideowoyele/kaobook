"""
RoleBox Social - Social Curation Field Mapping.

Implements field identification through Twitter list co-classification
following Schiffer et al. social curation methodology.
"""

from .curation import (
    TwitterAccount,
    TwitterList,
    CoCurationNetwork,
    ListCollector,
)
from .field import (
    FieldMapper,
    SubRegion,
    FieldNetwork,
)
from .analysis import (
    BridgingAnalyzer,
    TriangulationAnalyzer,
)

__version__ = "0.1.0"
__all__ = [
    "TwitterAccount",
    "TwitterList",
    "CoCurationNetwork",
    "ListCollector",
    "FieldMapper",
    "SubRegion",
    "FieldNetwork",
    "BridgingAnalyzer",
    "TriangulationAnalyzer",
]
