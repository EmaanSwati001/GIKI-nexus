import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { GraduationCap, BookOpen, ChevronRight, Building2 } from 'lucide-react';
import { getPrograms, getUnits } from '../services/api';
import { Program, Unit } from '../types';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';

export const ProgramsPage: React.FC = () => {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [selectedUnit, setSelectedUnit] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const filteredPrograms = selectedUnit
    ? programs.filter((p) => p.unit_id === selectedUnit)
    : programs;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
            <GraduationCap className="w-3.5 h-3.5 text-amber-600" />
            <span>Curriculum Roadmaps</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
            Degree Programs
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Undergraduate BS curricula, semester roadmaps, and course requirements at GIKI
          </p>
        </div>

        {/* Filter by Department */}
        <div>
          <select
            value={selectedUnit}
            onChange={(e) => setSelectedUnit(e.target.value)}
            className="input-field text-xs py-1.5 cursor-pointer"
          >
            <option value="">All Academic Faculties</option>
            {units.map((u) => (
              <option key={u.id} value={u.id}>
                {u.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <LoadingSpinner message="Loading degree programs..." />
      ) : error ? (
        <ErrorMessage message={error} onRetry={() => window.location.reload()} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPrograms.map((prog) => {
            const unit = units.find((u) => u.id === prog.unit_id);

            return (
              <Link
                key={prog.id}
                to={`/programs/${prog.id}`}
                className="card card-hover p-5 flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2.5">
                    <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200/80">
                      {prog.code}
                    </span>
                    <Badge variant="default" size="sm">
                      {prog.degree_level || 'BS'}
                    </Badge>
                  </div>

                  <h3 className="text-base font-bold text-slate-900 group-hover:text-amber-800 transition-colors">
                    {prog.name}
                  </h3>

                  {unit && (
                    <p className="text-xs text-slate-500 mt-1.5 flex items-center gap-1.5">
                      <Building2 className="w-3.5 h-3.5 text-slate-400" />
                      <span>{unit.name}</span>
                    </p>
                  )}
                </div>

                <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-400">4-Year Degree Roadmap</span>
                  <span className="font-semibold text-slate-700 group-hover:text-amber-800 flex items-center gap-0.5">
                    <span>View Curriculum</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ProgramsPage;
