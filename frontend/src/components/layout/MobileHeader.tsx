import React from 'react';
import { Menu, Search, Bookmark } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useSaved } from '../../context/SavedContext';

interface MobileHeaderProps {
  onToggleSidebar: () => void;
}

export const MobileHeader: React.FC<MobileHeaderProps> = ({ onToggleSidebar }) => {
  const { savedItems } = useSaved();

  return (
    <header className="lg:hidden sticky top-0 z-30 flex items-center justify-between h-14 px-4 bg-white border-b border-slate-200/80 shadow-xs">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <Link to="/" className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-slate-900 flex items-center justify-center text-white font-bold text-xs">
            GN
          </div>
          <span className="font-bold text-slate-900 text-sm tracking-tight">GIKI NEXUS</span>
        </Link>
      </div>

      <div className="flex items-center gap-1.5">
        <Link
          to="/search"
          className="p-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors"
          aria-label="Search"
        >
          <Search className="w-4 h-4" />
        </Link>
        <Link
          to="/my-space"
          className="p-1.5 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors relative"
          aria-label="My Space"
        >
          <Bookmark className="w-4 h-4" />
          {savedItems.length > 0 && (
            <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-sky-500" />
          )}
        </Link>
      </div>
    </header>
  );
};

export default MobileHeader;
