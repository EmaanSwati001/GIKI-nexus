"""
Integration tests for GIKI Nexus Student Project Teammate Finder REST API routes.
Verifies all /api/v1/teammates endpoints directly against an isolated SQLite test database.

Ownership keys are tested here as first-class citizens.  Every mutation endpoint
requires an X-Ownership-Key header; these tests verify both the happy path
(correct key passes) and the enforcement path (wrong/missing key → OwnershipError).

PROTOTYPE AUTHENTICATION NOTICE
================================
Ownership keys are a development-time prototype mechanism only.  They are NOT
equivalent to institutional SSO, session tokens, or production authentication.
"""

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi import HTTPException
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
from backend.app.services.teammate_service import TeammateService, OwnershipError


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
    # Helpers
    # -------------------------------------------------------------------------

    def _create_profile(self, display_name="Test Student", email=None, **kwargs):
        """Create a profile and return the ProfilePrivateResponse (includes ownership_key)."""
        if email is None:
            # Derive a simple email from the display name
            email = display_name.lower().replace(" ", ".") + "@giki.edu.pk"
        payload = ProfileCreate(
            display_name=display_name,
            email=email,
            programme=kwargs.pop("programme", "BS Computer Science"),
            academic_year=kwargs.pop("academic_year", 3),
            technical_skills=kwargs.pop("technical_skills", ["Python"]),
            visibility=kwargs.pop("visibility", ProfileVisibility.PUBLIC),
            **kwargs,
        )
        return routes.create_profile(data=payload, db=self.db)

    def _create_project(self, owner_id, title="Test Project", owner_key=None, **kwargs):
        """Create a project and return the ProjectCreateResponse (includes ownership_key)."""
        payload = ProjectCreate(
            owner_id=owner_id,
            title=title,
            description=kwargs.pop("description", "A test project description long enough."),
            domains=kwargs.pop("domains", ["Software Engineering"]),
            required_skills=kwargs.pop("required_skills", ["Python"]),
            preferred_roles=kwargs.pop("preferred_roles", ["Developer"]),
            additional_members_needed=kwargs.pop("additional_members_needed", 1),
            **kwargs,
        )
        return routes.create_project(data=payload, db=self.db)

    # -------------------------------------------------------------------------
    # 1. Profile Creation & Retrieval
    # -------------------------------------------------------------------------

    def test_api_create_returns_ownership_key(self):
        """POST /profiles returns ownership_key once at creation."""
        created = self._create_profile("Hamza Tariq")
        self.assertIsNotNone(created.id)
        self.assertTrue(hasattr(created, "ownership_key"))
        self.assertEqual(len(created.ownership_key), 32)  # 128-bit hex

    def test_api_create_and_get_profile(self):
        """POST /profiles then GET /profiles/{id} — public view has no email, no key."""
        created = self._create_profile("Hamza Tariq", email="hamza@giki.edu.pk")
        self.assertEqual(created.display_name, "Hamza Tariq")
        self.assertEqual(created.email, "hamza@giki.edu.pk")

        # Public GET suppresses email and ownership_key
        fetched = routes.get_profile(profile_id=created.id, db=self.db)
        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.display_name, "Hamza Tariq")
        self.assertFalse(hasattr(fetched, "email"), "Public profile must not expose email")
        self.assertFalse(hasattr(fetched, "ownership_key"), "Public profile must not expose ownership_key")

    def test_api_anonymous_profile_public_masking(self):
        """ANONYMOUS profile masks name and hides bio in public view."""
        created = self._create_profile(
            "Secret Identity",
            email="secret@giki.edu.pk",
            programme="BS Artificial Intelligence",
            academic_year=2,
            technical_skills=["PyTorch", "NLP"],
            bio="Identifying personal details here.",
            visibility=ProfileVisibility.ANONYMOUS,
        )
        fetched = routes.get_profile(profile_id=created.id, db=self.db)
        self.assertEqual(fetched.display_name, "Anonymous Student (BS Artificial Intelligence, Year 2)")
        self.assertIsNone(fetched.bio)
        self.assertTrue(fetched.is_anonymous)
        self.assertFalse(hasattr(fetched, "email"))

    def test_api_list_profiles_filtering(self):
        """GET /profiles with skill and programme filters."""
        self._create_profile(
            "Student 1",
            email="s1@giki.edu.pk",
            programme="BS CS",
            technical_skills=["Rust", "C++"],
        )
        self._create_profile(
            "Student 2",
            email="s2@giki.edu.pk",
            programme="BS Electrical",
            academic_year=4,
            technical_skills=["Verilog", "MATLAB"],
        )

        result_rust = routes.list_profiles(skill="Rust", db=self.db)
        self.assertEqual(result_rust["total"], 1)
        self.assertEqual(result_rust["items"][0].display_name, "Student 1")

        result_ee = routes.list_profiles(programme="Electrical", db=self.db)
        self.assertEqual(result_ee["total"], 1)
        self.assertEqual(result_ee["items"][0].display_name, "Student 2")

    def test_api_list_excludes_unlisted_profiles(self):
        """Unlisted profiles are excluded from public discovery listing."""
        self._create_profile("Visible Student", visibility=ProfileVisibility.PUBLIC)
        self._create_profile("Hidden Student", visibility=ProfileVisibility.UNLISTED)
        result = routes.list_profiles(db=self.db)
        names = [p.display_name for p in result["items"]]
        self.assertIn("Visible Student", names)
        self.assertNotIn("Hidden Student", names)

    def test_api_list_excludes_deactivated_profiles(self):
        """Deactivated profiles are excluded from discovery listing."""
        created = self._create_profile("Active Student")
        routes.deactivate_profile(
            profile_id=created.id,
            x_ownership_key=created.ownership_key,
            db=self.db,
        )
        result = routes.list_profiles(db=self.db)
        self.assertEqual(result["total"], 0)

    # -------------------------------------------------------------------------
    # 2. Profile Mutation Ownership Enforcement
    # -------------------------------------------------------------------------

    def test_api_update_profile_requires_correct_key(self):
        """PUT /profiles/{id} fails with wrong ownership key (HTTP 403)."""
        created = self._create_profile("Original Name")
        with self.assertRaises(HTTPException) as ctx:
            routes.update_profile(
                profile_id=created.id,
                data=ProfileUpdate(technical_skills=["Go"]),
                x_ownership_key="wrong_key_000000000000000000000000",
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_api_update_profile_succeeds_with_correct_key(self):
        """PUT /profiles/{id} succeeds with the correct ownership key."""
        created = self._create_profile("Original Name")
        updated = routes.update_profile(
            profile_id=created.id,
            data=ProfileUpdate(technical_skills=["Python", "FastAPI", "Docker"]),
            x_ownership_key=created.ownership_key,
            db=self.db,
        )
        self.assertEqual(len(updated.technical_skills), 3)

    def test_api_update_visibility_requires_key(self):
        """PATCH /profiles/{id}/visibility enforces ownership key (HTTP 403)."""
        created = self._create_profile("Original Name")
        with self.assertRaises(HTTPException) as ctx:
            routes.update_profile_visibility(
                profile_id=created.id,
                data=ProfileVisibilityUpdate(visibility=ProfileVisibility.UNLISTED),
                x_ownership_key="bad_key_0000000000000000000000000",
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_api_update_visibility_succeeds_and_hides_from_discovery(self):
        """PATCH /profiles/{id}/visibility with correct key unlists the profile."""
        created = self._create_profile("Original Name")
        vis_resp = routes.update_profile_visibility(
            profile_id=created.id,
            data=ProfileVisibilityUpdate(visibility=ProfileVisibility.UNLISTED),
            x_ownership_key=created.ownership_key,
            db=self.db,
        )
        self.assertEqual(vis_resp.visibility, ProfileVisibility.UNLISTED)
        discoverable = routes.list_profiles(db=self.db)
        self.assertEqual(discoverable["total"], 0)

    def test_api_deactivate_profile_requires_key(self):
        """POST /profiles/{id}/deactivate enforces ownership key (HTTP 403)."""
        created = self._create_profile("To Deactivate")
        with self.assertRaises(HTTPException) as ctx:
            routes.deactivate_profile(
                profile_id=created.id,
                x_ownership_key="bad_key_0000000000000000000000000",
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_api_deactivate_and_delete_profile(self):
        """POST .../deactivate and DELETE /profiles/{id} lifecycle with correct key."""
        created = self._create_profile("To Deactivate")

        deact_resp = routes.deactivate_profile(
            profile_id=created.id,
            x_ownership_key=created.ownership_key,
            db=self.db,
        )
        self.assertEqual(deact_resp["status"], "deactivated")

        discoverable = routes.list_profiles(db=self.db)
        self.assertEqual(discoverable["total"], 0)

        del_resp = routes.delete_profile(
            profile_id=created.id,
            x_ownership_key=created.ownership_key,
            db=self.db,
        )
        self.assertEqual(del_resp["status"], "deleted")

    def test_api_id_alone_does_not_grant_profile_ownership(self):
        """Profile mutations with no key (None) raise HTTP 403."""
        created = self._create_profile("ID-Only Student")
        with self.assertRaises(HTTPException) as ctx:
            routes.update_profile(
                profile_id=created.id,
                data=ProfileUpdate(bio="Injected bio"),
                x_ownership_key=None,
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    # -------------------------------------------------------------------------
    # 3. Project Endpoints
    # -------------------------------------------------------------------------

    def test_api_create_project_returns_ownership_key(self):
        """POST /projects returns ownership_key once at creation."""
        owner = self._create_profile("Project Owner")
        project = self._create_project(owner_id=owner.id)
        self.assertIsNotNone(project.id)
        self.assertTrue(hasattr(project, "ownership_key"))
        self.assertEqual(len(project.ownership_key), 32)

    def test_api_create_and_manage_project(self):
        """Full project lifecycle: create → update → close (with ownership keys)."""
        owner = self._create_profile("Project Owner", email="owner@giki.edu.pk")

        project = self._create_project(
            owner_id=owner.id,
            title="Smart Campus IoT Sensor Network",
            description="Deploying LoRaWAN sensors for campus air quality monitoring.",
            domains=["Internet of Things", "Embedded Systems"],
            required_skills=["C++", "LoRaWAN", "Circuit Design"],
            preferred_roles=["Hardware Lead", "Firmware Engineer"],
            additional_members_needed=2,
        )
        self.assertIsNotNone(project.id)
        self.assertEqual(project.title, "Smart Campus IoT Sensor Network")
        self.assertEqual(len(project.members), 1)
        self.assertEqual(project.status, ProjectStatus.OPEN)

        # Update project — requires owner key
        updated_proj = routes.update_project(
            project_id=project.id,
            data=ProjectUpdate(additional_members_needed=3),
            x_ownership_key=project.ownership_key,
            db=self.db,
        )
        self.assertEqual(updated_proj.additional_members_needed, 3)

        # Close project — requires owner key
        closed = routes.close_project(
            project_id=project.id,
            x_ownership_key=project.ownership_key,
            db=self.db,
        )
        self.assertEqual(closed.status, ProjectStatus.CLOSED)
        self.assertEqual(closed.additional_members_needed, 0)

    def test_api_update_project_requires_key(self):
        """PUT /projects/{id} with wrong key raises HTTP 403."""
        owner = self._create_profile("Owner")
        project = self._create_project(owner_id=owner.id)
        with self.assertRaises(HTTPException) as ctx:
            routes.update_project(
                project_id=project.id,
                data=ProjectUpdate(title="Hijacked Title"),
                x_ownership_key="bad_key_0000000000000000000000000",
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_api_close_project_requires_key(self):
        """POST /projects/{id}/close with wrong key raises HTTP 403."""
        owner = self._create_profile("Owner")
        project = self._create_project(owner_id=owner.id)
        with self.assertRaises(HTTPException) as ctx:
            routes.close_project(
                project_id=project.id,
                x_ownership_key="bad_key_0000000000000000000000000",
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_api_delete_project_requires_key(self):
        """DELETE /projects/{id} with wrong key raises HTTP 403."""
        owner = self._create_profile("Owner")
        project = self._create_project(owner_id=owner.id)
        with self.assertRaises(HTTPException) as ctx:
            routes.delete_project(
                project_id=project.id,
                x_ownership_key="bad_key_0000000000000000000000000",
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_api_id_alone_does_not_grant_project_ownership(self):
        """Project mutations with no key (None) raise HTTP 403."""
        owner = self._create_profile("Owner")
        project = self._create_project(owner_id=owner.id)
        with self.assertRaises(HTTPException) as ctx:
            routes.update_project(
                project_id=project.id,
                data=ProjectUpdate(title="Injected"),
                x_ownership_key=None,
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    # -------------------------------------------------------------------------
    # 4. Recommendation Endpoints
    # -------------------------------------------------------------------------

    def test_api_candidate_recommendations_no_email(self):
        """GET /projects/{id}/recommendations returns no email fields."""
        lead = self._create_profile("Project Lead", email="lead@giki.edu.pk")
        self._create_profile(
            "Vision Candidate",
            email="candidate@giki.edu.pk",
            programme="BS CS",
            academic_year=3,
            technical_skills=["Computer Vision", "PyTorch", "OpenCV"],
            preferred_domains=["Autonomous Systems"],
            preferred_roles=["CV Specialist"],
            availability="10-15 hrs/week",
        )
        project = self._create_project(
            owner_id=lead.id,
            title="Autonomous Rover Perception",
            description="Perception stack for rover obstacle avoidance system.",
            domains=["Autonomous Systems"],
            required_skills=["Computer Vision", "PyTorch"],
            preferred_roles=["CV Specialist"],
        )

        cand_recs = routes.recommend_candidates_for_project(
            project_id=project.id, limit=10, db=self.db
        )
        self.assertTrue(len(cand_recs) >= 1)
        for rec in cand_recs:
            self.assertFalse(hasattr(rec, "email"), "Recommendations must not expose email")
            self.assertFalse(hasattr(rec, "ownership_key"), "Recommendations must not expose ownership_key")

    def test_api_candidate_and_project_recommendations(self):
        """GET /projects/{id}/recommendations and GET /profiles/{id}/recommendations."""
        lead = self._create_profile("Project Lead", email="lead@giki.edu.pk")
        candidate = self._create_profile(
            "Vision Candidate",
            email="candidate@giki.edu.pk",
            programme="BS CS",
            academic_year=3,
            technical_skills=["Computer Vision", "PyTorch", "OpenCV"],
            preferred_domains=["Autonomous Systems"],
            preferred_roles=["CV Specialist"],
            availability="10-15 hrs/week",
        )
        project = self._create_project(
            owner_id=lead.id,
            title="Autonomous Rover Perception",
            description="Perception stack for rover obstacle avoidance system.",
            domains=["Autonomous Systems"],
            required_skills=["Computer Vision", "PyTorch"],
            preferred_roles=["CV Specialist"],
        )

        cand_recs = routes.recommend_candidates_for_project(
            project_id=project.id, limit=10, db=self.db
        )
        self.assertTrue(len(cand_recs) >= 1)
        top_cand = cand_recs[0]
        self.assertEqual(top_cand.profile_id, candidate.id)
        self.assertTrue(top_cand.overall_score >= 70.0)
        self.assertIn("Computer Vision", top_cand.matching_skills)
        self.assertIn("Compatibility alignment:", top_cand.explanation)

        proj_recs = routes.recommend_projects_for_student(
            profile_id=candidate.id, limit=10, db=self.db
        )
        self.assertTrue(len(proj_recs) >= 1)
        top_proj = proj_recs[0]
        self.assertEqual(top_proj.project_id, project.id)
        self.assertTrue(top_proj.overall_score >= 70.0)

    def test_api_unlisted_profile_excluded_from_recommendations(self):
        """Unlisted profiles are not surfaced in candidate recommendations."""
        lead = self._create_profile("Lead")
        hidden = self._create_profile(
            "Hidden Expert",
            technical_skills=["Python", "Rust"],
            visibility=ProfileVisibility.UNLISTED,
        )
        project = self._create_project(
            owner_id=lead.id,
            required_skills=["Python", "Rust"],
        )
        recs = routes.recommend_candidates_for_project(
            project_id=project.id, limit=20, db=self.db
        )
        rec_ids = [r.profile_id for r in recs]
        self.assertNotIn(hidden.id, rec_ids)

    # -------------------------------------------------------------------------
    # 5. Interest & Consent-Based Contact Sharing
    # -------------------------------------------------------------------------

    def test_api_express_interest_and_approval_workflow(self):
        """
        Interest lifecycle:
        - Submit interest (no key needed for applicant)
        - PENDING state withholds contact email
        - Owner approves using project ownership_key → contact email revealed
        """
        owner = self._create_profile("Project Owner", email="owner@giki.edu.pk")
        applicant = self._create_profile("Applicant", email="applicant@giki.edu.pk")
        project = self._create_project(
            owner_id=owner.id,
            title="Distributed Search Engine",
            description="Indexing and querying large datasets efficiently.",
            domains=["Information Retrieval"],
            required_skills=["Python", "FastAPI"],
            preferred_roles=["Backend Dev"],
        )

        # Submit interest — no ownership key required from applicant
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

        # List interests — requires project owner key
        interests = routes.list_project_interests(
            project_id=project.id,
            x_ownership_key=project.ownership_key,
            db=self.db,
        )
        self.assertEqual(len(interests), 1)
        self.assertIsNone(interests[0].shared_contact_email)

        # Owner approves — requires project owner key
        respond_resp = routes.respond_to_interest(
            interest_id=interest.id,
            data=InterestRespondRequest(action=InterestStatus.APPROVED),
            x_ownership_key=project.ownership_key,
            db=self.db,
        )
        self.assertEqual(respond_resp.status, InterestStatus.APPROVED)
        self.assertEqual(respond_resp.shared_contact_email, "applicant@giki.edu.pk")

    def test_api_list_interests_requires_owner_key(self):
        """GET /projects/{id}/interests requires project ownership key (HTTP 403)."""
        owner = self._create_profile("Owner")
        project = self._create_project(owner_id=owner.id)
        with self.assertRaises(HTTPException) as ctx:
            routes.list_project_interests(
                project_id=project.id,
                x_ownership_key="bad_key_0000000000000000000000000",
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_api_respond_to_interest_requires_project_owner_key(self):
        """POST /interests/{id}/respond requires the project's ownership key, not the applicant's (HTTP 403)."""
        owner = self._create_profile("Owner")
        applicant = self._create_profile("Applicant")
        project = self._create_project(owner_id=owner.id)

        interest = routes.express_interest(
            project_id=project.id,
            data=InterestCreate(profile_id=applicant.id),
            db=self.db,
        )

        # Applicant's own profile key must NOT authorize interest approval
        with self.assertRaises(HTTPException) as ctx:
            routes.respond_to_interest(
                interest_id=interest.id,
                data=InterestRespondRequest(action=InterestStatus.APPROVED),
                x_ownership_key=applicant.ownership_key,
                db=self.db,
            )
        self.assertEqual(ctx.exception.status_code, 403)

        # Project owner key succeeds
        resp = routes.respond_to_interest(
            interest_id=interest.id,
            data=InterestRespondRequest(action=InterestStatus.APPROVED),
            x_ownership_key=project.ownership_key,
            db=self.db,
        )
        self.assertEqual(resp.status, InterestStatus.APPROVED)

    def test_api_rejected_interest_withholds_contact(self):
        """Rejected interest does not reveal contact email."""
        owner = self._create_profile("Owner", email="owner@giki.edu.pk")
        applicant = self._create_profile("Applicant", email="applicant@giki.edu.pk")
        project = self._create_project(owner_id=owner.id)

        interest = routes.express_interest(
            project_id=project.id,
            data=InterestCreate(profile_id=applicant.id),
            db=self.db,
        )
        resp = routes.respond_to_interest(
            interest_id=interest.id,
            data=InterestRespondRequest(action=InterestStatus.REJECTED),
            x_ownership_key=project.ownership_key,
            db=self.db,
        )
        self.assertEqual(resp.status, InterestStatus.REJECTED)
        self.assertIsNone(resp.shared_contact_email)

    def test_api_anonymous_requester_name_masked_in_interest_response(self):
        """Anonymous applicant name is masked in interest response visible to owner."""
        owner = self._create_profile("Owner")
        anon_applicant = self._create_profile(
            "Real Name",
            programme="BS CS",
            academic_year=2,
            visibility=ProfileVisibility.ANONYMOUS,
        )
        project = self._create_project(owner_id=owner.id)

        interest = routes.express_interest(
            project_id=project.id,
            data=InterestCreate(profile_id=anon_applicant.id),
            db=self.db,
        )
        interests = routes.list_project_interests(
            project_id=project.id,
            x_ownership_key=project.ownership_key,
            db=self.db,
        )
        self.assertEqual(len(interests), 1)
        # Must NOT contain real name
        self.assertNotEqual(interests[0].requester_name, "Real Name")
        self.assertIn("Anonymous", interests[0].requester_name)

    def test_api_pending_interest_withholds_contact(self):
        """PENDING interest response has no shared_contact_email."""
        owner = self._create_profile("Owner", email="owner@giki.edu.pk")
        applicant = self._create_profile("Applicant", email="applicant@giki.edu.pk")
        project = self._create_project(owner_id=owner.id)

        interest = routes.express_interest(
            project_id=project.id,
            data=InterestCreate(profile_id=applicant.id),
            db=self.db,
        )
        self.assertEqual(interest.status, InterestStatus.PENDING)
        self.assertIsNone(interest.shared_contact_email)


if __name__ == "__main__":
    unittest.main()
