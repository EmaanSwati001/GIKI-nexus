import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Bookmark,
  Clock,
  Key,
  Trash2,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  BookOpen,
  Users,
  Briefcase,
  Copy,
  Check,
} from 'lucide-react';
import { useSaved, StoredKey } from '../context/SavedContext';
import Badge from '../components/ui/Badge';
import EmptyState from '../components/ui/EmptyState';

export const MySpacePage: React.FC = () => {
  const {
    savedItems,
    toggleSave,
    recentlyViewed,
    storedKeys,
    removeKey,
  } = useSaved();

  const [activeTab, setActiveTab] = useState<'saved' | 'recent' | 'keys'>('saved');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-200/80 pb-5">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
          <Bookmark className="w-3.5 h-3.5 text-sky-600" />
          <span>Personal Academic Space</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 mt-1">
          My Space
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Locally saved bookmarks, recently visited academic pages, and your secure prototype ownership keys
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200/80 pb-2 text-xs">
        <button
          onClick={() => setActiveTab('saved')}
          className={`px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
            activeTab === 'saved'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Bookmark className="w-3.5 h-3.5" />
          <span>Saved Items</span>
          <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-200">
            {savedItems.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('recent')}
          className={`px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
            activeTab === 'recent'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Clock className="w-3.5 h-3.5" />
          <span>Recently Viewed</span>
          <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-200">
            {recentlyViewed.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('keys')}
          className={`px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
            activeTab === 'keys'
              ? 'bg-slate-900 text-white'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
          }`}
        >
          <Key className="w-3.5 h-3.5" />
          <span>Ownership Keys</span>
          <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-200">
            {storedKeys.length}
          </span>
        </button>
      </div>

      {/* Saved Items Tab */}
      {activeTab === 'saved' && (
        <div className="space-y-3">
          {savedItems.length === 0 ? (
            <EmptyState
              icon={Bookmark}
              title="No saved items yet"
              description="Click the bookmark icon on any course, faculty profile, or project to save it here for fast access."
            />
          ) : (
            savedItems.map((item) => (
              <div
                key={item.id}
                className="card p-4 flex items-center justify-between gap-4 hover:border-slate-300 transition-all"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant={item.type === 'course' ? 'sky' : 'teal'} size="sm">
                      {item.type}
                    </Badge>
                    <span className="text-[10px] text-slate-400">
                      Saved {new Date(item.savedAt).toLocaleDateString()}
                    </span>
                  </div>

                  <Link
                    to={item.link}
                    className="text-sm font-bold text-slate-900 hover:text-sky-700 transition-colors block truncate"
                  >
                    {item.title}
                  </Link>

                  {item.subtitle && (
                    <p className="text-xs text-slate-500 mt-0.5 truncate">{item.subtitle}</p>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <Link to={item.link} className="btn-secondary text-xs py-1 px-2.5">
                    View
                  </Link>
                  <button
                    onClick={() => toggleSave(item)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg transition-colors"
                    title="Remove from saved"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Recently Viewed Tab */}
      {activeTab === 'recent' && (
        <div className="space-y-3">
          {recentlyViewed.length === 0 ? (
            <EmptyState
              icon={Clock}
              title="No recently viewed pages"
              description="Pages you visit will automatically appear here for easy history tracking."
            />
          ) : (
            recentlyViewed.map((item) => (
              <Link
                key={item.id}
                to={item.link}
                className="card card-hover p-4 flex items-center justify-between gap-4 block"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant={item.type === 'course' ? 'sky' : 'teal'} size="sm">
                      {item.type}
                    </Badge>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-900 truncate">{item.title}</h4>
                  {item.subtitle && (
                    <p className="text-xs text-slate-500 mt-0.5 truncate">{item.subtitle}</p>
                  )}
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400" />
              </Link>
            ))
          )}
        </div>
      )}

      {/* Ownership Keys Tab */}
      {activeTab === 'keys' && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-700 space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-slate-900">
              <Key className="w-3.5 h-3.5 text-slate-700" />
              <span>Prototype Key Vault</span>
            </div>
            <p className="leading-relaxed">
              These 128-bit keys were issued when you published student profiles or projects. They are stored
              securely in your local browser storage and used to authorize profile updates, interest approvals,
              and project management.
            </p>
          </div>

          {storedKeys.length === 0 ? (
            <EmptyState
              icon={Key}
              title="No ownership keys stored"
              description="Keys generated when you create a profile or project will automatically be stored in this vault."
            />
          ) : (
            <div className="space-y-3">
              {storedKeys.map((keyInfo) => (
                <div key={keyInfo.entityId} className="card p-5 space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <Badge
                          variant={keyInfo.entityType === 'profile' ? 'teal' : 'sky'}
                          size="sm"
                        >
                          {keyInfo.entityType} Owner
                        </Badge>
                        <span className="text-[10px] text-slate-400 font-mono">
                          ID: {keyInfo.entityId}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-slate-900">{keyInfo.title}</h4>
                    </div>

                    <button
                      onClick={() => removeKey(keyInfo.entityId)}
                      className="p-1 text-slate-400 hover:text-rose-600 transition-colors"
                      title="Remove key from vault"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-900 text-white flex items-center justify-between gap-3">
                    <span className="font-mono text-xs text-sky-400 truncate select-all">
                      {keyInfo.key}
                    </span>
                    <button
                      onClick={() => handleCopyKey(keyInfo.key)}
                      className="p-1 text-slate-300 hover:text-white transition-colors flex-shrink-0"
                      title="Copy key"
                    >
                      {copiedKey === keyInfo.key ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>

                  <div className="flex items-center justify-between text-xs pt-1">
                    <span className="text-[10px] text-slate-400">
                      Saved {new Date(keyInfo.createdAt).toLocaleDateString()}
                    </span>
                    <Link
                      to={
                        keyInfo.entityType === 'profile'
                          ? `/profiles/${keyInfo.entityId}`
                          : `/projects/${keyInfo.entityId}`
                      }
                      className="text-sky-700 hover:underline font-medium"
                    >
                      Manage {keyInfo.entityType} →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MySpacePage;
