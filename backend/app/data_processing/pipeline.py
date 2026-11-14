"""
Data processing pipeline orchestrator for GIKI Nexus.
Reads raw data from data/raw/, validates, cleans, deduplicates,
and saves standardized outputs to data/processed/.
Leaves raw input files strictly untouched.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .validator import (
    ValidationReport,
    validate_units,
    validate_faculty,
    validate_courses,
    validate_publications,
    validate_research_areas,
    validate_programs,
)
from .entities import (
    process_units,
    process_faculty,
    process_courses,
    process_publications,
    process_research_areas,
    process_programs,
    process_other_personnel,
    process_coursehub_links,
    build_curation_queue,
)

logger = logging.getLogger(__name__)


class DataPipeline:
    def __init__(self, raw_dir: Path, processed_dir: Path):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)

    def load_json(self, filename: str) -> Any:
        path = self.raw_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Raw file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_json(self, filename: str, data: Any) -> None:
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        path = self.processed_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def run(self) -> Dict[str, Any]:
        """
        Execute full data cleaning, normalization, and validation pipeline.
        """
        logger.info(f"Running pipeline with raw_dir={self.raw_dir}, processed_dir={self.processed_dir}")

        # 1. Load raw inputs
        raw_units_data = self.load_json("units.json")
        raw_faculty_data = self.load_json("faculty.json")
        raw_courses_data = self.load_json("courses.json")
        raw_pubs_data = self.load_json("publications.json")
        raw_areas_data = self.load_json("research_areas.json")
        raw_programs_data = self.load_json("programs.json")
        raw_other_data = self.load_json("other_personnel.json")
        raw_ch_data = self.load_json("coursehub_instructor_links.json")

        raw_units = raw_units_data.get("units", [])
        raw_faculty = raw_faculty_data.get("faculty", [])
        raw_courses = raw_courses_data.get("courses", [])
        raw_pubs = raw_pubs_data.get("publications", [])
        raw_areas = raw_areas_data.get("research_areas", [])
        raw_programs = raw_programs_data.get("programs", [])
        raw_other = raw_other_data.get("people", [])
        raw_ch_links = raw_ch_data.get("links", [])

        # 2. Process Units
        units = process_units(raw_units)
        valid_unit_ids = {u["id"] for u in units if u.get("id")}

        # 3. Process Faculty
        faculty, faculty_stats = process_faculty(raw_faculty, valid_unit_ids)
        valid_faculty_ids = {f["id"] for f in faculty if f.get("id")}

        # 4. Process Courses
        courses, courses_stats = process_courses(raw_courses, valid_unit_ids)

        # 5. Process Publications (intra-author deduplication)
        publications, pub_stats = process_publications(raw_pubs)

        # 6. Process Research Areas (ID collision resolution and label cleanup)
        research_areas, area_stats = process_research_areas(raw_areas)

        # 7. Process Programs
        programs = process_programs(raw_programs)

        # 8. Process Other Personnel
        other_personnel = process_other_personnel(raw_other)

        # 9. Process CourseHub Links
        coursehub_links = process_coursehub_links(raw_ch_links)

        # 10. Build Review Queue
        review_queue = build_curation_queue(faculty, courses, coursehub_links)

        # 11. Run Validations on Cleaned Data
        report = ValidationReport()
        validate_units(units, report)
        validate_faculty(faculty, valid_unit_ids, report)
        validate_courses(courses, valid_unit_ids, report)
        validate_publications(publications, valid_faculty_ids, report)
        validate_research_areas(research_areas, valid_faculty_ids, report)
        validate_programs(programs, valid_unit_ids, report)

        # 12. Save cleaned outputs to processed_dir
        meta = {
            "pipeline_version": "1.0.0",
            "source_raw_dir": str(self.raw_dir),
            "generated_from": [
                "GIKI Official Website (giki.edu.pk)",
                "GIKI Undergraduate Prospectus 2025",
                "GIKI Course Hub Snapshot",
            ],
        }

        self.save_json("units.json", {"meta": meta, "count": len(units), "units": units})
        self.save_json("faculty.json", {"meta": meta, "count": len(faculty), "faculty": faculty})
        self.save_json("courses.json", {"meta": meta, "count": len(courses), "courses": courses})
        self.save_json(
            "publications.json",
            {
                "meta": {
                    **meta,
                    "note": f"Cleaned citations with {pub_stats['duplicates_removed']} intra-author duplicates removed.",
                },
                "count": len(publications),
                "publications": publications,
            },
        )
        self.save_json(
            "research_areas.json",
            {
                "meta": {
                    **meta,
                    "note": f"Deduplicated research areas ({area_stats['id_collisions_resolved']} collisions resolved).",
                },
                "count": len(research_areas),
                "research_areas": research_areas,
            },
        )
        self.save_json("programs.json", {"meta": meta, "count": len(programs), "programs": programs})
        self.save_json(
            "other_personnel.json",
            {
                "meta": meta,
                "count": len(other_personnel),
                "people": other_personnel,
            },
        )
        self.save_json(
            "coursehub_instructor_links.json",
            {
                "meta": meta,
                "count": len(coursehub_links),
                "links": coursehub_links,
            },
        )
        self.save_json(
            "needs_review.json",
            {
                "meta": meta,
                "count": len(review_queue),
                "records": review_queue,
            },
        )

        pipeline_summary = {
            "meta": meta,
            "counts": {
                "units": len(units),
                "faculty": len(faculty),
                "courses": len(courses),
                "publications": len(publications),
                "research_areas": len(research_areas),
                "programs": len(programs),
                "other_personnel": len(other_personnel),
                "coursehub_instructor_links": len(coursehub_links),
                "review_queue_items": len(review_queue),
            },
            "statistics": {
                "faculty": faculty_stats,
                "courses": courses_stats,
                "publications": pub_stats,
                "research_areas": area_stats,
            },
            "validation": report.to_dict(),
        }

        self.save_json("processing_report.json", pipeline_summary)
        return pipeline_summary
