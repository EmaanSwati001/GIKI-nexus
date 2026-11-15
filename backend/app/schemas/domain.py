"""
GIKI Nexus Domain Models (Pydantic v2 Schemas).
Represents core entities for the academic knowledge graph and discovery platform.
Pure schema definitions with validation and serialization — no database persistence.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class UnitType(str, Enum):
    FACULTY = "faculty"
    DEPARTMENT = "department"
    SCHOOL = "school"


class EmploymentStatus(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    ON_STUDY_LEAVE = "on_study_leave"


class PublicationType(str, Enum):
    JOURNAL = "journal"
    CONFERENCE = "conference"
    BOOK_OR_CHAPTER = "book_or_chapter"
    PATENT = "patent"
    UNSPECIFIED = "unspecified"


class InstructorMatchStatus(str, Enum):
    MATCHED = "matched"
    SUGGESTED = "suggested"
    UNMATCHED = "unmatched"
    NEEDS_REVIEW = "needs_review"


class CurationStatus(str, Enum):
    RESOLVED = "resolved"
    NEEDS_REVIEW = "needs_review"
    INFORMATIONAL = "informational"


class ProvenanceMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")
    sources: List[str] = Field(default_factory=list, description="Source URLs or reference document citations")
    scraped_at: Optional[str] = Field(default=None, description="ISO timestamp of initial data collection")


class ProspectusCrossCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    listed_as: Optional[str] = Field(default=None, description="Exact name string found in prospectus")
    detail: Optional[str] = Field(default=None, description="Qualifications and affiliation from prospectus")
    section: Optional[str] = Field(default=None, description="Prospectus category heading (e.g. Lab Engineer)")
    match_score: Optional[float] = Field(default=None, description="String similarity score (0.0 to 1.0)")
    review_needed: bool = Field(default=False, description="Flag indicating possible false positive match")


class CourseOffering(BaseModel):
    model_config = ConfigDict(extra="ignore")
    program_id: str = Field(..., description="ID of program offering this course (e.g. 'bs-computer-science')")
    year: Optional[int] = Field(default=None, description="Academic year within curriculum (1-4)")
    semester: Optional[int] = Field(default=None, description="Curriculum semester (1-8)")
    name_in_catalog: Optional[str] = Field(default=None, description="Exact course title in program catalog")


# -------------------------------------------------------------------------
# Core Domain Entities
# -------------------------------------------------------------------------

class AcademicUnit(BaseModel):
    """Represents an organizational academic unit (Faculty, Department, or School)."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique slug identifier (e.g. 'fcse', 'dmse')")
    name: str = Field(..., description="Full official unit title")
    short: str = Field(..., description="Official acronym/abbreviation (e.g. 'FCSE', 'DMSE')")
    type: UnitType = Field(..., description="Classification (faculty, department, school)")
    parent: Optional[str] = Field(default=None, description="Parent unit ID if sub-department (e.g. 'fmce')")
    listing: Optional[str] = Field(default=None, description="Relative URL path of faculty profile listing")
    source_url: Optional[str] = Field(default=None, description="Canonical absolute listing URL")


class FacultyMember(BaseModel):
    """Represents an academic faculty member at GIKI."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique person slug derived from personnel URL")
    name: str = Field(..., description="Full name with status markers removed")
    designation: Optional[str] = Field(default=None, description="Primary academic designation from department roster")
    designation_on_profile_page: Optional[str] = Field(default=None, description="Designation from personal page")
    status: EmploymentStatus = Field(default=EmploymentStatus.ACTIVE, description="Active or on leave status")
    units: List[str] = Field(default_factory=list, description="Associated academic unit IDs (supports dual appointments)")
    email: Optional[str] = Field(default=None, description="Official GIKI email address")
    phone_or_ext: Optional[str] = Field(default=None, description="Office phone or extension")
    office: Optional[str] = Field(default=None, description="Room number / building location")
    qualifications_raw: Optional[str] = Field(default=None, description="Unparsed raw qualifications string")
    qualifications: List[str] = Field(default_factory=list, description="Structured list of degrees/credentials")
    qualifications_summary: Optional[str] = Field(default=None, description="Narrative qualifications if not structured")
    research_interests_raw: Optional[str] = Field(default=None, description="Unparsed research interests text")
    research_interests: List[str] = Field(default_factory=list, description="List of cleaned research topic strings")
    research_summary: Optional[str] = Field(default=None, description="Narrative research summary if not structured")
    bio: Optional[str] = Field(default=None, description="Biographical summary paragraph")
    publication_count_on_profile: int = Field(default=0, description="Count of parsed citations")
    profile_sections: List[str] = Field(default_factory=list, description="Profile section headings present")
    photo_url: Optional[str] = Field(default=None, description="URL of faculty profile portrait")
    profile_url: str = Field(..., description="Canonical personal URL on giki.edu.pk")
    listing_urls: List[str] = Field(default_factory=list, description="URLs of rosters where member appears")
    website_categories: List[str] = Field(default_factory=list, description="WordPress category tags")
    prospectus_2025: Optional[ProspectusCrossCheck] = Field(default=None, description="Prospectus match metadata")
    provenance: ProvenanceMetadata = Field(default_factory=ProvenanceMetadata, description="Origin sources and scrape timestamp")
    missing_fields: List[str] = Field(default_factory=list, description="List of missing expected fields")
    verified: bool = Field(default=False, description="True if unit and academic credentials confirmed")
    research_area_ids: List[str] = Field(default_factory=list, description="Slugs of linked research area nodes")
    preferred_designation: Optional[str] = Field(default=None, description="Preferred display designation")
    academic_rank: Optional[str] = Field(default=None, description="Extracted academic rank (e.g. Professor, Lecturer)")
    administrative_role: Optional[str] = Field(default=None, description="Extracted administrative role (e.g. HoD, Dean)")
    professional_credentials: List[str] = Field(default_factory=list, description="Professional credentials (e.g. HEC Approved PhD Supervisor)")
    designation_discrepancy: bool = Field(default=False, description="True if listing designation differs from profile page")
    designation_review_status: Optional[str] = Field(default=None, description="Resolution status of designation discrepancy")


class Course(BaseModel):
    """Represents a curriculum course."""
    model_config = ConfigDict(extra="ignore")

    code: str = Field(..., description="Standardized course code (e.g. 'CS101', 'CS3XX/CS4xx')")
    name: Optional[str] = Field(default=None, description="Full official course title")
    credits: Optional[str] = Field(default=None, description="Standardized lecture-lab-credit format (e.g. '3-0-3')")
    credit_hours: Optional[int] = Field(default=None, description="Total credit hours as integer")
    prerequisites: List[str] = Field(default_factory=list, description="Course codes required as prerequisites")
    prerequisites_raw: Optional[str] = Field(default=None, description="Unparsed prerequisite clause")
    description: Optional[str] = Field(default=None, description="Course syllabus and description")
    unit: Optional[str] = Field(default=None, description="Academic unit offering course (null if unassigned)")
    unit_mapping_source: Optional[str] = Field(default=None, description="Source of unit mapping ('prospectus_verified' or 'prefix_based_mapping')")
    unresolved_prerequisites: List[str] = Field(default_factory=list, description="Prerequisite codes not found in active catalog")
    prerequisite_statuses: Dict[str, str] = Field(default_factory=dict, description="Status per prerequisite code ('resolved' or 'unresolved')")
    offered_in: List[CourseOffering] = Field(default_factory=list, description="Program curriculum placements")
    is_lab: bool = Field(default=False, description="True if course is a laboratory session")
    provenance: ProvenanceMetadata = Field(default_factory=ProvenanceMetadata, description="Sources of syllabus / curriculum")


class Program(BaseModel):
    """Represents an academic degree program."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Slug identifier (e.g. 'bs-computer-science')")
    name: str = Field(..., description="Full program title")
    unit: str = Field(..., description="ID of host academic unit")
    coursehub_program_id: Optional[int] = Field(default=None, description="ID from CourseHub catalog snapshot")


class ResearchArea(BaseModel):
    """Represents a normalized academic research domain or topic."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Normalized topic slug (e.g. 'computational-fluid-dynamics')")
    label: str = Field(..., description="Canonical display title")
    aliases: List[str] = Field(default_factory=list, description="Variant spellings, abbreviations, or raw synonyms")
    faculty_ids: List[str] = Field(default_factory=list, description="Faculty member IDs active in this domain")
    faculty_count: int = Field(default=0, description="Count of associated faculty members")
    units: List[str] = Field(default_factory=list, description="Academic units conducting research in this area")


class Publication(BaseModel):
    """Represents an academic paper, book chapter, or patent citation."""
    model_config = ConfigDict(extra="ignore")

    faculty_id: str = Field(..., description="Faculty member ID who authored/listed this publication")
    citation: str = Field(..., description="Verbatim citation string")
    type: PublicationType = Field(default=PublicationType.UNSPECIFIED, description="Publication classification")
    section_heading: Optional[str] = Field(default=None, description="Profile tab heading where citation was listed")
    year: Optional[int] = Field(default=None, description="Extracted publication year")
    doi: Optional[str] = Field(default=None, description="Digital Object Identifier if available")


class OtherPersonnel(BaseModel):
    """Represents non-active faculty personnel with profile URLs on giki.edu.pk."""
    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Personnel slug identifier")
    name: str = Field(..., description="Full name")
    designation: Optional[str] = Field(default=None, description="Job title or role")
    email: Optional[str] = Field(default=None, description="Contact email")
    office: Optional[str] = Field(default=None, description="Office location")
    website_categories: List[str] = Field(default_factory=list, description="WordPress category tags")
    profile_sections: List[str] = Field(default_factory=list, description="Section headings on profile")
    profile_url: str = Field(..., description="Canonical profile URL")
    note: str = Field(..., description="Explanation of why personnel is isolated from current faculty roster")
    provenance: ProvenanceMetadata = Field(default_factory=ProvenanceMetadata, description="Origin sources and timestamp")


class CourseHubInstructorLink(BaseModel):
    """Represents instructor name linkage between CourseHub and GIKI Nexus."""
    model_config = ConfigDict(extra="ignore")

    coursehub_name: str = Field(..., description="Instructor name string from CourseHub")
    coursehub_faculty: Optional[str] = Field(default=None, description="Faculty code from CourseHub")
    faculty_id: Optional[str] = Field(default=None, description="Matched GIKI Nexus faculty ID (null if unmatched)")
    match_method: Optional[str] = Field(default=None, description="Algorithm used for match (full_name, partial, null)")
    match_score: Optional[float] = Field(default=None, description="String similarity score (0.0 to 1.0)")
    match_status: InstructorMatchStatus = Field(default=InstructorMatchStatus.UNMATCHED, description="Matching status (matched, suggested, unmatched, needs_review)")
    suggested_faculty_id: Optional[str] = Field(default=None, description="Suggested faculty ID pending confirmation")
    notes: Optional[str] = Field(default=None, description="Curation and resolution notes")


class CurationQueueItem(BaseModel):
    """Represents a standardized issue or decision item in the curation review queue."""
    model_config = ConfigDict(extra="ignore")

    entity_type: str = Field(..., description="Entity type ('course', 'faculty', 'coursehub_instructor')")
    id: str = Field(..., description="Unique entity identifier")
    name: Optional[str] = Field(default=None, description="Entity display name")
    units: List[str] = Field(default_factory=list, description="Associated academic units")
    category: str = Field(..., description="Issue category (e.g. 'missing_unit', 'broken_prerequisite')")
    reasons: List[str] = Field(default_factory=list, description="Descriptions of the issue")
    resolution_status: CurationStatus = Field(default=CurationStatus.NEEDS_REVIEW, description="Resolution status")
    resolution_notes: Optional[str] = Field(default=None, description="Explanation of resolution or next steps")
    source_info: Optional[Dict[str, Any]] = Field(default=None, description="Provenance or metadata context")
    profile_url: Optional[str] = Field(default=None, description="Canonical web URL if available")
