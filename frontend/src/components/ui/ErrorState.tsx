import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Button } from './Button';

export interface ErrorStateProps {
  code?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  code = 'ERROR',
  message = 'Terjadi kesalahan pada sistem. Silakan coba kembali.',
  onRetry,
  className = '',
}) => {
  return (
    <div
      role="alert"
      className={`flex flex-col items-center justify-center p-6 text-center space-y-3 rounded-lg border border-semantic-error/30 bg-semantic-error/5 dark:bg-semantic-error/10 ${className}`}
    >
      <div className="p-2.5 rounded-full bg-semantic-error/10 text-semantic-error">
        <AlertCircle className="w-6 h-6" />
      </div>
      <div className="space-y-1">
        <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-badgeText-error dark:text-badgeText-error-dark">
          Kode Error: {code}
        </span>
        <p className="text-xs text-neutral-700 dark:text-neutral-300 max-w-sm">
          {message}
        </p>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="mt-1">
          Coba Lagi
        </Button>
      )}
    </div>
  );
};
