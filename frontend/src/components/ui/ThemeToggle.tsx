import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';

export const ThemeToggle: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={`inline-flex items-center justify-center p-2 rounded-md text-neutral-600 dark:text-dark-textMuted hover:text-neutral-900 dark:hover:text-dark-text hover:bg-neutral-100 dark:hover:bg-dark-elevated transition-colors border border-transparent hover:border-neutral-200 dark:hover:border-dark-border ${className}`}
      aria-label={`Ganti ke mode ${theme === 'light' ? 'gelap' : 'terang'}`}
      title={`Mode ${theme === 'light' ? 'Gelap' : 'Terang'}`}
    >
      {/* Ukuran ikon 20px mengikuti referensi header (ikon terukur ~19px),
          warna mengikuti warna tombol (netral), bukan warna aksen. */}
      {theme === 'light' ? (
        <Moon className="w-5 h-5" />
      ) : (
        <Sun className="w-5 h-5" />
      )}
    </button>
  );
};
