import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Briefcase,
  Plus,
  Users,
  Search,
  ChevronRight,
  Filter,
  CheckCircle,
  Clock,
  Sparkles,
} from 'lucide-react';
import { getProjects } from '../services/api';
import { Project, ProjectStatus } from '../types';
import SearchInput from '../components/ui/SearchInput';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';
import ErrorMessage from '../components/ui/ErrorMessage';

export const ProjectsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialStatus = searchParams.get('status') || 'OPEN';
  const initialDomain = searchParams.get('domain') || '';
  const initialSearch = searchParams.get('search') || '';

  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState<string>(initialStatus);
  const [domain, setDomain] = useState<string>(initialDomain);
  const [search, setSearch] = useState<string>(initialSearch);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 15;

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getProjects({
        status: status || undefined,
        domain: domain.trim() || undefined,
        search: search.trim() || undefined,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setProjects(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch project listings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [status, domain, search, page]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <Briefcase className="w-3.5 h-3.5 text-teal-600" />
            <span>Student Collaboration Hub</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Projects & Teammate Recruitment
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Active capstone design projects, research collaborations, and competition teams looking for members
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/profiles" className="btn-secondary text-xs py-1.5 px-3">
            Find Candidates
          </Link>
          <Link to="/projects/new" className="btn-primary text-xs py-1.5 px-3.5 flex items-center gap-1.5">
            <Plus className="w-3.5 h-3.5" />
            <span>Post Project</span>
          </Link>
        </div>
      </div>

      {/* Filter Row */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <div className="sm:col-span-2">
          <SearchInput
            value={search}
            onChange={(val) => {
              setSearch(val);
              setPage(0);
            }}
            placeholder="Search project title, required skills, or domain..."
          />
        </div>

        <div>
          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(0);
            }}
            className="input-field text-xs py-2 cursor-pointer"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">Recruiting (OPEN)</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMPLETED">Completed</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>

        <div>
          <input
            type="text"
            value={domain}
            onChange={(e) => {
              setDomain(e.target.value);
              setPage(0);
            }}
            placeholder="Filter by domain (e.g. AI, Web)..."
            className="input-field text-xs py-2"
          />
        </div>
      </div>

      {/* Project Listings */}
      {loading ? (
        <LoadingSpinner message="Loading recruiting projects..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchProjects} />
      ) : projects.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title="No projects found"
          description="Be the first to post a collaboration opportunity or adjust your filters."
          action={{
            label: 'Post New Project',
            onClick: () => (window.location.href = '/projects/new'),
          }}
        />
      ) : (
        <div className="space-y-3.5">
          {projects.map((proj) => {
            const openSpots = proj.additional_members_needed;
            const currentMembers = proj.members || [];

            return (
              <div
                key={proj.id}
                className="card card-hover p-5 flex flex-col md:flex-row md:items-center justify-between gap-5 group"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <Badge
                      variant={
                        proj.status === 'OPEN'
                          ? 'emerald'
                          : proj.status === 'IN_PROGRESS'
                          ? 'amber'
                          : 'default'
                      }
                      size="sm"
                    >
                      {proj.status === 'OPEN' ? 'Recruiting' : proj.status.replace('_', ' ')}
                    </Badge>

                    {openSpots > 0 && (
                      <span className="text-xs font-semibold text-sky-700 bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-100">
                        {openSpots} Spot{openSpots !== 1 ? 's' : ''} Open
                      </span>
                    )}

                    {proj.domains &&
                      proj.domains.map((d) => (
                        <Badge key={d} variant="teal" size="sm">
                          {d}
                        </Badge>
                      ))}
                  </div>

                  <Link
                    to={`/projects/${proj.id}`}
                    className="text-base font-bold text-slate-900 group-hover:text-sky-700 transition-colors block truncate"
                  >
                    {proj.title}
                  </Link>

                  <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                    {proj.description}
                  </p>

                  {/* Required Skills & Roles */}
                  <div className="mt-3 flex flex-wrap items-center gap-1.5">
                    {proj.required_skills && proj.required_skills.length > 0 && (
                      <span className="text-[11px] font-semibold text-slate-400 mr-1">Skills:</span>
                    )}
                    {proj.required_skills &&
                      proj.required_skills.map((skill) => (
                        <span
                          key={skill}
                          className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700"
                        >
                          {skill}
                        </span>
                      ))}

                    {proj.preferred_roles && proj.preferred_roles.length > 0 && (
                      <>
                        <span className="text-[11px] font-semibold text-slate-400 ml-2 mr-1">
                          Roles:
                        </span>
                        {proj.preferred_roles.map((r) => (
                          <span
                            key={r}
                            className="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200/60"
                          >
                            {r}
                          </span>
                        ))}
                      </>
                    )}
                  </div>
                </div>

                {/* Right Side: Members & CTA */}
                <div className="flex md:flex-col items-center md:items-end justify-between gap-3 border-t md:border-t-0 pt-3 md:pt-0 border-slate-100 flex-shrink-0">
                  <div className="text-xs text-slate-500 flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                    <span>
                      {currentMembers.length} active member{currentMembers.length !== 1 ? 's' : ''}
                    </span>
                  </div>

                  <Link
                    to={`/projects/${proj.id}`}
                    className="btn-primary text-xs py-1.5 px-3.5 flex items-center gap-1"
                  >
                    <span>View Project</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}

          {/* Pagination */}
          {total > PAGE_SIZE && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-200/80 text-xs text-slate-500">
              <span>
                Page {page + 1} of {Math.ceil(total / PAGE_SIZE)} ({total} projects)
              </span>
              <div className="flex items-center gap-2">
                <button
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  className="btn-secondary text-xs py-1 px-3 disabled:opacity-40"
                >
                  Previous
                </button>
                <button
                  disabled={(page + 1) * PAGE_SIZE >= total}
                  onClick={() => setPage((p) => p + 1)}
                  className="btn-secondary text-xs py-1 px-3 disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProjectsPage;
