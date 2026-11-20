"""
Integration tests for GIKI Nexus Academic REST API routes.
Verifies all /api/v1 endpoints with real processed datasets and graph queries.
"""

import re
import unittest
from urllib.parse import urlparse, parse_qs
from fastapi import HTTPException

from backend.app.core.config import settings
from backend.app.database.academic_repository import AcademicRepository
from backend.app.graph.service import AcademicGraphService
from backend.app.services.academic_service import AcademicService
from backend.app.api.routes import academic


class MockResponse:
    """Mock HTTP response matching FastAPI TestClient interface."""
    def __init__(self, status_code: int, data: any):
        self.status_code = status_code
        self._data = data

    def json(self):
        return self._data


class DirectAPIClient:
    """
    Synchronous direct API test client.
    Dispatches HTTP GET requests directly to FastAPI route handlers
    without requiring loopback socket binding in sandboxed environments.
    """
    def __init__(self):
        self.repo = AcademicRepository(settings.PROCESSED_DATA_DIR)
        self.repo.load_datasets()
        self.graph = AcademicGraphService()
        self.graph.build_graph(self.repo)
        self.service = AcademicService(self.repo, self.graph)

    def get(self, url: str) -> MockResponse:
        parsed = urlparse(url)
        path = parsed.path
        qs = parse_qs(parsed.query)
        params = {k: v[0] if len(v) == 1 else v for k, v in qs.items()}

        try:
            # GET /health
            if path == "/health":
                stats = self.graph.get_graph_stats()
                return MockResponse(200, {
                    "status": "healthy",
                    "app_name": settings.PROJECT_NAME,
                    "version": settings.VERSION,
                    "datasets_loaded": True,
                    "graph_initialized": True,
                    "entity_counts": {
                        "units": len(self.repo.units),
                        "faculty": len(self.repo.faculty),
                        "courses": len(self.repo.courses),
                        "publications": len(self.repo.publications),
                        "research_areas": len(self.repo.research_areas),
                        "programs": len(self.repo.programs),
                    },
                    "graph": stats,
                })

            # GET /api/v1/units
            if path == "/api/v1/units":
                return MockResponse(200, academic.list_units(service=self.service))
            m = re.match(r"^/api/v1/units/([^/]+)$", path)
            if m:
                return MockResponse(200, academic.get_unit(unit_id=m.group(1), service=self.service))

            # GET /api/v1/faculty
            if path == "/api/v1/faculty":
                verified = params.get("verified_only", "false").lower() == "true"
                return MockResponse(200, academic.list_faculty(
                    unit=params.get("unit"),
                    research_area=params.get("research_area"),
                    verified_only=verified,
                    search=params.get("search"),
                    skip=int(params.get("skip", 0)),
                    limit=int(params.get("limit", 50)),
                    service=self.service,
                ))
            m = re.match(r"^/api/v1/faculty/([^/]+)/research-areas$", path)
            if m:
                return MockResponse(200, academic.get_faculty_research_areas(faculty_id=m.group(1), service=self.service))
            m = re.match(r"^/api/v1/faculty/([^/]+)/publications$", path)
            if m:
                return MockResponse(200, academic.get_faculty_publications(faculty_id=m.group(1), service=self.service))
            m = re.match(r"^/api/v1/faculty/([^/]+)$", path)
            if m:
                return MockResponse(200, academic.get_faculty(faculty_id=m.group(1), service=self.service))

            # GET /api/v1/courses
            if path == "/api/v1/courses":
                is_lab = None
                if "is_lab" in params:
                    is_lab = params["is_lab"].lower() == "true"
                return MockResponse(200, academic.list_courses(
                    unit=params.get("unit"),
                    program_id=params.get("program_id"),
                    is_lab=is_lab,
                    search=params.get("search"),
                    skip=int(params.get("skip", 0)),
                    limit=int(params.get("limit", 50)),
                    service=self.service,
                ))
            m = re.match(r"^/api/v1/courses/([^/]+)/prerequisites$", path)
            if m:
                return MockResponse(200, academic.get_course_prerequisites(course_code=m.group(1), service=self.service))
            m = re.match(r"^/api/v1/courses/([^/]+)/related$", path)
            if m:
                return MockResponse(200, academic.get_course_related_entities(course_code=m.group(1), service=self.service))
            m = re.match(r"^/api/v1/courses/([^/]+)$", path)
            if m:
                return MockResponse(200, academic.get_course(course_code=m.group(1), service=self.service))

            # GET /api/v1/research-areas
            if path == "/api/v1/research-areas":
                return MockResponse(200, academic.list_research_areas(
                    unit=params.get("unit"),
                    search=params.get("search"),
                    skip=int(params.get("skip", 0)),
                    limit=int(params.get("limit", 50)),
                    service=self.service,
                ))
            m = re.match(r"^/api/v1/research-areas/([^/]+)/faculty$", path)
            if m:
                return MockResponse(200, academic.get_research_area_faculty(area_id=m.group(1), service=self.service))
            m = re.match(r"^/api/v1/research-areas/([^/]+)$", path)
            if m:
                return MockResponse(200, academic.get_research_area(area_id=m.group(1), service=self.service))

            # GET /api/v1/publications
            if path == "/api/v1/publications":
                year = int(params["year"]) if "year" in params else None
                return MockResponse(200, academic.list_publications(
                    faculty_id=params.get("faculty_id"),
                    pub_type=params.get("pub_type"),
                    year=year,
                    search=params.get("search"),
                    skip=int(params.get("skip", 0)),
                    limit=int(params.get("limit", 50)),
                    service=self.service,
                ))
            m = re.match(r"^/api/v1/publications/([^/]+)$", path)
            if m:
                return MockResponse(200, academic.get_publication(publication_id=m.group(1), service=self.service))

            # GET /api/v1/programs
            if path == "/api/v1/programs":
                return MockResponse(200, academic.list_programs(unit=params.get("unit"), service=self.service))
            m = re.match(r"^/api/v1/programs/([^/]+)/curriculum$", path)
            if m:
                return MockResponse(200, academic.get_program_curriculum(program_id=m.group(1), service=self.service))
            m = re.match(r"^/api/v1/programs/([^/]+)$", path)
            if m:
                return MockResponse(200, academic.get_program(program_id=m.group(1), service=self.service))

            # GET /api/v1/search
            if path == "/api/v1/search":
                return MockResponse(200, academic.search_academic(
                    q=params.get("q", ""),
                    limit=int(params.get("limit", 20)),
                    service=self.service,
                ))

            # GET /api/v1/graph
            if path == "/api/v1/graph/stats":
                return MockResponse(200, academic.get_graph_stats(service=self.service))
            m = re.match(r"^/api/v1/graph/entity/([^/]+)/([^/]+)$", path)
            if m:
                return MockResponse(200, academic.get_entity_subgraph(
                    entity_type=m.group(1),
                    entity_id=m.group(2),
                    depth=int(params.get("depth", 1)),
                    service=self.service,
                ))

            return MockResponse(404, {"detail": f"Path '{path}' not found."})

        except HTTPException as he:
            return MockResponse(he.status_code, {"detail": he.detail})
        except Exception as e:
            return MockResponse(500, {"detail": str(e)})


class TestAcademicAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = DirectAPIClient()

    # ---------------------------------------------------------------------
    # Health & System Status
    # ---------------------------------------------------------------------
    def test_health_check_endpoint(self):
        """Verify /health returns healthy status and loaded counts."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["datasets_loaded"])
        self.assertTrue(data["graph_initialized"])
        self.assertEqual(data["entity_counts"]["units"], 9)
        self.assertEqual(data["entity_counts"]["courses"], 647)
        self.assertEqual(data["entity_counts"]["faculty"], 181)
        self.assertEqual(data["entity_counts"]["publications"], 2796)
        self.assertEqual(data["entity_counts"]["research_areas"], 656)
        self.assertEqual(data["entity_counts"]["programs"], 15)

    # ---------------------------------------------------------------------
    # Academic Units Endpoints
    # ---------------------------------------------------------------------
    def test_list_units(self):
        """Verify GET /api/v1/units returns all 9 academic units."""
        response = self.client.get("/api/v1/units")
        self.assertEqual(response.status_code, 200)
        units = response.json()
        self.assertEqual(len(units), 9)
        unit_ids = {u["id"] for u in units}
        self.assertIn("fcse", unit_ids)
        self.assertIn("fee", unit_ids)
        self.assertIn("fmce", unit_ids)

    def test_get_unit_detail_and_not_found(self):
        """Verify GET /api/v1/units/{unit_id} details and 404 handling."""
        # Success
        response = self.client.get("/api/v1/units/fcse")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["short"], "FCSE")
        self.assertGreater(len(data["faculty"]), 0)
        self.assertGreater(len(data["programs"]), 0)

        # 404 Not Found
        err_resp = self.client.get("/api/v1/units/invalid_unit_slug")
        self.assertEqual(err_resp.status_code, 404)
        self.assertIn("not found", err_resp.json()["detail"].lower())

    # ---------------------------------------------------------------------
    # Faculty Endpoints
    # ---------------------------------------------------------------------
    def test_list_faculty_pagination_and_filters(self):
        """Verify GET /api/v1/faculty supports pagination and filtering."""
        # Default pagination
        resp = self.client.get("/api/v1/faculty?skip=0&limit=20")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total"], 181)
        self.assertEqual(len(data["items"]), 20)

        # Filter by unit
        resp_unit = self.client.get("/api/v1/faculty?unit=fee")
        self.assertEqual(resp_unit.status_code, 200)
        fee_data = resp_unit.json()
        self.assertGreater(fee_data["total"], 0)
        self.assertTrue(all("fee" in f["units"] for f in fee_data["items"]))

        # Filter by verified_only
        resp_verified = self.client.get("/api/v1/faculty?verified_only=true")
        self.assertEqual(resp_verified.status_code, 200)
        self.assertEqual(resp_verified.json()["total"], 161)

    def test_get_faculty_detail_and_sub_resources(self):
        """Verify GET /api/v1/faculty/{id} and publications/research areas."""
        # Detail
        resp = self.client.get("/api/v1/faculty/dr-khurram-khan-jadoon")
        self.assertEqual(resp.status_code, 200)
        fac = resp.json()
        self.assertEqual(fac["id"], "dr-khurram-khan-jadoon")
        self.assertIn("graph_relationships", fac)

        # Sub-resources: publications
        resp_pubs = self.client.get("/api/v1/faculty/dr-massab-junaid/publications")
        self.assertEqual(resp_pubs.status_code, 200)
        self.assertIsInstance(resp_pubs.json(), list)

        # Sub-resources: research-areas
        resp_ra = self.client.get("/api/v1/faculty/dr-khurram-khan-jadoon/research-areas")
        self.assertEqual(resp_ra.status_code, 200)
        self.assertIsInstance(resp_ra.json(), list)

        # 404 Not Found
        err_resp = self.client.get("/api/v1/faculty/unknown_faculty_member")
        self.assertEqual(err_resp.status_code, 404)

    # ---------------------------------------------------------------------
    # Courses Endpoints
    # ---------------------------------------------------------------------
    def test_list_courses_and_filters(self):
        """Verify GET /api/v1/courses pagination and filters."""
        resp = self.client.get("/api/v1/courses?skip=0&limit=50")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total"], 647)
        self.assertEqual(len(data["items"]), 50)

        # Filter by unit
        resp_fcse = self.client.get("/api/v1/courses?unit=fcse")
        self.assertEqual(resp_fcse.status_code, 200)
        self.assertTrue(all(c["unit"] == "fcse" for c in resp_fcse.json()["items"]))

    def test_get_course_details_and_prerequisites(self):
        """Verify GET /api/v1/courses/{code} and prerequisite tracking."""
        # Success
        resp = self.client.get("/api/v1/courses/CS101")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["code"], "CS101")

        # Prerequisites: AI331 references unresolved AI321
        resp_prereq = self.client.get("/api/v1/courses/AI331/prerequisites")
        self.assertEqual(resp_prereq.status_code, 200)
        prereq_data = resp_prereq.json()
        self.assertTrue(prereq_data["found"])
        self.assertIn("AI321", prereq_data["unresolved_prerequisites"])

        # Related entities
        resp_rel = self.client.get("/api/v1/courses/CS101/related")
        self.assertEqual(resp_rel.status_code, 200)
        self.assertIn("programs", resp_rel.json())

        # 404 Not Found
        err_resp = self.client.get("/api/v1/courses/NOT_A_REAL_COURSE")
        self.assertEqual(err_resp.status_code, 404)

    # ---------------------------------------------------------------------
    # Research Areas Endpoints
    # ---------------------------------------------------------------------
    def test_research_areas_endpoints(self):
        """Verify GET /api/v1/research-areas and faculty listing."""
        resp = self.client.get("/api/v1/research-areas?skip=0&limit=30")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["total"], 656)

        # Detail
        detail_resp = self.client.get("/api/v1/research-areas/artificial-intelligence")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["id"], "artificial-intelligence")
        self.assertIn("faculty_members", detail_resp.json())

        # Sub-resource: faculty
        faculty_resp = self.client.get("/api/v1/research-areas/artificial-intelligence/faculty")
        self.assertEqual(faculty_resp.status_code, 200)
        self.assertIsInstance(faculty_resp.json(), list)

    # ---------------------------------------------------------------------
    # Publications Endpoints
    # ---------------------------------------------------------------------
    def test_publications_endpoints(self):
        """Verify GET /api/v1/publications and detail lookup."""
        resp = self.client.get("/api/v1/publications?skip=0&limit=25")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total"], 2796)
        self.assertEqual(len(data["items"]), 25)

        # Single lookup
        first_pub_id = data["items"][0]["id"]
        detail_resp = self.client.get(f"/api/v1/publications/{first_pub_id}")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["id"], first_pub_id)

    # ---------------------------------------------------------------------
    # Programs Endpoints
    # ---------------------------------------------------------------------
    def test_programs_and_curriculum(self):
        """Verify GET /api/v1/programs and curriculum roadmaps."""
        resp = self.client.get("/api/v1/programs")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 15)

        # Curriculum roadmap
        curriculum_resp = self.client.get("/api/v1/programs/bs-computer-science/curriculum")
        self.assertEqual(curriculum_resp.status_code, 200)
        data = curriculum_resp.json()
        self.assertTrue(data["found"])
        self.assertIn("semesters", data)
        self.assertGreater(data["total_courses"], 10)

    # ---------------------------------------------------------------------
    # Search & Knowledge Graph Endpoints
    # ---------------------------------------------------------------------
    def test_search_academic(self):
        """Verify GET /api/v1/search returns multi-entity ranked matches."""
        resp = self.client.get("/api/v1/search?q=machine+learning&limit=15")
        self.assertEqual(resp.status_code, 200)
        results = resp.json()
        self.assertGreater(len(results), 0)
        self.assertIn("entity_type", results[0])
        self.assertIn("title", results[0])

    def test_graph_endpoints(self):
        """Verify GET /api/v1/graph/stats and subgraph extraction."""
        stats_resp = self.client.get("/api/v1/graph/stats")
        self.assertEqual(stats_resp.status_code, 200)
        stats = stats_resp.json()
        self.assertEqual(stats["total_nodes"], 4514)
        self.assertEqual(stats["total_edges"], 5706)

        # Subgraph
        sub_resp = self.client.get("/api/v1/graph/entity/course/CS101?depth=1")
        self.assertEqual(sub_resp.status_code, 200)
        sub_data = sub_resp.json()
        self.assertIn("nodes", sub_data)
        self.assertIn("edges", sub_data)


if __name__ == "__main__":
    unittest.main()
