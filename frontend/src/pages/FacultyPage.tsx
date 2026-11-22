import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Users,
  Search,
  CheckCircle2,
  BookOpen,
  FlaskConical,
  ChevronRight,
  Bookmark,
  BookmarkCheck,
  Building2,
  Mail,
} from 'lucide-react';
import { getFaculty, getUnits } from '../services/api';
import { Faculty, Unit } from '../types';
import SearchInput from '../components/ui/SearchInput';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';
import ErrorMessage from '../components/ui/ErrorMessage';
import { useSaved } from '../context/SavedContext';

export const FacultyPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialUnit = searchParams.get('unit') || '';
  const initialSearch = searchParams.get('search') || '';

  const [faculty, setFaculty] = useState<Faculty[]>([]);
  const [total, setTotal] = useState(0);
  const [units, setUnits] = useState<Unit[]>([]);
  const [selectedUnit, setSelectedUnit] = useState(initialUnit);
  const [search, setSearch] = useState(initialSearch);
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 24;

  const { isSaved, toggleSave } = useSaved();

  useEffect(() => {
    getUnits()
      .then(setUnits)
      .catch((err) => console.error('Failed to load units', err));
  }, []);

  const fetchFaculty = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getFaculty({
        unit: selectedUnit || undefined,
        search: search.trim() || undefined,
        verified_only: verifiedOnly,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setFaculty(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch faculty directory');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFaculty();
  }, [selectedUnit, search, verifiedOnly, page]);

  const handleUnitChange = (unitId: string) => {
    setSelectedUnit(unitId);
    setPage(0);
    const newParams = new URLSearchParams(searchParams);
    if (unitId) newParams.set('unit', unitId);
    else newParams.delete('unit');
    setSearchParams(newParams);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <Users className="w-3.5 h-3.5 text-teal-600" />
            <span>Academic Staff</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Faculty Directory
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Showing {total} academic scholars and instructors at GIKI
          </p>
        </div>

        {/* Verified Filter Button */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setVerifiedOnly((prev) => !prev);
              setPage(0);
            }}
            className={`btn-secondary text-xs py-1.5 px-3 ${
              verifiedOnly ? 'bg-emerald-50 border-emerald-300 text-emerald-800' : ''
            }`}
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Verified Profiles Only</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="sm:col-span-2">
          <SearchInput
            value={search}
            onChange={(val) => {
              setSearch(val);
              setPage(0);
            }}
            placeholder="Search faculty name, designation, or research interests..."
          />
        </div>

        <div>
          <select
            value={selectedUnit}
            onChange={(e) => handleUnitChange(e.target.value)}
            className="input-field text-sm cursor-pointer"
          >
            <option value="">All Academic Units</option>
            {units.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name} ({u.code || u.id})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Faculty List */}
      {loading ? (
        <LoadingSpinner message="Searching faculty profiles..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchFaculty} />
      ) : faculty.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No faculty members found"
          description="Try broadening your search keyword or selecting a different academic unit."
          action={{
            label: 'Reset Filters',
            onClick: () => {
              setSelectedUnit('');
              setSearch('');
              setVerifiedOnly(false);
              setSearchParams({});
            },
          }}
        />
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {faculty.map((member) => {
              const saved = isSaved(member.id);
              const interests = member.research_interests || [];

              return (
                <div
                  key={member.id}
                  className="card card-hover p-5 flex flex-col justify-between group"
                >
                  <div>
                    {/* Top row: Unit badge + verified check + save */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {member.units && member.units.length > 0 && (
                          <Badge variant="default" size="sm">
                            {member.units.join(', ')}
                          </Badge>
                        )}
                        {member.verified && (
                          <Badge variant="emerald" size="sm">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            <span>Verified</span>
                          </Badge>
                        )}
                      </div>

                      <button
                        onClick={() =>
                          toggleSave({
                            id: member.id,
                            type: 'faculty',
                            title: member.name,
                            subtitle: member.designation || member.academic_rank || 'GIKI Faculty',
                            link: `/faculty/${member.id}`,
                          })
                        }
                        className="p-1 text-slate-400 hover:text-slate-700 transition-colors"
                        title={saved ? 'Remove from My Space' : 'Save to My Space'}
                      >
                        {saved ? (
                          <BookmarkCheck className="w-4 h-4 text-sky-600 fill-sky-100" />
                        ) : (
                          <Bookmark className="w-4 h-4" />
                        )}
                      </button>
                    </div>

                    {/* Faculty Name */}
                    <Link
                      to={`/faculty/${member.id}`}
                      className="text-base font-bold text-slate-900 group-hover:text-sky-700 transition-colors block"
                    >
                      {member.name}
                    </Link>

                    {/* Designation / Academic Rank */}
                    <p className="text-xs font-medium text-slate-500 mt-0.5">
                      {member.designation || member.academic_rank || 'Faculty Member'}
                    </p>

                    {/* Research Interests Tags */}
                    {interests.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-1">
                        {interests.slice(0, 3).map((item) => (
                          <span
                            key={item}
                            className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-50 text-slate-600 border border-slate-100"
                          >
                            {item}
                          </span>
                        ))}
                        {interests.length > 3 && (
                          <span className="text-[10px] text-slate-400 self-center">
                            +{interests.length - 3} more
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Bottom Row */}
                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-[11px] text-slate-400">
                      {member.publications_count !== undefined
                        ? `${member.publications_count} publication${
                            member.publications_count !== 1 ? 's' : ''
                          }`
                        : 'Academic Profile'}
                    </span>

                    <Link
                      to={`/faculty/${member.id}`}
                      className="font-medium text-slate-700 group-hover:text-sky-700 flex items-center gap-0.5"
                    >
                      <span>View Profile</span>
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
                Page {page + 1} of {Math.ceil(total / PAGE_SIZE)} ({total} faculty members)
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

export default FacultyPage;
