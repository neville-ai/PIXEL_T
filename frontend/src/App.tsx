import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '@/context/AuthContext';
import { AppShell } from '@/components/layout/AppShell';
import { AppRoutes } from '@/routes/AppRoutes';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppShell>
          <AppRoutes />
        </AppShell>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
