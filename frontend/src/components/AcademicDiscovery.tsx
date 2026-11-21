import React, { useState, useEffect } from 'react';
import {
  Search,
  BookOpen,
  Filter,
  Layers,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  GitBranch,
  X,
  ExternalLink,
} from 'lucide-react';
import { Course, Unit, Program } from '../types';
import { getCourses, getUnits, getPrograms, getCoursePrerequisites } from '../services/api';

export const AcademicDiscovery: React.FC = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [selectedUnit, setSelectedUnit] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [activeCourseModal, setActiveCourseModal] = useState<Course | null>(null);
  const [prereqData, setPrereqData] = useState<any | null>(null);
  const [loadingPrereqs, setLoadingPrereqs] = useState<boolean>(false);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [cList, uList, pList] = await Promise.all([
          getCourses({ limit: 100 }),
          getUnits(),
          getPrograms(),
        ]);
        setCourses(cList);
        setUnits(uList);
        setPrograms(pList);
      } catch (err) {
        console.error('Failed to load academic data', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const filtered = await getCourses({
        unit: selectedUnit === 'all' ? undefined : selectedUnit,
        search: searchQuery.trim() || undefined,
        limit: 100,
      });
      setCourses(filtered);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUnitChange = async (unitId: string) => {
    setSelectedUnit(unitId);
    setLoading(true);
    try {
      const filtered = await getCourses({
        unit: unitId === 'all' ? undefined : unitId,
        search: searchQuery.trim() || undefined,
        limit: 100,
      });
      setCourses(filtered);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const openCourseDetail = async (course: Course) => {
    setActiveCourseModal(course);
    setLoadingPrereqs(true);
    try {
      const pData = await getCoursePrerequisites(course.id);
      setPrereqData(pData);
    } catch {
      setPrereqData(null);
    } finally {
      setLoadingPrereqs(false);
    }
  };

  const unitMap = new Map(units.map((u) => [u.id.toLowerCase(), u.name]));

  return (
    <div className="space-y-6">
      {/* Hero & Search Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-sky-950 to-indigo-950 p-6 md:p-8 border border-sky-800/30 shadow-xl">
        <div className="max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-300 text-xs font-semibold mb-3">
            <BookOpen className="w-3.5 h-3.5" />
            <span>Academic Knowledge Base • 647 Verified Courses</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
            Explore GIKI Curriculum & Course Catalogs
          </h1>
          <p className="mt-2 text-sm md:text-base text-slate-300">
            Browse verified courses, prerequisite dependency chains, credit hour allocations, and academic department offerings across all undergraduate programs.
          </p>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="mt-5 flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search by course code (e.g. CS102, EE211) or title..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-700/80 rounded-xl text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 transition-all"
              />
            </div>
            <button
              type="submit"
              className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white font-medium text-sm rounded-xl transition-colors shadow-md shadow-sky-600/20 flex items-center space-x-1.5"
            >
              <span>Search</span>
            </button>
          </form>
        </div>
      </div>

      {/* Faculty/Unit Filter Pills */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1">
        <button
          onClick={() => handleUnitChange('all')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
            selectedUnit === 'all'
              ? 'bg-sky-600 text-white shadow-sm'
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
          }`}
        >
          All Faculties ({courses.length})
        </button>
        {units.map((unit) => (
          <button
            key={unit.id}
            onClick={() => handleUnitChange(unit.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
              selectedUnit.toLowerCase() === unit.id.toLowerCase()
                ? 'bg-sky-600 text-white shadow-sm'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
            }`}
          >
            {unit.code || unit.id.toUpperCase()} • {unit.name}
          </button>
        ))}
      </div>

      {/* Courses Grid */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center space-y-3">
          <div className="w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Loading verified courses from academic repository...</p>
        </div>
      ) : courses.length === 0 ? (
        <div className="py-16 text-center rounded-xl border border-slate-800 bg-slate-900/50">
          <AlertCircle className="w-10 h-10 text-slate-500 mx-auto mb-2" />
          <h3 className="text-base font-semibold text-slate-300">No courses match your query</h3>
          <p className="text-xs text-slate-500 mt-1">Try clearing filters or searching by a different course code.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {courses.map((course) => {
            const hasPrereqs = (course.prerequisites?.length || 0) > 0;
            const hasUnresolved = (course.unresolved_prerequisites?.length || 0) > 0;
            const unitName = unitMap.get(course.unit?.toLowerCase() || '') || course.unit?.toUpperCase() || 'GIKI';

            return (
              <div
                key={course.id}
                onClick={() => openCourseDetail(course)}
                className="group relative bg-[#111927] hover:bg-[#162032] border border-slate-800/80 hover:border-sky-500/50 rounded-xl p-5 transition-all duration-200 cursor-pointer flex flex-col justify-between shadow-sm hover:shadow-lg hover:shadow-sky-950/20"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <span className="inline-block px-2.5 py-1 rounded-md bg-sky-950/80 border border-sky-800/60 text-sky-400 font-mono text-xs font-bold">
                      {course.code}
                    </span>
                    <span className="text-xs font-medium text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded">
                      {course.credits_formatted || (course.credit_hours ? `${course.credit_hours} Cr` : 'Credit N/A')}
                    </span>
                  </div>

                  <h3 className="mt-3 text-base font-semibold text-white group-hover:text-sky-300 transition-colors line-clamp-2">
                    {course.title}
                  </h3>

                  <p className="mt-1 text-xs text-slate-400 font-medium">
                    {unitName}
                  </p>

                  {course.description && (
                    <p className="mt-2.5 text-xs text-slate-400 line-clamp-2 leading-relaxed">
                      {course.description}
                    </p>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs">
                  {hasPrereqs ? (
                    <div className="flex items-center space-x-1.5 text-amber-400">
                      <GitBranch className="w-3.5 h-3.5" />
                      <span>{course.prerequisites.length} Prerequisite{course.prerequisites.length > 1 ? 's' : ''}</span>
                    </div>
                  ) : (
                    <span className="text-slate-500 font-mono">No prerequisites</span>
                  )}

                  {hasUnresolved && (
                    <span className="text-[10px] text-amber-300 bg-amber-950/60 border border-amber-800/40 px-1.5 py-0.5 rounded">
                      Prospectus Code
                    </span>
                  )}

                  <span className="text-sky-400 group-hover:translate-x-0.5 transition-transform font-medium flex items-center space-x-1">
                    <span>Inspect</span>
                    <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Course Detail & Prerequisite Tree Modal */}
      {activeCourseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="relative w-full max-w-2xl bg-[#0f172a] border border-slate-700/80 rounded-2xl p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setActiveCourseModal(null)}
              className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center space-x-3">
              <span className="px-3 py-1 rounded-lg bg-sky-950 border border-sky-800 text-sky-400 font-mono font-bold text-sm">
                {activeCourseModal.code}
              </span>
              <span className="text-xs px-2.5 py-1 bg-slate-800 text-slate-300 rounded font-medium">
                {activeCourseModal.credits_formatted || (activeCourseModal.credit_hours ? `${activeCourseModal.credit_hours} Credit Hours` : '')}
              </span>
            </div>

            <h2 className="mt-3 text-xl font-bold text-white">
              {activeCourseModal.title}
            </h2>

            <p className="mt-1 text-xs text-sky-400 font-medium">
              Academic Unit: {unitMap.get(activeCourseModal.unit?.toLowerCase() || '') || activeCourseModal.unit}
            </p>

            {activeCourseModal.description && (
              <div className="mt-4 p-3.5 bg-slate-900/80 rounded-xl border border-slate-800">
                <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Course Description</h4>
                <p className="text-xs text-slate-300 leading-relaxed">{activeCourseModal.description}</p>
              </div>
            )}

            {/* Prerequisites Section */}
            <div className="mt-5">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-1.5 mb-2">
                <GitBranch className="w-3.5 h-3.5 text-sky-400" />
                <span>Prerequisite Dependency Structure</span>
              </h4>

              {loadingPrereqs ? (
                <div className="p-4 flex items-center space-x-2 text-xs text-slate-400">
                  <div className="w-4 h-4 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
                  <span>Tracing dependency graph...</span>
                </div>
              ) : activeCourseModal.prerequisites && activeCourseModal.prerequisites.length > 0 ? (
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-2">
                    {activeCourseModal.prerequisites.map((pCode) => {
                      const isUnresolved = activeCourseModal.unresolved_prerequisites?.includes(pCode);
                      return (
                        <div
                          key={pCode}
                          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-medium ${
                            isUnresolved
                              ? 'bg-amber-950/60 border border-amber-800/60 text-amber-300'
                              : 'bg-sky-950/70 border border-sky-800/70 text-sky-300'
                          }`}
                        >
                          <span>{pCode}</span>
                          {isUnresolved && (
                            <span className="text-[10px] text-amber-400 font-sans" title="Verified code from prospectus pending catalog expansion">
                              (Unresolved Code)
                            </span>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {prereqData?.resolved_prerequisites && prereqData.resolved_prerequisites.length > 0 && (
                    <div className="mt-3 bg-slate-900/60 border border-slate-800 rounded-xl p-3">
                      <span className="text-[11px] font-semibold text-slate-400 block mb-2">Resolved Prerequisite Details:</span>
                      <div className="space-y-1.5">
                        {prereqData.resolved_prerequisites.map((r: Course) => (
                          <div key={r.id} className="text-xs flex items-center justify-between text-slate-300">
                            <span className="font-mono text-sky-400">{r.code} — {r.title}</span>
                            <span className="text-[11px] text-slate-500">{r.credits_formatted}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-800/60 text-xs text-slate-400 flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>This course has no prerequisites. Open for eligible student enrollment.</span>
                </div>
              )}
            </div>

            {/* Program Curricula */}
            {activeCourseModal.offered_in && activeCourseModal.offered_in.length > 0 && (
              <div className="mt-5">
                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Degree Programs Offering This Course
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {activeCourseModal.offered_in.map((p) => (
                    <span key={p} className="text-xs px-2.5 py-1 bg-slate-800/70 text-slate-300 border border-slate-700/60 rounded-md">
                      {p.replace('bs-', 'BS ').toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
