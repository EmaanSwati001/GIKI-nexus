import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  UserCheck,
  ShieldAlert,
  Copy,
  Check,
  CheckCircle2,
  Lock,
  Sparkles,
} from 'lucide-react';
import { createProfile } from '../services/api';
import { useSaved } from '../context/SavedContext';

export const CreateProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const { saveKey } = useSaved();

  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [programme, setProgramme] = useState('Computer Science');
  const [academicYear, setAcademicYear] = useState<number>(3);
  const [skillsStr, setSkillsStr] = useState('');
  const [interestsStr, setInterestsStr] = useState('');
  const [domainsStr, setDomainsStr] = useState('');
  const [rolesStr, setRolesStr] = useState('');
  const [availability, setAvailability] = useState('10-15 hrs/week');
  const [experience, setExperience] = useState('');
  const [bio, setBio] = useState('');
  const [projectIdeas, setProjectIdeas] = useState('');
  const [visibility, setVisibility] = useState('PUBLIC');
  const [contactPref, setContactPref] = useState('UPON_REQUEST');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdProfile, setCreatedProfile] = useState<{
    id: string;
    display_name: string;
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
        display_name: displayName.trim(),
        email: email.trim(),
        programme: programme.trim(),
        academic_year: academicYear,
        technical_skills: parseList(skillsStr),
        research_interests: parseList(interestsStr),
        preferred_domains: parseList(domainsStr),
        preferred_roles: parseList(rolesStr),
        availability: availability.trim() || 'flexible',
        previous_experience: experience.trim() || undefined,
        bio: bio.trim() || undefined,
        project_ideas: projectIdeas.trim() || undefined,
        visibility,
        contact_preference: contactPref,
      };

      const result = await createProfile(payload);
      setCreatedProfile({
        id: result.id,
        display_name: result.display_name,
        ownership_key: result.ownership_key,
      });

      // Save key in localStorage via context
      saveKey({
        entityId: result.id,
        entityType: 'profile',
        title: result.display_name,
        key: result.ownership_key,
        createdAt: new Date().toISOString(),
      });
    } catch (err: any) {
      setError(err.message || 'Failed to create student profile');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopy = () => {
    if (createdProfile) {
      navigator.clipboard.writeText(createdProfile.ownership_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto pb-12">
      {/* Back button */}
      <div>
        <button
          onClick={() => navigate('/profiles')}
          className="btn-ghost text-xs py-1 px-2.5 -ml-2.5 text-slate-500 hover:text-slate-800"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Students Directory</span>
        </button>
      </div>

      {/* Header */}
      <div className="border-b border-slate-200/80 pb-4">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Create Student Collaborator Profile
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          List your skills and interests voluntarily to match with student project teams
        </p>
      </div>

      {/* Prototype Auth Notice */}
      <div className="p-4 rounded-xl bg-amber-50 border border-amber-200/80 text-xs text-amber-900 space-y-1">
        <div className="flex items-center gap-1.5 font-bold">
          <ShieldAlert className="w-4 h-4 text-amber-600" />
          <span>Prototype Security Architecture Notice</span>
        </div>
        <p className="leading-relaxed text-amber-800">
          GIKI Nexus generates a cryptographically secure 128-bit Ownership Key for profile management.
          Save this key! It is required to update or deactivate your profile. This is an institutional prototype,
          not full single sign-on authentication.
        </p>
      </div>

      {/* Success View with Ownership Key */}
      {createdProfile ? (
        <div className="card p-6 sm:p-8 border-emerald-300 bg-white space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center flex-shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Profile Created Successfully!</h2>
              <p className="text-xs text-slate-500">
                Profile ID: <span className="font-mono font-bold text-slate-800">{createdProfile.id}</span>
              </p>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900 text-white space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Your Secret Ownership Key
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
              {createdProfile.ownership_key}
            </p>

            <p className="text-[11px] text-slate-400 leading-relaxed">
              We have automatically saved this key in your browser's local storage (My Space). Keep a copy in
              a safe place as it is required for any future profile updates.
            </p>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <Link to={`/profiles/${createdProfile.id}`} className="btn-primary text-xs py-2 px-4">
              View Your Profile
            </Link>
          </div>
        </div>
      ) : (
        /* Form View */
        <form onSubmit={handleSubmit} className="card p-6 sm:p-8 bg-white space-y-6">
          {/* Section 1: Basic Information */}
          <div className="space-y-4">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2">
              1. Basic Information
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Full Display Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="e.g. Sarah Khan"
                  className="input-field text-xs py-2"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Institutional Email <span className="text-rose-500">*</span>
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="u2023123@giki.edu.pk"
                  className="input-field text-xs py-2"
                />
                <span className="text-[10px] text-slate-400 mt-0.5 block">
                  Never displayed publicly; shared only upon your mutual approval.
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Degree Programme <span className="text-rose-500">*</span>
                </label>
                <select
                  value={programme}
                  onChange={(e) => setProgramme(e.target.value)}
                  className="input-field text-xs py-2 cursor-pointer"
                >
                  <option value="Computer Science">BS Computer Science</option>
                  <option value="Artificial Intelligence">BS Artificial Intelligence</option>
                  <option value="Software Engineering">BS Software Engineering</option>
                  <option value="Data Science">BS Data Science</option>
                  <option value="Cyber Security">BS Cyber Security</option>
                  <option value="Electrical Engineering">BS Electrical Engineering</option>
                  <option value="Mechanical Engineering">BS Mechanical Engineering</option>
                  <option value="Civil Engineering">BS Civil Engineering</option>
                  <option value="Chemical Engineering">BS Chemical Engineering</option>
                  <option value="Materials Engineering">BS Materials Engineering</option>
                  <option value="Engineering Sciences">BS Engineering Sciences</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Academic Year <span className="text-rose-500">*</span>
                </label>
                <select
                  value={academicYear}
                  onChange={(e) => setAcademicYear(parseInt(e.target.value))}
                  className="input-field text-xs py-2 cursor-pointer"
                >
                  <option value={1}>1st Year (Freshman)</option>
                  <option value={2}>2nd Year (Sophomore)</option>
                  <option value={3}>3rd Year (Junior)</option>
                  <option value={4}>4th Year (Senior / Capstone)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Section 2: Technical Skills & Interests */}
          <div className="space-y-4">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2">
              2. Skills & Project Domains
            </h2>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Technical Skills (comma-separated)
              </label>
              <input
                type="text"
                value={skillsStr}
                onChange={(e) => setSkillsStr(e.target.value)}
                placeholder="Python, PyTorch, React, Embedded C, ROS2, Figma..."
                className="input-field text-xs py-2"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Preferred Project Domains
                </label>
                <input
                  type="text"
                  value={domainsStr}
                  onChange={(e) => setDomainsStr(e.target.value)}
                  placeholder="Machine Learning, IoT, Web, Robotics..."
                  className="input-field text-xs py-2"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Preferred Roles
                </label>
                <input
                  type="text"
                  value={rolesStr}
                  onChange={(e) => setRolesStr(e.target.value)}
                  placeholder="Backend Lead, ML Engineer, UI Designer..."
                  className="input-field text-xs py-2"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Research Interests
                </label>
                <input
                  type="text"
                  value={interestsStr}
                  onChange={(e) => setInterestsStr(e.target.value)}
                  placeholder="Computer Vision, Renewable Energy..."
                  className="input-field text-xs py-2"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Weekly Availability
                </label>
                <input
                  type="text"
                  value={availability}
                  onChange={(e) => setAvailability(e.target.value)}
                  placeholder="e.g. 10-15 hrs/week or Flexible"
                  className="input-field text-xs py-2"
                />
              </div>
            </div>
          </div>

          {/* Section 3: Biography & Project Concepts */}
          <div className="space-y-4">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2">
              3. About & Experience
            </h2>

            <div>
              <label className="text-xs font-bold text-slate-700 block mb-1">
                Short Biography / Motivation
              </label>
              <textarea
                rows={3}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Brief summary of your academic background and interests..."
                className="input-field text-xs py-2"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Previous Project Experience
                </label>
                <textarea
                  rows={2}
                  value={experience}
                  onChange={(e) => setExperience(e.target.value)}
                  placeholder="Key past projects, hackathons, or internships..."
                  className="input-field text-xs py-2"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Project Ideas You Want to Build
                </label>
                <textarea
                  rows={2}
                  value={projectIdeas}
                  onChange={(e) => setProjectIdeas(e.target.value)}
                  placeholder="Any proposed capstone or startup concepts..."
                  className="input-field text-xs py-2"
                />
              </div>
            </div>
          </div>

          {/* Section 4: Privacy Settings */}
          <div className="space-y-4">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-2 flex items-center gap-2">
              <Lock className="w-3.5 h-3.5 text-slate-500" />
              <span>4. Privacy & Contact Sharing Controls</span>
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Profile Visibility
                </label>
                <select
                  value={visibility}
                  onChange={(e) => setVisibility(e.target.value)}
                  className="input-field text-xs py-2 cursor-pointer"
                >
                  <option value="PUBLIC">PUBLIC (Searchable with name & bio)</option>
                  <option value="ANONYMOUS">ANONYMOUS (Masked display name & bio)</option>
                  <option value="UNLISTED">UNLISTED (Excluded from discovery)</option>
                </select>
                <span className="text-[10px] text-slate-400 mt-0.5 block">
                  You can change visibility at any time using your key.
                </span>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">
                  Email Sharing Preference
                </label>
                <select
                  value={contactPref}
                  onChange={(e) => setContactPref(e.target.value)}
                  className="input-field text-xs py-2 cursor-pointer"
                >
                  <option value="UPON_REQUEST">UPON REQUEST (Recommended — consent required)</option>
                  <option value="ALWAYS">ALWAYS (Share when interest approved)</option>
                  <option value="NEVER">NEVER (Do not disclose contact email)</option>
                </select>
              </div>
            </div>
          </div>

          {error && <p className="text-xs text-rose-600">{error}</p>}

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => navigate('/profiles')}
              className="btn-secondary text-xs py-2 px-4"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary text-xs py-2 px-5 disabled:opacity-50"
            >
              {submitting ? 'Creating Profile...' : 'Publish Profile'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default CreateProfilePage;
