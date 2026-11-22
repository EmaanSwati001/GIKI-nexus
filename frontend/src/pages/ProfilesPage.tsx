import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  UserCheck,
  Plus,
  Search,
  ChevronRight,
  ShieldCheck,
  Clock,
  Sparkles,
  BookOpen,
} from 'lucide-react';
import { getProfiles } from '../services/api';
import { StudentProfile } from '../types';
import SearchInput from '../components/ui/SearchInput';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';
import ErrorMessage from '../components/ui/ErrorMessage';

export const ProfilesPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialProg = searchParams.get('programme') || '';
  const initialYear = searchParams.get('year') ? parseInt(searchParams.get('year')!) : undefined;
  const initialSkill = searchParams.get('skill') || '';

  const [profiles, setProfiles] = useState<StudentProfile[]>([]);
  const [total, setTotal] = useState(0);
  const [programme, setProgramme] = useState(initialProg);
  const [year, setYear] = useState<number | undefined>(initialYear);
  const [skill, setSkill] = useState(initialSkill);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 18;

  const fetchProfiles = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getProfiles({
        programme: programme || undefined,
        academic_year: year,
        skill: skill.trim() || undefined,
        search: search.trim() || undefined,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setProfiles(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err.message || 'Failed to load student profiles');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfiles();
  }, [programme, year, skill, search, page]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <UserCheck className="w-3.5 h-3.5 text-teal-600" />
            <span>Peer Talent Directory</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Student Teammate Discovery
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Discover peer collaborators based on technical skills, academic year, and domain interests
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link to="/projects" className="btn-secondary text-xs py-1.5 px-3">
            Browse Projects
          </Link>
          <Link to="/profiles/new" className="btn-primary text-xs py-1.5 px-3.5 flex items-center gap-1.5">
            <Plus className="w-3.5 h-3.5" />
            <span>Create Profile</span>
          </Link>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <div className="sm:col-span-2">
          <SearchInput
            value={search}
            onChange={(val) => {
              setSearch(val);
              setPage(0);
            }}
            placeholder="Search student bio, skills, or display name..."
          />
        </div>

        <div>
          <input
            type="text"
            value={skill}
            onChange={(e) => {
              setSkill(e.target.value);
              setPage(0);
            }}
            placeholder="Filter by skill (e.g. Python, React)..."
            className="input-field text-xs py-2"
          />
        </div>

        <div>
          <select
            value={year !== undefined ? year.toString() : ''}
            onChange={(e) => {
              setYear(e.target.value ? parseInt(e.target.value) : undefined);
              setPage(0);
            }}
            className="input-field text-xs py-2 cursor-pointer"
          >
            <option value="">All Academic Years</option>
            <option value="1">Year 1 (Freshman)</option>
            <option value="2">Year 2 (Sophomore)</option>
            <option value="3">Year 3 (Junior)</option>
            <option value="4">Year 4 (Senior / Capstone)</option>
          </select>
        </div>
      </div>

      {/* Profiles Grid */}
      {loading ? (
        <LoadingSpinner message="Searching student talent..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchProfiles} />
      ) : profiles.length === 0 ? (
        <EmptyState
          icon={UserCheck}
          title="No student profiles found"
          description="Be the first to list your collaboration profile or adjust your search filters."
          action={{
            label: 'Create Student Profile',
            onClick: () => (window.location.href = '/profiles/new'),
          }}
        />
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {profiles.map((prof) => {
              const skills = prof.technical_skills || [];
              const interests = prof.research_interests || [];

              return (
                <div
                  key={prof.id}
                  className="card card-hover p-5 flex flex-col justify-between group"
                >
                  <div>
                    {/* Top Row: Year + anonymous check */}
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <Badge variant="default" size="sm">
                          {prof.programme} • Yr {prof.academic_year}
                        </Badge>
                        {prof.is_anonymous && (
                          <Badge variant="amber" size="sm">
                            Anonymous
                          </Badge>
                        )}
                      </div>

                      <span className="text-[11px] text-slate-400 font-medium">
                        {prof.availability || 'Flexible'}
                      </span>
                    </div>

                    {/* Display Name */}
                    <Link
                      to={`/profiles/${prof.id}`}
                      className="text-base font-bold text-slate-900 group-hover:text-teal-700 transition-colors block"
                    >
                      {prof.is_anonymous ? 'Anonymous Student' : prof.display_name}
                    </Link>

                    {/* Bio snippet (only if not anonymous) */}
                    {!prof.is_anonymous && prof.bio && (
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                        {prof.bio}
                      </p>
                    )}

                    {/* Skills Tags */}
                    {skills.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1">
                        {skills.slice(0, 4).map((s) => (
                          <span
                            key={s}
                            className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700"
                          >
                            {s}
                          </span>
                        ))}
                        {skills.length > 4 && (
                          <span className="text-[10px] text-slate-400 self-center">
                            +{skills.length - 4}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Bottom Row */}
                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-[11px] text-slate-400">
                      {prof.preferred_roles && prof.preferred_roles.length > 0
                        ? prof.preferred_roles[0]
                        : 'Open Collaborator'}
                    </span>

                    <Link
                      to={`/profiles/${prof.id}`}
                      className="font-medium text-slate-700 group-hover:text-teal-700 flex items-center gap-0.5 text-xs"
                    >
                      <span>Profile</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination */}
          {total > PAGE_SIZE && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-200/80 text-xs text-slate-500">
              <span>
                Page {page + 1} of {Math.ceil(total / PAGE_SIZE)} ({total} student profiles)
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

export default ProfilesPage;
