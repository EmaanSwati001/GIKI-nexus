import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  Search,
  BookOpen,
  Users,
  FlaskConical,
  Building2,
  GraduationCap,
  ChevronRight,
  ArrowRight,
} from 'lucide-react';
import { searchAcademic } from '../services/api';
import SearchInput from '../components/ui/SearchInput';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';
import ErrorMessage from '../components/ui/ErrorMessage';

export const SearchResultsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get('q') || '';

  const [query, setQuery] = useState(q);
  const [results, setResults] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'all' | 'course' | 'faculty' | 'research_area' | 'unit'>('all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setQuery(q);
    if (!q.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    setError(null);
    searchAcademic(q.trim(), 40)
      .then(setResults)
      .catch((err) => {
        setError(err.message || 'Search failed');
        setResults([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [q]);

  const handleSearchSubmit = () => {
    if (query.trim()) {
      setSearchParams({ q: query.trim() });
    }
  };

  const filteredResults =
    activeTab === 'all'
      ? results
      : results.filter((r) => (r.type || r.entity_type) === activeTab);

  const countsByType = {
    all: results.length,
    course: results.filter((r) => (r.type || r.entity_type) === 'course').length,
    faculty: results.filter((r) => (r.type || r.entity_type) === 'faculty').length,
    research_area: results.filter((r) => (r.type || r.entity_type) === 'research_area').length,
    unit: results.filter((r) => (r.type || r.entity_type) === 'unit').length,
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Search Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Academic Search
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Unified index across courses, professors, research areas, and departments
        </p>
      </div>

      {/* Main Search Input */}
      <div>
        <SearchInput
          value={query}
          onChange={setQuery}
          onSubmit={handleSearchSubmit}
          placeholder="Search courses, professors, research areas (e.g. CS101, Computer Vision)..."
          className="shadow-sm"
        />
      </div>

      {/* Facet Tabs */}
      {results.length > 0 && (
        <div className="flex items-center gap-1.5 border-b border-slate-200/80 pb-2 overflow-x-auto text-xs">
          {[
            { id: 'all', label: 'All Results', count: countsByType.all },
            { id: 'course', label: 'Courses', count: countsByType.course },
            { id: 'faculty', label: 'Faculty', count: countsByType.faculty },
            { id: 'research_area', label: 'Research Areas', count: countsByType.research_area },
            { id: 'unit', label: 'Departments', count: countsByType.unit },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
                activeTab === tab.id
                  ? 'bg-slate-900 text-white'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <span>{tab.label}</span>
              <span
                className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  activeTab === tab.id ? 'bg-slate-800 text-slate-200' : 'bg-slate-100 text-slate-500'
                }`}
              >
                {tab.count}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Results Content */}
      {loading ? (
        <LoadingSpinner message="Searching academic index..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={handleSearchSubmit} />
      ) : !q.trim() ? (
        <div className="card p-10 text-center text-xs text-slate-500">
          Enter an academic query above to search courses, faculty, and research domains.
        </div>
      ) : filteredResults.length === 0 ? (
        <EmptyState
          icon={Search}
          title="No results found"
          description={`We couldn't find any academic records matching "${q}".`}
        />
      ) : (
        <div className="space-y-3">
          {filteredResults.map((item, idx) => {
            const type = item.type || item.entity_type;
            let link = '/';
            let title = item.name || item.title || item.code || item.id;
            let subtitle = '';

            if (type === 'course') {
              link = `/courses/${item.code || item.id}`;
              title = `${item.code || item.id}: ${item.title || item.name}`;
              subtitle = item.description || item.unit || 'Course Offering';
            } else if (type === 'faculty') {
              link = `/faculty/${item.id}`;
              title = item.name;
              subtitle = item.designation || (item.units ? item.units.join(', ') : 'Faculty Member');
            } else if (type === 'research_area') {
              link = `/research?search=${encodeURIComponent(item.name || item.id)}`;
              title = item.name;
              subtitle = 'Research Specialization';
            } else if (type === 'unit') {
              link = `/units`;
              title = item.name;
              subtitle = item.type || 'Academic Unit';
            }

            return (
              <Link
                key={idx}
                to={link}
                className="card card-hover p-4 flex items-center justify-between gap-4 group"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge
                      variant={
                        type === 'course'
                          ? 'sky'
                          : type === 'faculty'
                          ? 'teal'
                          : type === 'research_area'
                          ? 'purple'
                          : 'default'
                      }
                      size="sm"
                    >
                      {type.replace('_', ' ')}
                    </Badge>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 group-hover:text-sky-700 transition-colors truncate">
                    {title}
                  </h3>

                  {subtitle && (
                    <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{subtitle}</p>
                  )}
                </div>

                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-700 flex-shrink-0" />
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SearchResultsPage;
