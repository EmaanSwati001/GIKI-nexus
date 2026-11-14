# GIKI Nexus: Initial Development Log

**Date:** November 2026  
**Milestone:** Phase 1 — Project Foundation & Data Audit  
**Author:** Antigravity Engineering Assistant (Google DeepMind)  
**Status:** Complete & Verified

---

## 1. Objectives & Scope

The primary objective of this initial development phase was to establish a rigorous, disciplined software engineering foundation for **GIKI Nexus** (a university academic discovery and teammate finding platform), inspect and audit raw GIKI academic data scraped from public sources and cross-checked against CourseHub snapshots and the GIKI Undergraduate Prospectus 2025, and build an automated Python-based data cleaning and validation pipeline.

### Architectural Decisions & Constraints
1. **Decoupled Architecture:** CourseHub is treated as a separate, external reference. GIKI Nexus maintains its own independent codebase, data models, processing pipeline, and future backend/frontend.
2. **Zero-Invention Policy:** Missing academic fields (such as missing course descriptions or missing faculty research interests) are strictly recorded as `None` or flagged in curation queues; no information is hallucinated or fabricated.
3. **Immutability of Raw Data:** Original raw JSON datasets (`data/raw/`) remain strictly untouched and read-only. Cleaned, normalized outputs are written exclusively to `data/processed/`.
4. **No Premature Heavy Abstractions:** In accordance with instructions, heavy external database engines (Neo4j, SQLite, PostgreSQL) or LLM/agent frameworks were intentionally deferred. Instead, clean, modular Python entities and schemas were implemented so that future graph and relational storage adapters can plug in cleanly.

---

## 2. Workspace Setup & Project Structure

The project was organized into a clean, modular structure conforming to standard software engineering best practices:

```text
GIKI-Nexus/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Future API route handlers
│   │   ├── database/            # Future DB connection and repositories
│   │   ├── data_processing/     # Python Data Processing Module
│   │   │   ├── __init__.py      # Package exports
│   │   │   ├── cleaner.py       # Whitespace, Unicode, label, and credit normalization
│   │   │   ├── validator.py     # Schema validation, duplicates, and integrity checking
│   │   │   ├── entities.py      # Entity processors (Units, Faculty, Courses, Pubs, etc.)
│   │   │   └── pipeline.py      # Pipeline orchestrator
│   │   ├── graph/               # Graph schemas and traversal algorithms (future phase)
│   │   ├── models/              # Core domain entities
│   │   ├── schemas/             # Pydantic schemas / contracts
│   │   └── services/            # Business logic services
│   └── tests/                   # Backend tests
├── frontend/                    # Future frontend UI
├── data/
│   ├── raw/                     # Original, untouched raw JSON files
│   ├── processed/               # Standardized, validated, deduplicated datasets
│   └── sample/                  # Small valid subset for rapid local development
├── docs/
│   ├── data_audit_report.md     # Detailed data quality and relationship audit
│   ├── data_dictionary.md       # Field-by-field entity data dictionary
│   ├── initial_development_log.md # Development decisions and audit log
│   ├── design/                  # Architecture and design specifications
│   ├── requirements/            # Product requirements
│   └── testing/                 # Test plans and reports
├── scripts/
│   ├── run_pipeline.py          # CLI runner for end-to-end data processing
│   ├── validate_data.py         # CLI runner for dataset validation
│   ├── inspect_audit.py         # Exploration script for raw file properties
│   └── deep_audit.py            # Deep-dive relationship and conflict analysis
├── tests/
│   ├── __init__.py
│   └── test_data_processing.py  # Automated unit tests
├── README.md                    # Project documentation and run guide
└── .gitignore                   # Ignore rules
```

---

## 3. Key Findings & Discoveries During Audit

### 3.1 Research Area ID Collision
- **Discovery:** In `research_areas.json`, 657 records contained only 656 unique IDs. Two records had the exact slug `computational-fluid-dynamics`. One had label `"Computational Fluid Dynamics"`, while the other had `"Computational Fluid Dynamics)"` with an unclosed trailing parenthesis from `dr-taqi-ahmad-cheema`'s profile.
- **Fix:** Implemented `normalize_label()` in `cleaner.py` to strip unbalanced trailing punctuation. `process_research_areas()` in `entities.py` merges faculty lists and units cleanly across ID collisions.

### 3.2 Intra-Author Duplicate Publications
- **Discovery:** 97 citations appeared multiple times under the exact same faculty member (e.g. `dr-massab-junaid` had 3 duplicated citations, `prof-dr-sirajul-haq` had 2 duplicated citations).
- **Fix:** Implemented deduplication on `(faculty_id, citation_text_lower)`. 97 duplicate citations were removed without affecting unique publications across co-authors, bringing the clean publication count to 2,796.

### 3.3 Elective Placeholder Code Case Collision
- **Discovery:** In `courses.json`, the codes `CS3XX/CS4xx` (Digital Business Analytics) and `CS3xx/CS4xx` (Generative AI with Large Language Models) represented two completely distinct elective courses. Converting course codes blindly to uppercase resulted in an ID collision.
- **Fix:** `clean_course_code()` preserves casing and slashes for composite/placeholder elective codes while standardizing alphanumeric course codes (`CS 101` -> `CS101`).

### 3.4 False-Positive Prospectus Matching
- **Discovery:** `Muhammad Naveed` was matched against `Mr. Muhammad Naeem` in the prospectus with a score of 0.90 due to shared token "Muhammad".
- **Fix:** `entities.py` now filters common honorific prefixes (`Muhammad`, `Mohammad`, `Syed`, `Dr`, `Engr`, `Prof`) when validating prospectus match confidence. The record is flagged with `review_needed: True` rather than blindly trusted.

### 3.5 Course Credit Normalization
- **Discovery:** 528 courses had credits formatted as strings (`"3-0-3"`, `"3 0 3"`, `"0-3-1"`).
- **Fix:** `parse_credits()` standardizes all valid patterns into `"3-0-3"` and extracts the total credit hours as an integer (`credit_hours: 3`).

### 3.6 Faculty Affiliations and Conflicts
- **Dual Affiliation:** `prof-dr-nisar-ahmed` is officially listed under both `fbs` and `fee`. Preserved as `units: ["fbs", "fee"]`.
- **Unassigned Unit:** `dr-asif-khan-assistant-professor` was listed only on `/faculty/` without department listing. Preserved as `units: []` and flagged for manual assignment.
- **Designation Conflicts:** 31 faculty members have divergent titles between listing page and individual profile page.
- **Other Personnel:** 20 individuals with profile URLs (e.g. late faculty, marketing manager, board of governors) were isolated in `other_personnel.json`.

---

## 4. Implementation Summary

1. **`backend/app/data_processing/cleaner.py`:**
   - Unicode NFKC normalization, zero-width space removal, whitespace collapsing.
   - Punctuation trimming and parenthesis balancing for entity labels.
   - Course code standardization.
   - Credit string formatting and total credit hour calculation.
   - Email and phone sanitization.
2. **`backend/app/data_processing/validator.py`:**
   - Validates JSON record structures, types, required fields, and foreign keys.
   - Detects duplicate keys, IDs, and citations.
   - Detects dangling prerequisite course codes (`AI321`, `MM102`, `MS290`, `ME101`, `ME261`).
   - Produces structured `ValidationReport` dictionaries.
3. **`backend/app/data_processing/entities.py`:**
   - Separate, dedicated processing functions for `Units`, `Faculty`, `Courses`, `Publications`, `ResearchAreas`, `Programs`, `OtherPersonnel`, and `CourseHubLinks`.
   - Assembles unified curation queue `build_curation_queue()` (256 review items).
4. **`backend/app/data_processing/pipeline.py`:**
   - Orchestrates loading raw files, applying entity cleaning, validating results, and exporting to `data/processed/`.
   - Leaves `data/raw/` strictly untouched (verified via file modification timestamps and hashes).
5. **CLI Scripts:**
   - `scripts/run_pipeline.py`: Executes end-to-end data processing.
   - `scripts/validate_data.py`: Validates dataset directories (`data/raw` or `data/processed`).
6. **Automated Test Suite:**
   - `tests/test_data_processing.py`: 8 comprehensive tests covering valid JSON reading, missing field safety, malformed record handling, duplicate detection and resolution, URL/provenance preservation, raw file immutability, credit parsing variations, and prospectus false-positive detection.
   - Verified passing with both `python -m unittest` and `python -m pytest` (100% pass rate).

---

## 5. Next Steps & Recommendations

1. **Phase 2 — Domain Models & Relational / Graph Mapping:**
   - Define Pydantic / SQLAlchemy / Neo4j schema definitions for `Department`, `Faculty`, `Course`, `Publication`, `ResearchArea`, and `Program`.
   - Maintain multi-unit foreign keys for dual appointments.
2. **Phase 3 — Curation Workflow for Unassigned Units & Broken Prereqs:**
   - Create a lightweight curation script or admin endpoint to assign academic units to the 111 unassigned courses based on course code prefixes (`CS` -> FCSE, `EE` -> FEE, etc.).
3. **Phase 4 — Teammate Discovery Feature Design:**
   - Design student profile models (`StudentProfile`, `Skill`, `Interest`, `ProjectExperience`).
   - Implement privacy-preserving matching algorithms connecting students with complementary skills and shared research/course interests.
