/**
 * P2-01 — Status Text Contrast Remediation (regresi).
 *
 * Batch ini hanya memindahkan warna TEKS pada alert/pesan error dari token
 * `semantic` tunggal ke pasangan token `badgeText` yang sudah ada, karena
 * `semantic.error`/`semantic.success` tidak sanggup mencapai 4.5:1 pada
 * surface bertint di tema terang maupun gelap (StyleGuide 38).
 *
 * Yang dijaga oleh test ini:
 *   1. Nilai global `semantic.*` tetap byte-for-byte (dipakai border, tint,
 *      tombol danger, dan ikon).
 *   2. Kelas latar/border tiap lokasi tidak berubah sama sekali.
 *   3. Hanya foreground teks yang pindah ke `badgeText`, tanpa hex baru.
 *   4. Teks dan makna status yang dapat diakses tetap identik.
 *   5. Badge yang sudah disetujui Phase 1 tidak tersentuh.
 *
 * Sumber dibaca lewat impor `?raw` bawaan Vite (lihat src/vite-env.d.ts),
 * bukan `node:fs`, karena proyek ini tidak memasang @types/node.
 *
 * LIMITASI: jsdom tidak mem-compile stylesheet Tailwind maupun pseudo-state,
 * sehingga test ini membuktikan TOKEN yang dipakai, bukan rasio kontras hasil
 * render. Pengukuran kontras sesungguhnya dilakukan di Chrome terpisah dan
 * dicatat pada laporan P2-01.
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { ErrorState } from '@/components/ui/ErrorState';
import { Input } from '@/components/ui/Input';

import cfgSrc from '../../tailwind.config.js?raw';
import loginSrc from '@/pages/auth/Login.tsx?raw';
import registerSrc from '@/pages/auth/Register.tsx?raw';
import analysisResultSrc from '@/pages/analysis/AnalysisResult.tsx?raw';
import newAnalysisSrc from '@/pages/analysis/index.tsx?raw';
import errorStateSrc from '@/components/ui/ErrorState.tsx?raw';
import inputSrc from '@/components/ui/Input.tsx?raw';
import appShellSrc from '@/components/layout/AppShell.tsx?raw';
import badgeSrc from '@/components/ui/Badge.tsx?raw';

const count = (text: string, needle: string): number => text.split(needle).length - 1;

/**
 * Hitung kemunculan kelas terang TANPA ikut menghitung varian gelapnya.
 * `text-badgeText-error` adalah substring dari `dark:text-badgeText-error-dark`,
 * jadi: kelas terang = total kemunculan − jumlah varian gelap.
 *
 * NB: dihitung lewat split, bukan regex look-ahead. Ekstraktor kandidat
 * Tailwind menemukan pola look-ahead sebagai "kelas", dan itu membuat
 * build CSS gagal saat diproses bersama `@apply` di index.css.
 */
const countLight = (text: string, kind: 'error' | 'success'): number =>
  count(text, `text-badgeText-${kind}`) - count(text, `text-badgeText-${kind}-dark`);

const countDark = (text: string, kind: 'error' | 'success'): number =>
  count(text, `dark:text-badgeText-${kind}-dark`);

afterEach(cleanup);

describe('P2-01: config token', () => {
  it('nilai global semantic.* tidak berubah sama sekali', () => {
    const block = cfgSrc.match(/semantic:\s*\{[^}]*\}/)?.[0] ?? '';
    expect(block).not.toBe('');
    expect(block).toContain("success: '#2E8B70'");
    expect(block).toContain("warning: '#D99A2B'");
    expect(block).toContain("error: '#C94A4A'");
    expect(block).toContain("info: '#2878A8'");
  });

  it('pasangan badgeText yang dipakai ulang sudah ada — tidak ada hex baru', () => {
    const block = cfgSrc.match(/badgeText:\s*\{[^}]*\}/)?.[0] ?? '';
    expect(block).not.toBe('');
    expect(block).toContain("success: '#25705B'");
    expect(block).toContain("'success-dark': '#3BB390'");
    expect(block).toContain("error: '#B43636'");
    expect(block).toContain("'error-dark': '#DB8585'");
  });
});

describe('P2-01: foreground pindah ke badgeText, latar/border tetap', () => {
  it('Login — dua alert error', () => {
    expect(countLight(loginSrc, 'error')).toBe(2);
    expect(countDark(loginSrc, 'error')).toBe(2);
    expect(count(loginSrc, 'bg-semantic-error/10')).toBe(2);
    expect(count(loginSrc, 'border-semantic-error/30')).toBe(2);
    expect(loginSrc).not.toContain('text-semantic-error');
  });

  it('Register — alert error dan alert success', () => {
    expect(countLight(registerSrc, 'error')).toBe(1);
    expect(countDark(registerSrc, 'error')).toBe(1);
    expect(countLight(registerSrc, 'success')).toBe(1);
    expect(countDark(registerSrc, 'success')).toBe(1);

    expect(count(registerSrc, 'bg-semantic-error/10')).toBe(1);
    expect(count(registerSrc, 'border-semantic-error/30')).toBe(1);
    expect(count(registerSrc, 'bg-semantic-success/10')).toBe(1);
    expect(count(registerSrc, 'border-semantic-success/30')).toBe(1);

    expect(registerSrc).not.toContain('text-semantic-error');
    expect(registerSrc).not.toContain('text-semantic-success');
  });

  it('AnalysisResult — alert role=alert; ikon di luar cakupan tidak berubah', () => {
    expect(countLight(analysisResultSrc, 'error')).toBe(1);
    expect(countDark(analysisResultSrc, 'error')).toBe(1);
    expect(analysisResultSrc).toContain('bg-semantic-error/5');
    expect(analysisResultSrc).toContain('border-semantic-error/30');

    // Ikon AlertCircle 16px adalah konten non-teks (WCAG 1.4.11, 3:1) dan
    // sengaja di luar cakupan P2-01.
    expect(count(analysisResultSrc, 'text-semantic-error')).toBe(1);
    expect(analysisResultSrc).toContain(
      '<AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-semantic-error" />',
    );
  });

  it('NewAnalysis — dua alert error', () => {
    expect(countLight(newAnalysisSrc, 'error')).toBe(2);
    expect(countDark(newAnalysisSrc, 'error')).toBe(2);
    expect(newAnalysisSrc).toContain('bg-semantic-error/5');
    expect(newAnalysisSrc).toContain('border-semantic-error/30');
    expect(newAnalysisSrc).not.toContain('text-semantic-error');
  });

  it('ErrorState — kode error pindah; container ikon tetap semantic', () => {
    expect(countLight(errorStateSrc, 'error')).toBe(1);
    expect(countDark(errorStateSrc, 'error')).toBe(1);

    // Latar alert tidak berubah (terang /5, gelap /10) + border.
    expect(errorStateSrc).toContain(
      'border border-semantic-error/30 bg-semantic-error/5 dark:bg-semantic-error/10',
    );
    // Container ikon 24px tetap memakai tint + token semantic asli.
    expect(errorStateSrc).toContain('bg-semantic-error/10 text-semantic-error');
    expect(count(errorStateSrc, 'text-semantic-error')).toBe(1);
  });

  it('Input — hanya pesan error; border/focus ring tidak berubah', () => {
    expect(countLight(inputSrc, 'error')).toBe(1);
    expect(countDark(inputSrc, 'error')).toBe(1);
    expect(inputSrc).toContain("'border-semantic-error focus:ring-semantic-error/30'");
    expect(inputSrc).not.toContain('text-semantic-error');
  });

  it('AppShell — item Sign Out; perilaku hover menu tidak berubah', () => {
    expect(countLight(appShellSrc, 'error')).toBe(1);
    expect(countDark(appShellSrc, 'error')).toBe(1);
    expect(appShellSrc).toContain('hover:bg-semantic-error/10 transition-colors');
    expect(appShellSrc).toContain('<span>Sign Out</span>');
    expect(appShellSrc).not.toContain('text-semantic-error');
  });

  it('Badge — varian yang sudah disetujui Phase 1 tidak tersentuh', () => {
    expect(badgeSrc).toContain(
      "success: 'bg-semantic-success/10 text-badgeText-success dark:text-badgeText-success-dark border border-semantic-success/20'",
    );
    expect(badgeSrc).toContain(
      "error: 'bg-semantic-error/10 text-badgeText-error dark:text-badgeText-error-dark border border-semantic-error/20'",
    );
  });

  it('tidak ada warna arbitrary pada foreground yang disentuh batch ini', () => {
    for (const src of [loginSrc, registerSrc, analysisResultSrc, newAnalysisSrc, errorStateSrc, inputSrc]) {
      expect(src).not.toMatch(/text-\[#/);
    }
  });
});

describe('P2-01: perilaku DOM yang dapat diakses tetap', () => {
  it('ErrorState menampilkan kode + pesan default dengan token badgeText', () => {
    render(<ErrorState code="ERR_500" />);

    const alert = screen.getByRole('alert');
    const code = screen.getByText('Kode Error: ERR_500');

    // Foreground teks memakai pasangan badgeText (terang + gelap).
    expect(code.className).toContain('text-badgeText-error');
    expect(code.className).toContain('dark:text-badgeText-error-dark');
    expect(code.className).not.toContain('text-semantic-error');

    // Latar/border alert tidak berubah.
    expect(alert.className).toContain('border-semantic-error/30');
    expect(alert.className).toContain('bg-semantic-error/5');
    expect(alert.className).toContain('dark:bg-semantic-error/10');

    // Container ikon di luar cakupan: tetap semantic.
    expect(alert.querySelector('.text-semantic-error')).not.toBeNull();

    // Teks & makna error tetap identik.
    expect(screen.getByText('Terjadi kesalahan pada sistem. Silakan coba kembali.')).toBeTruthy();
  });

  it('Input menampilkan pesan error dengan token badgeText, label tetap terhubung', () => {
    render(<Input label="Email address" error="Wajib diisi." />);

    const message = screen.getByText('Wajib diisi.');
    expect(message.className).toContain('text-badgeText-error');
    expect(message.className).toContain('dark:text-badgeText-error-dark');
    expect(message.className).not.toContain('text-semantic-error');

    // Border dan focus ring error pada input tidak berubah.
    const input = screen.getByLabelText('Email address');
    expect(input.className).toContain('border-semantic-error');
    expect(input.className).toContain('focus:ring-semantic-error/30');
  });
});

// ---------------------------------------------------------------------------
// P-15: Input field error association (aria-invalid + aria-describedby)
// ---------------------------------------------------------------------------
describe('P-15: Input field error association', () => {
  it('Input with error has aria-invalid="true"', () => {
    render(<Input label="Email address" error="Wajib diisi." />);

    const input = screen.getByLabelText('Email address');
    expect(input.getAttribute('aria-invalid')).toBe('true');
  });

  it('Input with error has aria-describedby pointing to error element', () => {
    render(<Input label="Email address" error="Wajib diisi." />);

    const input = screen.getByLabelText('Email address');
    const describedBy = input.getAttribute('aria-describedby');
    expect(describedBy).toBeTruthy();

    const errorId = describedBy!.split(' ').find((id) => id.startsWith(':r')) ?? describedBy;
    const errorEl = document.getElementById(errorId!);
    expect(errorEl).not.toBeNull();
    expect(errorEl?.textContent).toBe('Wajib diisi.');
  });

  it('Input without error has no aria-invalid or aria-describedby for error', () => {
    render(<Input label="Email address" />);

    const input = screen.getByLabelText('Email address');
    expect(input.getAttribute('aria-invalid')).toBeNull();
    expect(input.getAttribute('aria-describedby')).toBeNull();
  });

  it('Input with helperText but no error has aria-describedby for helper', () => {
    render(<Input label="Email address" helperText="Enter your email" />);

    const input = screen.getByLabelText('Email address');
    const describedBy = input.getAttribute('aria-describedby');
    expect(describedBy).toBeTruthy();

    const helperEl = document.getElementById(describedBy!);
    expect(helperEl).not.toBeNull();
    expect(helperEl?.textContent).toBe('Enter your email');
  });

  it('Two Input instances with errors receive distinct error IDs', () => {
    render(
      <div>
        <Input label="Email" error="Email error" />
        <Input label="Password" error="Password error" />
      </div>
    );

    const emailInput = screen.getByLabelText('Email');
    const passwordInput = screen.getByLabelText('Password');

    const emailDescribedBy = emailInput.getAttribute('aria-describedby');
    const passwordDescribedBy = passwordInput.getAttribute('aria-describedby');

    expect(emailDescribedBy).toBeTruthy();
    expect(passwordDescribedBy).toBeTruthy();
    expect(emailDescribedBy).not.toBe(passwordDescribedBy);
  });

  it('Existing label association and styling assertions still pass', () => {
    render(<Input label="Email address" error="Wajib diisi." />);

    const message = screen.getByText('Wajib diisi.');
    expect(message.className).toContain('text-badgeText-error');
    expect(message.className).toContain('dark:text-badgeText-error-dark');
    expect(message.className).not.toContain('text-semantic-error');

    const input = screen.getByLabelText('Email address');
    expect(input.className).toContain('border-semantic-error');
    expect(input.className).toContain('focus:ring-semantic-error/30');
  });
});
