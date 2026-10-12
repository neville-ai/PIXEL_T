import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PublicOnlyRoute } from '@/components/auth/PublicOnlyRoute';
import { Login } from '@/pages/auth/Login';
import { Register } from '@/pages/auth/Register';
import { Dashboard } from '@/pages/dashboard/Dashboard';
import { NewAnalysis } from '@/pages/analysis/NewAnalysis';
import { AnalysisResult } from '@/pages/analysis/AnalysisResult';
import { History } from '@/pages/history/History';
import { HistoryDetail } from '@/pages/history/HistoryDetail';
import { NotFound } from '@/pages/NotFound';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Root redirect to Dashboard (guarded by ProtectedRoute) */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Public Only Auth Routes (redirects to /dashboard if already authenticated) */}
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <Login />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicOnlyRoute>
            <Register />
          </PublicOnlyRoute>
        }
      />

      {/* Protected Clinical Routes (requires authenticated Supabase session) */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analysis/new"
        element={
          <ProtectedRoute>
            <NewAnalysis />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analysis/:id"
        element={
          <ProtectedRoute>
            <AnalysisResult />
          </ProtectedRoute>
        }
      />
      <Route
        path="/history"
        element={
          <ProtectedRoute>
            <History />
          </ProtectedRoute>
        }
      />
      <Route
        path="/history/:id"
        element={
          <ProtectedRoute>
            <HistoryDetail />
          </ProtectedRoute>
        }
      />

      {/* Fallback 404 Route */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

export default AppRoutes;
