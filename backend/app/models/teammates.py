"""
SQLAlchemy models for GIKI Nexus Student Project Teammate Finder.
Defines normalized schemas for student profiles, projects, team members, and interest workflows.

PROTOTYPE AUTHENTICATION NOTICE
================================
This module uses a lightweight ownership_key mechanism for prototype-stage access control.
Ownership keys are cryptographically random 32-character hex tokens (128 bits of entropy)
generated at profile and project creation time using Python's secrets module.

The creator MUST supply the correct ownership_key on all subsequent mutation requests
(update, deactivate, delete, close, approve/reject interest). The key is compared using
hmac.compare_digest to prevent timing-based side-channel attacks.

WHAT THIS PROVIDES:
- Prevents casual ID-guessing attacks where knowing a profile_id or project_id alone
  would grant unauthorized mutation access.

WHAT THIS DOES NOT PROVIDE:
- Institutional identity verification (no @giki.edu.pk email binding).
- Session management or token expiry.
- Brute-force rate limiting.
- Multi-factor authentication.
- Production-grade security guarantees.

A production deployment MUST replace this mechanism with an institutional SSO integration
(e.g., Google Workspace OAuth for @giki.edu.pk accounts or Shibboleth / SAML).

Ownership keys are intentionally:
- Never returned in public discovery or recommendation responses.
- Never logged at INFO level or above.
- Returned only once: in the private creation response (ProfilePrivateResponse / ProjectResponse
  with ownership_key field), which the creator must store securely.
"""

import enum
import hmac
import secrets
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Enum,
    Text,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship

from backend.app.database.session import Base


class ProfileVisibility(str, enum.Enum):
    PUBLIC = "PUBLIC"          # Visible in discovery with display name & details
    ANONYMOUS = "ANONYMOUS"    # Visible in discovery without real name or private identifiers
    UNLISTED = "UNLISTED"      # Excluded from discovery and recommendations


class ContactPreference(str, enum.Enum):
    UPON_REQUEST = "UPON_REQUEST"  # Shared only after project owner approves interest
    OPEN = "OPEN"                  # Open to contact from registered students
    DISABLED = "DISABLED"          # No contact requests accepted


class ProjectStatus(str, enum.Enum):
    OPEN = "OPEN"              # Actively recruiting
    CLOSED = "CLOSED"          # Team full / recruitment ended
    COMPLETED = "COMPLETED"    # Project finished


class InterestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


def generate_uuid(prefix: str = "") -> str:
    """Generate a clean URL-safe unique identifier."""
    raw = uuid.uuid4().hex[:12]
    return f"{prefix}_{raw}" if prefix else raw


def generate_ownership_key() -> str:
    """
    Generate a cryptographically secure 32-character hex ownership key (128-bit entropy).
    Uses secrets.token_hex which uses os.urandom() — cryptographically secure on all platforms.
    """
    return secrets.token_hex(16)  # 16 bytes → 32 hex characters


def verify_ownership_key(provided: str, stored: str) -> bool:
    """
    Compare ownership keys using hmac.compare_digest to prevent timing-based side-channel attacks.
    Returns False for any None/empty inputs.
    """
    if not provided or not stored:
        return False
    return hmac.compare_digest(provided.strip(), stored)


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("std"))
    display_name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, index=True)
    programme = Column(String(100), nullable=False, index=True)
    academic_year = Column(Integer, nullable=False, index=True)  # 1, 2, 3, or 4

    # Technical qualifications & preferences (stored as structured JSON lists)
    technical_skills = Column(JSON, default=list, nullable=False)
    research_interests = Column(JSON, default=list, nullable=False)
    preferred_domains = Column(JSON, default=list, nullable=False)
    preferred_roles = Column(JSON, default=list, nullable=False)

    # Narrative & availability fields
    previous_experience = Column(Text, nullable=True)
    availability = Column(String(50), default="flexible", nullable=False)
    bio = Column(Text, nullable=True)
    project_ideas = Column(Text, nullable=True)

    # Privacy & status
    visibility = Column(Enum(ProfileVisibility), default=ProfileVisibility.PUBLIC, nullable=False)
    contact_preference = Column(Enum(ContactPreference), default=ContactPreference.UPON_REQUEST, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Prototype ownership key — NEVER returned in public responses or logged
    ownership_key = Column(String(64), nullable=False, default=generate_ownership_key)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owned_projects = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        foreign_keys="Project.owner_id",
    )
    team_memberships = relationship(
        "ProjectMember",
        back_populates="profile",
        cascade="all, delete-orphan",
    )
    interests_sent = relationship(
        "ProjectInterest",
        back_populates="profile",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_student_active_vis", "is_active", "visibility"),
    )


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("proj"))
    owner_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=False)

    domains = Column(JSON, default=list, nullable=False)
    required_skills = Column(JSON, default=list, nullable=False)
    preferred_roles = Column(JSON, default=list, nullable=False)

    additional_members_needed = Column(Integer, default=1, nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.OPEN, nullable=False, index=True)

    # Prototype ownership key — NEVER returned in public responses or logged
    ownership_key = Column(String(64), nullable=False, default=generate_ownership_key)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    owner = relationship("StudentProfile", back_populates="owned_projects", foreign_keys=[owner_id])
    members = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    interests = relationship(
        "ProjectInterest",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(100), nullable=True)
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="members")
    profile = relationship("StudentProfile", back_populates="team_memberships")


class ProjectInterest(Base):
    __tablename__ = "project_interests"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid("int"))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    profile_id = Column(String(36), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True)

    proposed_role = Column(String(100), nullable=True)
    message = Column(Text, nullable=True)
    status = Column(Enum(InterestStatus), default=InterestStatus.PENDING, nullable=False, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    project = relationship("Project", back_populates="interests")
    profile = relationship("StudentProfile", back_populates="interests_sent")
