# RoleBox-Visual: Visual Materials Pipeline

Images, graphics, and visual content from EIT ecosystem communications.

## Overview

This modality captures the **embodied roles** dimension of multimodal cartography - how roles are materially performed through imagery and visual semiotics. Visual materials reveal institutional identity construction that verbal language alone cannot capture.

## Data Sources

| Source | Description | Access |
|--------|-------------|--------|
| Organization Websites | Logos, photos, graphics | Web scraping |
| Social Media | Posted images | API |
| Annual Reports | Document imagery | PDF extraction |
| Press Releases | Accompanying visuals | Web scraping |

## Directory Structure

```
rolebox-visual/
├── data/
│   ├── raw/                    # Original images
│   │   ├── websites/
│   │   ├── social/
│   │   └── reports/
│   └── processed/              # Analyzed/annotated images
├── docs/                       # Methodology documentation
├── notebooks/                  # Jupyter analysis notebooks
├── outputs/
│   ├── figures/               # Generated visualizations
│   └── tables/                # Coding results
└── scripts/
    ├── collect/               # Image collection scripts
    └── analyze/               # Computer vision pipelines
```

## Data Schema

### Image Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| image_id | str | Unique image identifier |
| source_url | str | Original URL |
| org_id | str | Associated organization |
| collection_date | date | Date collected |
| file_path | str | Local storage path |
| format | str | jpg/png/svg |
| width | int | Pixel width |
| height | int | Pixel height |

### Visual Coding Fields (Kress & van Leeuwen)

| Field | Type | Description |
|-------|------|-------------|
| content_type | str | people/technology/nature/abstract |
| people_count | int | Number of people depicted |
| gender_coding | str | male/female/mixed/unclear |
| contact | str | demand/offer (gaze direction) |
| distance | str | intimate/social/impersonal |
| angle | str | frontal/oblique/vertical |
| coding_orientation | str | naturalistic/sensory/technological/abstract |
| modality_markers | list | Color saturation, detail, depth |

## Usage

### Key Analyses

1. **Visual Register Analysis**: Patterns in how innovation is visually constructed
2. **Gender Representation**: Coding of gender in EIT imagery
3. **Three Gazes**: Partnership, Impact, Talent orientations (Chapter 8)
4. **Cross-KIC Comparison**: Visual identity differences

### Computer Vision Pipeline

```python
from transformers import pipeline
import face_recognition

# Face detection
face_detector = pipeline("object-detection", model="facebook/detr-resnet-50")

# Image classification
classifier = pipeline("image-classification")

# Scene understanding
def analyze_image(image_path):
    # Detect faces
    faces = face_recognition.face_locations(image)
    # Classify scene
    scene = classifier(image_path)
    return {'faces': len(faces), 'scene': scene}
```

## Related Chapters

- **Chapter 8: Visual Registers** - Primary analysis chapter
- **Chapter 10: Synthesis** - Visual vs. verbal register gaps

## Analytical Framework

Following Kress & van Leeuwen's *Reading Images* (2006):

### Ideational Metafunction
- **Participants**: Who/what is depicted
- **Processes**: Actions/states represented
- **Circumstances**: Settings, tools, contexts

### Interpersonal Metafunction
- **Contact**: Demand (direct gaze) vs. Offer (away)
- **Distance**: Intimate, Social, Impersonal
- **Angle**: Power relations (high/low/eye-level)

### Textual Metafunction
- **Composition**: Layout, Given/New, Ideal/Real
- **Framing**: Connection/disconnection of elements
- **Salience**: What draws attention

## Ethical Considerations

- Privacy: No analysis of identifiable individuals without consent
- Consent: Public communications only
- Storage: Secure handling of image files
- Bias: Awareness of CV model limitations

## Citation

```bibtex
@misc{rolebox2025visual,
  title = {EIT Ecosystem Visual Materials Dataset},
  author = {Owoyele, Babajide Alamu},
  year = {2025},
  note = {Visual content collection for dissertation research}
}

@book{kress2006reading,
  title = {Reading Images: The Grammar of Visual Design},
  author = {Kress, Gunther and Van Leeuwen, Theo},
  year = {2006},
  publisher = {Routledge},
  edition = {2nd}
}
```
