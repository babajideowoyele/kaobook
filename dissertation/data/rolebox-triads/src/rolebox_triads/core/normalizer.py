"""
Triad coordinate normalization and classification.

Converts raw scores to normalized ternary coordinates and classifies positions.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math

from rolebox_triads.core.triad_config import TriadConfig


@dataclass
class OrganizationTriadPosition:
    """Complete triad position for an organization."""

    org_id: str
    org_name: str
    coordinates: Tuple[float, float, float]  # (a, b, c) normalized, sum=1
    raw_scores: Tuple[float, float, float]  # Original scores
    classification: str  # "dominant_a", "dominant_b", "dominant_c", "interstitial"
    confidence: float = 1.0  # Confidence in the position (0-1)
    kic_sectors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    time_series: List[Dict[str, Any]] = field(default_factory=list)  # For animation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "org_id": self.org_id,
            "org_name": self.org_name,
            "coordinates": {
                "a": self.coordinates[0],
                "b": self.coordinates[1],
                "c": self.coordinates[2],
            },
            "raw_scores": {
                "a": self.raw_scores[0],
                "b": self.raw_scores[1],
                "c": self.raw_scores[2],
            },
            "classification": self.classification,
            "confidence": self.confidence,
            "kic_sectors": self.kic_sectors,
            "metadata": self.metadata,
            "time_series": self.time_series,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrganizationTriadPosition":
        """Create from dictionary."""
        coords = data.get("coordinates", {})
        raw = data.get("raw_scores", {})
        return cls(
            org_id=data["org_id"],
            org_name=data["org_name"],
            coordinates=(coords.get("a", 0), coords.get("b", 0), coords.get("c", 0)),
            raw_scores=(raw.get("a", 0), raw.get("b", 0), raw.get("c", 0)),
            classification=data.get("classification", "interstitial"),
            confidence=data.get("confidence", 1.0),
            kic_sectors=data.get("kic_sectors", []),
            metadata=data.get("metadata", {}),
            time_series=data.get("time_series", []),
        )


@dataclass
class NetworkEdge:
    """Edge between two organizations in the triad network."""

    source_id: str
    target_id: str
    weight: float = 1.0
    edge_type: str = "generic"  # "hyperlink", "mention", "investment", "co_membership"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "weight": self.weight,
            "edge_type": self.edge_type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NetworkEdge":
        """Create from dictionary."""
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            weight=data.get("weight", 1.0),
            edge_type=data.get("edge_type", "generic"),
            metadata=data.get("metadata", {}),
        )


class TriadNormalizer:
    """
    Normalizes raw scores to ternary coordinates.

    Coordinates satisfy: a + b + c = 1, a >= 0, b >= 0, c >= 0
    """

    def __init__(self, config: TriadConfig):
        self.config = config
        self.threshold = config.interstitial_threshold

    def normalize(
        self, raw_a: float, raw_b: float, raw_c: float
    ) -> Tuple[float, float, float]:
        """
        Convert raw scores to normalized ternary coordinates.

        Args:
            raw_a: Raw score for axis A
            raw_b: Raw score for axis B
            raw_c: Raw score for axis C

        Returns:
            Tuple of (a, b, c) where a + b + c = 1
        """
        total = raw_a + raw_b + raw_c
        if total == 0:
            return (1 / 3, 1 / 3, 1 / 3)  # Centroid if no data
        return (raw_a / total, raw_b / total, raw_c / total)

    def classify(self, a: float, b: float, c: float) -> str:
        """
        Classify position as dominant pole or interstitial.

        Args:
            a: Normalized coordinate for axis A
            b: Normalized coordinate for axis B
            c: Normalized coordinate for axis C

        Returns:
            Classification string: "dominant_{key}" or "interstitial"
        """
        max_val = max(a, b, c)

        # If no clear dominant (below threshold), classify as interstitial
        if max_val < self.threshold:
            return "interstitial"

        # Determine which axis is dominant
        if a == max_val:
            return f"dominant_{self.config.axis_a.key}"
        if b == max_val:
            return f"dominant_{self.config.axis_b.key}"
        return f"dominant_{self.config.axis_c.key}"

    def to_cartesian(self, a: float, b: float, c: float) -> Tuple[float, float]:
        """
        Convert ternary coordinates to Cartesian (x, y) for plotting.

        Uses the standard ternary to Cartesian transformation where:
        - A is at top vertex (0.5, sqrt(3)/2)
        - B is at bottom-left (0, 0)
        - C is at bottom-right (1, 0)

        Args:
            a: Normalized coordinate for axis A (top)
            b: Normalized coordinate for axis B (bottom-left)
            c: Normalized coordinate for axis C (bottom-right)

        Returns:
            Tuple of (x, y) in Cartesian coordinates
        """
        # Ensure normalization
        total = a + b + c
        if total == 0:
            return (0.5, math.sqrt(3) / 6)  # Centroid

        # Standard ternary to Cartesian
        x = 0.5 * (2 * c + a) / total
        y = (math.sqrt(3) / 2) * a / total

        return (x, y)

    def from_cartesian(self, x: float, y: float) -> Tuple[float, float, float]:
        """
        Convert Cartesian (x, y) back to ternary coordinates.

        Args:
            x: Cartesian x coordinate
            y: Cartesian y coordinate

        Returns:
            Tuple of (a, b, c) ternary coordinates
        """
        a = 2 * y / math.sqrt(3)
        c = x - y / math.sqrt(3)
        b = 1 - a - c

        # Clamp to valid range
        a = max(0, min(1, a))
        b = max(0, min(1, b))
        c = max(0, min(1, c))

        # Re-normalize
        total = a + b + c
        if total > 0:
            return (a / total, b / total, c / total)
        return (1 / 3, 1 / 3, 1 / 3)

    def get_color(self, classification: str) -> str:
        """Get the color for a classification."""
        return self.config.color_palette.get(classification, "#999999")

    def compute_position(
        self,
        org_id: str,
        org_name: str,
        raw_a: float,
        raw_b: float,
        raw_c: float,
        kic_sectors: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OrganizationTriadPosition:
        """
        Compute a complete triad position for an organization.

        Args:
            org_id: Unique identifier
            org_name: Display name
            raw_a, raw_b, raw_c: Raw scores for each axis
            kic_sectors: Optional list of KIC sector affiliations
            metadata: Optional additional metadata

        Returns:
            OrganizationTriadPosition with normalized coordinates and classification
        """
        coordinates = self.normalize(raw_a, raw_b, raw_c)
        classification = self.classify(*coordinates)

        # Compute confidence based on how clearly dominant the position is
        max_coord = max(coordinates)
        min_coord = min(coordinates)
        confidence = max_coord - min_coord  # Range from 0 (centroid) to ~0.67 (corner)

        return OrganizationTriadPosition(
            org_id=org_id,
            org_name=org_name,
            coordinates=coordinates,
            raw_scores=(raw_a, raw_b, raw_c),
            classification=classification,
            confidence=confidence,
            kic_sectors=kic_sectors or [],
            metadata=metadata or {},
        )

    def compute_centroid(
        self, positions: List[OrganizationTriadPosition]
    ) -> Tuple[float, float, float]:
        """Compute the centroid of a set of positions."""
        if not positions:
            return (1 / 3, 1 / 3, 1 / 3)

        sum_a = sum(p.coordinates[0] for p in positions)
        sum_b = sum(p.coordinates[1] for p in positions)
        sum_c = sum(p.coordinates[2] for p in positions)
        n = len(positions)

        return (sum_a / n, sum_b / n, sum_c / n)

    def compute_dispersion(self, positions: List[OrganizationTriadPosition]) -> float:
        """
        Compute the dispersion (spread) of positions around the centroid.

        Returns average Euclidean distance from centroid in Cartesian space.
        """
        if not positions:
            return 0.0

        centroid = self.compute_centroid(positions)
        centroid_xy = self.to_cartesian(*centroid)

        total_dist = 0.0
        for pos in positions:
            pos_xy = self.to_cartesian(*pos.coordinates)
            dist = math.sqrt(
                (pos_xy[0] - centroid_xy[0]) ** 2 + (pos_xy[1] - centroid_xy[1]) ** 2
            )
            total_dist += dist

        return total_dist / len(positions)
