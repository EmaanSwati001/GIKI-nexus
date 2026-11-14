"""
Validation script for GIKI Nexus datasets.
Can be executed from project root against either data/raw or data/processed.
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.data_processing.validator import (
    ValidationReport,
    validate_units,
    validate_faculty,
    validate_courses,
    validate_publications,
    validate_research_areas,
    validate_programs,
)


def load_dataset(target_dir: Path, filename: str):
    path = target_dir / filename
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Validate GIKI Nexus JSON datasets.")
    parser.add_argument(
        "--target",
        type=str,
        default="data/processed",
        help="Target directory to validate (e.g. data/raw or data/processed)",
    )
    args = parser.parse_args()

    target_dir = PROJECT_ROOT / args.target
    print("=" * 65)
    print(f"GIKI NEXUS - DATASET VALIDATION REPORT")
    print(f"Target Directory: {target_dir}")
    print("=" * 65)

    if not target_dir.exists():
        print(f"Error: Directory '{target_dir}' does not exist.")
        sys.exit(1)

    report = ValidationReport()

    # Load entities
    units_data = load_dataset(target_dir, "units.json")
    units = units_data.get("units", []) if units_data else []
    validate_units(units, report)
    valid_unit_ids = {u["id"] for u in units if u.get("id")}

    faculty_data = load_dataset(target_dir, "faculty.json")
    faculty = faculty_data.get("faculty", []) if faculty_data else []
    validate_faculty(faculty, valid_unit_ids, report)
    valid_faculty_ids = {f["id"] for f in faculty if f.get("id")}

    courses_data = load_dataset(target_dir, "courses.json")
    courses = courses_data.get("courses", []) if courses_data else []
    validate_courses(courses, valid_unit_ids, report)

    pubs_data = load_dataset(target_dir, "publications.json")
    pubs = pubs_data.get("publications", []) if pubs_data else []
    validate_publications(pubs, valid_faculty_ids, report)

    areas_data = load_dataset(target_dir, "research_areas.json")
    areas = areas_data.get("research_areas", []) if areas_data else []
    validate_research_areas(areas, valid_faculty_ids, report)

    progs_data = load_dataset(target_dir, "programs.json")
    progs = progs_data.get("programs", []) if progs_data else []
    validate_programs(progs, valid_unit_ids, report)

    # Output Summary
    print("\nRecord Counts:")
    for entity, count in report.record_counts.items():
        print(f"  - {entity.title():<20}: {count:>6} records")

    print("\nDuplicates Identified:")
    dup_found = False
    for cat, items in report.duplicates.items():
        if items:
            dup_found = True
            print(f"  - {cat}: {len(items)} duplicates")
    if not dup_found:
        print("  - None (All entity IDs and intra-author citations are unique)")

    print("\nMissing Field Statistics:")
    for entity, counts in report.missing_field_stats.items():
        print(f"  - {entity.title()}:")
        for field, c in counts.items():
            print(f"      • {field:<22}: {c} missing")

    print("\nIntegrity Issues / Anomalies:")
    if report.integrity_issues:
        print(f"  Total issues flagged: {len(report.integrity_issues)}")
        # Group by issue type
        grouped = {}
        for issue in report.integrity_issues:
            key = issue.get("issue")
            grouped[key] = grouped.get(key, 0) + 1
        for issue_msg, cnt in list(grouped.items())[:10]:
            print(f"    [{cnt}x] {issue_msg}")
        if len(grouped) > 10:
            print(f"    ... and {len(grouped) - 10} other distinct issue patterns")
    else:
        print("  - None")

    print("\nValidation Outcome:")
    print(f"  Errors: {len(report.errors)} | Warnings: {len(report.warnings)}")
    print("=" * 65)


if __name__ == "__main__":
    main()
