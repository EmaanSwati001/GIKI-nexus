# GIKI Nexus: Data Dictionary

**Document Version:** 1.0.0  
**Target Environment:** GIKI Nexus Pipeline & Storage Models  
**Reference Directory:** `data/processed/` (and raw references in `data/raw/`)

---

## 1. Academic Units (`units.json`)

Represents faculties and academic departments within GIKI.

| Field Name | Type | Nullable | Description | Example Value |
|---|---|---|---|---|
| `id` | `string` | No | Unique slug identifier for the academic unit | `"fcse"`, `"dmse"` |
| `name` | `string` | No | Full official name of the faculty or department | `"Faculty of Computer Science and Engineering"` |
| `short` | `string` | No | Standard official acronym/abbreviation | `"FCSE"`, `"FEE"`, `"DMSE"` |
| `type` | `string` | No | Unit classification (`faculty` or `department`) | `"faculty"`, `"department"` |
| `parent` | `string` | Yes | Parent unit `id` if this is a sub-department; otherwise `null` | `"fmce"` (for `dmse` and `dche`), `null` |
| `listing` | `string` | Yes | Relative URL path to faculty profile listing page on website | `"/fcse/faculty-profiles/"` |
| `source_url`| `string` | Yes | Absolute URL to the official listing page | `"https://giki.edu.pk/fcse/faculty-profiles/"` |

---

## 2. Faculty Profiles (`faculty.json`)

Represents academic faculty members currently listed on official GIKI department pages.

| Field Name | Type | Nullable | Description | Example Value |
|---|---|---|---|---|
| `id` | `string` | No | Stable slug identifier derived from personal profile URL | `"dr-zahid-ahmed"`, `"prof-dr-nisar-ahmed"` |
| `name` | `string` | No | Sanitized full name (status markers removed) | `"Dr. Zahid Ahmed"`, `"Muhammad Naveed"` |
| `designation` | `string` | Yes | Primary academic rank/position from department listing | `"Associate Professor"`, `"Lecturer"` |
| `designation_on_profile_page` | `string` | Yes | Designation as stated on individual profile page | `"HoD-Professor"`, `"Lecturer (ON STUDY LEAVE)"` |
| `status` | `string` | No | Employment status (`active`, `on_leave`, `on_study_leave`) | `"active"`, `"on_study_leave"` |
| `units` | `list[string]` | No | List of unit IDs the faculty belongs to | `["fcse"]`, `["fbs", "fee"]` |
| `email` | `string` | Yes | Official email address (lowercased, spaces removed) | `"zahid.ahmed@giki.edu.pk"` |
| `phone_or_ext` | `string` | Yes | Phone extension or direct line | `"Ext: 2341"` |
| `office` | `string` | Yes | Office room number or building location | `"Room 214, CS Building"` |
| `qualifications_raw` | `string` | Yes | Unparsed qualifications text from web page | `"PhD (Computer Science), MSc ..."` |
| `qualifications` | `list[string]` | No | Structured list of degrees and qualifications | `["PhD Computer Science", "MS Software Eng"]` |
| `qualifications_summary` | `string` | Yes | Narrative biography if qualifications are in prose | `"Dr. X received his doctorate from..."` |
| `research_interests_raw` | `string` | Yes | Unparsed research interests text | `"Machine Learning, Deep Learning, NLP"` |
| `research_interests` | `list[string]` | No | Structured list of cleaned research topic strings | `["Machine Learning", "Computer Vision"]` |
| `research_summary` | `string` | Yes | Narrative research summary when not listed as bullet points | `"His research focuses on applied cryptography..."` |
| `bio` | `string` | Yes | Biographical summary paragraph | `"Brief overview of academic background..."` |
| `publication_count_on_profile`| `int` | No | Count of publications found on faculty profile page | `24` |
| `profile_sections` | `list[string]` | No | List of tab/section headings present on profile page | `["Education", "Publications", "Awards"]` |
| `photo_url` | `string` | Yes | Direct URL to official faculty portrait | `"https://giki.edu.pk/wp-content/uploads/..."` |
| `profile_url` | `string` | No | Canonical web URL of the faculty profile | `"https://giki.edu.pk/personnel/dr-zahid-ahmed/"` |
| `listing_urls` | `list[string]` | No | URLs of department listing pages where card appears | `["https://giki.edu.pk/fcse/faculty-profiles/"]` |
| `website_categories` | `list[string]` | No | WordPress category slugs associated with profile | `["faculty-member", "fcse"]` |
| `prospectus_2025` | `object` | Yes | Prospectus cross-check match object (`listed_as`, `detail`, `section`, `match_score`, `review_needed`) | `{"match_score": 0.95, "review_needed": false}` |
| `provenance` | `object` | No | Provenance metadata containing `sources` and `scraped_at` | `{"sources": [...], "scraped_at": "..."}` |
| `missing_fields` | `list[string]` | No | List of missing key fields (`email`, `qualifications`, etc.) | `["email"]` |
| `verified` | `boolean` | No | Flag indicating complete profile (unit + quals + research) | `true`, `false` |
| `research_area_ids` | `list[string]` | No | Slugs of linked research area nodes | `["machine-learning", "computer-vision"]` |

---

## 3. Academic Courses (`courses.json`)

Represents undergraduate and graduate courses offered at GIKI.

| Field Name | Type | Nullable | Description | Example Value |
|---|---|---|---|---|
| `code` | `string` | No | Standardized course code identifier | `"CS101"`, `"AI202"`, `"CS3XX/CS4xx"` |
| `name` | `string` | Yes | Full official title of the course | `"Introduction to Computing"`, `"Machine Learning"` |
| `credits` | `string` | Yes | Standardized lecture-lab-credit representation | `"3-0-3"`, `"0-3-1"` |
| `credit_hours` | `int` | Yes | Total credit hours as an integer | `3`, `1`, `4` |
| `prerequisites` | `list[string]` | No | List of required prerequisite course codes | `["CS101", "MT101"]` |
| `prerequisites_raw` | `string` | Yes | Unparsed prerequisite string from prospectus | `"CS101 or Equivalent / MT101"` |
| `description` | `string` | Yes | Course syllabus, topics, and objectives paragraph | `"Covers data structures, arrays, linked lists..."` |
| `unit` | `string` | Yes | ID of the offering academic unit (`null` if unassigned) | `"fcse"`, `"fee"`, `null` |
| `offered_in` | `list[object]`| No | Degree program offerings (`program_id`, `year`, `semester`, `name_in_catalog`) | `[{"program_id": "bs-computer-science", "year": 1, "semester": 1}]` |
| `is_lab` | `boolean` | No | Indicates whether the course is a dedicated laboratory | `false`, `true` |
| `provenance` | `object` | No | Provenance metadata detailing sources (prospectus, Course Hub) | `{"sources": ["GIKI Prospectus 2025, p. 89"]}` |

---

## 4. Publications & Citations (`publications.json`)

Represents academic citations and research papers published by GIKI faculty.

| Field Name | Type | Nullable | Description | Example Value |
|---|---|---|---|---|
| `faculty_id` | `string` | No | Foreign key linking to faculty member's `id` | `"dr-massab-junaid"` |
| `citation` | `string` | No | Full citation string as extracted from faculty profile | `"M. Shamir, M. Junaid... (2023) Journal of Materials..."` |
| `type` | `string` | No | Classification (`journal`, `conference`, `book_or_chapter`, `patent`, `unspecified`) | `"journal"`, `"conference"` |
| `section_heading` | `string` | Yes | Original heading on profile page under which citation appeared | `"Selected Journal Publications"` |
| `year` | `int` | Yes | Best-effort parsed publication year | `2023`, `2021`, `null` |
| `doi` | `string` | Yes | Extracted Digital Object Identifier (DOI) string | `"10.1016/j.matdes.2023.111822"`, `null` |

---

## 5. Research Areas (`research_areas.json`)

Represents normalized research topics and academic domains across the university.

| Field Name | Type | Nullable | Description | Example Value |
|---|---|---|---|---|
| `id` | `string` | No | Unique slug identifier for the research domain | `"machine-learning"`, `"computational-fluid-dynamics"` |
| `label` | `string` | No | Canonical display label (trailing punctuation stripped) | `"Machine Learning"`, `"Computational Fluid Dynamics"` |
| `aliases` | `list[string]` | No | Variant spellings, synonyms, or raw input strings merged into this topic | `["ML", "Machine Learning (ML)"]` |
| `faculty_ids` | `list[string]` | No | List of faculty member IDs actively working in this area | `["dr-zahid-ahmed", "dr-taqi-ahmad-cheema"]` |
| `faculty_count`| `int` | No | Number of faculty associated with this research area | `5` |
| `units` | `list[string]` | No | Academic units with active research in this area | `["fcse", "fme", "dcve"]` |

---

## 6. Academic Programs (`programs.json`)

Represents undergraduate degree programs offered at GIKI.

| Field Name | Type | Nullable | Description | Example Value |
|---|---|---|---|---|
| `id` | `string` | No | Unique slug identifier for the degree program | `"bs-computer-science"`, `"bs-artificial-intelligence"` |
| `name` | `string` | No | Full program title | `"BS Computer Science"`, `"BS Mechanical Engineering"` |
| `unit` | `string` | No | ID of the host academic faculty | `"fcse"`, `"fme"`, `"fee"`, `"dcve"`, `"fmce"`, `"mgs"` |
| `coursehub_program_id` | `int` | Yes | Integer ID from CourseHub catalog snapshot | `1`, `4`, `12` |

---

## 7. Other Personnel (`other_personnel.json`)

Personnel records that exist in the web scrape but are excluded from active faculty listings.

| Field Name | Type | Nullable | Description | Example Value |
|---|---|---|---|---|
| `id` | `string` | No | Slug identifier from profile URL | `"prof-dr-khasan-s-karimov"`, `"ali-shaukat"` |
| `name` | `string` | No | Full name of individual | `"Prof. Dr. Khasan S. Karimov (Late)"` |
| `designation` | `string` | Yes | Role stated on profile page | `"Professor"`, `"Marketing Manager"` |
| `email` | `string` | Yes | Email address if available | `"ali.shaukat@giki.edu.pk"`, `null` |
| `office` | `string` | Yes | Office location if available | `"Administration Block"` |
| `website_categories` | `list[string]` | No | Category slugs | `[]` |
| `profile_sections` | `list[string]` | No | Headings present on profile page | `["Profile", "Contact"]` |
| `profile_url` | `string` | No | Web URL of profile | `"https://giki.edu.pk/personnel/ali-shaukat/"` |
| `note` | `string` | No | Context explaining why not imported as active faculty | `"Personnel page on giki.edu.pk but not on department listing..."` |
| `provenance` | `object` | No | Sources and scrape timestamp | `{"sources": [...], "scraped_at": "..."}` |

---

## 8. CourseHub Instructor Links (`coursehub_instructor_links.json`)

Mappings linking CourseHub instructor strings to GIKI Nexus faculty IDs.

| Field Name | Type | Nullable | Description | Example Value |
|---|---|---|---|---|
| `coursehub_name` | `string` | No | Instructor name string as stored in CourseHub | `"Dr. Zahid Ahmed"`, `"Ms. Beenish"` |
| `coursehub_faculty` | `string` | Yes | Faculty name in CourseHub | `"FCSE"`, `"FME"` |
| `faculty_id` | `string` | Yes | Matched GIKI Nexus faculty slug (`null` if unmatched) | `"dr-zahid-ahmed"`, `null` |
| `match_method` | `string` | Yes | Strategy used (`full_name`, `unique_partial_name`, `null`) | `"full_name"`, `"unique_partial_name"` |
| `match_score` | `float` | Yes | Fuzzy string similarity score (0.0 to 1.0) | `1.0`, `0.9`, `null` |

---

## 9. Curation Review Queue (`needs_review.json`)

Unified queue of entities requiring human inspection and verification.

| Field Name | Type | Nullable | Description | Example Value |
|---|---|---|---|---|
| `entity_type` | `string` | No | Type of entity (`faculty`, `course`, `coursehub_instructor`)| `"faculty"`, `"course"` |
| `id` | `string` | No | Identifier of the entity requiring review | `"dr-asif-khan-assistant-professor"`, `"AI102"` |
| `name` | `string` | Yes | Display name or title | `"Dr. Asif Khan"`, `"AI102"` |
| `units` | `list[string]` | No | Associated units if known | `[]`, `["fcse"]` |
| `reasons` | `list[string]` | No | Explicit reasons why review is required | `["Unassigned unit: Found only on general /faculty/ page"]` |
| `profile_url` | `string` | Yes | URL to original source for verification | `"https://giki.edu.pk/personnel/..."`, `null` |
