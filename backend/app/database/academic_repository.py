"""
Academic Data Repository for GIKI Nexus.
Safely loads, indexes, and provides fast in-memory access to all cleaned and validated
academic datasets (units, faculty, courses, publications, research areas, programs, etc.).
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

logger = logging.getLogger(__name__)


class AcademicRepository:
    """
    In-memory indexed repository for GIKI Nexus academic entities.
    Loads processed datasets once at startup and provides constant-time lookups and filters.
    """

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.is_loaded: bool = False
        
        # Raw records containers
        self.units: List[Dict[str, Any]] = []
        self.faculty: List[Dict[str, Any]] = []
        self.courses: List[Dict[str, Any]] = []
        self.publications: List[Dict[str, Any]] = []
        self.research_areas: List[Dict[str, Any]] = []
        self.programs: List[Dict[str, Any]] = []
        self.other_personnel: List[Dict[str, Any]] = []
        self.coursehub_links: List[Dict[str, Any]] = []
        self.curation_queue: List[Dict[str, Any]] = []
        
        # Metadata containers
        self.metadata: Dict[str, Any] = {}

        # Primary dictionary indexes
        self._units_by_id: Dict[str, Dict[str, Any]] = {}
        self._faculty_by_id: Dict[str, Dict[str, Any]] = {}
        self._courses_by_code: Dict[str, Dict[str, Any]] = {}
        self._publications_by_id: Dict[str, Dict[str, Any]] = {}
        self._research_areas_by_id: Dict[str, Dict[str, Any]] = {}
        self._programs_by_id: Dict[str, Dict[str, Any]] = {}
        self._other_personnel_by_id: Dict[str, Dict[str, Any]] = {}
        self._coursehub_by_name: Dict[str, Dict[str, Any]] = {}
        
        # Secondary inverted indexes for fast filtering
        self._faculty_by_unit: Dict[str, List[Dict[str, Any]]] = {}
        self._faculty_by_research_area: Dict[str, List[Dict[str, Any]]] = {}
        self._publications_by_faculty: Dict[str, List[Dict[str, Any]]] = {}
        self._courses_by_unit: Dict[str, List[Dict[str, Any]]] = {}
        self._courses_by_program: Dict[str, List[Dict[str, Any]]] = {}
        self._programs_by_unit: Dict[str, List[Dict[str, Any]]] = {}

    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """Safely read and parse a JSON dataset file."""
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required academic dataset file '{filename}' was not found in directory: {self.data_dir}"
            )
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed JSON in dataset file '{file_path}': {e}") from e

    def load_datasets(self) -> None:
        """
        Loads all verified processed datasets from disk and builds in-memory indexes.
        """
        logger.info(f"Loading academic datasets from {self.data_dir}")

        # 1. Units
        units_raw = self._load_json_file("units.json")
        self.units = units_raw.get("units", [])
        self._units_by_id = {u["id"]: u for u in self.units if "id" in u}

        # 2. Faculty
        faculty_raw = self._load_json_file("faculty.json")
        self.faculty = faculty_raw.get("faculty", [])
        self._faculty_by_id = {f["id"]: f for f in self.faculty if "id" in f}

        # 3. Courses (preserves exact case for elective placeholders like CS3XX/CS4xx)
        courses_raw = self._load_json_file("courses.json")
        self.courses = courses_raw.get("courses", [])
        self._courses_by_code = {c["code"]: c for c in self.courses if "code" in c}
        self._courses_by_upper_code = {c["code"].upper(): c for c in self.courses if "code" in c}

        # 4. Publications
        pubs_raw = self._load_json_file("publications.json")
        raw_pubs = pubs_raw.get("publications", [])
        # Assign deterministic stable IDs for each publication in memory: pub_0001 ...
        self.publications = []
        self._publications_by_id = {}
        for idx, p in enumerate(raw_pubs, start=1):
            pub_record = dict(p)
            pub_id = f"pub_{idx:04d}"
            pub_record["id"] = pub_id
            self.publications.append(pub_record)
            self._publications_by_id[pub_id] = pub_record

        # 5. Research Areas
        areas_raw = self._load_json_file("research_areas.json")
        self.research_areas = areas_raw.get("research_areas", [])
        self._research_areas_by_id = {ra["id"]: ra for ra in self.research_areas if "id" in ra}

        # 6. Programs
        programs_raw = self._load_json_file("programs.json")
        self.programs = programs_raw.get("programs", [])
        self._programs_by_id = {prg["id"]: prg for prg in self.programs if "id" in prg}

        # 7. Other Personnel
        other_raw = self._load_json_file("other_personnel.json")
        self.other_personnel = other_raw.get("people", [])
        self._other_personnel_by_id = {op["id"]: op for op in self.other_personnel if "id" in op}

        # 8. CourseHub Instructor Links
        ch_raw = self._load_json_file("coursehub_instructor_links.json")
        self.coursehub_links = ch_raw.get("links", [])
        self._coursehub_by_name = {
            link["coursehub_name"].lower().strip(): link
            for link in self.coursehub_links
            if "coursehub_name" in link
        }

        # 9. Curation review queue (optional, if file present)
        try:
            review_raw = self._load_json_file("needs_review.json")
            self.curation_queue = review_raw.get("records", [])
        except (FileNotFoundError, ValueError):
            self.curation_queue = []

        # Build secondary inverted indexes for high-speed queries
        self._build_secondary_indexes()
        self.is_loaded = True
        logger.info(
            f"Successfully loaded and indexed {len(self.units)} units, "
            f"{len(self.faculty)} faculty, {len(self.courses)} courses, "
            f"{len(self.publications)} publications, {len(self.research_areas)} research areas, "
            f"{len(self.programs)} programs."
        )

    def _build_secondary_indexes(self) -> None:
        """Construct inverted indexes for fast one-to-many lookups."""
        self._faculty_by_unit.clear()
        self._faculty_by_research_area.clear()
        self._publications_by_faculty.clear()
        self._courses_by_unit.clear()
        self._courses_by_program.clear()
        self._programs_by_unit.clear()

        # Faculty by unit & research area
        for fac in self.faculty:
            for u in fac.get("units", []):
                self._faculty_by_unit.setdefault(u, []).append(fac)
            for ra_id in fac.get("research_area_ids", []):
                self._faculty_by_research_area.setdefault(ra_id, []).append(fac)

        # Publications by faculty
        for pub in self.publications:
            fid = pub.get("faculty_id")
            if fid:
                self._publications_by_faculty.setdefault(fid, []).append(pub)

        # Courses by unit & program
        for course in self.courses:
            unit = course.get("unit")
            if unit:
                self._courses_by_unit.setdefault(unit, []).append(course)
            for offering in course.get("offered_in", []):
                prog_id = offering.get("program_id")
                if prog_id:
                    self._courses_by_program.setdefault(prog_id, []).append(course)

        # Programs by unit
        for prog in self.programs:
            unit = prog.get("unit")
            if unit:
                self._programs_by_unit.setdefault(unit, []).append(prog)

    # ---------------------------------------------------------------------
    # Academic Units
    # ---------------------------------------------------------------------
    def get_all_units(self) -> List[Dict[str, Any]]:
        return list(self.units)

    def get_unit(self, unit_id: str) -> Optional[Dict[str, Any]]:
        if not unit_id:
            return None
        return self._units_by_id.get(unit_id.strip().lower())

    # ---------------------------------------------------------------------
    # Faculty Members
    # ---------------------------------------------------------------------
    def get_all_faculty(
        self,
        unit: Optional[str] = None,
        research_area: Optional[str] = None,
        verified_only: bool = False,
    ) -> List[Dict[str, Any]]:
        results = self.faculty
        if unit:
            unit_norm = unit.strip().lower()
            results = [f for f in results if unit_norm in [u.lower() for u in f.get("units", [])]]
        if research_area:
            ra_norm = research_area.strip().lower()
            results = [f for f in results if ra_norm in [r.lower() for r in f.get("research_area_ids", [])]]
        if verified_only:
            results = [f for f in results if f.get("verified") is True]
        return results

    def get_faculty(self, faculty_id: str) -> Optional[Dict[str, Any]]:
        if not faculty_id:
            return None
        return self._faculty_by_id.get(faculty_id.strip())

    def get_faculty_publications(self, faculty_id: str) -> List[Dict[str, Any]]:
        if not faculty_id:
            return []
        return self._publications_by_faculty.get(faculty_id.strip(), [])

    # ---------------------------------------------------------------------
    # Courses
    # ---------------------------------------------------------------------
    def get_all_courses(
        self,
        unit: Optional[str] = None,
        program_id: Optional[str] = None,
        is_lab: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        results = self.courses
        if unit:
            u_norm = unit.strip().lower()
            results = [c for c in results if c.get("unit") and c["unit"].lower() == u_norm]
        if program_id:
            p_norm = program_id.strip().lower()
            results = [
                c for c in results
                if any(off.get("program_id", "").lower() == p_norm for off in c.get("offered_in", []))
            ]
        if is_lab is not None:
            results = [c for c in results if c.get("is_lab") == is_lab]
        return results

    def get_course(self, course_code: str) -> Optional[Dict[str, Any]]:
        if not course_code:
            return None
        code_str = course_code.strip()
        # 1. Exact case match (handles CS3XX/CS4xx distinct placeholders)
        if code_str in self._courses_by_code:
            return self._courses_by_code[code_str]
        # 2. Uppercase match
        upper_code = code_str.upper()
        if upper_code in self._courses_by_upper_code:
            return self._courses_by_upper_code[upper_code]
        # 3. Strip interior spaces fallback (e.g. 'CS 101' -> 'CS101')
        collapsed = code_str.replace(" ", "").upper()
        if collapsed in self._courses_by_upper_code:
            return self._courses_by_upper_code[collapsed]
        return None

    # ---------------------------------------------------------------------
    # Publications
    # ---------------------------------------------------------------------
    def get_all_publications(
        self,
        faculty_id: Optional[str] = None,
        pub_type: Optional[str] = None,
        year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        results = self.publications
        if faculty_id:
            fid_norm = faculty_id.strip()
            results = [p for p in results if p.get("faculty_id") == fid_norm]
        if pub_type:
            pt_norm = pub_type.strip().lower()
            results = [p for p in results if p.get("type", "").lower() == pt_norm]
        if year is not None:
            results = [p for p in results if p.get("year") == year]
        return results

    def get_publication(self, publication_id: str) -> Optional[Dict[str, Any]]:
        if not publication_id:
            return None
        return self._publications_by_id.get(publication_id.strip())

    # ---------------------------------------------------------------------
    # Research Areas
    # ---------------------------------------------------------------------
    def get_all_research_areas(self, unit: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self.research_areas
        if unit:
            u_norm = unit.strip().lower()
            results = [ra for ra in results if u_norm in [u.lower() for u in ra.get("units", [])]]
        return results

    def get_research_area(self, area_id: str) -> Optional[Dict[str, Any]]:
        if not area_id:
            return None
        return self._research_areas_by_id.get(area_id.strip().lower())

    # ---------------------------------------------------------------------
    # Programs
    # ---------------------------------------------------------------------
    def get_all_programs(self, unit: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self.programs
        if unit:
            u_norm = unit.strip().lower()
            results = [prg for prg in results if prg.get("unit", "").lower() == u_norm]
        return results

    def get_program(self, program_id: str) -> Optional[Dict[str, Any]]:
        if not program_id:
            return None
        return self._programs_by_id.get(program_id.strip().lower())

    def get_program_curriculum(self, program_id: str) -> List[Dict[str, Any]]:
        """Return courses offered in the specified program, sorted by year and semester."""
        if not program_id:
            return []
        prog_norm = program_id.strip().lower()
        curriculum = []
        for course in self.courses:
            for off in course.get("offered_in", []):
                if off.get("program_id", "").lower() == prog_norm:
                    item = dict(course)
                    item["curriculum_placement"] = off
                    curriculum.append(item)
                    break
        
        # Sort by year, semester, course code
        curriculum.sort(
            key=lambda x: (
                x.get("curriculum_placement", {}).get("year") or 99,
                x.get("curriculum_placement", {}).get("semester") or 99,
                x.get("code", "")
            )
        )
        return curriculum

    # ---------------------------------------------------------------------
    # Other Personnel & CourseHub Links
    # ---------------------------------------------------------------------
    def get_all_other_personnel(self) -> List[Dict[str, Any]]:
        return list(self.other_personnel)

    def get_other_personnel(self, person_id: str) -> Optional[Dict[str, Any]]:
        if not person_id:
            return None
        return self._other_personnel_by_id.get(person_id.strip())

    def get_all_coursehub_links(self, match_status: Optional[str] = None) -> List[Dict[str, Any]]:
        results = self.coursehub_links
        if match_status:
            ms_norm = match_status.strip().lower()
            results = [lnk for lnk in results if lnk.get("match_status", "").lower() == ms_norm]
        return results

    def get_coursehub_link(self, instructor_name: str) -> Optional[Dict[str, Any]]:
        if not instructor_name:
            return None
        return self._coursehub_by_name.get(instructor_name.strip().lower())

    # ---------------------------------------------------------------------
    # General Search Across Academic Entities
    # ---------------------------------------------------------------------
    def search_academic(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Multi-entity text search across courses, faculty, research areas, and units.
        Returns rank-sorted list of matching items with entity_type and match explanation.
        """
        if not query or not query.strip():
            return []

        q = query.strip().lower()
        results: List[Dict[str, Any]] = []

        # 1. Match Courses (code or name or description)
        for c in self.courses:
            code = c.get("code", "").lower()
            name = (c.get("name") or "").lower()
            desc = (c.get("description") or "").lower()
            
            score = 0
            if q == code:
                score = 100
            elif q in code:
                score = 80
            elif q in name:
                score = 60
            elif q in desc:
                score = 30

            if score > 0:
                results.append({
                    "entity_type": "course",
                    "id": c.get("code"),
                    "title": f"{c.get('code')}: {c.get('name') or 'Course'}",
                    "subtitle": f"Unit: {c.get('unit', '').upper()} | Credits: {c.get('credits', 'N/A')}",
                    "score": score,
                    "data": c,
                })

        # 2. Match Faculty (name, designation, email, qualifications, research interests)
        for f in self.faculty:
            name = (f.get("name") or "").lower()
            fid = f.get("id", "").lower()
            desig = (f.get("preferred_designation") or f.get("designation") or "").lower()
            interests = " ".join(f.get("research_interests", [])).lower()
            
            score = 0
            if q == fid or q == name:
                score = 100
            elif q in name:
                score = 85
            elif q in desig:
                score = 50
            elif q in interests:
                score = 40

            if score > 0:
                results.append({
                    "entity_type": "faculty",
                    "id": f.get("id"),
                    "title": f.get("name"),
                    "subtitle": f"{f.get('preferred_designation') or f.get('designation') or 'Faculty'} ({', '.join(u.upper() for u in f.get('units', []))})",
                    "score": score,
                    "data": f,
                })

        # 3. Match Research Areas (label, aliases)
        for ra in self.research_areas:
            label = ra.get("label", "").lower()
            aliases = " ".join(ra.get("aliases", [])).lower()
            
            score = 0
            if q == label:
                score = 95
            elif q in label:
                score = 75
            elif q in aliases:
                score = 50

            if score > 0:
                results.append({
                    "entity_type": "research_area",
                    "id": ra.get("id"),
                    "title": ra.get("label"),
                    "subtitle": f"{ra.get('faculty_count', 0)} faculty members | Units: {', '.join(u.upper() for u in ra.get('units', []))}",
                    "score": score,
                    "data": ra,
                })

        # 4. Match Academic Units (short, name)
        for u in self.units:
            short = u.get("short", "").lower()
            name = u.get("name", "").lower()
            uid = u.get("id", "").lower()
            
            score = 0
            if q == short or q == uid:
                score = 95
            elif q in short or q in name:
                score = 70

            if score > 0:
                results.append({
                    "entity_type": "unit",
                    "id": u.get("id"),
                    "title": f"{u.get('short')}: {u.get('name')}",
                    "subtitle": f"Classification: {u.get('type')}",
                    "score": score,
                    "data": u,
                })

        # Sort by score descending and return top matches
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
