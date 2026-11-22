import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Search,
  BookOpen,
  Users,
  FlaskConical,
  GraduationCap,
  Building2,
  Share2,
  Briefcase,
  UserCheck,
  ArrowRight,
  ExternalLink,
  Sparkles,
  Layers,
  ChevronRight,
  CheckCircle2,
} from 'lucide-react';
import { getHealthStatus, HealthStatus, getUnits } from '../services/api';
import { Unit } from '../types';
import StatCard from '../components/ui/StatCard';
import LoadingSpinner from '../components/ui/LoadingSpinner';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [units, setUnits] = useState<Unit[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [healthRes, unitsRes] = await Promise.all([
          getHealthStatus().catch(() => null),
          getUnits().catch(() => []),
        ]);
        if (healthRes) setHealth(healthRes);
        setUnits(unitsRes);
      } catch (err) {
        console.error('Failed to load homepage data', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const entityCounts = health?.entity_counts || {
    courses: 647,
    faculty: 181,
    publications: 2796,
    research_areas: 656,
    programs: 15,
    units: 9,
  };

  return (
    <div className="space-y-12 pb-12">
      {/* Search-First Hero Section */}
      <section className="relative pt-6 pb-4 sm:pt-10 sm:pb-8 text-center max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-200/80 text-slate-700 text-xs font-medium mb-6">
          <Sparkles className="w-3.5 h-3.5 text-sky-600" />
          <span>Institutional Academic & Research Portal</span>
        </div>

        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
          Discover GIKI's Academic <br className="hidden sm:inline" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-slate-900 via-sky-800 to-sky-600">
            Knowledge Ecosystem
          </span>
        </h1>

        <p className="mt-4 text-sm sm:text-base text-slate-600 max-w-xl mx-auto leading-relaxed">
          Navigate 600+ courses, faculty research profiles, prerequisite graph relationships, and
          collaborate with peers through the Student Teammate Finder.
        </p>

        {/* Hero Search Bar */}
        <form onSubmit={handleSearch} className="mt-8 relative max-w-2xl mx-auto">
          <div className="relative flex items-center shadow-md rounded-2xl overflow-hidden border border-slate-300/80 bg-white focus-within:ring-2 focus-within:ring-sky-500 focus-within:border-sky-500 transition-all">
            <Search className="absolute left-4 w-5 h-5 text-slate-400 stroke-[2]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search courses (e.g. CS101), professors, publications, or research areas..."
              className="w-full py-4 pl-12 pr-28 text-sm sm:text-base bg-transparent border-0 focus:outline-none placeholder:text-slate-400"
            />
            <button
              type="submit"
              className="absolute right-2.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs sm:text-sm font-semibold rounded-xl shadow-xs transition-colors flex items-center gap-1.5"
            >
              <span>Explore</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Quick Filter Tags */}
          <div className="flex flex-wrap items-center justify-center gap-2 mt-3.5 text-xs text-slate-500">
            <span className="font-medium text-slate-400">Popular:</span>
            {['CS112', 'Data Structures', 'Artificial Intelligence', 'Faculty of CSE', 'Robotics'].map(
              (tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => navigate(`/search?q=${encodeURIComponent(tag)}`)}
                  className="px-2.5 py-1 rounded-md bg-white border border-slate-200 hover:border-slate-300 hover:text-slate-900 transition-colors"
                >
                  {tag}
                </button>
              )
            )}
          </div>
        </form>
      </section>

      {/* Institutional Statistics Grid */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Academic Repository Index</h2>
            <p className="text-xs text-slate-500">Verified dataset statistics from GIKI's academic catalog</p>
          </div>
          <Link
            to="/graph"
            className="text-xs font-semibold text-sky-700 hover:text-sky-800 flex items-center gap-1"
          >
            <span>View Graph</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <LoadingSpinner size="md" message="Loading repository metrics..." />
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
            <StatCard
              icon={<BookOpen className="w-5 h-5 text-sky-600" />}
              label="Courses"
              value={entityCounts.courses.toLocaleString()}
              sublabel="Catalog offerings"
              onClick={() => navigate('/courses')}
            />
            <StatCard
              icon={<Users className="w-5 h-5 text-teal-600" />}
              label="Faculty"
              value={entityCounts.faculty.toLocaleString()}
              sublabel="Professors & lect."
              onClick={() => navigate('/faculty')}
            />
            <StatCard
              icon={<FlaskConical className="w-5 h-5 text-purple-600" />}
              label="Research"
              value={entityCounts.research_areas.toLocaleString()}
              sublabel="Active domains"
              onClick={() => navigate('/research')}
            />
            <StatCard
              icon={<GraduationCap className="w-5 h-5 text-amber-600" />}
              label="Programs"
              value={entityCounts.programs.toLocaleString()}
              sublabel="Degree tracks"
              onClick={() => navigate('/programs')}
            />
            <StatCard
              icon={<Building2 className="w-5 h-5 text-indigo-600" />}
              label="Units"
              value={entityCounts.units.toLocaleString()}
              sublabel="Faculties & depts"
              onClick={() => navigate('/units')}
            />
            <StatCard
              icon={<Layers className="w-5 h-5 text-rose-600" />}
              label="Publications"
              value={entityCounts.publications.toLocaleString()}
              sublabel="Indexed papers"
              onClick={() => navigate('/faculty')}
            />
          </div>
        )}
      </section>

      {/* Main Feature Highlight Split Cards */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Module A: Knowledge Graph Explorer */}
        <div className="card p-6 sm:p-7 flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-48 h-48 bg-sky-50 rounded-full blur-3xl -z-10 group-hover:bg-sky-100 transition-colors" />
          <div>
            <div className="w-10 h-10 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center mb-4">
              <Share2 className="w-5 h-5 stroke-[2]" />
            </div>
            <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-sky-50 text-sky-700 text-xs font-semibold mb-2">
              Module A
            </div>
            <h3 className="text-xl font-bold text-slate-900 tracking-tight">
              Academic Knowledge Graph
            </h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
              Explore interconnected relationships across 4,500+ nodes and 5,700+ edges. Traverse
              multi-tier prerequisite pathways, offering departments, and faculty co-authorships.
            </p>
          </div>
          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500 font-medium">Interactive Canvas & Subgraph Traversal</span>
            <Link
              to="/graph"
              className="btn-primary text-xs py-2 px-3.5 inline-flex items-center gap-1.5"
            >
              <span>Explore Graph</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Module B: Student Project Teammate Finder */}
        <div className="card p-6 sm:p-7 flex flex-col justify-between relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-48 h-48 bg-teal-50 rounded-full blur-3xl -z-10 group-hover:bg-teal-100 transition-colors" />
          <div>
            <div className="w-10 h-10 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center mb-4">
              <UserCheck className="w-5 h-5 stroke-[2]" />
            </div>
            <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 text-xs font-semibold mb-2">
              Module B
            </div>
            <h3 className="text-xl font-bold text-slate-900 tracking-tight">
              Student Project Teammate Finder
            </h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
              Voluntary student collaboration platform with a transparent 5-factor explainable matching
              engine. Form project teams, express collaboration interest, and protect your privacy.
            </p>
          </div>
          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between">
            <Link
              to="/profiles"
              className="text-xs font-semibold text-slate-700 hover:text-slate-900"
            >
              Browse Profiles
            </Link>
            <div className="flex items-center gap-2">
              <Link to="/profiles/new" className="btn-secondary text-xs py-1.5 px-3">
                Create Profile
              </Link>
              <Link to="/projects/new" className="btn-primary text-xs py-1.5 px-3">
                Post Project
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Academic Faculties / Units Directory Overview */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Academic Faculties & Departments</h2>
            <p className="text-xs text-slate-500">Explore teaching and research centers at GIKI</p>
          </div>
          <Link
            to="/units"
            className="text-xs font-semibold text-sky-700 hover:text-sky-800 flex items-center gap-1"
          >
            <span>All Units</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {units.slice(0, 6).map((unit) => (
            <Link
              key={unit.id}
              to={`/courses?unit=${encodeURIComponent(unit.id)}`}
              className="card card-hover p-4 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11px] font-mono font-bold uppercase text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-100">
                    {unit.code || unit.id}
                  </span>
                  <span className="text-[11px] text-slate-400 capitalize">{unit.type}</span>
                </div>
                <h4 className="text-sm font-semibold text-slate-900 line-clamp-1">{unit.name}</h4>
                {unit.description && (
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                    {unit.description}
                  </p>
                )}
              </div>
              <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                <span className="text-slate-400">Filter courses</span>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* GIKI CourseHub Ecosystem Companion Banner */}
      <section className="card bg-gradient-to-r from-slate-900 to-slate-800 text-white p-6 sm:p-8 rounded-2xl border-0 shadow-lg relative overflow-hidden">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-white/10 text-sky-300 text-xs font-medium mb-3">
            <ExternalLink className="w-3.5 h-3.5" />
            <span>Community Platform</span>
          </div>
          <h3 className="text-xl sm:text-2xl font-bold tracking-tight">
            GIKI CourseHub — Student Reviews & Course Notes
          </h3>
          <p className="mt-2 text-xs sm:text-sm text-slate-300 leading-relaxed">
            Need student-submitted past papers, instructor difficulty ratings, and crowd-sourced course
            reviews? Visit the independent GIKI CourseHub community web application.
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <a
              href="https://www.gikicoursehub.app/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-white text-slate-900 hover:bg-slate-100 rounded-lg text-xs font-bold transition-colors shadow-xs"
            >
              <span>Visit GIKI CourseHub</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <span className="text-xs text-slate-400">
              Opens external site (gikicoursehub.app)
            </span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
