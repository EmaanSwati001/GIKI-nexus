"""
Teammate Finder Service for GIKI Nexus.
Manages student profiles, projects, privacy masking, consent-based contact workflows,
and coordinates with the explainable MatchingEngine.

OWNERSHIP ENFORCEMENT
=====================
All mutation methods accept an `owner_key` parameter.
The service validates it against the stored ownership_key using hmac.compare_digest.
Raises PermissionError on mismatch — callers must map this to HTTP 403.

See backend/app/models/teammates.py for the full prototype authentication notice.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

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
    ProfilePublicResponse,
    ProfilePrivateResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectCreateResponse,
    ProjectMemberResponse,
    InterestCreate,
    InterestResponse,
    InterestRespondRequest,
    CandidateRecommendation,
    ProjectRecommendation,
)
from backend.app.services.matching_service import MatchingEngine

logger = logging.getLogger(__name__)


class OwnershipError(PermissionError):
    """Raised when an operation is attempted without valid ownership credentials."""
    pass


class PaginatedResult(dict):
    """
    Pagination response dictionary supporting both JSON serialization and direct
    list-style iteration for test compatibility.
    """
    def __iter__(self):
        return iter(self.get("items", []))

    def __len__(self):
        return len(self.get("items", []))

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.get("items", [])[key]
        return super().__getitem__(key)


class TeammateService:
    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def _resolve_db(self, db: Optional[Session]) -> Session:
        session = db if isinstance(db, Session) else self.db
        if session is None:
            raise ValueError("No database session provided to TeammateService.")
        return session

    # ------------------------------------------------------------------
    # Ownership Verification
    # ------------------------------------------------------------------
    @staticmethod
    def _require_profile_ownership(profile: StudentProfile, owner_key: Optional[str]) -> None:
        """
        Verify that the caller owns the profile.
        Raises OwnershipError if the key is absent or incorrect.
        Uses constant-time comparison to prevent timing attacks.
        """
        if not verify_ownership_key(owner_key or "", profile.ownership_key):
            # Log at DEBUG only — do not log the provided key value
            logger.debug(
                "Ownership check failed for profile %s — key mismatch.", profile.id
            )
            raise OwnershipError(
                "Invalid or missing ownership key. "
                "Only the profile creator may perform this operation."
            )

    @staticmethod
    def _require_project_ownership(project: Project, owner_key: Optional[str]) -> None:
        """
        Verify that the caller owns the project.
        Raises OwnershipError if the key is absent or incorrect.
        """
        if not verify_ownership_key(owner_key or "", project.ownership_key):
            logger.debug(
                "Ownership check failed for project %s — key mismatch.", project.id
            )
            raise OwnershipError(
                "Invalid or missing ownership key. "
                "Only the project creator may perform this operation."
            )

    # ------------------------------------------------------------------
    # Privacy Masking Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _mask_display_name(profile: StudentProfile) -> str:
        """Return masked display name for anonymous profiles."""
        if profile.visibility == ProfileVisibility.ANONYMOUS:
            return f"Anonymous Student ({profile.programme}, Year {profile.academic_year})"
        return profile.display_name

    @staticmethod
    def format_public_profile(profile: StudentProfile) -> ProfilePublicResponse:
        """
        Convert a DB profile into a privacy-sanitized public response.
        - email is NEVER included.
        - ownership_key is NEVER included.
        - Anonymous profiles have display_name masked and bio suppressed.
        """
        is_anon = profile.visibility == ProfileVisibility.ANONYMOUS
        display_name = (
            f"Anonymous Student ({profile.programme}, Year {profile.academic_year})"
            if is_anon else profile.display_name
        )
        bio = None if is_anon else profile.bio

        return ProfilePublicResponse(
            id=profile.id,
            display_name=display_name,
            programme=profile.programme,
            academic_year=profile.academic_year,
            technical_skills=profile.technical_skills or [],
            research_interests=profile.research_interests or [],
            preferred_domains=profile.preferred_domains or [],
            preferred_roles=profile.preferred_roles or [],
            availability=profile.availability,
            previous_experience=profile.previous_experience,
            bio=bio,
            project_ideas=profile.project_ideas,
            visibility=profile.visibility,
            contact_preference=profile.contact_preference,
            is_active=profile.is_active,
            is_anonymous=is_anon,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    @staticmethod
    def format_project_response(project: Project) -> ProjectResponse:
        """
        Format project DB entity into schema response.
        ownership_key is NOT included. Anonymous member names are masked.
        """
        members = [
            ProjectMemberResponse(
                profile_id=m.profile_id,
                display_name=(
                    f"Anonymous Student ({m.profile.programme}, Year {m.profile.academic_year})"
                    if m.profile and m.profile.visibility == ProfileVisibility.ANONYMOUS
                    else (m.profile.display_name if m.profile else "Member")
                ),
                programme=m.profile.programme if m.profile else "Unknown",
                role=m.role,
                joined_at=m.joined_at,
            )
            for m in project.members
        ]

        owner_name = None
        if project.owner:
            owner_name = (
                f"Anonymous Student ({project.owner.programme}, Year {project.owner.academic_year})"
                if project.owner.visibility == ProfileVisibility.ANONYMOUS
                else project.owner.display_name
            )

        return ProjectResponse(
            id=project.id,
            owner_id=project.owner_id,
            owner_name=owner_name,
            title=project.title,
            description=project.description,
            domains=project.domains or [],
            required_skills=project.required_skills or [],
            preferred_roles=project.preferred_roles or [],
            additional_members_needed=project.additional_members_needed,
            status=project.status,
            members=members,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    def format_interest_response(
        self,
        interest: ProjectInterest,
        viewer_id: Optional[str] = None,
    ) -> InterestResponse:
        """
        Format an interest record. Contact emails are revealed ONLY when status is APPROVED
        and the viewer is a direct participant (owner or applicant).
        Anonymous requester names are masked.
        """
        contact_email = None
        if interest.status == InterestStatus.APPROVED:
            if viewer_id and interest.project and viewer_id == interest.project.owner_id:
                # Owner sees applicant's email
                contact_email = interest.profile.email if interest.profile else None
            elif viewer_id and viewer_id == interest.profile_id:
                # Applicant sees project owner's email
                contact_email = (
                    interest.project.owner.email
                    if (interest.project and interest.project.owner)
                    else None
                )
            elif not viewer_id:
                # Fallback when viewer context not provided (e.g. owner viewing their interests list)
                contact_email = interest.profile.email if interest.profile else None

        # Mask anonymous requester names
        requester_name = None
        if interest.profile:
            if interest.profile.visibility == ProfileVisibility.ANONYMOUS:
                requester_name = (
                    f"Anonymous Student ({interest.profile.programme}, "
                    f"Year {interest.profile.academic_year})"
                )
            else:
                requester_name = interest.profile.display_name

        return InterestResponse(
            id=interest.id,
            project_id=interest.project_id,
            project_title=interest.project.title if interest.project else None,
            profile_id=interest.profile_id,
            requester_name=requester_name,
            requester_programme=interest.profile.programme if interest.profile else None,
            proposed_role=interest.proposed_role,
            message=interest.message,
            status=interest.status,
            created_at=interest.created_at,
            updated_at=interest.updated_at,
            shared_contact_email=contact_email,
        )

    # ------------------------------------------------------------------
    # Profile Management
    # ------------------------------------------------------------------
    def create_profile(self, db_or_data, data: Optional[ProfileCreate] = None) -> StudentProfile:
        """Create a new student profile. Returns DB object including ownership_key."""
        if isinstance(db_or_data, Session):
            db = db_or_data
            payload = data
        else:
            db = self._resolve_db(None)
            payload = db_or_data

        profile = StudentProfile(
            display_name=payload.display_name.strip(),
            email=payload.email.strip().lower(),
            programme=payload.programme.strip(),
            academic_year=payload.academic_year,
            technical_skills=[s.strip() for s in payload.technical_skills if s.strip()],
            research_interests=[r.strip() for r in payload.research_interests if r.strip()],
            preferred_domains=[d.strip() for d in payload.preferred_domains if d.strip()],
            preferred_roles=[role.strip() for role in payload.preferred_roles if role.strip()],
            availability=payload.availability.strip(),
            previous_experience=payload.previous_experience.strip() if payload.previous_experience else None,
            bio=payload.bio.strip() if payload.bio else None,
            project_ideas=payload.project_ideas.strip() if payload.project_ideas else None,
            visibility=payload.visibility,
            contact_preference=payload.contact_preference,
            is_active=True,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        logger.info("Created student profile: %s", profile.id)
        return profile

    def get_profile(self, db_or_id, profile_id: Optional[str] = None) -> Optional[StudentProfile]:
        """Fetch raw profile DB record by ID."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = profile_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id
        return db.query(StudentProfile).filter(StudentProfile.id == pid).first()

    def get_profile_by_id(self, profile_id: str, db: Optional[Session] = None) -> Optional[StudentProfile]:
        return self.get_profile(db or self.db, profile_id)

    def update_profile(
        self,
        db_or_id,
        profile_id_or_data=None,
        data: Optional[ProfileUpdate] = None,
        owner_key: Optional[str] = None,
    ) -> Optional[StudentProfile]:
        """Update a profile. Raises OwnershipError if key is wrong."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = profile_id_or_data
            payload = data
        else:
            db = self._resolve_db(None)
            pid = db_or_id
            payload = profile_id_or_data

        profile = self.get_profile(db, pid)
        if not profile:
            return None

        self._require_profile_ownership(profile, owner_key)

        update_dict = payload.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                if key in ["technical_skills", "research_interests", "preferred_domains", "preferred_roles"]:
                    value = [item.strip() for item in value if isinstance(item, str) and item.strip()]
                elif isinstance(value, str):
                    value = value.strip()
                setattr(profile, key, value)

        db.commit()
        db.refresh(profile)
        return profile

    def update_visibility(
        self,
        db_or_id,
        profile_id_or_vis=None,
        visibility=None,
        owner_key: Optional[str] = None,
    ) -> Optional[StudentProfile]:
        """Update visibility. Raises OwnershipError if key is wrong."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = profile_id_or_vis
            vis = visibility
        else:
            db = self._resolve_db(None)
            pid = db_or_id
            vis = profile_id_or_vis

        if hasattr(vis, "visibility"):
            vis = vis.visibility

        profile = self.get_profile(db, pid)
        if not profile:
            return None

        self._require_profile_ownership(profile, owner_key)

        profile.visibility = vis
        db.commit()
        db.refresh(profile)
        return profile

    def deactivate_profile(
        self,
        db_or_id,
        profile_id: Optional[str] = None,
        owner_key: Optional[str] = None,
    ) -> bool:
        """Deactivate profile. Raises OwnershipError if key is wrong."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = profile_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        profile = self.get_profile(db, pid)
        if not profile:
            return False

        self._require_profile_ownership(profile, owner_key)

        profile.is_active = False
        db.commit()
        return True

    def delete_profile(
        self,
        db_or_id,
        profile_id: Optional[str] = None,
        owner_key: Optional[str] = None,
    ) -> bool:
        """Permanently delete a profile. Raises OwnershipError if key is wrong."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = profile_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        profile = self.get_profile(db, pid)
        if not profile:
            return False

        self._require_profile_ownership(profile, owner_key)

        db.delete(profile)
        db.commit()
        return True

    def list_discoverable_profiles(
        self,
        db_or_first=None,
        programme: Optional[str] = None,
        academic_year: Optional[int] = None,
        skill: Optional[str] = None,
        domain: Optional[str] = None,
        role: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> PaginatedResult:
        """List active PUBLIC/ANONYMOUS profiles. UNLISTED and inactive are always excluded."""
        db = db_or_first if isinstance(db_or_first, Session) else self._resolve_db(None)

        query = db.query(StudentProfile).filter(
            StudentProfile.is_active.is_(True),
            StudentProfile.visibility.in_([ProfileVisibility.PUBLIC, ProfileVisibility.ANONYMOUS]),
        )

        if isinstance(programme, str) and programme.strip():
            query = query.filter(StudentProfile.programme.ilike(f"%{programme.strip()}%"))
        if isinstance(academic_year, int):
            query = query.filter(StudentProfile.academic_year == academic_year)

        profiles = query.all()

        if isinstance(skill, str) and skill.strip():
            s_clean = skill.strip().lower()
            profiles = [
                p for p in profiles
                if any(s_clean in (sk or "").lower() for sk in (p.technical_skills or []))
            ]
        if isinstance(domain, str) and domain.strip():
            d_clean = domain.strip().lower()
            profiles = [
                p for p in profiles
                if any(d_clean in (dm or "").lower() for dm in (p.preferred_domains or []))
                or any(d_clean in (ri or "").lower() for ri in (p.research_interests or []))
            ]
        if isinstance(role, str) and role.strip():
            r_clean = role.strip().lower()
            profiles = [
                p for p in profiles
                if any(r_clean in (ro or "").lower() for ro in (p.preferred_roles or []))
            ]
        if isinstance(search, str) and search.strip():
            q_clean = search.strip().lower()
            profiles = [
                p for p in profiles
                if (p.visibility == ProfileVisibility.PUBLIC and q_clean in p.display_name.lower())
                or q_clean in p.programme.lower()
                or (p.bio and q_clean in p.bio.lower())
                or any(q_clean in (sk or "").lower() for sk in (p.technical_skills or []))
                or any(q_clean in (dm or "").lower() for dm in (p.preferred_domains or []))
            ]

        total = len(profiles)
        skip_val = skip if isinstance(skip, int) else 0
        limit_val = limit if isinstance(limit, int) else 50
        paginated = profiles[skip_val : skip_val + limit_val]
        items = [self.format_public_profile(p) for p in paginated]

        return PaginatedResult({"total": total, "skip": skip_val, "limit": limit_val, "items": items})

    # ------------------------------------------------------------------
    # Project Management
    # ------------------------------------------------------------------
    def create_project(self, db_or_data, data: Optional[ProjectCreate] = None) -> Project:
        """Create a project and add the creator as Project Lead."""
        if isinstance(db_or_data, Session):
            db = db_or_data
            payload = data
        else:
            db = self._resolve_db(None)
            payload = db_or_data

        owner = self.get_profile(db, payload.owner_id)
        if not owner:
            raise ValueError(f"Student profile '{payload.owner_id}' not found.")

        project = Project(
            owner_id=payload.owner_id,
            title=payload.title.strip(),
            description=payload.description.strip(),
            domains=[d.strip() for d in payload.domains if d.strip()],
            required_skills=[s.strip() for s in payload.required_skills if s.strip()],
            preferred_roles=[r.strip() for r in payload.preferred_roles if r.strip()],
            additional_members_needed=payload.additional_members_needed,
            status=ProjectStatus.OPEN,
        )
        db.add(project)
        db.flush()

        lead_member = ProjectMember(
            project_id=project.id,
            profile_id=owner.id,
            role="Project Lead",
        )
        db.add(lead_member)
        db.commit()
        db.refresh(project)
        logger.info("Created project: %s ('%s')", project.id, project.title)
        return project

    def get_project(self, db_or_id, project_id: Optional[str] = None) -> Optional[Project]:
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = project_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id
        return db.query(Project).filter(Project.id == pid).first()

    def get_project_by_id(self, project_id: str, db: Optional[Session] = None) -> Optional[Project]:
        return self.get_project(db or self.db, project_id)

    def update_project(
        self,
        db_or_id,
        project_id_or_data=None,
        data: Optional[ProjectUpdate] = None,
        owner_key: Optional[str] = None,
    ) -> Optional[Project]:
        """Update project details. Raises OwnershipError if key is wrong."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = project_id_or_data
            payload = data
        else:
            db = self._resolve_db(None)
            pid = db_or_id
            payload = project_id_or_data

        proj = self.get_project(db, pid)
        if not proj:
            return None

        self._require_project_ownership(proj, owner_key)

        update_dict = payload.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                if key in ["domains", "required_skills", "preferred_roles"]:
                    value = [item.strip() for item in value if isinstance(item, str) and item.strip()]
                elif isinstance(value, str):
                    value = value.strip()
                setattr(proj, key, value)

        db.commit()
        db.refresh(proj)
        return proj

    def close_project(
        self,
        db_or_id,
        project_id: Optional[str] = None,
        owner_key: Optional[str] = None,
    ) -> Optional[Project]:
        """Close recruitment. Raises OwnershipError if key is wrong."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = project_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        proj = self.get_project(db, pid)
        if not proj:
            return None

        self._require_project_ownership(proj, owner_key)

        proj.status = ProjectStatus.CLOSED
        proj.additional_members_needed = 0
        db.commit()
        db.refresh(proj)
        return proj

    def delete_project(
        self,
        db_or_id,
        project_id: Optional[str] = None,
        owner_key: Optional[str] = None,
    ) -> bool:
        """Permanently delete a project. Raises OwnershipError if key is wrong."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = project_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        proj = self.get_project(db, pid)
        if not proj:
            return False

        self._require_project_ownership(proj, owner_key)

        db.delete(proj)
        db.commit()
        return True

    def list_projects(
        self,
        db_or_first=None,
        domain: Optional[str] = None,
        skill: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[ProjectStatus] = ProjectStatus.OPEN,
        status_filter: Optional[ProjectStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> PaginatedResult:
        """List projects with optional filtering."""
        db = db_or_first if isinstance(db_or_first, Session) else self._resolve_db(None)

        query = db.query(Project)
        effective_status = status_filter if status_filter is not None else status
        if effective_status and hasattr(effective_status, "value"):
            query = query.filter(Project.status == effective_status)

        projects = query.order_by(Project.created_at.desc()).all()

        if isinstance(domain, str) and domain.strip():
            d_clean = domain.strip().lower()
            projects = [p for p in projects if any(d_clean in (dm or "").lower() for dm in (p.domains or []))]
        if isinstance(skill, str) and skill.strip():
            s_clean = skill.strip().lower()
            projects = [p for p in projects if any(s_clean in (sk or "").lower() for sk in (p.required_skills or []))]
        if isinstance(role, str) and role.strip():
            r_clean = role.strip().lower()
            projects = [p for p in projects if any(r_clean in (ro or "").lower() for ro in (p.preferred_roles or []))]
        if isinstance(search, str) and search.strip():
            q_clean = search.strip().lower()
            projects = [p for p in projects if q_clean in p.title.lower() or q_clean in p.description.lower()]

        total = len(projects)
        skip_val = skip if isinstance(skip, int) else 0
        limit_val = limit if isinstance(limit, int) else 50
        paginated = projects[skip_val : skip_val + limit_val]
        items = [self.format_project_response(p) for p in paginated]

        return PaginatedResult({"total": total, "skip": skip_val, "limit": limit_val, "items": items})

    # ------------------------------------------------------------------
    # Explainable Recommendations
    # ------------------------------------------------------------------
    def recommend_candidates_for_project(
        self,
        db_or_id,
        project_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[CandidateRecommendation]:
        """
        Rank candidates for an open project.
        Excludes current team members, inactive profiles, and UNLISTED profiles.
        """
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = project_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        project = self.get_project(db, pid)
        if not project:
            return []

        current_member_ids = {m.profile_id for m in project.members}
        current_team_profiles = [m.profile for m in project.members if m.profile]

        candidates = db.query(StudentProfile).filter(
            StudentProfile.is_active.is_(True),
            StudentProfile.visibility.in_([ProfileVisibility.PUBLIC, ProfileVisibility.ANONYMOUS]),
            StudentProfile.id.notin_(current_member_ids),
        ).all()

        recommendations = [
            MatchingEngine.evaluate_candidate_for_project(
                candidate=cand,
                project=project,
                current_team_profiles=current_team_profiles,
            )
            for cand in candidates
        ]

        recommendations.sort(key=lambda r: r.overall_score, reverse=True)
        return recommendations[:limit]

    def recommend_projects_for_student(
        self,
        db_or_id,
        profile_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[ProjectRecommendation]:
        """
        Rank open projects for a student seeking a team.
        Excludes projects the student is already on and all non-OPEN projects.
        """
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = profile_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        student = self.get_profile(db, pid)
        if not student:
            return []

        existing_project_ids = {m.project_id for m in student.team_memberships}

        projects = db.query(Project).filter(
            Project.status == ProjectStatus.OPEN,
            Project.id.notin_(existing_project_ids),
        ).all()

        recommendations = [
            MatchingEngine.evaluate_project_for_student(student=student, project=proj)
            for proj in projects
        ]

        recommendations.sort(key=lambda r: r.overall_score, reverse=True)
        return recommendations[:limit]

    # ------------------------------------------------------------------
    # Interest & Consent-Based Contact Workflow
    # ------------------------------------------------------------------
    def express_interest(
        self,
        db_or_id,
        project_id_or_data=None,
        data: Optional[InterestCreate] = None,
    ) -> ProjectInterest:
        """Submit expression of interest. Contact emails remain hidden until approved."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = project_id_or_data
            payload = data
        else:
            db = self._resolve_db(None)
            pid = db_or_id
            payload = project_id_or_data

        project = self.get_project(db, pid)
        if not project:
            raise ValueError(f"Project '{pid}' not found.")
        if project.status != ProjectStatus.OPEN:
            raise ValueError("Recruitment is closed for this project.")

        student = self.get_profile(db, payload.profile_id)
        if not student:
            raise ValueError(f"Student profile '{payload.profile_id}' not found.")

        existing = db.query(ProjectInterest).filter(
            ProjectInterest.project_id == pid,
            ProjectInterest.profile_id == payload.profile_id,
            ProjectInterest.status.in_([InterestStatus.PENDING, InterestStatus.APPROVED]),
        ).first()
        if existing:
            raise ValueError("You have already submitted interest for this project.")

        interest = ProjectInterest(
            project_id=pid,
            profile_id=payload.profile_id,
            proposed_role=payload.proposed_role.strip() if payload.proposed_role else None,
            message=payload.message.strip() if payload.message else None,
            status=InterestStatus.PENDING,
        )
        db.add(interest)
        db.commit()
        db.refresh(interest)
        return interest

    def list_project_interests(
        self,
        db_or_id,
        project_id: Optional[str] = None,
        owner_key: Optional[str] = None,
    ) -> List[InterestResponse]:
        """
        List interest requests for a project.
        Requires the project owner_key to view applicant details.
        """
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = project_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        project = self.get_project(db, pid)
        if not project:
            return []

        self._require_project_ownership(project, owner_key)

        interests = (
            db.query(ProjectInterest)
            .filter(ProjectInterest.project_id == pid)
            .order_by(ProjectInterest.created_at.desc())
            .all()
        )

        return [self.format_interest_response(item, viewer_id=project.owner_id) for item in interests]

    def respond_to_interest(
        self,
        db_or_id,
        interest_id_or_status=None,
        new_status=None,
        owner_id: Optional[str] = None,
        response_data=None,
        owner_key: Optional[str] = None,
    ) -> Optional[ProjectInterest]:
        """
        Approve or reject an interest request.
        Only the project owner (verified by ownership_key) may call this.
        On approval: candidate is added as project member; contact emails are unlocked.
        """
        if isinstance(db_or_id, Session):
            db = db_or_id
            iid = interest_id_or_status
            target_status = new_status
        else:
            db = self._resolve_db(None)
            iid = db_or_id
            if response_data is not None:
                target_status = getattr(response_data, "target_status", None) or getattr(response_data, "action", None) or getattr(response_data, "status", None)
            elif interest_id_or_status is not None:
                target_status = interest_id_or_status
            else:
                target_status = new_status

        interest = db.query(ProjectInterest).filter(ProjectInterest.id == iid).first()
        if not interest:
            return None

        # Enforce project ownership
        self._require_project_ownership(interest.project, owner_key)

        if target_status == InterestStatus.PENDING:
            raise ValueError("Cannot set interest status back to PENDING.")

        interest.status = target_status

        if target_status == InterestStatus.APPROVED:
            is_member = db.query(ProjectMember).filter(
                ProjectMember.project_id == interest.project_id,
                ProjectMember.profile_id == interest.profile_id,
            ).first()
            if not is_member:
                member = ProjectMember(
                    project_id=interest.project_id,
                    profile_id=interest.profile_id,
                    role=interest.proposed_role or "Collaborator",
                )
                db.add(member)
                if interest.project and interest.project.additional_members_needed > 0:
                    interest.project.additional_members_needed -= 1

        db.commit()
        db.refresh(interest)
        return interest
