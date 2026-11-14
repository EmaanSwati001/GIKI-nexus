# GIKI Nexus

GIKI Nexus is an academic and research discovery platform designed for the Ghulam Ishaq Khan Institute of Engineering Sciences and Technology (GIKI). It enables students, faculty, and researchers to explore courses, faculties, research areas, and publications, while laying the foundation for an intelligent project teammate discovery engine.

---

## 1. Project Overview

GIKI Nexus addresses two core problem areas:

1. **Academic & Research Discovery:**
   - Explore academic units (faculties and departments), faculty profiles, publications, and normalized research domains.
   - Trace course offerings, credit breakdowns, and prerequisite sequences across degree programs.
   - Establish relationship graphs connecting researchers, academic disciplines, and curricula.
2. **Project Teammate Discovery:**
   - Voluntary student profiles highlighting skills, interests, and project experience.
   - Transparent, privacy-conscious matching based on complementary skillsets and shared research topics.

> **Note on CourseHub Isolation:** CourseHub is an external reference project. GIKI Nexus maintains an independent codebase, data models, backend, and database. No direct database or API connection to CourseHub is established; static data snapshots are used for initial seed cross-checks.

---

## 2. Project Structure

```text
GIKI-Nexus/
├── backend/                       # Backend application
│   ├── app/
│   │   ├── api/routes/            # API endpoints (FastAPI / future phase)
│   │   ├── database/              # DB connection & repositories
│   │   ├── data_processing/       # Python Data Processing & Audit Engine
│   │   │   ├── __init__.py        # Package exports
│   │   │   ├── cleaner.py         # Whitespace, Unicode, label, and credit normalization
│   │   │   ├── validator.py       # Structural, foreign key, and duplicate validators
│   │   │   ├── entities.py        # Domain entity transformers (Units, Faculty, etc.)
│   │   │   └── pipeline.py        # Pipeline orchestrator
│   │   ├── graph/                 # Knowledge graph schemas & queries
│   │   ├── models/                # Domain models
│   │   ├── schemas/               # Request/response schemas
│   │   └── services/              # Business logic services
│   └── tests/                     # Backend automated tests
│
├── frontend/                      # Frontend web interface (future phase)
│
├── data/                          # Dataset management
│   ├── raw/                       # Original, untouched raw JSON files
│   ├── processed/                 # Validated, deduplicated, standardized datasets
│   └── sample/                    # Representative sample subset for quick prototyping
│
├── docs/                          # Project documentation
│   ├── data_audit_report.md       # Comprehensive data audit report
│   ├── data_dictionary.md         # Field-by-field schema dictionary
│   ├── initial_development_log.md # Development history and architectural decisions
│   ├── requirements/              # Requirements specifications
│   ├── design/                    # Architecture and design documents
│   └── testing/                   # Test reports and test plans
│
├── scripts/                       # Executable CLI utility scripts
│   ├── run_pipeline.py            # Executes data cleaning & processing pipeline
│   ├── validate_data.py           # Validates dataset integrity and schemas
│   ├── inspect_audit.py           # Quick file structure audit tool
│   └── deep_audit.py              # In-depth relationship and anomaly analyzer
│
├── tests/                         # Root automated test suite
│   ├── __init__.py
│   └── test_data_processing.py    # Unit tests for data processing
│
├── README.md                      # Project documentation and user guide
└── .gitignore                     # Git ignore rules
```

---

## 3. Getting Started

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- No external heavy dependencies are required for the Phase 1 data processing foundation (uses standard library and optional `pytest`).

### Running the Data Processing Pipeline
To process the raw files from `data/raw/`, perform normalization, resolve duplicates, and write cleaned datasets to `data/processed/`:

```bash
python scripts/run_pipeline.py
```

This script:
1. Loads raw JSON datasets from `data/raw/`.
2. Cleans whitespace, normalizes Unicode, strips dangling punctuation, and parses credit strings (`"3-0-3"`).
3. Resolves the research area ID collision (`computational-fluid-dynamics`).
4. Eliminates intra-author duplicate publication citations (97 duplicates removed).
5. Detects false-positive prospectus cross-referencing (e.g. *Naveed* vs. *Naeem*).
6. Compiles a consolidated curation queue in `data/processed/needs_review.json`.
7. Verifies that original files in `data/raw/` remain 100% untouched.

### Validating Datasets
To validate dataset integrity, check for missing fields, verify unique constraints, and inspect anomalies:

```bash
# Validate cleaned processed datasets:
python scripts/validate_data.py --target data/processed

# Or validate raw datasets:
python scripts/validate_data.py --target data/raw
```

### Running Automated Tests
The automated test suite verifies JSON loading, missing field safety, malformed record handling, duplicate detection, URL preservation, credit parsing, and raw file immutability:

Using Python's built-in `unittest`:
```bash
python -m unittest discover tests
```

Or using `pytest`:
```bash
python -m pytest tests
```

---

## 4. Dataset Summary

| Entity | Raw Records | Processed Records | Key Characteristics |
|---|---|---|---|
| **Academic Units** | 9 | 9 | FCSE, FEE, FME, FBS, FMCE (with DMSE & DChE), DCvE, MGS |
| **Faculty Profiles** | 181 | 181 | 161 verified; 24 missing email; 15 missing qualifications |
| **Courses** | 647 | 647 | 528 with credits & descriptions; 111 unassigned units |
| **Publications** | 2,893 | 2,796 | 97 duplicate citations removed; 2,663 with verified years |
| **Research Areas** | 657 | 656 | 1 ID collision resolved; normalized topic labels |
| **Programs** | 15 | 15 | Bachelor of Science degree programs |
| **Other Personnel** | 20 | 20 | Non-faculty / former staff isolated from active faculty graph |
| **Instructor Links** | 190 | 190 | 124 matched to faculty slugs; 66 flagged for manual review |
| **Curation Queue** | 36 | 256 | Comprehensive queue for human verification |

For detailed field descriptions, refer to [docs/data_dictionary.md](file:///c:/Users/ek139/OneDrive/Desktop/GIKI%20nexus/docs/data_dictionary.md).  
For the complete data quality analysis, refer to [docs/data_audit_report.md](file:///c:/Users/ek139/OneDrive/Desktop/GIKI%20nexus/docs/data_audit_report.md).
