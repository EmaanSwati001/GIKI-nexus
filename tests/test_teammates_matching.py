"""
Unit tests for GIKI Nexus Teammate Finder models, service, and explainable matching engine.
Verifies profile lifecycle, privacy masking, consent-based contact exchange,
and deterministic rule-based matching scoring.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database.session import Base
from backend.app.models.teammates import (
    StudentProfile,
    Project,
    ProjectMember,
    ProjectInterest,
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
from backend.app.services.teammate_service import TeammateService
from backend.app.services.matching_service import MatchingEngine


@pytest.fixture
def db_session():
    """Create an isolated in-memory SQLite database session for each test."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def service(db_session):
    """TeammateService bound to the test db session."""
    return TeammateService(db=db_session)


# ==============================================================================
# 1. Profile Lifecycle & Privacy Tests
# ==============================================================================

def test_create_and_retrieve_profile(service):
    """Verify profile creation and private retrieval by owner."""
    data = ProfileCreate(
        display_name="Ali Khan",
        email="ali.khan@giki.edu.pk",
        programme="BS Computer Science",
        academic_year=3,
        technical_skills=["Python", "FastAPI", "PyTorch"],
        research_interests=["Computer Vision", "Machine Learning"],
        preferred_domains=["Autonomous Systems", "Healthcare AI"],
        preferred_roles=["ML Engineer", "Backend Developer"],
        availability="10-15 hrs/week",
        bio="Junior CS student passionate about deep learning.",
        visibility=ProfileVisibility.PUBLIC,
    )
    profile = service.create_profile(data)
    assert profile.id is not None
    assert profile.display_name == "Ali Khan"
    assert profile.email == "ali.khan@giki.edu.pk"
    assert "Python" in profile.technical_skills

    # Owner retrieval retains private email
    retrieved = service.get_profile_by_id(profile.id)
    assert retrieved is not None
    assert retrieved.email == "ali.khan@giki.edu.pk"


def test_public_profile_hides_email(service):
    """Verify public formatted profile NEVER leaks email."""
    data = ProfileCreate(
        display_name="Sara Ahmed",
        email="sara.ahmed@giki.edu.pk",
        programme="BS Software Engineering",
        academic_year=4,
        technical_skills=["React", "TypeScript", "TailwindCSS"],
        visibility=ProfileVisibility.PUBLIC,
    )
    profile = service.create_profile(data)
    public_view = service.format_public_profile(profile)

    assert public_view.display_name == "Sara Ahmed"
    assert not hasattr(public_view, "email") or not getattr(public_view, "email", None)
    assert public_view.programme == "BS Software Engineering"


def test_anonymous_profile_masks_identity_and_bio(service):
    """Verify anonymous profiles mask display name and suppress bio in public view."""
    data = ProfileCreate(
        display_name="Zubair Malik",
        email="zubair@giki.edu.pk",
        programme="BS Data Science",
        academic_year=2,
        technical_skills=["SQL", "Python", "Tableau"],
        bio="Secret personal bio with identifiable info.",
        visibility=ProfileVisibility.ANONYMOUS,
    )
    profile = service.create_profile(data)
    public_view = service.format_public_profile(profile)

    assert public_view.display_name == "Anonymous Student (BS Data Science, Year 2)"
    assert public_view.bio is None
    assert "SQL" in public_view.technical_skills


def test_unlisted_and_inactive_profiles_excluded_from_discovery(service):
    """Verify unlisted and deactivated profiles are omitted from public discovery listings."""
    # 1. Public profile
    service.create_profile(ProfileCreate(
        display_name="Public Student",
        email="pub@giki.edu.pk",
        programme="BS CS",
        academic_year=3,
        technical_skills=["Python"],
        visibility=ProfileVisibility.PUBLIC,
    ))
    # 2. Anonymous profile (should appear, masked)
    service.create_profile(ProfileCreate(
        display_name="Anon Student",
        email="anon@giki.edu.pk",
        programme="BS AI",
        academic_year=2,
        technical_skills=["Python"],
        visibility=ProfileVisibility.ANONYMOUS,
    ))
    # 3. Unlisted profile (should NOT appear)
    service.create_profile(ProfileCreate(
        display_name="Unlisted Student",
        email="unlisted@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
        visibility=ProfileVisibility.UNLISTED,
    ))
    # 4. Deactivated profile (should NOT appear)
    deact = service.create_profile(ProfileCreate(
        display_name="Deactivated Student",
        email="deact@giki.edu.pk",
        programme="BS CS",
        academic_year=1,
        technical_skills=["Python"],
        visibility=ProfileVisibility.PUBLIC,
    ))
    service.deactivate_profile(deact.id)

    discoverable = service.list_discoverable_profiles()
    names = [p.display_name for p in discoverable]

    assert "Public Student" in names
    assert any("Anonymous Student" in n for n in names)
    assert "Unlisted Student" not in names
    assert "Deactivated Student" not in names
    assert len(discoverable) == 2


def test_update_profile_and_visibility(service):
    """Verify profile updates and visibility toggle."""
    p = service.create_profile(ProfileCreate(
        display_name="Hassan",
        email="hassan@giki.edu.pk",
        programme="BS Mechanical",
        academic_year=3,
        technical_skills=["MATLAB", "SolidWorks"],
        visibility=ProfileVisibility.PUBLIC,
    ))

    # Update skills and roles
    updated = service.update_profile(p.id, ProfileUpdate(
        technical_skills=["MATLAB", "SolidWorks", "ANSYS", "Python"],
        preferred_roles=["CAD Specialist", "Simulation Lead"],
    ))
    assert len(updated.technical_skills) == 4
    assert "ANSYS" in updated.technical_skills

    # Update visibility
    vis_updated = service.update_visibility(p.id, ProfileVisibilityUpdate(
        visibility=ProfileVisibility.UNLISTED
    ))
    assert vis_updated.visibility == ProfileVisibility.UNLISTED


def test_delete_profile_cascades_safely(service):
    """Verify profile deletion removes profile record."""
    p = service.create_profile(ProfileCreate(
        display_name="Temp Student",
        email="temp@giki.edu.pk",
        programme="BS CS",
        academic_year=1,
        technical_skills=["C++"],
    ))
    pid = p.id
    assert service.get_profile_by_id(pid) is not None
    deleted = service.delete_profile(pid)
    assert deleted is True
    assert service.get_profile_by_id(pid) is None


# ==============================================================================
# 2. Project Lifecycle Tests
# ==============================================================================

def test_project_creation_and_member_assignment(service):
    """Verify project creation automatically registers owner as first member."""
    owner = service.create_profile(ProfileCreate(
        display_name="Lead Researcher",
        email="lead@giki.edu.pk",
        programme="BS AI",
        academic_year=4,
        technical_skills=["PyTorch", "Python", "ROS"],
    ))

    project_data = ProjectCreate(
        owner_id=owner.id,
        title="Autonomous Quadcopter Navigation",
        description="Developing SLAM and path planning for GPS-denied environments.",
        domains=["Robotics", "Autonomous Systems", "Computer Vision"],
        required_skills=["ROS", "C++", "SLAM", "Python"],
        preferred_roles=["Robotics Software Engineer", "Control Systems Lead"],
        additional_members_needed=2,
    )
    project = service.create_project(project_data)

    assert project.id is not None
    assert project.title == "Autonomous Quadcopter Navigation"
    assert project.status == ProjectStatus.OPEN
    assert len(project.members) == 1
    assert project.members[0].profile_id == owner.id
    assert project.members[0].role == "Project Lead"


def test_project_close_recruitment(service):
    """Verify closing project recruitment updates status and excludes from open listings."""
    owner = service.create_profile(ProfileCreate(
        display_name="Owner",
        email="own@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["React"],
    ))
    proj = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="Campus Event App",
        description="Mobile app for campus events.",
        domains=["Mobile", "Web"],
        required_skills=["Flutter", "Dart"],
        preferred_roles=["Mobile Dev"],
        additional_members_needed=1,
    ))

    # Before close
    open_projects = service.list_projects(status_filter=ProjectStatus.OPEN)
    assert any(p.id == proj.id for p in open_projects)

    # Close recruitment
    closed = service.close_project(proj.id)
    assert closed.status == ProjectStatus.CLOSED
    assert closed.additional_members_needed == 0

    open_projects_after = service.list_projects(status_filter=ProjectStatus.OPEN)
    assert not any(p.id == proj.id for p in open_projects_after)


# ==============================================================================
# 3. Privacy & Consent-Based Contact Exchange Tests
# ==============================================================================

def test_interest_workflow_consent_based_contact_sharing(service):
    """
    CRITICAL PRIVACY TEST:
    1. Student submits expression of interest.
    2. While PENDING, applicant cannot see owner's email, and owner cannot see applicant's email.
    3. Once APPROVED by owner, both mutual emails are unlocked via shared_contact_email.
    4. If REJECTED, email remains withheld.
    """
    owner = service.create_profile(ProfileCreate(
        display_name="Project Owner",
        email="owner.secret@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python", "FastAPI"],
    ))
    applicant = service.create_profile(ProfileCreate(
        display_name="Applicant Candidate",
        email="candidate.secret@giki.edu.pk",
        programme="BS AI",
        academic_year=3,
        technical_skills=["PyTorch", "Docker"],
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="Edge AI Platform",
        description="Deploying quantized models to edge devices.",
        domains=["Artificial Intelligence"],
        required_skills=["Python", "PyTorch", "Docker"],
        preferred_roles=["MLOps Engineer"],
        additional_members_needed=1,
    ))

    # 1. Express interest
    interest_data = InterestCreate(
        profile_id=applicant.id,
        proposed_role="MLOps Engineer",
        message="I have experience deploying ONNX models to Jetson Nano.",
    )
    interest = service.express_interest(project.id, interest_data)

    assert interest.id is not None
    assert interest.status == InterestStatus.PENDING

    # Format interest for view while PENDING: contact email MUST BE None
    pending_resp = service.format_interest_response(interest, viewer_id=owner.id)
    assert pending_resp.shared_contact_email is None

    pending_applicant_resp = service.format_interest_response(interest, viewer_id=applicant.id)
    assert pending_applicant_resp.shared_contact_email is None

    # 2. Owner APPROVES interest
    approved = service.respond_to_interest(
        interest.id,
        owner_id=owner.id,
        response_data=InterestRespondRequest(action=InterestStatus.APPROVED),
    )
    assert approved.status == InterestStatus.APPROVED

    # Now owner viewing interest sees applicant's email
    owner_view = service.format_interest_response(approved, viewer_id=owner.id)
    assert owner_view.shared_contact_email == "candidate.secret@giki.edu.pk"

    # Applicant viewing interest sees owner's email
    applicant_view = service.format_interest_response(approved, viewer_id=applicant.id)
    assert applicant_view.shared_contact_email == "owner.secret@giki.edu.pk"

    # Candidate should also have been added to project members
    updated_project = service.get_project_by_id(project.id)
    member_profile_ids = [m.profile_id for m in updated_project.members]
    assert applicant.id in member_profile_ids


# ==============================================================================
# 4. Explainable Matching Engine Tests
# ==============================================================================

def test_matching_engine_skill_and_domain_overlap():
    """Verify deterministic scoring and explanation generation for skills & domains."""
    engine = MatchingEngine()

    candidate = StudentProfile(
        id="c1",
        display_name="Taimoor",
        programme="BS Computer Science",
        academic_year=3,
        technical_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        research_interests=["Cloud Computing", "Distributed Systems"],
        preferred_domains=["Backend Systems", "Cloud Platforms"],
        preferred_roles=["Backend Engineer"],
        availability="10-15 hrs/week",
        previous_experience="Intern at tech firm",
    )

    project = Project(
        id="p1",
        title="Distributed Microservices Framework",
        description="High-performance RPC service.",
        domains=["Backend Systems", "Distributed Systems"],
        required_skills=["Python", "Docker", "Kubernetes", "gRPC"],
        preferred_roles=["Backend Engineer", "DevOps Specialist"],
        additional_members_needed=2,
    )

    score_card = engine.calculate_fit(candidate=candidate, project=project, existing_team=[])

    assert score_card.overall_score > 60.0
    assert "Python" in score_card.matched_skills
    assert "Docker" in score_card.matched_skills
    assert "Backend Systems" in score_card.matched_domains
    assert "Backend Engineer" in score_card.matched_roles
    assert score_card.breakdown.skill_score > 0
    assert score_card.breakdown.domain_score > 0
    assert score_card.breakdown.role_score > 0

    # Ensure explanation is informative and human readable
    assert "Offers 2 required skill(s)" in score_card.explanation
    assert "Shares project domain interest(s)" in score_card.explanation
    assert "Prefers requested role" in score_card.explanation


def test_matching_engine_complementary_skill_bonus():
    """Verify candidate receives complementarity bonus for covering missing team skills."""
    engine = MatchingEngine()

    # Lead already knows Python and FastAPI
    lead = StudentProfile(
        id="lead",
        display_name="Lead",
        technical_skills=["Python", "FastAPI"],
    )

    # Candidate knows React and CSS (fills frontend gap)
    cand_frontend = StudentProfile(
        id="c_front",
        display_name="Frontend Candidate",
        programme="BS Software Engineering",
        academic_year=3,
        technical_skills=["React", "CSS", "TypeScript"],
        preferred_domains=["Full Stack Web"],
        preferred_roles=["Frontend Lead"],
        availability="10-15 hrs/week",
    )

    project = Project(
        id="p_full",
        title="Full Stack Portal",
        domains=["Full Stack Web"],
        required_skills=["Python", "FastAPI", "React", "TypeScript"],
        preferred_roles=["Frontend Lead", "Backend Lead"],
        additional_members_needed=1,
    )

    score_card = engine.calculate_fit(
        candidate=cand_frontend,
        project=project,
        existing_team=[lead],
    )

    # The candidate covers React and TypeScript, which the team currently lacks
    assert "React" in score_card.complementary_skills
    assert "TypeScript" in score_card.complementary_skills
    assert "Fills critical team skill gap(s)" in score_card.explanation


def test_candidate_recommendations_ranking(service):
    """Verify candidate recommendations are ranked by descending matching score."""
    owner = service.create_profile(ProfileCreate(
        display_name="Owner",
        email="own@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
    ))

    # Candidate A: strong match
    cand_a = service.create_profile(ProfileCreate(
        display_name="Strong Candidate",
        email="strong@giki.edu.pk",
        programme="BS AI",
        academic_year=3,
        technical_skills=["PyTorch", "Computer Vision", "OpenCV"],
        preferred_domains=["Autonomous Systems", "Robotics"],
        preferred_roles=["Computer Vision Engineer"],
        availability="10-15 hrs/week",
        visibility=ProfileVisibility.PUBLIC,
    ))

    # Candidate B: weak match
    cand_b = service.create_profile(ProfileCreate(
        display_name="Weak Candidate",
        email="weak@giki.edu.pk",
        programme="BS Management",
        academic_year=1,
        technical_skills=["Excel", "PowerPoint"],
        preferred_domains=["Finance"],
        preferred_roles=["Project Manager"],
        availability="1-5 hrs/week",
        visibility=ProfileVisibility.PUBLIC,
    ))

    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="Autonomous Drone Vision",
        description="Developing computer vision algorithms for drones.",
        domains=["Autonomous Systems", "Robotics"],
        required_skills=["PyTorch", "Computer Vision", "OpenCV"],
        preferred_roles=["Computer Vision Engineer"],
        additional_members_needed=1,
    ))

    recommendations = service.recommend_candidates_for_project(project.id)

    assert len(recommendations) >= 2
    # Strong candidate should be ranked first with a significantly higher score
    assert recommendations[0].candidate.id == cand_a.id
    assert recommendations[0].match_score > recommendations[1].match_score
    assert recommendations[0].match_score >= 80.0
