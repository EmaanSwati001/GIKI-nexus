"""
Explainable Rule-Based Matching Engine for GIKI Nexus Teammate Finder.
Evaluates candidate profiles against project requirements and student preferences
without black-box ML or LLM hallucinations.
"""

from typing import List, Dict, Any, Set, Tuple
import re

from backend.app.models.teammates import StudentProfile, Project, ProfileVisibility
from backend.app.schemas.teammates import CandidateRecommendation, ProjectRecommendation


def _normalize_string_set(items: List[str]) -> Set[str]:
    """Normalize strings to lowercase stripped tokens for robust comparison."""
    result = set()
    for item in items or []:
        if isinstance(item, str):
            clean = item.strip().lower()
            if clean:
                result.add(clean)
    return result


def _find_matching_items(list_a: List[str], list_b: List[str]) -> List[str]:
    """Find case-insensitive common items, returning the original presentation casing from list_a."""
    norm_b = _normalize_string_set(list_b)
    matches = []
    seen = set()
    for item in list_a or []:
        if isinstance(item, str) and item.strip().lower() in norm_b:
            key = item.strip().lower()
            if key not in seen:
                seen.add(key)
                matches.append(item.strip())
    return matches


class MatchingEngine:
    """
    Transparent, explainable scoring engine for candidate-project compatibility.
    
    Default Scoring Weight Distribution (Total = 100):
      - Skill Match & Complementarity : 40% (fills critical missing team needs)
      - Domain & Research Interests   : 30% (shared topical focus)
      - Preferred Role Compatibility  : 15% (fills requested team role)
      - Availability Compatibility    : 10% (aligned time commitment)
      - Experience / Academic Year    :  5% (practical track record)
    """

    SKILL_WEIGHT: float = 40.0
    INTEREST_WEIGHT: float = 30.0
    ROLE_WEIGHT: float = 15.0
    AVAILABILITY_WEIGHT: float = 10.0
    EXPERIENCE_WEIGHT: float = 5.0

    @classmethod
    def evaluate_candidate_for_project(
        cls,
        candidate: StudentProfile,
        project: Project,
        current_team_profiles: List[StudentProfile],
    ) -> CandidateRecommendation:
        """
        Evaluate a single student candidate against a project's technical and team requirements.
        """
        # 1. Skills Evaluation (Weight: 40)
        req_skills = project.required_skills or []
        cand_skills = candidate.technical_skills or []
        
        # Determine skills already covered by current team
        team_skills_set = set()
        for member in current_team_profiles:
            team_skills_set.update(_normalize_string_set(member.technical_skills or []))
            
        req_norm = _normalize_string_set(req_skills)
        missing_team_skills_norm = req_norm - team_skills_set
        
        # Matching skills (candidate has, project needs)
        matching_skills = _find_matching_items(cand_skills, req_skills)
        
        # Missing skills covered (candidate brings skills the team currently lacks)
        missing_skills_covered = [
            s for s in cand_skills
            if isinstance(s, str) and s.strip().lower() in missing_team_skills_norm
        ]

        if req_skills:
            # Base match coverage (up to 25 pts)
            coverage_ratio = len(matching_skills) / max(1, len(req_skills))
            skill_base_score = min(25.0, coverage_ratio * 25.0)
            
            # Complementary bonus for filling missing team gaps (up to 15 pts)
            if missing_team_skills_norm:
                fill_ratio = len(missing_skills_covered) / max(1, len(missing_team_skills_norm))
                skill_bonus = min(15.0, fill_ratio * 15.0)
            else:
                skill_bonus = 10.0 if matching_skills else 0.0
                
            skill_score = skill_base_score + skill_bonus
        else:
            # Baseline if project has not specified skills
            skill_score = 20.0 if cand_skills else 10.0

        # 2. Domain & Research Interests (Weight: 30)
        proj_domains = project.domains or []
        cand_domains = (candidate.preferred_domains or []) + (candidate.research_interests or [])
        shared_interests = _find_matching_items(cand_domains, proj_domains)
        
        if proj_domains:
            domain_ratio = len(shared_interests) / max(1, min(3, len(proj_domains)))
            interest_score = min(cls.INTEREST_WEIGHT, domain_ratio * cls.INTEREST_WEIGHT)
        else:
            interest_score = 15.0 if cand_domains else 5.0

        # 3. Role Compatibility (Weight: 15)
        proj_roles = project.preferred_roles or []
        cand_roles = candidate.preferred_roles or []
        role_matches = _find_matching_items(cand_roles, proj_roles)
        role_compatible = len(role_matches) > 0
        
        if proj_roles:
            if role_compatible:
                role_score = 15.0
            elif not cand_roles or any("flexible" in r.lower() for r in cand_roles):
                role_score = 10.0
                role_compatible = True
            else:
                role_score = 0.0
        else:
            role_score = 12.0
            role_compatible = True

        # 4. Availability Compatibility (Weight: 10)
        cand_avail = (candidate.availability or "flexible").lower()
        # High compatibility for flexible or active commitments
        if "flexible" in cand_avail or "20" in cand_avail or "15" in cand_avail:
            avail_score = 10.0
            avail_compatible = True
        elif "10" in cand_avail:
            avail_score = 8.0
            avail_compatible = True
        else:
            avail_score = 5.0
            avail_compatible = True

        # 5. Experience Alignment (Weight: 5)
        exp_score = 0.0
        if candidate.previous_experience and len(candidate.previous_experience.strip()) > 10:
            exp_score += 3.0
        if candidate.academic_year in [2, 3, 4]:
            exp_score += 2.0
        elif candidate.academic_year == 1:
            exp_score += 1.0

        # Total rule-based score
        total_score = round(skill_score + interest_score + role_score + avail_score + exp_score, 1)
        total_score = max(0.0, min(100.0, total_score))

        # Build human-readable transparent explanation
        explanation_parts = []
        if matching_skills:
            explanation_parts.append(
                f"Offers {len(matching_skills)} required skill(s) ({', '.join(matching_skills[:3])})"
            )
        if missing_skills_covered:
            explanation_parts.append(
                f"Fills critical team skill gap(s) ({', '.join(missing_skills_covered[:3])})"
            )
        if shared_interests:
            explanation_parts.append(
                f"Shares project domain interest(s) in {', '.join(shared_interests[:2])}"
            )
        if role_compatible and role_matches:
            explanation_parts.append(f"Prefers requested role '{role_matches[0]}'")
        elif role_compatible:
            explanation_parts.append("Has flexible role availability")

        if not explanation_parts:
            explanation_parts.append("Potential general collaborator based on availability and academic profile")

        full_explanation = (
            f"Compatibility alignment: {'; '.join(explanation_parts)}. "
            f"(Score reflects rule-based alignment, not a guarantee of team performance)."
        )

        vis = getattr(candidate, "visibility", None)
        is_anon = (vis == ProfileVisibility.ANONYMOUS or getattr(vis, "value", None) == "ANONYMOUS")
        display_name = (
            f"Anonymous Student ({candidate.programme}, Year {candidate.academic_year})"
            if is_anon else candidate.display_name
        )

        return CandidateRecommendation(
            profile_id=candidate.id,
            display_name=display_name,
            programme=candidate.programme,
            academic_year=candidate.academic_year,
            is_anonymous=is_anon,
            availability=candidate.availability,
            skills_offered=candidate.technical_skills or [],
            overall_score=total_score,
            score_breakdown={
                "skills_score": round(skill_score, 1),
                "interests_score": round(interest_score, 1),
                "role_score": round(role_score, 1),
                "availability_score": round(avail_score, 1),
                "experience_score": round(exp_score, 1),
            },
            shared_interests=shared_interests,
            matching_skills=matching_skills,
            missing_skills_covered=missing_skills_covered,
            matched_roles=role_matches,
            role_compatibility=role_compatible,
            availability_compatibility=avail_compatible,
            explanation=full_explanation,
        )

    @classmethod
    def calculate_fit(
        cls,
        candidate: StudentProfile,
        project: Project,
        existing_team: List[StudentProfile] = None,
    ) -> CandidateRecommendation:
        """Alias for evaluate_candidate_for_project for clean fit calculation."""
        return cls.evaluate_candidate_for_project(
            candidate=candidate,
            project=project,
            current_team_profiles=existing_team or [],
        )

    @classmethod
    def evaluate_project_for_student(
        cls,
        student: StudentProfile,
        project: Project,
    ) -> ProjectRecommendation:
        """
        Evaluate a project's alignment with a student seeking a team to join.
        """
        # Re-use candidate evaluation logic
        cand_rec = cls.evaluate_candidate_for_project(
            candidate=student,
            project=project,
            current_team_profiles=[],
        )

        return ProjectRecommendation(
            project_id=project.id,
            project_title=project.title,
            domains=project.domains or [],
            required_skills=project.required_skills or [],
            preferred_roles=project.preferred_roles or [],
            overall_score=cand_rec.overall_score,
            score_breakdown=cand_rec.score_breakdown,
            shared_interests=cand_rec.shared_interests,
            matching_skills=cand_rec.matching_skills,
            skills_contributed=cand_rec.missing_skills_covered or cand_rec.matching_skills,
            role_compatibility=cand_rec.role_compatibility,
            explanation=cand_rec.explanation,
        )
