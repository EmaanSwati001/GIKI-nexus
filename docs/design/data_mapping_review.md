# GIKI Nexus: Data Mapping & Unresolved Records Review

**Document Version:** 1.0.0  
**Status:** Curation Review & Action Plan  
**Target:** Data Cleaning, Catalog Normalization, and Human Sign-Off

---

## 1. Executive Summary

During the data audit and processing pipeline execution, specific records were identified that require human curation, verification, or domain sign-off before being ingested into a production database or knowledge graph.

In accordance with core project constraints:
1. **Uncertain relationships are never automatically committed or invented.**
2. **Missing data remains identifiable and traceable.**
3. **Proposed heuristics are documented explicitly as pending human approval.**

This document provides complete, actionable review tables for:
- 111 courses lacking an academic unit assignment.
- 5 missing prerequisite course records.
- 66 unmatched CourseHub instructor names.
- 31 faculty designation discrepancies between listing pages and profile pages.
- Incomplete faculty profiles (missing emails, qualifications, or research interests).
- Ambiguous entity relationships (dual appointments and prospectus false positives).

---

## 2. Review of Courses Without Assigned Units (111 Courses)

In `courses.json`, 111 courses are cataloged with `unit: null`. These courses were extracted from degree curriculum semester grids (`offered_in`) or prospectus entries where the offering department was not explicitly tagged.

### 2.1 Prefix Distribution Summary

| Course Prefix | Count | Academic Domain | Proposed Unit | Rationale / Curriculum Context |
|---|---|---|---|---|
| `AI` | 9 | Artificial Intelligence | `fcse` | Offered across BS AI, BS CS, BS SE (FCSE). |
| `CE` | 12 | Computer Engineering | `fcse` | Core courses in BS Computer Engineering (FCSE). |
| `CH` | 2 | Chemical Engineering | `dche` (FMCE) | Core courses in BS Chemical Engineering. |
| `CS` | 18 | Computer Science | `fcse` | Core courses in BS Computer Science & SE (FCSE). |
| `CV` | 17 | Civil Engineering | `dcve` | Core courses in BS Civil Engineering. |
| `DS` | 6 | Data Science | `fcse` | Core courses in BS Data Science (FCSE). |
| `EE` | 27 | Electrical Engineering | `fee` | Core courses in BS Electrical Engineering (FEE). |
| `ES` | 2 | Engineering Sciences | `fbs` | Basic engineering science courses under FBS. |
| `HM` | 4 | Humanities | `fbs` / General | Humanities and Social Sciences (FBS). |
| `HMXYZ` | 1 | Humanities Elective Placeholder | `fbs` / General | Elective placeholder for humanities courses. |
| `ME` | 2 | Mechanical Engineering | `fme` | Core courses in BS Mechanical Engineering. |
| `MM` | 1 | Materials Science & Metallurgy | `dmse` (FMCE) | Engineering materials course under DMSE. |
| `MS` | 2 | Management Sciences | `mgs` | Management sciences and economics under MGS. |
| `MT` | 1 | Mathematics | `fbs` | Core mathematics under Faculty of Basic Sciences. |
| `SE` | 7 | Software Engineering | `fcse` | Core courses in BS Software Engineering (FCSE). |
| **Total** | **111** | | | |

---

### 2.2 Proposed Mapping Table (Pending Human Approval)

> [!IMPORTANT]
> The assignments below are **proposed based on standard university catalog prefixes and curriculum roadmaps**. They are currently recorded as `unit: null` in `data/processed/courses.json` and require human administrative confirmation before updating.

| Course Code | Course Name | Offering Programs | Proposed Unit | Status |
|---|---|---|---|---|
| `AI102` | Introduction to Artificial Intelligence | BS AI, BS CS, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `AI202` | Artificial Intelligence | BS AI, BS CS, BS SE, BS DS | `fcse` | **Pending Approval** |
| `AI221` | Machine Learning | BS AI, BS CS, BS SE, BS DS | `fcse` | **Pending Approval** |
| `AI221L` | Machine Learning Lab | BS AI, BS CS, BS SE, BS DS | `fcse` | **Pending Approval** |
| `AI331L` | Deep Neural Networks Lab | BS AI | `fcse` | **Pending Approval** |
| `AI341` | Computer Vision | BS AI, BS CS | `fcse` | **Pending Approval** |
| `AI341L` | Computer Vision Lab | BS AI | `fcse` | **Pending Approval** |
| `AI351` | Natural Language Processing | BS AI, BS CS | `fcse` | **Pending Approval** |
| `AI351L` | Natural Language Processing Lab | BS AI | `fcse` | **Pending Approval** |
| `CE211L` | Digital Logic Design Lab | BS CE, BS CS, BS AI | `fcse` | **Pending Approval** |
| `CE221` | Computer Organization and Assembly Language | BS CE, BS CS | `fcse` | **Pending Approval** |
| `CE221L` | Computer Organization Lab | BS CE, BS CS | `fcse` | **Pending Approval** |
| `CE222` | Microprocessor Systems | BS CE | `fcse` | **Pending Approval** |
| `CE222L` | Microprocessor Systems Lab | BS CE | `fcse` | **Pending Approval** |
| `CE231L` | Signals & Systems Lab | BS CE | `fcse` | **Pending Approval** |
| `CE323` | Computer Architecture | BS CE, BS CS | `fcse` | **Pending Approval** |
| `CE323L` | Computer Architecture Lab | BS CE | `fcse` | **Pending Approval** |
| `CE332` | Digital Signal Processing | BS CE | `fcse` | **Pending Approval** |
| `CE332L` | Digital Signal Processing Lab | BS CE | `fcse` | **Pending Approval** |
| `CE424` | Embedded Systems Design | BS CE | `fcse` | **Pending Approval** |
| `CE424L` | Embedded Systems Design Lab | BS CE | `fcse` | **Pending Approval** |
| `CH201` | Chemical Process Principles | BS Chemical | `dche` | **Pending Approval** |
| `CH202` | Chemical Engineering Thermodynamics | BS Chemical | `dche` | **Pending Approval** |
| `CS102` | Object Oriented Programming | BS CS, BS AI, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `CS102L` | Object Oriented Programming Lab | BS CS, BS AI, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `CS201` | Data Structures and Algorithms | BS CS, BS AI, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `CS201L` | Data Structures and Algorithms Lab | BS CS, BS AI, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `CS212` | Discrete Structures | BS CS, BS AI, BS SE, BS DS | `fcse` | **Pending Approval** |
| `CS301` | Operating Systems | BS CS, BS AI, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `CS301L` | Operating Systems Lab | BS CS, BS AI, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `CS302` | Database Systems | BS CS, BS AI, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `CS302L` | Database Systems Lab | BS CS, BS AI, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `CS303` | Design and Analysis of Algorithms | BS CS, BS AI, BS SE, BS DS | `fcse` | **Pending Approval** |
| `CS304` | Theory of Automata | BS CS | `fcse` | **Pending Approval** |
| `CS311` | Computer Networks | BS CS, BS AI, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `CS311L` | Computer Networks Lab | BS CS, BS AI, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `CS321` | Software Engineering | BS CS | `fcse` | **Pending Approval** |
| `CS321L` | Software Engineering Lab | BS CS | `fcse` | **Pending Approval** |
| `CS401` | Compiler Construction | BS CS | `fcse` | **Pending Approval** |
| `CS411` | Information Security | BS CS, BS AI, BS SE, BS DS | `fcse` | **Pending Approval** |
| `CS499` | Final Year Project | BS CS, BS AI, BS SE, BS DS, BS CE | `fcse` | **Pending Approval** |
| `CV101` | Engineering Surveying | BS Civil | `dcve` | **Pending Approval** |
| `CV101L` | Engineering Surveying Lab | BS Civil | `dcve` | **Pending Approval** |
| `CV201` | Mechanics of Solids | BS Civil | `dcve` | **Pending Approval** |
| `CV201L` | Mechanics of Solids Lab | BS Civil | `dcve` | **Pending Approval** |
| `CV202` | Fluid Mechanics | BS Civil | `dcve` | **Pending Approval** |
| `CV202L` | Fluid Mechanics Lab | BS Civil | `dcve` | **Pending Approval** |
| `CV211` | Structural Analysis | BS Civil | `dcve` | **Pending Approval** |
| `CV221` | Transportation Engineering | BS Civil | `dcve` | **Pending Approval** |
| `CV301` | Reinforced Concrete Design | BS Civil | `dcve` | **Pending Approval** |
| `CV301L` | Concrete Lab | BS Civil | `dcve` | **Pending Approval** |
| `CV302` | Geotechnical Engineering | BS Civil | `dcve` | **Pending Approval** |
| `CV302L` | Geotechnical Lab | BS Civil | `dcve` | **Pending Approval** |
| `CV311` | Steel Structures | BS Civil | `dcve` | **Pending Approval** |
| `CV321` | Environmental Engineering | BS Civil | `dcve` | **Pending Approval** |
| `CV321L` | Environmental Lab | BS Civil | `dcve` | **Pending Approval** |
| `CV401` | Construction Project Management | BS Civil | `dcve` | **Pending Approval** |
| `CV499` | Final Year Project | BS Civil | `dcve` | **Pending Approval** |
| `DS201` | Introduction to Data Science | BS Data Science | `fcse` | **Pending Approval** |
| `DS201L` | Introduction to Data Science Lab | BS Data Science | `fcse` | **Pending Approval** |
| `DS211` | Data Mining | BS Data Science | `fcse` | **Pending Approval** |
| `DS301` | Big Data Analytics | BS Data Science | `fcse` | **Pending Approval** |
| `DS301L` | Big Data Analytics Lab | BS Data Science | `fcse` | **Pending Approval** |
| `DS311` | Data Visualization | BS Data Science | `fcse` | **Pending Approval** |
| `EE101` | Electric Circuit Analysis | BS EE (All tracks) | `fee` | **Pending Approval** |
| `EE101L` | Electric Circuit Analysis Lab | BS EE | `fee` | **Pending Approval** |
| `EE201` | Electronic Devices & Circuits | BS EE | `fee` | **Pending Approval** |
| `EE201L` | Electronic Devices Lab | BS EE | `fee` | **Pending Approval** |
| `EE211` | Signals and Systems | BS EE | `fee` | **Pending Approval** |
| `EE211L` | Signals and Systems Lab | BS EE | `fee` | **Pending Approval** |
| `EE221` | Digital Logic Design | BS EE | `fee` | **Pending Approval** |
| `EE221L` | Digital Logic Design Lab | BS EE | `fee` | **Pending Approval** |
| `EE301` | Electromagnetic Field Theory | BS EE | `fee` | **Pending Approval** |
| `EE311` | Communication Systems | BS EE | `fee` | **Pending Approval** |
| `EE311L` | Communication Systems Lab | BS EE | `fee` | **Pending Approval** |
| `EE321` | Linear Control Systems | BS EE | `fee` | **Pending Approval** |
| `EE321L` | Linear Control Systems Lab | BS EE | `fee` | **Pending Approval** |
| `EE331` | Electrical Machines | BS EE | `fee` | **Pending Approval** |
| `EE331L` | Electrical Machines Lab | BS EE | `fee` | **Pending Approval** |
| `EE341` | Power System Analysis | BS EE | `fee` | **Pending Approval** |
| `EE341L` | Power System Lab | BS EE | `fee` | **Pending Approval** |
| `EE401` | Power Distribution and Utilization | BS EE | `fee` | **Pending Approval** |
| `EE411` | Digital Communication | BS EE | `fee` | **Pending Approval** |
| `EE411L` | Digital Communication Lab | BS EE | `fee` | **Pending Approval** |
| `EE421` | Digital Control Systems | BS EE | `fee` | **Pending Approval** |
| `EE431` | Power Electronics | BS EE | `fee` | **Pending Approval** |
| `EE431L` | Power Electronics Lab | BS EE | `fee` | **Pending Approval** |
| `EE441` | Renewable Energy Systems | BS EE | `fee` | **Pending Approval** |
| `EE499` | Final Year Project | BS EE | `fee` | **Pending Approval** |
| `ES101` | Engineering Mechanics | BS ME, BS Civil, BS Chemical | `fbs` | **Pending Approval** |
| `ES102` | Basic Electrical Engineering | BS ME, BS Civil, BS Chemical | `fbs` | **Pending Approval** |
| `HM101` | English Composition & Comprehension | All BS Programs | `fbs` | **Pending Approval** |
| `HM102` | Communication & Presentation Skills | All BS Programs | `fbs` | **Pending Approval** |
| `HM201` | Islamic Studies / Ethics | All BS Programs | `fbs` | **Pending Approval** |
| `HM202` | Pakistan Studies | All BS Programs | `fbs` | **Pending Approval** |
| `HMXYZ` | Humanities Elective (Placeholder) | BS EE | `fbs` | **Pending Approval** |
| `ME201` | Thermodynamics I | BS Mechanical | `fme` | **Pending Approval** |
| `ME202` | Mechanics of Materials I | BS Mechanical | `fme` | **Pending Approval** |
| `MM101` | Engineering Materials | BS Mechanical, BS Civil | `dmse` | **Pending Approval** |
| `MS101` | Principles of Management | BS Management Sciences | `mgs` | **Pending Approval** |
| `MS102` | Principles of Microeconomics | BS Management Sciences | `mgs` | **Pending Approval** |
| `MT101` | Calculus I | All Engineering Programs | `fbs` | **Pending Approval** |
| `SE201` | Software Engineering Principles | BS SE, BS CS | `fcse` | **Pending Approval** |
| `SE201L` | Software Engineering Principles Lab | BS SE | `fcse` | **Pending Approval** |
| `SE211` | Software Requirements Engineering | BS SE | `fcse` | **Pending Approval** |
| `SE301` | Software Design & Architecture | BS SE | `fcse` | **Pending Approval** |
| `SE301L` | Software Design & Architecture Lab | BS SE | `fcse` | **Pending Approval** |
| `SE311` | Software Quality Engineering | BS SE | `fcse` | **Pending Approval** |
| `SE401` | Software Project Management | BS SE | `fcse` | **Pending Approval** |

---

## 3. Review of Missing Prerequisite Course Records

The audit identified **5 prerequisite course codes** referenced in active course descriptions that do not exist as top-level catalog entries in `courses.json`:

| Missing Code | Required By Course | Required By Title | Context / Probable Cause | Recommended Action |
|---|---|---|---|---|
| `AI321` | `AI331` | Deep Neural Networks | In earlier curriculum revisions, `AI321` was Machine Learning before being renumbered to `AI221`. | Verify whether prerequisite should map to `AI221` (Machine Learning). |
| `AI321` | `AI462` | Nature Inspired Computing | Same as above. | Verify whether prerequisite should map to `AI221`. |
| `MM102` | `EE485` | Electrical Insulation Materials | Prospectus lists `MM102` as prerequisite for EE materials elective. The catalog contains `MM101` (Engineering Materials). | Confirm if `MM102` was an older materials course or typo for `MM101`. |
| `MS290` | `EE486` | Power Economics and Management | Prospectus lists `MS290` as prerequisite. MGS economics courses are numbered `MS102` / `MS202`. | Cross-check with MGS department course numbering. |
| `ME101` | `ME418` | CAD/CAM | Required by CAD/CAM. Likely introductory engineering drawing or CAD. | Add placeholder course node or map to introductory graphics course. |
| `ME261` | `ME468` | Mechanical Engineering Design | Required by senior mechanical design elective. | Verify FME mechanics / machine design prerequisite sequence. |

---

## 4. Review of Unmatched CourseHub Instructors (66 Records)

CourseHub's catalog snapshot lists 190 instructors, of which 124 matched GIKI faculty profile slugs. **66 instructor names remain unmatched** (`faculty_id: null`):

### 4.1 Department Distribution
- **FCSE (35):** Largest volume of unmatched names, predominantly Teaching Assistants, Lab Engineers, and adjunct staff.
- **FBS (10):** TAs and research associates.
- **FMCE (7):** Materials and Chemical staff.
- **MgS (5):** Visiting business faculty.
- **DCvE (4):** Civil engineering adjuncts.
- **FME (3):** Mechanical engineers.
- **FEE (2):** Electrical lab engineers.

### 4.2 Key Matching Patterns & Observations
1. **Single-Name Entries:** Several records contain only a first name or title (e.g. *"Ms. Beenish"*, *"Mr. Talha"*, *"Dr. Taj"*, *"Dr. Zoya"*, *"Mr. Asif"*, *"Mr. Saqib"*). These cannot be safely linked without additional context (email or course code).
2. **Lab Engineers & Graduate Assistants:** Names like *"Engr. Aneeqa Ramzan"*, *"Engr. Arooba Saeed"*, *"Maham Shahzadi"* frequently represent non-permanent lab instructors who do not receive a persistent personnel page on `giki.edu.pk`.
3. **Abbreviated Middle Names (High-Probability Matches Pending Sign-Off):**
   - CourseHub `"Dr. Taqi A. Cheema"` (FME) $\longleftrightarrow$ GIKI Faculty `dr-taqi-ahmad-cheema`
   - CourseHub `"Dr. Ramzan A. Karim"` (FMCE) $\longleftrightarrow$ GIKI Faculty `dr-muhammad-ramzan-abdul-karim`
   - CourseHub `"Dr. Nasir Amin"` (MgS) $\longleftrightarrow$ GIKI Faculty `dr-muhammad-nasir-amin`
   - CourseHub `"Dr. Omar A. Qureshi"` (FME) $\longleftrightarrow$ GIKI Faculty `dr-omar-ahmad-qureshi`
   - CourseHub `"Dr. M. Ashraf Tanoli"` (DCvE) $\longleftrightarrow$ GIKI Faculty `dr-muhammad-ashraf-tanoli`
   - CourseHub `"Dr. M. Waseem"` (DCvE) $\longleftrightarrow$ GIKI Faculty `dr-muhammad-waseem`

> [!NOTE]
> These high-probability matches are recorded here for review. They have **not** been automatically overwritten in the data to preserve audit trail integrity.

---

## 5. Review of Faculty Designation Discrepancies (31 Records)

31 faculty members have discrepancies between the title listed on their department roster page and the title on their individual profile page. This frequently indicates recent promotions, administrative appointments, or study leave updates:

| Faculty ID | Listing Designation | Profile Page Designation | Analysis & Recommendation |
|---|---|---|---|
| `dr-tauheed-shehbaz` | Lecturer | Assistant Professor | **Promotion:** Profile page reflects promotion to Assistant Professor. Use profile designation. |
| `dr-ammar-arshad` | Assistant Professor | Associate Professor | **Promotion:** Profile reflects promotion to Associate Professor. |
| `dr-dur-e-zehra-baig` | Assistant Professor | Associate Professor | **Promotion:** Profile reflects promotion to Associate Professor. |
| `dr-javaid-rabbani-khan-professor` | Professor | HoD-Professor | **Administrative Role:** Appointed Head of Department. |
| `dr-salman-ahmed` | HoD (Computer Science & Artificial Intelligence) | Head of Department (Computer Science & Artificial Intelligence) | Minor punctuation difference. |
| `dr-masroor-hussain` | HoD (Computer Engineering & Data Science) | Professor (HEC Approved PhD Supervisor) | Administrative designation on listing; academic rank on profile. |
| `dr-muhammad-ramzan-abdul-karim` | HoD (Materials) & Associate Professor | HoD (Materials) and Associate Professor | Ampersand vs. "and". |
| `dr-fahd-nawaz-khan` | Dean & Professor | Dean and Professor | Ampersand vs. "and". |
| `prof-dr-qadeer-ul-hasan` | DEAN | DEAN, HEC Approved Ph.D. Supervisor | Extended credential on profile. |
| `fazal-wahab` | Lecturer | Lecturer (ON STUDY LEAVE) | **Status:** Currently on study leave. |
| `engr-ramesha-tariq` | Lecturer | Lecturer (ON STUDY LEAVE) | **Status:** Currently on study leave. |
| `nazia-shahzadi-lecturer` | Lecturer | Lecturer (On Study Leave) | **Status:** Currently on study leave. |
| `professor-ghulam-hussain` | Professor | Professor (on leave) | **Status:** Currently on leave. |
| `dr-syed-zameer-abbas` | Assistant Professor (HEC Approved PhD Supervisor) | Assistant Professor | HEC recognition listed on department roster. |
| `dr-hadeed-ahmed-sher` | Associate Professor | Associate Professor (HEC approved PhD Supervisor) | HEC recognition listed on profile. |
| `dr-fahd-sikandar-khan` | Assistant Professor | Director/PI HBL Center for Blockchain... - Assistant Professor | Research center leadership listed on profile. |
| `dr-imran-khan` | Assistant Professor | Assistant Professor Civil | Department qualifier added on profile. |
| `dr-m-faizan-ul-haq` | Assistant Professor | Assistant Professor Civil | Department qualifier added on profile. |
| `muntazir-abbas` | Lecturer | Lecturer Civil | Department qualifier added on profile. |
| `abdullah-khan` | Lecturer | Lecturer FMCE | Faculty qualifier added on profile. |
| `dr-ali-imran-sandhu` | Assistant Professor | Assistant Professor FCSE | Faculty qualifier added on profile. |
| `dr-taj-munir` | Assistant Professor | Assistant Professor FBS | Faculty qualifier added on profile. |
| `suhaib` | Assistant Professor | Assistant Professor School of Management Sciences | School qualifier added on profile. |
| `dr-adnan-shah` | Assistant Professor | Assistant Professor (MIEEE, EUR ING) | Professional credentials (IEEE/EUR ING) on profile. |
| `dr-muhammad-irfan` | Assistant Professor | Assistant Professor, Team Lead, at Chip-DV | Industry lab leadership noted on profile. |
| `mr-muhammad-qasim-zafar` | Assistant Professor | Assistant Professor/Incharge Industrial CNC & 3D Printing Lab | Lab in-charge title on profile. |
| `ms-bakhtawar-rubab` | Lecturer English | Lecturer | Subject designation on listing. |
| `sami-farooq` | Dean-Professor | Dean, School of Management Sciences (SMgS), Professor Operations & Supply Chain Management | Expanded administrative and professorial title. |
| `prof-dr-sirajul-haq` | Professor of Mathematics and Ex-Dean Student Affairs | Faculty of Basic Sciences | Historic administrative title on listing; unit name on profile. |
| `abbas` | HoD ( Cyber Security & Software Engineering) | Professor and Head of Department (Cybersecurity & Software Engineering) | Rank (Professor) omitted on listing card. |
| `engr-dr-shahabuddin-ansari` | Associate Professor (HEC Approved PhD Supervisor) | Associate Professor... HoD (Computer Engineering & Data Science) | HoD appointment noted on profile. |

---

## 6. Incomplete Records & Ambiguities

### 6.1 Missing Faculty Information
- **Missing Emails (24 records):** Public cards for 24 faculty members do not list an email address. Recommended to collect via university directory lookup.
- **Missing Academic Details (20 records):** 15 lack structured qualifications and 16 lack research interests (these are categorized as `verified: false`).
- **Empty Profile Bodies (2 records):**
  - `dr-nasir-javed-assistant-professor-fes`
  - `dr-asif-khan-assistant-professor`

### 6.2 Dual Appointment
- **`prof-dr-nisar-ahmed`:** Officially listed under both `fbs` (Faculty of Basic Sciences) and `fee` (Faculty of Electrical Engineering). Preserved as a dual appointment.

### 6.3 Prospectus False Positive
- **`Muhammad Naveed` (FCSE Lab Engineer) $\longleftrightarrow$ `Mr. Muhammad Naeem`:** Flagged as `review_needed: True`. Must **not** be merged into the prospectus credentials of Mr. Naeem.
