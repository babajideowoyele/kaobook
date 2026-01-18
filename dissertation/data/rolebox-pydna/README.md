# RoleBox-PyDNA: Python Discourse Network Analysis

A Python reimplementation of Philip Leifeld's Discourse Network Analyzer (DNA), providing web-accessible discourse network analysis with modern Python tooling.

## Overview

RoleBox-PyDNA (previously ROLEDNA) is a Python platform for Discourse Network Analysis - a method combining qualitative content analysis with quantitative network methods to study how actors position themselves relative to concepts, claims, and each other in policy debates.

The "PyDNA" name reflects:
- **Py**: Python reimplementation (vs. original Java/R)
- **DNA**: Discourse Network Analysis heritage

## Background: The Original DNA

The Discourse Network Analyzer was created by Philip Leifeld (2009), enabling systematic coding of actor-concept relationships from policy documents, news articles, and parliamentary debates. The original tool:
- Written in Java (GUI) with R package (rDNA) for analysis
- Desktop-based application
- Extensive features for manual annotation

## Why Python?

Three developments motivate the Python reimplementation:

| Motivation | Original DNA | PyDNA Approach |
|------------|--------------|----------------|
| **Accessibility** | Desktop Java app | Web-based (FastAPI + browser) |
| **Ecosystem** | Java GUI + R analysis | Single Python environment |
| **AI Integration** | Manual coding only | LLM-assisted coding potential |

## Technical Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Browser Interface                        │
│              (Carbon Design System + Sigma.js)               │
├──────────────────────────────────────────────────────────────┤
│                     FastAPI Backend                          │
│              (REST API + Jinja2 Templates)                   │
├──────────────────────────────────────────────────────────────┤
│                   SQLAlchemy Async                           │
│              (SQLite / PostgreSQL)                           │
├──────────────────────────────────────────────────────────────┤
│                   Core Analysis                              │
│     (NetworkX + Pandas + Sentence Transformers)              │
└──────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.11+) |
| Database | SQLAlchemy async + SQLite/PostgreSQL |
| Templates | Jinja2 |
| Styling | IBM Carbon Design System |
| Visualization | Sigma.js + Graphology |
| Analysis | NetworkX, Pandas, NumPy |

## Directory Structure

```
rolebox-pydna/
├── README.md              # This file
├── data/
│   ├── raw/              # Source documents for coding
│   └── processed/        # Exported networks and analyses
├── docs/                 # Methodology documentation
├── notebooks/            # Jupyter analysis notebooks
├── outputs/
│   ├── figures/         # Generated visualizations
│   └── tables/          # Summary statistics
├── scripts/
│   ├── collect/         # Document collection scripts
│   └── analyze/         # Network analysis pipelines
└── src/
    └── roledna/         # Python package source
        ├── __init__.py
        ├── api/         # FastAPI routes
        ├── models/      # SQLAlchemy models
        ├── analysis/    # Network computations
        └── ui/          # Jinja2 templates
```

## Core Concepts

### Data Model

```
Document (source text)
    └── Statement (coded annotation)
            ├── Actor (who said it)
            ├── Concept (what was said)
            └── Qualifier (+1 agree / -1 disagree)
```

### Network Types

| Network | Description | Use Case |
|---------|-------------|----------|
| **Two-Mode** | Bipartite actor-concept affiliations | What concepts do actors reference? |
| **Actor Congruence** | Actors sharing positions | Who allies with whom? |
| **Actor Conflict** | Actors with opposing positions | Who opposes whom? |
| **Concept Co-occurrence** | Concepts mentioned together | Which ideas cluster? |

### Normalization Options

| Method | Formula | When to Use |
|--------|---------|-------------|
| Raw | Count | Compare absolute activity |
| Jaccard | A∩B / A∪B | Symmetric similarity |
| Cosine | A·B / (‖A‖‖B‖) | Directional similarity |
| Average Activity | 2(A∩B) / (‖A‖+‖B‖) | Balanced normalization |

## Usage

### Quick Start

```python
from roledna import Project, Document, Statement

# Create project
project = Project(name="Climate Policy Debate")

# Add documents
doc = Document(
    title="COP28 Press Release",
    source="UNFCCC",
    date="2023-12-01",
    text="The European Union committed to carbon neutrality..."
)
project.add_document(doc)

# Code statements
statement = Statement(
    document=doc,
    actor="European Union",
    concept="Carbon Neutrality",
    qualifier=1,  # Agreement
    text_selection="committed to carbon neutrality"
)
doc.add_statement(statement)

# Export network
network = project.export_network(
    type="actor_congruence",
    normalize="cosine"
)
```

### Web Interface

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn roledna.main:app --reload

# Open browser to http://localhost:8000
```

## Current Limitations

PyDNA is a proof-of-concept, not a production system. Missing features compared to original DNA:

- [ ] Regex-based entity detection
- [ ] Statement inheritance
- [ ] Multiple qualifier dimensions
- [ ] Network backbone extraction
- [ ] Time window analysis
- [ ] Import/export DNA format

## Future Directions

### LLM-Assisted Coding

```python
from roledna.llm import CodingAssistant

assistant = CodingAssistant(model="gpt-4")

# Suggest statements for human review
suggestions = assistant.suggest_statements(
    document=doc,
    actors=project.actors,
    concepts=project.concepts
)

for suggestion in suggestions:
    if human_approves(suggestion):
        doc.add_statement(suggestion.to_statement())
```

### NLP Pipeline Integration

- Named Entity Recognition for actor detection
- Coreference resolution for entity linking
- Stance detection for qualifier inference
- Topic modeling for concept discovery

### RoleBox Integration

PyDNA could integrate with other RoleBox modalities:
- Compare discourse positions to network positions
- Validate claimed roles against enacted roles
- Cross-reference actor positions across modalities

## Related Chapters

- **Chapter: ROLEDNA** - Technical architecture and methodology
- **Chapter 9: Power & Agency** - Discourse analysis application
- **Chapter 10: Synthesis** - Cross-modal integration

## References

### Original DNA

```bibtex
@article{leifeld2013reconstructing,
  title={Reconstructing policy networks: Using qualitative data to quantify
         policy discourse spaces},
  author={Leifeld, Philip},
  journal={Political Analysis},
  volume={21},
  number={4},
  pages={440--458},
  year={2013}
}
```

### PyDNA/ROLEDNA

```bibtex
@misc{owoyele2025pydna,
  title = {RoleBox-PyDNA: Python Discourse Network Analysis},
  author = {Owoyele, Babajide Alamu},
  year = {2025},
  note = {Python reimplementation of Discourse Network Analyzer}
}
```

## See Also

- [Original DNA](https://github.com/leifeld/dna) - Philip Leifeld's Discourse Network Analyzer
- [rDNA](https://cran.r-project.org/package=rDNA) - R package for DNA
- [NetworkX](https://networkx.org/) - Network analysis in Python
- [Sigma.js](https://www.sigmajs.org/) - Graph visualization
