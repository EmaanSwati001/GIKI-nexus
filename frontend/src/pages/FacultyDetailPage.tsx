import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Users,
  CheckCircle2,
  Mail,
  ExternalLink,
  BookOpen,
  FlaskConical,
  GraduationCap,
  Share2,
  Bookmark,
  BookmarkCheck,
  FileText,
} from 'lucide-react';
import {
  getFacultyDetail,
  getFacultyPublications,
  getFacultyResearchAreas,
} from '../services/api';
import { Faculty, Publication, ResearchArea } from '../types';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import { useSaved } from '../context/SavedContext';

export const FacultyDetailPage: React.FC = () => {
  const { facultyId } = useParams<{ facultyId: string }>();
  const navigate = useNavigate();

  const [faculty, setFaculty] = useState<Faculty | null>(null);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [researchAreas, setResearchAreas] = useState<ResearchArea[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { isSaved, toggleSave, addRecentlyViewed } = useSaved();

  useEffect(() => {
    if (!facultyId) return;

    setLoading(true);
    setError(null);

    Promise.all([
      getFacultyDetail(facultyId),
      getFacultyPublications(facultyId).catch(() => []),
      getFacultyResearchAreas(facultyId).catch(() => []),
    ])
      .then(([f, pubs, areas]) => {
        setFaculty(f);
        setPublications(pubs);
        setResearchAreas(areas);

        if (f) {
          addRecentlyViewed({
            id: f.id,
            type: 'faculty',
            title: f.name,
            subtitle: f.designation || f.academic_rank || 'GIKI Faculty',
            link: `/faculty/${f.id}`,
          });
        }
      })
      .catch((err) => {
        setError(err.message || 'Failed to load faculty profile');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [facultyId]);

  if (loading) {
    return <LoadingSpinner size="lg" message="Loading scholar profile..." />;
  }

  if (error || !faculty) {
    return (
      <div className="space-y-4">
        <button onClick={() => navigate('/faculty')} className="btn-ghost text-xs">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Faculty Directory
        </button>
        <ErrorMessage
          message={error || `Faculty profile '${facultyId}' not found.`}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  const saved = isSaved(faculty.id);

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/faculty')}
          className="btn-ghost text-xs py-1 px-2.5 -ml-2.5 text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Directory</span>
        </button>

        <div className="flex items-center gap-2">
          <Link
            to={`/graph?entity=faculty&id=${faculty.id}`}
            className="btn-secondary text-xs py-1.5 px-3"
          >
            <Share2 className="w-3.5 h-3.5 text-sky-600" />
            <span>Graph View</span>
          </Link>

          <button
            onClick={() =>
              toggleSave({
                id: faculty.id,
                type: 'faculty',
                title: faculty.name,
                subtitle: faculty.designation || faculty.academic_rank || 'GIKI Faculty',
                link: `/faculty/${faculty.id}`,
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

      {/* Main Profile Card */}
      <div className="card p-6 sm:p-8 bg-white">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-16 h-16 rounded-2xl bg-slate-900 text-white flex items-center justify-center font-bold text-xl flex-shrink-0 shadow-sm">
              {faculty.name
                .split(' ')
                .map((n) => n[0])
                .slice(0, 2)
                .join('')}
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                {faculty.verified && (
                  <Badge variant="emerald" size="sm">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    <span>Verified Academic Member</span>
                  </Badge>
                )}
                {faculty.units &&
                  faculty.units.map((u) => (
                    <Badge key={u} variant="default" size="sm">
                      {u}
                    </Badge>
                  ))}
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                {faculty.name}
              </h1>

              <p className="text-sm font-semibold text-slate-600 mt-1">
                {faculty.designation || faculty.academic_rank || 'Faculty Member'}
              </p>

              {faculty.administrative_role && (
                <p className="text-xs text-sky-700 font-medium mt-0.5">
                  Role: {faculty.administrative_role}
                </p>
              )}
            </div>
          </div>

          {/* Quick Contact & Links */}
          <div className="flex flex-col sm:items-end gap-2 text-xs">
            {faculty.email && (
              <a
                href={`mailto:${faculty.email}`}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
              >
                <Mail className="w-3.5 h-3.5 text-slate-400" />
                <span>{faculty.email}</span>
              </a>
            )}

            {faculty.profile_url && (
              <a
                href={faculty.profile_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 transition-colors"
              >
                <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                <span>Institutional Profile</span>
              </a>
            )}
          </div>
        </div>

        {/* Qualifications Bar */}
        {faculty.qualifications && faculty.qualifications.length > 0 && (
          <div className="mt-6 pt-5 border-t border-slate-100">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <GraduationCap className="w-3.5 h-3.5 text-slate-500" />
              <span>Academic Credentials & Qualifications</span>
            </h3>
            <div className="flex flex-wrap gap-2">
              {faculty.qualifications.map((q, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-50 text-slate-700 border border-slate-200/80"
                >
                  {q}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Grid: Research Areas & Publications */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Publications */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-sky-600" />
                <h2 className="text-base font-bold text-slate-900">
                  Scholarly Publications ({publications.length})
                </h2>
              </div>
            </div>

            {publications.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {publications.map((pub, idx) => (
                  <div key={pub.id || idx} className="py-3.5 first:pt-0 last:pb-0">
                    <h3 className="text-sm font-semibold text-slate-800 leading-snug">
                      {pub.title || pub.citation}
                    </h3>

                    {/* Metadata line */}
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 mt-1.5">
                      {pub.year && (
                        <span className="font-semibold text-slate-700">{pub.year}</span>
                      )}
                      {pub.venue && <span className="italic">{pub.venue}</span>}
                      {pub.doi && (
                        <a
                          href={`https://doi.org/${pub.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sky-600 hover:underline font-mono text-[11px]"
                        >
                          DOI: {pub.doi}
                        </a>
                      )}
                    </div>

                    {pub.authors && pub.authors.length > 0 && (
                      <p className="text-[11px] text-slate-400 mt-1">
                        Authors: {pub.authors.join(', ')}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400 py-3">
                No indexed publication citations currently linked in this repository snapshot.
              </p>
            )}
          </div>
        </div>

        {/* Right Col: Research Interests & Areas */}
        <div className="space-y-6">
          {/* Research Areas */}
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-3 border-b border-slate-100 pb-3">
              <FlaskConical className="w-4 h-4 text-purple-600" />
              <h2 className="text-base font-bold text-slate-900">Research Focus</h2>
            </div>

            {researchAreas.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {researchAreas.map((ra) => (
                  <Link
                    key={ra.id}
                    to={`/research?search=${encodeURIComponent(ra.name)}`}
                    className="px-2.5 py-1 rounded-md text-xs font-medium bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200/80 transition-colors"
                  >
                    {ra.name}
                  </Link>
                ))}
              </div>
            ) : faculty.research_interests && faculty.research_interests.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {faculty.research_interests.map((interest, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-700"
                  >
                    {interest}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">
                No explicit research interests documented for this profile.
              </p>
            )}
          </div>

          {/* Affiliated Unit info */}
          {faculty.units && faculty.units.length > 0 && (
            <div className="card p-6">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                Departmental Affiliation
              </h3>
              <p className="text-sm font-semibold text-slate-800">{faculty.units.join(' • ')}</p>
              <Link
                to={`/faculty?unit=${encodeURIComponent(faculty.units[0].toLowerCase())}`}
                className="mt-3 text-xs font-semibold text-sky-700 hover:text-sky-800 inline-block"
              >
                View all faculty in {faculty.units[0]} →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FacultyDetailPage;
