"""
GIKI Nexus domain schemas.
Exports Pydantic models for data validation, serialization, and API contracts.
"""

from .domain import (
    UnitType,
    EmploymentStatus,
    PublicationType,
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
)

__all__ = [
    "UnitType",
    "EmploymentStatus",
    "PublicationType",
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
]
