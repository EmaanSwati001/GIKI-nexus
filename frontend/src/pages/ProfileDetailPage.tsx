import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  UserCheck,
  ShieldCheck,
  Sparkles,
  Briefcase,
  Key,
  ChevronRight,
  Clock,
  Layers,
  Lock,
} from 'lucide-react';
import {
  getProfile,
  getStudentProjectRecommendations,
  updateProfileVisibility,
  deactivateProfile,
} from '../services/api';
import { StudentProfile, ProjectRecommendation } from '../types';
import Badge from '../components/ui/Badge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import { useSaved } from '../context/SavedContext';

export const ProfileDetailPage: React.FC = () => {
  const { profileId } = useParams<{ profileId: string }>();
  const navigate = useNavigate();
  const { storedKeys } = useSaved();

  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [recommendations, setRecommendations] = useState<ProjectRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Owner controls
  const matchedKey = storedKeys.find((k) => k.entityId === profileId)?.key || '';
  const [ownerKey, setOwnerKey] = useState<string>(matchedKey);
  const [visibility, setVisibility] = useState<string>('PUBLIC');
  const [ownerMsg, setOwnerMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!profileId) return;

    setLoading(true);
    setError(null);

    Promise.all([
      getProfile(profileId),
      getStudentProjectRecommendations(profileId).catch(() => []),
    ])
      .then(([prof, recs]) => {
        setProfile(prof);
        setVisibility(prof.visibility);
        setRecommendations(recs);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load student profile');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [profileId]);

  const handleUpdateVisibility = async () => {
    if (!profileId || !ownerKey) return;
    try {
      const updated = await updateProfileVisibility(profileId, visibility, ownerKey);
      setProfile(updated);
      setOwnerMsg('Profile visibility updated successfully.');
    } catch (err: any) {
      alert(`Update failed: ${err.message}`);
    }
  };

  const handleDeactivate = async () => {
    if (!profileId || !ownerKey) return;
    if (!confirm('Are you sure you want to deactivate your profile? It will be removed from discovery.')) return;
    try {
      await deactivateProfile(profileId, ownerKey);
      alert('Profile deactivated.');
      navigate('/profiles');
    } catch (err: any) {
      alert(`Deactivation failed: ${err.message}`);
    }
  };

  if (loading) {
    return <LoadingSpinner size="lg" message="Loading student profile..." />;
  }

  if (error || !profile) {
    return (
      <div className="space-y-4">
        <button onClick={() => navigate('/profiles')} className="btn-ghost text-xs">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Directory
        </button>
        <ErrorMessage
          message={error || `Profile '${profileId}' not found.`}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Top Back Nav */}
      <div>
        <button
          onClick={() => navigate('/profiles')}
          className="btn-ghost text-xs py-1 px-2.5 -ml-2.5 text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Students</span>
        </button>
      </div>

      {/* Main Profile Header Card */}
      <div className="card p-6 sm:p-8 bg-white">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-teal-800 text-white flex items-center justify-center font-bold text-lg flex-shrink-0">
              {profile.is_anonymous ? '?' : profile.display_name[0]}
            </div>

            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <Badge variant="default" size="sm">
                  {profile.programme}
                </Badge>
                <Badge variant="sky" size="sm">
                  Year {profile.academic_year}
                </Badge>
                {profile.is_anonymous && (
                  <Badge variant="amber" size="sm">
                    Anonymous Listing
                  </Badge>
                )}
                <Badge variant="teal" size="sm">
                  {profile.availability}
                </Badge>
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                {profile.is_anonymous ? 'Anonymous Student' : profile.display_name}
              </h1>

              <p className="text-xs text-slate-400 font-mono mt-1">ID: {profile.id}</p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600">
            <Lock className="w-3.5 h-3.5 text-slate-400" />
            <span>Email Protected by Consent Workflow</span>
          </div>
        </div>

        {/* Biography (if not anonymous) */}
        {!profile.is_anonymous && profile.bio && (
          <div className="mt-5 pt-4 border-t border-slate-100">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
              About & Background
            </h3>
            <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-line">
              {profile.bio}
            </p>
          </div>
        )}

        {/* Skills & Domains Grid */}
        <div className="mt-6 pt-5 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Technical Competencies
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {profile.technical_skills && profile.technical_skills.length > 0 ? (
                profile.technical_skills.map((s) => (
                  <span
                    key={s}
                    className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-100 text-slate-800"
                  >
                    {s}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-400">None specified</span>
              )}
            </div>
          </div>

          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
              Preferred Domains & Roles
            </h3>
            <div className="flex flex-wrap gap-1.5">
              {profile.preferred_roles &&
                profile.preferred_roles.map((r) => (
                  <Badge key={r} variant="amber" size="sm">
                    {r}
                  </Badge>
                ))}
              {profile.preferred_domains &&
                profile.preferred_domains.map((d) => (
                  <Badge key={d} variant="teal" size="sm">
                    {d}
                  </Badge>
                ))}
            </div>
          </div>
        </div>

        {/* Previous Experience / Project Ideas */}
        {(profile.previous_experience || profile.project_ideas) && (
          <div className="mt-6 pt-5 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-slate-600">
            {profile.previous_experience && (
              <div>
                <strong className="text-slate-800 block mb-1">Previous Experience:</strong>
                <p className="leading-relaxed">{profile.previous_experience}</p>
              </div>
            )}
            {profile.project_ideas && (
              <div>
                <strong className="text-slate-800 block mb-1">Project Concept Ideas:</strong>
                <p className="leading-relaxed">{profile.project_ideas}</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Recommended Projects for this student */}
      <div className="card p-6">
        <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
          <Sparkles className="w-4 h-4 text-sky-600" />
          <h2 className="text-base font-bold text-slate-900">
            Recommended Project Matches ({recommendations.length})
          </h2>
        </div>

        {recommendations.length > 0 ? (
          <div className="space-y-3">
            {recommendations.map((rec) => (
              <div
                key={rec.project_id}
                className="p-4 rounded-xl border border-slate-200 hover:border-slate-300 hover:bg-slate-50/40 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-bold text-slate-900">{rec.project_title}</span>
                    {rec.domains &&
                      rec.domains.map((d) => (
                        <Badge key={d} variant="teal" size="sm">
                          {d}
                        </Badge>
                      ))}
                  </div>

                  <p className="text-xs text-slate-600 mt-1">{rec.explanation}</p>
                </div>

                <div className="flex items-center gap-3 flex-shrink-0">
                  <div className="text-right">
                    <div className="text-lg font-extrabold text-sky-700">{rec.overall_score}%</div>
                    <span className="text-[10px] text-slate-400 uppercase font-semibold">Match</span>
                  </div>

                  <Link
                    to={`/projects/${rec.project_id}`}
                    className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
                  >
                    <span>View Project</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-400 py-3">
            No current open projects match this profile's combination of skills and domains.
          </p>
        )}
      </div>

      {/* Profile Owner Settings Box */}
      <div className="card p-6 border-slate-300/80 bg-slate-50/60">
        <div className="flex items-center gap-2 mb-3 border-b border-slate-200/60 pb-3">
          <Key className="w-4 h-4 text-slate-700" />
          <h2 className="text-base font-bold text-slate-900">Manage Profile (Owner Only)</h2>
        </div>

        <p className="text-xs text-slate-500 mb-3">
          Update your visibility preferences or deactivate your profile using your Ownership Key.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Ownership Key
            </label>
            <input
              type="password"
              value={ownerKey}
              onChange={(e) => setOwnerKey(e.target.value)}
              placeholder="X-Ownership-Key..."
              className="input-field text-xs py-1.5 font-mono"
            />
          </div>

          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
              Visibility Status
            </label>
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value)}
              className="input-field text-xs py-1.5 cursor-pointer"
            >
              <option value="PUBLIC">PUBLIC (Searchable with name)</option>
              <option value="ANONYMOUS">ANONYMOUS (Masked name/bio)</option>
              <option value="UNLISTED">UNLISTED (Excluded from discovery)</option>
            </select>
          </div>

          <div className="flex items-end gap-2">
            <button
              onClick={handleUpdateVisibility}
              className="btn-primary text-xs py-1.5 px-3"
            >
              Save Visibility
            </button>
            <button
              onClick={handleDeactivate}
              className="btn-secondary text-xs py-1.5 px-3 text-rose-700 hover:bg-rose-50"
            >
              Deactivate
            </button>
          </div>
        </div>

        {ownerMsg && <p className="text-xs text-emerald-700 font-medium mt-2">{ownerMsg}</p>}
      </div>
    </div>
  );
};

export default ProfileDetailPage;
