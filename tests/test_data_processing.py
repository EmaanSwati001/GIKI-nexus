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
from collections import Counter
from pathlib import Path

from backend.app.data_processing.cleaner import (
    normalize_text,
    normalize_label,
    clean_string_list,
    sanitize_email,
    clean_course_code,
    parse_credits,
    map_course_prefix_to_unit,
    normalize_instructor_name,
    parse_faculty_designation_components,
    COURSE_PREFIX_TO_UNIT_MAP,
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

    def test_prefix_based_course_mapping(self):
        """Verify prefix mapping rules match correctly without unsafe substrings."""
        valid_units = {"fcse", "fee", "dcve", "dche", "dmse", "fme", "mgs", "fbs"}
        
        # Test FCSE prefixes
        for p in ["AI101", "CS201", "CE301", "DS101", "CY201", "CYS301", "SE401"]:
            unit, matched = map_course_prefix_to_unit(p, valid_units)
            self.assertEqual(unit, "fcse", f"Failed for {p}")

        # Test other faculties
        self.assertEqual(map_course_prefix_to_unit("EE101", valid_units)[0], "fee")
        self.assertEqual(map_course_prefix_to_unit("CV201", valid_units)[0], "dcve")
        self.assertEqual(map_course_prefix_to_unit("CH301", valid_units)[0], "dche")
        self.assertEqual(map_course_prefix_to_unit("MM401", valid_units)[0], "dmse")
        self.assertEqual(map_course_prefix_to_unit("ME101", valid_units)[0], "fme")
        self.assertEqual(map_course_prefix_to_unit("MS101", valid_units)[0], "mgs")
        self.assertEqual(map_course_prefix_to_unit("MT101", valid_units)[0], "fbs")
        self.assertEqual(map_course_prefix_to_unit("ES101", valid_units)[0], "fbs")
        self.assertEqual(map_course_prefix_to_unit("HM101", valid_units)[0], "fbs")
        self.assertEqual(map_course_prefix_to_unit("HMXYZ", valid_units)[0], "fbs")

        # Test unknown prefix returns None
        self.assertIsNone(map_course_prefix_to_unit("UNKNOWN999", valid_units)[0])

        # Test anchored prefix: ensure prefix in middle is NOT matched
        self.assertIsNone(map_course_prefix_to_unit("XCS101", valid_units)[0])

        # Check full courses dataset in data/processed
        with open(self.project_root / "data" / "processed" / "courses.json", "r", encoding="utf-8") as f:
            courses = json.load(f)["courses"]
        
        # Check all 647 courses have units and valid mapping source
        for c in courses:
            self.assertIsNotNone(c["unit"], f"Course {c['code']} has null unit")
            self.assertIn(c["unit_mapping_source"], ["prospectus_verified", "prefix_based_mapping"])
            # Ensure offered_in is preserved as list
            self.assertIsInstance(c["offered_in"], list)

        prefix_mapped = [c for c in courses if c["unit_mapping_source"] == "prefix_based_mapping"]
        self.assertEqual(len(prefix_mapped), 111)

    def test_unresolved_prerequisites_tracking(self):
        """Verify tracking of the 5 missing prerequisite codes without inventing data."""
        with open(self.project_root / "data" / "processed" / "courses.json", "r", encoding="utf-8") as f:
            courses = json.load(f)["courses"]

        expected_missing = {"AI321", "MM102", "MS290", "ME101", "ME261"}
        courses_with_unresolved = [c for c in courses if c["unresolved_prerequisites"]]
        self.assertEqual(len(courses_with_unresolved), 6)

        observed_missing = set()
        for c in courses_with_unresolved:
            for p in c["unresolved_prerequisites"]:
                observed_missing.add(p)
                self.assertEqual(c["prerequisite_statuses"][p], "unresolved")

        self.assertEqual(observed_missing, expected_missing)

    def test_coursehub_instructor_statuses(self):
        """Verify 4-status CourseHub instructor matching and preservation."""
        with open(self.project_root / "data" / "processed" / "coursehub_instructor_links.json", "r", encoding="utf-8") as f:
            links = json.load(f)["links"]

        status_counts = Counter(l["match_status"] for l in links)
        self.assertEqual(status_counts["matched"], 124)
        self.assertEqual(status_counts["suggested"], 6)
        self.assertEqual(status_counts["needs_review"], 17)
        self.assertEqual(status_counts["unmatched"], 43)

        # Check the 6 suggested candidates have suggested_faculty_id and null faculty_id
        suggested = [l for l in links if l["match_status"] == "suggested"]
        self.assertEqual(len(suggested), 6)
        for s in suggested:
            self.assertIsNone(s["faculty_id"], "Suggested match must keep faculty_id null")
            self.assertIsNotNone(s["suggested_faculty_id"], "Suggested match must have suggested_faculty_id")

        # Check name normalization
        self.assertEqual(normalize_instructor_name("Dr.  Taqi A. Cheema"), "Dr Taqi A. Cheema")
        self.assertEqual(normalize_instructor_name("Engr.  Hamza"), "Engr Hamza")

    def test_faculty_designation_components(self):
        """Verify designation parsing preserves listing and profile designations."""
        # Case 1: Discrepancy between listing and profile
        comp = parse_faculty_designation_components(
            listing_desig="Assistant Professor",
            profile_desig="Associate Professor & HoD",
            status="active"
        )
        self.assertTrue(comp["designation_discrepancy"])
        self.assertEqual(comp["preferred_designation"], "Associate Professor & HoD")
        self.assertEqual(comp["academic_rank"], "Associate Professor")
        self.assertEqual(comp["administrative_role"], "HoD")

        # Case 2: In processed faculty dataset, verify 31 discrepancies detected
        with open(self.project_root / "data" / "processed" / "faculty.json", "r", encoding="utf-8") as f:
            faculty = json.load(f)["faculty"]

        discrepancies = [f for f in faculty if f["designation_discrepancy"]]
        self.assertEqual(len(discrepancies), 31)

    def test_incomplete_faculty_profiles_preserved(self):
        """Verify incomplete profiles are preserved with null/empty values without errors."""
        with open(self.project_root / "data" / "processed" / "faculty.json", "r", encoding="utf-8") as f:
            faculty = json.load(f)["faculty"]
        with open(self.project_root / "data" / "processed" / "other_personnel.json", "r", encoding="utf-8") as f:
            other = json.load(f)["people"]

        # Check empty profile in faculty.json: dr-asif-khan-assistant-professor
        asif = next((f for f in faculty if f["id"] == "dr-asif-khan-assistant-professor"), None)
        self.assertIsNotNone(asif)
        self.assertIsNone(asif["email"])
        self.assertEqual(asif["qualifications"], [])
        self.assertEqual(asif["research_interests"], [])
        self.assertFalse(asif["verified"])
        self.assertIn("email", asif["missing_fields"])

        # Check isolated empty personnel in other_personnel.json: dr-nasir-javed-assistant-professor-fes
        nasir_fes = next((o for o in other if o["id"] == "dr-nasir-javed-assistant-professor-fes"), None)
        self.assertIsNotNone(nasir_fes)
        self.assertIsNone(nasir_fes["email"])
        self.assertIsNotNone(nasir_fes["note"])

        # Check active Dr. Nasir Javed exists in faculty.json with complete credentials
        nasir_fac = next((f for f in faculty if f["id"] == "dr-nasir-javed"), None)
        self.assertIsNotNone(nasir_fac)
        self.assertTrue(nasir_fac["verified"])

    def test_curation_queue_categorization(self):
        """Verify curation queue structure, categories, and resolution statuses."""
        from backend.app.schemas.domain import CurationQueueItem

        with open(self.project_root / "data" / "processed" / "needs_review.json", "r", encoding="utf-8") as f:
            records = json.load(f)["records"]

        self.assertEqual(len(records), 378)
        statuses = Counter(r["resolution_status"] for r in records)
        self.assertEqual(statuses["resolved"], 142)
        self.assertEqual(statuses["needs_review"], 63)
        self.assertEqual(statuses["informational"], 173)

        # Validate every record conforms to CurationQueueItem schema
        for r in records:
            item = CurationQueueItem.model_validate(r)
            self.assertIn(item.resolution_status.value, ["resolved", "needs_review", "informational"])
            self.assertTrue(len(item.reasons) > 0)



if __name__ == "__main__":
    unittest.main()
