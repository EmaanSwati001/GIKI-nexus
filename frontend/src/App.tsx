import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { SavedProvider } from './context/SavedContext';
import AppLayout from './components/layout/AppLayout';

import HomePage from './pages/HomePage';
import CoursesPage from './pages/CoursesPage';
import CourseDetailPage from './pages/CourseDetailPage';
import FacultyPage from './pages/FacultyPage';
import FacultyDetailPage from './pages/FacultyDetailPage';
import ResearchAreasPage from './pages/ResearchAreasPage';
import ProgramsPage from './pages/ProgramsPage';
import ProgramDetailPage from './pages/ProgramDetailPage';
import UnitsPage from './pages/UnitsPage';
import KnowledgeGraphPage from './pages/KnowledgeGraphPage';
import ProjectsPage from './pages/ProjectsPage';
import ProjectDetailPage from './pages/ProjectDetailPage';
import CreateProjectPage from './pages/CreateProjectPage';
import ProfilesPage from './pages/ProfilesPage';
import ProfileDetailPage from './pages/ProfileDetailPage';
import CreateProfilePage from './pages/CreateProfilePage';
import SearchResultsPage from './pages/SearchResultsPage';
import MySpacePage from './pages/MySpacePage';
import NotFoundPage from './pages/NotFoundPage';

export const App: React.FC = () => {
  return (
    <SavedProvider>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/courses" element={<CoursesPage />} />
          <Route path="/courses/:courseCode" element={<CourseDetailPage />} />
          <Route path="/faculty" element={<FacultyPage />} />
          <Route path="/faculty/:facultyId" element={<FacultyDetailPage />} />
          <Route path="/research" element={<ResearchAreasPage />} />
          <Route path="/programs" element={<ProgramsPage />} />
          <Route path="/programs/:programId" element={<ProgramDetailPage />} />
          <Route path="/units" element={<UnitsPage />} />
          <Route path="/graph" element={<KnowledgeGraphPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="/projects/new" element={<CreateProjectPage />} />
          <Route path="/profiles" element={<ProfilesPage />} />
          <Route path="/profiles/:profileId" element={<ProfileDetailPage />} />
          <Route path="/profiles/new" element={<CreateProfilePage />} />
          <Route path="/search" element={<SearchResultsPage />} />
          <Route path="/my-space" element={<MySpacePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </SavedProvider>
  );
};

export default App;
