import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'bordered';
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  className = '',
  ...props
}) => {
  const variantStyles = {
    default: 'bg-white dark:bg-dark-surface border border-neutral-200 dark:border-dark-border shadow-sm',
    elevated: 'bg-white dark:bg-dark-elevated border border-neutral-200/80 dark:border-dark-border shadow-md',
    bordered: 'bg-transparent border border-neutral-300 dark:border-dark-border',
  };

  return (
    <div
      className={`rounded-lg p-5 transition-colors ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  children,
  className = '',
  ...props
}) => (
  <div className={`border-b border-neutral-100 dark:border-dark-border pb-3 mb-4 ${className}`} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className = '',
  ...props
}) => (
  <h3 className={`text-base font-semibold text-neutral-900 dark:text-dark-text tracking-tight ${className}`} {...props}>
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  children,
  className = '',
  ...props
}) => (
  <p className={`text-xs text-neutral-600 dark:text-dark-textMuted mt-0.5 ${className}`} {...props}>
    {children}
  </p>
);
