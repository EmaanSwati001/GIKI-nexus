# GIKI Nexus: Complete Project Overview & File-by-File Guide

**Document Version:** 1.0.0  
**Last Updated:** November 2026  
**Project:** GIKI Nexus — Academic & Research Discovery Platform with Project Teammate Discovery  
**Author:** Antigravity Engineering Assistant (Google DeepMind)

---

## 1. Executive Summary & Project Mission

**GIKI Nexus** is an intelligent academic discovery, research exploration, and student project teammate matching platform tailored for the Ghulam Ishaq Khan Institute of Engineering Sciences and Technology (GIKI).

The project is structured around two core functional pillars:
1. **Academic & Research Discovery:**
   - Explore faculties, departments, active faculty members, publications, and normalized research domains.
   - Explore degree program roadmaps, course prerequisites, and curriculum structures.
   - Lay the semantic foundation for a future university Knowledge Graph.
2. **Project Teammate Discovery:**
   - Voluntary student profiles highlighting technical skills, academic interests, and past project experience.
   - Transparent, privacy-conscious matching algorithms based on complementary skillsets and shared research topics.

### Engineering Philosophy of Phase 1
Before introducing databases, API servers, LLM agents, or frontend frameworks, Phase 1 focused strictly on **data audit, hygiene, normalization, validation, and domain modeling**:
- **Immutability of Raw Data:** Original raw JSON datasets (`data/raw/`) remain strictly untouched and read-only.
- **Zero-Invention Policy:** Missing data (e.g. unassigned course units, missing faculty emails) is never hallucinated or assumed. It is explicitly recorded as `None` or flagged for human review.
- **Decoupled from External Systems:** CourseHub is treated strictly as an external reference. No live database or backend connection is made to CourseHub; static data snapshots were cross-referenced to prevent interference.
- **Modular Foundation:** Python standard library and Pydantic v2 schemas were used to build an audit and processing pipeline that can feed directly into any future database engine (relational or graph).

---

## 2. Key Data Discoveries & Cleaning Achievements

| Problem Area | Raw Anomaly Identified | Resolution & Cleaning Implementation |
|---|---|---|
| **Research Area ID Collision** | `research_areas.json` had 657 records but only 656 unique IDs. `computational-fluid-dynamics` appeared twice due to a trailing parenthesis on one record (`Computational Fluid Dynamics)`). | Normalized labels by trimming unclosed punctuation. Merged the two records into a single clean entry with 5 unique faculty across 3 departments (`dcve`, `fbs`, `fme`). |
| **Intra-Author Duplicate Publications** | 97 citations appeared multiple times under the exact same faculty member (e.g. `dr-massab-junaid` had 3 identical duplicate citations). | Deduplicated citations on `(faculty_id, citation_text_lower)`. Removed all 97 duplicate citations, yielding 2,796 clean publications. |
| **Course Code Case Collisions** | Elective placeholders `CS3XX/CS4xx` (*Digital Business Analytics*) and `CS3xx/CS4xx` (*Generative AI*) were two distinct courses that collided if blindly converted to uppercase. | Preserved distinguishing casing and slashes for composite/placeholder elective codes while standardizing alphanumeric courses (`CS 101` $\rightarrow$ `CS101`). |
| **Course Credit Formatting** | 528 courses had credits formatted as strings (`"3-0-3"`, `"3 0 3"`, `"0-3-1"`). Naive integer casting marked them as null. | Built `parse_credits()` to standardize all formats into hyphenated representation (`"3-0-3"`) and extracted integer `credit_hours` (e.g. `3`). |
| **False-Positive Prospectus Match** | `Muhammad Naveed` was matched against `Mr. Muhammad Naeem` in the prospectus with score `0.90` due to the common prefix *"Muhammad"*. | Implemented honorific-aware token comparison that flags distinct distinguishing names as `review_needed: True` rather than falsely merging credentials. |
| **Dual Faculty Appointments** | `prof-dr-nisar-ahmed` is officially listed under both `fbs` and `fee`. | Modeled `units` as a list across schemas and pipeline to preserve multi-department memberships. |
| **Unassigned Course Units** | 111 courses in curriculum roadmaps lacked an academic unit tag (`unit: null`). | Compiled a prefix-based mapping proposal table marked `[PENDING HUMAN APPROVAL]` in `data_mapping_review.md` without guessing in the processed data. |
| **Broken Prerequisite References** | 5 course prerequisite codes (`AI321`, `MM102`, `MS290`, `ME101`, `ME261`) were referenced by courses but missing from the catalog. | Cataloged each missing code, its dependent courses, and probable historical causes in `data_mapping_review.md`. |
| **Unmatched CourseHub Instructors** | 66 of 190 instructors in CourseHub had no match on GIKI's website (mostly TAs, lab engineers, or abbreviated names like `Dr. Taqi A. Cheema`). | Preserved all 66 records in `coursehub_instructor_links.json` and documented high-probability candidate matches for review. |

---

## 3. Exhaustive File-by-File Guide

Below is a complete description of every file and directory in the GIKI Nexus project:

### 3.1 Project Root Files

- **`README.md`**  
  The main project documentation. Contains an overview of GIKI Nexus, directory layout, dataset metrics, and clear instructions for running the pipeline, validation script, and unit tests.
- **`.gitignore`**  
  Standard Git exclusion rules for Python (`__pycache__`, `.venv`, `.pytest_cache`), frontend artifacts (`node_modules`), databases (`*.db`, `*.sqlite`), OS files, and dataset rules (`data/raw/*` and `data/processed/*` are ignored while preserving their `.gitkeep` files).
- **`.gitattributes`**  
  Repository line-ending and Git configuration.

---

### 3.2 Backend Architecture (`backend/`)

The backend is structured for clean modularity, following standard layered architecture (API $\rightarrow$ Services $\rightarrow$ Models $\rightarrow$ Database):

- **`backend/__init__.py`** & **`backend/app/__init__.py`**  
  Package initializers marking the backend as an importable Python package.
- **`backend/app/schemas/domain.py`**  
  **Formal Pydantic v2 Domain Models.** Contains strongly typed, validated schema definitions:
  - `AcademicUnit`: Faculties, departments, schools with parent-child hierarchies.
  - `FacultyMember`: Complete faculty profile with dual-unit support, qualifications, research interests, verified status, and provenance.
  - `Course`: Standardized course codes, titles, credit breakdowns, credit hours, prerequisites, syllabus description, offering program placements, and lab flags.
  - `Program`: 15 Bachelor of Science degree programs.
  - `ResearchArea`: Normalized topics with aliases, faculty links, and unit associations.
  - `Publication`: Citations, publication types (`journal`, `conference`, `book_or_chapter`, `patent`), year, and DOI.
  - `OtherPersonnel`: Board of governors, marketing staff, and former/late faculty isolated from the active faculty roster.
  - `CourseHubInstructorLink`: Alignment mapping between CourseHub strings and GIKI faculty slugs.
  - Helper models: `ProvenanceMetadata`, `ProspectusCrossCheck`, `CourseOffering`, `UnitType`, `EmploymentStatus`, `PublicationType`.
- **`backend/app/schemas/__init__.py`**  
  Exports all Pydantic schemas for external consumption.
- **`backend/app/data_processing/cleaner.py`**  
  **Data Sanitization Engine.** Implements:
  - `normalize_text(text)`: Unicode NFKC normalization, strips zero-width spaces (`\u200b`, `\ufeff`), collapses whitespace, trims bullets.
  - `normalize_label(label)`: Strips unbalanced trailing/leading punctuation (e.g. `Computational Fluid Dynamics)` $\rightarrow$ `Computational Fluid Dynamics`).
  - `clean_string_list(items)`: Deduplicates and cleans string lists preserving order.
  - `sanitize_email(email)`: Strips whitespace, lowercases, and validates basic syntax.
  - `clean_course_code(code)`: Standardizes alphanumeric codes while preserving composite/placeholder elective codes.
  - `parse_credits(credits_val)`: Normalizes credit formats (`"3 0 3"` $\rightarrow$ `"3-0-3"`) and extracts total credit hours as an integer (`3`).
- **`backend/app/data_processing/validator.py`**  
  **Data Integrity & Schema Validator.** Implements:
  - `ValidationReport`: Accumulator for record counts, duplicate IDs, missing fields, foreign key violations, and integrity issues.
  - `validate_units()`, `validate_faculty()`, `validate_courses()`, `validate_publications()`, `validate_research_areas()`, `validate_programs()`: Entity-specific constraint and foreign key checkers.
- **`backend/app/data_processing/entities.py`**  
  **Entity Transformation Processors.** Contains:
  - `process_units()`: Cleans and standardizes organizational units.
  - `process_faculty()`: Handles qualifications, research interests, designation discrepancies, prospectus false-positive detection, and `verified` calculation.
  - `process_courses()`: Standardizes codes, parses credit breakdowns, and preserves program offerings.
  - `process_publications()`: Cleans citations and executes intra-author deduplication (removes 97 duplicate citations).
  - `process_research_areas()`: Resolves the `computational-fluid-dynamics` ID collision and merges faculty lists.
  - `process_programs()`: Cleans BS program records.
  - `process_other_personnel()`: Segregates non-faculty personnel.
  - `process_coursehub_links()`: Cleans instructor name mappings.
  - `build_curation_queue()`: Aggregates all records needing human attention into a single 256-item queue.
- **`backend/app/data_processing/pipeline.py`**  
  **Pipeline Orchestrator (`DataPipeline`).** Loads raw files from `data/raw/`, coordinates entity cleaning, executes validations, and writes standardized outputs to `data/processed/`. Ensures raw files are untouched.
- **`backend/app/data_processing/__init__.py`**  
  Exports all cleaners, validators, entity processors, and `DataPipeline`.
- **Scaffolded Folders for Next Phases:**
  - `backend/app/api/routes/.gitkeep`: Future REST / GraphQL API endpoints.
  - `backend/app/database/.gitkeep`: Future database connections and repositories.
  - `backend/app/graph/.gitkeep`: Future knowledge graph traversal and querying modules.
  - `backend/app/models/.gitkeep`: Future database ORM entities.
  - `backend/app/services/.gitkeep`: Future business logic and matching engine services.
  - `backend/tests/.gitkeep`: Backend integration tests.

---

### 3.3 Data Directory (`data/`)

- **`data/raw/` (Untouched Original Raw Data):**
  - `giki_scrape_raw.json` (1.57 MB): Complete raw scrape payload containing 201 personnel profile pages and 231 department listing cards.
  - `units.json` (9 records): Faculties and departments.
  - `faculty.json` (181 records): Roster of faculty members on listing pages.
  - `courses.json` (647 records): Catalog of courses from prospectus and live curricula.
  - `publications.json` (2,893 records): Verbatim citations extracted from profile pages.
  - `research_areas.json` (657 records): Research interests extracted from profile pages.
  - `programs.json` (15 records): 15 BS degree programs.
  - `other_personnel.json` (20 records): Profiles not listed on active department rosters.
  - `coursehub_instructor_links.json` (190 records): CourseHub instructor strings matched against faculty slugs.
  - `needs_review.json` (36 records): Initial audit curation list.
  - `build_report.json`: Extraction statistics.
- **`data/processed/` (Cleaned, Validated & Deduplicated Data):**
  - `units.json` (9 records): Standardized units with verified parent hierarchy.
  - `faculty.json` (181 records): 161 verified faculty, normalized degrees and research topics, dual appointments preserved.
  - `courses.json` (647 records): Standardized codes, parsed credit breakdowns (`credits: "3-0-3"`, `credit_hours: 3`).
  - `publications.json` (2,796 records): 97 intra-author duplicate citations removed; unique citations preserved.
  - `research_areas.json` (656 records): ID collision resolved, trailing punctuation trimmed, faculty sets merged.
  - `programs.json` (15 records): Standardized degree programs linked to units.
  - `other_personnel.json` (20 records): Non-faculty personnel isolated from active rosters.
  - `coursehub_instructor_links.json` (190 records): 124 matched, 66 unmatched instructors preserved without truncation.
  - `needs_review.json` (256 records): Comprehensive curation queue combining unassigned courses, missing prerequisites, unmatched instructors, and faculty discrepancies.
  - `processing_report.json`: Execution metadata, counts, cleaning metrics, and validation results.
- **`data/sample/` (Sample Subset for Rapid Prototyping):**
  - Contains valid subsets: 2 units (FCSE & FEE), 5 verified faculty, 8 courses, 10 publications, 10 research areas, and 3 programs. Ideal for quick offline testing and graph prototyping.

---

### 3.4 CLI Scripts (`scripts/`)

- **`scripts/run_pipeline.py`**  
  Root-executable command that runs `DataPipeline`. Reads from `data/raw/`, cleans, deduplicates, and saves to `data/processed/`. Automatically verifies that original raw files remain untouched via timestamp checks.
- **`scripts/validate_data.py`**  
  CLI validation tool. Accepts `--target data/processed` or `--target data/raw`. Runs structural, foreign key, duplicate, and missing-field audits, and outputs a formatted terminal report.
- **`scripts/inspect_audit.py`**  
  Exploratory script used during initial audit to inspect keys, data types, sizes, and record counts across all JSON files.
- **`scripts/deep_audit.py`**  
  Deep analysis script used to discover publication duplicates, research area collisions, designation conflicts, and course code discrepancies.

---

### 3.5 Automated Test Suite (`tests/`)

- **`tests/__init__.py`**  
  Marks the test directory as a Python package.
- **`tests/test_data_processing.py`**  
  Comprehensive unit test suite containing **18 test cases**:
  1. `test_read_valid_json`: Validates JSON loading from disk.
  2. `test_handle_missing_fields_safely`: Verifies missing fields do not crash the pipeline and correctly trigger `missing_fields` flags.
  3. `test_handle_malformed_records`: Tests trailing punctuation trimming, zero-width space removal, and bad email handling.
  4. `test_detect_and_resolve_duplicates`: Tests intra-author citation deduplication and research area ID collision merging.
  5. `test_preserve_source_urls_and_provenance`: Verifies URLs and provenance metadata are never altered or dropped.
  6. `test_raw_files_remain_untouched`: Verifies that pipeline execution does not mutate files in `data/raw/`.
  7. `test_credits_parsing_variations`: Tests `"3-0-3"`, `"3 0 3"`, `"0-3-1"`, integer, and `None` credit formats.
  8. `test_prospectus_false_positive_detection`: Verifies that false-positive matches (Naveed vs. Naeem) are caught and flagged for review.
  9. `test_unmatched_instructors_preserved`: Confirms all 190 CourseHub instructors are preserved across 4 statuses.
  10. `test_dual_appointment_preserved`: Confirms Prof. Dr. Nisar Ahmed retains both `fbs` and `fee` affiliations.
  11. `test_no_silent_record_discarding`: Asserts that no records were dropped between raw and processed datasets across all entities.
  12. `test_pydantic_domain_model_validation`: Validates processed data against the formal Pydantic domain models.
  13. `test_prefix_based_course_mapping`: Validates all prefix rules, anchored matching, and preservation of `offered_in`.
  14. `test_unresolved_prerequisites_tracking`: Validates tracking of the 5 missing prerequisite codes across 6 courses.
  15. `test_coursehub_instructor_statuses`: Validates 4-status matching lifecycle (124 matched, 6 suggested, 17 needs_review, 43 unmatched) and name normalization.
  16. `test_faculty_designation_components`: Validates distinction between academic rank, administrative role, and professional credentials with profile preference.
  17. `test_incomplete_faculty_profiles_preserved`: Validates safe preservation of empty profiles without fake data.
  18. `test_curation_queue_categorization`: Validates categorization of 378 queue items into `resolved` (142), `needs_review` (63), and `informational` (173).

---

### 3.6 Documentation Directory (`docs/`)

- **`docs/data_audit_report.md`**  
  Formal data audit report. Details the available datasets, record counts, field schemas, data hygiene findings, duplicate analyses, entity relationship confidences, curation items, and database import recommendations.
- **`docs/data_dictionary.md`**  
  Field-by-field reference describing data types, nullability, descriptions, and example values for every entity across all datasets.
- **`docs/initial_development_log.md`**  
  Development history log documenting architectural decisions, problem discoveries, cleaning rules, and milestone tracking.
- **`docs/design/domain_models.md`**  
  Formal domain model specifications and Mermaid class diagram covering all 8 core entities.
- **`docs/design/academic_relationships.md`**  
  Knowledge graph relationship architecture. Details edge cardinalities, source data support, verification status, and explicitly documents why `MEMBER_TEACHES_COURSE` is currently unsupported.
- **`docs/design/data_mapping_review.md`**  
  Curation review document. Contains:
  - The complete proposed mapping table for the 111 unassigned courses based on prefixes (marked *Pending Human Approval*).
  - Analysis of the 5 missing prerequisite course records (`AI321`, `MM102`, `MS290`, `ME101`, `ME261`).
  - Analysis of the 66 unmatched CourseHub instructors and identified candidate matches.
  - Complete 31-row comparison table of faculty designation discrepancies (listing vs. profile titles).
- **`docs/project_overview_and_file_guide.md`**  
  This document: the complete, master reference guide for the entire project.
- **Scaffolded Folders for Next Phases:**
  - `docs/requirements/.gitkeep`: Future product requirements documents.
  - `docs/design/.gitkeep`: Architecture and design documents.
  - `docs/testing/.gitkeep`: Test plans and test run reports.
  - `docs/project-management/.gitkeep`: Sprint plans and milestones.

---

### 3.7 Original Seed Dataset (`GIKI_Nexus_dataset/`)

The untouched reference bundle containing the initial scrape and reassembly scripts:
- `GIKI_Nexus_dataset/raw/giki_scrape_raw.json`: The original scrape file.
- `GIKI_Nexus_dataset/out/*.json`: Initial extraction outputs prior to our Phase 1 cleaning and deduplication.
- `GIKI_Nexus_dataset/scripts/build_dataset.py` & `reassemble.py`: Original build scripts used to create the seed JSON files.
- `GIKI_Nexus_dataset/README.md`: Provenance notes from the initial scraper.

---

## 4. How to Execute & Verify the Project

All commands run directly from the project root using standard Python:

### Run the Data Processing Pipeline
```bash
python scripts/run_pipeline.py
```
*Reads from `data/raw/`, cleans, deduplicates, and generates fresh standardized datasets in `data/processed/`.*

### Run the Dataset Validation Tool
```bash
python scripts/validate_data.py --target data/processed
```
*Validates that all processed files adhere to schema constraints, foreign keys, and unique IDs with zero errors.*

### Run the Automated Test Suite
Using Python's built-in `unittest`:
```bash
python -m unittest discover tests
```
Or using `pytest`:
```bash
python -m pytest tests
```
*Executes all 12 unit tests, verifying that all functionality passes with a 100% success rate.*

---

## 5. Decisions Pending Human Approval for Phase 2

Before proceeding to database persistence (relational or graph) or teammate discovery features, human administrative sign-off is needed on:

1. **Approval of Course Unit Mappings:** Review the proposed table in `docs/design/data_mapping_review.md` to officially assign the 111 unassigned courses to departments based on catalog prefixes (e.g. `AI`/`CS`/`SE`/`DS`/`CE` $\rightarrow$ FCSE, `EE` $\rightarrow$ FEE, `CV` $\rightarrow$ DCvE, etc.).
2. **Prerequisite Code Resolution:** Confirm whether `AI321` should alias to `AI221` (Machine Learning) and whether `MM102` should alias to `MM101` (Engineering Materials).
3. **Abbreviated Instructor Name Matches:** Approve the high-probability candidate matches for CourseHub instructors (e.g. `Dr. Taqi A. Cheema` $\rightarrow$ `dr-taqi-ahmad-cheema`).
4. **Primary Designation Selection:** Decide whether personal profile designations (reflecting recent promotions like Assistant Professor for Dr. Tauheed Shehbaz) take precedence over listing roster titles.
5. **Database Technology Selection:** Select the target persistence technology for Phase 2 (e.g. PostgreSQL/SQLite with SQLAlchemy vs. Neo4j graph database).
