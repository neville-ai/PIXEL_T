import React, { useEffect } from 'react';
import { X } from 'lucide-react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-neutral-950/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
        className="relative w-full max-w-lg rounded-xl bg-white dark:bg-dark-surface border border-neutral-200 dark:border-dark-border p-6 shadow-xl transition-all z-10 space-y-4"
      >
        <div className="flex items-center justify-between border-b border-neutral-100 dark:border-dark-border pb-3">
          <div>
            {title && (
              <h2 id="modal-title" className="text-base font-semibold text-neutral-900 dark:text-dark-text">
                {title}
              </h2>
            )}
            {description && (
              <p className="text-xs text-neutral-600 dark:text-dark-textMuted mt-0.5">{description}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-neutral-400 hover:text-neutral-700 dark:hover:text-dark-text hover:bg-neutral-100 dark:hover:bg-dark-elevated transition-colors"
            aria-label="Tutup modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div>{children}</div>
      </div>
    </div>
  );
};
