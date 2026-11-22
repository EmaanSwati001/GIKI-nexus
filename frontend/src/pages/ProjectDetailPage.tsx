import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Briefcase,
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Send,
  Key,
  ShieldAlert,
  ChevronRight,
  Mail,
  UserCheck,
  Award,
} from 'lucide-react';
import {
  getProject,
  getProjectRecommendations,
  expressInterest,
  getProjectInterests,
  respondToInterest,
  closeProject,
} from '../services/api';
import {
  Project,
  CandidateRecommendation,
  ProjectInterest,
  InterestStatus,
} from '../types';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorMessage from '../components/ui/ErrorMessage';
import { useSaved } from '../context/SavedContext';

export const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { storedKeys } = useSaved();

  const [project, setProject] = useState<Project | null>(null);
  const [candidates, setCandidates] = useState<CandidateRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Interest Modal
  const [interestModalOpen, setInterestModalOpen] = useState(false);
  const [myProfileId, setMyProfileId] = useState('');
  const [proposedRole, setProposedRole] = useState('');
  const [interestMessage, setInterestMessage] = useState('');
  const [interestSubmitting, setInterestSubmitting] = useState(false);
  const [interestSuccess, setInterestSuccess] = useState<string | null>(null);
  const [interestError, setInterestError] = useState<string | null>(null);

  // Owner Workspace
  const matchedKey = storedKeys.find((k) => k.entityId === projectId)?.key || '';
  const [ownerKey, setOwnerKey] = useState<string>(matchedKey);
  const [interestsList, setInterestsList] = useState<ProjectInterest[]>([]);
  const [ownerLoading, setOwnerLoading] = useState(false);
  const [ownerError, setOwnerError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    setError(null);

    Promise.all([
      getProject(projectId),
      getProjectRecommendations(projectId).catch(() => []),
    ])
      .then(([proj, cands]) => {
        setProject(proj);
        setCandidates(cands);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load project details');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [projectId]);

  // Load applicant interests if ownerKey is present
  const loadInterests = async (key: string) => {
    if (!projectId || !key.trim()) return;
    setOwnerLoading(true);
    setOwnerError(null);
    try {
      const list = await getProjectInterests(projectId, key.trim());
      setInterestsList(list);
    } catch (err: any) {
      setOwnerError(err.message || 'Failed to load applicant interests');
    } finally {
      setOwnerLoading(false);
    }
  };

  useEffect(() => {
    if (ownerKey) {
      loadInterests(ownerKey);
    }
  }, [ownerKey, projectId]);

  const handleExpressInterest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId || !myProfileId.trim()) return;

    setInterestSubmitting(true);
    setInterestError(null);
    try {
      await expressInterest(projectId, {
        profile_id: myProfileId.trim(),
        proposed_role: proposedRole.trim() || undefined,
        message: interestMessage.trim() || undefined,
      });
      setInterestSuccess(
        'Interest expression submitted successfully! The project owner will review your application.'
      );
    } catch (err: any) {
      setInterestError(err.message || 'Failed to submit expression of interest');
    } finally {
      setInterestSubmitting(false);
    }
  };

  const handleRespond = async (interestId: string, action: InterestStatus) => {
    if (!ownerKey) return;
    try {
      await respondToInterest(interestId, action, ownerKey);
      loadInterests(ownerKey);
    } catch (err: any) {
      alert(`Action failed: ${err.message}`);
    }
  };

  const handleCloseProject = async () => {
    if (!projectId || !ownerKey) return;
    if (!confirm('Are you sure you want to close recruitment for this project?')) return;
    try {
      const updated = await closeProject(projectId, ownerKey);
      setProject(updated);
      alert('Recruitment closed successfully.');
    } catch (err: any) {
      alert(`Failed to close project: ${err.message}`);
    }
  };

  if (loading) {
    return <LoadingSpinner size="lg" message="Loading project details..." />;
  }

  if (error || !project) {
    return (
      <div className="space-y-4">
        <button onClick={() => navigate('/projects')} className="btn-ghost text-xs">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Projects
        </button>
        <ErrorMessage
          message={error || `Project '${projectId}' not found.`}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/projects')}
          className="btn-ghost text-xs py-1 px-2.5 -ml-2.5 text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Projects</span>
        </button>

        {project.status === 'OPEN' && (
          <button
            onClick={() => {
              setInterestSuccess(null);
              setInterestError(null);
              setInterestModalOpen(true);
            }}
            className="btn-primary text-xs py-1.5 px-3.5 flex items-center gap-1.5"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Express Interest</span>
          </button>
        )}
      </div>

      {/* Main Project Header Card */}
      <div className="card p-6 sm:p-8 bg-white">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Badge
            variant={
              project.status === 'OPEN'
                ? 'emerald'
                : project.status === 'IN_PROGRESS'
                ? 'amber'
                : 'default'
            }
            size="md"
          >
            {project.status === 'OPEN' ? 'Recruiting Teammates' : project.status.replace('_', ' ')}
          </Badge>

          {project.additional_members_needed > 0 && (
            <span className="text-xs font-semibold text-sky-700 bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-100">
              {project.additional_members_needed} Member Spot
              {project.additional_members_needed !== 1 ? 's' : ''} Open
            </span>
          )}

          {project.domains &&
            project.domains.map((d) => (
              <Badge key={d} variant="teal" size="md">
                {d}
              </Badge>
            ))}
        </div>

        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          {project.title}
        </h1>

        <div className="mt-4 prose prose-slate max-w-none text-sm text-slate-600 leading-relaxed whitespace-pre-line">
          {project.description}
        </div>

        {/* Requirements Grid */}
        <div className="mt-6 pt-5 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
              Required Technical Skills
            </span>
            <div className="flex flex-wrap gap-1.5">
              {project.required_skills && project.required_skills.length > 0 ? (
                project.required_skills.map((s) => (
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
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
              Preferred Project Roles
            </span>
            <div className="flex flex-wrap gap-1.5">
              {project.preferred_roles && project.preferred_roles.length > 0 ? (
                project.preferred_roles.map((r) => (
                  <span
                    key={r}
                    className="px-2.5 py-1 rounded-md text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200/60"
                  >
                    {r}
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-400">Open to flexible roles</span>
              )}
            </div>
          </div>
        </div>

        {/* Current Team Members */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2.5 flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-slate-500" />
            <span>Current Team Roster ({project.members?.length || 0})</span>
          </span>

          <div className="flex flex-wrap gap-2">
            {project.members && project.members.length > 0 ? (
              project.members.map((m) => (
                <div
                  key={m.profile_id}
                  className="px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 flex items-center gap-2"
                >
                  <div className="w-5 h-5 rounded-full bg-slate-800 text-white flex items-center justify-center font-bold text-[10px]">
                    {m.display_name[0]}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs font-semibold text-slate-800">{m.display_name}</span>
                    <span className="text-[10px] text-slate-400">
                      {m.role || 'Contributor'} • {m.programme}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <span className="text-xs text-slate-400">Sole project initiator.</span>
            )}
          </div>
        </div>
      </div>

      {/* Explainable Candidate Recommendations */}
      {project.status === 'OPEN' && (
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4 border-b border-slate-100 pb-3">
            <div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-sky-600" />
                <h2 className="text-base font-bold text-slate-900">
                  Recommended Student Collaborators ({candidates.length})
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Transparent 5-factor scoring: Skills (35%), Domain (25%), Roles (15%), Availability
                (15%), Experience (10%)
              </p>
            </div>
          </div>

          {candidates.length > 0 ? (
            <div className="space-y-3">
              {candidates.map((cand) => (
                <div
                  key={cand.profile_id}
                  className="p-4 rounded-xl border border-slate-200 hover:border-slate-300 hover:bg-slate-50/40 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-bold text-slate-900">
                        {cand.is_anonymous ? 'Anonymous Student' : cand.display_name}
                      </span>
                      <Badge variant="default" size="sm">
                        {cand.programme} (Yr {cand.academic_year})
                      </Badge>
                      <Badge variant="teal" size="sm">
                        {cand.availability}
                      </Badge>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed mt-1">
                      {cand.explanation}
                    </p>

                    {/* Breakdown bars */}
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-[10px] text-slate-400">
                      <span>Skills: {cand.score_breakdown.skills_score}%</span>
                      <span>•</span>
                      <span>Domain: {cand.score_breakdown.interests_score}%</span>
                      <span>•</span>
                      <span>Role: {cand.score_breakdown.role_score}%</span>
                      <span>•</span>
                      <span>Avail: {cand.score_breakdown.availability_score}%</span>
                    </div>
                  </div>

                  <div className="flex md:flex-col items-center md:items-end justify-between gap-2 flex-shrink-0">
                    <div className="text-center md:text-right">
                      <div className="text-xl font-extrabold text-sky-700">
                        {cand.overall_score}%
                      </div>
                      <span className="text-[10px] text-slate-400 font-semibold uppercase">
                        Match Score
                      </span>
                    </div>

                    <Link
                      to={`/profiles/${cand.profile_id}`}
                      className="btn-secondary text-xs py-1 px-2.5"
                    >
                      View Profile
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 py-3">
              No matching discoverable student profiles meet the skill and domain criteria for this post yet.
            </p>
          )}
        </div>
      )}

      {/* Project Owner Management Workspace */}
      <div className="card p-6 border-slate-300/80 bg-slate-50/60">
        <div className="flex items-center justify-between mb-4 border-b border-slate-200/60 pb-3">
          <div className="flex items-center gap-2">
            <Key className="w-4 h-4 text-slate-700" />
            <h2 className="text-base font-bold text-slate-900">Project Owner Workspace</h2>
          </div>
          {project.status === 'OPEN' && ownerKey && (
            <button
              onClick={handleCloseProject}
              className="btn-secondary text-xs py-1 px-2.5 text-rose-700 border-rose-200 hover:bg-rose-50"
            >
              Close Recruitment
            </button>
          )}
        </div>

        <p className="text-xs text-slate-500 mb-3">
          Enter your 128-bit Ownership Key issued at project creation to review incoming collaboration
          interests and approve team members.
        </p>

        <div className="flex gap-2 max-w-md">
          <input
            type="password"
            value={ownerKey}
            onChange={(e) => setOwnerKey(e.target.value)}
            placeholder="Enter X-Ownership-Key..."
            className="input-field text-xs py-1.5 font-mono"
          />
          <button
            onClick={() => loadInterests(ownerKey)}
            className="btn-primary text-xs py-1.5 px-3 flex-shrink-0"
          >
            Authenticate
          </button>
        </div>

        {ownerError && <p className="text-xs text-rose-600 mt-2">{ownerError}</p>}

        {/* Incoming Applicants List */}
        {ownerKey && (
          <div className="mt-5 space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Pending Collaboration Requests ({interestsList.length})
            </h3>

            {ownerLoading ? (
              <LoadingSpinner size="sm" message="Loading applicants..." />
            ) : interestsList.length > 0 ? (
              <div className="space-y-2.5">
                {interestsList.map((interest) => (
                  <div
                    key={interest.id}
                    className="p-3.5 rounded-lg bg-white border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-900">
                          {interest.requester_name || 'Student Applicant'}
                        </span>
                        {interest.requester_programme && (
                          <Badge variant="default" size="sm">
                            {interest.requester_programme}
                          </Badge>
                        )}
                        <Badge
                          variant={
                            interest.status === 'APPROVED'
                              ? 'emerald'
                              : interest.status === 'REJECTED'
                              ? 'rose'
                              : 'amber'
                          }
                          size="sm"
                        >
                          {interest.status}
                        </Badge>
                      </div>

                      {interest.proposed_role && (
                        <p className="text-xs text-slate-600 mt-1">
                          <strong>Proposed Role:</strong> {interest.proposed_role}
                        </p>
                      )}

                      {interest.message && (
                        <p className="text-xs text-slate-500 mt-0.5 italic">
                          "{interest.message}"
                        </p>
                      )}

                      {/* Revealed Contact Email upon approval */}
                      {interest.shared_contact_email && (
                        <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 text-xs font-medium border border-emerald-200">
                          <Mail className="w-3.5 h-3.5" />
                          <span>Contact Email: {interest.shared_contact_email}</span>
                        </div>
                      )}
                    </div>

                    {interest.status === 'PENDING' && (
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          onClick={() => handleRespond(interest.id, 'APPROVED')}
                          className="btn-primary text-xs py-1 px-2.5 bg-emerald-700 hover:bg-emerald-800"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleRespond(interest.id, 'REJECTED')}
                          className="btn-secondary text-xs py-1 px-2.5 text-rose-700 hover:bg-rose-50"
                        >
                          Reject
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-400">
                No students have expressed interest in this project yet.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Express Interest Modal */}
      <Modal
        isOpen={interestModalOpen}
        onClose={() => setInterestModalOpen(false)}
        title="Express Collaboration Interest"
        subtitle={`Apply to collaborate on "${project.title}"`}
      >
        {interestSuccess ? (
          <div className="space-y-4 py-2">
            <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
              <span>{interestSuccess}</span>
            </div>
            <button
              onClick={() => setInterestModalOpen(false)}
              className="btn-secondary text-xs w-full py-2"
            >
              Close
            </button>
          </div>
        ) : (
          <form onSubmit={handleExpressInterest} className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Your Profile ID <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={myProfileId}
                onChange={(e) => setMyProfileId(e.target.value)}
                placeholder="Enter your student profile ID (e.g. prof_...)"
                className="input-field text-xs py-2 font-mono"
              />
              <span className="text-[11px] text-slate-400 mt-0.5 block">
                Don't have a profile yet?{' '}
                <Link to="/profiles/new" className="text-sky-600 hover:underline">
                  Create one here
                </Link>
                .
              </span>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Proposed Project Role
              </label>
              <input
                type="text"
                value={proposedRole}
                onChange={(e) => setProposedRole(e.target.value)}
                placeholder="e.g. Frontend Engineer, ML Researcher..."
                className="input-field text-xs py-2"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Brief Introduction / Note
              </label>
              <textarea
                rows={3}
                value={interestMessage}
                onChange={(e) => setInterestMessage(e.target.value)}
                placeholder="Describe your motivation and what skills you can contribute..."
                className="input-field text-xs py-2"
              />
            </div>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-500 leading-relaxed">
              <strong>Privacy Protection:</strong> Your institutional email is never disclosed
              until the project owner explicitly approves your interest request.
            </div>

            {interestError && <p className="text-xs text-rose-600">{interestError}</p>}

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setInterestModalOpen(false)}
                className="btn-secondary text-xs py-1.5 px-3"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={interestSubmitting}
                className="btn-primary text-xs py-1.5 px-4 disabled:opacity-50"
              >
                {interestSubmitting ? 'Submitting...' : 'Submit Expression'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};

export default ProjectDetailPage;
