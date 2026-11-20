"""
REST API routes for GIKI Nexus Student Project Teammate Finder (Module B).
Provides voluntary student profiles, project recruiting, explainable matching,
privacy controls, and consent-based contact workflows.

PROTOTYPE AUTHENTICATION NOTICE
================================
Mutation endpoints (PUT, PATCH, POST /deactivate, DELETE, POST /close,
POST /interests/respond) require an X-Ownership-Key header containing the
ownership key issued at resource creation.

This is NOT institutional authentication. See backend/app/models/teammates.py
for the full prototype authentication notice.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.services.teammate_service import TeammateService, OwnershipError
from backend.app.models.teammates import (
    ProfileVisibility,
    ProjectStatus,
    InterestStatus,
)
from backend.app.schemas.teammates import (
    ProfileCreate,
    ProfileUpdate,
    ProfileVisibilityUpdate,
    ProfilePublicResponse,
    ProfilePrivateResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectCreateResponse,
    InterestCreate,
    InterestResponse,
    InterestRespondRequest,
    CandidateRecommendation,
    ProjectRecommendation,
)

router = APIRouter(prefix="/teammates", tags=["Teammate Finder"])
service = TeammateService()
logger = logging.getLogger(__name__)


def _ownership_error_to_http(exc: OwnershipError) -> HTTPException:
    """Convert an OwnershipError to a 403 HTTP response without leaking key details."""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=str(exc),
    )


# -------------------------------------------------------------------------
# Student Profile Endpoints
# -------------------------------------------------------------------------

@router.post(
    "/profiles",
    response_model=ProfilePrivateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create student profile",
    description=(
        "Create a new voluntary student profile. "
        "Returns a one-time ownership_key that must be stored securely by the creator. "
        "This key is required for all subsequent profile mutations."
    ),
)
def create_profile(
    data: ProfileCreate,
    db: Session = Depends(get_db),
) -> ProfilePrivateResponse:
    """Create a new voluntary student profile."""
    profile = service.create_profile(db, data)
    return ProfilePrivateResponse(
        id=profile.id,
        display_name=profile.display_name,
        email=profile.email,
        ownership_key=profile.ownership_key,
        programme=profile.programme,
        academic_year=profile.academic_year,
        technical_skills=profile.technical_skills or [],
        research_interests=profile.research_interests or [],
        preferred_domains=profile.preferred_domains or [],
        preferred_roles=profile.preferred_roles or [],
        availability=profile.availability,
        previous_experience=profile.previous_experience,
        bio=profile.bio,
        project_ideas=profile.project_ideas,
        visibility=profile.visibility,
        contact_preference=profile.contact_preference,
        is_active=profile.is_active,
        is_anonymous=profile.visibility == ProfileVisibility.ANONYMOUS,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get(
    "/profiles",
    response_model=Dict[str, Any],
    summary="Discover active student profiles",
)
def list_profiles(
    programme: Optional[str] = Query(None, description="Filter by degree programme"),
    academic_year: Optional[int] = Query(None, ge=1, le=4, description="Filter by year (1-4)"),
    skill: Optional[str] = Query(None, description="Filter by technical skill"),
    domain: Optional[str] = Query(None, description="Filter by domain interest"),
    role: Optional[str] = Query(None, description="Filter by preferred role"),
    search: Optional[str] = Query(None, description="Search keyword in bio/name/skills"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve discoverable student profiles. UNLISTED and inactive profiles are excluded."""
    return service.list_discoverable_profiles(
        db,
        programme=programme,
        academic_year=academic_year,
        skill=skill,
        domain=domain,
        role=role,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/profiles/{profile_id}",
    response_model=ProfilePublicResponse,
    summary="Get student profile (public view)",
)
def get_profile(
    profile_id: str,
    db: Session = Depends(get_db),
) -> ProfilePublicResponse:
    """
    Retrieve a public, privacy-sanitized profile view.
    - Email is never returned.
    - Anonymous profiles have display name masked and bio suppressed.
    """
    profile = service.get_profile(db, profile_id)
    if not profile or not profile.is_active:
        raise HTTPException(status_code=404, detail=f"Student profile '{profile_id}' not found.")
    return service.format_public_profile(profile)


@router.put(
    "/profiles/{profile_id}",
    response_model=ProfilePublicResponse,
    summary="Update student profile (owner only)",
)
def update_profile(
    profile_id: str,
    data: ProfileUpdate,
    x_ownership_key: Optional[str] = Header(None, alias="X-Ownership-Key"),
    db: Session = Depends(get_db),
) -> ProfilePublicResponse:
    """
    Update profile fields. Requires the X-Ownership-Key header issued at profile creation.
    Returns 403 if the key is missing or incorrect.
    """
    try:
        profile = service.update_profile(db, profile_id, data, owner_key=x_ownership_key)
    except OwnershipError as exc:
        raise _ownership_error_to_http(exc)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student profile '{profile_id}' not found.")
    return service.format_public_profile(profile)


@router.patch(
    "/profiles/{profile_id}/visibility",
    response_model=ProfilePublicResponse,
    summary="Update profile visibility (owner only)",
)
def update_visibility(
    profile_id: str,
    data: ProfileVisibilityUpdate,
    x_ownership_key: Optional[str] = Header(None, alias="X-Ownership-Key"),
    db: Session = Depends(get_db),
) -> ProfilePublicResponse:
    """
    Toggle visibility between PUBLIC, ANONYMOUS, and UNLISTED.
    Requires the X-Ownership-Key header. Returns 403 if key is wrong.
    """
    try:
        profile = service.update_visibility(db, profile_id, data.visibility, owner_key=x_ownership_key)
    except OwnershipError as exc:
        raise _ownership_error_to_http(exc)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student profile '{profile_id}' not found.")
    return service.format_public_profile(profile)


# Alias for test suite compatibility
update_profile_visibility = update_visibility


@router.post(
    "/profiles/{profile_id}/deactivate",
    summary="Deactivate student profile (owner only)",
)
def deactivate_profile(
    profile_id: str,
    x_ownership_key: Optional[str] = Header(None, alias="X-Ownership-Key"),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Deactivate profile, removing it from all public discovery.
    Requires the X-Ownership-Key header. Returns 403 if key is wrong.
    """
    try:
        success = service.deactivate_profile(db, profile_id, owner_key=x_ownership_key)
    except OwnershipError as exc:
        raise _ownership_error_to_http(exc)
    if not success:
        raise HTTPException(status_code=404, detail=f"Student profile '{profile_id}' not found.")
    return {"status": "deactivated", "profile_id": profile_id}


@router.delete(
    "/profiles/{profile_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete student profile (owner only)",
)
def delete_profile(
    profile_id: str,
    x_ownership_key: Optional[str] = Header(None, alias="X-Ownership-Key"),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Permanently delete a student profile.
    Requires the X-Ownership-Key header. Returns 403 if key is wrong.
    """
    try:
        success = service.delete_profile(db, profile_id, owner_key=x_ownership_key)
    except OwnershipError as exc:
        raise _ownership_error_to_http(exc)
    if not success:
        raise HTTPException(status_code=404, detail=f"Student profile '{profile_id}' not found.")
    return {"status": "deleted", "profile_id": profile_id}


# -------------------------------------------------------------------------
# Project & Team Endpoints
# -------------------------------------------------------------------------

@router.post(
    "/projects",
    response_model=ProjectCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project team",
    description=(
        "Create a new project. Returns a one-time ownership_key that must be stored securely. "
        "Required for update, close, delete, and interest-approval operations."
    ),
)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectCreateResponse:
    """Create a new project recruitment post with required skills and open roles."""
    try:
        project = service.create_project(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    proj_resp = service.format_project_response(project)
    return ProjectCreateResponse(
        **proj_resp.model_dump(),
        ownership_key=project.ownership_key,
    )


@router.get(
    "/projects",
    response_model=Dict[str, Any],
    summary="List recruitment projects",
)
def list_projects(
    domain: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[ProjectStatus] = Query(ProjectStatus.OPEN),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve recruiting projects looking for teammates."""
    return service.list_projects(
        db, domain=domain, skill=skill, role=role,
        status=status, search=search, skip=skip, limit=limit,
    )


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Get project details",
)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Retrieve project details, required skills, and current team members."""
    project = service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return service.format_project_response(project)


@router.put(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Update project details (owner only)",
)
def update_project(
    project_id: str,
    data: ProjectUpdate,
    x_ownership_key: Optional[str] = Header(None, alias="X-Ownership-Key"),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Update project details or needed member count. Requires X-Ownership-Key."""
    try:
        project = service.update_project(db, project_id, data, owner_key=x_ownership_key)
    except OwnershipError as exc:
        raise _ownership_error_to_http(exc)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return service.format_project_response(project)


@router.post(
    "/projects/{project_id}/close",
    response_model=ProjectResponse,
    summary="Close project recruitment (owner only)",
)
def close_project(
    project_id: str,
    x_ownership_key: Optional[str] = Header(None, alias="X-Ownership-Key"),
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Close recruitment for a project. Requires X-Ownership-Key."""
    try:
        project = service.close_project(db, project_id, owner_key=x_ownership_key)
    except OwnershipError as exc:
        raise _ownership_error_to_http(exc)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return service.format_project_response(project)


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project (owner only)",
)
def delete_project(
    project_id: str,
    x_ownership_key: Optional[str] = Header(None, alias="X-Ownership-Key"),
    db: Session = Depends(get_db),
):
    """Permanently delete a project. Requires X-Ownership-Key."""
    try:
        success = service.delete_project(db, project_id, owner_key=x_ownership_key)
    except OwnershipError as exc:
        raise _ownership_error_to_http(exc)
    if not success:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")


# -------------------------------------------------------------------------
# Discovery & Explainable Recommendations Endpoints
# -------------------------------------------------------------------------

@router.get(
    "/discover",
    response_model=Dict[str, Any],
    summary="General discovery hub",
)
def discover_hub(
    query: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Unified discovery hub returning matching candidates and open projects."""
    profiles_res = service.list_discoverable_profiles(db, skill=skill, domain=domain, search=query, limit=10)
    projects_res = service.list_projects(db, skill=skill, domain=domain, search=query, limit=10)
    return {
        "candidates": profiles_res["items"],
        "projects": projects_res["items"],
        "total_candidates": profiles_res["total"],
        "total_projects": projects_res["total"],
    }


@router.get(
    "/projects/{project_id}/recommendations",
    response_model=List[CandidateRecommendation],
    summary="Explainable candidate recommendations for a project",
)
def recommend_candidates_for_project(
    project_id: str,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> List[CandidateRecommendation]:
    """
    Returns candidates ranked by transparent rule-based scoring.
    Does not include any email addresses or ownership keys in responses.
    """
    project = service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    if project.status != ProjectStatus.OPEN:
        raise HTTPException(status_code=400, detail="Cannot generate recommendations for a closed project.")
    return service.recommend_candidates_for_project(db, project_id, limit=limit)


@router.get(
    "/profiles/{profile_id}/recommendations",
    response_model=List[ProjectRecommendation],
    summary="Explainable project recommendations for a student",
)
def recommend_projects_for_student(
    profile_id: str,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> List[ProjectRecommendation]:
    """Returns open project recommendations for a student seeking a team."""
    profile = service.get_profile(db, profile_id)
    if not profile or not profile.is_active:
        raise HTTPException(status_code=404, detail=f"Student profile '{profile_id}' not found.")
    return service.recommend_projects_for_student(db, profile_id, limit=limit)


# -------------------------------------------------------------------------
# Interest & Consent-Based Contact Workflow Endpoints
# -------------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/interest",
    response_model=InterestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Express interest in joining a project",
)
def express_interest(
    project_id: str,
    data: InterestCreate,
    db: Session = Depends(get_db),
) -> InterestResponse:
    """
    Submit an expression of interest to collaborate on a project.
    Contact emails are NOT revealed until the project owner explicitly approves.
    """
    try:
        interest = service.express_interest(db, project_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return service.format_interest_response(interest, viewer_id=None)


@router.get(
    "/projects/{project_id}/interests",
    response_model=List[InterestResponse],
    summary="View interest requests for project (owner only)",
)
def list_project_interests(
    project_id: str,
    x_ownership_key: Optional[str] = Header(None, alias="X-Ownership-Key"),
    db: Session = Depends(get_db),
) -> List[InterestResponse]:
    """
    Project owner view of candidates who expressed interest.
    Requires X-Ownership-Key to prevent unauthorized snooping on applicants.
    """
    project = service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    try:
        return service.list_project_interests(db, project_id, owner_key=x_ownership_key)
    except OwnershipError as exc:
        raise _ownership_error_to_http(exc)


@router.post(
    "/interests/{interest_id}/respond",
    response_model=InterestResponse,
    summary="Approve or reject collaboration request (project owner only)",
)
def respond_to_interest(
    interest_id: str,
    data: InterestRespondRequest,
    x_ownership_key: Optional[str] = Header(None, alias="X-Ownership-Key"),
    db: Session = Depends(get_db),
) -> InterestResponse:
    """
    Project owner approves or rejects an interest request.
    Requires X-Ownership-Key matching the project (not the applicant's profile).
    Upon approval, contact emails are mutually revealed to both parties.
    Returns 403 if key is wrong. Returns 400 if action is invalid.
    """
    try:
        action = data.validated_action()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        interest = service.respond_to_interest(db, interest_id, action, owner_key=x_ownership_key)
    except OwnershipError as exc:
        raise _ownership_error_to_http(exc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not interest:
        raise HTTPException(status_code=404, detail=f"Interest request '{interest_id}' not found.")

    # Reveal applicant's email to the owner side of the response
    return service.format_interest_response(interest, viewer_id=interest.project.owner_id)
