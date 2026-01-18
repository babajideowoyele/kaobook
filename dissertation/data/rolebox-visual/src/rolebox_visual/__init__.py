"""
RoleBox Visual - Visual Register Analysis for Innovation Intermediaries.

Implements social semiotic analysis of visual communications following
Jancsary et al. (2018) metafunction framework.
"""

from .coding import (
    VisualCoding,
    IdeationalMetafunction,
    InterpersonalMetafunction,
    TextualMetafunction,
    CodingOrientation,
    ContactLevel,
    SocialDistance,
    VerticalAngle,
)
from .analysis import (
    GazeDetector,
    VisualRegisterAnalyzer,
    Gaze,
)
from .clustering import (
    CooccurrenceNetwork,
    GazeClusterer,
)

__version__ = "0.1.0"
__all__ = [
    "VisualCoding",
    "IdeationalMetafunction",
    "InterpersonalMetafunction",
    "TextualMetafunction",
    "CodingOrientation",
    "ContactLevel",
    "SocialDistance",
    "VerticalAngle",
    "GazeDetector",
    "VisualRegisterAnalyzer",
    "Gaze",
    "CooccurrenceNetwork",
    "GazeClusterer",
]
