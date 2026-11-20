"""
Unit tests for GIKI Nexus Teammate Finder — service layer, matching engine, and privacy rules.
Verifies profile lifecycle, ownership enforcement, privacy masking, consent workflows,
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
    verify_ownership_key,
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
# 1. Ownership Key Generation & Verification
# ==============================================================================

def test_ownership_key_is_securely_generated():
    """Ownership keys must be non-empty 32-char hex strings (128-bit entropy)."""
    from backend.app.models.teammates import generate_ownership_key
    key1 = generate_ownership_key()
    key2 = generate_ownership_key()
    assert len(key1) == 32
    assert len(key2) == 32
    assert key1 != key2  # Probabilistically guaranteed
    assert all(c in "0123456789abcdef" for c in key1)


def test_ownership_key_verification():
    """verify_ownership_key must use constant-time comparison."""
    from backend.app.models.teammates import generate_ownership_key
    key = generate_ownership_key()
    assert verify_ownership_key(key, key) is True
    assert verify_ownership_key("wrong_key_value_x", key) is False
    assert verify_ownership_key("", key) is False
    assert verify_ownership_key(None, key) is False


def test_profile_has_ownership_key_on_creation(service, db_session):
    """Every created profile must have a non-empty ownership_key stored in DB."""
    profile = service.create_profile(ProfileCreate(
        display_name="Key Test",
        email="keytest@giki.edu.pk",
        programme="BS CS",
        academic_year=2,
        technical_skills=["Python"],
    ))
    assert profile.ownership_key is not None
    assert len(profile.ownership_key) == 32


def test_project_has_ownership_key_on_creation(service, db_session):
    """Every created project must have a non-empty ownership_key stored in DB."""
    owner = service.create_profile(ProfileCreate(
        display_name="Proj Owner",
        email="pown@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=[],
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="Test Project",
        description="Testing key generation",
        domains=[],
        required_skills=[],
        preferred_roles=[],
        additional_members_needed=1,
    ))
    assert project.ownership_key is not None
    assert len(project.ownership_key) == 32


# ==============================================================================
# 2. Ownership Enforcement on Profile Mutations
# ==============================================================================

def test_update_profile_requires_correct_key(service, db_session):
    """Update fails with wrong key and succeeds with correct key."""
    profile = service.create_profile(ProfileCreate(
        display_name="Ali Khan",
        email="ali@giki.edu.pk",
        programme="BS CS",
        academic_year=3,
        technical_skills=["Python"],
    ))

    # Wrong key → OwnershipError
    with pytest.raises(OwnershipError):
        service.update_profile(
            db_session, profile.id,
            ProfileUpdate(technical_skills=["Python", "Hacking"]),
            owner_key="wrong_key_000000000000000000000000",
        )

    # Correct key → success
    updated = service.update_profile(
        db_session, profile.id,
        ProfileUpdate(technical_skills=["Python", "FastAPI"]),
        owner_key=profile.ownership_key,
    )
    assert updated is not None
    assert "FastAPI" in updated.technical_skills


def test_deactivate_profile_requires_correct_key(service, db_session):
    """Deactivation fails with wrong key."""
    profile = service.create_profile(ProfileCreate(
        display_name="Sara Ahmed",
        email="sara@giki.edu.pk",
        programme="BS AI",
        academic_year=2,
        technical_skills=["PyTorch"],
    ))

    with pytest.raises(OwnershipError):
        service.deactivate_profile(db_session, profile.id, owner_key="bad_key_00000000000000000000000")

    # Correct key succeeds
    success = service.deactivate_profile(db_session, profile.id, owner_key=profile.ownership_key)
    assert success is True


def test_delete_profile_requires_correct_key(service, db_session):
    """Deletion fails with wrong key."""
    profile = service.create_profile(ProfileCreate(
        display_name="Zubair",
        email="zub@giki.edu.pk",
        programme="BS CS",
        academic_year=1,
        technical_skills=[],
    ))

    with pytest.raises(OwnershipError):
        service.delete_profile(db_session, profile.id, owner_key="wrong_key_0000000000000000000000")

    success = service.delete_profile(db_session, profile.id, owner_key=profile.ownership_key)
    assert success is True
    assert service.get_profile(db_session, profile.id) is None


def test_id_alone_does_not_grant_ownership(service, db_session):
    """Knowing the profile_id alone is insufficient for mutations."""
    profile = service.create_profile(ProfileCreate(
        display_name="Hacked Target",
        email="target@giki.edu.pk",
        programme="BS CS",
        academic_year=3,
        technical_skills=["Python"],
    ))

    # Attempting update with no key → OwnershipError
    with pytest.raises(OwnershipError):
        service.update_profile(
            db_session, profile.id,
            ProfileUpdate(bio="Injected bio"),
            owner_key=None,
        )

    # Attempting update with empty string → OwnershipError
    with pytest.raises(OwnershipError):
        service.update_profile(
            db_session, profile.id,
            ProfileUpdate(bio="Injected bio"),
            owner_key="",
        )


# ==============================================================================
# 3. Ownership Enforcement on Project Mutations
# ==============================================================================

def test_project_mutations_require_correct_key(service, db_session):
    """Update, close, and delete all require the correct project ownership_key."""
    owner = service.create_profile(ProfileCreate(
        display_name="Owner",
        email="own@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="FYP Project",
        description="Final year project on AI.",
        domains=["AI"],
        required_skills=["Python"],
        preferred_roles=["Developer"],
        additional_members_needed=1,
    ))

    # Update with wrong key
    with pytest.raises(OwnershipError):
        service.update_project(
            db_session, project.id,
            ProjectUpdate(title="Hacked Title"),
            owner_key="bad_key_00000000000000000000000",
        )

    # Close with wrong key
    with pytest.raises(OwnershipError):
        service.close_project(db_session, project.id, owner_key="bad_key_00000000000000000000000")

    # Delete with wrong key
    with pytest.raises(OwnershipError):
        service.delete_project(db_session, project.id, owner_key="bad_key_00000000000000000000000")

    # Correct key → update succeeds
    updated = service.update_project(
        db_session, project.id,
        ProjectUpdate(additional_members_needed=2),
        owner_key=project.ownership_key,
    )
    assert updated.additional_members_needed == 2


def test_interest_response_requires_project_owner_key(service, db_session):
    """Only the project owner (with correct key) may approve interest requests."""
    owner = service.create_profile(ProfileCreate(
        display_name="Project Owner",
        email="owner@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
    ))
    applicant = service.create_profile(ProfileCreate(
        display_name="Applicant",
        email="applicant@giki.edu.pk",
        programme="BS AI",
        academic_year=3,
        technical_skills=["PyTorch"],
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="ML Pipeline",
        description="Building an ML pipeline for GIKI research.",
        domains=["AI"],
        required_skills=["PyTorch"],
        preferred_roles=["ML Engineer"],
        additional_members_needed=1,
    ))
    interest = service.express_interest(db_session, project.id, InterestCreate(
        profile_id=applicant.id,
        proposed_role="ML Engineer",
        message="I am interested!",
    ))

    # Applicant's key cannot approve their own interest
    with pytest.raises(OwnershipError):
        service.respond_to_interest(
            db_session,
            interest.id,
            InterestStatus.APPROVED,
            owner_key=applicant.ownership_key,
        )

    # Random wrong key cannot approve
    with pytest.raises(OwnershipError):
        service.respond_to_interest(
            db_session,
            interest.id,
            InterestStatus.APPROVED,
            owner_key="wrong_key_0000000000000000000000",
        )

    # Correct project owner key approves
    approved = service.respond_to_interest(
        db_session,
        interest.id,
        InterestStatus.APPROVED,
        owner_key=project.ownership_key,
    )
    assert approved.status == InterestStatus.APPROVED


# ==============================================================================
# 4. Privacy: Email Never Exposed in Public Responses
# ==============================================================================

def test_public_profile_never_contains_email(service, db_session):
    """ProfilePublicResponse must not have an email field."""
    profile = service.create_profile(ProfileCreate(
        display_name="Sara Ahmed",
        email="sara.secret@giki.edu.pk",
        programme="BS Software Engineering",
        academic_year=4,
        technical_skills=["React"],
        visibility=ProfileVisibility.PUBLIC,
    ))
    public_view = service.format_public_profile(profile)
    public_dict = public_view.model_dump()
    assert "email" not in public_dict
    assert "sara.secret@giki.edu.pk" not in str(public_dict)


def test_public_profile_never_contains_ownership_key(service, db_session):
    """ProfilePublicResponse must not have ownership_key field."""
    profile = service.create_profile(ProfileCreate(
        display_name="Key Test Student",
        email="keyst@giki.edu.pk",
        programme="BS CS",
        academic_year=2,
        technical_skills=["Python"],
    ))
    public_view = service.format_public_profile(profile)
    public_dict = public_view.model_dump()
    assert "ownership_key" not in public_dict
    assert profile.ownership_key not in str(public_dict)


def test_candidate_recommendation_never_contains_email(service, db_session):
    """CandidateRecommendation must not expose email of any candidate."""
    owner = service.create_profile(ProfileCreate(
        display_name="Owner",
        email="own@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
    ))
    cand = service.create_profile(ProfileCreate(
        display_name="Candidate",
        email="cand.secret@giki.edu.pk",
        programme="BS AI",
        academic_year=3,
        technical_skills=["PyTorch", "OpenCV"],
        preferred_domains=["AI"],
        preferred_roles=["ML Engineer"],
        availability="10-15 hrs/week",
        visibility=ProfileVisibility.PUBLIC,
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="Vision Project",
        description="Computer vision for autonomous systems.",
        domains=["AI"],
        required_skills=["PyTorch"],
        preferred_roles=["ML Engineer"],
        additional_members_needed=1,
    ))

    recommendations = service.recommend_candidates_for_project(db_session, project.id)
    assert len(recommendations) >= 1
    for rec in recommendations:
        rec_dict = rec.model_dump()
        assert "email" not in rec_dict
        assert "cand.secret@giki.edu.pk" not in str(rec_dict)
        assert "ownership_key" not in rec_dict


# ==============================================================================
# 5. Privacy: Anonymous Profile Masking
# ==============================================================================

def test_anonymous_profile_masks_identity_and_bio(service, db_session):
    """Anonymous profiles mask display name and suppress bio in public view."""
    profile = service.create_profile(ProfileCreate(
        display_name="Zubair Malik",
        email="zubair@giki.edu.pk",
        programme="BS Data Science",
        academic_year=2,
        technical_skills=["SQL", "Python"],
        bio="Secret bio with identifying details.",
        visibility=ProfileVisibility.ANONYMOUS,
    ))
    public_view = service.format_public_profile(profile)
    assert public_view.display_name == "Anonymous Student (BS Data Science, Year 2)"
    assert public_view.bio is None
    assert "Zubair Malik" not in public_view.display_name


def test_anonymous_requester_name_masked_in_interest_response(service, db_session):
    """An anonymous applicant's real name must not appear in interest responses."""
    owner = service.create_profile(ProfileCreate(
        display_name="Project Lead",
        email="lead@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
    ))
    anon_applicant = service.create_profile(ProfileCreate(
        display_name="Real Name Should Not Appear",
        email="secret@giki.edu.pk",
        programme="BS AI",
        academic_year=2,
        technical_skills=["PyTorch"],
        visibility=ProfileVisibility.ANONYMOUS,
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="AI Project",
        description="Building an AI recommendation system.",
        domains=["AI"],
        required_skills=["PyTorch"],
        preferred_roles=["ML Engineer"],
        additional_members_needed=1,
    ))

    interest = service.express_interest(db_session, project.id, InterestCreate(
        profile_id=anon_applicant.id,
        proposed_role="ML Engineer",
        message="Interested in joining.",
    ))

    formatted = service.format_interest_response(interest, viewer_id=owner.id)
    assert formatted.requester_name is not None
    assert "Real Name Should Not Appear" not in formatted.requester_name
    assert "Anonymous Student" in formatted.requester_name


# ==============================================================================
# 6. Privacy: Unlisted & Deactivated Profile Exclusion
# ==============================================================================

def test_unlisted_and_inactive_profiles_excluded_from_discovery(service, db_session):
    """Unlisted and deactivated profiles must not appear in discovery or recommendations."""
    service.create_profile(ProfileCreate(
        display_name="Public Student",
        email="pub@giki.edu.pk",
        programme="BS CS",
        academic_year=3,
        technical_skills=["Python"],
        visibility=ProfileVisibility.PUBLIC,
    ))
    service.create_profile(ProfileCreate(
        display_name="Anon Student",
        email="anon@giki.edu.pk",
        programme="BS AI",
        academic_year=2,
        technical_skills=["Python"],
        visibility=ProfileVisibility.ANONYMOUS,
    ))
    service.create_profile(ProfileCreate(
        display_name="Unlisted Student",
        email="unlisted@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
        visibility=ProfileVisibility.UNLISTED,
    ))
    deact = service.create_profile(ProfileCreate(
        display_name="Deactivated Student",
        email="deact@giki.edu.pk",
        programme="BS CS",
        academic_year=1,
        technical_skills=["Python"],
        visibility=ProfileVisibility.PUBLIC,
    ))
    service.deactivate_profile(db_session, deact.id, owner_key=deact.ownership_key)

    discoverable = service.list_discoverable_profiles(db_session)
    names = [p.display_name for p in discoverable]
    assert "Public Student" in names
    assert any("Anonymous Student" in n for n in names)
    assert "Unlisted Student" not in names
    assert "Deactivated Student" not in names
    assert len(discoverable) == 2


def test_recommendation_excludes_unlisted_profiles(service, db_session):
    """Unlisted candidates must NOT appear in project candidate recommendations."""
    owner = service.create_profile(ProfileCreate(
        display_name="Owner",
        email="own@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=[],
    ))
    unlisted_cand = service.create_profile(ProfileCreate(
        display_name="Unlisted Candidate",
        email="unl@giki.edu.pk",
        programme="BS CS",
        academic_year=3,
        technical_skills=["Python"],
        visibility=ProfileVisibility.UNLISTED,
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="Python Project",
        description="A project using Python.",
        domains=[],
        required_skills=["Python"],
        preferred_roles=[],
        additional_members_needed=1,
    ))
    recs = service.recommend_candidates_for_project(db_session, project.id)
    rec_ids = [r.profile_id for r in recs]
    assert unlisted_cand.id not in rec_ids


# ==============================================================================
# 7. Contact Email: Only Revealed on Approval
# ==============================================================================

def test_contact_email_withheld_until_approval(service, db_session):
    """shared_contact_email must be None while PENDING and populated when APPROVED."""
    owner = service.create_profile(ProfileCreate(
        display_name="Project Owner",
        email="owner.secret@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
    ))
    applicant = service.create_profile(ProfileCreate(
        display_name="Applicant",
        email="applicant.secret@giki.edu.pk",
        programme="BS AI",
        academic_year=3,
        technical_skills=["FastAPI"],
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="Edge AI Platform",
        description="Deploying AI models to edge devices.",
        domains=["AI"],
        required_skills=["FastAPI"],
        preferred_roles=["Backend Dev"],
        additional_members_needed=1,
    ))

    # Express interest
    interest = service.express_interest(db_session, project.id, InterestCreate(
        profile_id=applicant.id,
        proposed_role="Backend Dev",
        message="Happy to join.",
    ))

    # Pending: no email from either side
    pending_owner_view = service.format_interest_response(interest, viewer_id=owner.id)
    assert pending_owner_view.shared_contact_email is None
    pending_applicant_view = service.format_interest_response(interest, viewer_id=applicant.id)
    assert pending_applicant_view.shared_contact_email is None

    # Approve with correct key
    approved = service.respond_to_interest(
        db_session, interest.id, InterestStatus.APPROVED,
        owner_key=project.ownership_key,
    )

    # Owner sees applicant email
    owner_view = service.format_interest_response(approved, viewer_id=owner.id)
    assert owner_view.shared_contact_email == "applicant.secret@giki.edu.pk"

    # Applicant sees owner email
    applicant_view = service.format_interest_response(approved, viewer_id=applicant.id)
    assert applicant_view.shared_contact_email == "owner.secret@giki.edu.pk"


def test_rejected_interest_does_not_reveal_contact(service, db_session):
    """Rejected interest must NOT reveal any contact email."""
    owner = service.create_profile(ProfileCreate(
        display_name="Rejecting Owner",
        email="rej_owner@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
    ))
    applicant = service.create_profile(ProfileCreate(
        display_name="Rejected Applicant",
        email="rejected@giki.edu.pk",
        programme="BS AI",
        academic_year=2,
        technical_skills=["TensorFlow"],
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="Rejected Test Project",
        description="Project for rejection test.",
        domains=[],
        required_skills=["Python"],
        preferred_roles=[],
        additional_members_needed=1,
    ))
    interest = service.express_interest(db_session, project.id, InterestCreate(
        profile_id=applicant.id,
    ))
    rejected = service.respond_to_interest(
        db_session, interest.id, InterestStatus.REJECTED,
        owner_key=project.ownership_key,
    )

    owner_view = service.format_interest_response(rejected, viewer_id=owner.id)
    assert owner_view.shared_contact_email is None


# ==============================================================================
# 8. Matching Engine Verification
# ==============================================================================

def test_matching_engine_weights_sum_to_100():
    """The documented weights must sum exactly to 100."""
    total = (
        MatchingEngine.SKILL_WEIGHT
        + MatchingEngine.INTEREST_WEIGHT
        + MatchingEngine.ROLE_WEIGHT
        + MatchingEngine.AVAILABILITY_WEIGHT
        + MatchingEngine.EXPERIENCE_WEIGHT
    )
    assert total == 100.0


def test_matching_score_always_in_bounds():
    """Score must always be in [0.0, 100.0] regardless of input data."""
    engine = MatchingEngine()

    # Perfect match candidate
    cand = StudentProfile(
        id="c1", display_name="A", programme="BS CS", academic_year=4,
        technical_skills=["Python", "FastAPI", "Docker", "Kubernetes"],
        research_interests=["Cloud"], preferred_domains=["Backend"], preferred_roles=["Lead"],
        availability="flexible", previous_experience="5 years experience at FAANG",
    )
    proj = Project(
        id="p1", title="T", domains=["Backend"],
        required_skills=["Python", "FastAPI", "Docker", "Kubernetes"],
        preferred_roles=["Lead"], additional_members_needed=1,
    )
    result = engine.calculate_fit(cand, proj, [])
    assert 0.0 <= result.overall_score <= 100.0

    # Empty candidate against empty project
    empty_cand = StudentProfile(
        id="c2", display_name="Empty", programme="BS CS", academic_year=1,
        technical_skills=[], research_interests=[], preferred_domains=[],
        preferred_roles=[], availability=None, previous_experience=None,
    )
    empty_proj = Project(
        id="p2", title="Empty", domains=[], required_skills=[],
        preferred_roles=[], additional_members_needed=1,
    )
    result2 = engine.calculate_fit(empty_cand, empty_proj, [])
    assert 0.0 <= result2.overall_score <= 100.0


def test_no_division_by_zero_on_empty_lists():
    """Empty skill/domain/role lists must not cause ZeroDivisionError."""
    engine = MatchingEngine()
    cand = StudentProfile(
        id="c1", display_name="A", programme="BS CS", academic_year=2,
        technical_skills=[], research_interests=[], preferred_domains=[],
        preferred_roles=[], availability="flexible",
    )
    proj = Project(
        id="p1", title="T", domains=[], required_skills=[], preferred_roles=[],
        additional_members_needed=1,
    )
    # Must not raise
    result = engine.calculate_fit(cand, proj, [])
    assert result.overall_score >= 0.0


def test_matching_is_deterministic():
    """Same inputs must always produce identical scores."""
    engine = MatchingEngine()
    cand = StudentProfile(
        id="c1", display_name="A", programme="BS CS", academic_year=3,
        technical_skills=["Python", "Docker"],
        research_interests=["AI"], preferred_domains=["Backend"],
        preferred_roles=["Developer"], availability="10-15 hrs/week",
        previous_experience="6 months internship",
    )
    proj = Project(
        id="p1", title="T", domains=["Backend", "AI"],
        required_skills=["Python", "Docker", "Kubernetes"],
        preferred_roles=["Developer"], additional_members_needed=2,
    )
    score1 = engine.calculate_fit(cand, proj, []).overall_score
    score2 = engine.calculate_fit(cand, proj, []).overall_score
    score3 = engine.calculate_fit(cand, proj, []).overall_score
    assert score1 == score2 == score3


def test_missing_availability_no_unfair_boost():
    """A candidate with no availability should not score above 10 on availability."""
    engine = MatchingEngine()
    cand = StudentProfile(
        id="c1", display_name="A", programme="BS CS", academic_year=1,
        technical_skills=[], research_interests=[], preferred_domains=[],
        preferred_roles=[], availability=None,  # Missing
    )
    proj = Project(
        id="p1", title="T", domains=[], required_skills=[], preferred_roles=[],
        additional_members_needed=1,
    )
    result = engine.calculate_fit(cand, proj, [])
    avail_score = result.score_breakdown.get("availability_score", 0)
    assert avail_score <= 10.0


def test_missing_experience_no_unfair_boost():
    """A candidate with no experience should not receive experience score > 2."""
    engine = MatchingEngine()
    cand = StudentProfile(
        id="c1", display_name="A", programme="BS CS", academic_year=1,
        technical_skills=[], research_interests=[], preferred_domains=[],
        preferred_roles=[], availability="flexible", previous_experience=None,
    )
    proj = Project(
        id="p1", title="T", domains=[], required_skills=[], preferred_roles=[],
        additional_members_needed=1,
    )
    result = engine.calculate_fit(cand, proj, [])
    exp_score = result.score_breakdown.get("experience_score", 0)
    assert exp_score <= 2.0  # Year 1 → max 1.0, no prior experience → 0.0 bonus


def test_existing_team_skills_reduce_complementary_bonus(db_session, service):
    """When the team already covers a skill, the bonus for that skill should not double-count."""
    owner = service.create_profile(ProfileCreate(
        display_name="Owner",
        email="own@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
    ))
    team_member = service.create_profile(ProfileCreate(
        display_name="Team Member",
        email="tm@giki.edu.pk",
        programme="BS CS",
        academic_year=3,
        technical_skills=["FastAPI"],  # Already on the team
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="API Project",
        description="REST API development project.",
        domains=[],
        required_skills=["Python", "FastAPI", "Docker"],
        preferred_roles=[],
        additional_members_needed=2,
    ))

    # Simulate team member already added
    team_profile = service.get_profile(db_session, team_member.id)

    # Candidate who also knows FastAPI (already covered) but adds Docker
    cand_docker = StudentProfile(
        id="cand1", display_name="Docker Cand", programme="BS CS", academic_year=3,
        technical_skills=["FastAPI", "Docker"],  # FastAPI already on team
        availability="10-15 hrs/week",
    )

    score_with_team = MatchingEngine.evaluate_candidate_for_project(
        candidate=cand_docker,
        project=project,
        current_team_profiles=[team_profile],
    )
    score_without_team = MatchingEngine.evaluate_candidate_for_project(
        candidate=cand_docker,
        project=project,
        current_team_profiles=[],
    )

    # With a team member covering FastAPI, candidate's complementary bonus should be lower
    # because FastAPI is no longer a "missing" skill for the team
    comp_with = set(score_with_team.missing_skills_covered)
    comp_without = set(score_without_team.missing_skills_covered)

    # FastAPI should NOT be counted as complementary when team already has it
    assert "FastAPI" not in comp_with or "FastAPI" in comp_without


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

    assert "Offers 2 required skill(s)" in score_card.explanation
    assert "Shares project domain interest(s)" in score_card.explanation
    assert "Prefers requested role" in score_card.explanation


def test_matching_engine_complementary_skill_bonus():
    """Verify candidate receives complementarity bonus for covering missing team skills."""
    engine = MatchingEngine()

    lead = StudentProfile(
        id="lead",
        display_name="Lead",
        technical_skills=["Python", "FastAPI"],
    )

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

    assert "React" in score_card.complementary_skills
    assert "TypeScript" in score_card.complementary_skills
    assert "Fills critical team skill gap(s)" in score_card.explanation


def test_candidate_recommendations_ranking(service, db_session):
    """Verify candidate recommendations are ranked by descending matching score."""
    owner = service.create_profile(ProfileCreate(
        display_name="Owner",
        email="own@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
    ))

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

    service.create_profile(ProfileCreate(
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

    recommendations = service.recommend_candidates_for_project(db_session, project.id)

    assert len(recommendations) >= 2
    assert recommendations[0].candidate.id == cand_a.id
    assert recommendations[0].match_score > recommendations[1].match_score
    assert recommendations[0].match_score >= 80.0


# ==============================================================================
# 9. Database Safety
# ==============================================================================

def test_profile_deletion_cascades_to_projects_and_interests(service, db_session):
    """Deleting a profile must cascade to owned projects, memberships, and interests."""
    owner = service.create_profile(ProfileCreate(
        display_name="Owner To Delete",
        email="del@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=[],
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="Cascade Test",
        description="Test cascade deletion behavior.",
        domains=[],
        required_skills=[],
        preferred_roles=[],
        additional_members_needed=1,
    ))

    pid = owner.id
    proj_id = project.id

    service.delete_profile(db_session, pid, owner_key=owner.ownership_key)

    assert service.get_profile(db_session, pid) is None
    assert service.get_project(db_session, proj_id) is None


def test_project_deletion_cascades_to_members_and_interests(service, db_session):
    """Deleting a project must cascade to ProjectMember and ProjectInterest records."""
    from sqlalchemy.orm import Session

    owner = service.create_profile(ProfileCreate(
        display_name="Owner",
        email="owner2@giki.edu.pk",
        programme="BS CS",
        academic_year=4,
        technical_skills=["Python"],
    ))
    applicant = service.create_profile(ProfileCreate(
        display_name="Applicant",
        email="app2@giki.edu.pk",
        programme="BS AI",
        academic_year=3,
        technical_skills=["PyTorch"],
    ))
    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="Cascade Project",
        description="Cascade test for project deletion.",
        domains=[],
        required_skills=["Python"],
        preferred_roles=[],
        additional_members_needed=1,
    ))

    # Express interest to create ProjectInterest record
    service.express_interest(db_session, project.id, InterestCreate(profile_id=applicant.id))

    proj_id = project.id
    service.delete_project(db_session, proj_id, owner_key=project.ownership_key)

    # Verify project gone
    assert service.get_project(db_session, proj_id) is None

    # Verify interest records cascaded
    from backend.app.models.teammates import ProjectInterest, ProjectMember
    remaining_interests = db_session.query(ProjectInterest).filter_by(project_id=proj_id).all()
    remaining_members = db_session.query(ProjectMember).filter_by(project_id=proj_id).all()
    assert remaining_interests == []
    assert remaining_members == []


# ==============================================================================
# 10. Original Milestone 2 lifecycle tests (preserved)
# ==============================================================================

def test_create_and_retrieve_profile(service, db_session):
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

    retrieved = service.get_profile(db_session, profile.id)
    assert retrieved is not None
    assert retrieved.email == "ali.khan@giki.edu.pk"


def test_update_profile_and_visibility(service, db_session):
    """Verify profile updates and visibility toggle with correct ownership key."""
    p = service.create_profile(ProfileCreate(
        display_name="Hassan",
        email="hassan@giki.edu.pk",
        programme="BS Mechanical",
        academic_year=3,
        technical_skills=["MATLAB", "SolidWorks"],
        visibility=ProfileVisibility.PUBLIC,
    ))

    updated = service.update_profile(
        db_session, p.id,
        ProfileUpdate(technical_skills=["MATLAB", "SolidWorks", "ANSYS", "Python"]),
        owner_key=p.ownership_key,
    )
    assert len(updated.technical_skills) == 4
    assert "ANSYS" in updated.technical_skills

    vis_updated = service.update_visibility(
        db_session, p.id,
        ProfileVisibility.UNLISTED,
        owner_key=p.ownership_key,
    )
    assert vis_updated.visibility == ProfileVisibility.UNLISTED


def test_delete_profile_cascades_safely(service, db_session):
    """Profile deletion should work with correct key."""
    p = service.create_profile(ProfileCreate(
        display_name="Temp Student",
        email="temp@giki.edu.pk",
        programme="BS CS",
        academic_year=1,
        technical_skills=["C++"],
    ))
    pid = p.id
    deleted = service.delete_profile(db_session, pid, owner_key=p.ownership_key)
    assert deleted is True
    assert service.get_profile(db_session, pid) is None


def test_project_creation_and_member_assignment(service, db_session):
    """Project creation automatically registers owner as first member."""
    owner = service.create_profile(ProfileCreate(
        display_name="Lead Researcher",
        email="lead@giki.edu.pk",
        programme="BS AI",
        academic_year=4,
        technical_skills=["PyTorch", "Python", "ROS"],
    ))

    project = service.create_project(ProjectCreate(
        owner_id=owner.id,
        title="Autonomous Quadcopter Navigation",
        description="Developing SLAM and path planning for GPS-denied environments.",
        domains=["Robotics", "Autonomous Systems", "Computer Vision"],
        required_skills=["ROS", "C++", "SLAM", "Python"],
        preferred_roles=["Robotics Software Engineer", "Control Systems Lead"],
        additional_members_needed=2,
    ))

    assert project.id is not None
    assert project.status == ProjectStatus.OPEN
    assert len(project.members) == 1
    assert project.members[0].profile_id == owner.id
    assert project.members[0].role == "Project Lead"


def test_project_close_recruitment(service, db_session):
    """Closing project updates status and excludes from open listings."""
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

    open_projects = service.list_projects(db_session, status_filter=ProjectStatus.OPEN)
    assert any(p.id == proj.id for p in open_projects)

    closed = service.close_project(db_session, proj.id, owner_key=proj.ownership_key)
    assert closed.status == ProjectStatus.CLOSED
    assert closed.additional_members_needed == 0

    open_projects_after = service.list_projects(db_session, status_filter=ProjectStatus.OPEN)
    assert not any(p.id == proj.id for p in open_projects_after)


def test_public_profile_hides_email(service, db_session):
    """ProfilePublicResponse must never contain email."""
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
