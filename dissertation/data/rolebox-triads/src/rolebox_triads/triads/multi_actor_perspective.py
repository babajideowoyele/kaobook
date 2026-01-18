"""
Multi-actor Perspective (MaP) Calculator.

Computes State vs Market vs Community positions based on
Avelino & Wittmayer's (2015) Multi-actor Perspective framework.

Reference:
    Avelino, F., & Wittmayer, J. M. (2016). Shifting Power Relations in
    Sustainability Transitions: A Multi-actor Perspective. Journal of
    Environmental Policy & Planning, 18(5), 628-649.
    https://doi.org/10.1080/1523908X.2015.1112259
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rolebox_triads.core.triad_config import get_multi_actor_perspective_config, TriadConfig
from rolebox_triads.core.normalizer import OrganizationTriadPosition, TriadNormalizer
from rolebox_triads.core.data_loader import RoleBoxDataLoader


class MultiActorPerspectiveCalculator:
    """
    Computes State vs Market vs Community positions.

    Based on Avelino & Wittmayer's Multi-actor Perspective (MaP) framework,
    which distinguishes between four sectors (state, market, community,
    third sector). For ternary visualization, we use the three primary sectors.

    Third sector organizations (e.g., universities, NGOs) can be positioned
    based on their hybrid characteristics drawing from multiple sectors.
    """

    # State sector vocabulary
    STATE_KEYWORDS = [
        # Core government terms
        "government", "ministry", "agency", "municipality", "public sector",
        "state", "federal", "national", "regional", "local authority",
        # Regulatory and policy
        "regulation", "policy", "legislation", "governance", "authority",
        "law", "statute", "ordinance", "decree", "directive",
        # Administrative
        "public administration", "city council", "parliament", "department",
        "bureau", "commission", "committee", "inspector", "ombudsman",
        # European governance
        "European Commission", "European Union", "EU", "member state",
        "intergovernmental", "supranational", "treaty",
        # Enforcement and compliance
        "licensing", "permit", "compliance", "oversight", "enforcement",
        "sanction", "penalty", "audit", "inspection", "certification",
        # Public finance
        "taxation", "subsidy", "grant", "public funding", "state-owned",
        "public budget", "fiscal", "treasury", "procurement", "tender",
        # Welfare state
        "welfare", "social security", "public service", "public good",
        "redistribution", "social protection", "public health",
    ]

    # Market sector vocabulary
    MARKET_KEYWORDS = [
        # Business entities
        "company", "corporation", "enterprise", "startup", "SME",
        "firm", "business", "venture", "conglomerate", "multinational",
        # Investment and finance
        "investor", "venture capital", "private equity", "profit",
        "revenue", "capital", "shares", "equity", "dividend", "IPO",
        "investment", "fund", "portfolio", "asset", "valuation",
        # Market dynamics
        "market share", "competition", "customer", "product", "service",
        "supply", "demand", "price", "market forces", "consumer",
        # Business strategy
        "business model", "commercial", "trade", "industry", "sector",
        "competitive advantage", "market position", "differentiation",
        # Corporate
        "shareholder", "stakeholder", "CEO", "board", "executive",
        "management", "corporate", "headquarters", "subsidiary",
        # Growth and scale
        "growth", "scale", "exit", "acquisition", "merger", "expansion",
        "incubator", "accelerator", "scaling", "market entry",
        # Market actors
        "private sector", "entrepreneur", "founder", "B2B", "B2C",
        "contractor", "supplier", "vendor", "client",
    ]

    # Community sector vocabulary
    COMMUNITY_KEYWORDS = [
        # Core community terms
        "community", "citizen", "resident", "inhabitant", "neighborhood",
        "local", "grassroots", "bottom-up", "place-based",
        # Civil society
        "civil society", "NGO", "association", "foundation", "charity",
        "non-profit", "voluntary", "third sector", "public interest",
        # Collective action
        "cooperative", "collective", "mutual", "shared ownership",
        "commons", "peer-to-peer", "solidarity", "mutual aid",
        # Participation
        "participation", "participatory", "co-creation", "engagement",
        "involvement", "voice", "empowerment", "deliberation",
        # Social movements
        "activism", "social movement", "advocacy", "campaign", "protest",
        "mobilization", "grassroots movement", "initiative",
        # Community organizations
        "volunteer", "volunteering", "community group", "civic",
        "faith-based", "membership", "club", "society",
        # Alternative economy
        "social enterprise", "cooperative", "crowdfunding", "community energy",
        "transition initiative", "local food", "housing cooperative",
        "community garden", "time bank", "local currency",
        # Social cohesion
        "social capital", "trust", "reciprocity", "belonging", "identity",
        "social bond", "network", "relationship", "community building",
    ]

    def __init__(
        self,
        config: Optional[TriadConfig] = None,
        data_loader: Optional[RoleBoxDataLoader] = None,
    ):
        """
        Initialize the Multi-actor Perspective calculator.

        Args:
            config: Triad configuration (uses default MaP config if None)
            data_loader: RoleBox data loader instance
        """
        self.config = config or get_multi_actor_perspective_config()
        self.normalizer = TriadNormalizer(self.config)
        self.data_loader = data_loader

        # Lowercase all keywords for matching
        self.state_vocab = [kw.lower() for kw in self.STATE_KEYWORDS]
        self.market_vocab = [kw.lower() for kw in self.MARKET_KEYWORDS]
        self.community_vocab = [kw.lower() for kw in self.COMMUNITY_KEYWORDS]

    def score_text(self, text: str) -> Tuple[int, int, int]:
        """
        Score text against MaP's three sector vocabularies.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (state, market, community) keyword counts
        """
        text_lower = text.lower()

        state = sum(1 for kw in self.state_vocab if kw in text_lower)
        market = sum(1 for kw in self.market_vocab if kw in text_lower)
        community = sum(1 for kw in self.community_vocab if kw in text_lower)

        return (state, market, community)

    def score_text_detailed(self, text: str) -> Dict[str, List[str]]:
        """
        Score text and return matched keywords.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with lists of matched keywords per sector
        """
        text_lower = text.lower()

        return {
            "state": [kw for kw in self.state_vocab if kw in text_lower],
            "market": [kw for kw in self.market_vocab if kw in text_lower],
            "community": [kw for kw in self.community_vocab if kw in text_lower],
        }

    def calculate_from_text(
        self,
        org_id: str,
        org_name: str,
        text: str,
        kic_sectors: Optional[List[str]] = None,
    ) -> OrganizationTriadPosition:
        """
        Calculate triad position from organization text.

        Args:
            org_id: Organization identifier
            org_name: Organization display name
            text: Text to analyze (website content, description, etc.)
            kic_sectors: Optional KIC affiliations

        Returns:
            OrganizationTriadPosition with MaP coordinates
        """
        scores = self.score_text(text)
        matched = self.score_text_detailed(text)

        position = self.normalizer.compute_position(
            org_id=org_id,
            org_name=org_name,
            raw_a=scores[0],  # State
            raw_b=scores[1],  # Market
            raw_c=scores[2],  # Community
            kic_sectors=kic_sectors,
            metadata={
                "matched_keywords": matched,
                "text_length": len(text),
            },
        )

        return position

    def calculate_from_corpus(
        self,
        corpus: List[Dict[str, Any]],
        id_field: str = "id",
        name_field: str = "title",
        text_field: str = "text",
        kic_field: Optional[str] = None,
    ) -> List[OrganizationTriadPosition]:
        """
        Calculate positions for a corpus of documents.

        Args:
            corpus: List of document dictionaries
            id_field: Field name for document ID
            name_field: Field name for display name
            text_field: Field name for text content
            kic_field: Optional field name for KIC sectors

        Returns:
            List of OrganizationTriadPosition objects
        """
        positions = []

        for doc in corpus:
            org_id = doc.get(id_field, "")
            org_name = doc.get(name_field, org_id)
            text = doc.get(text_field, "")
            kic_sectors = doc.get(kic_field, []) if kic_field else []

            if isinstance(kic_sectors, str):
                kic_sectors = [kic_sectors]

            if text:
                position = self.calculate_from_text(
                    org_id=str(org_id),
                    org_name=str(org_name),
                    text=text,
                    kic_sectors=kic_sectors,
                )
                positions.append(position)

        return positions

    def classify_third_sector(
        self,
        positions: List[OrganizationTriadPosition],
        threshold: float = 0.35,
    ) -> List[OrganizationTriadPosition]:
        """
        Identify potential third sector organizations.

        Third sector organizations in MaP framework sit between state and
        community (e.g., universities, research institutes, some NGOs).
        They are characterized by:
        - Low market orientation
        - Balanced state/community presence

        Args:
            positions: List of positions to analyze
            threshold: Maximum market score to be considered third sector

        Returns:
            Positions with updated metadata indicating third sector status
        """
        for pos in positions:
            market_score = pos.coordinates[1]  # Market is axis_b
            state_score = pos.coordinates[0]
            community_score = pos.coordinates[2]

            # Third sector: low market, balanced state/community
            is_third_sector = (
                market_score < threshold and
                abs(state_score - community_score) < 0.2
            )

            pos.metadata["is_third_sector"] = is_third_sector
            if is_third_sector:
                pos.metadata["sector_type"] = "third_sector"
            elif pos.classification == "dominant_state":
                pos.metadata["sector_type"] = "state"
            elif pos.classification == "dominant_market":
                pos.metadata["sector_type"] = "market"
            elif pos.classification == "dominant_community":
                pos.metadata["sector_type"] = "community"
            else:
                pos.metadata["sector_type"] = "hybrid"

        return positions

    def get_sector_distribution(
        self,
        positions: List[OrganizationTriadPosition],
    ) -> Dict[str, int]:
        """
        Get distribution of organizations across sectors.

        Args:
            positions: List of positions

        Returns:
            Dictionary with counts per sector type
        """
        distribution = {
            "state": 0,
            "market": 0,
            "community": 0,
            "third_sector": 0,
            "hybrid": 0,
        }

        for pos in positions:
            sector_type = pos.metadata.get("sector_type", "hybrid")
            if sector_type in distribution:
                distribution[sector_type] += 1

        return distribution
