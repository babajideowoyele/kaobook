# RoleBox Triads

Triad visualization framework for multimodal role constellation cartography.

## Overview

This package provides tools for visualizing organizational positions in ternary space across four triad types:

1. **Role Modalities**: Claimed (websites) vs Attributed (news) vs Enacted (Crunchbase)
2. **Powell Framework**: Associational vs Scientific vs Managerial legitimacy vocabularies
3. **Actor Types**: Conforming vs Interfacing vs Bridging field positions
4. **Multi-actor Perspective (MaP)**: State vs Market vs Community (Avelino & Wittmayer 2015)

## Installation

```bash
cd dissertation/data/rolebox-triads
pip install -e .
```

## Quick Start

```python
from rolebox_triads import (
    get_powell_framework_config,
    TriadNormalizer,
    TriadHTMLGenerator,
)
from rolebox_triads.triads import PowellFrameworkCalculator

# Load configuration
config = get_powell_framework_config()

# Calculate positions from text data
calculator = PowellFrameworkCalculator(config)
positions = calculator.calculate_from_triad_data(your_triad_data)

# Generate interactive HTML
generator = TriadHTMLGenerator(config)
generator.generate(positions, output_path="visualization.html")
```

## Demo

Run the demo script to generate sample visualizations:

```bash
python demo.py
```

This creates three interactive HTML files in the `ui/` directory.

## Features

### Visualization Types
- **Ternary scatter plots**: Organizations positioned in triangular space
- **Network overlays**: Relationships between organizations shown as edges
- **Animated transitions**: Movement across time periods (requires time-series data)

### Output Formats
- **Interactive HTML**: Self-contained with Plotly.js
- **Static PNG/PDF**: Publication-quality figures (300 DPI)
- **TikZ code**: For direct LaTeX inclusion

### Interactive Features
- Organization search
- Classification filtering
- Color by classification or confidence
- Size by confidence or raw totals
- Click for detailed info panel
- Export to PNG

## Architecture

```
rolebox-triads/
├── src/rolebox_triads/
│   ├── core/
│   │   ├── triad_config.py      # Triad type definitions
│   │   ├── normalizer.py        # Coordinate normalization
│   │   └── data_loader.py       # Load from rolebox-* modules
│   ├── triads/
│   │   ├── role_modalities.py   # Claimed vs Attributed vs Enacted
│   │   ├── powell_framework.py  # Associational vs Scientific vs Managerial
│   │   └── actor_types.py       # Conforming vs Interfacing vs Bridging
│   ├── visualization/
│   │   ├── html_generator.py    # Interactive HTML output
│   │   ├── ternary_scatter.py   # Basic ternary plots
│   │   └── ternary_network.py   # Ternary + network edges
│   └── export/
│       └── static_export.py     # PDF/PNG for LaTeX
├── ui/                          # Generated visualizations
├── data/configs/                # JSON configuration files
└── demo.py                      # Demo script
```

## Integration with RoleBox

The framework integrates with other RoleBox modules:

- **rolebox-websites**: Website text for Powell framework scoring
- **rolebox-news**: RIVETER-X analysis for attributed roles
- **rolebox-crunchbase**: Investment data for enacted roles
- **rolebox-social**: Network analysis for actor types

## API Reference

### Core Classes

- `TriadConfig`: Configuration for a triad type
- `TriadAxis`: Definition of a single axis
- `TriadNormalizer`: Normalize raw scores to ternary coordinates
- `OrganizationTriadPosition`: Complete position data for an organization
- `NetworkEdge`: Edge between two organizations

### Calculators

- `PowellFrameworkCalculator`: Associational/Scientific/Managerial scoring
- `RoleModalitiesCalculator`: Claimed/Attributed/Enacted scoring
- `ActorTypesCalculator`: Conforming/Interfacing/Bridging scoring
- `MultiActorPerspectiveCalculator`: State/Market/Community scoring (Avelino & Wittmayer 2015)

### Visualization

- `TriadHTMLGenerator`: Generate interactive HTML
- `TernaryScatterPlot`: Create Plotly ternary scatter
- `TernaryNetworkPlot`: Create ternary with network edges
- `StaticExporter`: Export PNG/PDF/SVG/TikZ

## Citation

```bibtex
@phdthesis{owoyele2025rolebox,
  author = {Owoyele, Babajide Alamu},
  title = {Towards Multimodal Cartography of Role Constellations in Sustainability Transitions},
  school = {Erasmus University Rotterdam},
  year = {2025}
}
```
