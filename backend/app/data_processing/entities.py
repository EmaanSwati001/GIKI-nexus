"""
Entity-specific cleaning and transformation logic for GIKI Nexus datasets.
Handles individual domain models: Units, Faculty, Courses, Publications,
Research Areas, Programs, Other Personnel, and Curation Review Queue.
"""

import re
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import Counter, defaultdict
from .cleaner import (
    normalize_text,
    normalize_label,
    clean_string_list,
    sanitize_email,
    clean_phone,
    clean_course_code,
    parse_credits,
    map_course_prefix_to_unit,
    normalize_instructor_name,
    parse_faculty_designation_components,
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
    - Parse designation components (rank, administrative role, credentials)
    - Prefer profile page designation for display while preserving listing designation
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
        "designation_discrepancies": 0,
    }

    for f in raw_faculty:
        fid = normalize_text(f.get("id"))
        name = normalize_text(f.get("name"))
        desig = normalize_text(f.get("designation"))
        desig_profile = normalize_text(f.get("designation_on_profile_page"))
        status = normalize_text(f.get("status")) or "active"

        # Parse designation components and discrepancy
        desig_comp = parse_faculty_designation_components(desig, desig_profile, status)
        if desig_comp["designation_discrepancy"]:
            stats["designation_discrepancies"] += 1

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
            "preferred_designation": desig_comp["preferred_designation"],
            "academic_rank": desig_comp["academic_rank"],
            "administrative_role": desig_comp["administrative_role"],
            "professional_credentials": desig_comp["professional_credentials"],
            "designation_discrepancy": desig_comp["designation_discrepancy"],
            "designation_review_status": desig_comp["designation_review_status"],
        }
        cleaned.append(item)

    cleaned.sort(key=lambda x: (x["units"][0] if x["units"] else "zzz", x["name"] or ""))
    return cleaned, stats


def process_courses(
    raw_courses: List[Dict[str, Any]], valid_unit_ids: Set[str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Clean and standardize courses:
    - Normalizes course codes, titles, credits, and offerings
    - Resolves missing academic-unit mappings using approved prefix rules
    - Tracks mapping source ('prospectus_verified' vs 'prefix_based_mapping')
    - Checks prerequisites against full catalog and tracks unresolved codes
    """
    cleaned = []
    stats = {
        "total": len(raw_courses),
        "with_description": 0,
        "with_credits": 0,
        "with_unit": 0,
        "prospectus_verified_units": 0,
        "prefix_mapped_units": 0,
        "unresolved_units": 0,
        "mapped_by_unit": defaultdict(int),
        "in_live_catalog": 0,
        "courses_with_unresolved_prereqs": 0,
        "total_unresolved_prereq_refs": 0,
    }

    # First pass: collect all clean course codes across the dataset
    all_catalog_codes = {clean_course_code(c.get("code")) for c in raw_courses if clean_course_code(c.get("code"))}

    for c in raw_courses:
        code = clean_course_code(c.get("code"))
        name = normalize_text(c.get("name"))
        credits_str, credit_hours = parse_credits(c.get("credits"))

        prereqs = [clean_course_code(p) for p in c.get("prerequisites", []) if clean_course_code(p)]
        prereqs = sorted(set(prereqs))
        prereqs_raw = normalize_text(c.get("prerequisites_raw"))
        description = normalize_text(c.get("description"))

        # Unit resolution:
        # 1. If course already has a valid unit, preserve as prospectus-verified
        # 2. If missing, apply safe anchored prefix mapping
        # 3. If cannot be mapped, leave as None (unresolved)
        unit = normalize_text(c.get("unit"))
        unit_mapping_source = None

        if unit:
            unit_mapping_source = "prospectus_verified"
            stats["prospectus_verified_units"] += 1
            stats["with_unit"] += 1
        else:
            mapped_unit, matched_prefix = map_course_prefix_to_unit(code, valid_unit_ids)
            if mapped_unit:
                unit = mapped_unit
                unit_mapping_source = "prefix_based_mapping"
                stats["prefix_mapped_units"] += 1
                stats["with_unit"] += 1
                stats["mapped_by_unit"][mapped_unit] += 1
            else:
                unit = None
                unit_mapping_source = None
                stats["unresolved_units"] += 1

        # Prerequisite validation against catalog
        prereq_statuses: Dict[str, str] = {}
        unresolved_prereqs: List[str] = []
        for p in prereqs:
            if p in all_catalog_codes:
                prereq_statuses[p] = "resolved"
            else:
                prereq_statuses[p] = "unresolved"
                unresolved_prereqs.append(p)
                stats["total_unresolved_prereq_refs"] += 1

        if unresolved_prereqs:
            stats["courses_with_unresolved_prereqs"] += 1

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
            "unit_mapping_source": unit_mapping_source,
            "unresolved_prerequisites": sorted(unresolved_prereqs),
            "prerequisite_statuses": prereq_statuses,
            "offered_in": offered,
            "is_lab": is_lab,
            "provenance": c.get("provenance", {}),
        }
        cleaned.append(item)

    cleaned.sort(key=lambda x: x["code"] or "")
    # Convert defaultdict to regular dict for clean JSON serialization
    stats["mapped_by_unit"] = dict(stats["mapped_by_unit"])
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


# Six specific suggested instructor match candidates identified during data audit
SUGGESTED_INSTRUCTOR_MAP = {
    "dr. taqi a. cheema": ("dr-taqi-ahmad-cheema", "Suggested middle initial match with Dr. Taqi Ahmad Cheema"),
    "dr. ramzan a. karim": ("dr-muhammad-ramzan-abdul-karim", "Suggested name variant match with Dr. Muhammad Ramzan Abdul Karim"),
    "dr. nasir amin": ("dr-muhammad-nasir-amin", "Suggested prefix variant match with Dr. Muhammad Nasir Amin"),
    "dr. omar a. qureshi": ("dr-omar-ahmad-qureshi", "Suggested middle initial match with Dr. Omar Ahmad Qureshi"),
    "dr. m. ashraf tanoli": ("dr-muhammad-ashraf-tanoli", "Suggested abbreviation match with Dr. Muhammad Ashraf Tanoli"),
    "dr. m. waseem": ("dr-muhammad-waseem", "Suggested abbreviation match with Dr. Muhammad Waseem"),
}


def process_coursehub_links(
    raw_links: List[Dict[str, Any]], valid_faculty_ids: Optional[Set[str]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Clean and structure CourseHub instructor links with a 4-status system:
    - matched: Exact or confirmed match with official faculty roster (124 records)
    - suggested: 6 identified candidates pending human review (retains faculty_id as null, suggested_faculty_id populated)
    - needs_review: 17 single-name or ambiguous instructor records
    - unmatched: 43 unlisted instructors (lab engineers, teaching assistants, or visiting instructors)
    """
    cleaned = []
    stats = {
        "total": len(raw_links),
        "matched": 0,
        "suggested": 0,
        "needs_review": 0,
        "unmatched": 0,
    }

    for l in raw_links:
        raw_name = l.get("coursehub_name")
        ch_name = normalize_text(raw_name)
        norm_name = normalize_instructor_name(ch_name)
        ch_faculty = normalize_text(l.get("coursehub_faculty"))
        existing_fid = normalize_text(l.get("faculty_id"))
        score = l.get("match_score")
        method = normalize_text(l.get("match_method"))

        if existing_fid and (valid_faculty_ids is None or existing_fid in valid_faculty_ids):
            match_status = "matched"
            suggested_fid = None
            notes = "Verified match against official faculty roster"
            stats["matched"] += 1
        else:
            # Check suggested matches
            lookup_key = (ch_name or "").lower()
            if lookup_key in SUGGESTED_INSTRUCTOR_MAP:
                suggested_fid, note_desc = SUGGESTED_INSTRUCTOR_MAP[lookup_key]
                match_status = "suggested"
                notes = note_desc
                stats["suggested"] += 1
            else:
                # Check single name or ambiguous tokens
                tokens = [
                    t for t in (norm_name or "").split()
                    if t.lower().rstrip(".") not in ("dr", "mr", "ms", "mrs", "prof", "engr")
                ]
                if len(tokens) <= 1:
                    match_status = "needs_review"
                    suggested_fid = None
                    notes = "Single name or ambiguous token; cannot match to unique faculty without department roster review"
                    stats["needs_review"] += 1
                else:
                    match_status = "unmatched"
                    suggested_fid = None
                    notes = "Unmatched instructor: Likely visiting instructor, lab engineer, or teaching assistant without official faculty profile"
                    stats["unmatched"] += 1

        cleaned.append({
            "coursehub_name": ch_name,
            "coursehub_faculty": ch_faculty,
            "faculty_id": existing_fid if match_status == "matched" else None,
            "match_method": method,
            "match_score": float(score) if score is not None else None,
            "match_status": match_status,
            "suggested_faculty_id": suggested_fid,
            "notes": notes,
        })

    return cleaned, stats


def build_curation_queue(
    faculty: List[Dict[str, Any]],
    courses: List[Dict[str, Any]],
    coursehub_links: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Build a comprehensive, categorized curation review queue.
    Categorizes all items into:
    - resolved: Issues resolved with documented deterministic rules (e.g. prefix-mapped courses, designation preference)
    - needs_review: Ambiguous items requiring human domain expert review (e.g. missing prerequisites, suggested instructor matches, single names)
    - informational: Preserved structural observations (e.g. dual appointments, unlisted visiting instructors, courses lacking syllabus)
    """
    queue = []
    course_codes = {c["code"] for c in courses if c.get("code")}

    # 1. Faculty review items
    for f in faculty:
        fid = f["id"]
        fname = f.get("name")
        funits = f.get("units", [])
        furl = f.get("profile_url")

        # Designation discrepancies (resolved via preferred profile page designation)
        if f.get("designation_discrepancy"):
            queue.append({
                "entity_type": "faculty",
                "id": fid,
                "name": fname,
                "units": funits,
                "category": "designation_discrepancy",
                "reasons": [
                    f"Designation mismatch: Listing page shows '{f['designation']}' but Profile page shows '{f['designation_on_profile_page']}'"
                ],
                "resolution_status": "resolved",
                "resolution_notes": "Profile page designation adopted as preferred display designation; academic rank and admin roles extracted; both sources preserved in record.",
                "source_info": {
                    "listing_designation": f.get("designation"),
                    "profile_designation": f.get("designation_on_profile_page"),
                    "preferred_designation": f.get("preferred_designation"),
                },
                "profile_url": furl,
            })

        # Dual / Multiple appointments (informational)
        if len(funits) > 1:
            queue.append({
                "entity_type": "faculty",
                "id": fid,
                "name": fname,
                "units": funits,
                "category": "dual_appointment",
                "reasons": [f"Dual/multiple academic unit appointment: {', '.join(funits)}"],
                "resolution_status": "informational",
                "resolution_notes": "Preserved legitimate cross-department appointment (e.g. FBS and FEE) without discarding secondary affiliation.",
                "source_info": {"units": funits},
                "profile_url": furl,
            })

        # Missing expected fields (needs review)
        if f.get("missing_fields"):
            queue.append({
                "entity_type": "faculty",
                "id": fid,
                "name": fname,
                "units": funits,
                "category": "incomplete_profile",
                "reasons": [f"Missing expected academic fields: {', '.join(f['missing_fields'])}"],
                "resolution_status": "needs_review",
                "resolution_notes": "Preserved with null/empty values without fabricating fake data; requires administrative update from university portal.",
                "source_info": {"missing_fields": f.get("missing_fields")},
                "profile_url": furl,
            })

        # Dubious prospectus match (needs review)
        if f.get("prospectus_2025") and f["prospectus_2025"].get("review_needed"):
            queue.append({
                "entity_type": "faculty",
                "id": fid,
                "name": fname,
                "units": funits,
                "category": "dubious_prospectus_match",
                "reasons": [
                    f"Dubious prospectus match: Faculty '{fname}' matched to prospectus '{f['prospectus_2025']['listed_as']}' (Score: {f['prospectus_2025']['match_score']})"
                ],
                "resolution_status": "needs_review",
                "resolution_notes": "Distinguishing name tokens diverge (e.g. Muhammad Naveed vs Mr. Muhammad Naeem); kept separate with review flag.",
                "source_info": f.get("prospectus_2025"),
                "profile_url": furl,
            })

        # Research interests prose summary only (informational)
        if not f.get("research_interests") and f.get("research_summary"):
            queue.append({
                "entity_type": "faculty",
                "id": fid,
                "name": fname,
                "units": funits,
                "category": "narrative_research_interests",
                "reasons": ["Research interests provided only as prose paragraph (research_summary)"],
                "resolution_status": "informational",
                "resolution_notes": "Structured topic list empty; narrative paragraph preserved for search indexing.",
                "source_info": {"research_summary": f.get("research_summary")[:100] + "..."},
                "profile_url": furl,
            })

        # Large qualifications list (informational)
        if len(f.get("qualifications", [])) > 8:
            queue.append({
                "entity_type": "faculty",
                "id": fid,
                "name": fname,
                "units": funits,
                "category": "unstructured_qualifications",
                "reasons": ["Qualifications field contains unusually large list (>8 items), may contain prose or awards"],
                "resolution_status": "informational",
                "resolution_notes": "Preserved raw items without loss; human curation can split awards from degrees.",
                "source_info": {"qualifications_count": len(f.get("qualifications", []))},
                "profile_url": furl,
            })

    # 2. Courses review items
    for c in courses:
        cid = c["code"]
        cname = c.get("name")
        cunits = [c.get("unit")] if c.get("unit") else []

        # Prefix-mapped courses (resolved)
        if c.get("unit_mapping_source") == "prefix_based_mapping":
            queue.append({
                "entity_type": "course",
                "id": cid,
                "name": cname,
                "units": cunits,
                "category": "prefix_based_unit_mapping",
                "reasons": [f"Course unit was unassigned; mapped to academic unit '{c.get('unit')}' based on course code prefix rule"],
                "resolution_status": "resolved",
                "resolution_notes": f"Mapped to academic unit '{c.get('unit')}' via prefix rule (prefix_based_mapping); degree program curriculum placements preserved.",
                "source_info": {
                    "mapped_unit": c.get("unit"),
                    "mapping_source": "prefix_based_mapping",
                    "offered_in_count": len(c.get("offered_in", [])),
                },
                "profile_url": None,
            })

        # Unresolved prerequisites (needs review)
        if c.get("unresolved_prerequisites"):
            missing_codes = c["unresolved_prerequisites"]
            queue.append({
                "entity_type": "course",
                "id": cid,
                "name": cname,
                "units": cunits,
                "category": "unresolved_prerequisite",
                "reasons": [
                    f"Unresolved prerequisite: Requires course '{p}' which does not exist in catalog snapshot"
                    for p in missing_codes
                ],
                "resolution_status": "needs_review",
                "resolution_notes": f"Missing prerequisite codes {missing_codes} preserved as unresolved; pending review by department curriculum committee.",
                "source_info": {
                    "unresolved_prerequisites": missing_codes,
                    "prerequisites_raw": c.get("prerequisites_raw"),
                },
                "profile_url": None,
            })

        # Missing syllabus or credit hours (informational)
        if not c.get("description") or c.get("credits") is None:
            missing_meta = []
            if not c.get("description"):
                missing_meta.append("Missing course description/syllabus")
            if c.get("credits") is None:
                missing_meta.append("Missing credit hours")
            queue.append({
                "entity_type": "course",
                "id": cid,
                "name": cname,
                "units": cunits,
                "category": "missing_catalog_metadata",
                "reasons": missing_meta,
                "resolution_status": "informational",
                "resolution_notes": "Course entry lacks syllabus or credits in curriculum snapshot; course retained in catalog.",
                "source_info": {"has_description": bool(c.get("description")), "credits": c.get("credits")},
                "profile_url": None,
            })

    # 3. CourseHub instructors review items
    for l in coursehub_links:
        status = l.get("match_status")
        ch_name = l.get("coursehub_name")
        ch_faculty = l.get("coursehub_faculty")
        fac_units = [ch_faculty] if ch_faculty else []

        if status == "suggested":
            queue.append({
                "entity_type": "coursehub_instructor",
                "id": ch_name,
                "name": ch_name,
                "units": fac_units,
                "category": "coursehub_suggested_match",
                "reasons": [
                    f"Suggested candidate match: '{ch_name}' linked to faculty '{l.get('suggested_faculty_id')}' ({l.get('notes')})"
                ],
                "resolution_status": "needs_review",
                "resolution_notes": f"Candidate link proposed ({l.get('notes')}); faculty_id kept null until human confirmation.",
                "source_info": {
                    "suggested_faculty_id": l.get("suggested_faculty_id"),
                    "notes": l.get("notes"),
                    "coursehub_faculty": ch_faculty,
                },
                "profile_url": None,
            })
        elif status == "needs_review":
            queue.append({
                "entity_type": "coursehub_instructor",
                "id": ch_name,
                "name": ch_name,
                "units": fac_units,
                "category": "coursehub_ambiguous_name",
                "reasons": [l.get("notes") or "Single name or ambiguous token"],
                "resolution_status": "needs_review",
                "resolution_notes": "Single token name requires departmental roster check to associate with specific faculty member.",
                "source_info": {"coursehub_faculty": ch_faculty},
                "profile_url": None,
            })
        elif status == "unmatched":
            queue.append({
                "entity_type": "coursehub_instructor",
                "id": ch_name,
                "name": ch_name,
                "units": fac_units,
                "category": "coursehub_unmatched_instructor",
                "reasons": [l.get("notes") or "Unmatched instructor"],
                "resolution_status": "informational",
                "resolution_notes": "Instructor not listed on official faculty roster; preserved in registry without artificial link.",
                "source_info": {"coursehub_faculty": ch_faculty},
                "profile_url": None,
            })

    # Sort queue: needs_review first, then resolved, then informational
    order = {"needs_review": 0, "resolved": 1, "informational": 2}
    queue.sort(key=lambda x: (order.get(x["resolution_status"], 3), x["entity_type"], x["id"]))
    return queue
