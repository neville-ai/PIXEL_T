import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { AuthLoadingState } from './AuthLoadingState';

export interface PublicOnlyRouteProps {
  children?: React.ReactNode;
}

export const PublicOnlyRoute: React.FC<PublicOnlyRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <AuthLoadingState />;
  }

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};

export default PublicOnlyRoute;
