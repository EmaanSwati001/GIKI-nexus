// GIKI Nexus Unified TypeScript Domain Interfaces

export interface Unit {
  id: string;
  name: string;
  type: string;
  code?: string;
  description?: string;
  programs?: string[];
  head?: string;
}

export interface Course {
  id: string;
  code: string;
  title: string;
  credit_hours?: number;
  credits_formatted?: string;
  description?: string;
  unit?: string;
  unit_mapping_source?: string;
  prerequisites: string[];
  unresolved_prerequisites: string[];
  prerequisite_statuses?: Record<string, string>;
  offered_in: string[];
}

export interface Faculty {
  id: string;
  name: string;
  designation?: string;
  academic_rank?: string;
  administrative_role?: string;
  units: string[];
  email?: string;
  profile_url?: string;
  qualifications: string[];
  research_interests: string[];
  verified: boolean;
  citation_count?: number;
  publications_count?: number;
}

export interface Publication {
  id: string;
  citation: string;
  title?: string;
  authors: string[];
  year?: number;
  faculty_id: string;
  faculty_name?: string;
  venue?: string;
  doi?: string;
}

export interface ResearchArea {
  id: string;
  name: string;
  slug?: string;
  faculty_count?: number;
  faculty_ids?: string[];
  unit_ids?: string[];
  unit_names?: string[];
}

export interface Program {
  id: string;
  name: string;
  code: string;
  unit_id: string;
  unit_name?: string;
  degree_level: string;
  duration_years?: number;
  course_count?: number;
  curriculum?: Record<string, any>;
}

export interface GraphStats {
  total_nodes?: number;
  total_edges?: number;
  node_count?: number;
  edge_count?: number;
  node_counts?: Record<string, number>;
  relationship_counts?: Record<string, number>;
  node_types?: Record<string, number>;
  edge_types?: Record<string, number>;
}

export interface GraphNode {
  id: string;
  label: string;
  type?: string;
  entity_type?: string;
  is_center?: boolean;
  details?: Record<string, any>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type?: string;
  relationship?: string;
  verification_status?: string;
  metadata?: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Module B: Teammate Finder Interfaces
export type ProfileVisibility = 'PUBLIC' | 'ANONYMOUS' | 'UNLISTED';
export type ContactPreference = 'ALWAYS' | 'UPON_REQUEST' | 'NEVER';
export type ProjectStatus = 'OPEN' | 'IN_PROGRESS' | 'COMPLETED' | 'CLOSED';
export type InterestStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface StudentProfile {
  id: string;
  display_name: string;
  programme: string;
  academic_year: number;
  technical_skills: string[];
  research_interests: string[];
  preferred_domains: string[];
  preferred_roles: string[];
  availability: string;
  previous_experience?: string;
  bio?: string;
  project_ideas?: string;
  visibility: ProfileVisibility;
  contact_preference: ContactPreference;
  is_active: boolean;
  is_anonymous: boolean;
  created_at: string;
  updated_at: string;
  ownership_key?: string; // Only present in private response at creation
  email?: string; // Private
}

export interface ProjectMember {
  profile_id: string;
  display_name: string;
  programme: string;
  role?: string;
  joined_at: string;
}

export interface Project {
  id: string;
  owner_id: string;
  owner_name?: string;
  title: string;
  description: string;
  domains: string[];
  required_skills: string[];
  preferred_roles: string[];
  additional_members_needed: number;
  status: ProjectStatus;
  members: ProjectMember[];
  created_at: string;
  updated_at: string;
  ownership_key?: string; // Present only on ProjectCreateResponse
}

export interface CandidateRecommendation {
  profile_id: string;
  display_name: string;
  programme: string;
  academic_year: number;
  is_anonymous: boolean;
  availability: string;
  skills_offered: string[];
  overall_score: number;
  score_breakdown: {
    skills_score: number;
    interests_score: number;
    role_score: number;
    availability_score: number;
    experience_score: number;
  };
  shared_interests: string[];
  matching_skills: string[];
  missing_skills_covered: string[];
  matched_roles: string[];
  role_compatibility: boolean;
  availability_compatibility: boolean;
  explanation: string;
}

export interface ProjectRecommendation {
  project_id: string;
  project_title: string;
  domains: string[];
  required_skills: string[];
  preferred_roles: string[];
  overall_score: number;
  score_breakdown: Record<string, number>;
  shared_interests: string[];
  matching_skills: string[];
  skills_contributed: string[];
  role_compatibility: boolean;
  explanation: string;
}

export interface ProjectInterest {
  id: string;
  project_id: string;
  project_title?: string;
  profile_id: string;
  requester_name?: string;
  requester_programme?: string;
  proposed_role?: string;
  message?: string;
  status: InterestStatus;
  created_at: string;
  updated_at: string;
  shared_contact_email?: string | null;
}

export interface SearchResult {
  query: string;
  total_results: number;
  courses: Course[];
  faculty: Faculty[];
  publications: Publication[];
  research_areas: { id: string; name: string }[];
}
