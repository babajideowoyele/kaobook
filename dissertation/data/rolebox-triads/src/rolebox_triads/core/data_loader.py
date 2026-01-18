"""
Data loader for RoleBox modules.

Unified data loading from rolebox-websites, rolebox-news, rolebox-crunchbase, and rolebox-social.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class RoleBoxPaths:
    """Paths to RoleBox module directories."""

    websites: Path
    news: Path
    crunchbase: Path
    social: Path
    visual: Path

    @classmethod
    def from_base(cls, base_path: Path) -> "RoleBoxPaths":
        """Create paths from base dissertation/data directory."""
        return cls(
            websites=base_path / "rolebox-websites",
            news=base_path / "rolebox-news",
            crunchbase=base_path / "rolebox-crunchbase",
            social=base_path / "rolebox-social",
            visual=base_path / "rolebox-visual",
        )


class RoleBoxDataLoader:
    """
    Unified data loader for all RoleBox modules.

    Provides consistent access to data from:
    - rolebox-websites: Website text and field positions
    - rolebox-news: News article analysis
    - rolebox-crunchbase: Investment and funding data
    - rolebox-social: Social network data and field analysis
    - rolebox-visual: Visual register analysis
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the data loader.

        Args:
            base_path: Path to dissertation/data directory.
                      If None, attempts to auto-detect.
        """
        if base_path is None:
            # Try to auto-detect from current file location
            base_path = Path(__file__).parent.parent.parent.parent.parent
            if not (base_path / "rolebox-social").exists():
                base_path = Path.cwd()

        self.base_path = Path(base_path)
        self.paths = RoleBoxPaths.from_base(self.base_path)
        self._cache: Dict[str, Any] = {}

    def _load_json(self, path: Path, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Load JSON file with optional caching."""
        cache_key = str(path)
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if use_cache:
                self._cache[cache_key] = data
            return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load {path}: {e}")
            return None

    def clear_cache(self):
        """Clear the data cache."""
        self._cache.clear()

    # =========================================================================
    # Website Data (rolebox-websites)
    # =========================================================================

    def load_website_field_positions(
        self, kic: str = "climate"
    ) -> Optional[Dict[str, Any]]:
        """
        Load field positions from website analysis.

        Args:
            kic: KIC identifier (climate, digital, etc.)

        Returns:
            Dictionary with field position data or None
        """
        path = self.paths.websites / "outputs" / kic / "field_positions.json"
        return self._load_json(path)

    def load_website_triad_data(self, kic: str = "climate") -> Optional[Dict[str, Any]]:
        """
        Load triad data (Powell framework scores) from website analysis.

        Args:
            kic: KIC identifier

        Returns:
            Dictionary with triad scores per organization
        """
        path = self.paths.websites / "outputs" / kic / "triad_data_powell_dict.json"
        return self._load_json(path)

    def load_website_hyperlinks(self, kic: str = "climate") -> Optional[Dict[str, List[str]]]:
        """
        Load hyperlink relationships between organizations.

        Args:
            kic: KIC identifier

        Returns:
            Dictionary mapping org_id to list of linked org_ids
        """
        path = self.paths.websites / "outputs" / kic / "user2rel.json"
        return self._load_json(path)

    # =========================================================================
    # News Data (rolebox-news)
    # =========================================================================

    def load_news_riveterx_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Load RIVETER-X discourse analysis results.

        Returns:
            Dictionary with entity discourse scores
        """
        path = self.paths.news / "outputs" / "riveterx_analysis.json"
        return self._load_json(path)

    def load_news_entity_mentions(self) -> Optional[Dict[str, Any]]:
        """
        Load entity mention counts and contexts.

        Returns:
            Dictionary with entity mention data
        """
        path = self.paths.news / "outputs" / "entity_mentions.json"
        return self._load_json(path)

    # =========================================================================
    # Crunchbase Data (rolebox-crunchbase)
    # =========================================================================

    def load_crunchbase_profiles(self) -> Optional[Dict[str, Any]]:
        """
        Load organization profiles from Crunchbase.

        Returns:
            Dictionary with organization data including funding, categories, etc.
        """
        path = self.paths.crunchbase / "outputs" / "organization_profiles.json"
        return self._load_json(path)

    def load_crunchbase_triangulation(self) -> Optional[Dict[str, Any]]:
        """
        Load cross-modal triangulation results.

        Returns:
            Dictionary with triangulation analysis
        """
        path = self.paths.crunchbase / "outputs" / "triangulation_results.json"
        return self._load_json(path)

    def load_crunchbase_cluster_profiles(self) -> Optional[Dict[str, Any]]:
        """
        Load venture cluster profiles.

        Returns:
            Dictionary with cluster analysis results
        """
        path = self.paths.crunchbase / "outputs" / "cluster_profiles.json"
        return self._load_json(path)

    # =========================================================================
    # Social Data (rolebox-social)
    # =========================================================================

    def load_social_field_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Load field analysis with sub-regions and community structure.

        Returns:
            Dictionary with field structure data
        """
        path = self.paths.social / "data" / "outputs" / "field_analysis.json"
        return self._load_json(path)

    def load_social_triangulation_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Load triangulation analysis (sociotype to sub-region mapping).

        Returns:
            Dictionary with triangulation validation results
        """
        path = self.paths.social / "data" / "outputs" / "triangulation_analysis.json"
        return self._load_json(path)

    def load_social_network_data(self) -> Optional[Dict[str, Any]]:
        """
        Load network data for visualization.

        Returns:
            Dictionary with nodes and edges for network visualization
        """
        path = self.paths.social / "ui" / "network_data.json"
        return self._load_json(path)

    def load_social_community_data(self) -> Optional[Dict[str, Any]]:
        """
        Load community detection results.

        Returns:
            Dictionary with community assignments
        """
        path = self.paths.social / "ui" / "community_data.json"
        return self._load_json(path)

    # =========================================================================
    # Visual Data (rolebox-visual)
    # =========================================================================

    def load_visual_gaze_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Load gaze analysis results.

        Returns:
            Dictionary with visual register analysis
        """
        path = self.paths.visual / "data" / "outputs" / "gaze_analysis.json"
        return self._load_json(path)

    def load_visual_cooccurrence_network(self) -> Optional[Dict[str, Any]]:
        """
        Load visual element co-occurrence network.

        Returns:
            Dictionary with visual element network
        """
        path = self.paths.visual / "data" / "outputs" / "cooccurrence_network.json"
        return self._load_json(path)

    # =========================================================================
    # Cross-Modal Integration
    # =========================================================================

    def get_organization_ids(self) -> List[str]:
        """
        Get list of all organization IDs across modalities.

        Returns:
            List of unique organization identifiers
        """
        org_ids = set()

        # From field analysis
        field_data = self.load_social_field_analysis()
        if field_data and "actors" in field_data:
            org_ids.update(field_data["actors"].keys())

        # From Crunchbase
        cb_data = self.load_crunchbase_profiles()
        if cb_data and "organizations" in cb_data:
            org_ids.update(cb_data["organizations"].keys())

        # From websites
        website_data = self.load_website_field_positions()
        if website_data and "organizations" in website_data:
            org_ids.update(website_data["organizations"].keys())

        return sorted(org_ids)

    def get_kic_sectors(self) -> List[str]:
        """
        Get list of available KIC sectors.

        Returns:
            List of KIC sector names
        """
        return [
            "Climate-KIC",
            "EIT Digital",
            "EIT Health",
            "EIT InnoEnergy",
            "EIT Food",
            "EIT RawMaterials",
            "EIT Urban Mobility",
            "EIT Manufacturing",
            "EIT Culture & Creativity",
        ]

    def get_kic_color(self, kic: str) -> str:
        """
        Get the standard color for a KIC sector.

        Args:
            kic: KIC sector name

        Returns:
            Hex color code
        """
        colors = {
            "Climate-KIC": "#28a745",
            "EIT Digital": "#007bff",
            "EIT Health": "#dc3545",
            "EIT InnoEnergy": "#6f42c1",
            "EIT Food": "#20c997",
            "EIT RawMaterials": "#fd7e14",
            "EIT Urban Mobility": "#343a40",
            "EIT Manufacturing": "#e83e8c",
            "EIT Culture & Creativity": "#17a2b8",
        }
        return colors.get(kic, "#999999")
