# RoleBox Database Module

Unified SQLite database for annotation workflows across all RoleBox modalities.

## Purpose

This module provides persistent storage for human annotation tasks that require validation, coding, or labeling of extracted data. It supports:

- **Triplet validation** (rolebox-websites): Validate subject-predicate-object extractions
- **Venture classification** (rolebox-crunchbase): Classify company types and sectors
- **Visual coding** (rolebox-visual): Code visual elements and registers
- **Discourse coding** (rolebox-pydna): Code actor-concept relations

## Files

| File | Description |
|------|-------------|
| `schema.sql` | Database schema with all tables |
| `db.py` | Python interface (`RoleBoxDB` class) |
| `rolebox.db` | SQLite database file (generated on first use) |

## Usage

```python
from rolebox_db import RoleBoxDB

# Initialize database
db = RoleBoxDB()

# Create an annotation project
project_id = db.create_project(
    name="EIT KIC Website Triplets",
    module="rolebox-websites",
    description="Validate role triplets from EIT partner websites"
)

# Register an annotator
annotator_id = db.create_annotator(
    name="Research Assistant",
    email="ra@example.com"
)

# Start an annotation session
session_id = db.start_session(project_id, annotator_id)

# ... perform annotations ...

# End session
db.end_session(session_id)
```

## Schema Overview

```
projects ─────────┐
                  │
annotators ───────┼──── sessions
                  │
documents ────────┴──── annotations
  (per modality)         (per modality)
```

### Core Tables

- `projects`: Annotation projects (one per dataset/modality)
- `annotators`: Human coders
- `sessions`: Work sessions for tracking progress

### Modality-Specific Tables

- `website_documents`, `triplets`, `triplet_validations`
- `companies`, `company_classifications`
- `visual_items`, `visual_codings`
- `discourse_statements`, `discourse_codings`

## Inter-Annotator Reliability

The schema tracks multiple annotations per item to enable:

- Cohen's Kappa calculation
- Krippendorff's Alpha for ordinal scales
- Majority voting for gold labels

```python
# Get agreement statistics
stats = db.get_agreement_stats(project_id)
print(f"Kappa: {stats['kappa']:.3f}")
```

## Integration

Used by interactive HTML tools:

- `rolebox-triplets.html` - Triplet validation UI
- `rolebox-ventures.html` - Company classification UI
- `rolebox-vizreg.html` - Visual coding UI

## Dependencies

- Python 3.9+
- sqlite3 (standard library)

No external dependencies required.
