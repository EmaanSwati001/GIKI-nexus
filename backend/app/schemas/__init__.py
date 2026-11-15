"""
GIKI Nexus domain schemas.
Exports Pydantic models for data validation, serialization, and API contracts.
"""

from .domain import (
    UnitType,
    EmploymentStatus,
    PublicationType,
    InstructorMatchStatus,
    CurationStatus,
    ProvenanceMetadata,
    ProspectusCrossCheck,
    CourseOffering,
    AcademicUnit,
    FacultyMember,
    Course,
    Program,
    ResearchArea,
    Publication,
    OtherPersonnel,
    CourseHubInstructorLink,
    CurationQueueItem,
)

__all__ = [
    "UnitType",
    "EmploymentStatus",
    "PublicationType",
    "InstructorMatchStatus",
    "CurationStatus",
    "ProvenanceMetadata",
    "ProspectusCrossCheck",
    "CourseOffering",
    "AcademicUnit",
    "FacultyMember",
    "Course",
    "Program",
    "ResearchArea",
    "Publication",
    "OtherPersonnel",
    "CourseHubInstructorLink",
    "CurationQueueItem",
]
