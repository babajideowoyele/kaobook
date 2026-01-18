# RoleBox Dissertation Data Architecture

This directory contains data pipelines and submodules for multimodal role constellation cartography.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           KAOBOOK (Main Repository)                          │
│                    github.com/babajideowoyele/kaobook                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  dissertation/data/                                                          │
│  │                                                                          │
│  ├── MODALITY PIPELINES ─────────────────────────────────────────────────   │
│  │   ├── rolebox-wikipedia/    ✓ Reference data (Wikidata)                  │
│  │   ├── rolebox-websites/     ○ Claimed roles (web text)                   │
│  │   ├── rolebox-crunchbase/   ✓ Resourced roles (investment)              │
│  │   ├── rolebox-news/         ○ Attributed roles (media)                   │
│  │   ├── rolebox-social/       ○ Relational roles (Twitter)                 │
│  │   ├── rolebox-visual/       ○ Embodied roles (imagery)                   │
│  │   └── rolebox-xray/         ○ Scientific roles (bibliometrics)           │
│  │                                                                          │
│  ├── TOOL SUBMODULES ────────────────────────────────────────────────────   │
│  │   ├── rolesim/              ✓ Agent-based simulation                     │
│  │   └── rolebox-pydna/        ○ Discourse Network Analysis (Python)        │
│  │                                                                          │
│  └── Legend: ✓ = Active/Data present, ○ = Structure ready                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Seven Data Modalities

The multimodal cartography framework integrates seven complementary data sources:

| Modality | Folder | Role Dimension | Key Data |
|----------|--------|----------------|----------|
| **Wikipedia/Wikidata** | `rolebox-wikipedia/` | Reference | Structured entity data |
| **Websites** | `rolebox-websites/` | Claimed | Self-presentation text |
| **Crunchbase** | `rolebox-crunchbase/` | Resourced | Investment & funding |
| **News Media** | `rolebox-news/` | Attributed | Media coverage |
| **Social Media** | `rolebox-social/` | Relational | Network discourse |
| **Visual Materials** | `rolebox-visual/` | Embodied | Imagery & graphics |
| **Scientific Literature** | `rolebox-xray/` | Scientific | Bibliometric/topic data |

### Modality-Chapter Mapping

```
Modality          Primary Chapter              Integration
─────────────────────────────────────────────────────────────
Wikipedia     →   Appendix I                   Entity resolution
Websites      →   Ch.5 Interstitial Pluralism  Role vocabulary
Crunchbase    →   Ch.7 Venture Positioning     Portfolio analysis
News Media    →   Ch.9 Power & Agency          Discourse analysis
Social Media  →   Ch.5 Interstitial Pluralism  Network positions
Visual        →   Ch.8 Visual Registers        Semiotic analysis
Xray          →   Intermezzo: ROLEXRAY         Topic/author analysis
─────────────────────────────────────────────────────────────
All           →   Ch.10 Synthesis              Cross-modal integration
```

## Standard Directory Structure

Each modality folder follows a consistent structure:

```
rolebox-{modality}/
├── README.md              # Modality documentation
├── data/
│   ├── raw/              # Original/unprocessed data
│   └── processed/        # Cleaned/transformed data
├── docs/                 # Methodology documentation
├── notebooks/            # Jupyter analysis notebooks
├── outputs/
│   ├── figures/         # Generated visualizations
│   └── tables/          # Summary statistics
└── scripts/
    ├── collect/         # Data collection scripts
    └── analyze/         # Analysis pipelines
```

## Tool Submodules

### rolesim - Agent-Based Simulation

Python framework for simulating role dynamics in innovation ecosystems.

- Influence typology metrics
- Agent strategies: Exploit, Explore, Bridge, Specialize
- Network metrics and visualization

### rolebox-wikipedia - Reference Data

Wikipedia/Wikidata collection for dissertation entities.

- 112 NetZeroCities pilot cities
- 133 EIT KIC partner organizations
- Carbon Design System UI

### rolebox-xray - Socio-Semantic Analysis

Bibliometric and topic analysis pipeline (formerly "rolexray").

- BERTopic + sentence embeddings for topic modeling
- Author positioning in discourse space
- Interstitial author detection
- Co-authorship network analysis

### rolebox-pydna - Discourse Network Analysis

Python reimplementation of Philip Leifeld's Discourse Network Analyzer.

- Web-based interface (FastAPI + Carbon Design System)
- Actor-concept affiliation networks
- Congruence/conflict network projections
- LLM-assisted coding potential

## Quick Start

```bash
# Clone with all submodules
git clone --recurse-submodules https://github.com/babajideowoyele/kaobook.git

# Or initialize after clone
cd kaobook
git submodule init
git submodule update

# Explore Crunchbase data
cd dissertation/data/rolebox-crunchbase
python -c "import pandas as pd; df = pd.read_csv('data/raw/eit_companies-11-29-2025.csv'); print(f'Companies: {len(df)}')"
```

## Data Summary

| Modality | Records | Status | Last Updated |
|----------|---------|--------|--------------|
| Wikipedia | 245 entities | Active | 2025-01 |
| Websites | 20 sample | Structure ready | 2025-01 |
| Crunchbase | 654 companies | Active | 2025-11-29 |
| News | 20 sample | Structure ready | 2025-01 |
| Social | 20 sample | Structure ready | 2025-01 |
| Visual | 25 sample | Structure ready | 2025-01 |
| Xray | 10 sample | Structure ready | 2025-01 |

## Design Principles

1. **Consistent Structure**: All modalities follow the same folder layout
2. **Reproducibility**: Scripts + documentation for all data collection
3. **Modularity**: Each modality can be used independently
4. **Integration**: Common entity IDs enable cross-modal linking

## Citation

```bibtex
@phdthesis{owoyele2025rolebox,
  author = {Owoyele, Babajide Alamu},
  title = {Towards Multimodal Cartography of Role Constellations in Sustainability Transitions},
  school = {Erasmus University Rotterdam},
  year = {2025}
}
```
