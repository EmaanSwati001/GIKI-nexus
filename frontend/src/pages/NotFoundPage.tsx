import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Home, Search } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="card max-w-lg mx-auto my-16 p-8 sm:p-10 text-center">
      <div className="font-mono text-5xl font-extrabold text-slate-300">404</div>
      <h1 className="text-xl font-bold text-slate-900 mt-4">Page Not Found</h1>
      <p className="text-xs text-slate-500 mt-2 leading-relaxed">
        The academic resource or route you requested could not be located in the GIKI Nexus catalog.
      </p>

      <div className="mt-6 flex items-center justify-center gap-3">
        <Link to="/" className="btn-primary text-xs py-2 px-4 flex items-center gap-1.5">
          <Home className="w-3.5 h-3.5" />
          <span>Go to Home</span>
        </Link>
        <Link to="/search" className="btn-secondary text-xs py-2 px-4 flex items-center gap-1.5">
          <Search className="w-3.5 h-3.5" />
          <span>Search Index</span>
        </Link>
      </div>
    </div>
  );
};

export default NotFoundPage;
