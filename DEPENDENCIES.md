# Dependencies

This document lists the minimum requirements and dependencies for the kaobook class.

## TeX Distribution

**Minimum recommended:** TeX Live 2020 or later

| Distribution | Minimum Version | Notes |
|-------------|-----------------|-------|
| TeX Live | 2020+ | Full scheme recommended |
| MiKTeX | 21.1+ | Install packages on-the-fly |
| MacTeX | 2020+ | Full installation |

## LaTeX Engine

kaobook supports multiple engines with varying feature sets:

| Engine | Support | Font Features | Recommended |
|--------|---------|---------------|-------------|
| LuaLaTeX | Full | All (OpenType, Unicode) | ✅ Yes |
| XeLaTeX | Full | All (OpenType, Unicode) | ✅ Yes |
| pdfLaTeX | Partial | Limited (Type1 fonts) | For compatibility only |

**Recommendation:** Use LuaLaTeX for best results, especially with custom fonts.

## Required Packages

These packages are loaded automatically by kaobook and must be available:

### Core (kao.sty)

| Package | Minimum Version | Purpose |
|---------|-----------------|---------|
| KOMA-Script | 3.25+ | Base class (scrbook, scrreport) |
| kvoptions | 3.10+ | Package options handling |
| etoolbox | 2.5+ | LaTeX programming utilities |
| calc | — | Length calculations |
| xcolor | 2.12+ | Color support |
| iftex | 1.0+ | Engine detection |
| xifthen | 1.4+ | Conditional commands |
| xparse | 3+ | Argument parsing (part of LaTeX3) |
| xpatch | 0.3+ | Code patching |
| xstring | 1.7+ | String manipulation |
| afterpage | 1.08+ | Deferred commands |
| imakeidx | 1.3+ | Index generation |
| varioref | 1.6+ | Cross-references |
| scrhack | 3.25+ | KOMA-Script compatibility |

### Layout & Typography

| Package | Purpose |
|---------|---------|
| geometry | Page layout |
| marginfix | Margin note fixes |
| changepage | Detect odd/even pages |
| placeins | Float barriers |
| ragged2e | Better ragged text |
| setspace | Line spacing |
| footmisc | Footnote customization |

### Graphics & Tables

| Package | Purpose |
|---------|---------|
| graphicx | Image inclusion |
| tikz | Vector graphics |
| booktabs | Professional tables |
| multirow | Multi-row cells |
| makecell | Cell formatting |
| caption | Caption customization |

### Hyperlinks & References

| Package | Purpose |
|---------|---------|
| hyperref | Hyperlinks and PDF metadata |
| bookmark | PDF bookmarks |
| nameref | Name references |

## Optional Packages

### Bibliography (kaobiblio.sty)

| Package | Version | Notes |
|---------|---------|-------|
| biblatex | 3.12+ | Modern bibliography management |
| biber | 2.12+ | Backend for biblatex |

### Theorems (kaotheorems.sty)

| Package | Purpose |
|---------|---------|
| amsmath | Math typesetting |
| amsthm | Theorem environments |
| thmtools | Theorem customization |
| tcolorbox | Colored boxes (optional) |

### References (kaorefs.sty)

| Package | Purpose |
|---------|---------|
| cleveref | Smart cross-references |
| hyperref | Hyperlinked references |

### Fonts (kaofonts.sty)

For LuaLaTeX/XeLaTeX:
| Package | Purpose |
|---------|---------|
| fontspec | OpenType font loading |

For pdfLaTeX fallback:
| Package | Purpose |
|---------|---------|
| inputenc | Input encoding |
| fontenc | Font encoding |

### Glossaries & Nomenclature

| Package | External Tool | Purpose |
|---------|---------------|---------|
| glossaries | makeglossaries | Glossary/acronyms |
| nomencl | makeindex | Nomenclature lists |

## External Tools

For full functionality, these tools should be available:

| Tool | Purpose | Required For |
|------|---------|--------------|
| biber | Bibliography processing | Citations |
| makeindex | Index generation | Index, nomenclature |
| makeglossaries | Glossary processing | Glossaries |
| latexmk | Build automation | Recommended |

## Checking Your Installation

Run this command to verify your TeX installation:

```bash
# Check TeX Live version
tex --version

# Check available engines
lualatex --version
xelatex --version
pdflatex --version

# Check biber
biber --version

# Verify a key package
kpsewhich kaobook.cls
```

## Troubleshooting

### "Package not found" errors

```bash
# TeX Live
tlmgr install <package-name>

# MiKTeX (usually auto-installs)
mpm --install=<package-name>
```

### KOMA-Script version issues

If you see errors about `\Ifthispageodd`, update KOMA-Script:
```bash
tlmgr update koma-script
```

### Font issues with pdfLaTeX

pdfLaTeX has limited font support. Switch to LuaLaTeX:
```latex
% In .latexmkrc
$pdf_mode = 4;  % Use lualatex
```

## Version History

| kaobook Version | TeX Live | Notes |
|-----------------|----------|-------|
| 0.9.8 | 2022+ | Current stable |
| 0.9.7 | 2021+ | — |
| 0.9.6 | 2020+ | Minimum recommended |
