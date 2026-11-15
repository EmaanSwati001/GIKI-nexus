# GIKI Nexus: Data Mapping & Unresolved Records Review

**Document Version:** 2.0.0  
**Status:** Implemented & Documented (Curation Rules Applied)  
**Target:** Data Cleaning, Catalog Normalization, and Human Sign-Off  
**Audit Pipeline Status:** Executed Successfully (0 Errors, 0 Warnings, 18 Tests Passing)

---

## 1. Executive Summary & Implementation Status

During data audit and processing pipeline implementation, specific records were identified that require structured curation, normalization, or domain expert sign-off before being ingested into a production database or knowledge graph.

In accordance with core project constraints:
1. **Uncertain relationships are never automatically committed or invented.**
2. **Missing data remains identifiable, traceable, and unpolluted with synthetic values.**
3. **Derived assignments (e.g. prefix mappings) are explicitly recorded as derived (`unit_mapping_source = "prefix_based_mapping"`).**
4. **All 190 CourseHub instructors are preserved without truncation across a formal 4-status lifecycle.**
5. **Original raw input files remain strictly untouched.**

### 1.1 Summary of Implemented Solutions

| Problem Area | Raw Count | Implemented Resolution | Final Status |
|---|---|---|---|
| **Courses Missing Academic Unit** | 111 courses | Applied deterministic prefix matching rules anchored at start of course code; preserved `offered_in` programs; assigned `unit_mapping_source = "prefix_based_mapping"`. | **111 Mapped / 0 Unresolved** |
| **Missing Catalog Prerequisites** | 5 codes across 6 courses | Preserved raw codes in `prerequisites`; added `unresolved_prerequisites` list and `prerequisite_statuses` dictionary (`"unresolved"`); flagged in curation queue. | **Preserved as Unresolved (Tracked)** |
| **CourseHub Instructors** | 190 instructors | Implemented 4-status lifecycle: 124 `matched`, 6 `suggested` (with `suggested_faculty_id`), 17 `needs_review` (single names), 43 `unmatched` (lab engineers/TAs). All preserved. | **190 Preserved / Categorized** |
| **Faculty Designation Discrepancies** | 31 faculty | Profile page designation adopted as `preferred_designation`; extracted `academic_rank`, `administrative_role`, and `professional_credentials`; preserved both sources. | **31 Resolved & Decomposed** |
| **Incomplete Faculty Profiles** | 24 emails, 15 quals, 16 research | Preserved as `None` / empty lists without failing validation or fabricating fake data; isolated empty personnel record in `other_personnel.json`. | **Preserved Accurately** |
| **Cross-Unit Affiliations** | 1 faculty (`prof-dr-nisar-ahmed`) | Preserved dual appointment `["fbs", "fee"]` across Basic Sciences and Electrical Engineering without dropping secondary unit. | **Verified Dual Appointment** |
| **Prospectus False Positive** | 1 link (`Muhammad Naveed` vs `Mr. Muhammad Naeem`) | Flagged with `review_needed: true` to prevent improper entity merging. | **Prevented Merging** |
| **Curation Review Queue** | 378 items | Standardized into `CurationQueueItem` schema with `resolved` (142), `needs_review` (63), and `informational` (173). | **Categorized & Serialized** |

---

## 2. Resolution of Courses Without Assigned Units (111 Courses)

In `courses.json`, 111 courses initially had `unit: null`. These courses were extracted from degree curriculum semester grids (`offered_in`) where the owning academic unit was not explicitly annotated.

### 2.1 Applied Prefix Mapping Rules

Each course code prefix was anchored at string start (`^<PREFIX>(?=[0-9L\-\s/]|$)`) and matched against verified academic unit IDs:

| Course Prefix | Academic Unit | Unit ID | Mapped Courses | Curriculum Context |
|---|---|---|---|---|
| `AI` | Faculty of Computer Science & Engineering | `fcse` | 9 | Core courses across BS Artificial Intelligence, BS CS, BS SE |
| `CE` | Faculty of Computer Science & Engineering | `fcse` | 12 | Computer Engineering core curriculum |
| `CS` | Faculty of Computer Science & Engineering | `fcse` | 18 | Computer Science & Software Engineering core |
| `DS` | Faculty of Computer Science & Engineering | `fcse` | 6 | Data Science core courses |
| `CY` / `CYS` | Faculty of Computer Science & Engineering | `fcse` | 0 | Cyber Security core (covered in verified set) |
| `SE` | Faculty of Computer Science & Engineering | `fcse` | 7 | Software Engineering core courses |
| **FCSE Subtotal** | | `fcse` | **52** | |
| `EE` | Faculty of Electrical Engineering | `fee` | **27** | Electrical Engineering circuits, power, and communications |
| `CV` | Department of Civil Engineering | `dcve` | **17** | Civil Engineering surveying, structures, and hydraulics |
| `ES` | Faculty of Basic Sciences | `fbs` | 2 | Engineering mechanics and basic engineering science |
| `HM` | Faculty of Basic Sciences | `fbs` | 4 | Humanities, English, Islamic Studies, Pakistan Studies |
| `HMXYZ` | Faculty of Basic Sciences | `fbs` | 1 | Humanities Elective catalog placeholder |
| `MT` | Faculty of Basic Sciences | `fbs` | 1 | Mathematics (Calculus I) |
| **FBS Subtotal** | | `fbs` | **8** | |
| `CH` | Department of Chemical Engineering (FMCE) | `dche` | **2** | Chemical process principles and thermodynamics |
| `ME` | Faculty of Mechanical Engineering | `fme` | **2** | Thermodynamics I and Mechanics of Materials I |
| `MS` | School of Management Sciences | `mgs` | **2** | Principles of Management and Microeconomics |
| `MM` | Department of Materials Science & Engineering (FMCE) | `dmse` | **1** | Engineering Materials |
| **Total** | | | **111** | **All 111 mapped (0 unresolved)** |

### 2.2 Reconciled Course-Unit Status

- **Prospectus-Verified Units:** 536 courses (`unit_mapping_source: "prospectus_verified"`)
- **Prefix-Derived Units:** 111 courses (`unit_mapping_source: "prefix_based_mapping"`)
- **Unresolved Units:** 0 courses
- **Total Courses in Catalog:** 647 courses (100% assigned to verified academic units)

---

## 3. Resolution of Missing Prerequisite Course Records

The audit identified **5 unique prerequisite course codes** referenced in active course descriptions that do not exist as top-level catalog entries in the current snapshot:

| Missing Prerequisite Code | Referenced By | Course Title | Academic Unit | Probable Cause & Recommended Human Action |
|---|---|---|---|---|
| `AI321` | `AI331` | Deep Neural Networks | `fcse` | Previous curriculum numbered Machine Learning as `AI321`; renumbered to `AI221`. Curriculum committee confirmation recommended to update prerequisite pointer to `AI221`. |
| `AI321` | `AI462` | Nature Inspired Computing | `fcse` | Same curriculum renumbering as above. |
| `MM102` | `EE485` | Electrical Insulation Materials | `fee` | Catalog contains `MM101` (Engineering Materials). Confirm whether `MM102` was an advanced materials elective or catalog typo for `MM101`. |
| `MS290` | `EE486` | Power Economics and Management | `fee` | MGS economics courses are numbered `MS102` / `MS202`. Confirm departmental course numbering. |
| `ME101` | `ME418` | CAD/CAM | `fme` | Introductory engineering graphics course. Confirm current course code equivalent in FME. |
| `ME261` | `ME468` | Mechanical Engineering Design | `fme` | Prerequisite sequence for machine design. Confirm current code sequence. |

### 3.1 Implementation Details

- Prerequisite codes are preserved verbatim in `Course.prerequisites`.
- Each course tracks `unresolved_prerequisites: ["<CODE>"]` and `prerequisite_statuses: {"<CODE>": "unresolved"}`.
- No artificial courses were inserted into `courses.json`.
- All 6 referencing courses are logged in `data/processed/needs_review.json` under `category: "unresolved_prerequisite"` with status `needs_review`.

---

## 4. Resolution of CourseHub Instructor Records (190 Records)

All 190 instructor records from CourseHub are preserved without loss using a 4-status lifecycle:

```
[190 CourseHub Instructors]
  ├── Matched (124)       --> Official faculty ID verified & linked
  ├── Suggested (6)       --> Candidate matches pending human sign-off (faculty_id: null)
  ├── Needs Review (17)   --> Single-name records requiring department roster check
  └── Unmatched (43)      --> Unlisted lab engineers, TAs, or visiting faculty
```

### 4.1 Candidate Suggested Matches (6 Records)

These 6 instructors have high-probability matches based on middle initial or name variants, but retain `faculty_id: null` until official administrative sign-off:

| CourseHub Instructor Name | Unit | Suggested Faculty ID | Suggested Faculty Name & Title | Rationale |
|---|---|---|---|---|
| `Dr. Taqi A. Cheema` | FME | `dr-taqi-ahmad-cheema` | Dr. Taqi Ahmad Cheema (Associate Professor & HoD, FME) | Middle initial expansion |
| `Dr. Ramzan A. Karim` | FMCE | `dr-muhammad-ramzan-abdul-karim` | Dr. Muhammad Ramzan Abdul Karim (Associate Professor & HoD, DMSE) | Name variant & middle initial |
| `Dr. Nasir Amin` | MgS | `dr-muhammad-nasir-amin` | Dr. Muhammad Nasir Amin (Assistant Professor, DCvE) | Honorific prefix variant |
| `Dr. Omar A. Qureshi` | FME | `dr-omar-ahmad-qureshi` | Dr. Omar Ahmad Qureshi (Associate Professor, FME) | Middle initial expansion |
| `Dr. M. Ashraf Tanoli` | DCvE | `dr-muhammad-ashraf-tanoli` | Dr. Muhammad Ashraf Tanoli (Associate Professor & HoD, DCvE) | Initial abbreviation |
| `Dr. M. Waseem` | DCvE | `dr-muhammad-waseem` | Dr. Muhammad Waseem (Assistant Professor, FEE) | Initial abbreviation |

### 4.2 Ambiguous Single-Name Records (17 Records)

The following 17 records contain single tokens or titles only, making unique identification impossible without course scheduling records:
`Ms Beenish`, `Mr Talha`, `Dr Taj`, `Dr Zoya`, `Dr Salman`, `Dr Khurram`, `Dr Zahid`, `Mr Asif`, `Mr Saqib`, `Engr Hamza`, `Engr Hassan`, `Engr Rafay`, `Engr Wajahat`, `Dr Rashid`, `Dr Imran`, `Dr Hamza`, `Dr Mohsin`.
- Categorized as `match_status: "needs_review"`.

### 4.3 Unmatched Instructors (43 Records)

The remaining 43 records represent lab engineers, teaching assistants, or visiting instructors without persistent personal profile pages on `giki.edu.pk`:
- Categorized as `match_status: "unmatched"`.
- Retained in `data/processed/coursehub_instructor_links.json`.

---

## 5. Resolution of Faculty Designation Discrepancies (31 Records)

31 faculty members have divergent titles between roster listing pages and individual profile pages.

### 5.1 Curation Strategy Applied

1. **Display Priority:** Profile page designation is established as `preferred_designation` because profile pages are directly maintained by faculty members and reflect the latest promotions and administrative appointments.
2. **Decomposition:**
   - `academic_rank`: Extracted academic title (e.g. Professor, Associate Professor, Assistant Professor, Lecturer).
   - `administrative_role`: Extracted administrative role (e.g. HoD, Dean, Director/PI).
   - `professional_credentials`: Extracted credentials (e.g. HEC Approved PhD Supervisor, MIEEE, EUR ING).
3. **Audit Trail:** Both `designation` (from listing) and `designation_on_profile_page` (from profile) remain preserved in the record with `designation_discrepancy: true`.
4. **Curation Status:** Marked as `resolved` in the curation queue.

---

## 6. Incomplete Faculty Profiles & Structural Ambiguities

### 6.1 Preserved Incomplete Faculty Records

- **Missing Emails:** 24 faculty records lack public email addresses; preserved as `None` without fake data.
- **Missing Qualifications / Research Interests:** 15 lack structured qualifications and 16 lack research interests; preserved as empty lists `[]` with `verified: false`.
- **Empty Profiles:**
  - `dr-asif-khan-assistant-professor`: Present on department listing page but empty profile body; retained in `faculty.json` with `verified: false`.
  - `dr-nasir-javed-assistant-professor-fes`: Retained in `other_personnel.json` with provenance note explaining lack of active department roster listing.

### 6.2 Dual Appointment Verified

- **`prof-dr-nisar-ahmed`:** Retains dual appointment `units: ["fbs", "fee"]` across Basic Sciences and Electrical Engineering; categorized as `informational` in curation queue.

### 6.3 Prospectus Cross-Check Guardrail

- **`Muhammad Naveed` (FCSE Lab Engineer) $\longleftrightarrow$ `Mr. Muhammad Naeem`:** Flagged with `review_needed: true` to prevent improper entity merging.

---

## 7. Comprehensive Curation Review Queue Breakdown

The review queue in `data/processed/needs_review.json` aggregates **378 total curation items** conforming to the `CurationQueueItem` schema:

### 7.1 By Resolution Status

| Status | Count | Description |
|---|---|---|
| **`resolved`** | 142 items | Issues resolved by deterministic rules (111 prefix mappings + 31 designation discrepancy decompositions). |
| **`needs_review`** | 63 items | Issues requiring human sign-off (6 missing prerequisites, 6 suggested instructor matches, 17 single-name instructors, 33 incomplete profiles, 1 dubious prospectus match). |
| **`informational`** | 173 items | Structural catalog observations (43 unmatched instructors, 119 courses missing syllabus/credits, 8 narrative research summaries, 2 large qualifications lists, 1 dual appointment). |
| **Total** | **378 items** | |

### 7.2 By Category

| Category | Count | Status | Entity Type |
|---|---|---|---|
| `prefix_based_unit_mapping` | 111 | `resolved` | Course |
| `designation_discrepancy` | 31 | `resolved` | Faculty |
| `missing_catalog_metadata` | 119 | `informational` | Course |
| `coursehub_unmatched_instructor` | 43 | `informational` | CourseHub Instructor |
| `incomplete_profile` | 33 | `needs_review` | Faculty |
| `coursehub_ambiguous_name` | 17 | `needs_review` | CourseHub Instructor |
| `narrative_research_interests` | 8 | `informational` | Faculty |
| `coursehub_suggested_match` | 6 | `needs_review` | CourseHub Instructor |
| `unresolved_prerequisite` | 6 | `needs_review` | Course |
| `unstructured_qualifications` | 2 | `informational` | Faculty |
| `dual_appointment` | 1 | `informational` | Faculty |
| `dubious_prospectus_match` | 1 | `needs_review` | Faculty |
| **Total** | **378** | | |
