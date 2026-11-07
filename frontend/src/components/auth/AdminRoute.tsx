import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AuthLoadingState } from './AuthLoadingState';

export interface AdminRouteProps {
  children?: React.ReactNode;
}

/**
 * Route guard for admin-only pages.
 *
 * - Shows loading state while auth is being resolved.
 * - Redirects to /login if not authenticated.
 * - Redirects to /dashboard if authenticated but NOT an admin (doctors cannot
 *   access admin pages even if their account is approved).
 */
export const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  const { user, loading, role } = useAuth();
  const location = useLocation();

  if (loading) {
    return <AuthLoadingState />;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // Only users with admin role can access admin pages.
  // Approved doctors, pending doctors, and rejected doctors are all blocked.
  if (role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return children ? <>{children}</> : null;
};

export default AdminRoute;
