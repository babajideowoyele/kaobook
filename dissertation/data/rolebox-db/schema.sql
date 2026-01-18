-- RoleBox Annotation Database Schema
-- Unified storage for all annotation workflows
-- Version: 1.0.0
-- Date: 2026-01-15

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- ============================================================================
-- METADATA TABLES
-- ============================================================================

-- Projects (datasets being annotated)
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    module TEXT NOT NULL,  -- rolebox-websites, rolebox-crunchbase, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Annotators (users doing the coding)
CREATE TABLE IF NOT EXISTS annotators (
    annotator_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Annotation sessions (for tracking work sessions)
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    annotator_id TEXT REFERENCES annotators(annotator_id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    items_coded INTEGER DEFAULT 0
);

-- ============================================================================
-- ROLEBOX-WEBSITES: TRIPLET VALIDATION
-- ============================================================================

-- Source documents (web pages)
CREATE TABLE IF NOT EXISTS website_documents (
    doc_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    url TEXT,
    org_name TEXT,
    org_id TEXT,
    page_type TEXT,
    scraped_at TIMESTAMP,
    content_hash TEXT,
    metadata JSON
);

-- Extracted triplets
CREATE TABLE IF NOT EXISTS triplets (
    triplet_id TEXT PRIMARY KEY,
    doc_id TEXT REFERENCES website_documents(doc_id),
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    subject_normalized TEXT,
    predicate_normalized TEXT,
    object_normalized TEXT,
    source_text TEXT,
    extraction_method TEXT,
    confidence_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Triplet validations
CREATE TABLE IF NOT EXISTS triplet_validations (
    validation_id TEXT PRIMARY KEY,
    triplet_id TEXT REFERENCES triplets(triplet_id),
    annotator_id TEXT REFERENCES annotators(annotator_id),
    session_id TEXT REFERENCES sessions(session_id),
    status TEXT CHECK(status IN ('valid', 'invalid', 'modified')),
    corrected_subject TEXT,
    corrected_predicate TEXT,
    corrected_object TEXT,
    notes TEXT,
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ROLEBOX-CRUNCHBASE: VENTURE CLASSIFICATION
-- ============================================================================

-- Companies
CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    name TEXT NOT NULL,
    location TEXT,
    description TEXT,
    founded_year INTEGER,
    total_funding REAL,
    crunchbase_url TEXT,
    metadata JSON
);

-- Company-KIC affiliations (many-to-many)
CREATE TABLE IF NOT EXISTS company_kics (
    company_id TEXT REFERENCES companies(company_id),
    kic TEXT NOT NULL,
    source TEXT,  -- 'auto' or 'manual'
    confidence REAL,
    PRIMARY KEY (company_id, kic)
);

-- Company classifications
CREATE TABLE IF NOT EXISTS company_classifications (
    classification_id TEXT PRIMARY KEY,
    company_id TEXT REFERENCES companies(company_id),
    annotator_id TEXT REFERENCES annotators(annotator_id),
    session_id TEXT REFERENCES sessions(session_id),
    role_type TEXT CHECK(role_type IN (
        'resource_intermediary', 'venture_developer', 'knowledge_broker',
        'market_maker', 'standard_setter', 'direct_producer'
    )),
    validated_kics JSON,  -- Array of validated KIC strings
    notes TEXT,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ROLEBOX-SOCIAL: NETWORK ROLE CODING
-- ============================================================================

-- Social network actors
CREATE TABLE IF NOT EXISTS social_actors (
    actor_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    platform TEXT DEFAULT 'twitter',
    handle TEXT NOT NULL,
    name TEXT,
    bio TEXT,
    community TEXT,
    degree INTEGER,
    betweenness REAL,
    clustering REAL,
    metadata JSON
);

-- Network edges
CREATE TABLE IF NOT EXISTS social_edges (
    edge_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    source_id TEXT REFERENCES social_actors(actor_id),
    target_id TEXT REFERENCES social_actors(actor_id),
    edge_type TEXT,  -- 'mention', 'retweet', 'follow', etc.
    weight REAL DEFAULT 1.0,
    timestamp TIMESTAMP
);

-- Actor role codings
CREATE TABLE IF NOT EXISTS actor_codings (
    coding_id TEXT PRIMARY KEY,
    actor_id TEXT REFERENCES social_actors(actor_id),
    annotator_id TEXT REFERENCES annotators(annotator_id),
    session_id TEXT REFERENCES sessions(session_id),
    network_role TEXT CHECK(network_role IN (
        'hub', 'bridge', 'amplifier', 'coordinator', 'peripheral'
    )),
    actor_type TEXT CHECK(actor_type IN (
        'organization', 'individual', 'project', 'media'
    )),
    notes TEXT,
    coded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ROLEBOX-VISUAL: IMAGE ANNOTATION
-- ============================================================================

-- Images
CREATE TABLE IF NOT EXISTS images (
    image_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    filename TEXT,
    url TEXT,
    org_id TEXT,
    org_name TEXT,
    collection_date TIMESTAMP,
    file_hash TEXT,
    width INTEGER,
    height INTEGER,
    metadata JSON
);

-- Image codings (visual grammar)
CREATE TABLE IF NOT EXISTS image_codings (
    coding_id TEXT PRIMARY KEY,
    image_id TEXT REFERENCES images(image_id),
    annotator_id TEXT REFERENCES annotators(annotator_id),
    session_id TEXT REFERENCES sessions(session_id),
    -- Ideational
    participants TEXT,  -- 'people', 'technology', 'nature', 'abstract'
    processes TEXT,
    circumstances TEXT,
    -- Interpersonal
    contact TEXT,  -- 'strong', 'weak', 'none'
    distance TEXT,  -- 'intimate', 'interpersonal', 'impersonal'
    angle TEXT,  -- 'high', 'eye', 'low'
    orientation TEXT,  -- 'naturalistic', 'technological', 'sensory', 'abstract'
    -- Textual
    salience TEXT,
    framing TEXT,
    -- Derived
    gaze_type TEXT,  -- 'partnership', 'impact', 'talent'
    notes TEXT,
    coded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Absence annotations
CREATE TABLE IF NOT EXISTS absence_annotations (
    absence_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    annotator_id TEXT REFERENCES annotators(annotator_id),
    category TEXT NOT NULL,
    expected_proportion REAL,
    observed_proportion REAL,
    justification TEXT,
    keywords JSON,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ROLEBOX-NEWS: ARTICLE CODING (RIVETER-X)
-- ============================================================================

-- News articles
CREATE TABLE IF NOT EXISTS news_articles (
    article_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    url TEXT,
    title TEXT,
    source TEXT,
    author TEXT,
    publish_date TIMESTAMP,
    content TEXT,
    metadata JSON
);

-- Entity mentions in articles
CREATE TABLE IF NOT EXISTS entity_mentions (
    mention_id TEXT PRIMARY KEY,
    article_id TEXT REFERENCES news_articles(article_id),
    entity_name TEXT NOT NULL,
    entity_type TEXT,  -- 'organization', 'person', 'location', etc.
    start_char INTEGER,
    end_char INTEGER,
    context TEXT,
    sentiment REAL,
    agency_score REAL
);

-- ============================================================================
-- ROLEBOX-PYDNA: DISCOURSE NETWORK
-- ============================================================================

-- DNA Statements
CREATE TABLE IF NOT EXISTS dna_statements (
    statement_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    doc_id TEXT,
    actor TEXT NOT NULL,
    concept TEXT NOT NULL,
    qualifier INTEGER CHECK(qualifier IN (-1, 0, 1)),
    context TEXT,
    annotator_id TEXT REFERENCES annotators(annotator_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ROLEBOX-WIKIPEDIA: ENTITY INFORMATION
-- ============================================================================

-- Wikipedia entities (organizations, cities)
CREATE TABLE IF NOT EXISTS wikipedia_entities (
    entity_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    qid TEXT,  -- Wikidata QID
    entity_type TEXT,  -- 'organization', 'city'
    name TEXT NOT NULL,
    wikipedia_title TEXT,
    wikipedia_url TEXT,
    summary TEXT,
    text_length INTEGER,
    kic TEXT,  -- For organizations
    country TEXT,  -- For cities
    metadata JSON
);

-- Entity triangle scores (Powell, MaP, etc.)
CREATE TABLE IF NOT EXISTS entity_triangle_scores (
    score_id TEXT PRIMARY KEY,
    entity_id TEXT REFERENCES wikipedia_entities(entity_id),
    framework TEXT NOT NULL,  -- 'powell', 'map', 'role_modalities'
    axis_a_score REAL,
    axis_b_score REAL,
    axis_c_score REAL,
    classification TEXT,  -- 'dominant_a', 'dominant_b', 'dominant_c', 'interstitial'
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    method TEXT,  -- 'keyword', 'embedding', 'manual'
    metadata JSON
);

-- Entity annotations (manual corrections/validations)
CREATE TABLE IF NOT EXISTS entity_annotations (
    annotation_id TEXT PRIMARY KEY,
    entity_id TEXT REFERENCES wikipedia_entities(entity_id),
    annotator_id TEXT REFERENCES annotators(annotator_id),
    session_id TEXT REFERENCES sessions(session_id),
    framework TEXT NOT NULL,
    corrected_classification TEXT,
    corrected_axis_a REAL,
    corrected_axis_b REAL,
    corrected_axis_c REAL,
    confidence TEXT CHECK(confidence IN ('high', 'medium', 'low')),
    notes TEXT,
    annotated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ROLEBOX-TRIADS: TRIAD POSITION ANNOTATIONS
-- ============================================================================

-- Organizations for triad positioning
CREATE TABLE IF NOT EXISTS triad_organizations (
    org_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    name TEXT NOT NULL,
    external_id TEXT,  -- Link to other tables (wikipedia_entities, companies, etc.)
    source_modality TEXT,  -- Which rolebox-* the org comes from
    kic_sectors JSON,
    metadata JSON
);

-- Computed triad positions
CREATE TABLE IF NOT EXISTS triad_positions (
    position_id TEXT PRIMARY KEY,
    org_id TEXT REFERENCES triad_organizations(org_id),
    triad_type TEXT NOT NULL CHECK(triad_type IN (
        'role_modalities', 'powell_framework', 'actor_types', 'multi_actor_perspective'
    )),
    raw_a REAL,
    raw_b REAL,
    raw_c REAL,
    coord_a REAL,  -- Normalized (sum to 1)
    coord_b REAL,
    coord_c REAL,
    classification TEXT,
    confidence REAL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    method TEXT,  -- 'keyword', 'embedding', 'manual'
    metadata JSON
);

-- Manual triad position annotations
CREATE TABLE IF NOT EXISTS triad_annotations (
    annotation_id TEXT PRIMARY KEY,
    position_id TEXT REFERENCES triad_positions(position_id),
    org_id TEXT REFERENCES triad_organizations(org_id),
    annotator_id TEXT REFERENCES annotators(annotator_id),
    session_id TEXT REFERENCES sessions(session_id),
    triad_type TEXT NOT NULL,
    -- Manual position
    manual_coord_a REAL,
    manual_coord_b REAL,
    manual_coord_c REAL,
    manual_classification TEXT,
    -- Validation of computed position
    validated BOOLEAN,  -- Was the computed position correct?
    adjustment_reason TEXT,
    confidence TEXT CHECK(confidence IN ('high', 'medium', 'low')),
    notes TEXT,
    annotated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Network edges between organizations
CREATE TABLE IF NOT EXISTS triad_edges (
    edge_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    source_org_id TEXT REFERENCES triad_organizations(org_id),
    target_org_id TEXT REFERENCES triad_organizations(org_id),
    edge_type TEXT,  -- 'hyperlink', 'mention', 'investment', 'collaboration'
    weight REAL DEFAULT 1.0,
    source_modality TEXT,
    metadata JSON
);

-- ============================================================================
-- INTER-RATER RELIABILITY
-- ============================================================================

-- Double coding assignments
CREATE TABLE IF NOT EXISTS double_coding_assignments (
    assignment_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    item_type TEXT,  -- 'triplet', 'company', 'actor', 'image'
    item_id TEXT,
    annotator_1_id TEXT REFERENCES annotators(annotator_id),
    annotator_2_id TEXT REFERENCES annotators(annotator_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agreement scores
CREATE TABLE IF NOT EXISTS agreement_scores (
    score_id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(project_id),
    item_type TEXT,
    dimension TEXT,  -- what aspect is being compared
    annotator_1_id TEXT REFERENCES annotators(annotator_id),
    annotator_2_id TEXT REFERENCES annotators(annotator_id),
    cohens_kappa REAL,
    percent_agreement REAL,
    n_items INTEGER,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AUDIT LOG
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    action TEXT CHECK(action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_value JSON,
    new_value JSON,
    annotator_id TEXT REFERENCES annotators(annotator_id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_triplets_doc ON triplets(doc_id);
CREATE INDEX IF NOT EXISTS idx_triplet_validations_triplet ON triplet_validations(triplet_id);
CREATE INDEX IF NOT EXISTS idx_companies_project ON companies(project_id);
CREATE INDEX IF NOT EXISTS idx_company_classifications_company ON company_classifications(company_id);
CREATE INDEX IF NOT EXISTS idx_social_actors_project ON social_actors(project_id);
CREATE INDEX IF NOT EXISTS idx_actor_codings_actor ON actor_codings(actor_id);
CREATE INDEX IF NOT EXISTS idx_images_project ON images(project_id);
CREATE INDEX IF NOT EXISTS idx_image_codings_image ON image_codings(image_id);
CREATE INDEX IF NOT EXISTS idx_news_articles_project ON news_articles(project_id);
CREATE INDEX IF NOT EXISTS idx_dna_statements_project ON dna_statements(project_id);
CREATE INDEX IF NOT EXISTS idx_wikipedia_entities_project ON wikipedia_entities(project_id);
CREATE INDEX IF NOT EXISTS idx_wikipedia_entities_qid ON wikipedia_entities(qid);
CREATE INDEX IF NOT EXISTS idx_entity_triangle_scores_entity ON entity_triangle_scores(entity_id);
CREATE INDEX IF NOT EXISTS idx_entity_annotations_entity ON entity_annotations(entity_id);
CREATE INDEX IF NOT EXISTS idx_triad_organizations_project ON triad_organizations(project_id);
CREATE INDEX IF NOT EXISTS idx_triad_positions_org ON triad_positions(org_id);
CREATE INDEX IF NOT EXISTS idx_triad_positions_type ON triad_positions(triad_type);
CREATE INDEX IF NOT EXISTS idx_triad_annotations_position ON triad_annotations(position_id);
CREATE INDEX IF NOT EXISTS idx_triad_edges_project ON triad_edges(project_id);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Triplet validation progress
CREATE VIEW IF NOT EXISTS v_triplet_progress AS
SELECT
    p.project_id,
    p.name AS project_name,
    COUNT(t.triplet_id) AS total_triplets,
    COUNT(tv.validation_id) AS validated_triplets,
    ROUND(COUNT(tv.validation_id) * 100.0 / COUNT(t.triplet_id), 1) AS progress_pct
FROM projects p
LEFT JOIN website_documents d ON d.project_id = p.project_id
LEFT JOIN triplets t ON t.doc_id = d.doc_id
LEFT JOIN triplet_validations tv ON tv.triplet_id = t.triplet_id
WHERE p.module = 'rolebox-websites'
GROUP BY p.project_id;

-- Company classification progress
CREATE VIEW IF NOT EXISTS v_company_progress AS
SELECT
    p.project_id,
    p.name AS project_name,
    COUNT(c.company_id) AS total_companies,
    COUNT(cc.classification_id) AS classified_companies,
    ROUND(COUNT(cc.classification_id) * 100.0 / COUNT(c.company_id), 1) AS progress_pct
FROM projects p
LEFT JOIN companies c ON c.project_id = p.project_id
LEFT JOIN company_classifications cc ON cc.company_id = c.company_id
WHERE p.module = 'rolebox-crunchbase'
GROUP BY p.project_id;

-- Actor coding progress
CREATE VIEW IF NOT EXISTS v_actor_progress AS
SELECT
    p.project_id,
    p.name AS project_name,
    COUNT(a.actor_id) AS total_actors,
    COUNT(ac.coding_id) AS coded_actors,
    ROUND(COUNT(ac.coding_id) * 100.0 / COUNT(a.actor_id), 1) AS progress_pct
FROM projects p
LEFT JOIN social_actors a ON a.project_id = p.project_id
LEFT JOIN actor_codings ac ON ac.actor_id = a.actor_id
WHERE p.module = 'rolebox-social'
GROUP BY p.project_id;

-- Image coding progress
CREATE VIEW IF NOT EXISTS v_image_progress AS
SELECT
    p.project_id,
    p.name AS project_name,
    COUNT(i.image_id) AS total_images,
    COUNT(ic.coding_id) AS coded_images,
    ROUND(COUNT(ic.coding_id) * 100.0 / COUNT(i.image_id), 1) AS progress_pct
FROM projects p
LEFT JOIN images i ON i.project_id = p.project_id
LEFT JOIN image_codings ic ON ic.image_id = i.image_id
WHERE p.module = 'rolebox-visual'
GROUP BY p.project_id;
