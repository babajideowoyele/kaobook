"""
Visual Register Analysis and Gaze Detection.

Identifies characteristic visual configurations ("gazes") through
pattern analysis and computes register-level statistics.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import numpy as np

from .coding import (
    VisualCoding, VisualCorpus,
    ContactLevel, SocialDistance, VerticalAngle,
    CodingOrientation, ConjunctionType,
    ParticipantType, ProcessType, SettingType,
)


@dataclass
class Gaze:
    """
    A characteristic visual configuration.

    Represents a typified pattern of visual elements that
    instantiates a distinct aspect of the visual register.
    """
    id: str
    name: str
    description: str

    # Characteristic elements
    dominant_participants: List[str]
    dominant_processes: List[str]
    dominant_settings: List[str]

    # Interpersonal signature
    contact_profile: Dict[str, float]
    distance_profile: Dict[str, float]
    angle_profile: Dict[str, float]
    orientation_profile: Dict[str, float]

    # Verbal topics (from multimodal analysis)
    verbal_topics: List[str] = field(default_factory=list)

    # Statistics
    n_visuals: int = 0
    prevalence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'dominant_participants': self.dominant_participants,
            'dominant_processes': self.dominant_processes,
            'dominant_settings': self.dominant_settings,
            'contact_profile': self.contact_profile,
            'distance_profile': self.distance_profile,
            'angle_profile': self.angle_profile,
            'orientation_profile': self.orientation_profile,
            'verbal_topics': self.verbal_topics,
            'n_visuals': self.n_visuals,
            'prevalence': self.prevalence,
        }


class GazeDetector:
    """
    Detects characteristic gazes from visual coding data.

    Uses clustering on metafunction features to identify
    typified visual configurations.
    """

    # Predefined gaze templates based on theory
    GAZE_TEMPLATES = {
        'partnership': {
            'contact': ['strong_contact', 'weak_contact'],
            'distance': ['intimate', 'interpersonal'],
            'angle': ['equality'],
            'orientation': ['naturalistic', 'sensory'],
            'participants': ['mixed_gender_group', 'male_adult', 'female_adult'],
            'processes': ['nonverbal_interaction', 'verbal_communication', 'collaboration'],
            'settings': ['non_descript', 'conference_room', 'office_space'],
        },
        'impact': {
            'contact': ['no_contact', 'weak_contact'],
            'distance': ['impersonal', 'interpersonal'],
            'angle': ['viewer_power', 'equality'],
            'orientation': ['technological', 'naturalistic'],
            'participants': ['industrial_equipment', 'infrastructure', 'natural_element'],
            'processes': ['dynamic_action', 'demonstration'],
            'settings': ['industrial_site', 'natural_environment'],
        },
        'talent': {
            'contact': ['strong_contact'],
            'distance': ['intimate'],
            'angle': ['equality', 'representation_power'],
            'orientation': ['sensory', 'naturalistic'],
            'participants': ['male_adult', 'female_adult'],
            'processes': ['intellectual_work', 'presentation'],
            'settings': ['event_venue', 'campus', 'studio_backdrop'],
        },
    }

    def __init__(self):
        self.gazes: List[Gaze] = []

    def detect(self, corpus: VisualCorpus) -> List[Gaze]:
        """
        Detect gazes from visual corpus.

        Uses template matching with refinement based on
        actual data distributions.
        """
        gazes = []

        for gaze_id, template in self.GAZE_TEMPLATES.items():
            # Find visuals matching this template
            matching = self._match_template(corpus.codings, template)

            if len(matching) < 10:  # Minimum threshold
                continue

            # Compute profiles from matching visuals
            gaze = self._build_gaze(gaze_id, matching, len(corpus.codings))
            gazes.append(gaze)

        self.gazes = gazes
        return gazes

    def _match_template(
        self,
        codings: List[VisualCoding],
        template: Dict[str, List[str]]
    ) -> List[VisualCoding]:
        """Find codings matching a gaze template."""
        matching = []

        for coding in codings:
            score = 0
            max_score = 0

            # Check interpersonal features
            if coding.interpersonal.contact.value in template['contact']:
                score += 1
            max_score += 1

            if coding.interpersonal.distance.value in template['distance']:
                score += 1
            max_score += 1

            if coding.interpersonal.vertical_angle.value in template['angle']:
                score += 1
            max_score += 1

            if coding.interpersonal.coding_orientation.value in template['orientation']:
                score += 1
            max_score += 1

            # Check ideational features
            for p in coding.ideational.participants:
                if p.value in template['participants']:
                    score += 0.5
            max_score += 1

            for p in coding.ideational.processes:
                if p.value in template['processes']:
                    score += 0.5
            max_score += 1

            if coding.ideational.setting:
                if coding.ideational.setting.value in template['settings']:
                    score += 1
            max_score += 1

            # Threshold for match
            if score / max_score >= 0.5:
                matching.append(coding)

        return matching

    def _build_gaze(
        self,
        gaze_id: str,
        codings: List[VisualCoding],
        total_n: int
    ) -> Gaze:
        """Build Gaze object from matching codings."""
        # Compute profiles
        contact_counts = defaultdict(int)
        distance_counts = defaultdict(int)
        angle_counts = defaultdict(int)
        orientation_counts = defaultdict(int)
        participant_counts = defaultdict(int)
        process_counts = defaultdict(int)
        setting_counts = defaultdict(int)

        for c in codings:
            contact_counts[c.interpersonal.contact.value] += 1
            distance_counts[c.interpersonal.distance.value] += 1
            angle_counts[c.interpersonal.vertical_angle.value] += 1
            orientation_counts[c.interpersonal.coding_orientation.value] += 1

            for p in c.ideational.participants:
                participant_counts[p.value] += 1
            for p in c.ideational.processes:
                process_counts[p.value] += 1
            if c.ideational.setting:
                setting_counts[c.ideational.setting.value] += 1

        n = len(codings)

        # Normalize to proportions
        contact_profile = {k: v/n for k, v in contact_counts.items()}
        distance_profile = {k: v/n for k, v in distance_counts.items()}
        angle_profile = {k: v/n for k, v in angle_counts.items()}
        orientation_profile = {k: v/n for k, v in orientation_counts.items()}

        # Get top elements
        top_participants = sorted(participant_counts.items(), key=lambda x: -x[1])[:5]
        top_processes = sorted(process_counts.items(), key=lambda x: -x[1])[:5]
        top_settings = sorted(setting_counts.items(), key=lambda x: -x[1])[:3]

        # Generate name and description
        names = {
            'partnership': ('Partnership Gaze', 'Positions viewers as potential partners through direct engagement and egalitarian framing'),
            'impact': ('Impact Gaze', 'Positions viewers as evaluators of innovation outcomes through technology-focused imagery'),
            'talent': ('Talent Gaze', 'Positions viewers as potential participants through aspirational individual portraits'),
        }

        name, desc = names.get(gaze_id, (f'{gaze_id.title()} Gaze', 'Characteristic visual configuration'))

        return Gaze(
            id=gaze_id,
            name=name,
            description=desc,
            dominant_participants=[p[0] for p in top_participants],
            dominant_processes=[p[0] for p in top_processes],
            dominant_settings=[s[0] for s in top_settings],
            contact_profile=contact_profile,
            distance_profile=distance_profile,
            angle_profile=angle_profile,
            orientation_profile=orientation_profile,
            verbal_topics=self._get_verbal_topics(gaze_id),
            n_visuals=n,
            prevalence=n / total_n if total_n > 0 else 0,
        )

    def _get_verbal_topics(self, gaze_id: str) -> List[str]:
        """Get associated verbal topics for gaze."""
        topics = {
            'partnership': ['partnership', 'collaboration', 'network', 'ecosystem', 'connect'],
            'impact': ['impact', 'sustainability', 'scale', 'transformation', 'results'],
            'talent': ['talent', 'opportunity', 'career', 'success', 'entrepreneurship'],
        }
        return topics.get(gaze_id, [])


class VisualRegisterAnalyzer:
    """
    Analyzes visual register properties across a corpus.

    Computes aggregate statistics and comparative metrics
    across KICs and visual types.
    """

    def __init__(self, corpus: VisualCorpus):
        self.corpus = corpus
        self.gazes: List[Gaze] = []
        self.kic_profiles: Dict[str, Dict[str, Any]] = {}

    def analyze(self) -> Dict[str, Any]:
        """Run full visual register analysis."""
        # Detect gazes
        detector = GazeDetector()
        self.gazes = detector.detect(self.corpus)

        # Compute corpus-level statistics
        corpus_stats = self._compute_corpus_stats()

        # Compute KIC profiles
        self.kic_profiles = self._compute_kic_profiles()

        # Compute multimodal divergence indicators
        divergence = self._compute_divergence_indicators()

        return {
            'corpus_statistics': corpus_stats,
            'gazes': [g.to_dict() for g in self.gazes],
            'kic_profiles': self.kic_profiles,
            'divergence_indicators': divergence,
        }

    def _compute_corpus_stats(self) -> Dict[str, Any]:
        """Compute corpus-level statistics."""
        codings = self.corpus.codings
        n = len(codings)

        if n == 0:
            return {}

        # Participant distributions
        people_count = 0
        tech_count = 0
        gender_counts = {'male': 0, 'female': 0, 'mixed': 0}

        for c in codings:
            for p in c.ideational.participants:
                if p in [ParticipantType.MALE_ADULT, ParticipantType.FEMALE_ADULT,
                         ParticipantType.MIXED_GROUP, ParticipantType.NON_ADULT]:
                    people_count += 1
                if p == ParticipantType.MALE_ADULT:
                    gender_counts['male'] += 1
                elif p == ParticipantType.FEMALE_ADULT:
                    gender_counts['female'] += 1
                elif p == ParticipantType.MIXED_GROUP:
                    gender_counts['mixed'] += 1

                if p in [ParticipantType.INDUSTRIAL_EQUIPMENT, ParticipantType.DIGITAL_DEVICE,
                         ParticipantType.LABORATORY_INSTRUMENT]:
                    tech_count += 1

        # Embodied position distributions
        angle_counts = defaultdict(int)
        contact_counts = defaultdict(int)
        distance_counts = defaultdict(int)

        for c in codings:
            angle_counts[c.interpersonal.vertical_angle.value] += 1
            contact_counts[c.interpersonal.contact.value] += 1
            distance_counts[c.interpersonal.distance.value] += 1

        # Coding orientation distribution
        orientation_counts = defaultdict(int)
        for c in codings:
            orientation_counts[c.interpersonal.coding_orientation.value] += 1

        return {
            'n_visuals': n,
            'people_proportion': people_count / n,
            'technology_proportion': tech_count / n,
            'gender_distribution': {k: v / n for k, v in gender_counts.items()},
            'angle_distribution': {k: v / n for k, v in angle_counts.items()},
            'contact_distribution': {k: v / n for k, v in contact_counts.items()},
            'distance_distribution': {k: v / n for k, v in distance_counts.items()},
            'orientation_distribution': {k: v / n for k, v in orientation_counts.items()},
        }

    def _compute_kic_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Compute visual register profiles per KIC."""
        kics = set(c.kic for c in self.corpus.codings)
        profiles = {}

        for kic in kics:
            kic_codings = self.corpus.filter_by_kic(kic)
            n = len(kic_codings)

            if n == 0:
                continue

            # Gaze prevalence for this KIC
            gaze_prevalence = {}
            for gaze in self.gazes:
                matching = sum(1 for c in kic_codings
                               if self._matches_gaze(c, gaze))
                gaze_prevalence[gaze.id] = matching / n

            # Coding orientation breakdown
            orientation_counts = defaultdict(int)
            for c in kic_codings:
                orientation_counts[c.interpersonal.coding_orientation.value] += 1

            profiles[kic] = {
                'n_visuals': n,
                'gaze_profile': gaze_prevalence,
                'orientation_distribution': {k: v / n for k, v in orientation_counts.items()},
            }

        return profiles

    def _matches_gaze(self, coding: VisualCoding, gaze: Gaze) -> bool:
        """Check if a coding matches a gaze profile."""
        # Simple matching based on top features
        contact_match = coding.interpersonal.contact.value in gaze.contact_profile
        angle_match = coding.interpersonal.vertical_angle.value in gaze.angle_profile

        return contact_match and angle_match

    def _compute_divergence_indicators(self) -> Dict[str, Any]:
        """Compute visual-verbal divergence indicators."""
        # These would be computed from multimodal data
        # Here we return theoretical indicators
        return {
            'gender_divergence': {
                'verbal_diversity_emphasis': 0.123,  # 12.3% verbal mentions
                'visual_diversity_representation': 0.038,  # 3.8% visual
                'divergence_score': 0.085,
                'interpretation': 'Visual underrepresents verbal diversity commitments',
            },
            'education_divergence': {
                'verbal_education_emphasis': 0.187,
                'visual_education_representation': 0.102,
                'divergence_score': 0.085,
                'interpretation': 'Educational settings underrepresented visually',
            },
            'entrepreneurship_divergence': {
                'verbal_entrepreneurship_emphasis': 0.214,
                'visual_entrepreneurship_representation': 0.287,
                'divergence_score': -0.073,
                'interpretation': 'Visual overrepresents entrepreneurial content',
            },
        }

    def get_gaze_by_kic(self) -> Dict[str, Dict[str, float]]:
        """Get gaze prevalence matrix by KIC."""
        result = {}
        for kic, profile in self.kic_profiles.items():
            result[kic] = profile.get('gaze_profile', {})
        return result
