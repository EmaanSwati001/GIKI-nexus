import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { FlaskConical, Search, Users, ChevronRight, Share2 } from 'lucide-react';
import { getResearchAreas } from '../services/api';
import { ResearchArea } from '../types';
import SearchInput from '../components/ui/SearchInput';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';
import ErrorMessage from '../components/ui/ErrorMessage';

export const ResearchAreasPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialSearch = searchParams.get('search') || '';

  const [researchAreas, setResearchAreas] = useState<ResearchArea[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState(initialSearch);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 30;

  const fetchAreas = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getResearchAreas({
        search: search.trim() || undefined,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setResearchAreas(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch research areas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAreas();
  }, [search, page]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <FlaskConical className="w-3.5 h-3.5 text-purple-600" />
            <span>Research Domains</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Research Areas & Specializations
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Showing {total} academic disciplines and research directions pursued at GIKI
          </p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="max-w-md">
        <SearchInput
          value={search}
          onChange={(val) => {
            setSearch(val);
            setPage(0);
          }}
          placeholder="Search research topics (e.g. Machine Learning, Robotics)..."
        />
      </div>

      {/* Grid */}
      {loading ? (
        <LoadingSpinner message="Loading research domains..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchAreas} />
      ) : researchAreas.length === 0 ? (
        <EmptyState
          icon={FlaskConical}
          title="No research areas found"
          description="Try searching with a broader keyword (e.g. 'Network', 'Energy', 'Vision')."
          action={{
            label: 'Clear Search',
            onClick: () => {
              setSearch('');
              setSearchParams({});
            },
          }}
        />
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {researchAreas.map((area) => (
              <div
                key={area.id}
                className="card card-hover p-4 flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="font-mono text-xs font-bold text-slate-400 uppercase">
                      {area.slug || area.id.replace('ra_', '')}
                    </span>
                    <Link
                      to={`/graph?entity=research_area&id=${area.id}`}
                      className="p-1 text-slate-400 hover:text-sky-600 transition-colors"
                      title="View in Knowledge Graph"
                    >
                      <Share2 className="w-3.5 h-3.5" />
                    </Link>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 group-hover:text-purple-700 transition-colors">
                    {area.name}
                  </h3>

                  {area.unit_names && area.unit_names.length > 0 && (
                    <p className="text-[11px] text-slate-500 mt-1">
                      {area.unit_names.join(', ')}
                    </p>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-400">
                    {area.faculty_count !== undefined
                      ? `${area.faculty_count} faculty member${area.faculty_count !== 1 ? 's' : ''}`
                      : 'Research Domain'}
                  </span>

                  <Link
                    to={`/faculty?search=${encodeURIComponent(area.name)}`}
                    className="font-medium text-slate-700 group-hover:text-purple-700 flex items-center gap-0.5 text-xs"
                  >
                    <span>View Faculty</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {total > PAGE_SIZE && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-200/80 text-xs text-slate-500">
              <span>
                Page {page + 1} of {Math.ceil(total / PAGE_SIZE)} ({total} research areas)
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

export default ResearchAreasPage;
