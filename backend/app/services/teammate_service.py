"""
Teammate Finder Service for GIKI Nexus.
Manages student profiles, projects, privacy masking, consent-based contact workflows,
and coordinates with the explainable MatchingEngine.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

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
    ProfilePublicResponse,
    ProfilePrivateResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectMemberResponse,
    InterestCreate,
    InterestResponse,
    InterestRespondRequest,
    CandidateRecommendation,
    ProjectRecommendation,
)
from backend.app.services.matching_service import MatchingEngine

logger = logging.getLogger(__name__)


class PaginatedResult(dict):
    """
    Pagination response dictionary that also allows direct iteration
    over items for seamless compatibility in both API JSON serialization and tests.
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

    # ---------------------------------------------------------------------
    # Helper: Privacy Masking & Response Formatting
    # ---------------------------------------------------------------------
    @staticmethod
    def format_public_profile(profile: StudentProfile) -> ProfilePublicResponse:
        """Convert a DB student profile into a privacy-sanitized public response."""
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
        """Format project DB entity into schema response."""
        members = [
            ProjectMemberResponse(
                profile_id=m.profile_id,
                display_name=(
                    f"Anonymous Student ({m.profile.programme}, Year {m.profile.academic_year})"
                    if m.profile and m.profile.visibility == ProfileVisibility.ANONYMOUS else (m.profile.display_name if m.profile else "Member")
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
                if project.owner.visibility == ProfileVisibility.ANONYMOUS else project.owner.display_name
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
        Format an interest record, revealing contact details ONLY if approved
        and viewer is an authorized participant (owner or applicant).
        """
        contact_email = None
        if interest.status == InterestStatus.APPROVED:
            # If viewer is project owner, reveal applicant's email
            if viewer_id and interest.project and viewer_id == interest.project.owner_id:
                contact_email = interest.profile.email if interest.profile else None
            # If viewer is applicant, reveal project owner's email
            elif viewer_id and viewer_id == interest.profile_id:
                contact_email = interest.project.owner.email if (interest.project and interest.project.owner) else None
            elif not viewer_id:
                # Default fallback if viewer unspecified but approved
                contact_email = interest.profile.email if interest.profile else None

        return InterestResponse(
            id=interest.id,
            project_id=interest.project_id,
            project_title=interest.project.title if interest.project else None,
            profile_id=interest.profile_id,
            requester_name=(
                f"Anonymous Student ({interest.profile.programme}, Year {interest.profile.academic_year})"
                if interest.profile and interest.profile.visibility == ProfileVisibility.ANONYMOUS
                else (interest.profile.display_name if interest.profile else None)
            ),
            requester_programme=interest.profile.programme if interest.profile else None,
            proposed_role=interest.proposed_role,
            message=interest.message,
            status=interest.status,
            created_at=interest.created_at,
            updated_at=interest.updated_at,
            shared_contact_email=contact_email,
        )

    # ---------------------------------------------------------------------
    # Profile Management
    # ---------------------------------------------------------------------
    def create_profile(self, db_or_data, data: Optional[ProfileCreate] = None) -> StudentProfile:
        """Create a new student profile."""
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
        logger.info(f"Created student profile: {profile.id} ({profile.display_name})")
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
        """Convenience alias for get_profile."""
        return self.get_profile(db or self.db, profile_id)

    def update_profile(
        self,
        db_or_id,
        profile_id_or_data=None,
        data: Optional[ProfileUpdate] = None,
    ) -> Optional[StudentProfile]:
        """Update an existing student profile."""
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
    ) -> Optional[StudentProfile]:
        """Update privacy visibility mode (PUBLIC, ANONYMOUS, UNLISTED)."""
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
        profile.visibility = vis
        db.commit()
        db.refresh(profile)
        return profile

    def deactivate_profile(self, db_or_id, profile_id: Optional[str] = None) -> bool:
        """Mark profile as inactive."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = profile_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        profile = self.get_profile(db, pid)
        if not profile:
            return False
        profile.is_active = False
        db.commit()
        return True

    def delete_profile(self, db_or_id, profile_id: Optional[str] = None) -> bool:
        """Permanently delete a student profile."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = profile_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        profile = self.get_profile(db, pid)
        if not profile:
            return False
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
        """List active profiles permitted to appear in discovery (PUBLIC or ANONYMOUS)."""
        db = db_or_first if isinstance(db_or_first, Session) else self._resolve_db(None)

        query = db.query(StudentProfile).filter(
            StudentProfile.is_active.is_(True),
            StudentProfile.visibility.in_([ProfileVisibility.PUBLIC, ProfileVisibility.ANONYMOUS]),
        )

        if programme:
            query = query.filter(StudentProfile.programme.ilike(f"%{programme.strip()}%"))
        if academic_year:
            query = query.filter(StudentProfile.academic_year == academic_year)

        profiles = query.all()

        # In-memory filtering for JSON list fields
        if skill and skill.strip():
            s_clean = skill.strip().lower()
            profiles = [
                p for p in profiles
                if any(s_clean in (sk or "").lower() for sk in (p.technical_skills or []))
            ]
        if domain and domain.strip():
            d_clean = domain.strip().lower()
            profiles = [
                p for p in profiles
                if any(d_clean in (dm or "").lower() for dm in (p.preferred_domains or []))
                or any(d_clean in (ri or "").lower() for ri in (p.research_interests or []))
            ]
        if role and role.strip():
            r_clean = role.strip().lower()
            profiles = [
                p for p in profiles
                if any(r_clean in (ro or "").lower() for ro in (p.preferred_roles or []))
            ]
        if search and search.strip():
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
        paginated = profiles[skip : skip + limit]
        items = [self.format_public_profile(p) for p in paginated]

        return PaginatedResult({"total": total, "skip": skip, "limit": limit, "items": items})

    # ---------------------------------------------------------------------
    # Project & Team Management
    # ---------------------------------------------------------------------
    def create_project(self, db_or_data, data: Optional[ProjectCreate] = None) -> Project:
        """Create a new project and add the creator as lead member."""
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

        # Add creator as first team member
        lead_member = ProjectMember(
            project_id=project.id,
            profile_id=owner.id,
            role="Project Lead",
        )
        db.add(lead_member)
        db.commit()
        db.refresh(project)
        logger.info(f"Created project: {project.id} ('{project.title}') by {owner.display_name}")
        return project

    def get_project(self, db_or_id, project_id: Optional[str] = None) -> Optional[Project]:
        """Fetch project by ID."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = project_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id
        return db.query(Project).filter(Project.id == pid).first()

    def get_project_by_id(self, project_id: str, db: Optional[Session] = None) -> Optional[Project]:
        """Convenience alias for get_project."""
        return self.get_project(db or self.db, project_id)

    def update_project(
        self,
        db_or_id,
        project_id_or_data=None,
        data: Optional[ProjectUpdate] = None,
    ) -> Optional[Project]:
        """Update project details."""
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

    def close_project(self, db_or_id, project_id: Optional[str] = None) -> Optional[Project]:
        """Close recruitment for a project."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = project_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        proj = self.get_project(db, pid)
        if not proj:
            return None
        proj.status = ProjectStatus.CLOSED
        proj.additional_members_needed = 0
        db.commit()
        db.refresh(proj)
        return proj

    def delete_project(self, db_or_id, project_id: Optional[str] = None) -> bool:
        """Permanently delete a project."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = project_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        proj = self.get_project(db, pid)
        if not proj:
            return False
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
        if effective_status:
            query = query.filter(Project.status == effective_status)

        projects = query.order_by(Project.created_at.desc()).all()

        if domain and domain.strip():
            d_clean = domain.strip().lower()
            projects = [
                p for p in projects
                if any(d_clean in (dm or "").lower() for dm in (p.domains or []))
            ]
        if skill and skill.strip():
            s_clean = skill.strip().lower()
            projects = [
                p for p in projects
                if any(s_clean in (sk or "").lower() for sk in (p.required_skills or []))
            ]
        if role and role.strip():
            r_clean = role.strip().lower()
            projects = [
                p for p in projects
                if any(r_clean in (ro or "").lower() for ro in (p.preferred_roles or []))
            ]
        if search and search.strip():
            q_clean = search.strip().lower()
            projects = [
                p for p in projects
                if q_clean in p.title.lower() or q_clean in p.description.lower()
            ]

        total = len(projects)
        paginated = projects[skip : skip + limit]
        items = [self.format_project_response(p) for p in paginated]

        return PaginatedResult({"total": total, "skip": skip, "limit": limit, "items": items})

    # ---------------------------------------------------------------------
    # Explainable Recommendations
    # ---------------------------------------------------------------------
    def recommend_candidates_for_project(
        self,
        db_or_id,
        project_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[CandidateRecommendation]:
        """
        Rank and explain candidates for an open project.
        Excludes existing team members, inactive profiles, and unlisted profiles.
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

        # Get existing team member profile IDs
        current_member_ids = {m.profile_id for m in project.members}
        current_team_profiles = [m.profile for m in project.members if m.profile]

        # Query all active, discoverable profiles not on the team
        candidates = db.query(StudentProfile).filter(
            StudentProfile.is_active.is_(True),
            StudentProfile.visibility.in_([ProfileVisibility.PUBLIC, ProfileVisibility.ANONYMOUS]),
            StudentProfile.id.notin_(current_member_ids),
        ).all()

        recommendations = []
        for cand in candidates:
            rec = MatchingEngine.evaluate_candidate_for_project(
                candidate=cand,
                project=project,
                current_team_profiles=current_team_profiles,
            )
            recommendations.append(rec)

        # Sort by overall score descending
        recommendations.sort(key=lambda r: r.overall_score, reverse=True)
        return recommendations[:limit]

    def recommend_projects_for_student(
        self,
        db_or_id,
        profile_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[ProjectRecommendation]:
        """
        Rank and explain open projects for a student seeking a team.
        Excludes closed projects and projects student is already on.
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

        # Find project IDs student is already a member of
        existing_project_ids = {
            m.project_id for m in student.team_memberships
        }

        # Query open projects student is not on
        projects = db.query(Project).filter(
            Project.status == ProjectStatus.OPEN,
            Project.id.notin_(existing_project_ids),
        ).all()

        recommendations = []
        for proj in projects:
            rec = MatchingEngine.evaluate_project_for_student(
                student=student,
                project=proj,
            )
            recommendations.append(rec)

        recommendations.sort(key=lambda r: r.overall_score, reverse=True)
        return recommendations[:limit]

    # ---------------------------------------------------------------------
    # Interest & Consent-Based Contact Workflow
    # ---------------------------------------------------------------------
    def express_interest(
        self,
        db_or_id,
        project_id_or_data=None,
        data: Optional[InterestCreate] = None,
    ) -> ProjectInterest:
        """Create an expression of interest to join a project."""
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

        # Check for existing pending/approved interest
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
    ) -> List[InterestResponse]:
        """List incoming interest requests for a project."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            pid = project_id
        else:
            db = self._resolve_db(None)
            pid = db_or_id

        project = self.get_project(db, pid)
        if not project:
            return []

        interests = db.query(ProjectInterest).filter(
            ProjectInterest.project_id == pid
        ).order_by(ProjectInterest.created_at.desc()).all()

        results = []
        for item in interests:
            # Contact email is revealed ONLY if approved
            contact_email = None
            if item.status == InterestStatus.APPROVED and item.profile:
                contact_email = item.profile.email

            results.append(
                InterestResponse(
                    id=item.id,
                    project_id=item.project_id,
                    project_title=project.title,
                    profile_id=item.profile_id,
                    requester_name=(
                        f"Anonymous Student ({item.profile.programme}, Year {item.profile.academic_year})"
                        if item.profile and item.profile.visibility == ProfileVisibility.ANONYMOUS
                        else (item.profile.display_name if item.profile else None)
                    ),
                    requester_programme=item.profile.programme if item.profile else None,
                    proposed_role=item.proposed_role,
                    message=item.message,
                    status=item.status,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                    shared_contact_email=contact_email,
                )
            )
        return results

    def respond_to_interest(
        self,
        db_or_id,
        interest_id_or_status=None,
        new_status=None,
        owner_id: Optional[str] = None,
        response_data: Optional[Any] = None,
    ) -> Optional[ProjectInterest]:
        """Approve or reject an expression of interest."""
        if isinstance(db_or_id, Session):
            db = db_or_id
            iid = interest_id_or_status
            target_status = new_status
        else:
            db = self._resolve_db(None)
            iid = db_or_id
            if response_data is not None:
                target_status = (
                    response_data.target_status
                    if hasattr(response_data, "target_status")
                    else getattr(response_data, "status", None)
                )
            elif interest_id_or_status is not None:
                target_status = interest_id_or_status
            else:
                target_status = new_status

        interest = db.query(ProjectInterest).filter(
            ProjectInterest.id == iid
        ).first()
        if not interest:
            return None

        interest.status = target_status
        # If approved, add student as project member
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
