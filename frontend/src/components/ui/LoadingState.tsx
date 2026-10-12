import React from 'react';
import { Loader2 } from 'lucide-react';

export interface LoadingStateProps {
  title?: string;
  description?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  title = 'Memproses...',
  description = 'Sistem sedang memproses data sesuai antrean.',
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center space-y-3 rounded-lg border border-dashed border-neutral-200 dark:border-dark-border bg-neutral-50/50 dark:bg-dark-surface/50 ${className}`}>
      <Loader2 className="w-8 h-8 text-accent-600 dark:text-accent-500 animate-spin" />
      <div className="space-y-1">
        <h4 className="text-sm font-semibold text-neutral-900 dark:text-dark-text tracking-tight">
          {title}
        </h4>
        <p className="text-xs text-neutral-600 dark:text-dark-textMuted max-w-sm">
          {description}
        </p>
      </div>
    </div>
  );
};
