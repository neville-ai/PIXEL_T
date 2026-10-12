import React from 'react';
import { Inbox } from 'lucide-react';

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title?: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title = 'Tidak Ada Data',
  description = 'Belum ada data atau item untuk ditampilkan saat ini.',
  action,
  className = '',
}) => {
  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center space-y-3 rounded-lg border border-dashed border-neutral-200 dark:border-dark-border bg-white dark:bg-dark-surface ${className}`}>
      <div className="p-3 rounded-full bg-neutral-100 dark:bg-dark-elevated text-neutral-500 dark:text-neutral-400">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <div className="space-y-1">
        <h4 className="text-sm font-semibold text-neutral-900 dark:text-dark-text tracking-tight">
          {title}
        </h4>
        <p className="text-xs text-neutral-600 dark:text-dark-textMuted max-w-sm">
          {description}
        </p>
      </div>
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
};
