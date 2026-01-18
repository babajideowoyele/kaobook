"""
Role Modalities Calculator.

Computes Claimed (websites) vs Attributed (news) vs Enacted (Crunchbase) positions
for cross-modal triangulation.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json

from rolebox_triads.core.triad_config import get_role_modalities_config, TriadConfig
from rolebox_triads.core.normalizer import OrganizationTriadPosition, TriadNormalizer
from rolebox_triads.core.data_loader import RoleBoxDataLoader


class RoleModalitiesCalculator:
    """
    Computes Claimed vs Attributed vs Enacted positions.

    Data Sources:
    - Claimed: rolebox-websites (organizational self-presentation)
    - Attributed: rolebox-news (media portrayal via RIVETER-X)
    - Enacted: rolebox-crunchbase (investment/funding behavior)
    """

    def __init__(
        self,
        config: Optional[TriadConfig] = None,
        data_loader: Optional[RoleBoxDataLoader] = None,
    ):
        """
        Initialize the Role Modalities calculator.

        Args:
            config: Triad configuration (uses default Role Modalities config if None)
            data_loader: RoleBox data loader instance
        """
        self.config = config or get_role_modalities_config()
        self.normalizer = TriadNormalizer(self.config)
        self.data_loader = data_loader

        # Cached data
        self._claimed_scores: Dict[str, float] = {}
        self._attributed_scores: Dict[str, float] = {}
        self._enacted_scores: Dict[str, float] = {}
        self._org_metadata: Dict[str, Dict[str, Any]] = {}

    def compute_claimed_scores(
        self, website_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Extract role claim scores from website text.

        Uses TF-IDF or embedding-based role vocabulary scoring.

        Args:
            website_data: Pre-loaded website data or None to load from data_loader

        Returns:
            Dictionary mapping org_id to claimed role score
        """
        if website_data is None and self.data_loader:
            website_data = self.data_loader.load_website_field_positions()

        if website_data is None:
            return {}

        scores = {}

        # Extract from field positions (role vocabulary density)
        if "organizations" in website_data:
            for org_id, org_data in website_data["organizations"].items():
                # Score based on role vocabulary presence
                role_terms = org_data.get("role_terms", [])
                role_density = org_data.get("role_density", 0)

                # Combine term count and density
                score = len(role_terms) * (1 + role_density)
                scores[org_id] = score

                # Cache metadata
                self._org_metadata[org_id] = {
                    "name": org_data.get("name", org_id),
                    "kic_sectors": org_data.get("kic_sectors", []),
                }

        self._claimed_scores = scores
        return scores

    def compute_attributed_scores(
        self, news_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Extract attributed role scores from news articles.

        Uses RIVETER-X analysis and entity mention frequency.

        Args:
            news_data: Pre-loaded news data or None to load from data_loader

        Returns:
            Dictionary mapping org_id to attributed role score
        """
        if news_data is None and self.data_loader:
            news_data = self.data_loader.load_news_riveterx_analysis()

        if news_data is None:
            return {}

        scores = {}

        # Extract from RIVETER-X analysis
        if "entities" in news_data:
            for org_id, entity_data in news_data["entities"].items():
                # Score based on transformation agency and innovation positioning
                transformation = entity_data.get("transformation_agency", 0)
                innovation = entity_data.get("innovation_positioning", 0)
                mention_count = entity_data.get("mention_count", 1)

                # Combine scores weighted by mention frequency
                score = (transformation + innovation) * (1 + mention_count * 0.1)
                scores[org_id] = score

        self._attributed_scores = scores
        return scores

    def compute_enacted_scores(
        self, crunchbase_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Derive enacted role scores from Crunchbase data.

        Uses investment patterns, funding stages, and category alignment.

        Args:
            crunchbase_data: Pre-loaded Crunchbase data or None to load from data_loader

        Returns:
            Dictionary mapping org_id to enacted role score
        """
        if crunchbase_data is None and self.data_loader:
            crunchbase_data = self.data_loader.load_crunchbase_profiles()

        if crunchbase_data is None:
            return {}

        scores = {}

        # Extract from organization profiles
        if "organizations" in crunchbase_data:
            for org_id, org_data in crunchbase_data["organizations"].items():
                # Score based on funding, investment activity, and category diversity
                funding_rounds = org_data.get("funding_rounds", 0)
                total_funding = org_data.get("total_funding_usd", 0)
                num_investors = org_data.get("num_investors", 0)
                category_count = len(org_data.get("categories", []))

                # Normalize funding to log scale
                import math

                funding_log = math.log10(max(1, total_funding))

                # Combine factors
                score = (
                    funding_rounds * 2
                    + funding_log * 0.5
                    + num_investors * 0.5
                    + category_count
                )
                scores[org_id] = score

        self._enacted_scores = scores
        return scores

    def calculate_positions(self) -> List[OrganizationTriadPosition]:
        """
        Compute full triad positions for all organizations.

        Returns:
            List of OrganizationTriadPosition objects
        """
        # Compute scores for each modality
        claimed = self.compute_claimed_scores()
        attributed = self.compute_attributed_scores()
        enacted = self.compute_enacted_scores()

        # Get all organization IDs
        all_orgs = set(claimed.keys()) | set(attributed.keys()) | set(enacted.keys())

        positions = []

        for org_id in all_orgs:
            c = claimed.get(org_id, 0)
            a = attributed.get(org_id, 0)
            e = enacted.get(org_id, 0)

            # Skip if no data
            if c == 0 and a == 0 and e == 0:
                continue

            meta = self._org_metadata.get(org_id, {})

            position = self.normalizer.compute_position(
                org_id=org_id,
                org_name=meta.get("name", org_id),
                raw_a=c,  # Claimed
                raw_b=a,  # Attributed
                raw_c=e,  # Enacted
                kic_sectors=meta.get("kic_sectors", []),
                metadata={
                    "modality_scores": {
                        "claimed": c,
                        "attributed": a,
                        "enacted": e,
                    },
                    "data_sources": {
                        "has_website": c > 0,
                        "has_news": a > 0,
                        "has_crunchbase": e > 0,
                    },
                },
            )

            positions.append(position)

        return positions

    def calculate_from_vectors(
        self,
        claimed_vectors: Dict[str, List[float]],
        attributed_vectors: Dict[str, List[float]],
        enacted_vectors: Dict[str, List[float]],
        org_metadata: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[OrganizationTriadPosition]:
        """
        Calculate positions from embedding vectors.

        Uses vector norms or aggregated similarity scores.

        Args:
            claimed_vectors: Org ID -> embedding vector (from websites)
            attributed_vectors: Org ID -> embedding vector (from news)
            enacted_vectors: Org ID -> embedding vector (from Crunchbase)
            org_metadata: Optional metadata per organization

        Returns:
            List of OrganizationTriadPosition objects
        """
        import math

        org_metadata = org_metadata or {}

        def vector_magnitude(v: List[float]) -> float:
            return math.sqrt(sum(x * x for x in v)) if v else 0

        all_orgs = (
            set(claimed_vectors.keys())
            | set(attributed_vectors.keys())
            | set(enacted_vectors.keys())
        )

        positions = []

        for org_id in all_orgs:
            c_mag = vector_magnitude(claimed_vectors.get(org_id, []))
            a_mag = vector_magnitude(attributed_vectors.get(org_id, []))
            e_mag = vector_magnitude(enacted_vectors.get(org_id, []))

            if c_mag == 0 and a_mag == 0 and e_mag == 0:
                continue

            meta = org_metadata.get(org_id, {})

            position = self.normalizer.compute_position(
                org_id=org_id,
                org_name=meta.get("name", org_id),
                raw_a=c_mag,
                raw_b=a_mag,
                raw_c=e_mag,
                kic_sectors=meta.get("kic_sectors", []),
                metadata={"vector_magnitudes": {"claimed": c_mag, "attributed": a_mag, "enacted": e_mag}},
            )

            positions.append(position)

        return positions

    def detect_gaps(
        self, positions: List[OrganizationTriadPosition]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect claim-action and claim-perception gaps.

        Args:
            positions: List of triad positions

        Returns:
            Dictionary with gap analysis:
            - claim_action_gaps: Orgs with high claimed, low enacted
            - claim_perception_gaps: Orgs with high claimed, low attributed
            - perception_action_gaps: Orgs with high attributed, low enacted
        """
        gaps = {
            "claim_action_gaps": [],
            "claim_perception_gaps": [],
            "perception_action_gaps": [],
        }

        threshold = 0.2  # Gap threshold

        for pos in positions:
            claimed, attributed, enacted = pos.coordinates

            # Claim-Action gap: claims much higher than enactment
            if claimed - enacted > threshold:
                gaps["claim_action_gaps"].append(
                    {
                        "org_id": pos.org_id,
                        "org_name": pos.org_name,
                        "gap_size": claimed - enacted,
                        "claimed": claimed,
                        "enacted": enacted,
                    }
                )

            # Claim-Perception gap: claims much higher than attribution
            if claimed - attributed > threshold:
                gaps["claim_perception_gaps"].append(
                    {
                        "org_id": pos.org_id,
                        "org_name": pos.org_name,
                        "gap_size": claimed - attributed,
                        "claimed": claimed,
                        "attributed": attributed,
                    }
                )

            # Perception-Action gap: attribution much higher than enactment
            if attributed - enacted > threshold:
                gaps["perception_action_gaps"].append(
                    {
                        "org_id": pos.org_id,
                        "org_name": pos.org_name,
                        "gap_size": attributed - enacted,
                        "attributed": attributed,
                        "enacted": enacted,
                    }
                )

        # Sort by gap size
        for gap_type in gaps:
            gaps[gap_type].sort(key=lambda x: x["gap_size"], reverse=True)

        return gaps
