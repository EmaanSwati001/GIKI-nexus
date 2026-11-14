"""
Data validation module for GIKI Nexus datasets.
Checks structure, types, required fields, foreign key integrity,
duplicates, and generates actionable validation reports.
"""

from typing import Dict, List, Any, Set, Tuple
from collections import Counter, defaultdict


class ValidationReport:
    def __init__(self):
        self.record_counts: Dict[str, int] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.integrity_issues: List[Dict[str, Any]] = []
        self.duplicates: Dict[str, List[Any]] = defaultdict(list)
        self.missing_field_stats: Dict[str, Counter] = defaultdict(Counter)

    def add_error(self, message: str):
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_counts": self.record_counts,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
            "duplicates": {k: len(v) for k, v in self.duplicates.items()},
            "missing_fields": {k: dict(v) for k, v in self.missing_field_stats.items()},
            "integrity_issues": self.integrity_issues,
        }


def validate_units(units: List[Dict[str, Any]], report: ValidationReport) -> None:
    report.record_counts["units"] = len(units)
    seen_ids = set()

    for u in units:
        uid = u.get("id")
        if not uid:
            report.add_error("Unit record missing 'id'")
            continue
        if uid in seen_ids:
            report.duplicates["units"].append(uid)
            report.add_error(f"Duplicate unit ID: '{uid}'")
        seen_ids.add(uid)

        for req in ["name", "short", "type"]:
            if not u.get(req):
                report.missing_field_stats["units"][req] += 1
                report.add_warning(f"Unit '{uid}' missing required field '{req}'")


def validate_faculty(
    faculty: List[Dict[str, Any]], valid_unit_ids: Set[str], report: ValidationReport
) -> None:
    report.record_counts["faculty"] = len(faculty)
    seen_ids = set()

    for f in faculty:
        fid = f.get("id")
        if not fid:
            report.add_error("Faculty record missing 'id'")
            continue
        if fid in seen_ids:
            report.duplicates["faculty"].append(fid)
            report.add_error(f"Duplicate faculty ID: '{fid}'")
        seen_ids.add(fid)

        if not f.get("name"):
            report.missing_field_stats["faculty"]["name"] += 1
            report.add_error(f"Faculty '{fid}' missing 'name'")

        if not f.get("profile_url"):
            report.missing_field_stats["faculty"]["profile_url"] += 1
            report.add_error(f"Faculty '{fid}' missing 'profile_url'")

        # Missing optional/important academic fields
        for opt in ["email", "qualifications", "research_interests", "units"]:
            val = f.get(opt)
            if not val:
                report.missing_field_stats["faculty"][opt] += 1

        # Check unit foreign keys
        for u in f.get("units", []):
            if valid_unit_ids and u not in valid_unit_ids:
                report.integrity_issues.append({
                    "entity": "faculty",
                    "id": fid,
                    "issue": f"References unknown unit '{u}'",
                })


def validate_courses(
    courses: List[Dict[str, Any]], valid_unit_ids: Set[str], report: ValidationReport
) -> None:
    report.record_counts["courses"] = len(courses)
    course_codes = set()

    for c in courses:
        code = c.get("code")
        if not code:
            report.add_error("Course record missing 'code'")
            continue
        if code in course_codes:
            report.duplicates["courses"].append(code)
            report.add_error(f"Duplicate course code: '{code}'")
        course_codes.add(code)

        if not c.get("name"):
            report.missing_field_stats["courses"]["name"] += 1
            report.add_warning(f"Course '{code}' missing 'name'")

        if c.get("credits") is None:
            report.missing_field_stats["courses"]["credits"] += 1

        if not c.get("description"):
            report.missing_field_stats["courses"]["description"] += 1

        unit = c.get("unit")
        if not unit:
            report.missing_field_stats["courses"]["unit"] += 1
        elif valid_unit_ids and unit not in valid_unit_ids:
            report.integrity_issues.append({
                "entity": "course",
                "code": code,
                "issue": f"References unknown unit '{unit}'",
            })

    # Check prerequisite references
    for c in courses:
        code = c.get("code")
        for prereq in c.get("prerequisites", []):
            if prereq not in course_codes:
                report.integrity_issues.append({
                    "entity": "course_prerequisite",
                    "course": code,
                    "issue": f"Prerequisite '{prereq}' not found in course catalog",
                })


def validate_publications(
    publications: List[Dict[str, Any]], valid_faculty_ids: Set[str], report: ValidationReport
) -> None:
    report.record_counts["publications"] = len(publications)
    seen_by_faculty: Dict[str, Set[str]] = defaultdict(set)

    for p in publications:
        fid = p.get("faculty_id")
        citation = p.get("citation")

        if not fid:
            report.add_error("Publication missing 'faculty_id'")
        elif valid_faculty_ids and fid not in valid_faculty_ids:
            report.integrity_issues.append({
                "entity": "publication",
                "issue": f"References unknown faculty_id '{fid}'",
            })

        if not citation:
            report.add_error(f"Publication for faculty '{fid}' missing 'citation'")
        else:
            norm_cit = citation.strip().lower()
            if fid and norm_cit in seen_by_faculty[fid]:
                report.duplicates["publications_same_author"].append({
                    "faculty_id": fid,
                    "citation": citation[:60] + "...",
                })
            elif fid:
                seen_by_faculty[fid].add(norm_cit)

        if not p.get("year"):
            report.missing_field_stats["publications"]["year"] += 1
        if not p.get("doi"):
            report.missing_field_stats["publications"]["doi"] += 1


def validate_research_areas(
    research_areas: List[Dict[str, Any]], valid_faculty_ids: Set[str], report: ValidationReport
) -> None:
    report.record_counts["research_areas"] = len(research_areas)
    seen_ids = set()

    for ra in research_areas:
        raid = ra.get("id")
        if not raid:
            report.add_error("Research area missing 'id'")
            continue
        if raid in seen_ids:
            report.duplicates["research_areas"].append(raid)
            report.add_error(f"Duplicate research area ID: '{raid}'")
        seen_ids.add(raid)

        if not ra.get("label"):
            report.add_error(f"Research area '{raid}' missing 'label'")

        # Validate faculty IDs in research area
        for fid in ra.get("faculty_ids", []):
            if valid_faculty_ids and fid not in valid_faculty_ids:
                report.integrity_issues.append({
                    "entity": "research_area",
                    "id": raid,
                    "issue": f"References unknown faculty_id '{fid}'",
                })


def validate_programs(
    programs: List[Dict[str, Any]], valid_unit_ids: Set[str], report: ValidationReport
) -> None:
    report.record_counts["programs"] = len(programs)
    seen_ids = set()

    for p in programs:
        pid = p.get("id")
        if not pid:
            report.add_error("Program missing 'id'")
            continue
        if pid in seen_ids:
            report.duplicates["programs"].append(pid)
            report.add_error(f"Duplicate program ID: '{pid}'")
        seen_ids.add(pid)

        unit = p.get("unit")
        if not unit:
            report.missing_field_stats["programs"]["unit"] += 1
        elif valid_unit_ids and unit not in valid_unit_ids:
            report.integrity_issues.append({
                "entity": "program",
                "id": pid,
                "issue": f"References unknown unit '{unit}'",
            })
