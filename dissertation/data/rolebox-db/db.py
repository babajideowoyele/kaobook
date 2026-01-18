"""
RoleBox Database Module

Unified database operations for all RoleBox annotation workflows.
Supports SQLite for local development and can be extended to PostgreSQL.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent / "rolebox.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class RoleBoxDB:
    """Database interface for RoleBox annotation system."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_schema()

    def _ensure_schema(self):
        """Create database and tables if they don't exist."""
        with self._connect() as conn:
            with open(SCHEMA_PATH, "r") as f:
                conn.executescript(f.read())

    @contextmanager
    def _connect(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _generate_id(prefix: str = "") -> str:
        """Generate a unique ID with optional prefix."""
        return f"{prefix}{uuid.uuid4().hex[:12]}"

    # ========================================================================
    # PROJECT MANAGEMENT
    # ========================================================================

    def create_project(
        self, name: str, module: str, description: str = ""
    ) -> str:
        """Create a new annotation project."""
        project_id = self._generate_id("proj_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO projects (project_id, name, module, description)
                VALUES (?, ?, ?, ?)
                """,
                (project_id, name, module, description),
            )
        return project_id

    def get_projects(self, module: Optional[str] = None) -> List[Dict]:
        """Get all projects, optionally filtered by module."""
        with self._connect() as conn:
            if module:
                rows = conn.execute(
                    "SELECT * FROM projects WHERE module = ?", (module,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM projects").fetchall()
            return [dict(row) for row in rows]

    # ========================================================================
    # ANNOTATOR MANAGEMENT
    # ========================================================================

    def create_annotator(self, name: str, email: Optional[str] = None) -> str:
        """Register a new annotator."""
        annotator_id = self._generate_id("ann_")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO annotators (annotator_id, name, email) VALUES (?, ?, ?)",
                (annotator_id, name, email),
            )
        return annotator_id

    def get_annotator(self, annotator_id: str) -> Optional[Dict]:
        """Get annotator by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM annotators WHERE annotator_id = ?", (annotator_id,)
            ).fetchone()
            return dict(row) if row else None

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    def start_session(self, project_id: str, annotator_id: str) -> str:
        """Start a new annotation session."""
        session_id = self._generate_id("sess_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_id, project_id, annotator_id)
                VALUES (?, ?, ?)
                """,
                (session_id, project_id, annotator_id),
            )
        return session_id

    def end_session(self, session_id: str, items_coded: int = 0):
        """End an annotation session."""
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET ended_at = CURRENT_TIMESTAMP, items_coded = ?
                WHERE session_id = ?
                """,
                (items_coded, session_id),
            )

    # ========================================================================
    # TRIPLET OPERATIONS (rolebox-websites)
    # ========================================================================

    def add_triplet(
        self,
        doc_id: str,
        subject: str,
        predicate: str,
        obj: str,
        subject_normalized: Optional[str] = None,
        predicate_normalized: Optional[str] = None,
        object_normalized: Optional[str] = None,
        source_text: Optional[str] = None,
    ) -> str:
        """Add an extracted triplet."""
        triplet_id = self._generate_id("tri_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO triplets
                (triplet_id, doc_id, subject, predicate, object,
                 subject_normalized, predicate_normalized, object_normalized, source_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    triplet_id, doc_id, subject, predicate, obj,
                    subject_normalized, predicate_normalized, object_normalized, source_text
                ),
            )
        return triplet_id

    def validate_triplet(
        self,
        triplet_id: str,
        annotator_id: str,
        session_id: str,
        status: str,
        corrected_subject: Optional[str] = None,
        corrected_predicate: Optional[str] = None,
        corrected_object: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Record a triplet validation."""
        validation_id = self._generate_id("val_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO triplet_validations
                (validation_id, triplet_id, annotator_id, session_id, status,
                 corrected_subject, corrected_predicate, corrected_object, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    validation_id, triplet_id, annotator_id, session_id, status,
                    corrected_subject, corrected_predicate, corrected_object, notes
                ),
            )
        return validation_id

    def get_triplet_progress(self, project_id: str) -> Dict:
        """Get triplet validation progress for a project."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM v_triplet_progress WHERE project_id = ?",
                (project_id,)
            ).fetchone()
            return dict(row) if row else {}

    # ========================================================================
    # COMPANY OPERATIONS (rolebox-crunchbase)
    # ========================================================================

    def add_company(
        self,
        project_id: str,
        name: str,
        location: Optional[str] = None,
        description: Optional[str] = None,
        founded_year: Optional[int] = None,
        total_funding: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Add a company to the database."""
        company_id = self._generate_id("comp_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO companies
                (company_id, project_id, name, location, description,
                 founded_year, total_funding, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company_id, project_id, name, location, description,
                    founded_year, total_funding, json.dumps(metadata) if metadata else None
                ),
            )
        return company_id

    def classify_company(
        self,
        company_id: str,
        annotator_id: str,
        session_id: str,
        role_type: str,
        validated_kics: List[str],
        notes: Optional[str] = None,
    ) -> str:
        """Record a company classification."""
        classification_id = self._generate_id("cls_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO company_classifications
                (classification_id, company_id, annotator_id, session_id,
                 role_type, validated_kics, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    classification_id, company_id, annotator_id, session_id,
                    role_type, json.dumps(validated_kics), notes
                ),
            )
        return classification_id

    # ========================================================================
    # SOCIAL ACTOR OPERATIONS (rolebox-social)
    # ========================================================================

    def add_social_actor(
        self,
        project_id: str,
        handle: str,
        name: Optional[str] = None,
        bio: Optional[str] = None,
        community: Optional[str] = None,
        degree: Optional[int] = None,
        betweenness: Optional[float] = None,
        clustering: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Add a social network actor."""
        actor_id = self._generate_id("act_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO social_actors
                (actor_id, project_id, handle, name, bio, community,
                 degree, betweenness, clustering, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    actor_id, project_id, handle, name, bio, community,
                    degree, betweenness, clustering,
                    json.dumps(metadata) if metadata else None
                ),
            )
        return actor_id

    def code_actor(
        self,
        actor_id: str,
        annotator_id: str,
        session_id: str,
        network_role: str,
        actor_type: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Record an actor role coding."""
        coding_id = self._generate_id("cod_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO actor_codings
                (coding_id, actor_id, annotator_id, session_id,
                 network_role, actor_type, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (coding_id, actor_id, annotator_id, session_id, network_role, actor_type, notes),
            )
        return coding_id

    # ========================================================================
    # IMAGE OPERATIONS (rolebox-visual)
    # ========================================================================

    def add_image(
        self,
        project_id: str,
        filename: str,
        url: Optional[str] = None,
        org_id: Optional[str] = None,
        org_name: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Add an image to the database."""
        image_id = self._generate_id("img_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO images
                (image_id, project_id, filename, url, org_id, org_name, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    image_id, project_id, filename, url, org_id, org_name,
                    json.dumps(metadata) if metadata else None
                ),
            )
        return image_id

    def code_image(
        self,
        image_id: str,
        annotator_id: str,
        session_id: str,
        participants: Optional[str] = None,
        contact: Optional[str] = None,
        distance: Optional[str] = None,
        angle: Optional[str] = None,
        orientation: Optional[str] = None,
        gaze_type: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Record an image coding."""
        coding_id = self._generate_id("icod_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO image_codings
                (coding_id, image_id, annotator_id, session_id,
                 participants, contact, distance, angle, orientation, gaze_type, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    coding_id, image_id, annotator_id, session_id,
                    participants, contact, distance, angle, orientation, gaze_type, notes
                ),
            )
        return coding_id

    # ========================================================================
    # WIKIPEDIA ENTITY OPERATIONS (rolebox-wikipedia)
    # ========================================================================

    def add_wikipedia_entity(
        self,
        project_id: str,
        name: str,
        entity_type: str = "organization",
        qid: Optional[str] = None,
        wikipedia_title: Optional[str] = None,
        wikipedia_url: Optional[str] = None,
        summary: Optional[str] = None,
        text_length: Optional[int] = None,
        kic: Optional[str] = None,
        country: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Add a Wikipedia entity."""
        entity_id = self._generate_id("wiki_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO wikipedia_entities
                (entity_id, project_id, qid, entity_type, name, wikipedia_title,
                 wikipedia_url, summary, text_length, kic, country, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity_id, project_id, qid, entity_type, name, wikipedia_title,
                    wikipedia_url, summary, text_length, kic, country,
                    json.dumps(metadata) if metadata else None
                ),
            )
        return entity_id

    def add_entity_triangle_score(
        self,
        entity_id: str,
        framework: str,
        axis_a_score: float,
        axis_b_score: float,
        axis_c_score: float,
        classification: str,
        method: str = "keyword",
        metadata: Optional[Dict] = None,
    ) -> str:
        """Add a triangle score for an entity."""
        score_id = self._generate_id("tscore_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO entity_triangle_scores
                (score_id, entity_id, framework, axis_a_score, axis_b_score,
                 axis_c_score, classification, method, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    score_id, entity_id, framework, axis_a_score, axis_b_score,
                    axis_c_score, classification, method,
                    json.dumps(metadata) if metadata else None
                ),
            )
        return score_id

    def annotate_entity(
        self,
        entity_id: str,
        annotator_id: str,
        session_id: str,
        framework: str,
        corrected_classification: Optional[str] = None,
        corrected_axis_a: Optional[float] = None,
        corrected_axis_b: Optional[float] = None,
        corrected_axis_c: Optional[float] = None,
        confidence: str = "medium",
        notes: Optional[str] = None,
    ) -> str:
        """Record an entity annotation."""
        annotation_id = self._generate_id("eann_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO entity_annotations
                (annotation_id, entity_id, annotator_id, session_id, framework,
                 corrected_classification, corrected_axis_a, corrected_axis_b,
                 corrected_axis_c, confidence, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    annotation_id, entity_id, annotator_id, session_id, framework,
                    corrected_classification, corrected_axis_a, corrected_axis_b,
                    corrected_axis_c, confidence, notes
                ),
            )
        return annotation_id

    def get_wikipedia_entities(
        self, project_id: str, entity_type: Optional[str] = None
    ) -> List[Dict]:
        """Get all Wikipedia entities for a project."""
        with self._connect() as conn:
            if entity_type:
                rows = conn.execute(
                    """SELECT * FROM wikipedia_entities
                       WHERE project_id = ? AND entity_type = ?""",
                    (project_id, entity_type)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM wikipedia_entities WHERE project_id = ?",
                    (project_id,)
                ).fetchall()
            return [dict(row) for row in rows]

    # ========================================================================
    # TRIAD OPERATIONS (rolebox-triads)
    # ========================================================================

    def add_triad_organization(
        self,
        project_id: str,
        name: str,
        external_id: Optional[str] = None,
        source_modality: Optional[str] = None,
        kic_sectors: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Add an organization for triad positioning."""
        org_id = self._generate_id("torg_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO triad_organizations
                (org_id, project_id, name, external_id, source_modality, kic_sectors, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    org_id, project_id, name, external_id, source_modality,
                    json.dumps(kic_sectors) if kic_sectors else None,
                    json.dumps(metadata) if metadata else None
                ),
            )
        return org_id

    def add_triad_position(
        self,
        org_id: str,
        triad_type: str,
        raw_a: float,
        raw_b: float,
        raw_c: float,
        coord_a: float,
        coord_b: float,
        coord_c: float,
        classification: str,
        confidence: Optional[float] = None,
        method: str = "keyword",
        metadata: Optional[Dict] = None,
    ) -> str:
        """Add a computed triad position."""
        position_id = self._generate_id("tpos_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO triad_positions
                (position_id, org_id, triad_type, raw_a, raw_b, raw_c,
                 coord_a, coord_b, coord_c, classification, confidence, method, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    position_id, org_id, triad_type, raw_a, raw_b, raw_c,
                    coord_a, coord_b, coord_c, classification, confidence, method,
                    json.dumps(metadata) if metadata else None
                ),
            )
        return position_id

    def annotate_triad_position(
        self,
        org_id: str,
        annotator_id: str,
        session_id: str,
        triad_type: str,
        position_id: Optional[str] = None,
        manual_coord_a: Optional[float] = None,
        manual_coord_b: Optional[float] = None,
        manual_coord_c: Optional[float] = None,
        manual_classification: Optional[str] = None,
        validated: Optional[bool] = None,
        adjustment_reason: Optional[str] = None,
        confidence: str = "medium",
        notes: Optional[str] = None,
    ) -> str:
        """Record a manual triad position annotation."""
        annotation_id = self._generate_id("tann_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO triad_annotations
                (annotation_id, position_id, org_id, annotator_id, session_id,
                 triad_type, manual_coord_a, manual_coord_b, manual_coord_c,
                 manual_classification, validated, adjustment_reason, confidence, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    annotation_id, position_id, org_id, annotator_id, session_id,
                    triad_type, manual_coord_a, manual_coord_b, manual_coord_c,
                    manual_classification, validated, adjustment_reason, confidence, notes
                ),
            )
        return annotation_id

    def add_triad_edge(
        self,
        project_id: str,
        source_org_id: str,
        target_org_id: str,
        edge_type: str,
        weight: float = 1.0,
        source_modality: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Add a network edge between organizations."""
        edge_id = self._generate_id("tedge_")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO triad_edges
                (edge_id, project_id, source_org_id, target_org_id,
                 edge_type, weight, source_modality, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    edge_id, project_id, source_org_id, target_org_id,
                    edge_type, weight, source_modality,
                    json.dumps(metadata) if metadata else None
                ),
            )
        return edge_id

    def get_triad_positions(
        self, project_id: str, triad_type: Optional[str] = None
    ) -> List[Dict]:
        """Get all triad positions for a project."""
        with self._connect() as conn:
            if triad_type:
                rows = conn.execute(
                    """
                    SELECT tp.*, torg.name, torg.kic_sectors, torg.source_modality
                    FROM triad_positions tp
                    JOIN triad_organizations torg ON tp.org_id = torg.org_id
                    WHERE torg.project_id = ? AND tp.triad_type = ?
                    """,
                    (project_id, triad_type)
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT tp.*, torg.name, torg.kic_sectors, torg.source_modality
                    FROM triad_positions tp
                    JOIN triad_organizations torg ON tp.org_id = torg.org_id
                    WHERE torg.project_id = ?
                    """,
                    (project_id,)
                ).fetchall()
            return [dict(row) for row in rows]

    def get_triad_annotation_progress(self, project_id: str) -> Dict:
        """Get triad annotation progress for a project."""
        with self._connect() as conn:
            # Total positions
            total = conn.execute(
                """
                SELECT COUNT(*) as count FROM triad_positions tp
                JOIN triad_organizations torg ON tp.org_id = torg.org_id
                WHERE torg.project_id = ?
                """,
                (project_id,)
            ).fetchone()["count"]

            # Annotated positions
            annotated = conn.execute(
                """
                SELECT COUNT(DISTINCT ta.position_id) as count FROM triad_annotations ta
                JOIN triad_organizations torg ON ta.org_id = torg.org_id
                WHERE torg.project_id = ? AND ta.position_id IS NOT NULL
                """,
                (project_id,)
            ).fetchone()["count"]

            return {
                "total_positions": total,
                "annotated_positions": annotated,
                "progress_pct": round(annotated * 100.0 / total, 1) if total > 0 else 0
            }

    # ========================================================================
    # EXPORT FUNCTIONS
    # ========================================================================

    def export_project_data(self, project_id: str) -> Dict[str, Any]:
        """Export all data for a project as JSON-serializable dict."""
        with self._connect() as conn:
            project = dict(conn.execute(
                "SELECT * FROM projects WHERE project_id = ?", (project_id,)
            ).fetchone())

            module = project["module"]
            data = {"project": project, "export_date": datetime.now().isoformat()}

            if module == "rolebox-websites":
                docs = [dict(r) for r in conn.execute(
                    "SELECT * FROM website_documents WHERE project_id = ?", (project_id,)
                ).fetchall()]
                doc_ids = [d["doc_id"] for d in docs]

                triplets = []
                for doc_id in doc_ids:
                    triplets.extend([dict(r) for r in conn.execute(
                        "SELECT * FROM triplets WHERE doc_id = ?", (doc_id,)
                    ).fetchall()])

                triplet_ids = [t["triplet_id"] for t in triplets]
                validations = []
                for tid in triplet_ids:
                    validations.extend([dict(r) for r in conn.execute(
                        "SELECT * FROM triplet_validations WHERE triplet_id = ?", (tid,)
                    ).fetchall()])

                data["documents"] = docs
                data["triplets"] = triplets
                data["validations"] = validations

            elif module == "rolebox-crunchbase":
                companies = [dict(r) for r in conn.execute(
                    "SELECT * FROM companies WHERE project_id = ?", (project_id,)
                ).fetchall()]

                classifications = []
                for c in companies:
                    classifications.extend([dict(r) for r in conn.execute(
                        "SELECT * FROM company_classifications WHERE company_id = ?",
                        (c["company_id"],)
                    ).fetchall()])

                data["companies"] = companies
                data["classifications"] = classifications

            elif module == "rolebox-social":
                actors = [dict(r) for r in conn.execute(
                    "SELECT * FROM social_actors WHERE project_id = ?", (project_id,)
                ).fetchall()]

                codings = []
                for a in actors:
                    codings.extend([dict(r) for r in conn.execute(
                        "SELECT * FROM actor_codings WHERE actor_id = ?", (a["actor_id"],)
                    ).fetchall()])

                edges = [dict(r) for r in conn.execute(
                    "SELECT * FROM social_edges WHERE project_id = ?", (project_id,)
                ).fetchall()]

                data["actors"] = actors
                data["codings"] = codings
                data["edges"] = edges

            elif module == "rolebox-visual":
                images = [dict(r) for r in conn.execute(
                    "SELECT * FROM images WHERE project_id = ?", (project_id,)
                ).fetchall()]

                codings = []
                for img in images:
                    codings.extend([dict(r) for r in conn.execute(
                        "SELECT * FROM image_codings WHERE image_id = ?", (img["image_id"],)
                    ).fetchall()])

                absences = [dict(r) for r in conn.execute(
                    "SELECT * FROM absence_annotations WHERE project_id = ?", (project_id,)
                ).fetchall()]

                data["images"] = images
                data["codings"] = codings
                data["absences"] = absences

            return data

    def import_json_data(self, project_id: str, data: Dict[str, Any]):
        """Import data from JSON export format."""
        # Implementation depends on data format
        # This would parse the JSON and insert into appropriate tables
        pass


# Convenience function for quick database access
def get_db(db_path: Optional[Path] = None) -> RoleBoxDB:
    """Get a database instance."""
    return RoleBoxDB(db_path)


if __name__ == "__main__":
    # Demo usage
    db = get_db()

    # Create a test project
    project_id = db.create_project(
        name="EIT Visual Analysis Test",
        module="rolebox-visual",
        description="Test project for visual register annotation"
    )
    print(f"Created project: {project_id}")

    # Create an annotator
    annotator_id = db.create_annotator(
        name="Test Annotator",
        email="test@example.com"
    )
    print(f"Created annotator: {annotator_id}")

    # Start a session
    session_id = db.start_session(project_id, annotator_id)
    print(f"Started session: {session_id}")

    # List projects
    projects = db.get_projects()
    print(f"Projects: {projects}")
