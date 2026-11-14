"""
GIKI Nexus data processing package.
Provides data audit, cleaning, normalization, validation, and pipeline execution.
"""

from .cleaner import (
    normalize_text,
    normalize_label,
    clean_string_list,
    sanitize_email,
    clean_phone,
    clean_course_code,
)
from .validator import (
    ValidationReport,
    validate_units,
    validate_faculty,
    validate_courses,
    validate_publications,
    validate_research_areas,
    validate_programs,
)
from .entities import (
    process_units,
    process_faculty,
    process_courses,
    process_publications,
    process_research_areas,
    process_programs,
    process_other_personnel,
    process_coursehub_links,
    build_curation_queue,
)
from .pipeline import DataPipeline

__all__ = [
    "normalize_text",
    "normalize_label",
    "clean_string_list",
    "sanitize_email",
    "clean_phone",
    "clean_course_code",
    "ValidationReport",
    "validate_units",
    "validate_faculty",
    "validate_courses",
    "validate_publications",
    "validate_research_areas",
    "validate_programs",
    "process_units",
    "process_faculty",
    "process_courses",
    "process_publications",
    "process_research_areas",
    "process_programs",
    "process_other_personnel",
    "process_coursehub_links",
    "build_curation_queue",
    "DataPipeline",
]
