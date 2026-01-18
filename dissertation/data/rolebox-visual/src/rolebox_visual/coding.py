"""
Visual Coding Schema for Metafunction Analysis.

Implements coding categories for ideational, interpersonal, and textual
metafunctions following Kress & van Leeuwen (2006) and Jancsary et al. (2018).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


# =============================================================================
# Ideational Metafunction - Content Categories
# =============================================================================

class ParticipantType(Enum):
    """Categories of participants in visual representations."""
    # People
    MALE_ADULT = "male_adult"
    FEMALE_ADULT = "female_adult"
    MIXED_GROUP = "mixed_gender_group"
    PERSON_PARTIAL = "person_partial"
    NON_ADULT = "non_adult"

    # Technology
    INDUSTRIAL_EQUIPMENT = "industrial_equipment"
    DIGITAL_DEVICE = "digital_device"
    LABORATORY_INSTRUMENT = "laboratory_instrument"
    PROTOTYPE = "prototype"
    INFRASTRUCTURE = "infrastructure"

    # Nature
    NATURAL_ELEMENT = "natural_element"
    PLANT_AGRICULTURE = "plant_agriculture"

    # Built Environment
    BUILDING = "building"
    URBAN_SETTING = "urban_setting"


class ProcessType(Enum):
    """Categories of processes depicted in visuals."""
    # Interaction
    VERBAL_COMMUNICATION = "verbal_communication"
    NONVERBAL_INTERACTION = "nonverbal_interaction"
    COLLABORATION = "collaboration"

    # Work
    INTELLECTUAL_WORK = "intellectual_work"
    PHYSICAL_WORK = "physical_work"
    LABORATORY_WORK = "laboratory_work"

    # Display
    PRESENTATION = "presentation"
    DEMONSTRATION = "demonstration"
    EXHIBITION = "exhibition"

    # Movement
    DYNAMIC_ACTION = "dynamic_action"
    TRANSPORTATION = "transportation"


class SettingType(Enum):
    """Categories of settings/environments."""
    # Professional
    OFFICE = "office_space"
    CONFERENCE_ROOM = "conference_room"
    INDUSTRIAL_SITE = "industrial_site"

    # Educational
    CLASSROOM = "classroom"
    CAMPUS = "campus"
    LABORATORY = "laboratory"

    # Public
    EVENT_VENUE = "event_venue"
    URBAN_SPACE = "urban_space"
    NATURAL_ENVIRONMENT = "natural_environment"

    # Non-specific
    NON_DESCRIPT = "non_descript"
    STUDIO = "studio_backdrop"


class ConjunctionType(Enum):
    """Types of relationships between visual elements."""
    NARRATIVE = "narrative"          # Dynamic relationships, actions
    ANALYTICAL = "analytical"        # Classification, hierarchy
    SYMBOLIC = "symbolic"            # Metaphorical, associative
    NONE = "none"                    # Single element


# =============================================================================
# Interpersonal Metafunction - Viewer Positioning
# =============================================================================

class ContactLevel(Enum):
    """Level of engagement with viewer."""
    STRONG_CONTACT = "strong_contact"    # Direct eye contact
    WEAK_CONTACT = "weak_contact"        # People present, no engagement
    NO_CONTACT = "no_contact"            # No people, objects only


class SocialDistance(Enum):
    """Implied closeness to depicted content."""
    INTIMATE = "intimate"                # Close-up
    INTERPERSONAL = "interpersonal"      # Medium shot
    IMPERSONAL = "impersonal"            # Long shot


class VerticalAngle(Enum):
    """Power relationship suggested by viewing angle."""
    VIEWER_POWER = "viewer_power"        # High angle (looking down)
    EQUALITY = "equality"                # Eye level
    REPRESENTATION_POWER = "representation_power"  # Low angle (looking up)


class HorizontalAngle(Enum):
    """Involvement suggested by horizontal angle."""
    INVOLVEMENT = "involvement"          # Frontal
    DETACHMENT = "detachment"            # Oblique


class CodingOrientation(Enum):
    """Aesthetic/credibility code used."""
    NATURALISTIC = "naturalistic"        # Everyday perception
    SENSORY = "sensory"                  # Enhanced aesthetics
    TECHNOLOGICAL = "technological"      # Precision, measurement
    ABSTRACT = "abstract"                # Reduced, generic


# =============================================================================
# Textual Metafunction - Composition
# =============================================================================

class SalienceType(Enum):
    """What elements are most prominent."""
    PEOPLE_PRIMARY = "people_primary"
    TECHNOLOGY_PRIMARY = "technology_primary"
    SETTING_PRIMARY = "setting_primary"
    BALANCED = "balanced_composition"


class FramingType(Enum):
    """How different zones are separated."""
    STRONG_SEPARATION = "strong_separation"
    WEAK_SEPARATION = "weak_separation"
    NO_FRAMING = "no_framing"


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class IdeationalMetafunction:
    """Ideational metafunction coding - content of representation."""
    participants: List[ParticipantType] = field(default_factory=list)
    processes: List[ProcessType] = field(default_factory=list)
    setting: Optional[SettingType] = None
    conjunction: ConjunctionType = ConjunctionType.NONE

    # Additional attributes
    professional_dress: bool = False
    gender_mixed: bool = False
    technology_prominent: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'participants': [p.value for p in self.participants],
            'processes': [p.value for p in self.processes],
            'setting': self.setting.value if self.setting else None,
            'conjunction': self.conjunction.value,
            'professional_dress': self.professional_dress,
            'gender_mixed': self.gender_mixed,
            'technology_prominent': self.technology_prominent,
        }


@dataclass
class InterpersonalMetafunction:
    """Interpersonal metafunction coding - viewer positioning."""
    contact: ContactLevel = ContactLevel.NO_CONTACT
    distance: SocialDistance = SocialDistance.INTERPERSONAL
    vertical_angle: VerticalAngle = VerticalAngle.EQUALITY
    horizontal_angle: HorizontalAngle = HorizontalAngle.INVOLVEMENT
    coding_orientation: CodingOrientation = CodingOrientation.NATURALISTIC

    def to_dict(self) -> Dict[str, Any]:
        return {
            'contact': self.contact.value,
            'distance': self.distance.value,
            'vertical_angle': self.vertical_angle.value,
            'horizontal_angle': self.horizontal_angle.value,
            'coding_orientation': self.coding_orientation.value,
        }


@dataclass
class TextualMetafunction:
    """Textual metafunction coding - composition."""
    salience: SalienceType = SalienceType.BALANCED
    framing: FramingType = FramingType.WEAK_SEPARATION

    def to_dict(self) -> Dict[str, Any]:
        return {
            'salience': self.salience.value,
            'framing': self.framing.value,
        }


@dataclass
class VisualCoding:
    """
    Complete coding for a single visual artifact.

    Combines ideational, interpersonal, and textual metafunctions
    with metadata about source and coder.
    """
    image_id: str
    kic: str
    source_type: str  # website, report, social_media
    visual_type: str  # photograph, graphic, diagram, mixed

    # Metafunctions
    ideational: IdeationalMetafunction = field(default_factory=IdeationalMetafunction)
    interpersonal: InterpersonalMetafunction = field(default_factory=InterpersonalMetafunction)
    textual: TextualMetafunction = field(default_factory=TextualMetafunction)

    # Metadata
    notes: str = ""
    confidence: float = 0.8
    coder_id: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'image_id': self.image_id,
            'kic': self.kic,
            'source_type': self.source_type,
            'visual_type': self.visual_type,
            'ideational': self.ideational.to_dict(),
            'interpersonal': self.interpersonal.to_dict(),
            'textual': self.textual.to_dict(),
            'notes': self.notes,
            'confidence': self.confidence,
            'coder_id': self.coder_id,
            'timestamp': self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VisualCoding':
        """Create VisualCoding from dictionary."""
        ideational = IdeationalMetafunction(
            participants=[ParticipantType(p) for p in data.get('ideational', {}).get('participants', [])],
            processes=[ProcessType(p) for p in data.get('ideational', {}).get('processes', [])],
            setting=SettingType(data['ideational']['setting']) if data.get('ideational', {}).get('setting') else None,
            conjunction=ConjunctionType(data.get('ideational', {}).get('conjunction', 'none')),
        )

        interpersonal = InterpersonalMetafunction(
            contact=ContactLevel(data.get('interpersonal', {}).get('contact', 'no_contact')),
            distance=SocialDistance(data.get('interpersonal', {}).get('distance', 'interpersonal')),
            vertical_angle=VerticalAngle(data.get('interpersonal', {}).get('vertical_angle', 'equality')),
            horizontal_angle=HorizontalAngle(data.get('interpersonal', {}).get('horizontal_angle', 'involvement')),
            coding_orientation=CodingOrientation(data.get('interpersonal', {}).get('coding_orientation', 'naturalistic')),
        )

        textual = TextualMetafunction(
            salience=SalienceType(data.get('textual', {}).get('salience', 'balanced_composition')),
            framing=FramingType(data.get('textual', {}).get('framing', 'weak_separation')),
        )

        return cls(
            image_id=data['image_id'],
            kic=data['kic'],
            source_type=data['source_type'],
            visual_type=data['visual_type'],
            ideational=ideational,
            interpersonal=interpersonal,
            textual=textual,
            notes=data.get('notes', ''),
            confidence=data.get('confidence', 0.8),
            coder_id=data.get('coder_id', ''),
            timestamp=data.get('timestamp', ''),
        )


class VisualCorpus:
    """Collection of coded visual artifacts."""

    def __init__(self):
        self.codings: List[VisualCoding] = []

    def add(self, coding: VisualCoding):
        """Add a coding to the corpus."""
        self.codings.append(coding)

    def add_batch(self, codings: List[VisualCoding]):
        """Add multiple codings."""
        self.codings.extend(codings)

    def filter_by_kic(self, kic: str) -> List[VisualCoding]:
        """Get codings for a specific KIC."""
        return [c for c in self.codings if c.kic == kic]

    def filter_by_type(self, visual_type: str) -> List[VisualCoding]:
        """Get codings of a specific visual type."""
        return [c for c in self.codings if c.visual_type == visual_type]

    def get_statistics(self) -> Dict[str, Any]:
        """Compute corpus statistics."""
        if not self.codings:
            return {}

        kic_counts = {}
        type_counts = {}
        orientation_counts = {}

        for c in self.codings:
            kic_counts[c.kic] = kic_counts.get(c.kic, 0) + 1
            type_counts[c.visual_type] = type_counts.get(c.visual_type, 0) + 1
            orient = c.interpersonal.coding_orientation.value
            orientation_counts[orient] = orientation_counts.get(orient, 0) + 1

        return {
            'n_visuals': len(self.codings),
            'by_kic': kic_counts,
            'by_type': type_counts,
            'by_orientation': orientation_counts,
        }

    def to_list(self) -> List[Dict[str, Any]]:
        """Export corpus as list of dictionaries."""
        return [c.to_dict() for c in self.codings]
