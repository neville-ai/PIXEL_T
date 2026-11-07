import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AdminRoute } from '@/components/auth/AdminRoute';
import { DoctorRoute } from '@/components/auth/DoctorRoute';
import { PublicOnlyRoute } from '@/components/auth/PublicOnlyRoute';
import { Login } from '@/pages/auth/Login';
import { Register } from '@/pages/auth/Register';
import { ResetPassword } from '@/pages/auth/ResetPassword';
import { Dashboard } from '@/pages/dashboard/Dashboard';
import { NewAnalysis } from '@/pages/analysis/NewAnalysis';
import { AnalysisResult } from '@/pages/analysis/AnalysisResult';
import { History } from '@/pages/history/History';
import { HistoryDetail } from '@/pages/history/HistoryDetail';
import { DoctorProfile } from '@/pages/profile/DoctorProfile';
import { AdminDashboard } from '@/pages/admin/AdminDashboard';
import { NotFound } from '@/pages/NotFound';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Root redirect to Login (entry point per P-39) */}
      <Route path="/" element={<Navigate to="/login" replace />} />

      {/* Public Only Auth Routes (redirects to role-appropriate page if already authenticated) */}
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
      <Route
        path="/reset-password"
        element={<ResetPassword />}
      />

      {/* Protected Clinical Routes (requires authenticated + approved doctor) */}
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
      <Route
        path="/profile"
        element={
          <DoctorRoute>
            <DoctorProfile />
          </DoctorRoute>
        }
      />

      {/* Admin Routes (requires admin role — separate from doctor ProtectedRoute) */}
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        }
      />

      {/* Fallback 404 Route */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
};

export default AppRoutes;