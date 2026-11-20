"""
Integration tests for GIKI Nexus Student Project Teammate Finder REST API routes.
Verifies all /api/v1/teammates endpoints directly against an isolated SQLite test database.
"""

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.session import Base
from backend.app.api.routes import teammates as routes
from backend.app.models.teammates import (
    ProfileVisibility,
    ContactPreference,
    ProjectStatus,
    InterestStatus,
)
from backend.app.schemas.teammates import (
    ProfileCreate,
    ProfileUpdate,
    ProfileVisibilityUpdate,
    ProjectCreate,
    ProjectUpdate,
    InterestCreate,
    InterestRespondRequest,
)


class TestTeammatesAPI(unittest.TestCase):
    """Test suite for Teammate Finder REST API endpoints."""

    def setUp(self):
        """Set up an in-memory SQLite database for test isolation."""
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()

    def tearDown(self):
        """Clean up DB session and tables."""
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    # -------------------------------------------------------------------------
    # 1. Profile Endpoints Tests
    # -------------------------------------------------------------------------

    def test_api_create_and_get_profile(self):
        """Test POST /api/v1/teammates/profiles and GET /api/v1/teammates/profiles/{id}."""
        create_payload = ProfileCreate(
            display_name="Hamza Tariq",
            email="hamza@giki.edu.pk",
            programme="BS Computer Science",
            academic_year=3,
            technical_skills=["Python", "FastAPI", "PostgreSQL"],
            research_interests=["Cloud Computing"],
            preferred_domains=["Backend Systems"],
            preferred_roles=["Backend Lead"],
            availability="10-15 hrs/week",
            bio="Junior CS student interested in scalable systems.",
            visibility=ProfileVisibility.PUBLIC,
        )
        created = routes.create_profile(data=create_payload, db=self.db)
        self.assertIsNotNone(created.id)
        self.assertEqual(created.display_name, "Hamza Tariq")
        self.assertEqual(created.email, "hamza@giki.edu.pk")

        # GET profile by ID (public view suppresses email)
        fetched = routes.get_profile(profile_id=created.id, db=self.db)
        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.display_name, "Hamza Tariq")
        self.assertFalse(hasattr(fetched, "email"))

    def test_api_anonymous_profile_public_masking(self):
        """Test that ANONYMOUS profile masks name and hides bio in public view."""
        create_payload = ProfileCreate(
            display_name="Secret Identity",
            email="secret@giki.edu.pk",
            programme="BS Artificial Intelligence",
            academic_year=2,
            technical_skills=["PyTorch", "NLP"],
            bio="Identifying personal details here.",
            visibility=ProfileVisibility.ANONYMOUS,
        )
        created = routes.create_profile(data=create_payload, db=self.db)

        # GET public view
        fetched = routes.get_profile(profile_id=created.id, db=self.db)
        self.assertEqual(fetched.display_name, "Anonymous Student (BS Artificial Intelligence, Year 2)")
        self.assertIsNone(fetched.bio)
        self.assertTrue(fetched.is_anonymous)

    def test_api_list_profiles_filtering(self):
        """Test GET /api/v1/teammates/profiles with skill and programme filters."""
        routes.create_profile(
            data=ProfileCreate(
                display_name="Student 1",
                email="s1@giki.edu.pk",
                programme="BS CS",
                academic_year=3,
                technical_skills=["Rust", "C++"],
                visibility=ProfileVisibility.PUBLIC,
            ),
            db=self.db,
        )
        routes.create_profile(
            data=ProfileCreate(
                display_name="Student 2",
                email="s2@giki.edu.pk",
                programme="BS Electrical",
                academic_year=4,
                technical_skills=["Verilog", "MATLAB"],
                visibility=ProfileVisibility.PUBLIC,
            ),
            db=self.db,
        )

        # Filter by skill
        result_rust = routes.list_profiles(skill="Rust", db=self.db)
        self.assertEqual(result_rust["total"], 1)
        self.assertEqual(result_rust["items"][0].display_name, "Student 1")

        # Filter by programme
        result_ee = routes.list_profiles(programme="Electrical", db=self.db)
        self.assertEqual(result_ee["total"], 1)
        self.assertEqual(result_ee["items"][0].display_name, "Student 2")

    def test_api_update_profile_and_visibility(self):
        """Test PUT /api/v1/teammates/profiles/{id} and PATCH .../visibility."""
        created = routes.create_profile(
            data=ProfileCreate(
                display_name="Original Name",
                email="orig@giki.edu.pk",
                programme="BS CS",
                academic_year=2,
                technical_skills=["Python"],
                visibility=ProfileVisibility.PUBLIC,
            ),
            db=self.db,
        )

        # Update profile skills
        updated = routes.update_profile(
            profile_id=created.id,
            data=ProfileUpdate(technical_skills=["Python", "FastAPI", "Docker"]),
            db=self.db,
        )
        self.assertEqual(len(updated.technical_skills), 3)

        # Update visibility to UNLISTED
        vis_resp = routes.update_profile_visibility(
            profile_id=created.id,
            data=ProfileVisibilityUpdate(visibility=ProfileVisibility.UNLISTED),
            db=self.db,
        )
        self.assertEqual(vis_resp["visibility"], ProfileVisibility.UNLISTED)

        # Verify it disappears from discovery listings
        discoverable = routes.list_profiles(db=self.db)
        self.assertEqual(discoverable["total"], 0)

    def test_api_deactivate_and_delete_profile(self):
        """Test POST .../deactivate and DELETE /api/v1/teammates/profiles/{id}."""
        created = routes.create_profile(
            data=ProfileCreate(
                display_name="To Deactivate",
                email="deact@giki.edu.pk",
                programme="BS AI",
                academic_year=1,
                technical_skills=["Python"],
                visibility=ProfileVisibility.PUBLIC,
            ),
            db=self.db,
        )

        # Deactivate
        deact_resp = routes.deactivate_profile(profile_id=created.id, db=self.db)
        self.assertEqual(deact_resp["status"], "deactivated")

        # Confirm excluded from discovery
        discoverable = routes.list_profiles(db=self.db)
        self.assertEqual(discoverable["total"], 0)

        # Delete
        del_resp = routes.delete_profile(profile_id=created.id, db=self.db)
        self.assertEqual(del_resp["status"], "deleted")

    # -------------------------------------------------------------------------
    # 2. Project Endpoints Tests
    # -------------------------------------------------------------------------

    def test_api_create_and_manage_project(self):
        """Test POST /projects, GET /projects/{id}, PUT /projects/{id}, and close."""
        owner = routes.create_profile(
            data=ProfileCreate(
                display_name="Project Owner",
                email="owner@giki.edu.pk",
                programme="BS CS",
                academic_year=4,
                technical_skills=["Python"],
            ),
            db=self.db,
        )

        proj_payload = ProjectCreate(
            owner_id=owner.id,
            title="Smart Campus IoT Sensor Network",
            description="Deploying LoRaWAN sensors for campus air quality.",
            domains=["Internet of Things", "Embedded Systems"],
            required_skills=["C++", "LoRaWAN", "Circuit Design"],
            preferred_roles=["Hardware Lead", "Firmware Engineer"],
            additional_members_needed=2,
        )
        project = routes.create_project(data=proj_payload, db=self.db)
        self.assertIsNotNone(project.id)
        self.assertEqual(project.title, "Smart Campus IoT Sensor Network")
        self.assertEqual(len(project.members), 1)
        self.assertEqual(project.status, ProjectStatus.OPEN)

        # Update project
        updated_proj = routes.update_project(
            project_id=project.id,
            data=ProjectUpdate(additional_members_needed=3),
            db=self.db,
        )
        self.assertEqual(updated_proj.additional_members_needed, 3)

        # Close project
        closed = routes.close_project(project_id=project.id, db=self.db)
        self.assertEqual(closed.status, ProjectStatus.CLOSED)
        self.assertEqual(closed.additional_members_needed, 0)

    # -------------------------------------------------------------------------
    # 3. Recommendation Endpoints Tests
    # -------------------------------------------------------------------------

    def test_api_candidate_and_project_recommendations(self):
        """Test GET /projects/{id}/recommendations and GET /profiles/{id}/recommendations."""
        lead = routes.create_profile(
            data=ProfileCreate(
                display_name="Project Lead",
                email="lead@giki.edu.pk",
                programme="BS AI",
                academic_year=4,
                technical_skills=["Python"],
            ),
            db=self.db,
        )
        candidate = routes.create_profile(
            data=ProfileCreate(
                display_name="Vision Candidate",
                email="candidate@giki.edu.pk",
                programme="BS CS",
                academic_year=3,
                technical_skills=["Computer Vision", "PyTorch", "OpenCV"],
                preferred_domains=["Autonomous Systems"],
                preferred_roles=["CV Specialist"],
                availability="10-15 hrs/week",
                visibility=ProfileVisibility.PUBLIC,
            ),
            db=self.db,
        )

        project = routes.create_project(
            data=ProjectCreate(
                owner_id=lead.id,
                title="Autonomous Rover Perception",
                description="Perception stack for rover obstacle avoidance.",
                domains=["Autonomous Systems"],
                required_skills=["Computer Vision", "PyTorch"],
                preferred_roles=["CV Specialist"],
                additional_members_needed=1,
            ),
            db=self.db,
        )

        # Candidate recommendations for project
        cand_recs = routes.recommend_candidates_for_project(
            project_id=project.id,
            limit=10,
            db=self.db,
        )
        self.assertTrue(len(cand_recs) >= 1)
        top_cand = cand_recs[0]
        self.assertEqual(top_cand.profile_id, candidate.id)
        self.assertTrue(top_cand.overall_score >= 70.0)
        self.assertIn("Computer Vision", top_cand.matching_skills)
        self.assertTrue("Compatibility alignment:" in top_cand.explanation)

        # Project recommendations for candidate
        proj_recs = routes.recommend_projects_for_student(
            profile_id=candidate.id,
            limit=10,
            db=self.db,
        )
        self.assertTrue(len(proj_recs) >= 1)
        top_proj = proj_recs[0]
        self.assertEqual(top_proj.project_id, project.id)
        self.assertTrue(top_proj.overall_score >= 70.0)

    # -------------------------------------------------------------------------
    # 4. Interest & Consent-Based Mutual Contact Sharing Endpoints Tests
    # -------------------------------------------------------------------------

    def test_api_express_interest_and_approval_workflow(self):
        """
        Verify interest submission, pending state withholding contact,
        and approved state revealing mutual contact emails.
        """
        owner = routes.create_profile(
            data=ProfileCreate(
                display_name="Project Owner",
                email="owner@giki.edu.pk",
                programme="BS CS",
                academic_year=4,
                technical_skills=["Python"],
            ),
            db=self.db,
        )
        applicant = routes.create_profile(
            data=ProfileCreate(
                display_name="Applicant",
                email="applicant@giki.edu.pk",
                programme="BS AI",
                academic_year=2,
                technical_skills=["FastAPI"],
            ),
            db=self.db,
        )
        project = routes.create_project(
            data=ProjectCreate(
                owner_id=owner.id,
                title="Distributed Search Engine",
                description="Indexing and querying large datasets.",
                domains=["Information Retrieval"],
                required_skills=["Python", "FastAPI"],
                preferred_roles=["Backend Dev"],
                additional_members_needed=1,
            ),
            db=self.db,
        )

        # Submit interest
        interest = routes.express_interest(
            project_id=project.id,
            data=InterestCreate(
                profile_id=applicant.id,
                proposed_role="Backend Dev",
                message="Hi, I'd love to join!",
            ),
            db=self.db,
        )
        self.assertEqual(interest.status, InterestStatus.PENDING)
        self.assertIsNone(interest.shared_contact_email)

        # List interests for project
        interests = routes.list_project_interests(project_id=project.id, db=self.db)
        self.assertEqual(len(interests), 1)
        self.assertIsNone(interests[0].shared_contact_email)

        # Owner approves interest
        respond_resp = routes.respond_to_interest(
            interest_id=interest.id,
            data=InterestRespondRequest(status=InterestStatus.APPROVED),
            db=self.db,
        )
        self.assertEqual(respond_resp.status, InterestStatus.APPROVED)
        # In approved state, applicant's contact email is now disclosed to owner
        self.assertEqual(respond_resp.shared_contact_email, "applicant@giki.edu.pk")


if __name__ == "__main__":
    unittest.main()
