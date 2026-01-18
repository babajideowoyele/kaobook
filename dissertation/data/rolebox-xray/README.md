# RoleBox-Xray: Scientific Literature & Bibliometric Pipeline

Socio-semantic analysis of scientific literature to understand actors, topics, and role structures.

## Overview

This modality captures the **scientific roles** dimension of multimodal cartography - how actors and topics are positioned in scholarly discourse. The "X-ray" metaphor reflects seeing through literature to reveal underlying structures of knowledge production and actor positioning.

The methodology combines:
- **Semantic analysis**: What topics do actors write about?
- **Social analysis**: Who collaborates with whom?
- **Interstitial identification**: Who bridges separate communities?

## Data Sources

| Source | Description | Access |
|--------|-------------|--------|
| Web of Science | Citation database | API/Export |
| Scopus | Citation database | API |
| OpenAlex | Open bibliometric data | API |
| Semantic Scholar | AI-powered literature | API |

## Directory Structure

```
rolebox-xray/
├── data/
│   ├── raw/                    # Original bibliometric exports
│   └── processed/              # Cleaned/analyzed data
├── docs/                       # Methodology documentation
├── notebooks/                  # Jupyter analysis notebooks
├── outputs/
│   ├── figures/               # Generated visualizations
│   └── tables/                # Summary statistics
└── scripts/
    ├── collect/               # Data collection scripts
    └── analyze/               # Analysis pipelines
```

## Data Schema

### Article Data Fields

| Field | Type | Description |
|-------|------|-------------|
| article_id | str | Unique identifier (DOI/WOS ID) |
| title | str | Article title |
| authors | list | Author names |
| author_affiliations | list | Institution affiliations |
| journal | str | Journal name |
| year | int | Publication year |
| abstract | str | Article abstract |
| keywords | list | Author/index keywords |
| citations | int | Citation count |
| references | list | Cited references |

### Author Data Fields

| Field | Type | Description |
|-------|------|-------------|
| author_id | str | Unique author identifier |
| name | str | Author name |
| affiliations | list | Current/past affiliations |
| h_index | int | H-index |
| total_citations | int | Total citation count |
| coauthors | list | Co-author IDs |
| topics | list | Research topics |

### Topic Data Fields

| Field | Type | Description |
|-------|------|-------------|
| topic_id | str | Topic cluster ID |
| label | str | Human-readable label |
| keywords | list | Representative keywords |
| articles | int | Number of articles |
| trajectory | str | hot/cold/evergreen/wallflower |

## Methodology

### The Socio-Semantic X-Ray

Following the methodology developed in the dissertation's Intermezzo:

1. **Corpus Construction**: Collect articles from target journals/queries
2. **Topic Modeling**: BERTopic with sentence embeddings (all-MiniLM-L6-v2)
3. **Author Positioning**: Map authors in topic space
4. **Network Construction**: Co-authorship and citation networks
5. **Interstitial Detection**: Identify boundary-spanning actors

### The Chromatic Triangle

For multi-journal analysis, authors are positioned in a triangle where:
- Each vertex = pure discourse of one journal/community
- Position = mixture of discourses
- Center = interstitial (bridging all communities)

```python
# Calculate author position in discourse triangle
def calculate_position(author_topics, community_profiles):
    weights = []
    for community in community_profiles:
        similarity = cosine_similarity(author_topics, community)
        weights.append(similarity)
    return normalize(weights)  # Sum to 1.0
```

## Usage

### Topic Extraction

```python
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer

# Initialize models
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
topic_model = BERTopic(embedding_model=embedding_model)

# Fit on abstracts
topics, probs = topic_model.fit_transform(abstracts)
```

### Author Network Analysis

```python
import networkx as nx

# Build co-authorship network
G = nx.Graph()
for paper in papers:
    authors = paper['authors']
    for i, a1 in enumerate(authors):
        for a2 in authors[i+1:]:
            if G.has_edge(a1, a2):
                G[a1][a2]['weight'] += 1
            else:
                G.add_edge(a1, a2, weight=1)
```

## Related Chapters

- **Intermezzo: ROLEXRAY** - Methodology development and demonstration
- **Chapter 5: Interstitial Pluralism** - Application to EIT actor analysis
- **Chapter 10: Synthesis** - Integration with other modalities

## Key Analyses

1. **Topic Landscapes**: What themes dominate each community?
2. **Author Positioning**: Where do actors sit in topic space?
3. **Interstitial Authors**: Who bridges communities?
4. **Temporal Trajectories**: How do topics evolve (hot/cold/evergreen)?
5. **Collaboration Networks**: Who works with whom across boundaries?

## Sample Queries

### EIT-Related Literature
```
TOPIC: ("innovation intermediar*" OR "knowledge triangle" OR "EIT" OR "Knowledge Innovation Communit*")
AND YEAR: 2015-2024
```

### Sustainability Transitions
```
TOPIC: ("sustainability transition*" OR "socio-technical transition*" OR "multi-level perspective")
AND YEAR: 2010-2024
```

## Citation

```bibtex
@misc{rolebox2025xray,
  title = {RoleBox-Xray: Socio-Semantic Analysis of Scientific Literature},
  author = {Owoyele, Babajide Alamu},
  year = {2025},
  note = {Bibliometric analysis pipeline for dissertation research}
}
```

## See Also

- [BERTopic Documentation](https://maartengr.github.io/BERTopic/)
- [OpenAlex API](https://docs.openalex.org/)
- [Semantic Scholar API](https://api.semanticscholar.org/)
