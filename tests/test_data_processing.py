"""
Comprehensive automated unit tests for GIKI Nexus data processing module.
Tests cover:
- Reading valid JSON files
- Handling missing fields safely
- Handling malformed and edge-case records
- Detecting and resolving duplicate records
- Preserving source URLs and provenance
- Verifying raw files remain strictly untouched
- Credit parsing and normalization
- False-positive detection in cross-referencing
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.app.data_processing.cleaner import (
    normalize_text,
    normalize_label,
    clean_string_list,
    sanitize_email,
    clean_course_code,
    parse_credits,
)
from backend.app.data_processing.validator import (
    ValidationReport,
    validate_units,
    validate_faculty,
    validate_courses,
    validate_publications,
    validate_research_areas,
    validate_programs,
)
from backend.app.data_processing.entities import (
    process_units,
    process_faculty,
    process_courses,
    process_publications,
    process_research_areas,
    build_curation_queue,
)
from backend.app.data_processing.pipeline import DataPipeline


class TestDataProcessing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project_root = Path(__file__).resolve().parent.parent
        cls.raw_dir = cls.project_root / "data" / "raw"
        cls.sample_dir = cls.project_root / "data" / "sample"

    def test_read_valid_json(self):
        """Verify reading valid JSON files works reliably."""
        pipeline = DataPipeline(raw_dir=self.raw_dir, processed_dir=self.sample_dir)
        units_data = pipeline.load_json("units.json")
        self.assertIn("units", units_data)
        self.assertEqual(len(units_data["units"]), 9)

        faculty_data = pipeline.load_json("faculty.json")
        self.assertIn("faculty", faculty_data)
        self.assertEqual(len(faculty_data["faculty"]), 181)

    def test_handle_missing_fields_safely(self):
        """Verify handling missing and optional fields without raising exceptions."""
        raw_faculty_with_missing = [
            {
                "id": "dr-missing-fields",
                "name": "Dr. Incomplete",
                "designation": None,
                "status": None,
                "units": [],
                "email": None,
                "qualifications": [],
                "research_interests": [],
                "profile_url": "https://giki.edu.pk/personnel/dr-missing-fields/",
            }
        ]
        cleaned, stats = process_faculty(raw_faculty_with_missing, valid_unit_ids={"fcse"})
        self.assertEqual(len(cleaned), 1)
        record = cleaned[0]
        self.assertEqual(record["id"], "dr-missing-fields")
        self.assertIn("email", record["missing_fields"])
        self.assertIn("qualifications", record["missing_fields"])
        self.assertIn("research_interests", record["missing_fields"])
        self.assertFalse(record["verified"])
        self.assertEqual(stats["missing_email"], 1)

    def test_handle_malformed_records(self):
        """Verify cleaning malformed strings, control characters, and unclosed punctuation."""
        # Unclosed trailing parenthesis
        bad_label = "Computational Fluid Dynamics)"
        cleaned_label = normalize_label(bad_label)
        self.assertEqual(cleaned_label, "Computational Fluid Dynamics")

        # Zero-width spaces and irregular whitespace
        dirty_text = "  Artificial \u200b  Intelligence\u00a0\t "
        cleaned_text = normalize_text(dirty_text)
        self.assertEqual(cleaned_text, "Artificial Intelligence")

        # Non-string or None inputs
        self.assertIsNone(normalize_text(None))
        self.assertIsNone(normalize_label(None))
        self.assertEqual(clean_string_list(None), [])
        self.assertIsNone(sanitize_email("invalid-email-address"))

    def test_detect_and_resolve_duplicates(self):
        """Verify deduplication of publications and resolution of research area ID collisions."""
        # 1. Intra-author duplicate citations
        raw_pubs = [
            {
                "faculty_id": "dr-author",
                "citation": "Paper Title, Journal of AI, 2024",
                "type": "journal",
                "year": 2024,
            },
            {
                "faculty_id": "dr-author",
                "citation": "Paper Title, Journal of AI, 2024",  # Duplicate
                "type": "journal",
                "year": 2024,
            },
            {
                "faculty_id": "dr-other",
                "citation": "Paper Title, Journal of AI, 2024",  # Different author -> kept
                "type": "journal",
                "year": 2024,
            },
        ]
        cleaned_pubs, stats = process_publications(raw_pubs)
        self.assertEqual(len(cleaned_pubs), 2)
        self.assertEqual(stats["duplicates_removed"], 1)

        # 2. Research area ID collision resolution
        raw_areas = [
            {
                "id": "computational-fluid-dynamics",
                "label": "Computational Fluid Dynamics",
                "aliases": [],
                "faculty_ids": ["fac-1", "fac-2"],
                "units": ["fme"],
            },
            {
                "id": "computational-fluid-dynamics",
                "label": "Computational Fluid Dynamics)",
                "aliases": [],
                "faculty_ids": ["fac-3"],
                "units": ["dcve"],
            },
        ]
        cleaned_areas, area_stats = process_research_areas(raw_areas)
        self.assertEqual(len(cleaned_areas), 1)
        self.assertEqual(area_stats["id_collisions_resolved"], 1)
        self.assertEqual(cleaned_areas[0]["label"], "Computational Fluid Dynamics")
        self.assertEqual(cleaned_areas[0]["faculty_count"], 3)
        self.assertIn("fme", cleaned_areas[0]["units"])
        self.assertIn("dcve", cleaned_areas[0]["units"])

    def test_preserve_source_urls_and_provenance(self):
        """Verify provenance and source URLs are strictly preserved across processing."""
        raw_faculty = [
            {
                "id": "dr-test",
                "name": "Dr. Test User",
                "designation": "Associate Professor",
                "status": "active",
                "units": ["fcse"],
                "email": "test@giki.edu.pk",
                "qualifications": ["PhD CS"],
                "research_interests": ["AI"],
                "profile_url": "https://giki.edu.pk/personnel/dr-test/",
                "listing_urls": ["https://giki.edu.pk/fcse/faculty-profiles/"],
                "provenance": {
                    "sources": ["https://giki.edu.pk/personnel/dr-test/"],
                    "scraped_at": "2026-11-10T16:37:44Z",
                },
            }
        ]
        cleaned, _ = process_faculty(raw_faculty, valid_unit_ids={"fcse"})
        item = cleaned[0]
        self.assertEqual(item["profile_url"], "https://giki.edu.pk/personnel/dr-test/")
        self.assertIn("https://giki.edu.pk/fcse/faculty-profiles/", item["listing_urls"])
        self.assertEqual(item["provenance"]["sources"], ["https://giki.edu.pk/personnel/dr-test/"])
        self.assertEqual(item["provenance"]["scraped_at"], "2026-11-10T16:37:44Z")

    def test_raw_files_remain_untouched(self):
        """Verify pipeline execution does not modify raw files."""
        raw_files = list(self.raw_dir.glob("*.json"))
        self.assertGreater(len(raw_files), 0)
        mtimes_before = {f.name: f.stat().st_mtime for f in raw_files}

        with tempfile.TemporaryDirectory() as temp_out:
            pipeline = DataPipeline(raw_dir=self.raw_dir, processed_dir=Path(temp_out))
            summary = pipeline.run()
            self.assertIn("counts", summary)

        mtimes_after = {f.name: f.stat().st_mtime for f in raw_files}
        for fname in mtimes_before:
            self.assertEqual(
                mtimes_before[fname],
                mtimes_after[fname],
                f"Raw file {fname} was modified during pipeline run!",
            )

    def test_credits_parsing_variations(self):
        """Verify credits parsing handles hyphenated, space-separated, and numeric formats."""
        s1, h1 = parse_credits("3-0-3")
        self.assertEqual(s1, "3-0-3")
        self.assertEqual(h1, 3)

        s2, h2 = parse_credits("3 0 3")
        self.assertEqual(s2, "3-0-3")
        self.assertEqual(h2, 3)

        s3, h3 = parse_credits("0-3-1")
        self.assertEqual(s3, "0-3-1")
        self.assertEqual(h3, 1)

        s4, h4 = parse_credits(4)
        self.assertEqual(s4, "4")
        self.assertEqual(h4, 4)

        s5, h5 = parse_credits(None)
        self.assertIsNone(s5)
        self.assertIsNone(h5)

    def test_prospectus_false_positive_detection(self):
        """Verify detection of false-positive prospectus matches like Naveed vs Naeem."""
        faculty_rec = [
            {
                "id": "muhammad-naveed",
                "name": "Muhammad Naveed",
                "designation": "Lab Engineer",
                "units": ["fcse"],
                "qualifications": ["MS Computer Science"],
                "research_interests": ["Networks"],
                "profile_url": "https://giki.edu.pk/personnel/muhammad-naveed/",
                "prospectus_2025": {
                    "listed_as": "Mr. Muhammad Naeem",
                    "detail": "MS Computer Science",
                    "section": "Lab Engineer",
                    "match_score": 0.90,
                },
            }
        ]
        cleaned, stats = process_faculty(faculty_rec, valid_unit_ids={"fcse"})
        self.assertEqual(stats["prospectus_flags"], 1)
        self.assertTrue(cleaned[0]["prospectus_2025"]["review_needed"])

    def test_unmatched_instructors_preserved(self):
        """Verify that all 66 unmatched CourseHub instructors are preserved without truncation."""
        with open(self.project_root / "data" / "processed" / "coursehub_instructor_links.json", "r", encoding="utf-8") as f:
            links = json.load(f)["links"]
        unmatched = [l for l in links if not l.get("faculty_id")]
        self.assertEqual(len(links), 190)
        self.assertEqual(len(unmatched), 66)

    def test_dual_appointment_preserved(self):
        """Verify faculty with dual affiliations (Prof. Dr. Nisar Ahmed) retain both units."""
        with open(self.project_root / "data" / "processed" / "faculty.json", "r", encoding="utf-8") as f:
            fac = json.load(f)["faculty"]
        nisar = next((f for f in fac if f["id"] == "prof-dr-nisar-ahmed"), None)
        self.assertIsNotNone(nisar)
        self.assertEqual(sorted(nisar["units"]), ["fbs", "fee"])

    def test_no_silent_record_discarding(self):
        """Verify that no records were dropped between raw and processed datasets."""
        raw_counts = {
            "units.json": ("units", 9),
            "faculty.json": ("faculty", 181),
            "courses.json": ("courses", 647),
            "programs.json": ("programs", 15),
            "other_personnel.json": ("people", 20),
            "coursehub_instructor_links.json": ("links", 190),
        }
        for fname, (key, expected_count) in raw_counts.items():
            with open(self.raw_dir / fname, "r", encoding="utf-8") as rf:
                r_len = len(json.load(rf)[key])
            with open(self.project_root / "data" / "processed" / fname, "r", encoding="utf-8") as pf:
                p_len = len(json.load(pf)[key])
            self.assertEqual(r_len, expected_count)
            self.assertEqual(p_len, expected_count)

    def test_pydantic_domain_model_validation(self):
        """Verify that processed data records validate against Pydantic domain models."""
        from backend.app.schemas.domain import (
            AcademicUnit, FacultyMember, Course, Program,
            ResearchArea, Publication, OtherPersonnel, CourseHubInstructorLink
        )
        proc_dir = self.project_root / "data" / "processed"
        with open(proc_dir / "units.json", "r", encoding="utf-8") as f:
            for u in json.load(f)["units"]:
                AcademicUnit.model_validate(u)

        with open(proc_dir / "faculty.json", "r", encoding="utf-8") as f:
            for fac in json.load(f)["faculty"][:20]:  # sample check
                FacultyMember.model_validate(fac)

        with open(proc_dir / "courses.json", "r", encoding="utf-8") as f:
            for c in json.load(f)["courses"][:20]:
                Course.model_validate(c)


if __name__ == "__main__":
    unittest.main()
