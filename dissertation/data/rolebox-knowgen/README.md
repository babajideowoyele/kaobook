# RoleBox KnowGen

**Knowledge Generation Infrastructure** for RoleBox modalities.

Shared extraction and analysis capabilities used across all RoleBox data modules:
- `rolebox-wikipedia` - Wikipedia and Wikidata
- `rolebox-websites` - Organizational websites
- `rolebox-news` - News article analysis
- `rolebox-crunchbase` - Startup/investment data
- `rolebox-social` - Social media analysis

## Features

### NuExtract Structured Extraction
Template-based information extraction using [NuExtract 1.5](https://huggingface.co/numind/NuExtract-1.5):
- **Multilingual**: EN, FR, DE, ES, PT, IT
- **Local inference**: Runs via Ollama (no API keys needed)
- **Domain templates**: Customized for Wikipedia, websites, news articles

```python
from rolebox_knowgen import NuExtractExtractor

extractor = NuExtractExtractor()
result = extractor.extract(
    text=article_text,
    doc_id="doc1",
    modality="news",
    doc_type="article"
)
print(f"Found {len(result.organizations)} organizations")
print(f"Found {len(result.relations)} relationships")
```

### Entity Linking
Link extracted entities to knowledge bases:
- **Wikidata QIDs** - Structured knowledge graph
- **KIC Registry** - EIT ecosystem partners
- **Cross-modal** - Track entities across RoleBox modalities

```python
from rolebox_knowgen import EntityLinker

linker = EntityLinker(enable_wikidata_api=True)
linker.load_kic_registry("orgs_wikidata.csv")

linked = linker.link("TU Delft", "ORG")
print(f"QID: {linked.wikidata_qid}")  # Q1137652
print(f"KIC: {linked.kic_affiliation}")  # EIT Digital
```

### Powell Triangle Scoring
Classify entities on the knowledge triangle:
- **Associational**: Civil society, values, social purpose
- **Scientific**: Research, evidence, methodology
- **Managerial**: Business, efficiency, performance

```python
from rolebox_knowgen import TriangleScorer

scorer = TriangleScorer()
score = scorer.score("org1", "ETH Zurich", website_text)
print(f"Classification: {score.classification}")  # dominant_scientific
print(f"Coordinates: A={score.coord_associational:.2f}, S={score.coord_scientific:.2f}, M={score.coord_managerial:.2f}")
```

## Installation

```bash
# Install from source
pip install -e dissertation/data/rolebox-knowgen

# Or add to another module's dependencies
pip install -e ../rolebox-knowgen
```

## Requirements

- Python 3.9+
- [Ollama](https://ollama.ai/) with NuExtract model:
  ```bash
  ollama pull sroecker/nuextract-tiny-v1.5
  ```

## Modality Templates

### Wikipedia Organizations
```json
{
  "organizations": [{
    "name": "", "type": "", "country": "",
    "roles": [], "partnerships": [], "focus_areas": []
  }]
}
```

### News Articles
```json
{
  "main_actors": [{"name": "", "type": "", "role_in_story": ""}],
  "events": [{"event_type": "", "description": "", "date": ""}],
  "funding": [{"amount": "", "funder": "", "recipient": ""}],
  "relations": [{"source": "", "relation_type": "", "target": ""}]
}
```

### Organizational Websites
```json
{
  "organization": {"name": "", "type": "", "mission": ""},
  "roles_claimed": [{"role_identity": "", "practice": "", "counterroles": []}],
  "partnerships": [{"partner_name": "", "partnership_type": ""}],
  "programs": [{"name": "", "type": "", "target_audience": ""}]
}
```

## Architecture

```
rolebox-knowgen/
├── src/rolebox_knowgen/
│   ├── __init__.py
│   └── extraction/
│       ├── nuextract.py   # NuExtract structured extraction
│       ├── linker.py      # Entity linking (Wikidata + fuzzy)
│       └── triangle.py    # Powell Triangle scoring
└── pyproject.toml
```

## Usage in Other Modules

```python
# In rolebox-websites
from rolebox_knowgen import NuExtractExtractor, TriangleScorer

# Extract structured info from website content
extractor = NuExtractExtractor()
result = extractor.extract(website_html, "org1", modality="websites")

# Score on Powell triangle
scorer = TriangleScorer()
score = scorer.score("org1", "Company Name", website_text)
```

```python
# In rolebox-news
from rolebox_knowgen import NuExtractExtractor, EntityLinker

# Extract from news articles
extractor = NuExtractExtractor()
results = extractor.extract_batch(articles, modality="news", doc_type="article")

# Link entities across modalities
linker = EntityLinker()
linker.load_modality_entities("wikipedia", wiki_orgs)
linker.load_modality_entities("websites", website_orgs)

for org in results[0].organizations:
    linked = linker.link(org["name"], "ORG")
    print(f"{org['name']} found in: {linked.found_in_modalities}")
```
