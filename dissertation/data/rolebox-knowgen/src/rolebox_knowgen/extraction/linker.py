"""
Entity Linking Module.

Links extracted entities to:
- Wikidata QIDs (structured knowledge)
- Other RoleBox modalities (cross-modal triangulation)
- EIT KIC partner registry (domain-specific)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class LinkedEntity:
    """An entity linked to external knowledge bases."""

    surface_form: str  # As found in text
    canonical_name: str  # Normalized form
    entity_type: str  # ORG, PERSON, GPE, etc.

    # Wikidata linking
    wikidata_qid: Optional[str] = None
    wikidata_label: Optional[str] = None
    wikidata_description: Optional[str] = None

    # RoleBox cross-modal linking
    rolebox_id: Optional[str] = None
    found_in_modalities: List[str] = field(default_factory=list)

    # EIT KIC linking
    kic_affiliation: Optional[str] = None
    kic_partner_type: Optional[str] = None

    # Confidence and provenance
    link_confidence: float = 0.0
    link_method: str = ""  # "exact", "fuzzy", "alias", "wikidata_search"

    def to_dict(self) -> Dict:
        return {
            "surface_form": self.surface_form,
            "canonical_name": self.canonical_name,
            "entity_type": self.entity_type,
            "wikidata": {
                "qid": self.wikidata_qid,
                "label": self.wikidata_label,
                "description": self.wikidata_description,
            },
            "rolebox": {
                "id": self.rolebox_id,
                "modalities": self.found_in_modalities,
            },
            "kic": {
                "affiliation": self.kic_affiliation,
                "partner_type": self.kic_partner_type,
            },
            "linking": {
                "confidence": self.link_confidence,
                "method": self.link_method,
            },
        }


class EntityLinker:
    """
    Link extracted entities to knowledge bases and RoleBox modalities.

    Supports:
    - Exact and fuzzy matching to known entities
    - Wikidata QID lookup
    - Cross-modal linking to rolebox-websites, rolebox-news, etc.
    - EIT KIC partner registry lookup

    Example:
        >>> linker = EntityLinker()
        >>> linker.load_kic_registry("path/to/orgs_wikidata.csv")
        >>> linked = linker.link("TU Delft", "ORG")
        >>> print(linked.wikidata_qid)  # Q1137652
    """

    def __init__(
        self,
        fuzzy_threshold: float = 0.85,
        enable_wikidata_api: bool = False,
    ):
        """
        Initialize entity linker.

        Args:
            fuzzy_threshold: Minimum similarity for fuzzy matching (0-1)
            enable_wikidata_api: Whether to query Wikidata API for unknown entities
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.enable_wikidata_api = enable_wikidata_api

        # Entity registries (populated by load methods)
        self.kic_registry: Dict[str, Dict] = {}  # canonical_name -> entity data
        self.city_registry: Dict[str, Dict] = {}
        self.alias_map: Dict[str, str] = {}  # alias -> canonical_name

        # Cross-modal presence tracking
        self.modality_presence: Dict[str, Set[str]] = {
            "websites": set(),
            "news": set(),
            "crunchbase": set(),
            "social": set(),
            "wikipedia": set(),
        }

    def load_kic_registry(self, csv_path: str) -> int:
        """
        Load EIT KIC partner registry from CSV.

        Args:
            csv_path: Path to orgs_wikidata.csv

        Returns:
            Number of organizations loaded
        """
        import pandas as pd

        try:
            df = pd.read_csv(csv_path)
        except FileNotFoundError:
            logger.warning(f"KIC registry not found: {csv_path}")
            return 0

        for _, row in df.iterrows():
            name = str(row.get("name", row.get("organization", ""))).strip()
            if not name:
                continue

            canonical = self._normalize_name(name)

            self.kic_registry[canonical] = {
                "name": name,
                "qid": row.get("qid"),
                "kic": row.get("kic"),
                "country": row.get("country"),
                "org_type": row.get("org_type_label"),
                "wikidata_label": row.get("wikidata_label", name),
            }

            # Also register by exact name (before normalization)
            self.kic_registry[name.lower()] = self.kic_registry[canonical]

            # Add aliases
            wikidata_label = str(row.get("wikidata_label", "")).strip()
            if wikidata_label and wikidata_label != name:
                self.alias_map[self._normalize_name(wikidata_label)] = canonical

        logger.info(f"Loaded {len(self.kic_registry)} KIC partners")
        return len(self.kic_registry)

    def load_city_registry(self, csv_path: str) -> int:
        """
        Load city registry from CSV.

        Args:
            csv_path: Path to cities_wikidata.csv

        Returns:
            Number of cities loaded
        """
        import pandas as pd

        try:
            df = pd.read_csv(csv_path)
        except FileNotFoundError:
            logger.warning(f"City registry not found: {csv_path}")
            return 0

        for _, row in df.iterrows():
            name = str(row.get("city", row.get("name", ""))).strip()
            if not name:
                continue

            canonical = self._normalize_name(name)

            self.city_registry[canonical] = {
                "name": name,
                "qid": row.get("qid"),
                "country": row.get("country"),
                "population": row.get("population"),
                "wikidata_label": row.get("wikidata_label"),
            }

            # Add wikidata label as alias
            wikidata_label = str(row.get("wikidata_label", "")).strip()
            if wikidata_label and wikidata_label != name:
                self.alias_map[self._normalize_name(wikidata_label)] = canonical

        logger.info(f"Loaded {len(self.city_registry)} cities")
        return len(self.city_registry)

    def load_modality_entities(
        self,
        modality: str,
        entities: List[str],
    ) -> None:
        """
        Load known entities from a RoleBox modality.

        Args:
            modality: Modality name (websites, news, crunchbase, social)
            entities: List of entity names found in that modality
        """
        if modality not in self.modality_presence:
            self.modality_presence[modality] = set()

        for entity in entities:
            canonical = self._normalize_name(entity)
            self.modality_presence[modality].add(canonical)

    def link(
        self,
        surface_form: str,
        entity_type: str = "ORG",
    ) -> LinkedEntity:
        """
        Link an entity mention to knowledge bases.

        Args:
            surface_form: Entity as found in text
            entity_type: Entity type (ORG, PERSON, GPE, etc.)

        Returns:
            LinkedEntity with resolved links
        """
        normalized = self._normalize_name(surface_form)

        # Create base entity
        linked = LinkedEntity(
            surface_form=surface_form,
            canonical_name=surface_form,
            entity_type=entity_type,
        )

        # Try exact match first
        if entity_type in ("ORG", "PERSON"):
            match = self._match_organization(normalized)
            if match:
                self._apply_org_match(linked, match, "exact")
                return linked

        elif entity_type == "GPE":
            match = self._match_city(normalized)
            if match:
                self._apply_city_match(linked, match, "exact")
                return linked

        # Try alias lookup
        if normalized in self.alias_map:
            canonical = self.alias_map[normalized]
            if entity_type in ("ORG", "PERSON") and canonical in self.kic_registry:
                self._apply_org_match(linked, self.kic_registry[canonical], "alias")
                return linked
            elif entity_type == "GPE" and canonical in self.city_registry:
                self._apply_city_match(linked, self.city_registry[canonical], "alias")
                return linked

        # Try fuzzy matching
        if entity_type in ("ORG", "PERSON"):
            match, score = self._fuzzy_match_org(normalized)
            if match and score >= self.fuzzy_threshold:
                self._apply_org_match(linked, match, "fuzzy")
                linked.link_confidence = score
                return linked

        elif entity_type == "GPE":
            match, score = self._fuzzy_match_city(normalized)
            if match and score >= self.fuzzy_threshold:
                self._apply_city_match(linked, match, "fuzzy")
                linked.link_confidence = score
                return linked

        # Check cross-modal presence even without full linking
        linked.found_in_modalities = self._find_modality_presence(normalized)

        # Try Wikidata API as last resort
        if self.enable_wikidata_api and not linked.wikidata_qid:
            wikidata_result = self._query_wikidata(surface_form, entity_type)
            if wikidata_result:
                linked.wikidata_qid = wikidata_result.get("qid")
                linked.wikidata_label = wikidata_result.get("label")
                linked.wikidata_description = wikidata_result.get("description")
                linked.link_method = "wikidata_search"
                linked.link_confidence = wikidata_result.get("score", 0.8)

        return linked

    def link_batch(
        self,
        entities: List[Tuple[str, str]],
    ) -> List[LinkedEntity]:
        """
        Link multiple entities.

        Args:
            entities: List of (surface_form, entity_type) tuples

        Returns:
            List of LinkedEntity objects
        """
        return [self.link(surface, etype) for surface, etype in entities]

    def _normalize_name(self, name: str) -> str:
        """Normalize entity name for matching."""
        name = name.lower().strip()
        # Remove common suffixes
        for suffix in [" inc.", " inc", " ltd.", " ltd", " gmbh", " b.v.", " bv",
                       " ag", " sa", " spa", " as", " ab", " oy"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        # Remove punctuation
        name = re.sub(r'[^\w\s]', '', name)
        # Normalize whitespace
        name = ' '.join(name.split())
        return name

    def _match_organization(self, normalized: str) -> Optional[Dict]:
        """Exact match against KIC registry."""
        return self.kic_registry.get(normalized)

    def _match_city(self, normalized: str) -> Optional[Dict]:
        """Exact match against city registry."""
        return self.city_registry.get(normalized)

    def _fuzzy_match_org(
        self,
        normalized: str,
    ) -> Tuple[Optional[Dict], float]:
        """Fuzzy match against KIC registry."""
        best_match = None
        best_score = 0.0

        for canonical, data in self.kic_registry.items():
            score = SequenceMatcher(None, normalized, canonical).ratio()
            if score > best_score:
                best_score = score
                best_match = data

        return best_match, best_score

    def _fuzzy_match_city(
        self,
        normalized: str,
    ) -> Tuple[Optional[Dict], float]:
        """Fuzzy match against city registry."""
        best_match = None
        best_score = 0.0

        for canonical, data in self.city_registry.items():
            score = SequenceMatcher(None, normalized, canonical).ratio()
            if score > best_score:
                best_score = score
                best_match = data

        return best_match, best_score

    def _apply_org_match(
        self,
        linked: LinkedEntity,
        match: Dict,
        method: str,
    ) -> None:
        """Apply organization match to linked entity."""
        linked.canonical_name = match["name"]
        linked.wikidata_qid = match.get("qid")
        linked.wikidata_label = match.get("wikidata_label")
        linked.kic_affiliation = match.get("kic")
        linked.kic_partner_type = match.get("org_type")
        linked.link_method = method
        linked.link_confidence = 1.0 if method in ("exact", "alias") else linked.link_confidence

        # Check cross-modal presence
        canonical_normalized = self._normalize_name(match["name"])
        linked.found_in_modalities = self._find_modality_presence(canonical_normalized)

    def _apply_city_match(
        self,
        linked: LinkedEntity,
        match: Dict,
        method: str,
    ) -> None:
        """Apply city match to linked entity."""
        linked.canonical_name = match["name"]
        linked.wikidata_qid = match.get("qid")
        linked.wikidata_label = match.get("wikidata_label")
        linked.link_method = method
        linked.link_confidence = 1.0 if method in ("exact", "alias") else linked.link_confidence

        # Check cross-modal presence
        canonical_normalized = self._normalize_name(match["name"])
        linked.found_in_modalities = self._find_modality_presence(canonical_normalized)

    def _find_modality_presence(self, normalized: str) -> List[str]:
        """Find which modalities contain this entity."""
        present_in = []
        for modality, entities in self.modality_presence.items():
            if normalized in entities:
                present_in.append(modality)
        return present_in

    def _query_wikidata(
        self,
        surface_form: str,
        entity_type: str,
    ) -> Optional[Dict]:
        """
        Query Wikidata API to find entity QID.

        Uses the wbsearchentities API for fast entity search.
        """
        import requests

        try:
            url = "https://www.wikidata.org/w/api.php"
            params = {
                "action": "wbsearchentities",
                "search": surface_form,
                "language": "en",
                "format": "json",
                "limit": 5,
            }

            headers = {
                "User-Agent": "RoleBox-KnowGen/1.0 (research project) python-requests"
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = data.get("search", [])
            if not results:
                return None

            # Map entity types to expected Wikidata patterns
            type_patterns = {
                "ORG": ["organization", "company", "university", "institute", "agency"],
                "PERSON": ["human"],
                "GPE": ["city", "country", "state", "municipality", "administrative"],
            }
            patterns = type_patterns.get(entity_type, [])

            for result in results:
                qid = result.get("id")
                label = result.get("label", "")
                description = result.get("description", "").lower()

                if patterns:
                    if any(p in description for p in patterns):
                        return {
                            "qid": qid,
                            "label": label,
                            "description": result.get("description"),
                            "score": 0.9,
                        }
                else:
                    return {
                        "qid": qid,
                        "label": label,
                        "description": result.get("description"),
                        "score": 0.7,
                    }

            # Return first result with lower confidence
            if results:
                result = results[0]
                return {
                    "qid": result.get("id"),
                    "label": result.get("label"),
                    "description": result.get("description"),
                    "score": 0.5,
                }

            return None

        except Exception as e:
            logger.debug(f"Wikidata API error for '{surface_form}': {e}")
            return None

    def get_cross_modal_stats(self) -> Dict:
        """Get statistics on cross-modal entity linking."""
        all_entities = set()
        for entities in self.modality_presence.values():
            all_entities.update(entities)

        multi_modal = []
        for entity in all_entities:
            modalities = [m for m, e in self.modality_presence.items() if entity in e]
            if len(modalities) > 1:
                multi_modal.append({
                    "entity": entity,
                    "modalities": modalities,
                    "count": len(modalities),
                })

        multi_modal.sort(key=lambda x: x["count"], reverse=True)

        return {
            "total_unique_entities": len(all_entities),
            "entities_per_modality": {
                m: len(e) for m, e in self.modality_presence.items()
            },
            "multi_modal_entities": len(multi_modal),
            "top_cross_modal": multi_modal[:20],
        }
