"""
NuExtract-based Information Extraction.

Shared extraction module using NuExtract models for reliable template-based
structured extraction across all RoleBox modalities.

Supports:
- Wikipedia articles (organizations, cities)
- Organizational websites
- News articles
- Multilingual content (EN, FR, DE, ES, PT, IT)
"""

import json
import logging
import requests
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class NuExtractConfig:
    """Configuration for NuExtract-based extraction."""
    model: str = "sroecker/nuextract-tiny-v1.5"  # Multilingual by default
    ollama_url: str = "http://localhost:11434"
    temperature: float = 0.0  # NuExtract works best with temp=0
    max_tokens: int = 2048
    chunk_size: int = 6000  # Characters per chunk


@dataclass
class ExtractedInfo:
    """Result of NuExtract extraction from a single document."""
    doc_id: str
    doc_type: str
    title: str
    source_modality: str = ""
    organizations: List[Dict[str, Any]] = field(default_factory=list)
    people: List[Dict[str, Any]] = field(default_factory=list)
    locations: List[Dict[str, Any]] = field(default_factory=list)
    activities: List[Dict[str, Any]] = field(default_factory=list)
    relations: List[Dict[str, Any]] = field(default_factory=list)
    funding: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "doc_type": self.doc_type,
            "title": self.title,
            "source_modality": self.source_modality,
            "organizations": self.organizations,
            "people": self.people,
            "locations": self.locations,
            "activities": self.activities,
            "relations": self.relations,
            "funding": self.funding,
            "metadata": self.metadata,
            "stats": {
                "num_organizations": len(self.organizations),
                "num_people": len(self.people),
                "num_locations": len(self.locations),
                "num_activities": len(self.activities),
                "num_relations": len(self.relations),
                "num_funding": len(self.funding),
            }
        }


# =============================================================================
# EXTRACTION TEMPLATES BY MODALITY
# =============================================================================

# Wikipedia - Organizations
WIKIPEDIA_ORG_TEMPLATE = {
    "organizations": [
        {
            "name": "",
            "type": "",  # university, company, research_institute, agency, NGO
            "country": "",
            "roles": [],  # research, education, innovation, policy
            "partnerships": [],  # other org names
            "focus_areas": []  # climate, energy, digital, health, etc.
        }
    ]
}

# Wikipedia - Cities
WIKIPEDIA_CITY_TEMPLATE = {
    "city_info": {
        "name": "",
        "country": "",
        "population": "",
        "climate_commitments": [],  # C40, EU Mission, etc.
        "key_policies": []
    },
    "governance": [
        {
            "organization": "",
            "role": ""  # municipal, regional, national agency
        }
    ],
    "initiatives": [
        {
            "name": "",
            "focus": "",  # mobility, energy, buildings, etc.
            "partners": []
        }
    ]
}

# Organizational Websites
WEBSITE_TEMPLATE = {
    "organization": {
        "name": "",
        "type": "",
        "mission": "",
        "focus_areas": []
    },
    "roles_claimed": [
        {
            "role_identity": "",  # educator, researcher, investor, etc.
            "practice": "",  # what they do
            "counterroles": []  # who they serve
        }
    ],
    "partnerships": [
        {
            "partner_name": "",
            "partnership_type": ""  # research, funding, consortium, etc.
        }
    ],
    "programs": [
        {
            "name": "",
            "type": "",  # accelerator, training, research program
            "target_audience": ""
        }
    ]
}

# News Articles
NEWS_ARTICLE_TEMPLATE = {
    "main_actors": [
        {
            "name": "",
            "type": "",  # organization, person, institution
            "role_in_story": ""  # subject, source, mentioned
        }
    ],
    "events": [
        {
            "event_type": "",  # investment, partnership, launch, policy
            "description": "",
            "date": ""
        }
    ],
    "funding": [
        {
            "amount": "",
            "currency": "",
            "funder": "",
            "recipient": "",
            "purpose": ""
        }
    ],
    "relations": [
        {
            "source": "",
            "relation_type": "",  # invests_in, partners_with, acquires, funds
            "target": "",
            "context": ""
        }
    ]
}

# Generic Relations (for any modality)
RELATIONS_TEMPLATE = {
    "relations": [
        {
            "source": "",
            "relation_type": "",  # partners_with, funds, member_of, located_in
            "target": "",
            "context": ""
        }
    ]
}


class NuExtractExtractor:
    """
    Extract structured information using NuExtract models via Ollama.

    Supports multiple modalities with domain-specific templates.

    Example:
        >>> extractor = NuExtractExtractor()
        >>> result = extractor.extract(
        ...     text, doc_id="doc1",
        ...     modality="news", doc_type="article"
        ... )
        >>> print(f"Found {len(result.organizations)} organizations")
    """

    # Map modality + doc_type to templates
    TEMPLATES = {
        ("wikipedia", "organization"): WIKIPEDIA_ORG_TEMPLATE,
        ("wikipedia", "city"): WIKIPEDIA_CITY_TEMPLATE,
        ("websites", "organization"): WEBSITE_TEMPLATE,
        ("news", "article"): NEWS_ARTICLE_TEMPLATE,
        ("default", "default"): RELATIONS_TEMPLATE,
    }

    def __init__(self, config: Optional[NuExtractConfig] = None):
        self.config = config or NuExtractConfig()

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with NuExtract model."""
        url = f"{self.config.ollama_url}/api/generate"

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            }
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return ""

    def _format_prompt(self, text: str, template: Dict) -> str:
        """Format NuExtract prompt with text and template."""
        template_str = json.dumps(template, indent=2)
        return f"""<|input|>
### Template:
{template_str}

### Text:
{text}

<|output|>
"""

    def _parse_response(self, response: str) -> Dict:
        """Parse JSON response from NuExtract."""
        try:
            response = response.strip()

            # Handle case where model repeats template
            if response.startswith("{"):
                depth = 0
                end_pos = 0
                for i, char in enumerate(response):
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            end_pos = i + 1
                            break
                if end_pos > 0:
                    return json.loads(response[:end_pos])
                return json.loads(response)

            # Try to find JSON in response
            start = response.find("{")
            if start >= 0:
                depth = 0
                end_pos = start
                for i, char in enumerate(response[start:], start):
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            end_pos = i + 1
                            break
                if end_pos > start:
                    return json.loads(response[start:end_pos])

            return {}
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse NuExtract response: {e}")
            return {}

    def _chunk_text(self, text: str, max_chars: int = 6000) -> List[str]:
        """Split text into chunks for processing."""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += "\n\n" + para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _get_template(
        self,
        modality: str,
        doc_type: str,
        custom_template: Optional[Dict] = None
    ) -> Dict:
        """Get appropriate template for modality and doc_type."""
        if custom_template:
            return custom_template

        key = (modality, doc_type)
        if key in self.TEMPLATES:
            return self.TEMPLATES[key]

        # Try modality-only match
        for (m, d), template in self.TEMPLATES.items():
            if m == modality:
                return template

        return self.TEMPLATES[("default", "default")]

    def extract(
        self,
        text: str,
        doc_id: str,
        modality: str = "default",
        doc_type: str = "default",
        title: str = "",
        template: Optional[Dict] = None,
    ) -> ExtractedInfo:
        """
        Extract structured information from text.

        Args:
            text: Document text
            doc_id: Document identifier
            modality: Source modality (wikipedia, websites, news)
            doc_type: Document type (organization, city, article)
            title: Document title
            template: Custom extraction template (optional)

        Returns:
            ExtractedInfo with extracted entities and relations
        """
        selected_template = self._get_template(modality, doc_type, template)

        # Process chunks
        chunks = self._chunk_text(text)
        all_results = []

        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)} for {doc_id}")

            prompt = self._format_prompt(chunk, selected_template)
            response = self._call_ollama(prompt)
            result = self._parse_response(response)

            if result:
                all_results.append(result)

        # Merge results from all chunks
        merged = self._merge_results(all_results)

        # Create ExtractedInfo
        return ExtractedInfo(
            doc_id=doc_id,
            doc_type=doc_type,
            title=title,
            source_modality=modality,
            organizations=merged.get("organizations", []),
            people=merged.get("people", merged.get("main_actors", [])),
            locations=merged.get("locations", []),
            activities=merged.get("activities", merged.get("programs", [])),
            relations=merged.get("relations", []),
            funding=merged.get("funding", []),
            metadata={
                "num_chunks": len(chunks),
                "model": self.config.model,
                "modality": modality,
                "doc_type": doc_type,
            }
        )

    def _merge_results(self, results: List[Dict]) -> Dict:
        """Merge extraction results from multiple chunks."""
        merged = {
            "organizations": [],
            "people": [],
            "main_actors": [],
            "locations": [],
            "activities": [],
            "programs": [],
            "relations": [],
            "funding": [],
        }

        seen_orgs = set()
        seen_people = set()
        seen_locations = set()

        for result in results:
            # Organizations
            for org in result.get("organizations", []):
                name = org.get("name", "").strip()
                if name and name.lower() not in seen_orgs:
                    seen_orgs.add(name.lower())
                    merged["organizations"].append(org)

            # Handle organization field (singular) from website template
            if "organization" in result and isinstance(result["organization"], dict):
                org = result["organization"]
                name = org.get("name", "").strip()
                if name and name.lower() not in seen_orgs:
                    seen_orgs.add(name.lower())
                    merged["organizations"].append(org)

            # People / Main actors
            for person in result.get("people", []) + result.get("main_actors", []):
                name = person.get("name", "").strip()
                if name and name.lower() not in seen_people:
                    seen_people.add(name.lower())
                    merged["people"].append(person)

            # Locations
            for loc in result.get("locations", []):
                name = loc.get("name", "").strip()
                if name and name.lower() not in seen_locations:
                    seen_locations.add(name.lower())
                    merged["locations"].append(loc)

            # Activities/Programs - merge without strict deduplication
            for activity in result.get("activities", []) + result.get("programs", []):
                if activity.get("name"):
                    merged["activities"].append(activity)

            # Roles claimed (from websites)
            for role in result.get("roles_claimed", []):
                if role.get("role_identity"):
                    merged["activities"].append({
                        "name": role.get("role_identity"),
                        "type": "role_claim",
                        "practice": role.get("practice"),
                        "counterroles": role.get("counterroles", []),
                    })

            # Relations - keep all
            for relation in result.get("relations", []):
                if relation.get("source") and relation.get("target"):
                    merged["relations"].append(relation)

            # Partnerships (from websites/wikipedia)
            for partner in result.get("partnerships", []):
                if isinstance(partner, dict) and partner.get("partner_name"):
                    merged["relations"].append({
                        "source": "",  # Will be filled by caller
                        "relation_type": partner.get("partnership_type", "partners_with"),
                        "target": partner["partner_name"],
                    })
                elif isinstance(partner, str):
                    merged["relations"].append({
                        "source": "",
                        "relation_type": "partners_with",
                        "target": partner,
                    })

            # Funding
            for fund in result.get("funding", []):
                if fund.get("amount") or fund.get("funder"):
                    merged["funding"].append(fund)

            # Events (from news)
            for event in result.get("events", []):
                if event.get("event_type"):
                    merged["activities"].append({
                        "name": event.get("description", event["event_type"]),
                        "type": event["event_type"],
                        "date": event.get("date"),
                    })

            # Handle city-specific fields
            if "governance" in result:
                for gov in result["governance"]:
                    if gov.get("organization"):
                        merged["organizations"].append({
                            "name": gov["organization"],
                            "type": "governance",
                            "roles": [gov.get("role", "")]
                        })

            if "city_info" in result:
                city = result["city_info"]
                if city.get("name"):
                    merged["locations"].append({
                        "name": city["name"],
                        "type": "city",
                        "country": city.get("country", ""),
                        "metadata": {
                            "population": city.get("population"),
                            "climate_commitments": city.get("climate_commitments", [])
                        }
                    })

            if "initiatives" in result:
                for init in result["initiatives"]:
                    if init.get("name"):
                        merged["activities"].append({
                            "name": init["name"],
                            "type": "initiative",
                            "focus": init.get("focus"),
                            "partners": init.get("partners", []),
                        })

        return merged

    def extract_batch(
        self,
        documents: List[Dict[str, Any]],
        modality: str = "default",
        doc_type: str = "default",
        text_field: str = "text",
        id_field: str = "id",
        title_field: str = "title",
    ) -> List[ExtractedInfo]:
        """
        Extract from multiple documents.

        Args:
            documents: List of document dicts
            modality: Source modality
            doc_type: Type of documents
            text_field: Key for text content
            id_field: Key for document ID
            title_field: Key for document title

        Returns:
            List of ExtractedInfo objects
        """
        results = []

        for i, doc in enumerate(documents):
            title = doc.get(title_field, "unknown")
            logger.info(f"Extracting {i+1}/{len(documents)}: {title}")

            text = doc.get(text_field, "")
            if not text:
                continue

            result = self.extract(
                text=text,
                doc_id=doc.get(id_field, str(i)),
                modality=modality,
                doc_type=doc_type,
                title=title,
            )
            results.append(result)

        return results

    def extract_relations_only(
        self,
        text: str,
        doc_id: str,
        title: str = "",
    ) -> List[Dict]:
        """Extract only relations from text."""
        prompt = self._format_prompt(text[:6000], RELATIONS_TEMPLATE)
        response = self._call_ollama(prompt)
        result = self._parse_response(response)
        return result.get("relations", [])
