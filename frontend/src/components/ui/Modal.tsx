import React, { useEffect } from 'react';
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
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
        className={`relative w-full ${maxWidthClass} rounded-xl border ${paddingClass} shadow-xl transition-all z-10 ${spacingClass} ${surfaceClass}`}
      >
        <div
          className={`flex items-center justify-between ${
            hideHeaderDivider ? '' : 'border-b border-neutral-100 dark:border-dark-border pb-3'
          }`}
        >
          <div>
            {title && (
              <h2 id="modal-title" className={titleClass}>
                {title}
              </h2>
            )}
            {description && (
              <p className={descriptionClass}>{description}</p>
            )}
          </div>
          {!hideClose && (
            <button
              onClick={onClose}
              className="rounded-md p-1.5 text-neutral-400 hover:text-neutral-700 dark:hover:text-dark-text hover:bg-neutral-100 dark:hover:bg-dark-elevated transition-colors"
              aria-label="Tutup modal"
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
