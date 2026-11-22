import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import MobileHeader from './MobileHeader';

export const AppLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-stone-50 flex flex-col">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <MobileHeader onToggleSidebar={() => setSidebarOpen((prev) => !prev)} />

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col">
        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Outlet />
        </main>

        {/* Global Institutional Footer */}
        <footer className="w-full border-t border-slate-200/80 bg-white py-6 px-4 sm:px-6 lg:px-8 text-xs text-slate-500">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-700">GIKI Nexus</span>
              <span>— Ghulam Ishaq Khan Institute of Engineering Sciences and Technology</span>
            </div>
            <div className="flex items-center gap-4 text-slate-400">
              <a
                href="https://www.gikicoursehub.app/"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-slate-600 transition-colors"
              >
                GIKI CourseHub
              </a>
              <span>•</span>
              <a
                href="/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-slate-600 transition-colors"
              >
                API Docs
              </a>
              <span>•</span>
              <span>Prototype Platform</span>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default AppLayout;
