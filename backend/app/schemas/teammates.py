"""
Pydantic v2 schemas for GIKI Nexus Teammate Finder.
Defines contracts for profile CRUD, project management, privacy enforcement,
contact workflows, and explainable match recommendations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict

from backend.app.models.teammates import (
    ProfileVisibility,
    ContactPreference,
    ProjectStatus,
    InterestStatus,
)


# -------------------------------------------------------------------------
# Student Profile Schemas
# -------------------------------------------------------------------------

class ProfileBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    display_name: str = Field(..., min_length=2, max_length=100, description="Full student display name")
    programme: str = Field(..., description="Academic degree programme (e.g. 'BS Computer Science')")
    academic_year: int = Field(..., ge=1, le=4, description="Current academic year (1-4)")
    technical_skills: List[str] = Field(default_factory=list, description="Technical skill tags (e.g. Python, PyTorch)")
    research_interests: List[str] = Field(default_factory=list, description="Academic/research interest domains")
    preferred_domains: List[str] = Field(default_factory=list, description="Preferred project domains (e.g. AI/ML, Web)")
    preferred_roles: List[str] = Field(default_factory=list, description="Preferred project roles (e.g. Backend Developer)")
    availability: str = Field(default="flexible", description="Weekly time commitment or flexibility")
    previous_experience: Optional[str] = Field(default=None, description="Summary of past projects, hackathons, or coursework")
    bio: Optional[str] = Field(default=None, description="Brief student introduction")
    project_ideas: Optional[str] = Field(default=None, description="Ideas student wishes to work on")
    visibility: ProfileVisibility = Field(default=ProfileVisibility.PUBLIC, description="Public, Anonymous, or Unlisted")
    contact_preference: ContactPreference = Field(default=ContactPreference.UPON_REQUEST, description="Contact sharing policy")


class ProfileCreate(ProfileBase):
    email: str = Field(..., description="Official GIKI student email (stored privately)")


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    display_name: Optional[str] = None
    email: Optional[str] = None
    programme: Optional[str] = None
    academic_year: Optional[int] = Field(default=None, ge=1, le=4)
    technical_skills: Optional[List[str]] = None
    research_interests: Optional[List[str]] = None
    preferred_domains: Optional[List[str]] = None
    preferred_roles: Optional[List[str]] = None
    availability: Optional[str] = None
    previous_experience: Optional[str] = None
    bio: Optional[str] = None
    project_ideas: Optional[str] = None
    visibility: Optional[ProfileVisibility] = None
    contact_preference: Optional[ContactPreference] = None
    is_active: Optional[bool] = None


class ProfileVisibilityUpdate(BaseModel):
    visibility: ProfileVisibility


class ProfilePublicResponse(BaseModel):
    """
    Public discovery view of a student profile.
    Email is NEVER exposed here. Anonymous profiles mask their display name.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    programme: str
    academic_year: int
    technical_skills: List[str] = Field(default_factory=list)
    research_interests: List[str] = Field(default_factory=list)
    preferred_domains: List[str] = Field(default_factory=list)
    preferred_roles: List[str] = Field(default_factory=list)
    availability: str
    previous_experience: Optional[str] = None
    bio: Optional[str] = None
    project_ideas: Optional[str] = None
    visibility: ProfileVisibility
    contact_preference: ContactPreference
    is_active: bool
    is_anonymous: bool = False
    created_at: datetime
    updated_at: datetime


class ProfilePrivateResponse(ProfilePublicResponse):
    """Full profile returned to the owner, including private contact info."""
    email: str


# -------------------------------------------------------------------------
# Project Schemas
# -------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    owner_id: str = Field(..., description="Student profile ID of project creator")
    title: str = Field(..., min_length=3, max_length=150, description="Project title")
    description: str = Field(..., min_length=10, description="Project scope and goals")
    domains: List[str] = Field(default_factory=list, description="Project domains/topics")
    required_skills: List[str] = Field(default_factory=list, description="Skills required for the project")
    preferred_roles: List[str] = Field(default_factory=list, description="Open roles being recruited")
    additional_members_needed: int = Field(default=1, ge=1, le=10, description="Number of additional members desired")


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = None
    description: Optional[str] = None
    domains: Optional[List[str]] = None
    required_skills: Optional[List[str]] = None
    preferred_roles: Optional[List[str]] = None
    additional_members_needed: Optional[int] = Field(default=None, ge=0, le=10)
    status: Optional[ProjectStatus] = None


class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    profile_id: str
    display_name: str
    programme: str
    role: Optional[str] = None
    joined_at: datetime


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    owner_name: Optional[str] = None
    title: str
    description: str
    domains: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_roles: List[str] = Field(default_factory=list)
    additional_members_needed: int
    status: ProjectStatus
    members: List[ProjectMemberResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# -------------------------------------------------------------------------
# Interest & Contact Workflow Schemas
# -------------------------------------------------------------------------

class InterestCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    profile_id: str = Field(..., description="ID of student expressing interest")
    proposed_role: Optional[str] = Field(default=None, description="Proposed role on the project")
    message: Optional[str] = Field(default=None, description="Introductory note to the project owner")


class InterestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    project_title: Optional[str] = None
    profile_id: str
    requester_name: Optional[str] = None
    requester_programme: Optional[str] = None
    proposed_role: Optional[str] = None
    message: Optional[str] = None
    status: InterestStatus
    created_at: datetime
    updated_at: datetime
    shared_contact_email: Optional[str] = Field(
        default=None,
        description="Revealed ONLY upon owner approval for mutual contact",
    )


class InterestRespondRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Optional[InterestStatus] = Field(default=None, description="APPROVED or REJECTED")
    action: Optional[InterestStatus] = Field(default=None, description="Alias for status")

    @property
    def target_status(self) -> InterestStatus:
        res = self.status or self.action
        if res is None:
            raise ValueError("Either status or action must be provided.")
        return res


# -------------------------------------------------------------------------
# Explainable Matching & Recommendations Schemas
# -------------------------------------------------------------------------

class CandidateRecommendation(BaseModel):
    """Explainable candidate recommendation for a project."""
    model_config = ConfigDict(extra="ignore")

    profile_id: str
    display_name: str
    programme: str
    academic_year: int
    is_anonymous: bool
    availability: str
    skills_offered: List[str]
    overall_score: float = Field(..., description="Rule-based alignment score from 0.0 to 100.0 (not a guarantee)")
    score_breakdown: Dict[str, float] = Field(..., description="Criterion-by-criterion scores")
    shared_interests: List[str] = Field(default_factory=list)
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills_covered: List[str] = Field(default_factory=list, description="Project skills candidate fills")
    matched_roles: List[str] = Field(default_factory=list)
    role_compatibility: bool = False
    availability_compatibility: bool = False
    explanation: str = Field(..., description="Clear human-readable breakdown of match rationale")

    @property
    def matched_skills(self) -> List[str]:
        return self.matching_skills

    @property
    def complementary_skills(self) -> List[str]:
        return self.missing_skills_covered

    @property
    def matched_domains(self) -> List[str]:
        return self.shared_interests

    @property
    def match_score(self) -> float:
        return self.overall_score

    @property
    def candidate(self):
        class _CandObj:
            def __init__(self, pid):
                self.id = pid
        return _CandObj(self.profile_id)

    @property
    def breakdown(self):
        class _BreakdownObj:
            def __init__(self, d):
                self.skill_score = d.get("skills_score", 0.0)
                self.domain_score = d.get("interests_score", 0.0)
                self.role_score = d.get("role_score", 0.0)
                self.availability_score = d.get("availability_score", 0.0)
                self.experience_score = d.get("experience_score", 0.0)
        return _BreakdownObj(self.score_breakdown)


class ProjectRecommendation(BaseModel):
    """Explainable project recommendation for a student looking for a team."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    project_title: str
    domains: List[str]
    required_skills: List[str]
    preferred_roles: List[str]
    overall_score: float = Field(..., description="Rule-based alignment score from 0.0 to 100.0")
    score_breakdown: Dict[str, float]
    shared_interests: List[str] = Field(default_factory=list)
    matching_skills: List[str] = Field(default_factory=list)
    skills_contributed: List[str] = Field(default_factory=list)
    role_compatibility: bool = False
    explanation: str
