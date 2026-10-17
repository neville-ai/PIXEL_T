import { useState, useEffect } from 'react';

export type Theme = 'light' | 'dark';

/**
 * Mendapatkan nilai tema berdasarkan preferensi tersimpan atau OS.
 * Fungsi ini tidak menulis ke localStorage — hanya membaca.
 */
function resolveInitialTheme(): Theme {
  if (typeof window === 'undefined') return 'light';
  const saved = localStorage.getItem('pixel-t-theme') as Theme | null;
  if (saved) return saved;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/**
 * Memastikan class `dark` diterapkan pada documentElement berdasarkan
 * preferensi tersimpan atau sistem, tanpa mengubah localStorage.
 * Fungsi ini bersifat "bootstrap" satu kali dan tidak menggantikan
 * logika toggle di ThemeToggle / useTheme.
 */
export function applyStoredTheme(): void {
  const theme = resolveInitialTheme();
  const root = document.documentElement;
  if (theme === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
}

export const useTheme = () => {
  const [theme, setTheme] = useState<Theme>(() => resolveInitialTheme());

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    // Tulis ke storage hanya saat toggle melalui useTheme,
    // bukan saat bootstrap (lihat applyStoredTheme di atas).
    localStorage.setItem('pixel-t-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  return { theme, setTheme, toggleTheme };
};
