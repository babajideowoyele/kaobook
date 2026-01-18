"""
Powell Framework Calculator.

Computes Associational vs Scientific vs Managerial positions based on
Powell's legitimacy vocabulary framework.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rolebox_triads.core.triad_config import get_powell_framework_config, TriadConfig
from rolebox_triads.core.normalizer import OrganizationTriadPosition, TriadNormalizer
from rolebox_triads.core.data_loader import RoleBoxDataLoader


class PowellFrameworkCalculator:
    """
    Computes Associational vs Scientific vs Managerial positions.

    Based on Powell's legitimacy framework vocabulary analysis of organizational text.
    """

    # Extended vocabulary lists (from existing triads.py)
    ASSOCIATIONAL_KEYWORDS = [
        "accountability", "advancement", "advocacy", "awareness", "care",
        "charity", "commitment", "common good", "compassion", "democracy",
        "development", "elimination", "emotion", "empowerment", "eradication",
        "ethics", "justice", "make a difference", "mission", "moral",
        "motivation", "participation", "principles", "quality of life",
        "relationship", "rights-based", "social benefit", "social change",
        "social movement", "social progress", "solidarity", "trust", "values",
        "vision", "voice", "civil society", "humanitarianism", "altruism",
        "political action", "positive action", "betterment", "social harmony",
        "ethical behavior", "human decency", "ideals", "society", "governance",
        "social structure", "well being", "human rights", "individuality",
        "collective action", "activism", "democratic values", "greater good",
        "social equality", "social reform", "human nature",
    ]

    SCIENTIFIC_KEYWORDS = [
        "analysis", "assessment", "causality", "control group", "correlation",
        "counterfactual", "criteria", "data", "design", "eligible population",
        "evaluation", "evidence", "experiment", "framework", "identification strategy",
        "indicators", "informed philanthropy", "logical framework model",
        "means of verification", "measurement", "measures", "meta-analysis",
        "methodology", "proven strategy", "quantification", "randomized control trials",
        "review", "root cause", "social impact analysis", "statistically significant",
        "survey", "tactics", "target group", "theory of change", "treatment effects",
        "statistical analysis", "inference", "empirical data", "experimental data",
        "hypothesis", "correlations", "experimental results", "empirical evidence",
        "observations", "statistical significance", "empirical research", "findings",
        "statistics", "data set", "scientific study", "scientific analysis",
        "mathematical model", "regression analysis", "causal relationships",
        "confidence intervals", "hypothesis testing", "theoretical model",
    ]

    MANAGERIAL_KEYWORDS = [
        "administrative overhead", "benchmarks", "best practice", "bottom line",
        "capacity", "certification", "constituent satisfaction", "cost-benefit",
        "earned income", "effectiveness", "efficiency", "exit strategy", "growth",
        "impact", "key performance indicators", "lessons learned", "leverage",
        "management", "market based", "milestones", "monitoring and evaluation",
        "objectives", "optimization", "outcome", "output", "performance",
        "productivity", "return on investment", "smart giving", "stakeholder satisfaction",
        "strategic", "swot", "transparency", "value proposition", "venture philanthropy",
        "profitability", "metrics", "scalability", "efficiencies", "trade offs",
        "resource allocation", "optimizing", "business case", "cost savings",
        "cost effectiveness", "roi", "capability", "feasibility", "risk analysis",
        "competitive advantage", "value creation", "cost reduction",
    ]

    def __init__(
        self,
        config: Optional[TriadConfig] = None,
        data_loader: Optional[RoleBoxDataLoader] = None,
    ):
        """
        Initialize the Powell Framework calculator.

        Args:
            config: Triad configuration (uses default Powell config if None)
            data_loader: RoleBox data loader instance
        """
        self.config = config or get_powell_framework_config()
        self.normalizer = TriadNormalizer(self.config)
        self.data_loader = data_loader

        # Lowercase all keywords for matching
        self.associational_vocab = [kw.lower() for kw in self.ASSOCIATIONAL_KEYWORDS]
        self.scientific_vocab = [kw.lower() for kw in self.SCIENTIFIC_KEYWORDS]
        self.managerial_vocab = [kw.lower() for kw in self.MANAGERIAL_KEYWORDS]

    def score_text(self, text: str) -> Tuple[int, int, int]:
        """
        Score text against Powell's three vocabularies.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (associational, scientific, managerial) keyword counts
        """
        text_lower = text.lower()

        associational = sum(1 for kw in self.associational_vocab if kw in text_lower)
        scientific = sum(1 for kw in self.scientific_vocab if kw in text_lower)
        managerial = sum(1 for kw in self.managerial_vocab if kw in text_lower)

        return (associational, scientific, managerial)

    def score_text_detailed(self, text: str) -> Dict[str, List[str]]:
        """
        Score text and return matched keywords.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with lists of matched keywords per dimension
        """
        text_lower = text.lower()

        return {
            "associational": [kw for kw in self.associational_vocab if kw in text_lower],
            "scientific": [kw for kw in self.scientific_vocab if kw in text_lower],
            "managerial": [kw for kw in self.managerial_vocab if kw in text_lower],
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
            OrganizationTriadPosition with Powell framework coordinates
        """
        scores = self.score_text(text)
        matched = self.score_text_detailed(text)

        position = self.normalizer.compute_position(
            org_id=org_id,
            org_name=org_name,
            raw_a=scores[0],  # Associational
            raw_b=scores[1],  # Scientific
            raw_c=scores[2],  # Managerial
            kic_sectors=kic_sectors,
            metadata={
                "matched_keywords": matched,
                "text_length": len(text),
            },
        )

        return position

    def calculate_from_triad_data(
        self,
        triad_data: Dict[str, Dict[str, Dict[str, int]]],
        org_metadata: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[OrganizationTriadPosition]:
        """
        Calculate positions from pre-computed triad data.

        Args:
            triad_data: Dictionary from triads.py output format:
                        {org_id: {dim1: {keyword: count}, dim2: {...}, dim3: {...}}}
            org_metadata: Optional metadata per organization

        Returns:
            List of OrganizationTriadPosition objects
        """
        positions = []
        org_metadata = org_metadata or {}

        for org_id, dimensions in triad_data.items():
            # Sum keyword counts per dimension
            dim1_count = sum(dimensions.get("dim1", {}).values())
            dim2_count = sum(dimensions.get("dim2", {}).values())
            dim3_count = sum(dimensions.get("dim3", {}).values())

            meta = org_metadata.get(org_id, {})

            position = self.normalizer.compute_position(
                org_id=org_id,
                org_name=meta.get("name", org_id),
                raw_a=dim1_count,  # Associational
                raw_b=dim2_count,  # Scientific
                raw_c=dim3_count,  # Managerial
                kic_sectors=meta.get("kic_sectors", []),
                metadata={
                    "keyword_counts": {
                        "associational": dim1_count,
                        "scientific": dim2_count,
                        "managerial": dim3_count,
                    },
                    "matched_keywords": dimensions,
                },
            )

            positions.append(position)

        return positions

    def calculate_positions(
        self, kic: str = "climate"
    ) -> List[OrganizationTriadPosition]:
        """
        Calculate positions for all organizations from RoleBox data.

        Args:
            kic: KIC identifier for data loading

        Returns:
            List of OrganizationTriadPosition objects
        """
        if self.data_loader is None:
            raise ValueError("data_loader required for calculate_positions")

        triad_data = self.data_loader.load_website_triad_data(kic)
        if triad_data is None:
            return []

        return self.calculate_from_triad_data(triad_data)

    def classify_interstitial(
        self, positions: List[OrganizationTriadPosition]
    ) -> List[OrganizationTriadPosition]:
        """
        Re-classify positions using median-based interstitial detection.

        Organizations with dominant proportion below median are classified as interstitial.

        Args:
            positions: List of positions to re-classify

        Returns:
            List with updated classifications
        """
        if not positions:
            return positions

        # Compute medians per dimension
        a_values = [p.coordinates[0] for p in positions]
        b_values = [p.coordinates[1] for p in positions]
        c_values = [p.coordinates[2] for p in positions]

        a_median = sorted(a_values)[len(a_values) // 2]
        b_median = sorted(b_values)[len(b_values) // 2]
        c_median = sorted(c_values)[len(c_values) // 2]

        medians = {
            f"dominant_{self.config.axis_a.key}": a_median,
            f"dominant_{self.config.axis_b.key}": b_median,
            f"dominant_{self.config.axis_c.key}": c_median,
        }

        # Re-classify based on median
        for pos in positions:
            if pos.classification in medians:
                dominant_coord = max(pos.coordinates)
                if dominant_coord < medians[pos.classification]:
                    pos.classification = "interstitial"

        return positions
