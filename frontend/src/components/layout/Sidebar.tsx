import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Home,
  BookOpen,
  Users,
  FlaskConical,
  GraduationCap,
  Building2,
  Share2,
  Briefcase,
  UserCheck,
  Bookmark,
  ExternalLink,
  Search,
  Sparkles,
} from 'lucide-react';
import { useSaved } from '../../context/SavedContext';

interface SidebarProps {
  isOpen: boolean;
  onClose?: () => void;
}

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  end?: boolean;
  badge?: number;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();
  const { savedItems } = useSaved();

  const navGroups: NavGroup[] = [
    {
      title: 'Navigation',
      items: [
        { label: 'Home', path: '/', icon: Home, end: true },
        { label: 'Search', path: '/search', icon: Search },
      ],
    },
    {
      title: 'Academic Discovery',
      items: [
        { label: 'Courses', path: '/courses', icon: BookOpen },
        { label: 'Faculty Directory', path: '/faculty', icon: Users },
        { label: 'Research Areas', path: '/research', icon: FlaskConical },
        { label: 'Degree Programs', path: '/programs', icon: GraduationCap },
        { label: 'Academic Units', path: '/units', icon: Building2 },
      ],
    },
    {
      title: 'Knowledge Graph',
      items: [
        { label: 'Graph Visualizer', path: '/graph', icon: Share2 },
      ],
    },
    {
      title: 'Project Hub',
      items: [
        { label: 'Projects', path: '/projects', icon: Briefcase },
        { label: 'Teammate Finder', path: '/profiles', icon: UserCheck },
      ],
    },
    {
      title: 'Personal Workspace',
      items: [
        {
          label: 'My Space',
          path: '/my-space',
          icon: Bookmark,
          badge: savedItems.length > 0 ? savedItems.length : undefined,
        },
      ],
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/30 backdrop-blur-xs lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col w-64 bg-white border-r border-slate-200/80 shadow-sm transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="flex items-center gap-3 px-6 h-16 border-b border-slate-100 flex-shrink-0">
          <div className="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center text-white font-bold text-sm shadow-sm">
            GN
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-slate-900 text-sm tracking-tight">GIKI NEXUS</span>
              <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-sky-50 text-sky-700 border border-sky-100">
                v1.0
              </span>
            </div>
            <span className="text-[11px] text-slate-400 font-medium">Academic Discovery</span>
          </div>
        </div>

        {/* Scrollable Navigation */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {navGroups.map((group) => (
            <div key={group.title}>
              <div className="px-3 mb-1.5 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
                {group.title}
              </div>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = item.end
                    ? location.pathname === item.path
                    : location.pathname.startsWith(item.path);

                  return (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={onClose}
                      className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-slate-900 text-white shadow-xs font-semibold'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon
                          className={`w-4 h-4 ${
                            isActive ? 'text-white' : 'text-slate-400'
                          } stroke-[1.75]`}
                        />
                        <span>{item.label}</span>
                      </div>
                      {item.badge !== undefined && (
                        <span
                          className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                            isActive
                              ? 'bg-slate-800 text-slate-200'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* GIKI CourseHub Ecosystem Banner */}
        <div className="p-3 border-t border-slate-100 bg-stone-50/50 flex-shrink-0">
          <a
            href="https://www.gikicoursehub.app/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 bg-white hover:border-slate-300 hover:shadow-xs transition-all group"
          >
            <div className="flex items-center gap-2.5">
              <div className="w-6 h-6 rounded bg-sky-50 text-sky-600 flex items-center justify-center font-bold text-xs">
                CH
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-slate-800 group-hover:text-sky-600 transition-colors">
                  GIKI CourseHub
                </span>
                <span className="text-[10px] text-slate-400">Student Reviews & Notes</span>
              </div>
            </div>
            <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600" />
          </a>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
