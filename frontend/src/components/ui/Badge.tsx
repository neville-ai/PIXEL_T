import React from 'react';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  className = '',
  ...props
}) => {
  const variantStyles = {
    default: 'bg-neutral-100 text-neutral-700 dark:bg-dark-elevated dark:text-neutral-300 border border-neutral-200 dark:border-dark-border',
    success: 'bg-semantic-success/10 text-semantic-success border border-semantic-success/20',
    warning: 'bg-semantic-warning/10 text-semantic-warning border border-semantic-warning/20',
    error: 'bg-semantic-error/10 text-semantic-error border border-semantic-error/20',
    info: 'bg-semantic-info/10 text-semantic-info border border-semantic-info/20',
    accent: 'bg-accent-100 text-accent-700 dark:bg-dark-accentSurface dark:text-accent-500 border border-accent-600/20',
  };

  const sizeStyles = {
    sm: 'text-[11px] px-2 py-0.5 rounded-sm font-medium',
    md: 'text-xs px-2.5 py-1 rounded-sm font-semibold',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 uppercase tracking-wider ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};
