import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  BookOpen,
  GitBranch,
  Building2,
  GraduationCap,
  ExternalLink,
  Bookmark,
  BookmarkCheck,
  AlertCircle,
  Share2,
  ChevronRight,
  Layers,
} from 'lucide-react';
import {
  getCourseDetail,
  getCoursePrerequisites,
  getCourseRelated,
  PrerequisiteResponse,
} from '../services/api';
import { Course, Program, Unit } from '../types';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import { useSaved } from '../context/SavedContext';

export const CourseDetailPage: React.FC = () => {
  const { courseCode } = useParams<{ courseCode: string }>();
  const navigate = useNavigate();

  const [course, setCourse] = useState<Course | null>(null);
  const [prereqData, setPrereqData] = useState<PrerequisiteResponse | null>(null);
  const [relatedData, setRelatedData] = useState<{
    unit: Unit | null;
    programs: Program[];
    prerequisites: string[];
    dependent_courses: string[];
  } | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { isSaved, toggleSave, addRecentlyViewed } = useSaved();

  useEffect(() => {
    if (!courseCode) return;

    setLoading(true);
    setError(null);

    Promise.all([
      getCourseDetail(courseCode),
      getCoursePrerequisites(courseCode).catch(() => null),
      getCourseRelated(courseCode).catch(() => null),
    ])
      .then(([c, prereqs, related]) => {
        setCourse(c);
        setPrereqData(prereqs);
        setRelatedData(related);

        if (c) {
          addRecentlyViewed({
            id: c.code,
            type: 'course',
            title: `${c.code}: ${c.title}`,
            subtitle: c.unit || 'GIKI Course',
            link: `/courses/${c.code}`,
          });
        }
      })
      .catch((err) => {
        setError(err.message || 'Failed to load course details');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [courseCode]);

  if (loading) {
    return <LoadingSpinner size="lg" message={`Loading course ${courseCode}...`} />;
  }

  if (error || !course) {
    return (
      <div className="space-y-4">
        <button onClick={() => navigate('/courses')} className="btn-ghost text-xs">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Courses
        </button>
        <ErrorMessage
          message={error || `Course '${courseCode}' not found in catalog.`}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  const saved = isSaved(course.code);

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/courses')}
          className="btn-ghost text-xs py-1 px-2.5 -ml-2.5 text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Courses</span>
        </button>

        <div className="flex items-center gap-2">
          <Link
            to={`/graph?entity=course&id=${course.code}`}
            className="btn-secondary text-xs py-1.5 px-3"
          >
            <Share2 className="w-3.5 h-3.5 text-sky-600" />
            <span>Graph View</span>
          </Link>

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
            className={`btn-secondary text-xs py-1.5 px-3 ${
              saved ? 'bg-sky-50 text-sky-800 border-sky-300' : ''
            }`}
          >
            {saved ? (
              <>
                <BookmarkCheck className="w-3.5 h-3.5 text-sky-600" />
                <span>Saved</span>
              </>
            ) : (
              <>
                <Bookmark className="w-3.5 h-3.5 text-slate-400" />
                <span>Save</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Course Header */}
      <div className="card p-6 sm:p-8 bg-white">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <span className="font-mono text-base font-extrabold text-slate-900 bg-slate-100 px-3 py-1 rounded-md border border-slate-200">
            {course.code}
          </span>
          {course.credits_formatted ? (
            <Badge variant="sky" size="md">
              {course.credits_formatted} Credit Hours
            </Badge>
          ) : course.credit_hours ? (
            <Badge variant="sky" size="md">
              {course.credit_hours} Cr
            </Badge>
          ) : null}
          {course.code.endsWith('L') && <Badge variant="teal" size="md">Laboratory Session</Badge>}
          {course.unit && <Badge variant="default" size="md">{course.unit}</Badge>}
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          {course.title}
        </h1>

        {course.description ? (
          <div className="mt-5 prose prose-slate max-w-none text-sm text-slate-600 leading-relaxed">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
              Course Syllabus & Objectives
            </h3>
            <p className="whitespace-pre-line">{course.description}</p>
          </div>
        ) : (
          <p className="mt-4 text-xs italic text-slate-400">
            No detailed syllabus description provided in the institutional catalog.
          </p>
        )}
      </div>

      {/* Grid: Prerequisites vs Curriculum / Programs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Prerequisites Network */}
        <div className="lg:col-span-2 space-y-6">
          {/* Prerequisite Structure */}
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
              <GitBranch className="w-4 h-4 text-sky-600" />
              <h2 className="text-base font-bold text-slate-900">Academic Prerequisites</h2>
            </div>

            {prereqData &&
            (prereqData.direct_prerequisites.length > 0 ||
              prereqData.unresolved_prerequisites.length > 0) ? (
              <div className="space-y-4">
                {/* Direct Verified Prerequisites */}
                {prereqData.direct_prerequisites.length > 0 && (
                  <div>
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                      Direct Required Courses
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {prereqData.direct_prerequisites.map((code) => {
                        const resolvedCourse = (prereqData.resolved_prerequisites || []).find(
                          (c) => c.code === code
                        );
                        return (
                          <Link
                            key={code}
                            to={`/courses/${code}`}
                            className="p-3 rounded-lg border border-slate-200 hover:border-sky-300 hover:bg-sky-50/40 transition-all flex items-center justify-between group"
                          >
                            <div>
                              <div className="font-mono text-xs font-bold text-slate-900 group-hover:text-sky-700">
                                {code}
                              </div>
                              {resolvedCourse && (
                                <div className="text-[11px] text-slate-500 truncate max-w-[200px]">
                                  {resolvedCourse.title}
                                </div>
                              )}
                            </div>
                            <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-600" />
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Unresolved Prerequisite Codes Notice */}
                {prereqData.unresolved_prerequisites.length > 0 && (
                  <div className="p-3.5 rounded-lg bg-amber-50 border border-amber-200/80 text-xs text-amber-900 space-y-1">
                    <div className="flex items-center gap-1.5 font-bold">
                      <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                      <span>Historical or Special Prerequisite Codes</span>
                    </div>
                    <p className="text-[11px] text-amber-800">
                      The syllabus lists code(s):{' '}
                      <span className="font-mono font-bold">
                        {prereqData.unresolved_prerequisites.join(', ')}
                      </span>
                      . These refer to legacy or cross-disciplinary courses not actively offering a separate page.
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-3">
                This course has no prerequisites listed in the catalog. It can be taken directly.
              </div>
            )}
          </div>

          {/* Dependent Courses (courses that require this one) */}
          {relatedData && relatedData.dependent_courses && relatedData.dependent_courses.length > 0 && (
            <div className="card p-6">
              <div className="flex items-center gap-2 mb-3 border-b border-slate-100 pb-3">
                <Layers className="w-4 h-4 text-teal-600" />
                <h2 className="text-base font-bold text-slate-900">Unlocks Higher-Level Courses</h2>
              </div>
              <p className="text-xs text-slate-500 mb-3">
                Completing {course.code} serves as an academic prerequisite for:
              </p>
              <div className="flex flex-wrap gap-2">
                {relatedData.dependent_courses.map((depCode) => (
                  <Link
                    key={depCode}
                    to={`/courses/${depCode}`}
                    className="font-mono text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-800 hover:bg-slate-200 transition-colors border border-slate-200"
                  >
                    {depCode}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Academic Degree Programs & CourseHub Link */}
        <div className="space-y-6">
          {/* Associated Degree Programs */}
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-3 border-b border-slate-100 pb-3">
              <GraduationCap className="w-4 h-4 text-amber-600" />
              <h2 className="text-base font-bold text-slate-900">Degree Programs</h2>
            </div>

            {relatedData && relatedData.programs && relatedData.programs.length > 0 ? (
              <div className="space-y-2">
                <p className="text-xs text-slate-500 mb-2">
                  Included in curriculum roadmaps for:
                </p>
                {relatedData.programs.map((prog) => (
                  <Link
                    key={prog.id}
                    to={`/programs/${prog.id}`}
                    className="p-2.5 rounded-lg border border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-all flex items-center justify-between group block"
                  >
                    <div>
                      <div className="text-xs font-semibold text-slate-800 group-hover:text-sky-700">
                        {prog.name}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                        {prog.code} • {prog.degree_level}
                      </div>
                    </div>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600" />
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">
                Not tied to a specific single BS program roadmap (elective or institute-wide course).
              </p>
            )}
          </div>

          {/* Offering Department */}
          {relatedData && relatedData.unit && (
            <div className="card p-6">
              <div className="flex items-center gap-2 mb-2 border-b border-slate-100 pb-3">
                <Building2 className="w-4 h-4 text-slate-700" />
                <h2 className="text-base font-bold text-slate-900">Department</h2>
              </div>
              <h3 className="text-xs font-bold text-slate-800">{relatedData.unit.name}</h3>
              <p className="text-xs text-slate-500 mt-1">Code: {relatedData.unit.code || relatedData.unit.id}</p>
              <Link
                to={`/courses?unit=${relatedData.unit.id}`}
                className="mt-3 text-xs font-semibold text-sky-700 hover:text-sky-800 inline-flex items-center gap-1"
              >
                <span>Browse all {relatedData.unit.code} courses</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}

          {/* GIKI CourseHub External Companion Box */}
          <div className="card p-6 border-sky-200/80 bg-sky-50/40">
            <div className="flex items-center gap-2 mb-2 text-sky-900 font-bold text-sm">
              <ExternalLink className="w-4 h-4 text-sky-600" />
              <span>GIKI CourseHub</span>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Looking for student-contributed course evaluations, past midterm/final papers, or instructor
              feedback? Check GIKI CourseHub.
            </p>
            <a
              href="https://www.gikicoursehub.app/"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3.5 btn-primary text-xs w-full justify-center"
            >
              <span>Open GIKI CourseHub</span>
              <ExternalLink className="w-3 h-3" />
            </a>
            <span className="text-[10px] text-slate-400 block text-center mt-1.5">
              Independent student-maintained platform
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseDetailPage;
