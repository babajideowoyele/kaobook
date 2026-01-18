"""
Actor Types Calculator.

Computes Conforming vs Interfacing vs Bridging positions based on
field positioning from social network analysis.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rolebox_triads.core.triad_config import get_actor_types_config, TriadConfig
from rolebox_triads.core.normalizer import OrganizationTriadPosition, TriadNormalizer
from rolebox_triads.core.data_loader import RoleBoxDataLoader


class ActorTypesCalculator:
    """
    Computes Conforming vs Interfacing vs Bridging positions.

    Based on field positioning analysis from rolebox-social:
    - Conforming: High within-region ties, low cross-region ties
    - Interfacing: Balanced within/cross-region ties
    - Bridging: High cross-region ties, connects different communities
    """

    def __init__(
        self,
        config: Optional[TriadConfig] = None,
        data_loader: Optional[RoleBoxDataLoader] = None,
    ):
        """
        Initialize the Actor Types calculator.

        Args:
            config: Triad configuration (uses default Actor Types config if None)
            data_loader: RoleBox data loader instance
        """
        self.config = config or get_actor_types_config()
        self.normalizer = TriadNormalizer(self.config)
        self.data_loader = data_loader

        # Thresholds for classification
        self.bridging_threshold = 0.5  # Above this = bridging
        self.conforming_threshold = 0.2  # Below this = conforming

    def compute_from_field_analysis(
        self, field_data: Optional[Dict[str, Any]] = None
    ) -> List[OrganizationTriadPosition]:
        """
        Compute actor type positions from field analysis data.

        Args:
            field_data: Pre-loaded field analysis or None to load from data_loader

        Returns:
            List of OrganizationTriadPosition objects
        """
        if field_data is None and self.data_loader:
            field_data = self.data_loader.load_social_field_analysis()

        if field_data is None:
            return []

        positions = []

        # Extract bridging analysis if available
        bridging_data = field_data.get("bridging_analysis", {})
        actors = field_data.get("actors", {})
        communities = field_data.get("communities", {})

        for actor_id, actor_data in actors.items():
            # Get bridging score
            bridging_score = actor_data.get("bridging_score", 0)

            # Compute within-region and cross-region ties
            within_ties = actor_data.get("within_region_ties", 0)
            cross_ties = actor_data.get("cross_region_ties", 0)
            total_ties = within_ties + cross_ties

            if total_ties == 0:
                continue

            # Compute proportions
            cross_proportion = cross_ties / total_ties

            # Map to triad coordinates
            # Conforming: low cross-region proportion
            # Interfacing: balanced (mid-range)
            # Bridging: high cross-region proportion

            if cross_proportion < self.conforming_threshold:
                # Strongly conforming
                conforming = 1 - cross_proportion
                interfacing = cross_proportion
                bridging = 0
            elif cross_proportion > self.bridging_threshold:
                # Strongly bridging
                conforming = 0
                interfacing = 1 - cross_proportion
                bridging = cross_proportion
            else:
                # Interfacing zone
                conforming = max(0, self.conforming_threshold - cross_proportion + 0.1)
                bridging = max(0, cross_proportion - self.bridging_threshold + 0.1)
                interfacing = 1 - conforming - bridging

            # Normalize
            total = conforming + interfacing + bridging
            if total > 0:
                conforming /= total
                interfacing /= total
                bridging /= total

            position = self.normalizer.compute_position(
                org_id=actor_id,
                org_name=actor_data.get("name", actor_id),
                raw_a=conforming,
                raw_b=interfacing,
                raw_c=bridging,
                kic_sectors=actor_data.get("kic_sectors", []),
                metadata={
                    "within_ties": within_ties,
                    "cross_ties": cross_ties,
                    "cross_proportion": cross_proportion,
                    "original_bridging_score": bridging_score,
                    "home_region": actor_data.get("home_region"),
                    "connected_regions": actor_data.get("connected_regions", []),
                },
            )

            positions.append(position)

        return positions

    def compute_from_triangulation(
        self, triangulation_data: Optional[Dict[str, Any]] = None
    ) -> List[OrganizationTriadPosition]:
        """
        Compute positions from triangulation analysis data.

        Uses conforming_vs_interfacing classification from triangulation analysis.

        Args:
            triangulation_data: Pre-loaded triangulation analysis or None to load

        Returns:
            List of OrganizationTriadPosition objects
        """
        if triangulation_data is None and self.data_loader:
            triangulation_data = self.data_loader.load_social_triangulation_analysis()

        if triangulation_data is None:
            return []

        positions = []

        # Extract conforming vs interfacing classification
        conf_vs_int = triangulation_data.get("conforming_vs_interfacing", {})
        bridging_analysis = triangulation_data.get("bridging_analysis", {})

        # Get top bridging actors
        top_bridging = {
            actor["actor_id"]: actor
            for actor in bridging_analysis.get("top_bridging_actors", [])
        }

        # Process seed overlap (KIC-based)
        seed_overlap = triangulation_data.get("seed_overlap_jaccard", {})

        # Build positions from available data
        conforming_actors = conf_vs_int.get("conforming_actors", 0)
        interfacing_actors = conf_vs_int.get("interfacing_actors", 0)

        # For each bridging actor, create position
        for actor_id, actor_data in top_bridging.items():
            bridging_score = actor_data.get("bridging_score", 0.5)

            # High bridging score -> bridging position
            bridging = bridging_score
            interfacing = (1 - bridging_score) * 0.7
            conforming = (1 - bridging_score) * 0.3

            position = self.normalizer.compute_position(
                org_id=actor_id,
                org_name=actor_data.get("name", actor_id),
                raw_a=conforming,
                raw_b=interfacing,
                raw_c=bridging,
                metadata={
                    "bridging_score": bridging_score,
                    "home_region": actor_data.get("home_region"),
                    "connected_regions": actor_data.get("connected_regions", []),
                },
            )

            positions.append(position)

        return positions

    def calculate_positions(self) -> List[OrganizationTriadPosition]:
        """
        Compute actor type positions from RoleBox data.

        Tries field analysis first, falls back to triangulation analysis.

        Returns:
            List of OrganizationTriadPosition objects
        """
        # Try field analysis first
        positions = self.compute_from_field_analysis()

        if not positions:
            # Fall back to triangulation analysis
            positions = self.compute_from_triangulation()

        return positions

    def compute_from_network(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        communities: Dict[str, int],
    ) -> List[OrganizationTriadPosition]:
        """
        Compute positions directly from network data.

        Args:
            nodes: List of node dictionaries with 'id' and optional metadata
            edges: List of edge dictionaries with 'source' and 'target'
            communities: Mapping of node_id to community_id

        Returns:
            List of OrganizationTriadPosition objects
        """
        # Build adjacency and compute tie types
        node_ties = {node["id"]: {"within": 0, "cross": 0} for node in nodes}

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")

            if source not in communities or target not in communities:
                continue

            source_community = communities[source]
            target_community = communities[target]

            if source_community == target_community:
                # Within-region tie
                node_ties[source]["within"] += 1
                node_ties[target]["within"] += 1
            else:
                # Cross-region tie
                node_ties[source]["cross"] += 1
                node_ties[target]["cross"] += 1

        # Compute positions
        positions = []
        node_lookup = {node["id"]: node for node in nodes}

        for node_id, ties in node_ties.items():
            total = ties["within"] + ties["cross"]
            if total == 0:
                continue

            cross_prop = ties["cross"] / total

            # Map to triad
            if cross_prop < 0.2:
                conforming, interfacing, bridging = 0.8, 0.15, 0.05
            elif cross_prop > 0.6:
                conforming, interfacing, bridging = 0.05, 0.25, 0.7
            else:
                conforming, interfacing, bridging = 0.15, 0.7, 0.15

            node_data = node_lookup.get(node_id, {})

            position = self.normalizer.compute_position(
                org_id=node_id,
                org_name=node_data.get("label", node_id),
                raw_a=conforming,
                raw_b=interfacing,
                raw_c=bridging,
                kic_sectors=node_data.get("kic_sectors", []),
                metadata={
                    "within_ties": ties["within"],
                    "cross_ties": ties["cross"],
                    "community": communities.get(node_id),
                },
            )

            positions.append(position)

        return positions

    def get_archetype_examples(
        self, positions: List[OrganizationTriadPosition], n: int = 5
    ) -> Dict[str, List[OrganizationTriadPosition]]:
        """
        Get example organizations for each archetype.

        Args:
            positions: List of triad positions
            n: Number of examples per archetype

        Returns:
            Dictionary with lists of exemplar positions per archetype
        """
        archetypes = {
            "conforming": [],
            "interfacing": [],
            "bridging": [],
        }

        for pos in positions:
            if pos.classification == f"dominant_{self.config.axis_a.key}":
                archetypes["conforming"].append(pos)
            elif pos.classification == f"dominant_{self.config.axis_b.key}":
                archetypes["interfacing"].append(pos)
            elif pos.classification == f"dominant_{self.config.axis_c.key}":
                archetypes["bridging"].append(pos)

        # Sort each by confidence and take top n
        for archetype in archetypes:
            archetypes[archetype].sort(key=lambda p: p.confidence, reverse=True)
            archetypes[archetype] = archetypes[archetype][:n]

        return archetypes
