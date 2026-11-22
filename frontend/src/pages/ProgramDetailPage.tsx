import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  GraduationCap,
  Building2,
  BookOpen,
  Calendar,
  ChevronRight,
  Layers,
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
  const [curriculum, setCurriculum] = useState<any | null>(null);
  const [unit, setUnit] = useState<Unit | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
        setCurriculum(curr);

        if (prog && prog.unit_id) {
          getUnitDetail(prog.unit_id)
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

  // Curriculum breakdown
  const curriculumMap =
    curriculum?.curriculum ||
    curriculum?.semesters ||
    program.curriculum ||
    {};

  const semesterKeys = Object.keys(curriculumMap).sort((a, b) => {
    const numA = parseInt(a.replace(/\D/g, '')) || 0;
    const numB = parseInt(b.replace(/\D/g, '')) || 0;
    return numA - numB;
  });

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Back button */}
      <div>
        <button
          onClick={() => navigate('/programs')}
          className="btn-ghost text-xs py-1 px-2.5 -ml-2.5 text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Programs</span>
        </button>
      </div>

      {/* Program Header */}
      <div className="card p-6 sm:p-8 bg-white">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <span className="font-mono text-xs font-bold text-amber-800 bg-amber-50 px-2.5 py-1 rounded border border-amber-200">
            {program.code}
          </span>
          <Badge variant="default" size="md">
            {program.degree_level || 'Bachelor of Science (BS)'}
          </Badge>
          {unit && <Badge variant="sky" size="md">{unit.name}</Badge>}
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          {program.name}
        </h1>

        <p className="text-xs sm:text-sm text-slate-500 mt-2 leading-relaxed">
          Four-year academic roadmap comprising core engineering fundamentals, computing electives,
          mathematical sciences, and final year capstone design projects.
        </p>
      </div>

      {/* Curriculum Semester Roadmap */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-slate-200/80 pb-3">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-sky-600" />
            <h2 className="text-base font-bold text-slate-900">Curriculum Course Roadmap</h2>
          </div>
          <span className="text-xs text-slate-500">
            {semesterKeys.length} Semester{semesterKeys.length !== 1 ? 's' : ''} Documented
          </span>
        </div>

        {semesterKeys.length > 0 ? (
          <div className="space-y-6">
            {semesterKeys.map((semKey) => {
              const coursesList: string[] = Array.isArray(curriculumMap[semKey])
                ? curriculumMap[semKey]
                : [];

              return (
                <div key={semKey} className="card p-5">
                  <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-sky-500" />
                    <span>{semKey.replace(/_/g, ' ')}</span>
                    <span className="text-xs font-normal text-slate-400 normal-case">
                      ({coursesList.length} courses)
                    </span>
                  </h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                    {coursesList.map((courseItem) => {
                      // courseItem may be string code like "CS101" or an object
                      const code =
                        typeof courseItem === 'string'
                          ? courseItem
                          : (courseItem as any).code || JSON.stringify(courseItem);

                      return (
                        <Link
                          key={code}
                          to={`/courses/${code}`}
                          className="p-2.5 rounded-lg border border-slate-200 hover:border-sky-300 hover:bg-sky-50/30 transition-all flex items-center justify-between group"
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-slate-900 group-hover:text-sky-700">
                              {code}
                            </span>
                          </div>
                          <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-sky-600" />
                        </Link>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="card p-8 text-center text-xs text-slate-500">
            Detailed semester breakdown for {program.name} is scheduled for dynamic ingestion in the next catalog release.
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgramDetailPage;
