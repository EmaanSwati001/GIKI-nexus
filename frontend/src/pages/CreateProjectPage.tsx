import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Briefcase,
  ShieldAlert,
  Copy,
  Check,
  CheckCircle2,
  Users,
} from 'lucide-react';
import { createProject } from '../services/api';
import { useSaved } from '../context/SavedContext';

export const CreateProjectPage: React.FC = () => {
  const navigate = useNavigate();
  const { storedKeys, saveKey } = useSaved();

  // Pre-fill owner_id if student profile key is saved
  const existingProfileKey = storedKeys.find((k) => k.entityType === 'profile');
  const [ownerId, setOwnerId] = useState(existingProfileKey?.entityId || '');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [domainsStr, setDomainsStr] = useState('');
  const [skillsStr, setSkillsStr] = useState('');
  const [rolesStr, setRolesStr] = useState('');
  const [membersNeeded, setMembersNeeded] = useState<number>(2);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdProject, setCreatedProject] = useState<{
    id: string;
    title: string;
    ownership_key: string;
  } | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const parseList = (str: string) =>
      str
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

    try {
      const payload = {
        owner_id: ownerId.trim(),
        title: title.trim(),
        description: description.trim(),
        domains: parseList(domainsStr),
        required_skills: parseList(skillsStr),
        preferred_roles: parseList(rolesStr),
        additional_members_needed: membersNeeded,
      };

      const result = await createProject(payload);
      setCreatedProject({
        id: result.id,
        title: result.title,
        ownership_key: result.ownership_key,
      });

      // Save key in localStorage via context
      saveKey({
        entityId: result.id,
        entityType: 'project',
        title: result.title,
        key: result.ownership_key,
        createdAt: new Date().toISOString(),
      });
    } catch (err: any) {
      setError(err.message || 'Failed to create recruitment project');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopy = () => {
    if (createdProject) {
      navigator.clipboard.writeText(createdProject.ownership_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto pb-12">
      {/* Back button */}
      <div>
        <button
          onClick={() => navigate('/projects')}
          className="btn-ghost text-xs py-1 px-2.5 -ml-2.5 text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Projects</span>
        </button>
      </div>

      {/* Header */}
      <div className="border-b border-slate-200/80 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Post Collaboration Project
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Recruit student teammates for final-year design capstones, research ventures, or hackathons
        </p>
      </div>

      {/* Security Architecture Notice */}
      <div className="p-4 rounded-xl bg-amber-50 border border-amber-200/80 text-xs text-amber-900 space-y-1">
        <div className="flex items-center gap-1.5 font-bold">
          <ShieldAlert className="w-4 h-4 text-amber-600" />
          <span>Project Ownership & Verification Notice</span>
        </div>
        <p className="leading-relaxed text-amber-800">
          Creating a project requires a valid Profile ID as project owner. You will receive an exclusive
          128-bit Project Ownership Key. You will need this key to view applicant applications, approve
          teammates, and close recruitment.
        </p>
      </div>

      {/* Success View with Ownership Key */}
      {createdProject ? (
        <div className="card p-6 sm:p-8 border-emerald-300 bg-white space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center flex-shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Project Published Successfully!</h2>
              <p className="text-xs text-slate-500">
                Project ID: <span className="font-mono font-bold text-slate-800">{createdProject.id}</span>
              </p>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900 text-white space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Your Secret Project Ownership Key
              </span>
              <button
                onClick={handleCopy}
                className="btn-secondary text-xs py-1 px-2.5 bg-slate-800 border-slate-700 text-slate-200 hover:bg-slate-700"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied!' : 'Copy Key'}</span>
              </button>
            </div>

            <p className="font-mono text-sm sm:text-base text-sky-400 break-all select-all font-semibold">
              {createdProject.ownership_key}
            </p>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              We have automatically saved this key in your browser's local storage (My Space). Keep a copy in
              a safe place; you will need it to approve teammate interest requests.
            </p>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <Link to={`/projects/${createdProject.id}`} className="btn-primary text-xs py-2 px-4">
              View Project Workspace
            </Link>
          </div>
        </div>
      ) : (
        /* Form View */
        <form onSubmit={handleSubmit} className="card p-6 sm:p-8 bg-white space-y-6">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Your Student Profile ID <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={ownerId}
                onChange={(e) => setOwnerId(e.target.value)}
                placeholder="prof_..."
                className="input-field text-xs py-2 font-mono"
              />
              <span className="text-[10px] text-slate-400 mt-0.5 block">
                Must be an active student profile ID.{' '}
                <Link to="/profiles/new" className="text-sky-600 hover:underline">
                  Create a profile first
                </Link>{' '}
                if you don't have one.
              </span>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Project Title <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Autonomous Campus Delivery Rover"
                className="input-field text-xs py-2"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Project Description & Goals <span className="text-rose-500">*</span>
              </label>
              <textarea
                required
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the problem, technologies used, planned milestones, and what your team aims to achieve..."
                className="input-field text-xs py-2"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Domains / Fields (comma-separated)
                </label>
                <input
                  type="text"
                  value={domainsStr}
                  onChange={(e) => setDomainsStr(e.target.value)}
                  placeholder="Robotics, Embedded Systems, Computer Vision..."
                  className="input-field text-xs py-2"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Additional Teammates Needed <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  required
                  min={1}
                  max={10}
                  value={membersNeeded}
                  onChange={(e) => setMembersNeeded(parseInt(e.target.value) || 1)}
                  className="input-field text-xs py-2"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Required Technical Skills (comma-separated)
                </label>
                <input
                  type="text"
                  value={skillsStr}
                  onChange={(e) => setSkillsStr(e.target.value)}
                  placeholder="ROS2, C++, PyTorch, PCB Design..."
                  className="input-field text-xs py-2"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Preferred Team Roles (comma-separated)
                </label>
                <input
                  type="text"
                  value={rolesStr}
                  onChange={(e) => setRolesStr(e.target.value)}
                  placeholder="Hardware Lead, Perception Engineer..."
                  className="input-field text-xs py-2"
                />
              </div>
            </div>
          </div>

          {error && <p className="text-xs text-rose-600">{error}</p>}

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => navigate('/projects')}
              className="btn-secondary text-xs py-2 px-4"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary text-xs py-2 px-5 disabled:opacity-50"
            >
              {submitting ? 'Creating Project...' : 'Publish Project'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default CreateProjectPage;
