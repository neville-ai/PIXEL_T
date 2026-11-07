import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AuthLoadingState } from './AuthLoadingState';

export interface ProtectedRouteProps {
  children?: React.ReactNode;
}

/**
 * Route guard for clinical/doctor features.
 *
 * - Shows loading state while auth is being resolved.
 * - Redirects to /login if not authenticated.
 * - Redirects to /login if the account is pending (awaiting approval).
 * - Redirects to /login if the account is rejected.
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, loading, accountStatus } = useAuth();
  const location = useLocation();

  if (loading) {
    return <AuthLoadingState />;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // Block access for pending or rejected accounts
  if (accountStatus === 'pending') {
    return <Navigate to="/login" replace state={{ from: location, pending: true }} />;
  }
  if (accountStatus === 'rejected') {
    return <Navigate to="/login" replace state={{ from: location, rejected: true }} />;
  }

  return children ? <>{children}</> : <Outlet />;
};

export default ProtectedRoute;
