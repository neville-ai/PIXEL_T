import React, { useState } from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import {
  Activity,
  PlusCircle,
  History as HistoryIcon,
  LayoutDashboard,
  LogIn,
  UserPlus,
  LogOut,
  User as UserIcon,
  Menu,
  X,
} from 'lucide-react';

export interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    setIsMobileMenuOpen(false);
    await signOut();
    navigate('/login', { replace: true });
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-colors select-none ${
      isActive
        ? 'bg-primary-50 text-primary-900 dark:bg-dark-elevated dark:text-accent-500 font-semibold shadow-xs'
        : 'text-neutral-600 hover:text-neutral-900 dark:text-dark-textMuted dark:hover:text-dark-text hover:bg-neutral-100 dark:hover:bg-dark-elevated/60'
    }`;

  const mobileNavLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2.5 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
      isActive
        ? 'bg-primary-50 text-primary-900 dark:bg-dark-elevated dark:text-accent-500 font-semibold'
        : 'text-neutral-600 hover:text-neutral-900 dark:text-dark-textMuted dark:hover:text-dark-text hover:bg-neutral-100 dark:hover:bg-dark-elevated/60'
    }`;

  const closeMobileMenu = () => setIsMobileMenuOpen(false);

  return (
    <div className="min-h-screen flex flex-col bg-neutral-50 dark:bg-dark-bg text-neutral-900 dark:text-dark-text transition-colors">
      {/* Header / Top Navigation */}
      <header className="sticky top-0 z-40 w-full border-b border-neutral-200 dark:border-dark-border bg-white/95 dark:bg-dark-surface/95 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo / Brand Identity */}
          <div className="flex items-center gap-6">
            <Link to={user ? '/dashboard' : '/login'} className="flex items-center gap-3 group">
              <div className="p-2 rounded-md bg-primary-900 text-white dark:bg-primary-600 group-hover:opacity-90 transition-opacity">
                <Activity className="w-5 h-5 text-accent-500" />
              </div>
              <div className="flex flex-col">
                <span className="text-base sm:text-lg font-bold tracking-tight text-primary-900 dark:text-dark-text leading-tight">
                  PIXEL-T
                </span>
                <span className="hidden sm:inline-block text-[10px] text-neutral-500 dark:text-dark-textMuted tracking-tight leading-none">
                  U-Net &bull; ResNet50 &bull; Grad-CAM
                </span>
              </div>
            </Link>

            {/* Desktop Primary Navigation Links (Authenticated only) */}
            {user && (
              <nav className="hidden md:flex items-center gap-1 border-l border-neutral-200 dark:border-dark-border pl-5">
                <NavLink to="/dashboard" className={navLinkClass}>
                  <LayoutDashboard className="w-4 h-4 text-accent-600 dark:text-accent-500" />
                  <span>Dashboard</span>
                </NavLink>

                <NavLink to="/analysis/new" className={navLinkClass}>
                  <PlusCircle className="w-4 h-4 text-accent-600 dark:text-accent-500" />
                  <span>New Analysis</span>
                </NavLink>

                <NavLink to="/history" className={navLinkClass}>
                  <HistoryIcon className="w-4 h-4 text-accent-600 dark:text-accent-500" />
                  <span>History</span>
                </NavLink>
              </nav>
            )}
          </div>

          {/* Right Action Area */}
          <div className="flex items-center gap-2">
            {user ? (
              /* Authenticated User Status & Logout */
              <div className="hidden md:flex items-center gap-3 mr-2 border-r border-neutral-200 dark:border-dark-border pr-3">
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-neutral-100 dark:bg-dark-elevated text-xs text-neutral-700 dark:text-neutral-300">
                  <UserIcon className="w-3.5 h-3.5 text-accent-600 dark:text-accent-500" />
                  <span className="max-w-[150px] truncate font-medium">{user.email}</span>
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-medium text-neutral-600 hover:text-semantic-error dark:text-dark-textMuted dark:hover:text-semantic-error hover:bg-neutral-100 dark:hover:bg-dark-elevated transition-colors"
                  title="Keluar dari sesi"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              /* Unauthenticated Auth Links */
              <div className="hidden lg:flex items-center gap-1.5 mr-2 border-r border-neutral-200 dark:border-dark-border pr-3">
                <NavLink to="/login" className={navLinkClass}>
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Login</span>
                </NavLink>
                <NavLink to="/register" className={navLinkClass}>
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Register</span>
                </NavLink>
              </div>
            )}

            {/* Theme Toggle Button */}
            <ThemeToggle />

            {/* Mobile Hamburger Button */}
            <button
              type="button"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="md:hidden p-2 rounded-md text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100 hover:bg-neutral-100 dark:hover:bg-dark-elevated transition-colors"
              aria-label="Toggle navigation menu"
              aria-expanded={isMobileMenuOpen}
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Dropdown Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-neutral-200 dark:border-dark-border bg-white dark:bg-dark-surface px-4 py-3 space-y-1 shadow-lg">
            {user ? (
              <>
                <div className="px-3 py-2 mb-2 rounded-md bg-neutral-100 dark:bg-dark-elevated text-xs text-neutral-700 dark:text-neutral-300 flex items-center gap-2">
                  <UserIcon className="w-4 h-4 text-accent-600 dark:text-accent-500" />
                  <span className="truncate font-medium">{user.email}</span>
                </div>

                <NavLink to="/dashboard" onClick={closeMobileMenu} className={mobileNavLinkClass}>
                  <LayoutDashboard className="w-4 h-4 text-accent-600 dark:text-accent-500" />
                  <span>Dashboard</span>
                </NavLink>

                <NavLink to="/analysis/new" onClick={closeMobileMenu} className={mobileNavLinkClass}>
                  <PlusCircle className="w-4 h-4 text-accent-600 dark:text-accent-500" />
                  <span>New Analysis</span>
                </NavLink>

                <NavLink to="/history" onClick={closeMobileMenu} className={mobileNavLinkClass}>
                  <HistoryIcon className="w-4 h-4 text-accent-600 dark:text-accent-500" />
                  <span>History</span>
                </NavLink>

                <div className="pt-2 mt-2 border-t border-neutral-100 dark:border-dark-border">
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-md text-sm font-medium text-semantic-error hover:bg-semantic-error/10 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Logout</span>
                  </button>
                </div>
              </>
            ) : (
              <div className="flex flex-col gap-1">
                <NavLink to="/login" onClick={closeMobileMenu} className={mobileNavLinkClass}>
                  <LogIn className="w-4 h-4" />
                  <span>Login</span>
                </NavLink>
                <NavLink to="/register" onClick={closeMobileMenu} className={mobileNavLinkClass}>
                  <UserPlus className="w-4 h-4" />
                  <span>Register</span>
                </NavLink>
              </div>
            )}
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer & Clinical Disclaimer */}
      <footer className="w-full border-t border-neutral-200 dark:border-dark-border bg-white dark:bg-dark-surface py-6 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-2 text-center">
          <p className="text-xs text-neutral-600 dark:text-dark-textMuted max-w-3xl mx-auto leading-relaxed">
            <strong className="text-neutral-700 dark:text-neutral-300 font-semibold">Disclaimer Medis:</strong> Hasil yang ditampilkan merupakan keluaran analisis model AI dan ditujukan sebagai informasi pendukung bagi tenaga medis. Hasil ini tidak dimaksudkan sebagai diagnosis medis atau pengganti penilaian profesional tenaga medis.
          </p>
          <p className="text-[11px] text-neutral-400 dark:text-neutral-500">
            PIXEL-T &copy; 2026 &mdash; Transfer Learning dan Explainable AI untuk Segmentasi Polip Usus
          </p>
        </div>
      </footer>
    </div>
  );
};

export default AppShell;
