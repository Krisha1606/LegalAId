import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import { useAuth } from '../context/AuthContext';

// Lazy loading pages can be added later
import { LandingPage } from '../pages/Landing/LandingPage';
import { Login } from '../pages/Login/Login';
import { Home } from '../pages/Home/Home';
import { LegalAssistant } from '../pages/LegalAssistant/LegalAssistant';
import { Results } from '../pages/Results/Results';
import { DocumentEditorPage } from '../pages/Documents/DocumentEditorPage';
import { NotFound } from '../pages/NotFound/NotFound';

export const AppRoutes = () => {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route path="/" element={
        isAuthenticated ? <Navigate to="/home" replace /> : <LandingPage />
      } />
      
      <Route path="/login" element={
        isAuthenticated ? <Navigate to="/home" replace /> : <Login />
      } />

      <Route path="/home" element={
        <ProtectedRoute>
          <Home />
        </ProtectedRoute>
      } />

      <Route path="/assistant" element={
        <ProtectedRoute>
          <LegalAssistant />
        </ProtectedRoute>
      } />

      <Route path="/results" element={
        <ProtectedRoute>
          <Results />
        </ProtectedRoute>
      } />

      <Route path="/documents" element={
        <ProtectedRoute>
          <div className="p-8 max-w-7xl mx-auto py-10">
            <div className="bg-white rounded-[2rem] shadow-xl border border-gray-100 p-12 text-center">
              <h1 className="text-3xl font-bold text-[#1a1a1a] mb-4">My Documents</h1>
              <p className="text-lg text-[#52525b]">Document history will be available here.</p>
            </div>
          </div>
        </ProtectedRoute>
      } />

      <Route path="/documents/:id" element={
        <ProtectedRoute>
          <DocumentEditorPage />
        </ProtectedRoute>
      } />

      <Route path="/profile" element={
        <ProtectedRoute>
          <div className="p-8 max-w-7xl mx-auto py-10">
            <div className="bg-white rounded-[2rem] shadow-xl border border-gray-100 p-12 text-center">
              <h1 className="text-3xl font-bold text-[#1a1a1a] mb-4">Profile</h1>
              <p className="text-lg text-[#52525b]">User profile details will be displayed here.</p>
            </div>
          </div>
        </ProtectedRoute>
      } />

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};
