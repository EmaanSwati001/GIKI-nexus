"""
Academic Service for GIKI Nexus.
Coordinates the AcademicRepository and AcademicGraphService to provide
business logic, multi-faceted filtering, and enriched responses for the REST API.
"""

import logging
from typing import Dict, List, Optional, Any

from backend.app.database.academic_repository import AcademicRepository
from backend.app.graph.service import AcademicGraphService

logger = logging.getLogger(__name__)


class AcademicService:
    """
    Core service coordinating data retrieval, relationship exploration,
    and search across all GIKI academic entities.
    """

    def __init__(self, repo: AcademicRepository, graph_service: AcademicGraphService):
        self.repo = repo
        self.graph = graph_service

    # ---------------------------------------------------------------------
    # Academic Units
    # ---------------------------------------------------------------------
    def get_units(self) -> List[Dict[str, Any]]:
        """Return all academic units with member counts and sub-departments."""
        units = self.repo.get_all_units()
        enriched = []
        for u in units:
            item = dict(u)
            uid = u.get("id")
            # Calculate faculty count
            fac_in_unit = self.repo.get_all_faculty(unit=uid)
            item["faculty_count"] = len(fac_in_unit)
            # Find sub-departments
            sub_depts = [
                d.get("id") for d in units
                if d.get("parent") == uid and d.get("id") != uid
            ]
            item["sub_departments"] = sub_depts
            enriched.append(item)
        return enriched

    def get_unit(self, unit_id: str) -> Optional[Dict[str, Any]]:
        """Return single unit details with faculty members and degree programs."""
        u = self.repo.get_unit(unit_id)
        if not u:
            return None
        item = dict(u)
        uid = u.get("id")
        item["faculty"] = [
            {
                "id": f.get("id"),
                "name": f.get("name"),
                "designation": f.get("preferred_designation") or f.get("designation"),
                "verified": f.get("verified"),
            }
            for f in self.repo.get_all_faculty(unit=uid)
        ]
        item["programs"] = [
            {"id": p.get("id"), "name": p.get("name")}
            for p in self.repo.get_all_programs(unit=uid)
        ]
        return item

    # ---------------------------------------------------------------------
    # Faculty Members
    # ---------------------------------------------------------------------
    def get_faculty_list(
        self,
        unit: Optional[str] = None,
        research_area: Optional[str] = None,
        verified_only: bool = False,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Return paginated faculty members with optional filtering."""
        all_fac = self.repo.get_all_faculty(
            unit=unit,
            research_area=research_area,
            verified_only=verified_only,
        )

        if search and search.strip():
            q = search.strip().lower()
            all_fac = [
                f for f in all_fac
                if q in f.get("name", "").lower()
                or q in (f.get("preferred_designation") or f.get("designation") or "").lower()
                or any(q in ra.lower() for ra in f.get("research_interests", []))
                or any(q in u.lower() for u in f.get("units", []))
            ]

        total = len(all_fac)
        paginated = all_fac[skip : skip + limit]

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": paginated,
        }

    def get_faculty_member(self, faculty_id: str) -> Optional[Dict[str, Any]]:
        """Return single faculty member details enriched with graph relationships."""
        fac = self.repo.get_faculty(faculty_id)
        if not fac:
            return None
        item = dict(fac)
        # Enrich with graph relationships
        rels = self.graph.get_faculty_relationships(faculty_id)
        item["graph_relationships"] = rels
        return item

    def get_faculty_publications(self, faculty_id: str) -> List[Dict[str, Any]]:
        """Return all publications for a specific faculty member."""
        return self.repo.get_faculty_publications(faculty_id)

    def get_faculty_research_areas(self, faculty_id: str) -> List[Dict[str, Any]]:
        """Return research areas linked to a faculty member."""
        return self.graph.get_faculty_research_areas(faculty_id)

    # ---------------------------------------------------------------------
    # Courses
    # ---------------------------------------------------------------------
    def get_courses_list(
        self,
        unit: Optional[str] = None,
        program_id: Optional[str] = None,
        is_lab: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Return paginated course catalog with filters."""
        all_courses = self.repo.get_all_courses(
            unit=unit,
            program_id=program_id,
            is_lab=is_lab,
        )

        if search and search.strip():
            q = search.strip().lower()
            all_courses = [
                c for c in all_courses
                if q in c.get("code", "").lower()
                or q in (c.get("name") or "").lower()
                or q in (c.get("title") or "").lower()
                or q in (c.get("description") or "").lower()
                or (c.get("unit") and q in c["unit"].lower())
            ]

        total = len(all_courses)
        paginated = all_courses[skip : skip + limit]

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": paginated,
        }

    def get_course(self, course_code: str) -> Optional[Dict[str, Any]]:
        """Return single course details."""
        return self.repo.get_course(course_code)

    def get_course_prerequisites(self, course_code: str) -> Dict[str, Any]:
        """Return full prerequisite graph breakdown for a course."""
        return self.graph.get_course_prerequisites(course_code)

    def get_course_related_entities(self, course_code: str) -> Dict[str, Any]:
        """Return all entities connected to this course (unit, programs, prereqs)."""
        return self.graph.get_course_relationships(course_code)

    # ---------------------------------------------------------------------
    # Research Areas
    # ---------------------------------------------------------------------
    def get_research_areas(
        self,
        unit: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Return paginated research areas."""
        all_areas = self.repo.get_all_research_areas(unit=unit)

        if search and search.strip():
            q = search.strip().lower()
            all_areas = [
                ra for ra in all_areas
                if q in ra.get("label", "").lower()
                or any(q in alias.lower() for alias in ra.get("aliases", []))
            ]

        total = len(all_areas)
        paginated = [
            {**ra, "name": ra.get("name") or ra.get("label", ra.get("id", ""))}
            for ra in all_areas[skip : skip + limit]
        ]

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": paginated,
        }

    def get_research_area(self, area_id: str) -> Optional[Dict[str, Any]]:
        """Return research area details with linked faculty members."""
        ra = self.repo.get_research_area(area_id)
        if not ra:
            return None
        item = dict(ra)
        item["faculty_members"] = self.graph.get_research_area_faculty(area_id)
        return item

    def get_research_area_faculty(self, area_id: str) -> List[Dict[str, Any]]:
        """Return faculty members in this research area."""
        return self.graph.get_research_area_faculty(area_id)

    # ---------------------------------------------------------------------
    # Publications
    # ---------------------------------------------------------------------
    def get_publications_list(
        self,
        faculty_id: Optional[str] = None,
        pub_type: Optional[str] = None,
        year: Optional[int] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Return paginated publications with filters."""
        all_pubs = self.repo.get_all_publications(
            faculty_id=faculty_id,
            pub_type=pub_type,
            year=year,
        )

        if search and search.strip():
            q = search.strip().lower()
            all_pubs = [
                p for p in all_pubs
                if q in p.get("citation", "").lower()
                or (p.get("doi") and q in p["doi"].lower())
            ]

        total = len(all_pubs)
        paginated = all_pubs[skip : skip + limit]

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": paginated,
        }

    def get_publication(self, pub_id: str) -> Optional[Dict[str, Any]]:
        """Return single publication by ID."""
        return self.repo.get_publication(pub_id)

    # ---------------------------------------------------------------------
    # Programs & Curriculum
    # ---------------------------------------------------------------------
    def get_programs(self, unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all degree programs with course counts, unit details, and duration."""
        programs = self.repo.get_all_programs(unit=unit)
        result = []
        for p in programs:
            pid = p.get("id")
            unit_id = p.get("unit_id") or p.get("unit")
            unit_obj = self.repo.get_unit(unit_id) if unit_id else None
            curriculum = self.repo.get_program_curriculum(pid)
            result.append({
                **p,
                "unit_id": unit_id,
                "unit_name": unit_obj.get("name") if unit_obj else (p.get("faculty") or unit_id),
                "code": p.get("code") or p.get("id", "").replace("bs-", "BS ").replace("-", " ").upper(),
                "duration_years": p.get("duration_years", 4),
                "degree_level": p.get("degree_level", "BS"),
                "course_count": len(curriculum),
            })
        return result

    def get_program(self, program_id: str) -> Optional[Dict[str, Any]]:
        """Return single degree program details with enriched metadata."""
        p = self.repo.get_program(program_id)
        if not p:
            return None
        unit_id = p.get("unit_id") or p.get("unit")
        unit_obj = self.repo.get_unit(unit_id) if unit_id else None
        curriculum = self.repo.get_program_curriculum(program_id)
        return {
            **p,
            "unit_id": unit_id,
            "unit_name": unit_obj.get("name") if unit_obj else (p.get("faculty") or unit_id),
            "code": p.get("code") or p.get("id", "").replace("bs-", "BS ").replace("-", " ").upper(),
            "duration_years": p.get("duration_years", 4),
            "degree_level": p.get("degree_level", "BS"),
            "course_count": len(curriculum),
        }

    def get_program_curriculum(self, program_id: str) -> Dict[str, Any]:
        """Return curriculum courses cleanly organized semester by semester (Semesters 1-8)."""
        prg = self.get_program(program_id)
        if not prg:
            return {
                "found": False,
                "program_id": program_id,
                "semesters": {},
                "total_courses": 0,
                "total_semesters": 0,
            }

        curriculum = self.repo.get_program_curriculum(program_id)

        semester_labels = {
            1: "Semester 1 (Freshman - Fall)",
            2: "Semester 2 (Freshman - Spring)",
            3: "Semester 3 (Sophomore - Fall)",
            4: "Semester 4 (Sophomore - Spring)",
            5: "Semester 5 (Junior - Fall)",
            6: "Semester 6 (Junior - Spring)",
            7: "Semester 7 (Senior - Fall)",
            8: "Semester 8 (Senior - Spring)",
        }

        # Initialize semesters dictionary in order
        semesters_dict: Dict[str, List[Dict[str, Any]]] = {
            label: [] for label in semester_labels.values()
        }

        formatted_courses = []
        for c in curriculum:
            placement = c.get("curriculum_placement", {})
            sem_num = placement.get("semester")

            cr = c.get("credit_hours")
            is_lab = bool(c.get("is_lab")) or (str(c.get("code", "")).endswith("L"))
            cr_display = f"{cr} Cr" if cr is not None else ("1 Cr (Lab)" if is_lab else "")

            title = c.get("title") or c.get("name") or c.get("code")
            name = c.get("name") or c.get("title") or c.get("code")

            prereqs = c.get("prerequisites") or []
            clean_prereqs = []
            for pre in prereqs:
                if isinstance(pre, str):
                    clean_prereqs.append(pre)
                elif isinstance(pre, dict):
                    clean_prereqs.append(pre.get("code") or pre.get("course_code") or str(pre))

            formatted_c = {
                "code": c.get("code"),
                "title": title,
                "name": name,
                "credit_hours": cr,
                "credits_display": cr_display,
                "is_lab": is_lab,
                "prerequisites": clean_prereqs,
                "year": placement.get("year"),
                "semester": sem_num,
                "program_id": program_id,
            }
            formatted_courses.append(formatted_c)

            if sem_num in semester_labels:
                semesters_dict[semester_labels[sem_num]].append(formatted_c)
            elif sem_num:
                custom_label = f"Semester {sem_num}"
                semesters_dict.setdefault(custom_label, []).append(formatted_c)
            else:
                semesters_dict.setdefault("Electives & Core Requirements", []).append(formatted_c)

        # Retain only semesters that have courses
        clean_semesters = {k: v for k, v in semesters_dict.items() if len(v) > 0}

        return {
            "found": True,
            "program": prg,
            "total_courses": len(formatted_courses),
            "total_semesters": len(clean_semesters),
            "semesters": clean_semesters,
            "curriculum": formatted_courses,
        }

    # ---------------------------------------------------------------------
    # Search & Graph
    # ---------------------------------------------------------------------
    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Unified multi-entity search."""
        return self.repo.search_academic(query=query, limit=limit)

    def get_graph_stats(self) -> Dict[str, Any]:
        """Knowledge graph statistics."""
        return self.graph.get_graph_stats()

    def get_entity_subgraph(self, entity_type: str, entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """Subgraph for entity visualization."""
        return self.graph.get_entity_subgraph(entity_type=entity_type, entity_id=entity_id, depth=depth)
