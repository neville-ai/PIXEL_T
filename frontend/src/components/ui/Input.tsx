import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className = '', id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`w-full px-3.5 py-2 text-sm rounded-md border transition-colors bg-white dark:bg-dark-surface text-neutral-900 dark:text-dark-text placeholder:text-neutral-400 focus:outline-none focus:ring-2 ${
            error
              ? 'border-semantic-error focus:ring-semantic-error/30'
              : 'border-neutral-200 dark:border-dark-border focus:border-primary-700 focus:ring-primary-700/20 dark:focus:border-primary-600 dark:focus:ring-primary-600/30'
          } disabled:bg-neutral-100 disabled:opacity-60 disabled:cursor-not-allowed ${className}`}
          {...props}
        />
        {error && (
          <p className="text-xs text-badgeText-error dark:text-badgeText-error-dark font-medium">{error}</p>
        )}
        {!error && helperText && (
          <p className="text-xs text-neutral-600 dark:text-dark-textMuted">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
