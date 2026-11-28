import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  GraduationCap,
  BookOpen,
  ChevronRight,
  ChevronDown,
  Building2,
  Terminal,
  Zap,
  Flame,
  Wrench,
  Landmark,
  Briefcase,
  Search,
  Clock,
  Layers,
  FlaskConical,
} from 'lucide-react';
import { getPrograms, getUnits, getProgramCurriculum } from '../services/api';
import { Program, Unit } from '../types';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';

// Helper to choose distinct icon for each academic unit
function getFacultyIcon(unitId: string) {
  const norm = unitId.toLowerCase();
  if (norm.includes('fcse') || norm.includes('cs')) {
    return <Terminal className="w-5 h-5" />;
  }
  if (norm.includes('fee') || norm.includes('ee')) {
    return <Zap className="w-5 h-5" />;
  }
  if (norm.includes('fmce') || norm.includes('che') || norm.includes('mse')) {
    return <Flame className="w-5 h-5" />;
  }
  if (norm.includes('fme') || norm.includes('me')) {
    return <Wrench className="w-5 h-5" />;
  }
  if (norm.includes('dcve') || norm.includes('civil')) {
    return <Landmark className="w-5 h-5" />;
  }
  if (norm.includes('mgs') || norm.includes('management')) {
    return <Briefcase className="w-5 h-5" />;
  }
  return <Building2 className="w-5 h-5" />;
}

export const ProgramsPage: React.FC = () => {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [selectedUnit, setSelectedUnit] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Accordion state for faculties (all open by default)
  const [collapsedFaculties, setCollapsedFaculties] = useState<Record<string, boolean>>({});

  // Inline expanded programs for showing semesters directly (like Course Hub)
  const [expandedProgramId, setExpandedProgramId] = useState<string | null>(null);
  const [inlineCurricula, setInlineCurricula] = useState<Record<string, any>>({});
  const [inlineLoading, setInlineLoading] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getPrograms(), getUnits()])
      .then(([progs, uList]) => {
        setPrograms(progs);
        setUnits(uList);
      })
      .catch((err) => {
        setError(err.message || 'Failed to fetch academic degree programs');
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const toggleFaculty = (unitId: string) => {
    setCollapsedFaculties((prev) => ({
      ...prev,
      [unitId]: !prev[unitId],
    }));
  };

  const toggleProgramExpand = async (progId: string) => {
    if (expandedProgramId === progId) {
      setExpandedProgramId(null);
      return;
    }

    setExpandedProgramId(progId);

    // If curriculum not loaded yet for this program, fetch it
    if (!inlineCurricula[progId]) {
      setInlineLoading(progId);
      try {
        const curr = await getProgramCurriculum(progId);
        setInlineCurricula((prev) => ({ ...prev, [progId]: curr }));
      } catch (err) {
        console.error('Failed to load inline curriculum', err);
      } finally {
        setInlineLoading(null);
      }
    }
  };

  // Group programs by faculty/unit
  const unitMap = new Map<string, Unit>();
  units.forEach((u) => unitMap.set(u.id.toLowerCase(), u));

  // Determine list of faculties to display
  const facultyGroups: {
    unitId: string;
    unitCode: string;
    unitName: string;
    programs: Program[];
    totalCourses: number;
  }[] = [];

  const grouped = new Map<string, Program[]>();
  programs.forEach((p) => {
    const rawUnit = p.unit_id || (p as any).unit || 'other';
    const uKey = rawUnit.toLowerCase();
    if (!grouped.has(uKey)) {
      grouped.set(uKey, []);
    }
    grouped.get(uKey)!.push(p);
  });

  // Desired faculty order matching GIKI Course Hub
  const facultyOrder = ['fcse', 'fee', 'fmce', 'fme', 'dcve', 'mgs'];
  const allKeys = Array.from(
    new Set([...facultyOrder, ...Array.from(grouped.keys())])
  ).filter((k) => grouped.has(k));

  allKeys.forEach((uKey) => {
    let progs = grouped.get(uKey) || [];

    // Filter by search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      progs = progs.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.code.toLowerCase().includes(q) ||
          p.id.toLowerCase().includes(q)
      );
    }

    // Filter by selected faculty pill
    if (selectedUnit !== 'all' && selectedUnit.toLowerCase() !== uKey) {
      return;
    }

    if (progs.length > 0) {
      const unitObj = unitMap.get(uKey);
      const unitName =
        unitObj?.name ||
        (uKey === 'fcse'
          ? 'Faculty of Computer Science & Engineering'
          : uKey === 'fee'
          ? 'Faculty of Electrical Engineering'
          : uKey === 'fmce'
          ? 'Faculty of Materials and Chemical Engineering'
          : uKey === 'fme'
          ? 'Faculty of Mechanical Engineering'
          : uKey === 'dcve'
          ? 'Department of Civil Engineering'
          : uKey === 'mgs'
          ? 'School of Management Sciences'
          : uKey.toUpperCase());

      const totCourses = progs.reduce((sum, p) => sum + (p.course_count || 0), 0);

      facultyGroups.push({
        unitId: uKey,
        unitCode: uKey.toUpperCase(),
        unitName,
        programs: progs,
        totalCourses: totCourses,
      });
    }
  });

  const totalProgramsCount = programs.length;
  const totalCoursesCount = programs.reduce((sum, p) => sum + (p.course_count || 0), 0);

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-sky-700 bg-sky-50 px-2.5 py-1 rounded-md w-fit mb-2">
            <GraduationCap className="w-3.5 h-3.5" />
            <span>Academic Curricula & Roadmaps</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900">
            Degree Programs
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl">
            Explore 4-year undergraduate bachelor curricula at GIKI organized by faculty and semester-by-semester course schedules.
          </p>
        </div>

        {/* Global Summary Badge */}
        <div className="flex items-center gap-3">
          <div className="card px-3.5 py-2 bg-slate-50 text-slate-700 text-xs border border-slate-200">
            <span className="font-bold text-slate-900">{totalProgramsCount}</span> Programs
          </div>
          <div className="card px-3.5 py-2 bg-slate-50 text-slate-700 text-xs border border-slate-200">
            <span className="font-bold text-slate-900">{facultyGroups.length}</span> Faculties
          </div>
          <div className="card px-3.5 py-2 bg-sky-50 text-sky-800 text-xs border border-sky-200 font-medium">
            <span className="font-bold">{totalCoursesCount}</span> Total Courses
          </div>
        </div>
      </div>

      {/* Search and Faculty Filter Pills */}
      <div className="space-y-3">
        {/* Search Bar */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search degree program (e.g., Computer Science, Artificial Intelligence, Electrical)..."
            className="input-field pl-9 pr-4 py-2.5 text-xs w-full bg-white shadow-sm"
          />
        </div>

        {/* Faculty filter tabs */}
        <div className="flex flex-wrap items-center gap-1.5 pt-1">
          <button
            onClick={() => setSelectedUnit('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              selectedUnit === 'all'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            All Faculties
          </button>
          {facultyOrder.map((fKey) => {
            const isSelected = selectedUnit.toLowerCase() === fKey;
            return (
              <button
                key={fKey}
                onClick={() => setSelectedUnit(fKey)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                  isSelected
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                }`}
              >
                {fKey}
              </button>
            );
          })}
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Loading GIKI degree programs and curricula..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={() => window.location.reload()} />
      ) : facultyGroups.length === 0 ? (
        <div className="card p-12 text-center text-xs text-slate-500">
          No degree programs match your filter &apos;{searchQuery}&apos;.
        </div>
      ) : (
        /* Faculties List modeled after GIKI Course Hub */
        <div className="space-y-8">
          {facultyGroups.map((group) => {
            const isFacultyCollapsed = Boolean(collapsedFaculties[group.unitId]);

            return (
              <div
                key={group.unitId}
                className="rounded-2xl border border-slate-300/80 bg-white shadow-sm overflow-hidden"
              >
                {/* Faculty Card Header (styled like Course Hub teal/slate banner) */}
                <div
                  onClick={() => toggleFaculty(group.unitId)}
                  className="p-5 sm:p-6 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white flex items-center justify-between cursor-pointer select-none transition-all hover:brightness-105"
                >
                  <div className="flex items-center gap-3.5 sm:gap-4">
                    <div className="w-12 h-12 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 flex items-center justify-center text-emerald-400 shrink-0">
                      {getFacultyIcon(group.unitId)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold uppercase tracking-wider text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-500/30">
                          {group.unitCode}
                        </span>
                        <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">
                          {group.unitName}
                        </h2>
                      </div>
                      <div className="flex items-center gap-2 mt-1.5 text-xs text-slate-300">
                        <span className="bg-white/10 px-2 py-0.5 rounded-full font-medium text-slate-200">
                          {group.programs.length} Programs
                        </span>
                        <span>•</span>
                        <span className="text-slate-300">
                          {group.totalCourses} Courses in curriculum
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="text-slate-300 hover:text-white transition-colors p-1">
                    {isFacultyCollapsed ? (
                      <ChevronRight className="w-5 h-5" />
                    ) : (
                      <ChevronDown className="w-5 h-5" />
                    )}
                  </div>
                </div>

                {/* Programs under this Faculty */}
                {!isFacultyCollapsed && (
                  <div className="divide-y divide-slate-100 bg-slate-50/40">
                    {group.programs.map((prog) => {
                      const isExpanded = expandedProgramId === prog.id;
                      const currData = inlineCurricula[prog.id];
                      const isLoadingCurr = inlineLoading === prog.id;

                      const semestersMap: Record<string, any[]> =
                        currData?.semesters && typeof currData.semesters === 'object'
                          ? currData.semesters
                          : {};

                      const semesterKeys = Object.keys(semestersMap).sort((a, b) => {
                        const numA = parseInt(a.replace(/\D/g, '')) || 99;
                        const numB = parseInt(b.replace(/\D/g, '')) || 99;
                        return numA - numB;
                      });

                      return (
                        <div key={prog.id} className="transition-all">
                          {/* Program Row */}
                          <div className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white hover:bg-slate-50/80 transition-colors">
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="text-base font-bold text-slate-900 hover:text-sky-700">
                                  <Link to={`/programs/${prog.id}`}>
                                    {prog.name}
                                  </Link>
                                </h3>
                              </div>
                              <p className="text-xs text-slate-500 mt-1 flex items-center gap-1.5">
                                <Clock className="w-3.5 h-3.5 text-slate-400" />
                                <span>{prog.duration_years || 4} years</span>
                                <span>•</span>
                                <span className="font-semibold text-slate-700">
                                  {prog.course_count || 0} courses
                                </span>
                              </p>
                            </div>

                            {/* Action Buttons: Expand inline OR View Program Page */}
                            <div className="flex items-center gap-2 self-start sm:self-auto">
                              <button
                                onClick={() => toggleProgramExpand(prog.id)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all border ${
                                  isExpanded
                                    ? 'bg-sky-50 text-sky-800 border-sky-300'
                                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                                }`}
                              >
                                <span>{isExpanded ? 'Collapse' : 'Expand'}</span>
                                {isExpanded ? (
                                  <ChevronDown className="w-3.5 h-3.5 text-sky-700" />
                                ) : (
                                  <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                                )}
                              </button>

                              <Link
                                to={`/programs/${prog.id}`}
                                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-900 text-white hover:bg-slate-800 flex items-center gap-1 transition-all"
                              >
                                <span>Roadmap</span>
                                <ChevronRight className="w-3.5 h-3.5" />
                              </Link>
                            </div>
                          </div>

                          {/* Inline Curriculum View when 'Expand' is clicked (matching Course Hub experience) */}
                          {isExpanded && (
                            <div className="p-4 sm:p-6 bg-slate-50/90 border-t border-b border-slate-200/80 animate-in fade-in duration-200">
                              {isLoadingCurr ? (
                                <div className="py-6 flex justify-center">
                                  <LoadingSpinner size="sm" message="Loading semester breakdown..." />
                                </div>
                              ) : semesterKeys.length > 0 ? (
                                <div className="space-y-6">
                                  <div className="flex items-center justify-between">
                                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                                      <Layers className="w-4 h-4 text-sky-600" />
                                      <span>
                                        {prog.name} — 8 Semester Schedule
                                      </span>
                                    </h4>
                                    <Link
                                      to={`/programs/${prog.id}`}
                                      className="text-xs font-semibold text-sky-600 hover:text-sky-800 flex items-center gap-1"
                                    >
                                      <span>Open full details page</span>
                                      <ChevronRight className="w-3 h-3" />
                                    </Link>
                                  </div>

                                  <div className="space-y-4">
                                    {semesterKeys.map((semKey, sIndex) => {
                                      const courses: any[] = semestersMap[semKey] || [];
                                      return (
                                        <div
                                          key={semKey}
                                          className="p-3.5 rounded-xl bg-white border border-slate-200 shadow-2xs"
                                        >
                                          <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-slate-100">
                                            <div className="flex items-center gap-2">
                                              <span className="w-5 h-5 rounded-full bg-sky-100 text-sky-800 text-[11px] font-bold flex items-center justify-center">
                                                {sIndex + 1}
                                              </span>
                                              <span className="text-xs font-bold text-slate-800">
                                                {semKey}
                                              </span>
                                            </div>
                                            <span className="text-[11px] text-slate-500 font-medium">
                                              {courses.length} courses
                                            </span>
                                          </div>

                                          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                                            {courses.map((c) => {
                                              const code = c.code || 'UNKNOWN';
                                              const title = c.title || c.name || code;
                                              const isLab = c.is_lab || code.endsWith('L');

                                              return (
                                                <Link
                                                  key={code}
                                                  to={`/courses/${code}`}
                                                  className="p-2.5 rounded-lg border border-slate-200/80 hover:border-sky-300 hover:bg-sky-50/30 transition-all flex items-center justify-between group bg-white"
                                                >
                                                  <div className="min-w-0 pr-2">
                                                    <div className="flex items-center gap-1.5">
                                                      <span className="font-mono text-xs font-bold text-slate-900 group-hover:text-sky-700">
                                                        {code}
                                                      </span>
                                                      {isLab && (
                                                        <span className="text-[9px] font-bold text-indigo-700 bg-indigo-50 px-1 rounded">
                                                          Lab
                                                        </span>
                                                      )}
                                                      {c.credit_hours !== null && (
                                                        <span className="text-[10px] text-slate-500">
                                                          {c.credit_hours} Cr
                                                        </span>
                                                      )}
                                                    </div>
                                                    <p className="text-[11px] text-slate-600 truncate mt-0.5 group-hover:text-slate-900">
                                                      {title}
                                                    </p>
                                                  </div>
                                                  <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-600 shrink-0" />
                                                </Link>
                                              );
                                            })}
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              ) : (
                                <p className="text-xs text-slate-500 italic py-2">
                                  Curriculum roadmap is being processed for this program.
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ProgramsPage;
