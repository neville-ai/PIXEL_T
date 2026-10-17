import type { ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import App from './App';
import { useAuth } from '@/context/AuthContext';
import { OPENING_SESSION_STORAGE_KEY } from '@/lib/openingTimeline';

vi.mock('@/context/AuthContext', () => ({
  // Passthrough provider: no Supabase session machinery in this unit test.
  AuthProvider: ({ children }: { children?: ReactNode }) => children ?? null,
  useAuth: vi.fn(),
}));

beforeEach(() => {
  // jsdom in this project does not implement window.matchMedia, and the
  // existing useTheme hook (unmodified, outside this task's scope) calls it
  // unguarded from ThemeToggle inside AppShell. Provide a minimal shim so the
  // shell can render in this unit test.
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  window.sessionStorage.clear();
  // Keep the intro skipped so we assert chrome/layout, not animation state.
  window.sessionStorage.setItem(OPENING_SESSION_STORAGE_KEY, '1');
  vi.mocked(useAuth).mockReturnValue({
    user: null,
    session: null,
    loading: false,
    signIn: vi.fn(),
    signUp: vi.fn(),
    signOut: vi.fn(),
  } as unknown as ReturnType<typeof useAuth>);
});

afterEach(() => {
  cleanup();
});

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

describe('App shell composition', () => {
  it('/login dirender TANPA global header, footer, atau disclaimer', () => {
    renderAt('/login');

    expect(screen.getByRole('heading', { level: 1, name: 'Welcome Back' })).toBeTruthy();
    expect(screen.queryByRole('banner')).toBeNull();
    expect(screen.queryByRole('contentinfo')).toBeNull();
  });

  it('/register tetap menggunakan AppShell (header & footer global)', () => {
    renderAt('/register');

    expect(screen.getByRole('banner')).toBeTruthy();
    expect(screen.getByRole('contentinfo')).toBeTruthy();
  });
});

describe('Theme bootstrap on bare routes', () => {
  it('tema dark tersimpan tetap diterapkan pada /login tanpa AppShell', () => {
    window.localStorage.setItem('pixel-t-theme', 'dark');
    renderAt('/login');

    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('tema light tersimpan menghapus class dark pada /login', () => {
    document.documentElement.classList.add('dark');
    window.localStorage.setItem('pixel-t-theme', 'light');
    renderAt('/login');

    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });
});
