import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Building2, BookOpen, Users, GraduationCap, ChevronRight } from 'lucide-react';
import { getUnits, getPrograms } from '../services/api';
import { Unit, Program } from '../types';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';

export const UnitsPage: React.FC = () => {
  const [units, setUnits] = useState<Unit[]>([]);
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getUnits(), getPrograms().catch(() => [])])
      .then(([uList, pList]) => {
        setUnits(uList);
        setPrograms(pList);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load academic units');
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-200/80 pb-5">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          <Building2 className="w-3.5 h-3.5 text-indigo-600" />
          <span>Institutional Architecture</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
          Academic Faculties & Departments
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          The 9 founding faculties, schools, and teaching departments comprising GIKI
        </p>
      </div>

      {loading ? (
        <LoadingSpinner message="Loading faculties & departments..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={() => window.location.reload()} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {units.map((unit) => {
            const unitPrograms = programs.filter(
              (p) => p.unit_id === unit.id || p.unit_id === unit.code
            );

            return (
              <div
                key={unit.id}
                className="card card-hover p-6 flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="font-mono text-xs font-extrabold uppercase text-indigo-800 bg-indigo-50 px-2.5 py-1 rounded border border-indigo-200/80">
                      {unit.code || unit.id}
                    </span>
                    <Badge variant="default" size="sm">
                      {unit.type || 'Faculty'}
                    </Badge>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 group-hover:text-indigo-800 transition-colors">
                    {unit.name}
                  </h3>

                  {unit.description && (
                    <p className="text-xs text-slate-500 mt-2 leading-relaxed line-clamp-3">
                      {unit.description}
                    </p>
                  )}

                  {/* Degree Programs under this unit */}
                  {unitPrograms.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-slate-100">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">
                        Degree Programs ({unitPrograms.length})
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {unitPrograms.map((p) => (
                          <Link
                            key={p.id}
                            to={`/programs/${p.id}`}
                            className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-50 text-slate-700 hover:bg-slate-100 border border-slate-200/60"
                          >
                            {p.code}
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Bottom Quick Links */}
                <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between gap-2 text-xs">
                  <Link
                    to={`/courses?unit=${encodeURIComponent(unit.id)}`}
                    className="font-medium text-slate-700 hover:text-indigo-700 flex items-center gap-1"
                  >
                    <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                    <span>Courses</span>
                  </Link>

                  <Link
                    to={`/faculty?unit=${encodeURIComponent(unit.id)}`}
                    className="font-medium text-slate-700 hover:text-indigo-700 flex items-center gap-1"
                  >
                    <Users className="w-3.5 h-3.5 text-slate-400" />
                    <span>Faculty</span>
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default UnitsPage;
