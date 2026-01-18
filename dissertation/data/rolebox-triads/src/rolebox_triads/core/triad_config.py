"""
Triad configuration definitions.

Defines the three triad types and their axis configurations.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


class TriadType(Enum):
    """Enumeration of supported triad types."""

    ROLE_MODALITIES = "role_modalities"
    POWELL_FRAMEWORK = "powell_framework"
    ACTOR_TYPES = "actor_types"
    MULTI_ACTOR_PERSPECTIVE = "multi_actor_perspective"  # Avelino & Wittmayer (2015)


@dataclass
class TriadAxis:
    """Definition of a single axis in the ternary space."""

    name: str  # Display name, e.g., "Claimed"
    key: str  # Internal key, e.g., "claimed"
    color: str  # Hex color for this pole
    description: str  # Human-readable description
    keywords: List[str] = field(default_factory=list)  # Vocabulary for text-based scoring
    source_modality: Optional[str] = None  # Which rolebox-* provides data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "key": self.key,
            "color": self.color,
            "description": self.description,
            "keywords": self.keywords,
            "source_modality": self.source_modality,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriadAxis":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            key=data["key"],
            color=data["color"],
            description=data.get("description", ""),
            keywords=data.get("keywords", []),
            source_modality=data.get("source_modality"),
        )


@dataclass
class TriadConfig:
    """Complete configuration for a triad type."""

    triad_type: TriadType
    name: str
    description: str
    axis_a: TriadAxis
    axis_b: TriadAxis
    axis_c: TriadAxis
    interstitial_threshold: float = 0.4  # Below this on dominant axis = interstitial
    color_palette: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Set default color palette if not provided."""
        if not self.color_palette:
            self.color_palette = {
                f"dominant_{self.axis_a.key}": self.axis_a.color,
                f"dominant_{self.axis_b.key}": self.axis_b.color,
                f"dominant_{self.axis_c.key}": self.axis_c.color,
                "interstitial": "#f1c40f",  # Yellow for interstitial
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "triad_type": self.triad_type.value,
            "name": self.name,
            "description": self.description,
            "axis_a": self.axis_a.to_dict(),
            "axis_b": self.axis_b.to_dict(),
            "axis_c": self.axis_c.to_dict(),
            "interstitial_threshold": self.interstitial_threshold,
            "color_palette": self.color_palette,
        }

    def to_json(self, path: Optional[Path] = None) -> str:
        """Export configuration to JSON."""
        json_str = json.dumps(self.to_dict(), indent=2)
        if path:
            path.write_text(json_str)
        return json_str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TriadConfig":
        """Create from dictionary."""
        return cls(
            triad_type=TriadType(data["triad_type"]),
            name=data["name"],
            description=data.get("description", ""),
            axis_a=TriadAxis.from_dict(data["axis_a"]),
            axis_b=TriadAxis.from_dict(data["axis_b"]),
            axis_c=TriadAxis.from_dict(data["axis_c"]),
            interstitial_threshold=data.get("interstitial_threshold", 0.4),
            color_palette=data.get("color_palette", {}),
        )

    @classmethod
    def from_json(cls, path: Path) -> "TriadConfig":
        """Load configuration from JSON file."""
        data = json.loads(path.read_text())
        return cls.from_dict(data)


# Pre-defined configurations for the three triad types


def get_role_modalities_config() -> TriadConfig:
    """Get the Role Modalities triad configuration (Claimed vs Attributed vs Enacted)."""
    return TriadConfig(
        triad_type=TriadType.ROLE_MODALITIES,
        name="Role Modalities",
        description="Organizations positioned by Claimed (websites) vs Attributed (news) vs Enacted (Crunchbase) roles",
        axis_a=TriadAxis(
            name="Claimed",
            key="claimed",
            color="#3498db",  # Blue
            description="Self-presented organizational identity from websites",
            source_modality="rolebox-websites",
        ),
        axis_b=TriadAxis(
            name="Attributed",
            key="attributed",
            color="#2ecc71",  # Green
            description="Media portrayal and external characterization",
            source_modality="rolebox-news",
        ),
        axis_c=TriadAxis(
            name="Enacted",
            key="enacted",
            color="#e74c3c",  # Red
            description="Actual behavior from investment/funding patterns",
            source_modality="rolebox-crunchbase",
        ),
    )


def get_powell_framework_config() -> TriadConfig:
    """Get the Powell Framework triad configuration (Associational vs Scientific vs Managerial)."""
    return TriadConfig(
        triad_type=TriadType.POWELL_FRAMEWORK,
        name="Powell Framework",
        description="Organizations positioned by legitimacy vocabulary: Associational vs Scientific vs Managerial",
        axis_a=TriadAxis(
            name="Associational",
            key="associational",
            color="#3498db",  # Blue
            description="Social values, civil society, moral purpose vocabulary",
            keywords=[
                "accountability", "advocacy", "awareness", "charity", "commitment",
                "common good", "compassion", "democracy", "empowerment", "ethics",
                "justice", "mission", "moral", "participation", "principles",
                "quality of life", "social benefit", "social change", "solidarity",
                "trust", "values", "vision", "voice",
            ],
            source_modality="rolebox-websites",
        ),
        axis_b=TriadAxis(
            name="Scientific",
            key="scientific",
            color="#2ecc71",  # Green
            description="Evidence-based, research methodology vocabulary",
            keywords=[
                "analysis", "assessment", "causality", "control group", "correlation",
                "counterfactual", "criteria", "data", "evaluation", "evidence",
                "experiment", "framework", "indicators", "measurement", "methodology",
                "quantification", "randomized control trials", "review", "survey",
                "theory of change", "treatment effects",
            ],
            source_modality="rolebox-websites",
        ),
        axis_c=TriadAxis(
            name="Managerial",
            key="managerial",
            color="#e74c3c",  # Red
            description="Business efficiency, performance metrics vocabulary",
            keywords=[
                "benchmarks", "best practice", "bottom line", "capacity", "cost-benefit",
                "effectiveness", "efficiency", "growth", "impact", "kpi",
                "leverage", "management", "milestones", "monitoring", "objectives",
                "optimization", "outcome", "output", "performance", "productivity",
                "return on investment", "strategic", "transparency", "value proposition",
            ],
            source_modality="rolebox-websites",
        ),
    )


def get_actor_types_config() -> TriadConfig:
    """Get the Actor Types triad configuration (Conforming vs Interfacing vs Bridging)."""
    return TriadConfig(
        triad_type=TriadType.ACTOR_TYPES,
        name="Actor Types",
        description="Organizations positioned by field positioning: Conforming vs Interfacing vs Bridging",
        axis_a=TriadAxis(
            name="Conforming",
            key="conforming",
            color="#3498db",  # Blue
            description="Concentrated within-region ties, anchored in single community",
            source_modality="rolebox-social",
        ),
        axis_b=TriadAxis(
            name="Interfacing",
            key="interfacing",
            color="#2ecc71",  # Green
            description="Balanced within/cross-region ties, anchors region while connecting",
            source_modality="rolebox-social",
        ),
        axis_c=TriadAxis(
            name="Bridging",
            key="bridging",
            color="#e74c3c",  # Red
            description="Primarily cross-region ties, connects different communities",
            source_modality="rolebox-social",
        ),
    )


def get_multi_actor_perspective_config() -> TriadConfig:
    """
    Get the Multi-actor Perspective (MaP) triad configuration.

    Based on Avelino & Wittmayer (2015) "Shifting Power Relations in Sustainability
    Transitions: A Multi-actor Perspective", Journal of Environmental Policy & Planning.

    The MaP distinguishes between four sectors (state, market, community, third sector),
    but for ternary visualization we use the three primary sectors: State, Market, Community.
    Third sector organizations can be positioned based on their hybrid characteristics.
    """
    return TriadConfig(
        triad_type=TriadType.MULTI_ACTOR_PERSPECTIVE,
        name="Multi-actor Perspective",
        description="Actors positioned by sector: State vs Market vs Community (Avelino & Wittmayer 2015)",
        axis_a=TriadAxis(
            name="State",
            key="state",
            color="#1a365d",  # Dark blue - government/institutional
            description="Government actors, public agencies, regulatory bodies, policy institutions",
            keywords=[
                "government", "ministry", "agency", "municipality", "public sector",
                "regulation", "policy", "legislation", "governance", "authority",
                "public administration", "city council", "national", "regional",
                "European Commission", "parliament", "department", "bureau",
                "licensing", "permit", "compliance", "oversight", "enforcement",
                "taxation", "subsidy", "grant", "public funding", "state-owned",
            ],
            source_modality="rolebox-websites",
        ),
        axis_b=TriadAxis(
            name="Market",
            key="market",
            color="#22543d",  # Dark green - business/commercial
            description="Business actors, corporations, SMEs, entrepreneurs, investors",
            keywords=[
                "company", "corporation", "enterprise", "startup", "SME",
                "investor", "venture capital", "private equity", "profit",
                "revenue", "market share", "competition", "customer", "product",
                "service", "business model", "commercial", "trade", "industry",
                "shareholder", "dividend", "growth", "scale", "exit",
                "incubator", "accelerator", "corporate", "B2B", "B2C",
                "private sector", "entrepreneur", "founder", "CEO",
            ],
            source_modality="rolebox-crunchbase",
        ),
        axis_c=TriadAxis(
            name="Community",
            key="community",
            color="#9b2c2c",  # Dark red - civil society/grassroots
            description="Civil society actors, grassroots initiatives, local communities, cooperatives",
            keywords=[
                "community", "citizen", "grassroots", "cooperative", "collective",
                "neighborhood", "local", "volunteer", "participation", "activism",
                "social movement", "NGO", "association", "foundation", "charity",
                "mutual aid", "commons", "shared ownership", "bottom-up",
                "solidarity", "civil society", "public interest", "social enterprise",
                "cooperative", "crowdfunding", "peer-to-peer", "community energy",
                "transition initiative", "local food", "housing cooperative",
            ],
            source_modality="rolebox-social",
        ),
        interstitial_threshold=0.4,
        color_palette={
            "dominant_state": "#1a365d",
            "dominant_market": "#22543d",
            "dominant_community": "#9b2c2c",
            "interstitial": "#d69e2e",  # Gold for hybrid/third sector positioning
        },
    )


def get_config_for_type(triad_type: TriadType) -> TriadConfig:
    """Get the configuration for a specific triad type."""
    configs = {
        TriadType.ROLE_MODALITIES: get_role_modalities_config,
        TriadType.POWELL_FRAMEWORK: get_powell_framework_config,
        TriadType.ACTOR_TYPES: get_actor_types_config,
        TriadType.MULTI_ACTOR_PERSPECTIVE: get_multi_actor_perspective_config,
    }
    return configs[triad_type]()
