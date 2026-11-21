import {
  Unit,
  Course,
  Faculty,
  Publication,
  Program,
  GraphStats,
  GraphData,
  StudentProfile,
  Project,
  CandidateRecommendation,
  ProjectRecommendation,
  ProjectInterest,
  SearchResult,
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
      // ignore
    }
    throw new Error(errDetail);
  }

  return res.json();
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------
export async function getHealthStatus(): Promise<{ status: string; dataset_stats: Record<string, number> }> {
  return fetchJson<{ status: string; dataset_stats: Record<string, number> }>('/health');
}

// ---------------------------------------------------------------------------
// Academic Discovery
// ---------------------------------------------------------------------------
export async function getUnits(): Promise<Unit[]> {
  const data = await fetchJson<any>(`${BASE_URL}/academic/units`);
  return Array.isArray(data) ? data : data.items || [];
}

export async function getCourses(params?: { unit?: string; search?: string; limit?: number }): Promise<Course[]> {
  const query = new URLSearchParams();
  if (params?.unit) query.set('unit', params.unit);
  if (params?.search) query.set('query', params.search);
  if (params?.limit) query.set('limit', params.limit.toString());
  const data = await fetchJson<any>(`${BASE_URL}/academic/courses?${query.toString()}`);
  return Array.isArray(data) ? data : data.items || [];
}

export async function getCourseDetail(courseId: string): Promise<Course> {
  return fetchJson<Course>(`${BASE_URL}/academic/courses/${courseId}`);
}

export async function getCoursePrerequisites(courseId: string): Promise<{
  course_code: string;
  direct_prerequisites: string[];
  resolved_prerequisites: Course[];
  unresolved_prerequisites: string[];
  prerequisite_tree: any;
}> {
  return fetchJson(`${BASE_URL}/academic/courses/${courseId}/prerequisites`);
}

export async function getFaculty(params?: { unit?: string; search?: string; rank?: string }): Promise<Faculty[]> {
  const query = new URLSearchParams();
  if (params?.unit) query.set('unit', params.unit);
  if (params?.search) query.set('query', params.search);
  if (params?.rank) query.set('rank', params.rank);
  const data = await fetchJson<any>(`${BASE_URL}/academic/faculty?${query.toString()}`);
  return Array.isArray(data) ? data : data.items || [];
}

export async function getFacultyDetail(facultyId: string): Promise<Faculty> {
  return fetchJson<Faculty>(`${BASE_URL}/academic/faculty/${facultyId}`);
}

export async function getFacultyPublications(facultyId: string): Promise<Publication[]> {
  const data = await fetchJson<any>(`${BASE_URL}/academic/faculty/${facultyId}/publications`);
  return Array.isArray(data) ? data : data.items || [];
}

export async function getPrograms(): Promise<Program[]> {
  const data = await fetchJson<any>(`${BASE_URL}/academic/programs`);
  return Array.isArray(data) ? data : data.items || [];
}

export async function getGraphStats(): Promise<GraphStats> {
  return fetchJson<GraphStats>(`${BASE_URL}/academic/graph/stats`);
}

export async function getGraphSubgraph(entityType: string, entityId: string, depth = 1): Promise<GraphData> {
  return fetchJson<GraphData>(`${BASE_URL}/academic/graph/subgraph?entity_type=${entityType}&entity_id=${entityId}&depth=${depth}`);
}

export async function searchAcademic(query: string): Promise<SearchResult> {
  return fetchJson<SearchResult>(`${BASE_URL}/academic/search?query=${encodeURIComponent(query)}`);
}

// ---------------------------------------------------------------------------
// Module B: Teammate Finder
// ---------------------------------------------------------------------------
export async function getProfiles(params?: { skill?: string; programme?: string; year?: number }): Promise<StudentProfile[]> {
  const query = new URLSearchParams();
  if (params?.skill) query.set('skill', params.skill);
  if (params?.programme) query.set('programme', params.programme);
  if (params?.year) query.set('year', params.year.toString());
  const data = await fetchJson<any>(`${BASE_URL}/teammates/profiles?${query.toString()}`);
  return Array.isArray(data) ? data : data.items || [];
}

export async function createProfile(data: any): Promise<StudentProfile> {
  return fetchJson<StudentProfile>(`${BASE_URL}/teammates/profiles`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProfile(profileId: string, data: any, ownershipKey?: string): Promise<StudentProfile> {
  const headers: Record<string, string> = {};
  if (ownershipKey) headers['X-Ownership-Key'] = ownershipKey;
  return fetchJson<StudentProfile>(`${BASE_URL}/teammates/profiles/${profileId}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(data),
  });
}

export async function getProjects(params?: { domain?: string; skill?: string; status?: string }): Promise<Project[]> {
  const query = new URLSearchParams();
  if (params?.domain) query.set('domain', params.domain);
  if (params?.skill) query.set('skill', params.skill);
  if (params?.status) query.set('status', params.status);
  const data = await fetchJson<any>(`${BASE_URL}/teammates/projects?${query.toString()}`);
  return Array.isArray(data) ? data : data.items || [];
}

export async function createProject(data: any): Promise<Project> {
  return fetchJson<Project>(`${BASE_URL}/teammates/projects`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getProjectCandidates(projectId: string): Promise<CandidateRecommendation[]> {
  return fetchJson<CandidateRecommendation[]>(`${BASE_URL}/teammates/projects/${projectId}/recommendations`);
}

export async function getStudentProjectRecommendations(profileId: string): Promise<ProjectRecommendation[]> {
  return fetchJson<ProjectRecommendation[]>(`${BASE_URL}/teammates/profiles/${profileId}/recommendations`);
}

export async function expressInterest(projectId: string, data: { profile_id: string; proposed_role?: string; message?: string }): Promise<ProjectInterest> {
  return fetchJson<ProjectInterest>(`${BASE_URL}/teammates/projects/${projectId}/interests`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getProjectInterests(projectId: string, ownerKey: string): Promise<ProjectInterest[]> {
  return fetchJson<ProjectInterest[]>(`${BASE_URL}/teammates/projects/${projectId}/interests`, {
    headers: { 'X-Ownership-Key': ownerKey },
  });
}

export async function respondToInterest(interestId: string, action: InterestStatus, ownerKey: string): Promise<ProjectInterest> {
  return fetchJson<ProjectInterest>(`${BASE_URL}/teammates/interests/${interestId}/respond`, {
    method: 'POST',
    headers: { 'X-Ownership-Key': ownerKey },
    body: JSON.stringify({ action }),
  });
}
