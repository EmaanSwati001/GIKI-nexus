import React from 'react';
import {
  GraduationCap,
  BookOpen,
  Users,
  Share2,
  UserCheck,
  Search,
  Sparkles,
  Activity,
  Key,
} from 'lucide-react';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  systemStatus: 'online' | 'offline' | 'checking';
  myProfileKey: string | null;
  onManageKeys: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  systemStatus,
  myProfileKey,
  onManageKeys,
}) => {
  const navItems = [
    { id: 'academic', label: 'Academic & Courses', icon: BookOpen },
    { id: 'faculty', label: 'Faculty & Research', icon: Users },
    { id: 'graph', label: 'Knowledge Graph', icon: Share2 },
    { id: 'teammates', label: 'Teammate Finder', icon: UserCheck, badge: 'Milestone 2' },
    { id: 'assistant', label: 'Nexus AI Search', icon: Sparkles },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0d1424]/90 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Institute Branding */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('academic')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 text-white font-bold">
              <GraduationCap className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-sky-100 to-sky-400 bg-clip-text text-transparent">
                  GIKI NEXUS
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wider bg-sky-950 text-sky-400 border border-sky-800/60 px-1.5 py-0.5 rounded">
                  v1.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 -mt-0.5 font-medium hidden sm:block">
                Ghulam Ishaq Khan Institute of Engineering Sciences and Technology
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-sky-600 text-white shadow-md shadow-sky-600/25'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                      isActive ? 'bg-sky-800 text-sky-200' : 'bg-emerald-950 text-emerald-400 border border-emerald-800/40'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right Status & Quick Action */}
          <div className="flex items-center space-x-3">
            {/* System Status Indicator */}
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-xs">
              <div
                className={`w-2 h-2 rounded-full ${
                  systemStatus === 'online'
                    ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]'
                    : systemStatus === 'checking'
                    ? 'bg-amber-400 animate-pulse'
                    : 'bg-rose-500'
                }`}
              />
              <span className="text-slate-300 text-[11px] font-mono capitalize hidden sm:inline">
                API {systemStatus}
              </span>
            </div>

            {/* Ownership Key Storage Pill */}
            <button
              onClick={onManageKeys}
              title="Manage your profile/project ownership keys"
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                myProfileKey
                  ? 'bg-sky-950/60 border-sky-700 text-sky-300 hover:bg-sky-900/60'
                  : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-700'
              }`}
            >
              <Key className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">
                {myProfileKey ? 'Auth Key Active' : 'Saved Keys'}
              </span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation bar */}
        <div className="flex md:hidden overflow-x-auto py-2 space-x-1 border-t border-slate-800/60">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap ${
                  isActive
                    ? 'bg-sky-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
};
