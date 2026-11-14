# GIKI Nexus: seed dataset

This is the academic data for the GIKI Nexus knowledge graph: faculty, research areas, publications, courses and programs. Each record carries its source URL. The data covers every GIKI faculty, not only FCSE.

Scraped from giki.edu.pk on **10 Nov 2026** and cross-checked against the **GIKI Undergraduate Prospectus 2025** and the **GIKI Course Hub** repo (read-only; the repo was not changed).

## What's in `out/`

| File | Records | What it is | Graph role |
|---|---|---|---|
| `units.json` | 9 | Faculties and departments (FCSE, FEE, FME, FBS, FMCE → DMSE and DChE, Civil, MGS) | `Department` nodes |
| `faculty.json` | 181 | Every person on a current faculty listing page | `Faculty` nodes |
| `research_areas.json` | 657 | Research interests normalised across people (e.g. "ML" and "Machine Learning" merged) | `ResearchArea` nodes, `RESEARCHES` edges |
| `publications.json` | 2,893 | Citations parsed from profile pages (110 faculty have lists) | `Publication` nodes, `AUTHORED` edges |
| `courses.json` | 647 | Code, name, credits, prerequisites, description, unit, and where each sits in a program | `Course` nodes, `PREREQUISITE_OF` and `OFFERED_IN` edges |
| `programs.json` | 15 | BS programs from Course Hub's live catalog | `Program` nodes |
| `coursehub_instructor_links.json` | 190 | Course Hub instructor names matched to faculty IDs (124 matched) | Joins Course Hub to Nexus |
| `other_personnel.json` | 20 | People with a personnel page but on no current listing (board members, staff, former or late faculty) | Not imported |
| `needs_review.json` | 36 | Records to check by hand, each with the reason | Curation to-do list |
| `build_report.json` | n/a | Counts and coverage | Numbers for the data-audit report |

### Faculty per unit
FCSE 48 · MGS 33 · FBS 22 · Civil 19 · FME 19 · FEE 15 · DMSE 13 · DChE 12. Prof. Dr. Nisar Ahmed is listed under both FBS and FEE. One person appears only on the general `/faculty/` page and has no unit.

## Key fields and rules

- **`id`** is the person's slug on giki.edu.pk (`/personnel/<id>/`), so it is stable and joins across files.
- **`verified: true`** means the person is on an official department listing **and** has qualifications and research interests on record. 161 of 181 qualify. The rest are listed in `needs_review.json`. The scope document requires that unverified records are never presented as verified, and this flag is how that's enforced.
- **`status`** is `active`, `on_leave` or `on_study_leave`, taken from the site's labels.
- **`*_raw` fields** hold the original text as it appears on the site. The parsed lists (`qualifications`, `research_interests`) are derived from them. When a profile is written as a paragraph rather than a list, the text goes in `research_summary` or `qualifications_summary` and the list is left empty, so nothing is invented.
- **`publications.json`**: `citation` is verbatim. `year`, `doi` and `type` are best-effort extractions, and `type` follows the heading the faculty member used on their page. 230 citations have no detectable year and 446 include a DOI.
- **`prospectus_2025`** is filled when the person matches a prospectus faculty entry (35 matches). The prospectus lists qualifications in a parseable bullet format mainly for FCSE, so this is a partial cross-check. The website is the primary source.
- **`provenance.sources`** lists every page a record came from, plus `scraped_at`.

## Known gaps

1. **Who teaches which course** isn't in any public file. It lives in Course Hub's database (`course_instructors` table). A read-only export, joined using `coursehub_instructor_links.json`, would add `TEACHES` edges.
2. **CourseHub resource links** (notes, slides, past papers) are also only in the Course Hub database (`files` and `file_course_links`).
3. 16 faculty have no research interests and 15 have no qualifications on the site. These are mostly lab staff, research officers and new or on-leave faculty.
4. Faculty contact details (email, extension, office) come from public official pages. The scope document's privacy limits apply to *student* data, so these fields are fine to store. Even so, the matching UI should not display them more widely than needed.

## Rebuilding

```bash
python3 scripts/reassemble.py      # only needed after a fresh browser scrape
python3 scripts/build_dataset.py <path-to-giki_course_hub-1> <prospectus.txt>
```
`raw/giki_scrape_raw.json` is the untouched scrape (201 personnel pages and 9 listing pages), so the build can be re-run without scraping again.
