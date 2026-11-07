import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AuthLoadingState } from './AuthLoadingState';

export interface DoctorRouteProps {
  children?: React.ReactNode;
}

/**
 * Route guard for doctor-only clinical features.
 *
 * - Shows loading state while auth is being resolved.
 * - Redirects to /login if not authenticated.
 * - Redirects to /dashboard if the user is an Admin (admins have no clinical
 *   features and must not see the Doctor Profile or analysis pages).
 * - Redirects to /login if the account is pending (awaiting approval).
 * - Redirects to /login if the account is rejected.
 * - Approved doctors are allowed through.
 */
export const DoctorRoute: React.FC<DoctorRouteProps> = ({ children }) => {
  const { user, loading, role, accountStatus } = useAuth();
  const location = useLocation();

  if (loading) {
    return <AuthLoadingState />;
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // Admins must not access doctor-only clinical pages.
  if (role === 'admin') {
    return <Navigate to="/admin" replace />;
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

export default DoctorRoute;
