"""
REST API routes for GIKI Nexus Student Project Teammate Finder (Module B).
Provides voluntary student profiles, project recruiting, explainable matching,
privacy controls, and consent-based contact workflows.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.services.teammate_service import TeammateService
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
    InterestCreate,
    InterestResponse,
    InterestRespondRequest,
    CandidateRecommendation,
    ProjectRecommendation,
)

router = APIRouter(prefix="/teammates", tags=["Teammate Finder"])
service = TeammateService()


# -------------------------------------------------------------------------
# Student Profile Endpoints
# -------------------------------------------------------------------------

@router.post(
    "/profiles",
    response_model=ProfilePrivateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create student profile",
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
    """Retrieve discoverable student profiles (PUBLIC and ANONYMOUS, excluding UNLISTED)."""
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
    summary="Get student profile view",
)
def get_profile(
    profile_id: str,
    db: Session = Depends(get_db),
) -> ProfilePublicResponse:
    """Retrieve a public/sanitized profile view (masks anonymous profiles; omits email)."""
    profile = service.get_profile(db, profile_id)
    if not profile or not profile.is_active:
        raise HTTPException(status_code=404, detail=f"Student profile '{profile_id}' not found.")
    return service.format_public_profile(profile)


@router.put(
    "/profiles/{profile_id}",
    response_model=ProfilePublicResponse,
    summary="Update student profile",
)
def update_profile(
    profile_id: str,
    data: ProfileUpdate,
    db: Session = Depends(get_db),
) -> ProfilePublicResponse:
    """Update profile fields, skills, and availability."""
    profile = service.update_profile(db, profile_id, data)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student profile '{profile_id}' not found.")
    return service.format_public_profile(profile)


@router.patch(
    "/profiles/{profile_id}/visibility",
    response_model=ProfilePublicResponse,
    summary="Update profile visibility",
)
def update_visibility(
    profile_id: str,
    data: ProfileVisibilityUpdate,
    db: Session = Depends(get_db),
) -> ProfilePublicResponse:
    """Toggle visibility between PUBLIC, ANONYMOUS, and UNLISTED."""
    profile = service.update_visibility(db, profile_id, data.visibility)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student profile '{profile_id}' not found.")
    return service.format_public_profile(profile)


@router.delete(
    "/profiles/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete student profile",
)
def delete_profile(
    profile_id: str,
    db: Session = Depends(get_db),
):
    """Permanently delete a student profile."""
    success = service.delete_profile(db, profile_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Student profile '{profile_id}' not found.")


# -------------------------------------------------------------------------
# Project & Team Endpoints
# -------------------------------------------------------------------------

@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project team",
)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Create a new project recruitment post with required skills and open roles."""
    try:
        project = service.create_project(db, data)
        return service.format_project_response(project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/projects",
    response_model=Dict[str, Any],
    summary="List recruitment projects",
)
def list_projects(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    skill: Optional[str] = Query(None, description="Filter by required skill"),
    role: Optional[str] = Query(None, description="Filter by open role"),
    status: Optional[ProjectStatus] = Query(ProjectStatus.OPEN, description="Filter by project status"),
    search: Optional[str] = Query(None, description="Keyword search in title/description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve recruiting projects looking for teammates."""
    return service.list_projects(
        db,
        domain=domain,
        skill=skill,
        role=role,
        status=status,
        search=search,
        skip=skip,
        limit=limit,
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
    summary="Update project details",
)
def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Update project details or needed member count."""
    project = service.update_project(db, project_id, data)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return service.format_project_response(project)


@router.post(
    "/projects/{project_id}/close",
    response_model=ProjectResponse,
    summary="Close project recruitment",
)
def close_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectResponse:
    """Close recruitment for a project."""
    project = service.close_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return service.format_project_response(project)


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Permanently delete a project."""
    success = service.delete_project(db, project_id)
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
    query: Optional[str] = Query(None, description="Search across profiles and projects"),
    skill: Optional[str] = Query(None, description="Filter by skill"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
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
    summary="Get explainable candidate recommendations for a project",
)
def recommend_candidates_for_project(
    project_id: str,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> List[CandidateRecommendation]:
    """
    Returns candidate recommendations scored using explainable rules.
    Ranks candidates by skill coverage, missing skill fulfillment, domain overlap, and role fit.
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
    summary="Get explainable project recommendations for a student",
)
def recommend_projects_for_student(
    profile_id: str,
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
) -> List[ProjectRecommendation]:
    """
    Returns open project recommendations for a student seeking a team to join.
    """
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
    """Submit an expression of interest to collaborate on a project."""
    try:
        interest = service.express_interest(db, project_id, data)
        return InterestResponse(
            id=interest.id,
            project_id=interest.project_id,
            project_title=interest.project.title,
            profile_id=interest.profile_id,
            requester_name=interest.profile.display_name,
            requester_programme=interest.profile.programme,
            proposed_role=interest.proposed_role,
            message=interest.message,
            status=interest.status,
            created_at=interest.created_at,
            updated_at=interest.updated_at,
            shared_contact_email=None,  # Not revealed until approval
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/projects/{project_id}/interests",
    response_model=List[InterestResponse],
    summary="View interest requests for project",
)
def list_project_interests(
    project_id: str,
    db: Session = Depends(get_db),
) -> List[InterestResponse]:
    """Project owner view of candidates who expressed interest."""
    project = service.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found.")
    return service.list_project_interests(db, project_id)


@router.post(
    "/interests/{interest_id}/respond",
    response_model=InterestResponse,
    summary="Approve or reject collaboration request",
)
def respond_to_interest(
    interest_id: str,
    data: InterestRespondRequest,
    db: Session = Depends(get_db),
) -> InterestResponse:
    """
    Project owner approves or rejects an interest request.
    Upon approval, contact email is revealed for mutual communication.
    """
    interest = service.respond_to_interest(db, interest_id, data.status)
    if not interest:
        raise HTTPException(status_code=404, detail=f"Interest request '{interest_id}' not found.")

    contact_email = interest.profile.email if interest.status == InterestStatus.APPROVED else None
    return InterestResponse(
        id=interest.id,
        project_id=interest.project_id,
        project_title=interest.project.title,
        profile_id=interest.profile_id,
        requester_name=interest.profile.display_name,
        requester_programme=interest.profile.programme,
        proposed_role=interest.proposed_role,
        message=interest.message,
        status=interest.status,
        created_at=interest.created_at,
        updated_at=interest.updated_at,
        shared_contact_email=contact_email,
    )
