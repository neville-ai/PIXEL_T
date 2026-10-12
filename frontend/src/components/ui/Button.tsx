import React from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  leftIcon,
  rightIcon,
  className = '',
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none';

  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 rounded-sm gap-1.5',
    md: 'text-sm px-4 py-2 rounded-md gap-2',
    lg: 'text-base px-6 py-2.5 rounded-lg gap-2.5',
  };

  const variantStyles = {
    primary: 'bg-primary-900 text-white hover:bg-primary-800 active:bg-primary-700 focus:ring-primary-700 dark:bg-primary-600 dark:hover:bg-primary-700 dark:focus:ring-primary-600',
    secondary: 'bg-neutral-100 text-neutral-900 hover:bg-neutral-200 active:bg-neutral-300 focus:ring-neutral-400 dark:bg-dark-elevated dark:text-dark-text dark:hover:bg-dark-border',
    accent: 'bg-accent-600 text-white hover:bg-accent-700 active:bg-accent-800 focus:ring-accent-500 dark:bg-accent-500 dark:hover:bg-accent-600 dark:text-neutral-950',
    outline: 'border border-neutral-300 text-neutral-900 bg-transparent hover:bg-neutral-100 focus:ring-primary-700 dark:border-dark-border dark:text-dark-text dark:hover:bg-dark-elevated',
    ghost: 'text-neutral-700 hover:bg-neutral-100 focus:ring-primary-700 dark:text-neutral-300 dark:hover:bg-dark-elevated',
    danger: 'bg-semantic-error text-white hover:opacity-90 focus:ring-semantic-error',
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        leftIcon
      )}
      <span>{children}</span>
      {!isLoading && rightIcon}
    </button>
  );
};
