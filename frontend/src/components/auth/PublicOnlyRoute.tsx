import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AuthLoadingState } from './AuthLoadingState';

export interface PublicOnlyRouteProps {
  children?: React.ReactNode;
}

/**
 * Route guard for public-only pages (login, register).
 *
 * - Shows loading state while auth is being resolved.
 * - Redirects authenticated users to their appropriate home page:
 *   - Admin → /admin
 *   - Approved doctor → /dashboard
 * - Allows unauthenticated users and pending/rejected users to stay on public pages.
 */
export const PublicOnlyRoute: React.FC<PublicOnlyRouteProps> = ({ children }) => {
  const { user, loading, role, accountStatus } = useAuth();

  if (loading) {
    return <AuthLoadingState />;
  }

  // Redirect authenticated users to their role-appropriate home page.
  if (user) {
    if (role === 'admin') {
      return <Navigate to="/admin" replace />;
    }
    if (accountStatus === 'approved') {
      return <Navigate to="/dashboard" replace />;
    }
    // Pending and rejected users are allowed to stay on public pages
    // (e.g. to see the awaiting-approval notice on /login).
  }

  return children ? <>{children}</> : <Outlet />;
};

export default PublicOnlyRoute;
