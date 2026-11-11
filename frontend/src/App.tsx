import React, { useLayoutEffect } from 'react';
import { BrowserRouter, useLocation } from 'react-router-dom';
import { AuthProvider } from '@/context/AuthContext';
import { AppShell } from '@/components/layout/AppShell';
import { AppRoutes } from '@/AppRoutes';
import { applyStoredTheme } from '@/hooks/useTheme';

/**
 * Applies the user's stored/system theme preference to <html> once, before the
 * first paint, on EVERY route.
 *
 * Why this lives here: the only other place that touches the `dark` class is
 * `useTheme`, which is invoked exclusively by `ThemeToggle`, and `ThemeToggle`
 * only exists inside `AppShell`. Since `/login` deliberately renders outside
 * `AppShell`, a direct visit or reload of `/login` never applied the `dark`
 * class — dark-mode users saw the light (near-white) form panel instead.
 *
 * This is a passive read: it never writes to storage and never forces a theme.
 * `ThemeToggle` remains the single writer of the user's preference.
 */
const ThemeBootstrap: React.FC = () => {
  useLayoutEffect(() => {
    applyStoredTheme();
  }, []);

  return null;
};

/**
 * Renders the global AppShell (header, footer) around the routes — EXCEPT for
 * `/login`, which must be a bare two-panel page with no global chrome (per the
 * locked Login design).
 *
 * Phase 1: AppShell was updated to the approved dashboard reference (official
 * PIXEL-T lockup, centered nav, user menu, footer). The global footer no longer
 * carries the clinical disclaimer; per StyleGuide §26 and FunctionalSpec §28 it
 * lives in the result context, where `AnalysisResult` renders it.
 */
const AppShellSwitch: React.FC = () => {
  const location = useLocation();
  const isBareLogin = location.pathname === '/login';

  if (isBareLogin) {
    return <AppRoutes />;
  }

  return (
    <AppShell>
      <AppRoutes />
    </AppShell>
  );
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ThemeBootstrap />
        <AppShellSwitch />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
