import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  GraduationCap,
  Building2,
  Calendar,
  ChevronRight,
  ChevronDown,
  Layers,
  Clock,
  BookOpen,
  FlaskConical,
} from 'lucide-react';
import { getProgramDetail, getProgramCurriculum, getUnitDetail } from '../services/api';
import { Program, Unit } from '../types';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';

export const ProgramDetailPage: React.FC = () => {
  const { programId } = useParams<{ programId: string }>();
  const navigate = useNavigate();

  const [program, setProgram] = useState<Program | null>(null);
  const [curriculumData, setCurriculumData] = useState<any | null>(null);
  const [unit, setUnit] = useState<Unit | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collapsedSemesters, setCollapsedSemesters] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!programId) return;

    setLoading(true);
    setError(null);

    Promise.all([
      getProgramDetail(programId),
      getProgramCurriculum(programId).catch(() => null),
    ])
      .then(([prog, curr]) => {
        setProgram(prog);
        setCurriculumData(curr);

        const targetUnitId = prog?.unit_id || (prog as any)?.unit;
        if (targetUnitId) {
          getUnitDetail(targetUnitId)
            .then(setUnit)
            .catch(() => null);
        }
      })
      .catch((err) => {
        setError(err.message || 'Failed to load degree program');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [programId]);

  if (loading) {
    return <LoadingSpinner size="lg" message="Loading program curriculum roadmap..." />;
  }

  if (error || !program) {
    return (
      <div className="space-y-4">
        <button onClick={() => navigate('/programs')} className="btn-ghost text-xs">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Programs
        </button>
        <ErrorMessage
          message={error || `Program '${programId}' not found.`}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  // Extract clean semester map
  // Note: curriculumData?.semesters is an object with { "Semester 1 (Freshman - Fall)": [...], ... }
  let semestersMap: Record<string, any[]> = {};

  if (curriculumData?.semesters && typeof curriculumData.semesters === 'object' && !Array.isArray(curriculumData.semesters)) {
    semestersMap = curriculumData.semesters;
  } else if (Array.isArray(curriculumData?.curriculum)) {
    // If flat curriculum list was provided, group by semester 1..8
    curriculumData.curriculum.forEach((c: any) => {
      const sem = c.semester || c.curriculum_placement?.semester || 0;
      const key = sem > 0 ? `Semester ${sem}` : 'Electives & Other Requirements';
      if (!semestersMap[key]) semestersMap[key] = [];
      semestersMap[key].push(c);
    });
  }

  // Ordered list of semester keys
  const semesterKeys = Object.keys(semestersMap).sort((a, b) => {
    const numA = parseInt(a.replace(/\D/g, '')) || 99;
    const numB = parseInt(b.replace(/\D/g, '')) || 99;
    return numA - numB;
  });

  const totalCourses =
    curriculumData?.total_courses ||
    Object.values(semestersMap).reduce((acc, list) => acc + (Array.isArray(list) ? list.length : 0), 0);

  const toggleSemester = (semKey: string) => {
    setCollapsedSemesters((prev) => ({
      ...prev,
      [semKey]: !prev[semKey],
    }));
  };

  const collapseAll = () => {
    const allCollapsed: Record<string, boolean> = {};
    semesterKeys.forEach((k) => (allCollapsed[k] = true));
    setCollapsedSemesters(allCollapsed);
  };

  const expandAll = () => {
    setCollapsedSemesters({});
  };

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Back button */}
      <div>
        <button
          onClick={() => navigate('/programs')}
          className="btn-ghost text-xs py-1 px-2.5 -ml-2.5 text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to All Programs</span>
        </button>
      </div>

      {/* Program Header */}
      <div className="card p-6 sm:p-8 bg-white border border-slate-200/80 shadow-sm">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="font-mono text-xs font-bold text-amber-800 bg-amber-50 px-2.5 py-1 rounded border border-amber-200">
            {program.code || program.id.toUpperCase()}
          </span>
          <Badge variant="default" size="md">
            {program.degree_level || 'Bachelor of Science (BS)'}
          </Badge>
          {(unit?.name || program.unit_name) && (
            <Badge variant="sky" size="md">
              {unit?.name || program.unit_name}
            </Badge>
          )}
          <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full flex items-center gap-1">
            <Clock className="w-3 h-3 text-slate-400" />
            <span>4 Years • 8 Semesters</span>
          </span>
          <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200/60 flex items-center gap-1">
            <BookOpen className="w-3 h-3 text-emerald-600" />
            <span>{totalCourses} Courses</span>
          </span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          {program.name}
        </h1>

        <p className="text-xs sm:text-sm text-slate-500 mt-2.5 leading-relaxed max-w-3xl">
          Four-year academic roadmap comprising core engineering fundamentals, computing electives,
          mathematical sciences, and final-year capstone design projects organized semester-by-semester.
        </p>

        {/* Quick jump semester bar */}
        {semesterKeys.length > 0 && (
          <div className="mt-6 pt-5 border-t border-slate-100">
            <div className="flex items-center justify-between gap-3 mb-2.5">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                Quick Jump to Semester:
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={expandAll}
                  className="text-[11px] font-medium text-sky-600 hover:text-sky-700 underline"
                >
                  Expand all
                </button>
                <span className="text-slate-300">•</span>
                <button
                  onClick={collapseAll}
                  className="text-[11px] font-medium text-slate-500 hover:text-slate-700 underline"
                >
                  Collapse all
                </button>
              </div>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {semesterKeys.map((semKey, idx) => {
                const semShort = `Sem ${idx + 1}`;
                const count = Array.isArray(semestersMap[semKey]) ? semestersMap[semKey].length : 0;
                return (
                  <a
                    key={semKey}
                    href={`#semester-${idx + 1}`}
                    className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 hover:bg-sky-50 hover:text-sky-700 hover:border-sky-200 border border-transparent transition-all flex items-center gap-1 text-slate-700"
                  >
                    <span>{semShort}</span>
                    <span className="text-[10px] text-slate-400">({count})</span>
                  </a>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Curriculum Semester Roadmap */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-700 flex items-center justify-center border border-sky-100">
              <Calendar className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Curriculum Course Roadmap</h2>
              <p className="text-xs text-slate-500">
                Official syllabus schedule from Semester 1 through Semester 8
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold text-slate-700 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
            {semesterKeys.length} Semesters ({totalCourses} courses)
          </span>
        </div>

        {semesterKeys.length > 0 ? (
          <div className="space-y-5">
            {semesterKeys.map((semKey, sIndex) => {
              const coursesList: any[] = Array.isArray(semestersMap[semKey])
                ? semestersMap[semKey]
                : [];
              const isCollapsed = Boolean(collapsedSemesters[semKey]);

              // Calculate total credit hours in this semester
              const totalCredits = coursesList.reduce((sum, c) => {
                const cr = typeof c.credit_hours === 'number' ? c.credit_hours : 0;
                return sum + cr;
              }, 0);

              return (
                <div
                  key={semKey}
                  id={`semester-${sIndex + 1}`}
                  className="card overflow-hidden border border-slate-200/90 shadow-sm"
                >
                  {/* Semester Header Accordion */}
                  <div
                    onClick={() => toggleSemester(semKey)}
                    className="p-4 sm:p-5 bg-gradient-to-r from-slate-50 to-white border-b border-slate-200/70 flex items-center justify-between cursor-pointer hover:bg-slate-50/80 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-sky-600 text-white text-xs font-bold flex items-center justify-center shrink-0 shadow-sm">
                        {sIndex + 1}
                      </div>
                      <div>
                        <h3 className="text-sm sm:text-base font-bold text-slate-900">
                          {semKey}
                        </h3>
                        <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                          <span>{coursesList.length} courses</span>
                          {totalCredits > 0 && (
                            <>
                              <span>•</span>
                              <span>{totalCredits} Credit Hours</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-slate-400">
                      <span className="text-xs font-medium text-slate-500 hidden sm:inline">
                        {isCollapsed ? 'Show courses' : 'Hide'}
                      </span>
                      {isCollapsed ? (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-500" />
                      )}
                    </div>
                  </div>

                  {/* Course Cards Grid */}
                  {!isCollapsed && (
                    <div className="p-4 sm:p-5 bg-white">
                      {coursesList.length === 0 ? (
                        <p className="text-xs text-slate-400 italic py-2">
                          No specific courses scheduled for this semester.
                        </p>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
                          {coursesList.map((courseItem) => {
                            const code =
                              typeof courseItem === 'string'
                                ? courseItem
                                : courseItem.code || 'UNKNOWN';
                            const title =
                              typeof courseItem === 'string'
                                ? courseItem
                                : courseItem.title || courseItem.name || code;
                            const isLab =
                              typeof courseItem === 'object' &&
                              (courseItem.is_lab || code.endsWith('L'));
                            const creditHours =
                              typeof courseItem === 'object' ? courseItem.credit_hours : null;
                            const prereqs: string[] =
                              typeof courseItem === 'object' && Array.isArray(courseItem.prerequisites)
                                ? courseItem.prerequisites
                                : [];

                            return (
                              <Link
                                key={code}
                                to={`/courses/${code}`}
                                className="p-3.5 rounded-xl border border-slate-200/80 hover:border-sky-300 hover:bg-sky-50/20 hover:shadow-sm transition-all flex flex-col justify-between group bg-white"
                              >
                                <div>
                                  {/* Code and Credit badges */}
                                  <div className="flex items-center justify-between gap-2 mb-2">
                                    <span className="font-mono text-xs font-bold text-slate-900 group-hover:text-sky-700 bg-slate-100 group-hover:bg-sky-100/70 px-2 py-0.5 rounded transition-colors">
                                      {code}
                                    </span>
                                    <div className="flex items-center gap-1.5">
                                      {creditHours !== null && creditHours !== undefined && (
                                        <span className="text-[11px] font-semibold text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded">
                                          {creditHours} Cr
                                        </span>
                                      )}
                                      {isLab && (
                                        <span className="text-[10px] font-bold text-indigo-700 bg-indigo-50 border border-indigo-200/60 px-1.5 py-0.5 rounded flex items-center gap-0.5">
                                          <FlaskConical className="w-2.5 h-2.5" />
                                          Lab
                                        </span>
                                      )}
                                    </div>
                                  </div>

                                  {/* Course Title */}
                                  <h4 className="text-xs sm:text-sm font-semibold text-slate-800 group-hover:text-sky-900 line-clamp-2 leading-snug">
                                    {title}
                                  </h4>
                                </div>

                                {/* Prerequisites and Arrow Footer */}
                                <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px]">
                                  {prereqs.length > 0 ? (
                                    <span className="text-amber-700 font-medium truncate max-w-[170px]">
                                      Prereq: {prereqs.join(', ')}
                                    </span>
                                  ) : (
                                    <span className="text-slate-400">Core Course</span>
                                  )}
                                  <span className="text-sky-600 group-hover:translate-x-0.5 transition-transform flex items-center font-medium">
                                    <ChevronRight className="w-3.5 h-3.5" />
                                  </span>
                                </div>
                              </Link>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="card p-8 text-center text-xs text-slate-500">
            Curriculum details for {program.name} are currently being updated.
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgramDetailPage;
