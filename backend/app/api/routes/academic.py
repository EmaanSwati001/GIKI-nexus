"""
REST API endpoints for GIKI Nexus Academic & Research Discovery (Module A).
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.app.services.academic_service import AcademicService

router = APIRouter(tags=["Academic Discovery"])


def get_service(request: Request) -> AcademicService:
    """Dependency provider for AcademicService from application state."""
    service = getattr(request.app.state, "academic_service", None)
    if not service:
        raise HTTPException(status_code=500, detail="Academic service is not initialized.")
    return service


# -------------------------------------------------------------------------
# Academic Units
# -------------------------------------------------------------------------
@router.get("/units", summary="List all academic units")
def list_units(service: AcademicService = Depends(get_service)) -> List[Dict[str, Any]]:
    """Retrieve all faculties, departments, and schools with metadata."""
    return service.get_units()


@router.get("/units/{unit_id}", summary="Get academic unit details")
def get_unit(unit_id: str, service: AcademicService = Depends(get_service)) -> Dict[str, Any]:
    """Retrieve details for a specific academic unit, including faculty and degree programs."""
    unit = service.get_unit(unit_id)
    if not unit:
        raise HTTPException(status_code=404, detail=f"Academic unit '{unit_id}' not found.")
    return unit


# -------------------------------------------------------------------------
# Faculty Members
# -------------------------------------------------------------------------
@router.get("/faculty", summary="List and filter faculty members")
def list_faculty(
    unit: Optional[str] = Query(None, description="Filter by academic unit slug (e.g. 'fcse', 'fee')"),
    research_area: Optional[str] = Query(None, description="Filter by research area ID"),
    verified_only: bool = Query(False, description="Filter to verified faculty only"),
    search: Optional[str] = Query(None, description="Keyword search in name, designation, or interests"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    service: AcademicService = Depends(get_service),
) -> Dict[str, Any]:
    """Retrieve paginated faculty profiles with multi-faceted filtering."""
    return service.get_faculty_list(
        unit=unit,
        research_area=research_area,
        verified_only=verified_only,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/faculty/{faculty_id}", summary="Get faculty profile")
def get_faculty(faculty_id: str, service: AcademicService = Depends(get_service)) -> Dict[str, Any]:
    """Retrieve complete faculty profile, credentials, and graph relationships."""
    fac = service.get_faculty_member(faculty_id)
    if not fac:
        raise HTTPException(status_code=404, detail=f"Faculty member '{faculty_id}' not found.")
    return fac


@router.get("/faculty/{faculty_id}/research-areas", summary="Get faculty research areas")
def get_faculty_research_areas(
    faculty_id: str, service: AcademicService = Depends(get_service)
) -> List[Dict[str, Any]]:
    """Retrieve research areas associated with a faculty member."""
    fac = service.repo.get_faculty(faculty_id)
    if not fac:
        raise HTTPException(status_code=404, detail=f"Faculty member '{faculty_id}' not found.")
    return service.get_faculty_research_areas(faculty_id)


@router.get("/faculty/{faculty_id}/publications", summary="Get faculty publications")
def get_faculty_publications(
    faculty_id: str, service: AcademicService = Depends(get_service)
) -> List[Dict[str, Any]]:
    """Retrieve publication citations for a faculty member."""
    fac = service.repo.get_faculty(faculty_id)
    if not fac:
        raise HTTPException(status_code=404, detail=f"Faculty member '{faculty_id}' not found.")
    return service.get_faculty_publications(faculty_id)


# -------------------------------------------------------------------------
# Courses
# -------------------------------------------------------------------------
@router.get("/courses", summary="List and filter courses")
def list_courses(
    unit: Optional[str] = Query(None, description="Filter by offering academic unit"),
    program_id: Optional[str] = Query(None, description="Filter by program degree slug"),
    is_lab: Optional[bool] = Query(None, description="Filter lab vs lecture courses"),
    search: Optional[str] = Query(None, description="Search course code, title, or syllabus"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    service: AcademicService = Depends(get_service),
) -> Dict[str, Any]:
    """Retrieve paginated courses from the GIKI catalog."""
    return service.get_courses_list(
        unit=unit,
        program_id=program_id,
        is_lab=is_lab,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/courses/{course_code}", summary="Get course details")
def get_course(course_code: str, service: AcademicService = Depends(get_service)) -> Dict[str, Any]:
    """Retrieve details for a course code."""
    course = service.get_course(course_code)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_code}' not found.")
    return course


@router.get("/courses/{course_code}/prerequisites", summary="Get course prerequisites")
def get_course_prerequisites(
    course_code: str, service: AcademicService = Depends(get_service)
) -> Dict[str, Any]:
    """
    Retrieve direct prerequisites, recursive dependency tree,
    and unresolved prerequisite codes for a course.
    """
    course = service.get_course(course_code)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_code}' not found.")
    return service.get_course_prerequisites(course_code)


@router.get("/courses/{course_code}/related", summary="Get related academic entities")
def get_course_related_entities(
    course_code: str, service: AcademicService = Depends(get_service)
) -> Dict[str, Any]:
    """Retrieve programs offering this course, unit, and prerequisite network."""
    course = service.get_course(course_code)
    if not course:
        raise HTTPException(status_code=404, detail=f"Course '{course_code}' not found.")
    return service.get_course_related_entities(course_code)


# -------------------------------------------------------------------------
# Research Areas
# -------------------------------------------------------------------------
@router.get("/research-areas", summary="List research areas")
def list_research_areas(
    unit: Optional[str] = Query(None, description="Filter by associated unit"),
    search: Optional[str] = Query(None, description="Keyword search in research topics"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    service: AcademicService = Depends(get_service),
) -> Dict[str, Any]:
    """Retrieve normalized academic research areas and domains."""
    return service.get_research_areas(unit=unit, search=search, skip=skip, limit=limit)


@router.get("/research-areas/{area_id}", summary="Get research area details")
def get_research_area(
    area_id: str, service: AcademicService = Depends(get_service)
) -> Dict[str, Any]:
    """Retrieve research area details with active faculty members."""
    ra = service.get_research_area(area_id)
    if not ra:
        raise HTTPException(status_code=404, detail=f"Research area '{area_id}' not found.")
    return ra


@router.get("/research-areas/{area_id}/faculty", summary="Get faculty in research area")
def get_research_area_faculty(
    area_id: str, service: AcademicService = Depends(get_service)
) -> List[Dict[str, Any]]:
    """Retrieve faculty members active in a research area."""
    ra = service.repo.get_research_area(area_id)
    if not ra:
        raise HTTPException(status_code=404, detail=f"Research area '{area_id}' not found.")
    return service.get_research_area_faculty(area_id)


# -------------------------------------------------------------------------
# Publications
# -------------------------------------------------------------------------
@router.get("/publications", summary="List publications")
def list_publications(
    faculty_id: Optional[str] = Query(None, description="Filter by author faculty ID"),
    pub_type: Optional[str] = Query(None, description="Filter by type (journal, conference, patent)"),
    year: Optional[int] = Query(None, description="Filter by publication year"),
    search: Optional[str] = Query(None, description="Search citations or DOI"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    service: AcademicService = Depends(get_service),
) -> Dict[str, Any]:
    """Retrieve paginated publication citations."""
    return service.get_publications_list(
        faculty_id=faculty_id,
        pub_type=pub_type,
        year=year,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/publications/{publication_id}", summary="Get publication details")
def get_publication(
    publication_id: str, service: AcademicService = Depends(get_service)
) -> Dict[str, Any]:
    """Retrieve a single publication citation by ID."""
    pub = service.get_publication(publication_id)
    if not pub:
        raise HTTPException(status_code=404, detail=f"Publication '{publication_id}' not found.")
    return pub


# -------------------------------------------------------------------------
# Degree Programs
# -------------------------------------------------------------------------
@router.get("/programs", summary="List degree programs")
def list_programs(
    unit: Optional[str] = Query(None, description="Filter by academic unit"),
    service: AcademicService = Depends(get_service),
) -> List[Dict[str, Any]]:
    """Retrieve all BS degree programs."""
    return service.get_programs(unit=unit)


@router.get("/programs/{program_id}", summary="Get program details")
def get_program(program_id: str, service: AcademicService = Depends(get_service)) -> Dict[str, Any]:
    """Retrieve single program details."""
    prg = service.get_program(program_id)
    if not prg:
        raise HTTPException(status_code=404, detail=f"Program '{program_id}' not found.")
    return prg


@router.get("/programs/{program_id}/curriculum", summary="Get program curriculum roadmap")
def get_program_curriculum(
    program_id: str, service: AcademicService = Depends(get_service)
) -> Dict[str, Any]:
    """Retrieve program curriculum structured by year and semester."""
    prg = service.get_program(program_id)
    if not prg:
        raise HTTPException(status_code=404, detail=f"Program '{program_id}' not found.")
    return service.get_program_curriculum(program_id)


# -------------------------------------------------------------------------
# Search & Knowledge Graph
# -------------------------------------------------------------------------
@router.get("/search", summary="Unified academic search")
def search_academic(
    q: str = Query(..., min_length=1, description="Query string across academic entities"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    service: AcademicService = Depends(get_service),
) -> List[Dict[str, Any]]:
    """Search courses, faculty, research domains, and academic units."""
    return service.search(query=q, limit=limit)


@router.get("/graph/stats", summary="Get knowledge graph statistics")
def get_graph_stats(service: AcademicService = Depends(get_service)) -> Dict[str, Any]:
    """Retrieve node and relationship statistics from the knowledge graph."""
    return service.get_graph_stats()


@router.get("/graph/entity/{entity_type}/{entity_id}", summary="Get entity subgraph")
def get_entity_subgraph(
    entity_type: str,
    entity_id: str,
    depth: int = Query(1, ge=1, le=2, description="Hop depth for visualization"),
    service: AcademicService = Depends(get_service),
) -> Dict[str, Any]:
    """Extract an ego-subgraph for an academic entity."""
    return service.get_entity_subgraph(entity_type=entity_type, entity_id=entity_id, depth=depth)
