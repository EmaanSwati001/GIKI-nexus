"""
Academic Knowledge Graph Service for GIKI Nexus.
Builds and queries a directed property multigraph using NetworkX representing
academic entities (Units, Faculty, Courses, Research Areas, Publications, Programs)
and their official relationships.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx

from backend.app.database.academic_repository import AcademicRepository

logger = logging.getLogger(__name__)


class AcademicGraphService:
    """
    NetworkX-based in-memory academic knowledge graph service.
    Implements multi-relational queries, prerequisite chain resolution,
    and subgraph extractions for GIKI academic exploration.
    """

    def __init__(self):
        # Directed multigraph to support multiple relationship types between identical entities
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self._is_built: bool = False

    @staticmethod
    def make_node_id(entity_type: str, entity_id: str) -> str:
        """Create a namespaced unique node identifier."""
        return f"{entity_type.lower()}:{str(entity_id).strip()}"

    def build_graph(self, repo: AcademicRepository) -> None:
        """
        Constructs the knowledge graph from an initialized AcademicRepository.
        Adheres to relationship definitions in docs/design/academic_relationships.md.
        """
        logger.info("Building Academic Knowledge Graph from repository...")
        self.graph.clear()

        # -----------------------------------------------------------------
        # 1. Add AcademicUnit Nodes & UNIT_SUB_DEPARTMENT_OF Edges
        # -----------------------------------------------------------------
        for unit in repo.get_all_units():
            u_id = unit.get("id")
            if not u_id:
                continue
            node_id = self.make_node_id("unit", u_id)
            self.graph.add_node(
                node_id,
                entity_type="AcademicUnit",
                id=u_id,
                name=unit.get("name"),
                short=unit.get("short"),
                type=unit.get("type"),
                source_url=unit.get("source_url"),
                raw_data=unit,
            )

        for unit in repo.get_all_units():
            u_id = unit.get("id")
            parent_id = unit.get("parent")
            if parent_id and parent_id != u_id:
                source = self.make_node_id("unit", u_id)
                target = self.make_node_id("unit", parent_id)
                if self.graph.has_node(source) and self.graph.has_node(target):
                    self.graph.add_edge(
                        source,
                        target,
                        key="UNIT_SUB_DEPARTMENT_OF",
                        relationship="UNIT_SUB_DEPARTMENT_OF",
                        verification_status="verified",
                    )

        # -----------------------------------------------------------------
        # 2. Add ResearchArea Nodes
        # -----------------------------------------------------------------
        for ra in repo.get_all_research_areas():
            ra_id = ra.get("id")
            if not ra_id:
                continue
            node_id = self.make_node_id("research_area", ra_id)
            self.graph.add_node(
                node_id,
                entity_type="ResearchArea",
                id=ra_id,
                label=ra.get("label"),
                faculty_count=ra.get("faculty_count", 0),
                raw_data=ra,
            )

        # -----------------------------------------------------------------
        # 3. Add Faculty Nodes, MEMBER_BELONGS_TO_UNIT, & MEMBER_HAS_RESEARCH_AREA
        # -----------------------------------------------------------------
        for fac in repo.get_all_faculty():
            f_id = fac.get("id")
            if not f_id:
                continue
            f_node = self.make_node_id("faculty", f_id)
            self.graph.add_node(
                f_node,
                entity_type="FacultyMember",
                id=f_id,
                name=fac.get("name"),
                designation=fac.get("preferred_designation") or fac.get("designation"),
                academic_rank=fac.get("academic_rank"),
                administrative_role=fac.get("administrative_role"),
                email=fac.get("email"),
                verified=fac.get("verified", False),
                profile_url=fac.get("profile_url"),
                raw_data=fac,
            )

            # MEMBER_BELONGS_TO_UNIT (supports dual appointments like prof-dr-nisar-ahmed)
            for u_id in fac.get("units", []):
                u_node = self.make_node_id("unit", u_id)
                if self.graph.has_node(u_node):
                    self.graph.add_edge(
                        f_node,
                        u_node,
                        key="MEMBER_BELONGS_TO_UNIT",
                        relationship="MEMBER_BELONGS_TO_UNIT",
                        verification_status="verified",
                    )

            # MEMBER_HAS_RESEARCH_AREA
            for ra_id in fac.get("research_area_ids", []):
                ra_node = self.make_node_id("research_area", ra_id)
                if self.graph.has_node(ra_node):
                    self.graph.add_edge(
                        f_node,
                        ra_node,
                        key="MEMBER_HAS_RESEARCH_AREA",
                        relationship="MEMBER_HAS_RESEARCH_AREA",
                        verification_status="verified",
                    )

        # -----------------------------------------------------------------
        # 4. Add Publication Nodes & MEMBER_AUTHORED_PUBLICATION Edges
        # -----------------------------------------------------------------
        for pub in repo.get_all_publications():
            pub_id = pub.get("id")
            f_id = pub.get("faculty_id")
            if not pub_id or not f_id:
                continue
            pub_node = self.make_node_id("publication", pub_id)
            self.graph.add_node(
                pub_node,
                entity_type="Publication",
                id=pub_id,
                citation=pub.get("citation"),
                type=pub.get("type"),
                year=pub.get("year"),
                doi=pub.get("doi"),
                raw_data=pub,
            )

            f_node = self.make_node_id("faculty", f_id)
            if self.graph.has_node(f_node):
                self.graph.add_edge(
                    f_node,
                    pub_node,
                    key="MEMBER_AUTHORED_PUBLICATION",
                    relationship="MEMBER_AUTHORED_PUBLICATION",
                    verification_status="verified",
                )

        # -----------------------------------------------------------------
        # 5. Add Program Nodes & PROGRAM_OFFERED_BY Edges
        # -----------------------------------------------------------------
        for prog in repo.get_all_programs():
            prog_id = prog.get("id")
            if not prog_id:
                continue
            prog_node = self.make_node_id("program", prog_id)
            self.graph.add_node(
                prog_node,
                entity_type="Program",
                id=prog_id,
                name=prog.get("name"),
                unit=prog.get("unit"),
                raw_data=prog,
            )

            u_id = prog.get("unit")
            if u_id:
                u_node = self.make_node_id("unit", u_id)
                if self.graph.has_node(u_node):
                    self.graph.add_edge(
                        prog_node,
                        u_node,
                        key="PROGRAM_OFFERED_BY",
                        relationship="PROGRAM_OFFERED_BY",
                        verification_status="verified",
                    )

        # -----------------------------------------------------------------
        # 6. Add Course Nodes, COURSE_BELONGS_TO_UNIT, PROGRAM_CONTAINS_COURSE,
        #    and COURSE_HAS_PREREQUISITE
        # -----------------------------------------------------------------
        # Index node IDs for both exact case and uppercase to support robust lookup
        course_node_lookup: Dict[str, str] = {}
        for course in repo.get_all_courses():
            c_code = course.get("code")
            if not c_code:
                continue
            c_node = self.make_node_id("course", c_code)
            course_node_lookup[c_code] = c_node
            course_node_lookup[c_code.upper()] = c_node

            self.graph.add_node(
                c_node,
                entity_type="Course",
                id=c_code,
                name=course.get("name"),
                credits=course.get("credits"),
                credit_hours=course.get("credit_hours"),
                unit=course.get("unit"),
                unit_mapping_source=course.get("unit_mapping_source"),
                unresolved_prerequisites=course.get("unresolved_prerequisites", []),
                prerequisite_statuses=course.get("prerequisite_statuses", {}),
                is_lab=course.get("is_lab", False),
                raw_data=course,
            )

            # COURSE_BELONGS_TO_UNIT
            u_id = course.get("unit")
            if u_id:
                u_node = self.make_node_id("unit", u_id)
                if self.graph.has_node(u_node):
                    self.graph.add_edge(
                        c_node,
                        u_node,
                        key="COURSE_BELONGS_TO_UNIT",
                        relationship="COURSE_BELONGS_TO_UNIT",
                        source_rule=course.get("unit_mapping_source", "unknown"),
                    )

            # PROGRAM_CONTAINS_COURSE
            for off in course.get("offered_in", []):
                prog_id = off.get("program_id")
                if prog_id:
                    prog_node = self.make_node_id("program", prog_id)
                    if self.graph.has_node(prog_node):
                        self.graph.add_edge(
                            prog_node,
                            c_node,
                            key="PROGRAM_CONTAINS_COURSE",
                            relationship="PROGRAM_CONTAINS_COURSE",
                            year=off.get("year"),
                            semester=off.get("semester"),
                            name_in_catalog=off.get("name_in_catalog"),
                        )

        # Prerequisite Edges (COURSE_HAS_PREREQUISITE)
        # Note rule: Unresolved prerequisites are NOT added as fake Course nodes.
        # They remain tracked in course node attributes. Only valid catalog courses get edges.
        for course in repo.get_all_courses():
            c_code = course.get("code")
            c_node = course_node_lookup.get(c_code)
            if not c_node:
                continue
            for prereq_code in course.get("prerequisites", []):
                p_clean = prereq_code.strip()
                p_node = course_node_lookup.get(p_clean) or course_node_lookup.get(p_clean.upper())
                if p_node and self.graph.has_node(p_node):
                    self.graph.add_edge(
                        c_node,
                        p_node,
                        key="COURSE_HAS_PREREQUISITE",
                        relationship="COURSE_HAS_PREREQUISITE",
                        status="resolved",
                    )

        # -----------------------------------------------------------------
        # 7. Add CourseHubInstructorLink Nodes & INSTRUCTOR_MAPS_TO_FACULTY Edges
        # -----------------------------------------------------------------
        for link in repo.get_all_coursehub_links():
            ch_name = link.get("coursehub_name")
            if not ch_name:
                continue
            ch_fac = link.get("coursehub_faculty") or ""
            # Composite ID ensures faculty dual entries (e.g. Dr. Memoon Sajid in FCSE & FEE) are distinct
            ch_key = f"{ch_name}::{ch_fac}" if ch_fac else ch_name
            ch_node = self.make_node_id("coursehub_link", ch_key)
            self.graph.add_node(
                ch_node,
                entity_type="CourseHubInstructorLink",
                id=ch_name,
                coursehub_faculty=ch_fac,
                match_status=link.get("match_status"),
                match_score=link.get("match_score"),
                match_method=link.get("match_method"),
                suggested_faculty_id=link.get("suggested_faculty_id"),
                raw_data=link,
            )

            # Edge to faculty only for verified matched records
            f_id = link.get("faculty_id")
            if f_id:
                f_node = self.make_node_id("faculty", f_id)
                if self.graph.has_node(f_node):
                    self.graph.add_edge(
                        ch_node,
                        f_node,
                        key="INSTRUCTOR_MAPS_TO_FACULTY",
                        relationship="INSTRUCTOR_MAPS_TO_FACULTY",
                        match_status=link.get("match_status"),
                        match_score=link.get("match_score"),
                    )

        # -----------------------------------------------------------------
        # 8. Add OtherPersonnel Nodes (isolated, no academic relationships)
        # -----------------------------------------------------------------
        for person in repo.get_all_other_personnel():
            p_id = person.get("id")
            if not p_id:
                continue
            p_node = self.make_node_id("other_personnel", p_id)
            self.graph.add_node(
                p_node,
                entity_type="OtherPersonnel",
                id=p_id,
                name=person.get("name"),
                designation=person.get("designation"),
                note=person.get("note"),
                raw_data=person,
            )

        self._is_built = True
        stats = self.get_graph_stats()
        logger.info(
            f"Knowledge Graph successfully built: {stats['total_nodes']} nodes, "
            f"{stats['total_edges']} edges across {len(stats['node_counts'])} entity types."
        )

    # ---------------------------------------------------------------------
    # Graph Inspection & Statistics
    # ---------------------------------------------------------------------
    def get_graph_stats(self) -> Dict[str, Any]:
        """Return comprehensive node and relationship counts."""
        node_counts: Dict[str, int] = {}
        for _, data in self.graph.nodes(data=True):
            etype = data.get("entity_type", "Unknown")
            node_counts[etype] = node_counts.get(etype, 0) + 1

        rel_counts: Dict[str, int] = {}
        for _, _, _, data in self.graph.edges(data=True, keys=True):
            rtype = data.get("relationship", "Unknown")
            rel_counts[rtype] = rel_counts.get(rtype, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_counts": node_counts,
            "relationship_counts": rel_counts,
        }

    def _find_course_node(self, course_code: str) -> Optional[str]:
        """Find the matching course node ID in the graph, checking exact and uppercase variants."""
        c_clean = course_code.strip()
        node = self.make_node_id("course", c_clean)
        if self.graph.has_node(node):
            return node
        node_upper = self.make_node_id("course", c_clean.upper())
        if self.graph.has_node(node_upper):
            return node_upper
        node_collapsed = self.make_node_id("course", c_clean.replace(" ", "").upper())
        if self.graph.has_node(node_collapsed):
            return node_collapsed
        return None

    # ---------------------------------------------------------------------
    # Course Queries & Prerequisite Trees
    # ---------------------------------------------------------------------
    def get_course_prerequisites(self, course_code: str) -> Dict[str, Any]:
        """
        Retrieve direct prerequisites, recursive dependency tree,
        and explicitly tracked unresolved prerequisite codes for a course.
        """
        c_node = self._find_course_node(course_code)

        if not c_node or not self.graph.has_node(c_node):
            return {
                "course_code": course_code,
                "found": False,
                "direct_prerequisites": [],
                "prerequisite_chain": [],
                "unresolved_prerequisites": [],
            }

        c_data = self.graph.nodes[c_node]
        unresolved = c_data.get("unresolved_prerequisites", [])

        # Direct resolved prerequisites
        direct: List[Dict[str, Any]] = []
        for _, target, data in self.graph.out_edges(c_node, data=True):
            if data.get("relationship") == "COURSE_HAS_PREREQUISITE":
                target_data = self.graph.nodes[target]
                direct.append({
                    "code": target_data.get("id"),
                    "name": target_data.get("name"),
                    "credits": target_data.get("credits"),
                    "status": "resolved",
                })

        # Add tracked unresolved prerequisites to direct summary
        for ucode in unresolved:
            direct.append({
                "code": ucode,
                "name": None,
                "credits": None,
                "status": "unresolved",
                "notes": "Code not cataloged as standalone course in prospectus",
            })

        # Recursive prerequisite chain (DFS without cycles)
        chain: List[str] = []
        visited: Set[str] = set()

        def dfs(node: str):
            for _, nxt, edata in self.graph.out_edges(node, data=True):
                if edata.get("relationship") == "COURSE_HAS_PREREQUISITE":
                    if nxt not in visited:
                        visited.add(nxt)
                        nxt_code = self.graph.nodes[nxt].get("id")
                        if nxt_code:
                            chain.append(nxt_code)
                        dfs(nxt)

        dfs(c_node)

        return {
            "course_code": c_data.get("id"),
            "found": True,
            "direct_prerequisites": direct,
            "prerequisite_chain": chain,
            "unresolved_prerequisites": unresolved,
        }

    def get_course_relationships(self, course_code: str) -> Dict[str, Any]:
        """Retrieve all incoming and outgoing connections for a course."""
        c_node = self._find_course_node(course_code)

        if not c_node or not self.graph.has_node(c_node):
            return {"course_code": course_code, "found": False}

        c_data = self.graph.nodes[c_node]
        prereqs = self.get_course_prerequisites(course_code)

        # Parent academic unit
        unit = None
        for _, target, data in self.graph.out_edges(c_node, data=True):
            if data.get("relationship") == "COURSE_BELONGS_TO_UNIT":
                unit_data = self.graph.nodes[target]
                unit = {
                    "id": unit_data.get("id"),
                    "name": unit_data.get("name"),
                    "short": unit_data.get("short"),
                    "source_rule": data.get("source_rule"),
                }
                break

        # Programs containing this course
        programs: List[Dict[str, Any]] = []
        for src, _, data in self.graph.in_edges(c_node, data=True):
            if data.get("relationship") == "PROGRAM_CONTAINS_COURSE":
                prog_data = self.graph.nodes[src]
                programs.append({
                    "id": prog_data.get("id"),
                    "name": prog_data.get("name"),
                    "year": data.get("year"),
                    "semester": data.get("semester"),
                    "name_in_catalog": data.get("name_in_catalog"),
                })

        # Courses for which this course is a prerequisite
        dependent_courses: List[Dict[str, Any]] = []
        for src, _, data in self.graph.in_edges(c_node, data=True):
            if data.get("relationship") == "COURSE_HAS_PREREQUISITE":
                dep_data = self.graph.nodes[src]
                dependent_courses.append({
                    "code": dep_data.get("id"),
                    "name": dep_data.get("name"),
                })

        return {
            "course_code": c_data.get("id"),
            "name": c_data.get("name"),
            "found": True,
            "unit": unit,
            "programs": programs,
            "prerequisites": prereqs,
            "dependent_courses": dependent_courses,
        }

    # ---------------------------------------------------------------------
    # Faculty Queries
    # ---------------------------------------------------------------------
    def get_faculty_relationships(self, faculty_id: str) -> Dict[str, Any]:
        """Retrieve unit memberships, research areas, publications, and CourseHub links."""
        f_node = self.make_node_id("faculty", faculty_id.strip())
        if not self.graph.has_node(f_node):
            return {"faculty_id": faculty_id, "found": False}

        f_data = self.graph.nodes[f_node]

        # Units (supports dual appointments)
        units: List[Dict[str, Any]] = []
        for _, target, data in self.graph.out_edges(f_node, data=True):
            if data.get("relationship") == "MEMBER_BELONGS_TO_UNIT":
                u_data = self.graph.nodes[target]
                units.append({
                    "id": u_data.get("id"),
                    "name": u_data.get("name"),
                    "short": u_data.get("short"),
                })

        # Research areas
        research_areas: List[Dict[str, Any]] = []
        for _, target, data in self.graph.out_edges(f_node, data=True):
            if data.get("relationship") == "MEMBER_HAS_RESEARCH_AREA":
                ra_data = self.graph.nodes[target]
                research_areas.append({
                    "id": ra_data.get("id"),
                    "label": ra_data.get("label"),
                })

        # Publication count
        pub_count = 0
        for _, _, data in self.graph.out_edges(f_node, data=True):
            if data.get("relationship") == "MEMBER_AUTHORED_PUBLICATION":
                pub_count += 1

        # CourseHub Links
        coursehub_links: List[Dict[str, Any]] = []
        for src, _, data in self.graph.in_edges(f_node, data=True):
            if data.get("relationship") == "INSTRUCTOR_MAPS_TO_FACULTY":
                ch_data = self.graph.nodes[src]
                coursehub_links.append({
                    "coursehub_name": ch_data.get("id"),
                    "match_status": data.get("match_status"),
                    "match_score": data.get("match_score"),
                })

        return {
            "faculty_id": f_data.get("id"),
            "name": f_data.get("name"),
            "found": True,
            "units": units,
            "research_areas": research_areas,
            "publication_count": pub_count,
            "coursehub_links": coursehub_links,
        }

    def get_faculty_research_areas(self, faculty_id: str) -> List[Dict[str, Any]]:
        """Return list of research areas for a faculty member."""
        rels = self.get_faculty_relationships(faculty_id)
        return rels.get("research_areas", [])

    def get_research_area_faculty(self, area_id: str) -> List[Dict[str, Any]]:
        """Return list of faculty members active in a research area."""
        ra_node = self.make_node_id("research_area", area_id.strip().lower())
        if not self.graph.has_node(ra_node):
            return []

        faculty_list: List[Dict[str, Any]] = []
        for src, _, data in self.graph.in_edges(ra_node, data=True):
            if data.get("relationship") == "MEMBER_HAS_RESEARCH_AREA":
                f_data = self.graph.nodes[src]
                faculty_list.append({
                    "id": f_data.get("id"),
                    "name": f_data.get("name"),
                    "designation": f_data.get("designation"),
                    "email": f_data.get("email"),
                    "verified": f_data.get("verified"),
                })
        return faculty_list

    # ---------------------------------------------------------------------
    # Subgraph Extraction for Exploration & Visualization
    # ---------------------------------------------------------------------
    def get_entity_subgraph(self, entity_type: str, entity_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        Extract an ego-subgraph centered around an entity up to specified hop depth.
        Returns serialized nodes and edges for graph visualization.
        """
        center_node = self.make_node_id(entity_type, entity_id)
        if not self.graph.has_node(center_node):
            return {"nodes": [], "edges": []}

        # Ego graph traversal
        visited_nodes: Set[str] = {center_node}
        current_layer: Set[str] = {center_node}

        for _ in range(depth):
            next_layer: Set[str] = set()
            for n in current_layer:
                # Include both successors and predecessors
                neighbors = set(self.graph.successors(n)).union(set(self.graph.predecessors(n)))
                for neighbor in neighbors:
                    if neighbor not in visited_nodes:
                        # Exclude overwhelming publication nodes from 1-hop expansions unless requested
                        if not neighbor.startswith("publication:"):
                            visited_nodes.add(neighbor)
                            next_layer.add(neighbor)
            current_layer = next_layer

        sub_g = self.graph.subgraph(visited_nodes)

        nodes: List[Dict[str, Any]] = []
        for n, data in sub_g.nodes(data=True):
            nodes.append({
                "id": n,
                "entity_type": data.get("entity_type"),
                "label": data.get("name") or data.get("label") or data.get("id"),
                "is_center": n == center_node,
            })

        edges: List[Dict[str, Any]] = []
        for u, v, _, edata in sub_g.edges(data=True, keys=True):
            edges.append({
                "source": u,
                "target": v,
                "relationship": edata.get("relationship"),
                "verification_status": edata.get("verification_status") or edata.get("source_rule"),
            })

        return {"nodes": nodes, "edges": edges}
