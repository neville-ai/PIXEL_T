import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent';
  size?: 'sm' | 'md';
  /**
   * Ikon opsional yang ditampilkan sebelum label (mis. ikon status pada
   * kartu dashboard). Default tanpa ikon, sehingga pemakaian lama tidak
   * berubah.
   */
  icon?: React.ReactNode;
  /**
   * Label huruf besar. Default `true` (perilaku lama). Diset `false` untuk
   * mengikuti referensi dashboard yang memakai huruf biasa (sentence case).
   */
  uppercase?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  icon,
  uppercase = true,
  className = '',
  ...props
}) => {
  /**
   * Teks badge memakai token `badgeText` (diturunkan dari hue semantic yang
   * sama) agar lolos WCAG AA 4.5:1 pada tint /10 di kedua theme.
   * Border dan background tetap memakai token `semantic`/`accent` asli,
   * jadi hue dan makna status tidak berubah (StyleGuide 5.4, 31, 38).
   * `warning` dark dan `accent` dark sudah lolos dengan token lama, sehingga
   * token lamanya dipakai ulang — tidak ada nilai duplikat.
   */
  const variantStyles = {
    default: 'bg-neutral-100 text-neutral-700 dark:bg-dark-elevated dark:text-neutral-300 border border-neutral-200 dark:border-dark-border',
    success: 'bg-semantic-success/10 text-badgeText-success dark:text-badgeText-success-dark border border-semantic-success/20',
    warning: 'bg-semantic-warning/10 text-badgeText-warning dark:text-semantic-warning border border-semantic-warning/20',
    error: 'bg-semantic-error/10 text-badgeText-error dark:text-badgeText-error-dark border border-semantic-error/20',
    info: 'bg-semantic-info/10 text-badgeText-info dark:text-badgeText-info-dark border border-semantic-info/20',
    accent: 'bg-accent-100 text-badgeText-accent dark:bg-dark-accentSurface dark:text-accent-500 border border-accent-600/20',
  };

  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 rounded-sm font-medium',
    md: 'text-xs px-2.5 py-1 rounded-sm font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 ${uppercase ? 'uppercase tracking-wider' : ''} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {icon}
      {children}
    </span>
  );
};
