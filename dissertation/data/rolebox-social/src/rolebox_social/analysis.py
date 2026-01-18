"""
Bridging Analysis and Triangulation.

Identifies bridging actors and validates internal configurations
against external field structure.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict
import numpy as np

from .field import FieldNetwork, SubRegion


@dataclass
class BridgingActor:
    """
    An actor bridging multiple sub-regions.
    """
    username: str
    bridging_score: float
    home_region: int
    connected_regions: List[int]
    cross_region_ties: int
    total_ties: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'username': self.username,
            'bridging_score': self.bridging_score,
            'home_region': self.home_region,
            'connected_regions': self.connected_regions,
            'cross_region_ties': self.cross_region_ties,
            'total_ties': self.total_ties,
        }


class BridgingAnalyzer:
    """
    Analyzes bridging structure in the field network.

    Identifies actors that connect sub-regions and
    quantifies field permeability.
    """

    def __init__(self, field: FieldNetwork):
        self.field = field
        self.bridging_actors: List[BridgingActor] = []
        self.region_matrix: Dict[Tuple[int, int], int] = {}

    def analyze(self) -> Dict[str, Any]:
        """
        Run bridging analysis.

        Returns
        -------
        dict
            Analysis results including bridging actors and region connectivity
        """
        # Compute bridging scores
        self.bridging_actors = self._compute_bridging_scores()

        # Compute region-to-region connectivity
        self.region_matrix = self._compute_region_matrix()

        # Summary statistics
        stats = self._compute_statistics()

        return {
            'bridging_actors': [a.to_dict() for a in self.bridging_actors[:20]],
            'region_matrix': {
                f"{k[0]}-{k[1]}": v for k, v in self.region_matrix.items()
            },
            'statistics': stats,
        }

    def _compute_bridging_scores(self) -> List[BridgingActor]:
        """Compute bridging score for each actor."""
        communities = self.field.communities
        network = self.field.network

        # Build neighbor-to-community mapping
        actor_neighbors = defaultdict(list)
        for (u1, u2), weight in network.edges.items():
            if u1 in communities and u2 in communities:
                actor_neighbors[u1].append((u2, communities[u2], weight))
                actor_neighbors[u2].append((u1, communities[u1], weight))

        bridging_actors = []

        for actor, neighbors in actor_neighbors.items():
            if actor not in communities:
                continue

            home_region = communities[actor]
            total_weight = 0
            cross_region_weight = 0
            connected_regions = set()

            for neighbor, neighbor_region, weight in neighbors:
                total_weight += weight
                if neighbor_region != home_region:
                    cross_region_weight += weight
                    connected_regions.add(neighbor_region)

            if total_weight > 0:
                bridging_score = cross_region_weight / total_weight
            else:
                bridging_score = 0

            if bridging_score > 0.1:  # Threshold for "bridging"
                bridging_actors.append(BridgingActor(
                    username=actor,
                    bridging_score=bridging_score,
                    home_region=home_region,
                    connected_regions=list(connected_regions),
                    cross_region_ties=int(cross_region_weight),
                    total_ties=int(total_weight),
                ))

        # Sort by bridging score
        bridging_actors.sort(key=lambda x: -x.bridging_score)
        return bridging_actors

    def _compute_region_matrix(self) -> Dict[Tuple[int, int], int]:
        """Compute region-to-region bridging counts."""
        communities = self.field.communities
        network = self.field.network

        matrix = defaultdict(int)

        for (u1, u2), weight in network.edges.items():
            if u1 in communities and u2 in communities:
                r1, r2 = communities[u1], communities[u2]
                if r1 != r2:
                    key = tuple(sorted([r1, r2]))
                    matrix[key] += 1

        return dict(matrix)

    def _compute_statistics(self) -> Dict[str, Any]:
        """Compute summary statistics."""
        if not self.bridging_actors:
            return {}

        scores = [a.bridging_score for a in self.bridging_actors]
        cross_ties = [a.cross_region_ties for a in self.bridging_actors]

        return {
            'n_bridging_actors': len(self.bridging_actors),
            'avg_bridging_score': np.mean(scores),
            'max_bridging_score': max(scores),
            'total_cross_region_ties': sum(cross_ties),
            'n_region_pairs_connected': len(self.region_matrix),
        }

    def get_conforming_vs_interfacing(self) -> Dict[str, List[str]]:
        """
        Classify actors as conforming or interfacing.

        Conforming: primarily within-region ties
        Interfacing: balanced within/cross-region ties
        """
        conforming = []
        interfacing = []

        for actor in self.bridging_actors:
            if actor.bridging_score >= 0.3:
                interfacing.append(actor.username)
            else:
                conforming.append(actor.username)

        return {
            'conforming': conforming[:50],
            'interfacing': interfacing[:50],
        }


@dataclass
class TriangulationResult:
    """
    Result of triangulating internal and external perspectives.
    """
    sociotype: str
    internal_character: str
    corresponding_regions: List[str]
    alignment: str  # strong, moderate, weak, none
    interpretation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'sociotype': self.sociotype,
            'internal_character': self.internal_character,
            'corresponding_regions': self.corresponding_regions,
            'alignment': self.alignment,
            'interpretation': self.interpretation,
        }


class TriangulationAnalyzer:
    """
    Triangulates internal sociotype configurations with external field structure.

    Maps sociotypes from Chapter 5 to sub-regions identified through
    social curation in Chapter 6.
    """

    # Theoretical mapping from sociotypes to expected sub-regions
    SOCIOTYPE_MAPPING = {
        'Connective': {
            'internal': 'Platform, broker, ecosystem builder',
            'expected_regions': [],  # Function, not domain
            'interpretation': 'Connection is a function, not a domain. No corresponding sub-region expected.',
        },
        'Acceleration': {
            'internal': 'Startup support, funding, scaling',
            'expected_regions': ['Venture Capital', 'Digital & Tech Startups'],
            'interpretation': 'Acceleration maps to VC and startup ecosystems.',
        },
        'Development': {
            'internal': 'Education, training, certification',
            'expected_regions': ['Higher Education'],
            'interpretation': 'Development maps to educational institutions.',
        },
        'Knowledge': {
            'internal': 'Research, discovery, validation',
            'expected_regions': ['Higher Education', 'Research'],
            'interpretation': 'Knowledge production spans research and education.',
        },
        'Accountability': {
            'internal': 'Impact delivery, policy contribution',
            'expected_regions': ['EU Policy & Funding', 'Impact & Social Innovation'],
            'interpretation': 'Accountability recognized as distinct relational space.',
        },
        'Sectoral': {
            'internal': 'Domain-specific stakeholders',
            'expected_regions': ['Climate', 'Health', 'Food', 'Urban', 'Digital'],
            'interpretation': 'Sectoral configurations map to thematic sub-regions.',
        },
    }

    def __init__(self, field: FieldNetwork):
        self.field = field
        self.results: List[TriangulationResult] = []

    def triangulate(self) -> Dict[str, Any]:
        """
        Perform triangulation analysis.

        Returns
        -------
        dict
            Triangulation results with alignment assessments
        """
        # Get actual region labels
        region_labels = {sr.id: sr.label for sr in self.field.sub_regions}

        self.results = []

        for sociotype, mapping in self.SOCIOTYPE_MAPPING.items():
            # Check alignment with actual regions
            expected = mapping['expected_regions']
            actual_labels = list(region_labels.values())

            if not expected:
                alignment = 'none'
                matched = []
            else:
                matched = [r for r in expected if any(r.lower() in al.lower() for al in actual_labels)]
                if len(matched) == len(expected):
                    alignment = 'strong'
                elif len(matched) > 0:
                    alignment = 'moderate'
                else:
                    alignment = 'weak'

            result = TriangulationResult(
                sociotype=sociotype,
                internal_character=mapping['internal'],
                corresponding_regions=matched if matched else ['Distributed' if not expected else 'Not found'],
                alignment=alignment,
                interpretation=mapping['interpretation'],
            )
            self.results.append(result)

        # Compute key observations
        observations = self._generate_observations()

        return {
            'triangulation': [r.to_dict() for r in self.results],
            'key_observations': observations,
            'validation_summary': self._summarize_validation(),
        }

    def _generate_observations(self) -> List[str]:
        """Generate key observations from triangulation."""
        observations = []

        # Check connective
        connective = next((r for r in self.results if r.sociotype == 'Connective'), None)
        if connective and connective.alignment == 'none':
            observations.append(
                "Connective sociotype does not map to external sub-region - connection is a function, not a domain"
            )

        # Check sectoral
        sectoral = next((r for r in self.results if r.sociotype == 'Sectoral'), None)
        if sectoral and sectoral.alignment in ['strong', 'moderate']:
            observations.append(
                "Sectoral configurations validated by thematic sub-regions"
            )

        # Check accountability
        account = next((r for r in self.results if r.sociotype == 'Accountability'), None)
        if account and account.alignment in ['strong', 'moderate']:
            observations.append(
                "Accountability recognized externally as distinct relational space (EU Policy)"
            )

        return observations

    def _summarize_validation(self) -> Dict[str, Any]:
        """Summarize validation results."""
        alignments = [r.alignment for r in self.results]

        return {
            'strong_alignments': alignments.count('strong'),
            'moderate_alignments': alignments.count('moderate'),
            'weak_alignments': alignments.count('weak'),
            'no_alignment': alignments.count('none'),
            'overall_validation': 'Supported' if alignments.count('strong') + alignments.count('moderate') >= 3 else 'Partial',
        }

    def compute_seed_overlap(self, seed_networks: Dict[str, Set[str]]) -> Dict[Tuple[str, str], float]:
        """
        Compute Jaccard overlap between seed networks.

        Parameters
        ----------
        seed_networks : dict
            Mapping from seed name to set of actor usernames

        Returns
        -------
        dict
            Pairwise Jaccard similarities
        """
        seeds = list(seed_networks.keys())
        overlaps = {}

        for i, s1 in enumerate(seeds):
            for j, s2 in enumerate(seeds):
                if i >= j:
                    continue

                set1 = seed_networks[s1]
                set2 = seed_networks[s2]

                intersection = len(set1 & set2)
                union = len(set1 | set2)

                jaccard = intersection / union if union > 0 else 0
                overlaps[(s1, s2)] = jaccard

        return overlaps
