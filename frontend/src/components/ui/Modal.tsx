import React, { useEffect, useRef, useId } from 'react';
import { X } from 'lucide-react';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  /**
   * `default` mengikuti tema aktif (perilaku lama, dipakai dialog hapus
   * riwayat). `light` memaksa permukaan putih terlepas dari tema, sesuai
   * referensi dashboard untuk dialog konfirmasi sign-out.
   */
  surface?: 'default' | 'light';
  /** Sembunyikan tombol silang pada header (referensi dialog sign-out). */
  hideClose?: boolean;
  /** Sembunyikan garis pemisah bawah header (referensi dialog sign-out). */
  hideHeaderDivider?: boolean;
  /** Kelas tambahan untuk membatasi lebar dialog. */
  maxWidthClass?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  surface = 'default',
  hideClose = false,
  hideHeaderDivider = false,
  maxWidthClass = 'max-w-lg',
}) => {
  const dialogRef = useRef<HTMLDivElement>(null);
  const previouslyFocusedRef = useRef<HTMLElement | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Unique IDs per instance using React 18 useId()
  const titleId = useId();
  const descriptionId = useId();

  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  // Focus management: trap focus, initial focus, restore focus
  useEffect(() => {
    if (!isOpen) return;

    // Store previously focused element
    previouslyFocusedRef.current = document.activeElement as HTMLElement;

    // Initial focus: prefer close button, then first focusable in dialog
    const focusDialog = () => {
      if (dialogRef.current) {
        // Do not steal focus if focus is already inside dialog (e.g. user already clicked/focused an input)
        if (document.activeElement && dialogRef.current.contains(document.activeElement)) {
          return;
        }

        // Try close button first
        if (closeButtonRef.current) {
          closeButtonRef.current.focus();
        } else {
          // Fallback: find first focusable element
          const focusable = dialogRef.current.querySelector<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          if (focusable) {
            focusable.focus();
          } else {
            // Last resort: focus the dialog itself
            dialogRef.current.focus();
          }
        }
      }
    };

    // Defer focus to next tick to ensure DOM is ready
    const timeoutId = window.setTimeout(focusDialog, 0);

    // Focus trap handler
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onCloseRef.current();
        return;
      }

      if (e.key === 'Tab' && dialogRef.current) {
        const focusableElements = dialogRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const focusableArray = Array.from(focusableElements).filter((el) => {
          const style = window.getComputedStyle(el);
          const isDisabled = el.hasAttribute('disabled') || (el as HTMLButtonElement | HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement).disabled === true;
          return style.display !== 'none' && style.visibility !== 'hidden' && !isDisabled;
        });

        if (focusableArray.length === 0) return;

        const firstElement = focusableArray[0];
        const lastElement = focusableArray[focusableArray.length - 1];

        if (e.shiftKey) {
          // Shift+Tab: if on first element, wrap to last
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          // Tab: if on last element, wrap to first
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.clearTimeout(timeoutId);
      window.removeEventListener('keydown', handleKeyDown);
      // Restore focus to previously focused element (hardened)
      const prev = previouslyFocusedRef.current;
      if (prev && typeof prev.focus === 'function') {
        // Check if element is still in document and focusable
        if (prev.isConnected && document.body.contains(prev)) {
          const style = window.getComputedStyle(prev);
          if (style.display !== 'none' && style.visibility !== 'hidden' && !prev.hasAttribute('disabled')) {
            try {
              prev.focus();
            } catch {
              // Focus failed silently; do not interrupt cleanup
            }
          }
        }
      }
    };
  }, [isOpen]);

  if (!isOpen) return null;

  // Permukaan dialog. `default` mengikuti tema (perilaku lama); `light` selalu
  // putih sesuai referensi dashboard untuk dialog konfirmasi sign-out.
  const surfaceClass =
    surface === 'light'
      ? 'bg-white text-neutral-900 border-neutral-200'
      : 'bg-white dark:bg-dark-surface border-neutral-200 dark:border-dark-border';

  // Tipografi judul/deskripsi. Jalur default dipertahankan persis seperti
  // perilaku lama Modal agar dialog hapus riwayat tidak berubah. Jalur
  // `light` memakai skala tipografi dialog konfirmasi sign-out referensi
  // (judul 20px, deskripsi 14px, padding 32px).
  const titleClass =
    surface === 'light'
      ? 'text-xl font-semibold text-neutral-900'
      : 'text-base font-semibold text-neutral-900 dark:text-dark-text';

  const descriptionClass =
    surface === 'light'
      ? 'text-sm leading-relaxed text-neutral-600 mt-1'
      : 'text-xs text-neutral-600 dark:text-dark-textMuted mt-0.5';

  const paddingClass = surface === 'light' ? 'p-8' : 'p-6';

  // Jarak antara blok judul/deskripsi dan blok isi. Jalur `light` memakai
  // 36px sesuai referensi dialog konfirmasi sign-out.
  const spacingClass = surface === 'light' ? 'space-y-9' : 'space-y-4';

  // Scrim dialog. Referensi memakai navy #001620 dengan opasitas 75% tanpa
  // blur (terverifikasi pada 3 sampel piksel); jalur default dipertahankan.
  const backdropClass =
    surface === 'light' ? 'bg-[#001620]/75' : 'bg-neutral-950/60 backdrop-blur-sm';

  // Conditional ARIA references using unique IDs
  const labelledBy = title ? titleId : undefined;
  const describedBy = description ? descriptionId : undefined;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className={`fixed inset-0 ${backdropClass} transition-opacity`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Dialog */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        aria-describedby={describedBy}
        tabIndex={-1}
        className={`relative w-full ${maxWidthClass} rounded-xl border ${paddingClass} shadow-xl transition-all z-10 ${spacingClass} ${surfaceClass}`}
      >
        <div
          className={`flex items-center justify-between ${
            hideHeaderDivider ? '' : 'border-b border-neutral-100 dark:border-dark-border pb-3'
          }`}
        >
          <div>
            {title && (
              <h2 id={titleId} className={titleClass}>
                {title}
              </h2>
            )}
            {description && (
              <p id={descriptionId} className={descriptionClass}>{description}</p>
            )}
          </div>
          {!hideClose && (
            <button
              ref={closeButtonRef}
              type="button"
              onClick={onClose}
              className="rounded-md p-1.5 text-neutral-400 hover:text-neutral-700 dark:hover:text-dark-text hover:bg-neutral-100 dark:hover:bg-dark-elevated transition-colors"
              aria-label="Close modal"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <div>{children}</div>
      </div>
    </div>
  );
};
