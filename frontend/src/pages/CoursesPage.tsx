import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import {
  BookOpen,
  Filter,
  Search,
  ChevronRight,
  GitBranch,
  FlaskConical,
  Bookmark,
  BookmarkCheck,
  Building2,
} from 'lucide-react';
import { getCourses, getUnits } from '../services/api';
import { Course, Unit } from '../types';
import SearchInput from '../components/ui/SearchInput';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import EmptyState from '../components/ui/EmptyState';
import ErrorMessage from '../components/ui/ErrorMessage';
import { useSaved } from '../context/SavedContext';

export const CoursesPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialUnit = searchParams.get('unit') || '';
  const initialSearch = searchParams.get('search') || '';

  const [courses, setCourses] = useState<Course[]>([]);
  const [total, setTotal] = useState(0);
  const [units, setUnits] = useState<Unit[]>([]);
  const [selectedUnit, setSelectedUnit] = useState(initialUnit);
  const [search, setSearch] = useState(initialSearch);
  const [isLabOnly, setIsLabOnly] = useState<boolean | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 30;

  const { isSaved, toggleSave } = useSaved();

  // Load Units once
  useEffect(() => {
    getUnits()
      .then(setUnits)
      .catch((err) => console.error('Error fetching units', err));
  }, []);

  // Fetch Courses on filter/pagination change
  const fetchCourses = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getCourses({
        unit: selectedUnit || undefined,
        search: search.trim() || undefined,
        is_lab: isLabOnly,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setCourses(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch courses');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, [selectedUnit, search, isLabOnly, page]);

  // Sync state to searchParams
  const handleUnitChange = (unitId: string) => {
    setSelectedUnit(unitId);
    setPage(0);
    const newParams = new URLSearchParams(searchParams);
    if (unitId) newParams.set('unit', unitId);
    else newParams.delete('unit');
    setSearchParams(newParams);
  };

  const handleSearchChange = (val: string) => {
    setSearch(val);
    setPage(0);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <BookOpen className="w-3.5 h-3.5 text-sky-600" />
            <span>Academic Catalog</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Courses Directory
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Showing {total} verified courses from the GIKI academic syllabus
          </p>
        </div>

        {/* Lab Filter Toggle */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setIsLabOnly((prev) => (prev === true ? undefined : true));
              setPage(0);
            }}
            className={`btn-secondary text-xs py-1.5 px-3 ${
              isLabOnly === true ? 'bg-sky-50 border-sky-300 text-sky-800' : ''
            }`}
          >
            <FlaskConical className="w-3.5 h-3.5 text-sky-600" />
            <span>Lab Courses</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="sm:col-span-2">
          <SearchInput
            value={search}
            onChange={handleSearchChange}
            placeholder="Search course code or title (e.g. CS101, Data Structures)..."
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

      {/* Course List / Grid */}
      {loading ? (
        <LoadingSpinner message="Searching catalog offerings..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={fetchCourses} />
      ) : courses.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No courses found"
          description="Try adjusting your keyword search or switching to another academic department."
          action={{
            label: 'Clear Filters',
            onClick: () => {
              setSelectedUnit('');
              setSearch('');
              setIsLabOnly(undefined);
              setSearchParams({});
            },
          }}
        />
      ) : (
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {courses.map((course) => {
              const saved = isSaved(course.code);
              const prereqCount = (course.prerequisites || []).length;
              const hasUnresolved = (course.unresolved_prerequisites || []).length > 0;

              return (
                <div
                  key={course.code}
                  className="card card-hover p-4 flex flex-col justify-between group"
                >
                  <div>
                    {/* Top Row: Code, Credits, Bookmark */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-mono font-bold text-sm text-slate-900 px-2 py-0.5 rounded bg-slate-100 border border-slate-200/80">
                          {course.code}
                        </span>
                        {course.credits_formatted ? (
                          <Badge variant="sky">{course.credits_formatted} Cr</Badge>
                        ) : course.credit_hours ? (
                          <Badge variant="sky">{course.credit_hours} Cr</Badge>
                        ) : null}
                        {course.code.endsWith('L') && <Badge variant="teal">Lab</Badge>}
                      </div>

                      <button
                        onClick={() =>
                          toggleSave({
                            id: course.code,
                            type: 'course',
                            title: `${course.code}: ${course.title}`,
                            subtitle: course.unit || 'GIKI Course',
                            link: `/courses/${course.code}`,
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

                    {/* Course Title */}
                    <Link
                      to={`/courses/${course.code}`}
                      className="text-sm font-semibold text-slate-800 group-hover:text-sky-700 transition-colors line-clamp-1 block"
                    >
                      {course.title}
                    </Link>

                    {/* Description excerpt */}
                    {course.description && (
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                        {course.description}
                      </p>
                    )}
                  </div>

                  {/* Bottom Metadata & Link */}
                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      {prereqCount > 0 ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-500">
                          <GitBranch className="w-3 h-3 text-slate-400" />
                          <span>{prereqCount} Prereq{prereqCount > 1 ? 's' : ''}</span>
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-400">No prerequisites</span>
                      )}
                      {hasUnresolved && (
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" title="Unresolved codes present" />
                      )}
                    </div>

                    <Link
                      to={`/courses/${course.code}`}
                      className="font-medium text-slate-700 group-hover:text-sky-700 flex items-center gap-0.5 text-xs"
                    >
                      <span>Details</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination Controls */}
          {total > PAGE_SIZE && (
            <div className="flex items-center justify-between pt-4 border-t border-slate-200/80 text-xs text-slate-500">
              <span>
                Page {page + 1} of {Math.ceil(total / PAGE_SIZE)} ({total} total courses)
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

export default CoursesPage;
