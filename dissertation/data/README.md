# RoleBox Dissertation Data Architecture

This directory contains Git submodules for supplementary data, analysis code, and interactive tools.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           KAOBOOK (Main Repository)                          │
│                    github.com/babajideowoyele/kaobook                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  dissertation/                                                               │
│  ├── main.tex              ← LaTeX source (Fira Sans)                       │
│  ├── main-ebgaramond.tex   ← LaTeX source (EB Garamond)                     │
│  │                                                                          │
│  ├── chapters/             ← 12 dissertation chapters                       │
│  │   ├── 01-introduction                                                    │
│  │   ├── 02-role-categories                                                 │
│  │   ├── 03-methodology                                                     │
│  │   ├── 04-role-constellations                                             │
│  │   ├── 05-interstitial-pluralism  ──┐                                     │
│  │   ├── 06-rolefield               ──┼── Empirical Studies                 │
│  │   ├── 07-venture-positioning     ──┤                                     │
│  │   ├── 08-visual-registers        ──┤                                     │
│  │   ├── 09-power-agency            ──┘                                     │
│  │   ├── 10-synthesis                                                       │
│  │   ├── 11-discussion                                                      │
│  │   └── 12-conclusion                                                      │
│  │                                                                          │
│  ├── intermezzos/          ← Bridge sections (tools)                        │
│  │   ├── eit-communities                                                    │
│  │   ├── rolexray          ──→ links to rolexray submodule                  │
│  │   ├── rolesim           ──→ links to rolesim submodule                   │
│  │   ├── roledna                                                            │
│  │   ├── multimodal-cartography                                             │
│  │   └── triangulation                                                      │
│  │                                                                          │
│  ├── appendices/           ← A-N appendices                                 │
│  │   ├── A-H: Methods & Documentation                                       │
│  │   ├── I-wikipedia-data  ──→ links to rolebox-wikipedia                   │
│  │   └── J-N: Data Modalities                                               │
│  │                                                                          │
│  └── data/                 ← SUBMODULES (this folder)                       │
│      ├── rolesim/          ✓ Agent-based simulation                         │
│      ├── rolexray/         ✓ Role extraction (METAFRASIA)                   │
│      ├── rolebox-wikipedia/✓ Wikipedia/Wikidata pipeline                    │
│      └── rolebox-data/     ○ Consolidated data (planned)                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Current Submodules

| Submodule | Status | Description | Source |
|-----------|--------|-------------|--------|
| `rolesim` | ✅ Active | Agent-based role simulation | [rolesim](https://github.com/babajideowoyele/rolesim) |
| `rolexray` | ✅ Active | Role extraction & classification | [rolexray](https://github.com/babajideowoyele/rolexray) |
| `rolebox-wikipedia` | ✅ Active | Wikipedia/Wikidata collection | [rolebox-wikipedia](https://github.com/babajideowoyele/rolebox-wikipedia) |
| `rolebox-data` | 🔲 Planned | Consolidated chapter data | TBD |

## Tool Submodules

### rolesim - Agent-Based Simulation
Python framework for simulating role dynamics in innovation ecosystems.
- Influence typology (ported from watch-complexity)
- Agent strategies: Exploit, Explore, Bridge, Specialize
- Network metrics and visualization

### rolexray - Role Extraction

NLP pipeline for extracting and classifying organizational roles from text.
- BERTopic + spaCy NLP backend
- Role taxonomy classification
- Discourse network analysis

### rolebox-wikipedia - Reference Data
Wikipedia/Wikidata collection for dissertation entities.
- 112 NetZeroCities pilot cities
- 133 EIT KIC partner organizations
- Carbon Design System UI with Plotly charts

## Quick Start

```bash
# Clone with all submodules
git clone --recurse-submodules https://github.com/babajideowoyele/kaobook.git

# Or initialize after clone
cd kaobook
git submodule init
git submodule update

# Run Wikipedia explorer
cd dissertation/data/rolebox-wikipedia/ui
python -m http.server 8000

# Run RoleXray
cd dissertation/data/rolexray
conda env create -f environment.yml
conda activate rolexray
```

## Adding Chapter Data Repos

When you provide the repos for chapters 05-09, they can be added as:

```bash
cd dissertation/data
git submodule add https://github.com/babajideowoyele/REPO_NAME.git
```

## Design Principles

1. **Carbon Design System**: All UIs use IBM Carbon for consistency
2. **Plotly + Sigma.js**: Interactive charts and network visualizations
3. **Python + JavaScript**: Analysis in Python, UIs in JavaScript
4. **Reproducibility**: Every analysis has scripts + sample data

## Citation

```bibtex
@phdthesis{owoyele2025rolebox,
  author = {Owoyele, Babajide Alamu},
  title = {Towards Multimodal Cartography of Role Constellations in Sustainability Transitions},
  school = {Erasmus University Rotterdam},
  year = {2025}
}
```
