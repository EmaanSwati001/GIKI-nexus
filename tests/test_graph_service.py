"""
Automated unit tests for AcademicGraphService in GIKI Nexus.
Verifies knowledge graph topology, node and edge counts, multi-relational queries,
dual faculty appointments, unresolved prerequisite tracking, and subgraph extraction.
"""

import unittest

from backend.app.core.config import settings
from backend.app.database.academic_repository import AcademicRepository
from backend.app.graph.service import AcademicGraphService


class TestAcademicGraphService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = AcademicRepository(data_dir=settings.PROCESSED_DATA_DIR)
        cls.repo.load_datasets()
        cls.graph_service = AcademicGraphService()
        cls.graph_service.build_graph(cls.repo)
        cls.stats = cls.graph_service.get_graph_stats()

    def test_graph_node_counts(self):
        """Verify graph node counts match processed datasets exactly."""
        node_counts = self.stats["node_counts"]
        self.assertEqual(node_counts["AcademicUnit"], 9)
        self.assertEqual(node_counts["FacultyMember"], 181)
        self.assertEqual(node_counts["Course"], 647)
        self.assertEqual(node_counts["Publication"], 2796)
        self.assertEqual(node_counts["ResearchArea"], 656)
        self.assertEqual(node_counts["Program"], 15)
        self.assertEqual(node_counts["CourseHubInstructorLink"], 190)
        self.assertEqual(node_counts["OtherPersonnel"], 20)
        self.assertEqual(self.stats["total_nodes"], 4514)

    def test_graph_relationship_counts(self):
        """Verify knowledge graph relationship counts."""
        rel_counts = self.stats["relationship_counts"]
        self.assertEqual(rel_counts["UNIT_SUB_DEPARTMENT_OF"], 2)
        self.assertEqual(rel_counts["MEMBER_BELONGS_TO_UNIT"], 181)
        self.assertEqual(rel_counts["MEMBER_HAS_RESEARCH_AREA"], 766)
        self.assertEqual(rel_counts["MEMBER_AUTHORED_PUBLICATION"], 2796)
        self.assertEqual(rel_counts["PROGRAM_OFFERED_BY"], 15)
        self.assertEqual(rel_counts["PROGRAM_CONTAINS_COURSE"], 869)
        self.assertEqual(rel_counts["COURSE_BELONGS_TO_UNIT"], 647)
        self.assertEqual(rel_counts["COURSE_HAS_PREREQUISITE"], 306)
        self.assertEqual(rel_counts["INSTRUCTOR_MAPS_TO_FACULTY"], 124)
        self.assertEqual(self.stats["total_edges"], 5706)

    def test_sub_department_relationships(self):
        """Verify parent-child unit relationships (DMSE and DChE under FMCE)."""
        dmse_node = self.graph_service.make_node_id("unit", "dmse")
        fmce_node = self.graph_service.make_node_id("unit", "fmce")
        self.assertTrue(self.graph_service.graph.has_edge(dmse_node, fmce_node))

        dche_node = self.graph_service.make_node_id("unit", "dche")
        self.assertTrue(self.graph_service.graph.has_edge(dche_node, fmce_node))

    def test_dual_faculty_appointment(self):
        """Verify faculty dual appointments have multiple MEMBER_BELONGS_TO_UNIT edges."""
        nisar_rels = self.graph_service.get_faculty_relationships("prof-dr-nisar-ahmed")
        self.assertTrue(nisar_rels["found"])
        unit_ids = [u["id"] for u in nisar_rels["units"]]
        self.assertEqual(len(unit_ids), 2)
        self.assertIn("fbs", unit_ids)
        self.assertIn("fee", unit_ids)

    def test_course_unit_mapping_source_distinction(self):
        """Verify distinction between prospectus_verified and prefix_based_mapping on edges."""
        # CS101: Prospectus verified
        cs101_rels = self.graph_service.get_course_relationships("CS101")
        self.assertEqual(cs101_rels["unit"]["source_rule"], "prospectus_verified")

        # AI102: Prefix-based mapping
        ai102_rels = self.graph_service.get_course_relationships("AI102")
        self.assertEqual(ai102_rels["unit"]["source_rule"], "prefix_based_mapping")

    def test_unresolved_prerequisites_handling(self):
        """Verify unresolved prerequisites are tracked without creating fake nodes."""
        prereqs = self.graph_service.get_course_prerequisites("AI331")
        self.assertTrue(prereqs["found"])
        self.assertIn("AI321", prereqs["unresolved_prerequisites"])

        # Crucial constraint: fake course node for AI321 must NOT exist
        fake_node = self.graph_service.make_node_id("course", "AI321")
        self.assertFalse(self.graph_service.graph.has_node(fake_node))

        # Direct prereqs report should list AI321 as unresolved
        direct_statuses = {p["code"]: p["status"] for p in prereqs["direct_prerequisites"]}
        self.assertEqual(direct_statuses.get("AI321"), "unresolved")

    def test_resolved_prerequisite_chain(self):
        """Verify multi-hop prerequisite resolution."""
        prereqs = self.graph_service.get_course_prerequisites("CE222/CS223")
        self.assertTrue(prereqs["found"])
        direct_codes = {p["code"] for p in prereqs["direct_prerequisites"]}
        self.assertIn("CE221", direct_codes)
        self.assertIn("CS221", direct_codes)

    def test_course_relationships(self):
        """Verify program placement and dependent courses."""
        rels = self.graph_service.get_course_relationships("CS101")
        self.assertTrue(rels["found"])
        self.assertEqual(rels["unit"]["short"], "FCSE")
        self.assertGreater(len(rels["programs"]), 0)

        # Non-existent course
        missing = self.graph_service.get_course_relationships("GIBBERISH_XYZ")
        self.assertFalse(missing["found"])

    def test_faculty_research_and_publications(self):
        """Verify retrieval of research domains and publication citations."""
        ra_faculty = self.graph_service.get_research_area_faculty("artificial-intelligence")
        self.assertGreater(len(ra_faculty), 0)

        fac_areas = self.graph_service.get_faculty_research_areas("dr-khurram-khan-jadoon")
        self.assertIsInstance(fac_areas, list)

    def test_entity_subgraph_extraction(self):
        """Verify ego-subgraph extraction for visualizers."""
        subgraph = self.graph_service.get_entity_subgraph("course", "CS101", depth=1)
        self.assertGreater(len(subgraph["nodes"]), 0)
        self.assertGreater(len(subgraph["edges"]), 0)
        center = next((n for n in subgraph["nodes"] if n["is_center"]), None)
        self.assertIsNotNone(center)
        self.assertEqual(center["id"], "course:CS101")

    def test_prerequisite_exact_resolution_and_unresolved_isolation(self):
        """Verify prerequisite edge counts (306 verified) and strict isolation of 5 unresolved codes."""
        prereq_edges = [
            (u, v, d) for u, v, _, d in self.graph_service.graph.edges(data=True, keys=True)
            if d.get("relationship") == "COURSE_HAS_PREREQUISITE"
        ]
        self.assertEqual(len(prereq_edges), 306)

        # Confirm all edge endpoints exist as real Course nodes
        for u, v, d in prereq_edges:
            self.assertTrue(self.graph_service.graph.has_node(u))
            self.assertTrue(self.graph_service.graph.has_node(v))
            self.assertEqual(self.graph_service.graph.nodes[u]["entity_type"], "Course")
            self.assertEqual(self.graph_service.graph.nodes[v]["entity_type"], "Course")
            self.assertEqual(d.get("status"), "resolved")

        # Verify none of the 5 unresolved codes are in the graph as nodes or edges
        unresolved_codes = {"AI321", "MM102", "MS290", "ME101", "ME261"}
        targets = {v for u, v, _ in prereq_edges}
        sources = {u for u, v, _ in prereq_edges}
        for code in unresolved_codes:
            node = self.graph_service.make_node_id("course", code)
            self.assertFalse(self.graph_service.graph.has_node(node))
            self.assertNotIn(node, targets)
            self.assertNotIn(node, sources)

        # Verify multi-hop traversal with mixed resolved & unresolved prerequisites
        ee485 = self.graph_service.get_course_prerequisites("EE485")
        self.assertIn("MM102", ee485["unresolved_prerequisites"])
        self.assertNotIn("MM102", ee485["prerequisite_chain"])
        self.assertIn("EE371", ee485["prerequisite_chain"])
        self.assertIn("PH101", ee485["prerequisite_chain"])

        ee486 = self.graph_service.get_course_prerequisites("EE486")
        self.assertIn("MS290", ee486["unresolved_prerequisites"])
        self.assertNotIn("MS290", ee486["prerequisite_chain"])
        self.assertIn("EE312", ee486["prerequisite_chain"])
        self.assertIn("EE212", ee486["prerequisite_chain"])

    def test_program_contains_course_exact_offerings(self):
        """Verify 869 total program-course offerings for 321 distinct courses across 15 programs."""
        prog_edges = [
            (u, v, d) for u, v, _, d in self.graph_service.graph.edges(data=True, keys=True)
            if d.get("relationship") == "PROGRAM_CONTAINS_COURSE"
        ]
        self.assertEqual(len(prog_edges), 869)

        # Verify exactly 321 distinct courses are offered across programs
        distinct_courses = {v for u, v, _ in prog_edges}
        self.assertEqual(len(distinct_courses), 321)

        # Verify edge properties (year, semester, catalog name) are preserved
        for u, v, d in prog_edges:
            self.assertIsNotNone(d.get("year"))
            self.assertIsNotNone(d.get("semester"))
            self.assertIn(d.get("year"), [1, 2, 3, 4])
            self.assertTrue(1 <= d.get("semester") <= 8)
            self.assertIsNotNone(d.get("name_in_catalog"))

    def test_faculty_unit_affiliations_exact_breakdown(self):
        """Verify mathematical consistency: 179 single + 1 unassigned (0) + 1 dual (2) = 181 affiliations."""
        affil_edges = [
            (u, v, d) for u, v, _, d in self.graph_service.graph.edges(data=True, keys=True)
            if d.get("relationship") == "MEMBER_BELONGS_TO_UNIT"
        ]
        self.assertEqual(len(affil_edges), 181)

        # Faculty node counts
        faculty_nodes = [
            n for n, d in self.graph_service.graph.nodes(data=True)
            if d.get("entity_type") == "FacultyMember"
        ]
        self.assertEqual(len(faculty_nodes), 181)

        # Unassigned member has 0 unit edges
        asif_node = self.graph_service.make_node_id("faculty", "dr-asif-khan-assistant-professor")
        asif_unit_edges = [
            v for _, v, d in self.graph_service.graph.out_edges(asif_node, data=True)
            if d.get("relationship") == "MEMBER_BELONGS_TO_UNIT"
        ]
        self.assertEqual(len(asif_unit_edges), 0)

        # Dual appointment member has 2 unit edges
        nisar_node = self.graph_service.make_node_id("faculty", "prof-dr-nisar-ahmed")
        nisar_unit_edges = [
            v for _, v, d in self.graph_service.graph.out_edges(nisar_node, data=True)
            if d.get("relationship") == "MEMBER_BELONGS_TO_UNIT"
        ]
        self.assertEqual(len(nisar_unit_edges), 2)
        target_units = {self.graph_service.graph.nodes[v]["id"] for v in nisar_unit_edges}
        self.assertEqual(target_units, {"fbs", "fee"})

    def test_non_matched_instructors_have_no_edges(self):
        """Verify only the 124 verified matches have edges; 66 unverified links have 0 edges."""
        match_edges = [
            (u, v, d) for u, v, _, d in self.graph_service.graph.edges(data=True, keys=True)
            if d.get("relationship") == "INSTRUCTOR_MAPS_TO_FACULTY"
        ]
        self.assertEqual(len(match_edges), 124)
        for _, _, d in match_edges:
            self.assertEqual(d.get("match_status"), "matched")

        # Check all non-matched links in repo
        for link in self.repo.coursehub_links:
            if link.get("match_status") != "matched":
                ch_name = link["coursehub_name"]
                ch_fac = link.get("coursehub_faculty") or ""
                ch_key = f"{ch_name}::{ch_fac}" if ch_fac else ch_name
                node = self.graph_service.make_node_id("coursehub_link", ch_key)
                self.assertEqual(self.graph_service.graph.out_degree(node), 0)

    def test_member_teaches_course_absent(self):
        """Verify MEMBER_TEACHES_COURSE relationship is completely absent from the graph."""
        all_relationships = {
            d.get("relationship")
            for _, _, _, d in self.graph_service.graph.edges(data=True, keys=True)
        }
        self.assertNotIn("MEMBER_TEACHES_COURSE", all_relationships)


if __name__ == "__main__":
    unittest.main()
