import React, { useCallback, useEffect, useRef, useState } from 'react';
import { NavLink, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { ThemeToggle } from '@/components/ui/ThemeToggle';
import { Modal } from '@/components/ui/Modal';
import { LogoPixelT } from '@/components/brand/LogoPixelT';
import { getDisplayName, getUserInitials } from '@/lib/format';
import {
  PlusCircle,
  History as HistoryIcon,
  LayoutDashboard,
  LogIn,
  UserPlus,
  LogOut,
  User as UserIcon,
  Menu,
  X,
  ChevronDown,
  Settings2,
} from 'lucide-react';

export interface AppShellProps {
  children: React.ReactNode;
}

/**
 * Mengamati class `dark` pada <html> sehingga komponen chrome (logo, dsb.)
 * mengikuti theme walau toggle dipanggil dari instance `useTheme` lain
 * (ThemeToggle menyimpan state-nya sendiri, jadi state lokal tidak sinkron).
 */
function useDocumentDarkClass(): boolean {
  const [isDark, setIsDark] = useState<boolean>(() =>
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark'),
  );

  useEffect(() => {
    const root = document.documentElement;
    const sync = () => setIsDark(root.classList.contains('dark'));
    sync();

    if (typeof MutationObserver === 'undefined') return;
    const observer = new MutationObserver(sync);
    observer.observe(root, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  return isDark;
}

const NAV_LINK_CLASS = ({ isActive }: { isActive: boolean }) =>
  `relative inline-flex items-center h-16 select-none text-sm font-medium transition-colors after:absolute after:inset-x-0 after:bottom-px after:h-0.5 after:bg-accent-600 after:transition-opacity ${
    isActive
      ? 'text-accent-600 dark:text-accent-500 after:opacity-100'
      : 'text-neutral-600 after:opacity-0 hover:text-neutral-900 dark:text-dark-textMuted dark:hover:text-dark-text'
  }`;

const MOBILE_NAV_LINK_CLASS = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-2.5 px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
    isActive
      ? 'bg-primary-50 text-primary-900 dark:bg-dark-elevated dark:text-accent-500 font-semibold'
      : 'text-neutral-600 hover:text-neutral-900 dark:text-dark-textMuted dark:hover:text-dark-text hover:bg-neutral-100 dark:hover:bg-dark-elevated/60'
  }`;

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const isDark = useDocumentDarkClass();

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isSignOutOpen, setIsSignOutOpen] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);

  const userMenuRef = useRef<HTMLDivElement | null>(null);

  // Tutup dropdown user saat klik di area lain atau menekan Escape.
  useEffect(() => {
    if (!isUserMenuOpen) return;

    const handlePointerDown = (event: MouseEvent) => {
      if (!userMenuRef.current?.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsUserMenuOpen(false);
    };

    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isUserMenuOpen]);

  const requestSignOut = useCallback(() => {
    setIsUserMenuOpen(false);
    setIsMobileMenuOpen(false);
    setIsSignOutOpen(true);
  }, []);

  const cancelSignOut = useCallback(() => {
    if (isSigningOut) return;
    setIsSignOutOpen(false);
  }, [isSigningOut]);

  const confirmSignOut = useCallback(async () => {
    if (isSigningOut) return;
    setIsSigningOut(true);
    try {
      // Layanan autentikasi Supabase yang sudah ada — tidak diubah.
      await signOut();
      setIsSignOutOpen(false);
      navigate('/login', { replace: true });
    } finally {
      setIsSigningOut(false);
    }
  }, [isSigningOut, navigate, signOut]);

  const closeMobileMenu = () => setIsMobileMenuOpen(false);

  const displayName = getDisplayName(user);
  const initials = getUserInitials(displayName);

  return (
    <div className="min-h-screen flex flex-col bg-neutral-50 dark:bg-dark-bg text-neutral-900 dark:text-dark-text transition-colors">
      {/* Header / Top Navigation */}
      <header className="sticky top-0 z-40 w-full border-b border-neutral-200 bg-white dark:border-[#1E384A] dark:bg-[#001620] transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand Identity — official PIXEL-T lockup */}
          <Link
            to={user ? '/dashboard' : '/login'}
            className="flex items-center shrink-0"
            aria-label="PIXEL-T"
          >
            <LogoPixelT
              variant={isDark ? 'light' : 'transparent'}
              inkHeight={26}
            />
          </Link>

          {/* Desktop Primary Navigation (center group) */}
          {user && (
            <nav className="hidden md:flex items-center gap-8" aria-label="Primary">
              <NavLink to="/dashboard" className={NAV_LINK_CLASS}>
                Dashboard
              </NavLink>
              <NavLink to="/analysis/new" className={NAV_LINK_CLASS}>
                New Analysis
              </NavLink>
              <NavLink to="/history" className={NAV_LINK_CLASS}>
                History
              </NavLink>
            </nav>
          )}

          {/* Right Action Area */}
          <div className="flex items-center gap-3">
            {user ? (
              <>
                <ThemeToggle />

                {/* Pemisah vertikal antara kontrol tema dan identitas pengguna
                    (terukur ~2x21px pada referensi). */}
                <span
                  aria-hidden="true"
                  className="hidden sm:block h-5 w-0.5 bg-neutral-200 dark:bg-[#1E384A]"
                />

                {/* User avatar / menu trigger */}
                <div className="relative" ref={userMenuRef}>
                  <button
                    type="button"
                    onClick={() => setIsUserMenuOpen((open) => !open)}
                    className="inline-flex items-center gap-2.5 h-11 pl-2.5 pr-2.5 rounded-md border border-neutral-200 bg-white text-neutral-700 hover:bg-neutral-50 dark:border-dark-border dark:bg-[#081D29] dark:text-dark-text dark:hover:bg-dark-elevated transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-[#001620]"
                    aria-haspopup="menu"
                    aria-expanded={isUserMenuOpen}
                    aria-label={displayName ? `Menu pengguna ${displayName}` : 'Menu pengguna'}
                  >
                    <span
                      aria-hidden="true"
                      className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-accent-600/40 bg-accent-100 text-xs font-bold tracking-wide text-accent-700 dark:bg-dark-accentSurface dark:text-accent-500"
                    >
                      {initials}
                    </span>
                    <span className="hidden sm:inline max-w-[180px] truncate text-sm font-semibold">
                      {displayName}
                    </span>
                    <ChevronDown
                      aria-hidden="true"
                      className={`w-3.5 h-3.5 text-neutral-400 dark:text-dark-textMuted transition-transform ${
                        isUserMenuOpen ? 'rotate-180' : ''
                      }`}
                    />
                  </button>

                  {/* User dropdown */}
                  {isUserMenuOpen && (
                    <div
                      role="menu"
                      aria-label="Menu pengguna"
                      className="absolute right-0 top-full mt-2 w-72 origin-top-right rounded-lg border border-neutral-200 bg-white shadow-lg dark:border-[#1E3749] dark:bg-[#10222E] dark:shadow-black/40 overflow-hidden"
                    >
                      <div className="px-4 py-3.5 border-b border-neutral-100 dark:border-[#1E3645]">
                        <p className="text-sm font-semibold text-neutral-900 dark:text-dark-text truncate">
                          {displayName || 'Pengguna'}
                        </p>
                        {user?.email && (
                          <p className="mt-0.5 text-xs text-neutral-500 dark:text-dark-textMuted truncate">
                            {user.email}
                          </p>
                        )}
                      </div>

                      {/* Account Information — inert in this phase: no profile
                          route is added until that design is implemented. */}
                      <div
                        role="menuitem"
                        aria-disabled="true"
                        title="Halaman Account Information belum tersedia"
                        className="flex items-start gap-3 px-4 py-2.5 dark:items-center dark:py-3.5 text-neutral-400 dark:text-neutral-500 cursor-not-allowed select-none"
                      >
                        <span
                          aria-hidden="true"
                          className="inline-flex shrink-0 items-center justify-center dark:h-8 dark:w-8 dark:rounded-[10px] dark:bg-[#102D3E]"
                        >
                          <UserIcon className="w-4 h-4 mt-0.5 dark:mt-0 dark:text-[#18A6A6]" />
                        </span>
                        <span className="min-w-0">
                          <span className="block text-xs font-semibold">Account Information</span>
                          <span className="block text-[11px]">View your account information</span>
                        </span>
                      </div>

                      <div>
                        <button
                          type="button"
                          role="menuitem"
                          onClick={requestSignOut}
                          className="w-full flex items-start gap-3 px-4 py-2.5 dark:items-center dark:py-3.5 text-left text-neutral-700 hover:bg-neutral-50 dark:text-dark-text dark:hover:bg-dark-elevated transition-colors"
                        >
                          <span
                            aria-hidden="true"
                            className="inline-flex shrink-0 items-center justify-center dark:h-8 dark:w-8 dark:rounded-[10px] dark:bg-[#102D3E]"
                          >
                            <LogOut className="w-4 h-4 mt-0.5 dark:mt-0 dark:text-[#18A6A6]" />
                          </span>
                          <span className="min-w-0">
                            <span className="block text-xs font-semibold">Sign Out</span>
                            <span className="block text-[11px] text-neutral-500 dark:text-dark-textMuted">
                              End workstation session
                            </span>
                          </span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              /* Unauthenticated Auth Links */
              <div className="hidden lg:flex items-center gap-1.5">
                <NavLink to="/login" className={NAV_LINK_CLASS}>
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Login</span>
                </NavLink>
                <NavLink to="/register" className={NAV_LINK_CLASS}>
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Register</span>
                </NavLink>
              </div>
            )}

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
          <div className="md:hidden border-t border-neutral-200 bg-white px-4 py-3 space-y-1 shadow-lg dark:border-dark-border dark:bg-[#001620]">
            {user ? (
              <>
                <div className="px-3 py-2 mb-2 rounded-md bg-neutral-100 text-xs text-neutral-700 flex items-center gap-2 dark:bg-dark-elevated dark:text-neutral-300">
                  <UserIcon className="w-4 h-4 text-accent-600 dark:text-accent-500" />
                  <span className="truncate font-medium">{displayName}</span>
                </div>

                <NavLink to="/dashboard" onClick={closeMobileMenu} className={MOBILE_NAV_LINK_CLASS}>
                  <LayoutDashboard className="w-4 h-4 text-accent-600 dark:text-accent-500" />
                  <span>Dashboard</span>
                </NavLink>

                <NavLink to="/analysis/new" onClick={closeMobileMenu} className={MOBILE_NAV_LINK_CLASS}>
                  <PlusCircle className="w-4 h-4 text-accent-600 dark:text-accent-500" />
                  <span>New Analysis</span>
                </NavLink>

                <NavLink to="/history" onClick={closeMobileMenu} className={MOBILE_NAV_LINK_CLASS}>
                  <HistoryIcon className="w-4 h-4 text-accent-600 dark:text-accent-500" />
                  <span>History</span>
                </NavLink>

                <div className="pt-2 mt-2 border-t border-neutral-100 dark:border-dark-border">
                  <div
                    className="flex items-center gap-2.5 px-3 py-2.5 text-sm font-medium text-neutral-400 dark:text-neutral-500 cursor-not-allowed select-none"
                    aria-disabled="true"
                    title="Halaman Account Information belum tersedia"
                  >
                    <Settings2 className="w-4 h-4" />
                    <span>Account Information</span>
                  </div>
                  <button
                    type="button"
                    onClick={requestSignOut}
                    className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-md text-sm font-medium text-semantic-error hover:bg-semantic-error/10 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </>
            ) : (
              <div className="flex flex-col gap-1">
                <NavLink to="/login" onClick={closeMobileMenu} className={MOBILE_NAV_LINK_CLASS}>
                  <LogIn className="w-4 h-4" />
                  <span>Login</span>
                </NavLink>
                <NavLink to="/register" onClick={closeMobileMenu} className={MOBILE_NAV_LINK_CLASS}>
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

      {/* Footer */}
      <footer className="w-full border-t border-neutral-200 bg-white dark:border-[#1E384A] dark:bg-[#001620] transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 sm:h-16 sm:py-0 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <LogoPixelT variant={isDark ? 'light' : 'transparent'} inkHeight={23} />
            <span
              aria-hidden="true"
              className="hidden sm:block h-4 w-px bg-neutral-200 dark:bg-dark-border"
            />
            <p className="text-xs text-neutral-500 dark:text-dark-textMuted">
              Polyp Image eXplainable Learning Technology
            </p>
          </div>
          <p className="text-xs text-neutral-400 dark:text-neutral-500">
            &copy; 2026 PIXEL-T. All rights reserved.
          </p>
        </div>
      </footer>

      {/* Sign-out confirmation dialog */}
      <Modal
        isOpen={isSignOutOpen}
        onClose={cancelSignOut}
        surface="light"
        hideClose
        hideHeaderDivider
        maxWidthClass="max-w-[420px]"
        title="Are you sure you want to sign out?"
        description="You will need to sign in again to access your account and analysis history."
      >
        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={cancelSignOut}
            disabled={isSigningOut}
            className="inline-flex items-center justify-center rounded-md border border-neutral-300 bg-white h-11 px-5 text-base font-medium text-neutral-900 transition-colors hover:bg-neutral-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 focus-visible:ring-offset-2 disabled:opacity-50"
          >
            No
          </button>
          <button
            type="button"
            onClick={() => void confirmSignOut()}
            disabled={isSigningOut}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-semantic-error h-11 px-5 text-base font-medium text-white transition-colors hover:bg-semantic-error/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-semantic-error focus-visible:ring-offset-2 disabled:opacity-50"
          >
            {isSigningOut ? 'Signing out\u2026' : 'Yes'}
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default AppShell;
