"""
Entity-specific cleaning and transformation logic for GIKI Nexus datasets.
Handles individual domain models: Units, Faculty, Courses, Publications,
Research Areas, Programs, Other Personnel, and Curation Review Queue.
"""

import re
from typing import Dict, List, Any, Set, Tuple
from collections import Counter, defaultdict
from .cleaner import (
    normalize_text,
    normalize_label,
    clean_string_list,
    sanitize_email,
    clean_phone,
    clean_course_code,
    parse_credits,
)


def process_units(raw_units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and standardize academic units."""
    cleaned = []
    for u in raw_units:
        item = {
            "id": normalize_text(u.get("id")),
            "name": normalize_text(u.get("name")),
            "short": normalize_text(u.get("short")),
            "type": normalize_text(u.get("type")),
            "parent": normalize_text(u.get("parent")),
            "listing": normalize_text(u.get("listing")),
            "source_url": normalize_text(u.get("source_url")),
        }
        cleaned.append(item)
    return cleaned


def process_faculty(
    raw_faculty: List[Dict[str, Any]], valid_unit_ids: Set[str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Clean faculty records:
    - Normalize text fields, qualifications, and research interests
    - Sanitize email and phone
    - Detect prospectus false-positive matches
    - Preserve source URLs and provenance
    - Accurately determine verified flag and missing_fields
    """
    cleaned = []
    stats = {
        "total": len(raw_faculty),
        "verified": 0,
        "prospectus_flags": 0,
        "missing_email": 0,
        "missing_qualifications": 0,
        "missing_research_interests": 0,
        "no_unit": 0,
    }

    for f in raw_faculty:
        fid = normalize_text(f.get("id"))
        name = normalize_text(f.get("name"))
        desig = normalize_text(f.get("designation"))
        desig_profile = normalize_text(f.get("designation_on_profile_page"))
        status = normalize_text(f.get("status")) or "active"

        raw_units = f.get("units", [])
        units = sorted({normalize_text(u) for u in raw_units if normalize_text(u)})

        email = sanitize_email(f.get("email"))
        phone = clean_phone(f.get("phone_or_ext"))
        office = normalize_text(f.get("office"))
        bio = normalize_text(f.get("bio"))

        quals_raw = normalize_text(f.get("qualifications_raw"))
        quals = clean_string_list(f.get("qualifications"))
        quals_summary = normalize_text(f.get("qualifications_summary"))

        ri_raw = normalize_text(f.get("research_interests_raw"))
        ri = clean_string_list(f.get("research_interests"))
        ri_summary = normalize_text(f.get("research_summary"))

        ra_ids = sorted({normalize_text(r) for r in f.get("research_area_ids", []) if normalize_text(r)})

        # Prospectus cross-check inspection
        prosp = f.get("prospectus_2025")
        prosp_obj = None
        prosp_review_flag = False
        if prosp and isinstance(prosp, dict):
            prosp_listed = normalize_text(prosp.get("listed_as"))
            score = prosp.get("match_score", 0.0)
            
            # Catch known false positives where distinguishing names do not match (e.g. Naveed vs Naeem)
            # Filter out titles and common honorific prefixes (muhammad, syed, mr, dr, engr, prof)
            honorifics = {"mr", "mr.", "dr", "dr.", "ms", "ms.", "mrs", "mrs.", "prof", "prof.", "engr", "engr.", "muhammad", "mohammad", "syed"}
            f_tokens = {re.sub(r"[^\w]", "", t.lower()) for t in (name or "").split()}
            p_tokens = {re.sub(r"[^\w]", "", t.lower()) for t in (prosp_listed or "").split()}
            
            distinguishing_f = {t for t in f_tokens if t not in honorifics and len(t) > 2}
            distinguishing_p = {t for t in p_tokens if t not in honorifics and len(t) > 2}
            
            if distinguishing_f and distinguishing_p and not (distinguishing_f & distinguishing_p):
                prosp_review_flag = True
                stats["prospectus_flags"] += 1

            prosp_obj = {
                "listed_as": prosp_listed,
                "detail": normalize_text(prosp.get("detail")),
                "section": normalize_text(prosp.get("section")),
                "match_score": score,
                "review_needed": prosp_review_flag,
            }

        # Calculate missing fields
        missing = []
        if not email:
            missing.append("email")
            stats["missing_email"] += 1
        if not quals and not quals_summary:
            missing.append("qualifications")
            stats["missing_qualifications"] += 1
        if not ri and not ri_summary:
            missing.append("research_interests")
            stats["missing_research_interests"] += 1
        if not units:
            stats["no_unit"] += 1

        # A faculty member is verified only if assigned to an official unit
        # and has both qualifications and research interests on record.
        verified = bool(units) and ("qualifications" not in missing) and ("research_interests" not in missing)
        if verified:
            stats["verified"] += 1

        item = {
            "id": fid,
            "name": name,
            "designation": desig,
            "designation_on_profile_page": desig_profile,
            "status": status,
            "units": units,
            "email": email,
            "phone_or_ext": phone,
            "office": office,
            "qualifications_raw": quals_raw,
            "qualifications": quals,
            "qualifications_summary": quals_summary,
            "research_interests_raw": ri_raw,
            "research_interests": ri,
            "research_summary": ri_summary,
            "bio": bio,
            "publication_count_on_profile": f.get("publication_count_on_profile", 0),
            "profile_sections": [normalize_text(s) for s in f.get("profile_sections", []) if normalize_text(s)],
            "photo_url": normalize_text(f.get("photo_url")),
            "profile_url": normalize_text(f.get("profile_url")),
            "listing_urls": [normalize_text(u) for u in f.get("listing_urls", []) if normalize_text(u)],
            "website_categories": f.get("website_categories", []),
            "prospectus_2025": prosp_obj,
            "provenance": f.get("provenance", {}),
            "missing_fields": missing,
            "verified": verified,
            "research_area_ids": ra_ids,
        }
        cleaned.append(item)

    cleaned.sort(key=lambda x: (x["units"][0] if x["units"] else "zzz", x["name"] or ""))
    return cleaned, stats


def process_courses(
    raw_courses: List[Dict[str, Any]], valid_unit_ids: Set[str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Clean and standardize courses."""
    cleaned = []
    stats = {
        "total": len(raw_courses),
        "with_description": 0,
        "with_credits": 0,
        "with_unit": 0,
        "in_live_catalog": 0,
    }

    for c in raw_courses:
        code = clean_course_code(c.get("code"))
        name = normalize_text(c.get("name"))
        credits_str, credit_hours = parse_credits(c.get("credits"))

        prereqs = [clean_course_code(p) for p in c.get("prerequisites", []) if clean_course_code(p)]
        prereqs = sorted(set(prereqs))
        prereqs_raw = normalize_text(c.get("prerequisites_raw"))
        description = normalize_text(c.get("description"))
        unit = normalize_text(c.get("unit"))

        offered = []
        for o in c.get("offered_in", []):
            offered.append({
                "program_id": normalize_text(o.get("program_id")),
                "year": o.get("year"),
                "semester": o.get("semester"),
                "name_in_catalog": normalize_text(o.get("name_in_catalog")),
            })

        is_lab = bool(c.get("is_lab") or (code and code.endswith("L")))

        if description:
            stats["with_description"] += 1
        if credits_str is not None:
            stats["with_credits"] += 1
        if unit:
            stats["with_unit"] += 1
        if offered:
            stats["in_live_catalog"] += 1

        item = {
            "code": code,
            "name": name,
            "credits": credits_str,
            "credit_hours": credit_hours,
            "prerequisites": prereqs,
            "prerequisites_raw": prereqs_raw,
            "description": description,
            "unit": unit,
            "offered_in": offered,
            "is_lab": is_lab,
            "provenance": c.get("provenance", {}),
        }
        cleaned.append(item)

    cleaned.sort(key=lambda x: x["code"] or "")
    return cleaned, stats


def process_publications(
    raw_publications: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Clean publications:
    - Normalize citation text
    - Deduplicate exact duplicate citations belonging to the same author
    - Preserve year, DOI, and publication type
    """
    cleaned = []
    seen_by_author = set()
    stats = {
        "total_raw": len(raw_publications),
        "duplicates_removed": 0,
        "with_year": 0,
        "with_doi": 0,
        "unique_publications": 0,
    }

    for p in raw_publications:
        fid = normalize_text(p.get("faculty_id"))
        cit = normalize_text(p.get("citation"))
        if not cit:
            continue

        # Check intra-author duplicate
        author_cit_key = (fid, cit.lower())
        if author_cit_key in seen_by_author:
            stats["duplicates_removed"] += 1
            continue
        seen_by_author.add(author_cit_key)

        ptype = normalize_text(p.get("type")) or "unspecified"
        sec = normalize_text(p.get("section_heading"))
        year = p.get("year")
        if isinstance(year, int) and (1950 <= year <= 2030):
            stats["with_year"] += 1
        else:
            year = None

        doi = normalize_text(p.get("doi"))
        if doi:
            stats["with_doi"] += 1

        item = {
            "faculty_id": fid,
            "citation": cit,
            "type": ptype,
            "section_heading": sec,
            "year": year,
            "doi": doi,
        }
        cleaned.append(item)

    stats["unique_publications"] = len(cleaned)
    return cleaned, stats


def process_research_areas(
    raw_areas: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Clean and deduplicate research areas:
    - Resolves duplicate ID collision (e.g. 'computational-fluid-dynamics')
    - Cleans labels (strips trailing parentheses and punctuation)
    - Merges faculty lists and units cleanly
    """
    merged_map: Dict[str, Dict[str, Any]] = {}
    stats = {
        "raw_count": len(raw_areas),
        "id_collisions_resolved": 0,
        "final_count": 0,
    }

    for ra in raw_areas:
        raw_id = normalize_text(ra.get("id"))
        raw_label = normalize_label(ra.get("label"))
        if not raw_id:
            continue

        fac_ids = set(ra.get("faculty_ids", []))
        units = set(ra.get("units", []))
        aliases = set(ra.get("aliases", []))

        if raw_id in merged_map:
            stats["id_collisions_resolved"] += 1
            existing = merged_map[raw_id]
            existing["faculty_ids"].update(fac_ids)
            existing["units"].update(units)
            # If the current label is cleaner (e.g. doesn't have stray characters), keep it
            if raw_label and len(raw_label) <= len(existing["label"]):
                existing["label"] = raw_label
            if raw_label != existing["label"]:
                existing["aliases"].add(raw_label)
            existing["aliases"].update(aliases)
        else:
            merged_map[raw_id] = {
                "id": raw_id,
                "label": raw_label,
                "aliases": aliases,
                "faculty_ids": fac_ids,
                "units": units,
            }

    cleaned = []
    for raid, data in merged_map.items():
        faculty_list = sorted(data["faculty_ids"])
        clean_aliases = sorted(a for a in data["aliases"] if a and a != data["label"])
        cleaned.append({
            "id": raid,
            "label": data["label"],
            "aliases": clean_aliases,
            "faculty_ids": faculty_list,
            "faculty_count": len(faculty_list),
            "units": sorted(data["units"]),
        })

    cleaned.sort(key=lambda x: (-x["faculty_count"], x["id"]))
    stats["final_count"] = len(cleaned)
    return cleaned, stats


def process_programs(raw_programs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and standardize academic programs."""
    cleaned = []
    for p in raw_programs:
        cleaned.append({
            "id": normalize_text(p.get("id")),
            "name": normalize_text(p.get("name")),
            "unit": normalize_text(p.get("unit")),
            "coursehub_program_id": p.get("coursehub_program_id"),
        })
    return cleaned


def process_other_personnel(raw_other: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean records of personnel who have profile pages but no current department listing."""
    cleaned = []
    for o in raw_other:
        cleaned.append({
            "id": normalize_text(o.get("id")),
            "name": normalize_text(o.get("name")),
            "designation": normalize_text(o.get("designation")),
            "email": sanitize_email(o.get("email")),
            "office": normalize_text(o.get("office")),
            "website_categories": o.get("website_categories", []),
            "profile_sections": [normalize_text(s) for s in o.get("profile_sections", []) if normalize_text(s)],
            "profile_url": normalize_text(o.get("profile_url")),
            "note": normalize_text(o.get("note")),
            "provenance": o.get("provenance", {}),
        })
    return cleaned


def process_coursehub_links(raw_links: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean CourseHub instructor link mappings."""
    cleaned = []
    for l in raw_links:
        score = l.get("match_score")
        cleaned.append({
            "coursehub_name": normalize_text(l.get("coursehub_name")),
            "coursehub_faculty": normalize_text(l.get("coursehub_faculty")),
            "faculty_id": normalize_text(l.get("faculty_id")),
            "match_method": normalize_text(l.get("match_method")),
            "match_score": float(score) if score is not None else None,
        })
    return cleaned


def build_curation_queue(
    faculty: List[Dict[str, Any]],
    courses: List[Dict[str, Any]],
    coursehub_links: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Build a unified review queue for records needing human verification:
    - Faculty with missing fields, prose summaries, designation conflicts, or multiple units
    - Courses with missing units or broken prerequisite references
    - Unmatched CourseHub instructors
    """
    queue = []
    course_codes = {c["code"] for c in courses if c.get("code")}

    # 1. Faculty review items
    for f in faculty:
        reasons = []
        if f.get("missing_fields"):
            reasons.append(f"Missing required/expected fields: {', '.join(f['missing_fields'])}")
        if not f.get("units"):
            reasons.append("Unassigned unit: Found only on general /faculty/ page, not on department listing")
        elif len(f.get("units", [])) > 1:
            reasons.append(f"Dual/multiple unit appointment: {', '.join(f['units'])}")
        if len(f.get("qualifications", [])) > 8:
            reasons.append("Qualifications field contains unusually large list (>8), may contain prose or awards")
        if not f.get("research_interests") and f.get("research_summary"):
            reasons.append("Research interests only provided as prose paragraph (research_summary)")
        if f.get("designation") and f.get("designation_on_profile_page"):
            if f["designation"].lower() != f["designation_on_profile_page"].lower():
                reasons.append(
                    f"Designation mismatch: Listing page shows '{f['designation']}' but Profile page shows '{f['designation_on_profile_page']}'"
                )
        if f.get("prospectus_2025") and f["prospectus_2025"].get("review_needed"):
            reasons.append(
                f"Dubious prospectus match: Faculty '{f['name']}' matched to prospectus '{f['prospectus_2025']['listed_as']}' (Score: {f['prospectus_2025']['match_score']})"
            )

        if reasons:
            queue.append({
                "entity_type": "faculty",
                "id": f["id"],
                "name": f["name"],
                "units": f["units"],
                "reasons": reasons,
                "profile_url": f.get("profile_url"),
            })

    # 2. Courses review items
    for c in courses:
        reasons = []
        if not c.get("unit"):
            reasons.append("Missing unit: Course is offered in curriculum but not linked to an academic unit")
        if not c.get("description"):
            reasons.append("Missing course description/syllabus")
        if c.get("credits") is None:
            reasons.append("Missing credit hours")
        for prereq in c.get("prerequisites", []):
            if prereq not in course_codes:
                reasons.append(f"Broken prerequisite: Requires course '{prereq}' which does not exist in catalog")

        if reasons:
            queue.append({
                "entity_type": "course",
                "id": c["code"],
                "name": c.get("name"),
                "units": [c.get("unit")] if c.get("unit") else [],
                "reasons": reasons,
                "profile_url": None,
            })

    # 3. CourseHub instructors review items (unmatched)
    for l in coursehub_links:
        if not l.get("faculty_id"):
            queue.append({
                "entity_type": "coursehub_instructor",
                "id": l["coursehub_name"],
                "name": l["coursehub_name"],
                "units": [l.get("coursehub_faculty")] if l.get("coursehub_faculty") else [],
                "reasons": ["Unmatched instructor: No corresponding faculty profile found on official GIKI website"],
                "profile_url": None,
            })

    return queue
