import {
  Unit,
  Course,
  Faculty,
  Publication,
  Program,
  ResearchArea,
  GraphStats,
  GraphData,
  StudentProfile,
  Project,
  CandidateRecommendation,
  ProjectRecommendation,
  ProjectInterest,
  InterestStatus,
} from '../types';

const BASE_URL = '/api/v1';

async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!res.ok) {
    let errDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const data = await res.json();
      if (data.detail) errDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
    } catch {
      // ignore JSON parse error
    }
    throw new Error(errDetail);
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------
export interface HealthStatus {
  status: string;
  app_name: string;
  version: string;
  datasets_loaded: boolean;
  graph_initialized: boolean;
  database_initialized: boolean;
  entity_counts: {
    units: number;
    faculty: number;
    courses: number;
    publications: number;
    research_areas: number;
    programs: number;
  };
  graph: {
    node_count?: number;
    edge_count?: number;
    node_types?: Record<string, number>;
    edge_types?: Record<string, number>;
  };
}

export async function getHealthStatus(): Promise<HealthStatus> {
  return fetchJson<HealthStatus>('/health');
}

// ---------------------------------------------------------------------------
// Academic Units
// ---------------------------------------------------------------------------
export async function getUnits(): Promise<Unit[]> {
  const data = await fetchJson<any>(`${BASE_URL}/units`);
  return Array.isArray(data) ? data : data.items || [];
}

export async function getUnitDetail(unitId: string): Promise<Unit & { faculty?: Faculty[]; programs?: Program[] }> {
  return fetchJson(`${BASE_URL}/units/${unitId}`);
}

// ---------------------------------------------------------------------------
// Courses
// ---------------------------------------------------------------------------
export async function getCourses(params?: {
  unit?: string;
  program_id?: string;
  is_lab?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}): Promise<{ items: Course[]; total: number; skip: number; limit: number }> {
  const query = new URLSearchParams();
  if (params?.unit) query.set('unit', params.unit);
  if (params?.program_id) query.set('program_id', params.program_id);
  if (params?.is_lab !== undefined) query.set('is_lab', params.is_lab.toString());
  if (params?.search) query.set('search', params.search);
  if (params?.skip !== undefined) query.set('skip', params.skip.toString());
  if (params?.limit !== undefined) query.set('limit', params.limit.toString());
  return fetchJson(`${BASE_URL}/courses?${query.toString()}`);
}

export async function getCourseDetail(courseCode: string): Promise<Course> {
  return fetchJson<Course>(`${BASE_URL}/courses/${courseCode}`);
}

export interface PrerequisiteResponse {
  course_code: string;
  direct_prerequisites: string[];
  resolved_prerequisites: Course[];
  unresolved_prerequisites: string[];
  prerequisite_tree: any;
}

export async function getCoursePrerequisites(courseCode: string): Promise<PrerequisiteResponse> {
  return fetchJson<PrerequisiteResponse>(`${BASE_URL}/courses/${courseCode}/prerequisites`);
}

export async function getCourseRelated(courseCode: string): Promise<{
  course_code: string;
  unit: Unit | null;
  programs: Program[];
  prerequisites: string[];
  dependent_courses: string[];
}> {
  return fetchJson(`${BASE_URL}/courses/${courseCode}/related`);
}

// ---------------------------------------------------------------------------
// Faculty Members
// ---------------------------------------------------------------------------
export async function getFaculty(params?: {
  unit?: string;
  research_area?: string;
  verified_only?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}): Promise<{ items: Faculty[]; total: number; skip: number; limit: number }> {
  const query = new URLSearchParams();
  if (params?.unit) query.set('unit', params.unit);
  if (params?.research_area) query.set('research_area', params.research_area);
  if (params?.verified_only) query.set('verified_only', 'true');
  if (params?.search) query.set('search', params.search);
  if (params?.skip !== undefined) query.set('skip', params.skip.toString());
  if (params?.limit !== undefined) query.set('limit', params.limit.toString());
  return fetchJson(`${BASE_URL}/faculty?${query.toString()}`);
}

export async function getFacultyDetail(facultyId: string): Promise<Faculty> {
  return fetchJson<Faculty>(`${BASE_URL}/faculty/${facultyId}`);
}

export async function getFacultyResearchAreas(facultyId: string): Promise<ResearchArea[]> {
  return fetchJson<ResearchArea[]>(`${BASE_URL}/faculty/${facultyId}/research-areas`);
}

export async function getFacultyPublications(facultyId: string): Promise<Publication[]> {
  const data = await fetchJson<any>(`${BASE_URL}/faculty/${facultyId}/publications`);
  return Array.isArray(data) ? data : data.items || [];
}

// ---------------------------------------------------------------------------
// Research Areas
// ---------------------------------------------------------------------------
export async function getResearchAreas(params?: {
  unit?: string;
  search?: string;
  skip?: number;
  limit?: number;
}): Promise<{ items: ResearchArea[]; total: number; skip: number; limit: number }> {
  const query = new URLSearchParams();
  if (params?.unit) query.set('unit', params.unit);
  if (params?.search) query.set('search', params.search);
  if (params?.skip !== undefined) query.set('skip', params.skip.toString());
  if (params?.limit !== undefined) query.set('limit', params.limit.toString());
  return fetchJson(`${BASE_URL}/research-areas?${query.toString()}`);
}

export async function getResearchAreaDetail(areaId: string): Promise<ResearchArea> {
  return fetchJson<ResearchArea>(`${BASE_URL}/research-areas/${areaId}`);
}

export async function getResearchAreaFaculty(areaId: string): Promise<Faculty[]> {
  return fetchJson<Faculty[]>(`${BASE_URL}/research-areas/${areaId}/faculty`);
}

// ---------------------------------------------------------------------------
// Degree Programs
// ---------------------------------------------------------------------------
export async function getPrograms(unit?: string): Promise<Program[]> {
  const query = unit ? `?unit=${encodeURIComponent(unit)}` : '';
  const data = await fetchJson<any>(`${BASE_URL}/programs${query}`);
  return Array.isArray(data) ? data : data.items || [];
}

export async function getProgramDetail(programId: string): Promise<Program> {
  return fetchJson<Program>(`${BASE_URL}/programs/${programId}`);
}

export async function getProgramCurriculum(programId: string): Promise<any> {
  return fetchJson(`${BASE_URL}/programs/${programId}/curriculum`);
}

// ---------------------------------------------------------------------------
// Publications
// ---------------------------------------------------------------------------
export async function getPublications(params?: {
  faculty_id?: string;
  pub_type?: string;
  year?: number;
  search?: string;
  skip?: number;
  limit?: number;
}): Promise<{ items: Publication[]; total: number; skip: number; limit: number }> {
  const query = new URLSearchParams();
  if (params?.faculty_id) query.set('faculty_id', params.faculty_id);
  if (params?.pub_type) query.set('pub_type', params.pub_type);
  if (params?.year) query.set('year', params.year.toString());
  if (params?.search) query.set('search', params.search);
  if (params?.skip !== undefined) query.set('skip', params.skip.toString());
  if (params?.limit !== undefined) query.set('limit', params.limit.toString());
  return fetchJson(`${BASE_URL}/publications?${query.toString()}`);
}

// ---------------------------------------------------------------------------
// Unified Search & Knowledge Graph
// ---------------------------------------------------------------------------
export async function searchAcademic(query: string, limit = 20): Promise<any[]> {
  return fetchJson<any[]>(`${BASE_URL}/search?q=${encodeURIComponent(query)}&limit=${limit}`);
}

export async function getGraphStats(): Promise<GraphStats> {
  return fetchJson<GraphStats>(`${BASE_URL}/graph/stats`);
}

export async function getEntitySubgraph(entityType: string, entityId: string, depth = 1): Promise<GraphData> {
  return fetchJson<GraphData>(`${BASE_URL}/graph/entity/${entityType}/${entityId}?depth=${depth}`);
}

// ---------------------------------------------------------------------------
// Module B: Teammate Finder
// ---------------------------------------------------------------------------
export async function getProfiles(params?: {
  programme?: string;
  academic_year?: number;
  skill?: string;
  domain?: string;
  role?: string;
  search?: string;
  skip?: number;
  limit?: number;
}): Promise<{ items: StudentProfile[]; total: number; skip: number; limit: number }> {
  const query = new URLSearchParams();
  if (params?.programme) query.set('programme', params.programme);
  if (params?.academic_year) query.set('academic_year', params.academic_year.toString());
  if (params?.skill) query.set('skill', params.skill);
  if (params?.domain) query.set('domain', params.domain);
  if (params?.role) query.set('role', params.role);
  if (params?.search) query.set('search', params.search);
  if (params?.skip !== undefined) query.set('skip', params.skip.toString());
  if (params?.limit !== undefined) query.set('limit', params.limit.toString());
  return fetchJson(`${BASE_URL}/teammates/profiles?${query.toString()}`);
}

export async function getProfile(profileId: string): Promise<StudentProfile> {
  return fetchJson<StudentProfile>(`${BASE_URL}/teammates/profiles/${profileId}`);
}

export async function createProfile(data: any): Promise<StudentProfile & { ownership_key: string }> {
  return fetchJson<StudentProfile & { ownership_key: string }>(`${BASE_URL}/teammates/profiles`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProfile(profileId: string, data: any, ownershipKey: string): Promise<StudentProfile> {
  return fetchJson<StudentProfile>(`${BASE_URL}/teammates/profiles/${profileId}`, {
    method: 'PUT',
    headers: { 'X-Ownership-Key': ownershipKey },
    body: JSON.stringify(data),
  });
}

export async function updateProfileVisibility(profileId: string, visibility: string, ownershipKey: string): Promise<StudentProfile> {
  return fetchJson<StudentProfile>(`${BASE_URL}/teammates/profiles/${profileId}/visibility`, {
    method: 'PATCH',
    headers: { 'X-Ownership-Key': ownershipKey },
    body: JSON.stringify({ visibility }),
  });
}

export async function deactivateProfile(profileId: string, ownershipKey: string): Promise<{ status: string; profile_id: string }> {
  return fetchJson(`${BASE_URL}/teammates/profiles/${profileId}/deactivate`, {
    method: 'POST',
    headers: { 'X-Ownership-Key': ownershipKey },
  });
}

// Projects
export async function getProjects(params?: {
  domain?: string;
  skill?: string;
  role?: string;
  status?: string;
  search?: string;
  skip?: number;
  limit?: number;
}): Promise<{ items: Project[]; total: number; skip: number; limit: number }> {
  const query = new URLSearchParams();
  if (params?.domain) query.set('domain', params.domain);
  if (params?.skill) query.set('skill', params.skill);
  if (params?.role) query.set('role', params.role);
  if (params?.status) query.set('status', params.status);
  if (params?.search) query.set('search', params.search);
  if (params?.skip !== undefined) query.set('skip', params.skip.toString());
  if (params?.limit !== undefined) query.set('limit', params.limit.toString());
  return fetchJson(`${BASE_URL}/teammates/projects?${query.toString()}`);
}

export async function getProject(projectId: string): Promise<Project> {
  return fetchJson<Project>(`${BASE_URL}/teammates/projects/${projectId}`);
}

export async function createProject(data: any): Promise<Project & { ownership_key: string }> {
  return fetchJson<Project & { ownership_key: string }>(`${BASE_URL}/teammates/projects`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProject(projectId: string, data: any, ownershipKey: string): Promise<Project> {
  return fetchJson<Project>(`${BASE_URL}/teammates/projects/${projectId}`, {
    method: 'PUT',
    headers: { 'X-Ownership-Key': ownershipKey },
    body: JSON.stringify(data),
  });
}

export async function closeProject(projectId: string, ownershipKey: string): Promise<Project> {
  return fetchJson<Project>(`${BASE_URL}/teammates/projects/${projectId}/close`, {
    method: 'POST',
    headers: { 'X-Ownership-Key': ownershipKey },
  });
}

export async function getProjectRecommendations(projectId: string, limit = 20): Promise<CandidateRecommendation[]> {
  return fetchJson<CandidateRecommendation[]>(`${BASE_URL}/teammates/projects/${projectId}/recommendations?limit=${limit}`);
}

export async function getStudentProjectRecommendations(profileId: string, limit = 20): Promise<ProjectRecommendation[]> {
  return fetchJson<ProjectRecommendation[]>(`${BASE_URL}/teammates/profiles/${profileId}/recommendations?limit=${limit}`);
}

export async function expressInterest(
  projectId: string,
  data: { profile_id: string; proposed_role?: string; message?: string }
): Promise<ProjectInterest> {
  return fetchJson<ProjectInterest>(`${BASE_URL}/teammates/projects/${projectId}/interest`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getProjectInterests(projectId: string, ownerKey: string): Promise<ProjectInterest[]> {
  return fetchJson<ProjectInterest[]>(`${BASE_URL}/teammates/projects/${projectId}/interests`, {
    headers: { 'X-Ownership-Key': ownerKey },
  });
}

export async function respondToInterest(
  interestId: string,
  action: InterestStatus,
  ownerKey: string
): Promise<ProjectInterest> {
  return fetchJson<ProjectInterest>(`${BASE_URL}/teammates/interests/${interestId}/respond`, {
    method: 'POST',
    headers: { 'X-Ownership-Key': ownerKey },
    body: JSON.stringify({ action }),
  });
}
