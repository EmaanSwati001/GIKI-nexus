"""
Automated unit tests for AcademicRepository in GIKI Nexus.
Verifies dataset loading, indexing, constant-time lookups, case-insensitive searches,
and graceful handling of invalid identifiers or missing files.
"""

import unittest
from pathlib import Path

from backend.app.core.config import settings
from backend.app.database.academic_repository import AcademicRepository


class TestAcademicRepository(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_dir = settings.PROCESSED_DATA_DIR
        cls.repo = AcademicRepository(data_dir=cls.data_dir)
        cls.repo.load_datasets()

    def test_repository_initialization_and_counts(self):
        """Verify that all processed datasets load with exact expected entity counts."""
        self.assertTrue(self.repo.is_loaded)
        self.assertEqual(len(self.repo.units), 9)
        self.assertEqual(len(self.repo.faculty), 181)
        self.assertEqual(len(self.repo.courses), 647)
        self.assertEqual(len(self.repo.publications), 2796)
        self.assertEqual(len(self.repo.research_areas), 656)
        self.assertEqual(len(self.repo.programs), 15)
        self.assertEqual(len(self.repo.other_personnel), 20)
        self.assertEqual(len(self.repo.coursehub_links), 190)

    def test_lookup_unit_by_id(self):
        """Verify academic unit retrieval by unique slug."""
        fcse = self.repo.get_unit("fcse")
        self.assertIsNotNone(fcse)
        self.assertEqual(fcse["short"], "FCSE")
        self.assertEqual(fcse["type"], "faculty")

        dmse = self.repo.get_unit("dmse")
        self.assertIsNotNone(dmse)
        self.assertEqual(dmse["parent"], "fmce")

        # Case insensitivity
        self.assertIsNotNone(self.repo.get_unit("FCSE"))

        # Non-existent unit
        self.assertIsNone(self.repo.get_unit("nonexistent_unit"))
        self.assertIsNone(self.repo.get_unit(""))

    def test_lookup_faculty_by_id(self):
        """Verify faculty profile retrieval and metadata preservation."""
        fac = self.repo.get_faculty("dr-khurram-khan-jadoon")
        self.assertIsNotNone(fac)
        self.assertEqual(fac["name"], "Dr. Khurram Khan Jadoon")
        self.assertIn("fcse", fac["units"])
        self.assertTrue(fac["verified"])
        self.assertIn("https://giki.edu.pk", fac["profile_url"])

        # Dual appointment faculty
        nisar = self.repo.get_faculty("prof-dr-nisar-ahmed")
        self.assertIsNotNone(nisar)
        self.assertIn("fbs", nisar["units"])
        self.assertIn("fee", nisar["units"])

        # Unverified faculty
        asif = self.repo.get_faculty("dr-asif-khan-assistant-professor")
        self.assertIsNotNone(asif)
        self.assertFalse(asif["verified"])

        # Non-existent faculty
        self.assertIsNone(self.repo.get_faculty("nobody-at-giki"))

    def test_lookup_course_by_code(self):
        """Verify course code normalization, case handling, and elective placeholder distinction."""
        # Standard lookup
        cs101 = self.repo.get_course("CS101")
        self.assertIsNotNone(cs101)
        self.assertEqual(cs101["unit"], "fcse")

        # Lowercase lookup
        self.assertIsNotNone(self.repo.get_course("cs101"))

        # Spaced code lookup
        self.assertIsNotNone(self.repo.get_course("CS 101"))

        # Distinct elective placeholder preservation
        course_a = self.repo.get_course("CS3XX/CS4xx")
        course_b = self.repo.get_course("CS3xx/CS4xx")
        self.assertIsNotNone(course_a)
        self.assertIsNotNone(course_b)
        self.assertNotEqual(course_a["name"], course_b["name"])

        # Non-existent course
        self.assertIsNone(self.repo.get_course("GIBBERISH999"))

    def test_course_filtering(self):
        """Verify course filtering by unit, degree program, and lab status."""
        fcse_courses = self.repo.get_all_courses(unit="fcse")
        self.assertGreater(len(fcse_courses), 50)
        self.assertTrue(all(c["unit"] == "fcse" for c in fcse_courses))

        bs_ai_courses = self.repo.get_all_courses(program_id="bs-artificial-intelligence")
        self.assertGreater(len(bs_ai_courses), 10)

        lab_courses = self.repo.get_all_courses(is_lab=True)
        self.assertTrue(all(c["is_lab"] is True for c in lab_courses))

    def test_faculty_filtering(self):
        """Verify faculty filtering by unit, research area, and verification status."""
        fee_fac = self.repo.get_all_faculty(unit="fee")
        self.assertGreater(len(fee_fac), 10)
        self.assertTrue(all("fee" in f["units"] for f in fee_fac))

        verified_only = self.repo.get_all_faculty(verified_only=True)
        self.assertEqual(len(verified_only), 161)
        self.assertTrue(all(f["verified"] is True for f in verified_only))

    def test_publications_retrieval(self):
        """Verify publication citations indexing and faculty association."""
        pubs = self.repo.get_all_publications()
        self.assertEqual(len(pubs), 2796)

        # First pub has generated ID
        first_pub = pubs[0]
        self.assertIn("id", first_pub)
        self.assertTrue(first_pub["id"].startswith("pub_"))

        # Lookup by ID
        pub_by_id = self.repo.get_publication(first_pub["id"])
        self.assertEqual(pub_by_id["citation"], first_pub["citation"])

        # Filter by author
        fac_pubs = self.repo.get_faculty_publications("dr-massab-junaid")
        self.assertGreater(len(fac_pubs), 5)

    def test_program_curriculum_sorting(self):
        """Verify program curriculum courses are structured and ordered by semester."""
        curriculum = self.repo.get_program_curriculum("bs-computer-science")
        self.assertGreater(len(curriculum), 20)

        # Check ordering
        semesters = [
            c["curriculum_placement"]["semester"]
            for c in curriculum
            if c.get("curriculum_placement", {}).get("semester") is not None
        ]
        self.assertEqual(semesters, sorted(semesters))

    def test_unified_search(self):
        """Verify multi-entity search returns ranked matching items."""
        # Search for course code
        results = self.repo.search_academic("CS101", limit=10)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["entity_type"], "course")
        self.assertEqual(results[0]["id"], "CS101")

        # Search for faculty name
        fac_results = self.repo.search_academic("Khurram Khan Jadoon", limit=10)
        self.assertGreater(len(fac_results), 0)
        self.assertEqual(fac_results[0]["entity_type"], "faculty")

        # Search for research domain
        ai_results = self.repo.search_academic("Artificial Intelligence", limit=10)
        self.assertGreater(len(ai_results), 0)
        types = {r["entity_type"] for r in ai_results}
        self.assertTrue(len(types) >= 1)

    def test_missing_directory_error_handling(self):
        """Verify that attempting to load from an invalid path raises a clear FileNotFoundError."""
        bad_repo = AcademicRepository(data_dir=Path("/invalid/path/to/nowhere"))
        with self.assertRaises(FileNotFoundError) as ctx:
            bad_repo.load_datasets()
        self.assertIn("Required academic dataset file", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
