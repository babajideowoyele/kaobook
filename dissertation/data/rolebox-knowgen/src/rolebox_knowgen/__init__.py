"""
RoleBox KnowGen - Knowledge Generation Infrastructure.

Shared extraction and analysis infrastructure for all RoleBox modalities:
- NuExtract-based structured extraction (multilingual)
- Entity linking (Wikidata + fuzzy matching)
- Powell Triangle scoring
- Cross-modal entity resolution

Supports: Wikipedia, Websites, News Articles, Crunchbase, Social Media
"""

from .extraction import (
    NuExtractExtractor,
    NuExtractConfig,
    ExtractedInfo,
    EntityLinker,
    LinkedEntity,
    TriangleScorer,
)

__version__ = "0.1.0"

__all__ = [
    "NuExtractExtractor",
    "NuExtractConfig",
    "ExtractedInfo",
    "EntityLinker",
    "LinkedEntity",
    "TriangleScorer",
]
