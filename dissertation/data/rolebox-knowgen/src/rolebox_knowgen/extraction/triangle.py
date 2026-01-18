"""
Powell Triangle Scorer.

Classifies entities based on legitimacy vocabulary:
- Associational: Civil society, values, social purpose
- Scientific: Evidence, research, methodology
- Managerial: Efficiency, performance, business

Based on Walter Powell's work on organizational legitimacy.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class TriangleScore:
    """Score on the Powell knowledge triangle."""
    entity_id: str
    entity_name: str

    # Raw keyword counts
    raw_associational: int = 0
    raw_scientific: int = 0
    raw_managerial: int = 0

    # Normalized coordinates (sum to 1)
    coord_associational: float = 0.333
    coord_scientific: float = 0.333
    coord_managerial: float = 0.333

    # Classification
    classification: str = "balanced"  # dominant_X, balanced, mixed

    # Metadata
    total_keywords: int = 0
    method: str = "keyword"

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "entity_name": self.entity_name,
            "raw_scores": {
                "associational": self.raw_associational,
                "scientific": self.raw_scientific,
                "managerial": self.raw_managerial,
            },
            "coordinates": {
                "associational": self.coord_associational,
                "scientific": self.coord_scientific,
                "managerial": self.coord_managerial,
            },
            "classification": self.classification,
            "total_keywords": self.total_keywords,
            "method": self.method,
        }


# =============================================================================
# POWELL VOCABULARY LISTS
# =============================================================================

ASSOCIATIONAL_KEYWORDS = [
    # Social values
    "accountability", "advocacy", "awareness", "charity", "commitment",
    "common good", "compassion", "democracy", "empowerment", "ethics",
    "justice", "mission", "moral", "participation", "principles",
    "quality of life", "social benefit", "social change", "solidarity",
    "trust", "values", "vision", "voice",
    # Civil society
    "citizen", "civic", "civil society", "community", "grassroots",
    "movement", "nonprofit", "ngo", "public interest", "volunteer",
    # Engagement
    "dialogue", "engagement", "inclusion", "stakeholder", "transparency",
]

SCIENTIFIC_KEYWORDS = [
    # Research methodology
    "analysis", "assessment", "causality", "control group", "correlation",
    "counterfactual", "criteria", "data", "evaluation", "evidence",
    "experiment", "framework", "indicators", "measurement", "methodology",
    "quantification", "randomized control trials", "review", "survey",
    "theory of change", "treatment effects",
    # Academic
    "academic", "hypothesis", "peer review", "publication", "research",
    "scientific", "study", "systematic", "validation", "verification",
    # Knowledge
    "discovery", "expertise", "innovation", "knowledge", "learning",
    "technology", "understanding",
]

MANAGERIAL_KEYWORDS = [
    # Business efficiency
    "benchmarks", "best practice", "bottom line", "capacity", "cost-benefit",
    "effectiveness", "efficiency", "growth", "impact", "kpi",
    "leverage", "management", "milestones", "monitoring", "objectives",
    "optimization", "outcome", "output", "performance", "productivity",
    "return on investment", "strategic", "transparency", "value proposition",
    # Operations
    "budget", "delivery", "execution", "implementation", "operations",
    "process", "project", "resources", "schedule", "scalability",
    # Market
    "business", "commercial", "competitive", "customer", "market",
    "profit", "revenue", "sales", "service",
]


class TriangleScorer:
    """
    Score entities on the Powell knowledge triangle.

    Uses keyword matching to position entities between:
    - Associational (civil society, values)
    - Scientific (research, evidence)
    - Managerial (business, efficiency)

    Example:
        >>> scorer = TriangleScorer()
        >>> score = scorer.score("doc1", "TU Delft", text)
        >>> print(f"Classification: {score.classification}")
    """

    def __init__(
        self,
        associational_keywords: Optional[List[str]] = None,
        scientific_keywords: Optional[List[str]] = None,
        managerial_keywords: Optional[List[str]] = None,
        dominance_threshold: float = 0.5,
        mixed_threshold: float = 0.4,
    ):
        """
        Initialize triangle scorer.

        Args:
            associational_keywords: Custom associational vocabulary
            scientific_keywords: Custom scientific vocabulary
            managerial_keywords: Custom managerial vocabulary
            dominance_threshold: Min proportion for "dominant" classification
            mixed_threshold: Max proportion difference for "balanced"
        """
        self.associational = set(
            kw.lower() for kw in (associational_keywords or ASSOCIATIONAL_KEYWORDS)
        )
        self.scientific = set(
            kw.lower() for kw in (scientific_keywords or SCIENTIFIC_KEYWORDS)
        )
        self.managerial = set(
            kw.lower() for kw in (managerial_keywords or MANAGERIAL_KEYWORDS)
        )

        self.dominance_threshold = dominance_threshold
        self.mixed_threshold = mixed_threshold

    def score(
        self,
        entity_id: str,
        entity_name: str,
        text: str,
    ) -> TriangleScore:
        """
        Score an entity's text on the knowledge triangle.

        Args:
            entity_id: Entity identifier
            entity_name: Entity name
            text: Text to analyze (article, website content, etc.)

        Returns:
            TriangleScore with coordinates and classification
        """
        text_lower = text.lower()

        # Count keyword occurrences
        raw_a = sum(text_lower.count(kw) for kw in self.associational)
        raw_b = sum(text_lower.count(kw) for kw in self.scientific)
        raw_c = sum(text_lower.count(kw) for kw in self.managerial)

        total = raw_a + raw_b + raw_c

        # Normalize to coordinates
        if total > 0:
            coord_a = raw_a / total
            coord_b = raw_b / total
            coord_c = raw_c / total
        else:
            coord_a = coord_b = coord_c = 1/3

        # Classify
        classification = self._classify(coord_a, coord_b, coord_c)

        return TriangleScore(
            entity_id=entity_id,
            entity_name=entity_name,
            raw_associational=raw_a,
            raw_scientific=raw_b,
            raw_managerial=raw_c,
            coord_associational=coord_a,
            coord_scientific=coord_b,
            coord_managerial=coord_c,
            classification=classification,
            total_keywords=total,
            method="keyword",
        )

    def _classify(self, a: float, b: float, c: float) -> str:
        """Classify based on triangle coordinates."""
        coords = [("associational", a), ("scientific", b), ("managerial", c)]
        coords.sort(key=lambda x: x[1], reverse=True)

        top_name, top_score = coords[0]
        second_name, second_score = coords[1]

        # Dominant if one pole has majority
        if top_score >= self.dominance_threshold:
            return f"dominant_{top_name}"

        # Balanced if all roughly equal
        max_diff = max(a, b, c) - min(a, b, c)
        if max_diff < self.mixed_threshold:
            return "balanced"

        # Otherwise mixed
        return "mixed"

    def score_batch(
        self,
        documents: List[Dict],
        id_field: str = "id",
        name_field: str = "title",
        text_field: str = "text",
    ) -> List[TriangleScore]:
        """
        Score multiple documents.

        Args:
            documents: List of document dicts
            id_field: Key for document ID
            name_field: Key for entity name
            text_field: Key for text content

        Returns:
            List of TriangleScore objects
        """
        results = []

        for doc in documents:
            text = doc.get(text_field, "")
            if not text:
                continue

            score = self.score(
                entity_id=doc.get(id_field, ""),
                entity_name=doc.get(name_field, ""),
                text=text,
            )
            results.append(score)

        return results

    def get_vocabulary_stats(self) -> Dict:
        """Get statistics about the vocabulary lists."""
        return {
            "associational_keywords": len(self.associational),
            "scientific_keywords": len(self.scientific),
            "managerial_keywords": len(self.managerial),
            "total_keywords": len(self.associational) + len(self.scientific) + len(self.managerial),
        }

    def find_overlapping_keywords(self) -> Dict[str, List[str]]:
        """Find keywords that appear in multiple categories."""
        overlaps = {}

        ab = self.associational & self.scientific
        if ab:
            overlaps["associational_scientific"] = list(ab)

        ac = self.associational & self.managerial
        if ac:
            overlaps["associational_managerial"] = list(ac)

        bc = self.scientific & self.managerial
        if bc:
            overlaps["scientific_managerial"] = list(bc)

        abc = self.associational & self.scientific & self.managerial
        if abc:
            overlaps["all_three"] = list(abc)

        return overlaps


def aggregate_scores(scores: List[TriangleScore]) -> Dict:
    """
    Aggregate triangle scores to get distribution statistics.

    Args:
        scores: List of TriangleScore objects

    Returns:
        Dictionary with aggregated statistics
    """
    if not scores:
        return {}

    classifications = Counter(s.classification for s in scores)

    # Compute centroid
    n = len(scores)
    centroid_a = sum(s.coord_associational for s in scores) / n
    centroid_b = sum(s.coord_scientific for s in scores) / n
    centroid_c = sum(s.coord_managerial for s in scores) / n

    # Compute dispersion (average distance from centroid)
    dispersion = sum(
        ((s.coord_associational - centroid_a) ** 2 +
         (s.coord_scientific - centroid_b) ** 2 +
         (s.coord_managerial - centroid_c) ** 2) ** 0.5
        for s in scores
    ) / n

    return {
        "total": n,
        "by_classification": dict(classifications),
        "centroid": {
            "associational": centroid_a,
            "scientific": centroid_b,
            "managerial": centroid_c,
        },
        "dispersion": dispersion,
        "avg_keywords": sum(s.total_keywords for s in scores) / n,
    }
