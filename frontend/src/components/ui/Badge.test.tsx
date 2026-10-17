import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { Badge } from './Badge';

afterEach(() => {
  cleanup();
});

/**
 * Finalisasi Phase 1 — koreksi kontras teks badge (keputusan Option B).
 *
 * Batasan jsdom yang perlu jujur diakui: jsdom TIDAK memakai stylesheet
 * Tailwind, sehingga `getComputedStyle` tidak pernah bisa membuktikan warna
 * render sesungguhnya memenuhi WCAG. Unit test di bawah karena itu hanya
 * mengunci PEMILIHAN TOKEN/kelas yang sudah divalidasi dan memastikan
 * perilaku komponen tidak berubah. Angka kontras hasil render sesungguhnya
 * diverifikasi di Chrome produksi (light + dark), bukan di sini.
 */

interface VariantCase {
  variant: 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent';
  label: string;
  lightFg: string;
  darkFg: string;
  bg: string;
  border: string;
  extraBg: string;
}

/** Semua varian yang didukung komponen — termasuk warning yang belum dipakai UI. */
const VARIANTS: VariantCase[] = [
  {
    variant: 'success',
    label: 'Selesai',
    lightFg: 'text-badgeText-success',
    darkFg: 'dark:text-badgeText-success-dark',
    bg: 'bg-semantic-success/10',
    border: 'border-semantic-success/20',
    extraBg: '',
  },
  {
    variant: 'warning',
    label: 'Peringatan',
    lightFg: 'text-badgeText-warning',
    // warning dark sudah lolos 5.15:1 dengan token semantic lama, jadi token
    // lamanya dipakai ulang — tidak ada nilai duplikat di palet.
    darkFg: 'dark:text-semantic-warning',
    bg: 'bg-semantic-warning/10',
    border: 'border-semantic-warning/20',
    extraBg: '',
  },
  {
    variant: 'error',
    label: 'Gagal',
    lightFg: 'text-badgeText-error',
    darkFg: 'dark:text-badgeText-error-dark',
    bg: 'bg-semantic-error/10',
    border: 'border-semantic-error/20',
    extraBg: '',
  },
  {
    variant: 'info',
    label: 'Menunggu',
    lightFg: 'text-badgeText-info',
    darkFg: 'dark:text-badgeText-info-dark',
    bg: 'bg-semantic-info/10',
    border: 'border-semantic-info/20',
    extraBg: '',
  },
  {
    variant: 'accent',
    label: 'Unggah citra',
    lightFg: 'text-badgeText-accent',
    // accent-500 sudah lolos 5.10:1 pada dark-accentSurface; dipertahankan.
    darkFg: 'dark:text-accent-500',
    bg: 'bg-accent-100',
    border: 'border-accent-600/20',
    extraBg: 'dark:bg-dark-accentSurface',
  },
  {
    variant: 'default',
    label: '1 sesi',
    lightFg: 'text-neutral-700',
    darkFg: 'dark:text-neutral-300',
    bg: 'bg-neutral-100',
    border: 'border-neutral-200',
    extraBg: 'dark:bg-dark-elevated',
  },
];

describe('Badge: koreksi foreground teks (Option B)', () => {
  describe.each(VARIANTS)('variant $variant', (c: VariantCase) => {
    it('memakai token foreground terpisah untuk light DAN dark', () => {
      render(<Badge variant={c.variant}>{c.label}</Badge>);

      const badge = screen.getByText(c.label);
      // Kedua theme wajib mempunyai foreground sendiri; melewatkan salah
      // satu berarti theme itu gagal kontras.
      expect(badge.classList.contains(c.lightFg)).toBe(true);
      expect(badge.classList.contains(c.darkFg)).toBe(true);
      // Foreground berupa TOKEN, bukan hex hard-coded (StyleGuide 49).
      expect(c.lightFg.startsWith('text-')).toBe(true);
      expect(c.darkFg.startsWith('dark:text-')).toBe(true);
    });

    it('hue semantik dipertahankan: background tint DAN border tetap utuh', () => {
      render(<Badge variant={c.variant}>{c.label}</Badge>);

      const badge = screen.getByText(c.label);
      expect(badge.classList.contains(c.bg)).toBe(true);
      expect(badge.classList.contains(c.border)).toBe(true);
      if (c.extraBg) {
        expect(badge.classList.contains(c.extraBg)).toBe(true);
      }
    });

    it('tidak memakai warna referensi yang dilarang', () => {
      render(<Badge variant={c.variant}>{c.label}</Badge>);

      const cls = screen.getByText(c.label).className;
      for (const forbidden of ['#39CD99', '#3BD49E', '#F06169', '#FF0303', '#FF4242']) {
        expect(cls).not.toContain(forbidden);
      }
    });
  });

  it('setiap hue mempunyai token foreground sendiri (status tetap terbedakan)', () => {
    const semanticVariants = VARIANTS.filter((v) => v.variant !== 'default');
    const lightTokens = semanticVariants.map((v) => v.lightFg);
    const darkTokens = semanticVariants.map((v) => v.darkFg);

    // Menyeragamkan warna teks akan menghapus pembeda warna antar status
    // (StyleGuide 31: status harus punya kombinasi warna, ikon, dan teks).
    expect(new Set(lightTokens).size).toBe(lightTokens.length);
    expect(new Set(darkTokens).size).toBe(darkTokens.length);
  });

  it('keenam varian tetap dirender dengan benar', () => {
    for (const c of VARIANTS) {
      render(<Badge variant={c.variant}>{c.label}</Badge>);
      expect(screen.getByText(c.label).tagName).toBe('SPAN');
      cleanup();
    }
  });
});

describe('Badge: perilaku & API tidak berubah', () => {
  it('ukuran sm/md tetap seperti semula', () => {
    const { rerender } = render(<Badge size="sm">Kecil</Badge>);
    expect(screen.getByText('Kecil').classList.contains('text-[11px]')).toBe(true);
    expect(screen.getByText('Kecil').classList.contains('font-medium')).toBe(true);

    rerender(<Badge size="md">Besar</Badge>);
    expect(screen.getByText('Besar').classList.contains('text-xs')).toBe(true);
    expect(screen.getByText('Besar').classList.contains('font-semibold')).toBe(true);
  });

  it('uppercase default aktif dan bisa dimatikan', () => {
    render(<Badge>Riwayat</Badge>);
    expect(screen.getByText('Riwayat').classList.contains('uppercase')).toBe(true);
    cleanup();

    render(<Badge uppercase={false}>Selesai</Badge>);
    const badge = screen.getByText('Selesai');
    expect(badge.classList.contains('uppercase')).toBe(false);
    expect(badge.classList.contains('tracking-wider')).toBe(false);
  });

  it('ikon opsional dirender sebelum label; tanpa ikon tetap bersih', () => {
    render(
      <Badge
        variant="success"
        size="sm"
        uppercase={false}
        icon={<svg data-testid="status-icon" />}
      >
        Selesai
      </Badge>,
    );

    const badge = screen.getByText('Selesai');
    expect(badge.classList.contains('gap-1.5')).toBe(true);
    expect(badge.querySelector('[data-testid="status-icon"]')).not.toBeNull();

    cleanup();
    render(<Badge variant="success">Selesai</Badge>);
    expect(screen.getByText('Selesai').querySelector('svg')).toBeNull();
  });

  it('memakai varian default ketika prop variant tidak diberikan', () => {
    render(<Badge>Netral</Badge>);
    const badge = screen.getByText('Netral');
    expect(badge.classList.contains('bg-neutral-100')).toBe(true);
    expect(badge.classList.contains('text-neutral-700')).toBe(true);
    expect(badge.classList.contains('dark:text-neutral-300')).toBe(true);
  });

  it('className tambahan dan atribut elemen diteruskan (API tidak berubah)', () => {
    render(
      <Badge variant="info" className="mt-2" data-testid="custom-badge" id="badge-id">
        Menunggu
      </Badge>,
    );

    const badge = screen.getByTestId('custom-badge');
    expect(badge.classList.contains('mt-2')).toBe(true);
    expect(badge.getAttribute('id')).toBe('badge-id');
    // Kelas varian tidak hilang saat className eksternal ditambahkan.
    expect(badge.classList.contains('bg-semantic-info/10')).toBe(true);
    expect(badge.tagName).toBe('SPAN');
  });

  it('label status tetap teks biasa sehingga tidak bergantung pada warna', () => {
    for (const c of VARIANTS) {
      render(<Badge variant={c.variant}>{c.label}</Badge>);
      expect(screen.getByText(c.label).textContent).toBe(c.label);
      cleanup();
    }
  });
});
