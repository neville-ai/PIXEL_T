import type { ReactNode } from 'react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import App from './App';
import { useAuth } from '@/context/AuthContext';
import { OPENING_SESSION_STORAGE_KEY } from '@/lib/openingTimeline';
import { listHistory } from '@/services/analysis';

vi.mock('@/context/AuthContext', () => ({
  // Passthrough provider: no Supabase session machinery in this unit test.
  AuthProvider: ({ children }: { children?: ReactNode }) => children ?? null,
  useAuth: vi.fn(),
}));

// Halaman yang dirender di balik shell memanggil listHistory(); beri tiruan
// agar unit test AppShell fokus pada perilaku chrome, bukan pada jaringan.
vi.mock('@/services/analysis', () => ({
  listHistory: vi.fn().mockResolvedValue({ items: [] }),
  getAnalysis: vi.fn(),
  createAnalysis: vi.fn(),
  deleteAnalysis: vi.fn(),
}));

beforeEach(() => {
  // jsdom in this project does not implement window.matchMedia, and the
  // existing useTheme hook (unmodified, outside this task's scope) calls it
  // unguarded from ThemeToggle inside AppShell. Provide a minimal shim so the
  // shell can render in this unit test.
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });

  window.sessionStorage.clear();
  // Keep the intro skipped so we assert chrome/layout, not animation state.
  window.sessionStorage.setItem(OPENING_SESSION_STORAGE_KEY, '1');
  vi.mocked(useAuth).mockReturnValue({
    user: null,
    session: null,
    loading: false,
    signIn: vi.fn(),
    signUp: vi.fn(),
    signOut: vi.fn(),
  } as unknown as ReturnType<typeof useAuth>);
});

afterEach(() => {
  cleanup();
});

function renderAt(path: string) {
  window.history.pushState({}, '', path);
  return render(<App />);
}

describe('App shell composition', () => {
  it('/login dirender TANPA global header, footer, atau disclaimer', () => {
    renderAt('/login');

    expect(screen.getByRole('heading', { level: 1, name: 'Welcome Back' })).toBeTruthy();
    expect(screen.queryByRole('banner')).toBeNull();
    expect(screen.queryByRole('contentinfo')).toBeNull();
  });

  it('/register tetap menggunakan AppShell (header & footer global)', () => {
    renderAt('/register');

    expect(screen.getByRole('banner')).toBeTruthy();
    expect(screen.getByRole('contentinfo')).toBeTruthy();
  });
});

describe('Theme bootstrap on bare routes', () => {
  it('tema dark tersimpan tetap diterapkan pada /login tanpa AppShell', () => {
    window.localStorage.setItem('pixel-t-theme', 'dark');
    renderAt('/login');

    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('tema light tersimpan menghapus class dark pada /login', () => {
    document.documentElement.classList.add('dark');
    window.localStorage.setItem('pixel-t-theme', 'light');
    renderAt('/login');

    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });
});

describe('AppShell: menu pengguna & konfirmasi sign-out (Phase 1)', () => {
  const signOutMock = vi.fn();

  beforeEach(() => {
    signOutMock.mockReset();
    signOutMock.mockResolvedValue(undefined);

    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 'user-1',
        email: 'nevilleawuy@gmail.com',
        user_metadata: { full_name: 'Dr. Neville' },
      },
      session: null,
      loading: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: signOutMock,
    } as unknown as ReturnType<typeof useAuth>);
  });

  it('header memakai nama display dari metadata Supabase, bukan nama hardcode', () => {
    renderAt('/dashboard');

    expect(screen.getByRole('button', { name: /Menu pengguna Dr\. Neville/i })).toBeTruthy();
  });

  it('dropdown menampilkan Account Information (inert) dan Sign Out', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));

    expect(screen.getByText('Account Information')).toBeTruthy();
    expect(screen.getByText('View your account information')).toBeTruthy();
    expect(screen.getByRole('menuitem', { name: /Sign Out/i })).toBeTruthy();
  });

  it('Sign Out pada menu mobile memakai token badgeText (P2-01)', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: 'Toggle navigation menu' }));

    const signOutItem = screen.getByRole('button', { name: /Sign Out/i });

    // Panel mobile: putih (tema terang) / #001620 (tema gelap). Teks pindah
    // ke pasangan token badgeText agar lolos 4.5:1 di kedua permukaan;
    // label, ikon, dan perilaku hover menu tidak berubah.
    expect(signOutItem.className).toContain('text-badgeText-error');
    expect(signOutItem.className).toContain('dark:text-badgeText-error-dark');
    expect(signOutItem.className).toContain('hover:bg-semantic-error/10');
    expect(signOutItem.className).not.toContain('text-semantic-error');
    expect(signOutItem.textContent).toContain('Sign Out');

    // Latar panel mobile tetap memakai token yang sama seperti sebelum batch.
    const panel = signOutItem.parentElement?.parentElement;
    expect(panel?.className).toContain('bg-white');
    expect(panel?.className).toContain('dark:bg-[#001620]');
  });

  it('kedua item menu memakai badge ikon 32x32 sesuai referensi', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));

    const badges = Array.from(screen.getByRole('menu').querySelectorAll('span')).filter((node) =>
      node.classList.contains('dark:h-8') && node.classList.contains('dark:w-8'),
    );

    expect(badges).toHaveLength(2);
    for (const badge of badges) {
      expect(badge.classList.contains('dark:rounded-[10px]')).toBe(true);
      expect(badge.classList.contains('dark:bg-[#102D3E]')).toBe(true);
      expect(badge.getAttribute('aria-hidden')).toBe('true');
      // Ikon di dalam badge memakai teal referensi, bukan token global.
      const icon = badge.querySelector('svg');
      expect(icon?.classList.contains('dark:text-[#18A6A6]')).toBe(true);
    }
  });

  it('dropdown dark memakai warna panel, border, dan divider hasil ukur referensi', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));

    const menu = screen.getByRole('menu');
    expect(menu.classList.contains('dark:bg-[#10222E]')).toBe(true);
    expect(menu.classList.contains('dark:border-[#1E3749]')).toBe(true);
    // Tidak boleh kembali ke warna lama yang keliru.
    expect(menu.classList.contains('dark:bg-[#041924]')).toBe(false);

    // Referensi hanya punya SATU divider: di bawah blok identitas.
    // Tidak ada pemisah antar item menu.
    expect(document.querySelectorAll('[class*="1E3645"]')).toHaveLength(1);
  });

  it('mode light dropdown tidak berubah: tanpa badge berwarna', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));

    const badges = Array.from(screen.getByRole('menu').querySelectorAll('span')).filter((node) =>
      node.classList.contains('dark:h-8') && node.classList.contains('dark:w-8'),
    );

    expect(badges).toHaveLength(2);
    for (const badge of badges) {
      // Ukuran & warna badge hanya aktif lewat variante dark; light tetap
      // memakai tata letak ikon lama (tanpa kotak, tanpa teal).
      expect(badge.classList.contains('h-8')).toBe(false);
      expect(badge.classList.contains('bg-[#102D3E]')).toBe(false);
      expect(badge.classList.contains('dark:bg-[#102D3E]')).toBe(true);

      const icon = badge.querySelector('svg');
      expect(icon?.classList.contains('text-[#18A6A6]')).toBe(false);
      expect(icon?.classList.contains('dark:text-[#18A6A6]')).toBe(true);
    }
  });

  it('Account Information TIDAK menambah route profile pada Phase 1', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));
    fireEvent.click(screen.getByText('Account Information'));

    expect(window.location.pathname).toBe('/dashboard');
    expect(signOutMock).not.toHaveBeenCalled();
  });

  it('Escape menutup dropdown tanpa membuka dialog sign-out', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));
    fireEvent.keyDown(document, { key: 'Escape' });

    expect(screen.queryByRole('menuitem', { name: /Sign Out/i })).toBeNull();
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('klik Sign Out membuka dialog konfirmasi', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));
    fireEvent.click(screen.getByRole('menuitem', { name: /Sign Out/i }));

    const dialog = screen.getByRole('dialog');
    expect(dialog.textContent).toContain('Are you sure you want to sign out?');
    expect(screen.getByRole('button', { name: 'No' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Yes' })).toBeTruthy();
    expect(signOutMock).not.toHaveBeenCalled();
  });

  it('membatalkan dialog sign-out TIDAK memanggil layanan logout', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));
    fireEvent.click(screen.getByRole('menuitem', { name: /Sign Out/i }));
    fireEvent.click(screen.getByRole('button', { name: 'No' }));

    expect(screen.queryByRole('dialog')).toBeNull();
    expect(signOutMock).not.toHaveBeenCalled();
    expect(window.location.pathname).toBe('/dashboard');
  });

  it('Escape pada dialog konfirmasi juga membatalkan sign-out', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));
    fireEvent.click(screen.getByRole('menuitem', { name: /Sign Out/i }));
    fireEvent.keyDown(document, { key: 'Escape' });

    expect(screen.queryByRole('dialog')).toBeNull();
    expect(signOutMock).not.toHaveBeenCalled();
  });

  it('mengonfirmasi sign-out memanggil layanan logout satu kali dan menutup dialog', async () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));
    fireEvent.click(screen.getByRole('menuitem', { name: /Sign Out/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Yes' }));

    // Flus microtask sampai rantai async `confirmSignOut` selesai.
    await act(async () => {
      for (let i = 0; i < 5; i += 1) {
        await Promise.resolve();
      }
    });

    // Layanan logout Supabase dipanggil tepat satu kali dan dialog ditutup.
    // (Redirect final ke /login tidak dapat diverifikasi di sini karena
    // `useAuth` di-mock statik — `PublicOnlyRoute` akan memantul kembali ke
    // /dashboard. Alur tersebut diverifikasi pada pemeriksaan browser.)
    expect(signOutMock).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('footer global tetap ada (tanpa disclaimer klinis global)', () => {
    renderAt('/dashboard');

    expect(screen.getByRole('contentinfo')).toBeTruthy();
    expect(screen.getByText(/Polyp Image eXplainable Learning Technology/)).toBeTruthy();
    expect(screen.getByText(/2026 PIXEL-T\. All rights reserved\./)).toBeTruthy();
    expect(screen.queryByText(/Disclaimer Medis/)).toBeNull();
  });

  it('dropdown tertutup saat klik di luar area menu', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));
    expect(screen.queryByRole('menuitem', { name: /Sign Out/i })).not.toBeNull();

    fireEvent.mouseDown(screen.getByRole('heading', { level: 1, name: 'Dashboard' }));

    expect(screen.queryByRole('menuitem', { name: /Sign Out/i })).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Phase 1 finalisasi — keputusan pengguna:
//   • CTA "New Analysis" memakai Deep Medical Navy (StyleGuide §29/§5.1),
//     bukan teal referensi.
//   • Token semantik success/error (§5.4) dipakai konsisten; warna referensi
//     (#39CD99 / #F06169 / #FF0303) tidak boleh bocor ke komponen mana pun.
// ---------------------------------------------------------------------------
describe('Phase 1 finalisasi: CTA primary & token semantik', () => {
  beforeEach(() => {
    vi.mocked(useAuth).mockReturnValue({
      user: {
        id: 'user-1',
        email: 'nevilleawuy@gmail.com',
        user_metadata: { full_name: 'Dr. Neville' },
      },
      session: null,
      loading: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>);

    vi.mocked(listHistory).mockResolvedValue({ items: [] });
  });

  afterEach(() => {
    // Kembalikan kondisi default agar fixture tidak bocor ke test lain.
    vi.mocked(listHistory).mockResolvedValue({ items: [] });
  });

  /**
   * CTA "New Analysis" pada panel Start New Analysis. Dinilai lewat heading
   * panelnya karena link nav header/mobile juga menuju /analysis/new dan
   * namanya sama persis, sehingga query by role tunggal akan ambigu.
   */
  function newAnalysisCta(): HTMLAnchorElement {
    const heading = screen.getByRole('heading', { name: 'Start New Analysis' });
    const link = heading.closest('section')?.querySelector('a');
    if (!link) throw new Error('CTA New Analysis tidak ditemukan pada panel Start New Analysis');
    return link as HTMLAnchorElement;
  }

  it('CTA menuju /analysis/new dengan accessible name "New Analysis"', () => {
    renderAt('/dashboard');

    const cta = newAnalysisCta();

    expect(cta.getAttribute('href')).toBe('/analysis/new');
    expect(cta.textContent?.trim()).toBe('New Analysis');
    // Ikon Plus dekoratif: tidak boleh menambah noise pada accessible name.
    expect(cta.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true');
  });

  it('CTA memakai palet primary yang disetujui; kelas accent lama sudah hilang', () => {
    renderAt('/dashboard');

    const cta = newAnalysisCta();

    // rest / hover / press — ketiganya token palet primary yang valid.
    expect(cta.classList.contains('bg-primary-900')).toBe(true); // #0F3D56 §29
    expect(cta.classList.contains('hover:bg-primary-700')).toBe(true);
    expect(cta.classList.contains('active:bg-primary-800')).toBe(true); // §5.1

    // Guard: keadaan diam teal, dan active:bg-accent-800 yang tidak pernah
    // ada tokennya (skala accent berhenti di 700) tidak boleh kembali muncul.
    expect(cta.classList.contains('bg-accent-600')).toBe(false);
    expect(cta.classList.contains('hover:bg-accent-700')).toBe(false);
    expect(cta.classList.contains('active:bg-accent-800')).toBe(false);

    // Perilaku yang dipertahankan: teks putih & visibilitas fokus.
    expect(cta.classList.contains('text-white')).toBe(true);
    expect(cta.classList.contains('focus-visible:ring-2')).toBe(true);
    expect(cta.classList.contains('focus-visible:ring-accent-500')).toBe(true);
  });

  it('CTA tetap link biasa yang dapat difokus lewat keyboard', () => {
    renderAt('/dashboard');

    const cta = newAnalysisCta();

    expect(cta.tagName).toBe('A');
    expect(cta.hasAttribute('disabled')).toBe(false);

    cta.focus();
    expect(document.activeElement).toBe(cta);
  });

  it('kartu dashboard memakai token semantic success/error, bukan warna referensi', async () => {
    // Data dari API tiruan hanya dipakai oleh unit test; thumbnail sengaja
    // null sehingga tidak ada citra medis contoh yang ikut dirender.
    vi.mocked(listHistory).mockResolvedValue({
      items: [
        {
          id: 'an-1',
          created_at: '2026-10-02T14:20:00Z',
          status: 'completed',
          original_filename: 'colonoscopy_case_0842.jpg',
          thumbnail_url: null,
          segmentation_status: 'detected',
        },
        {
          id: 'an-2',
          created_at: '2026-10-01T11:30:00Z',
          status: 'failed',
          original_filename: 'sigmoidoscopy_seg_012.png',
          thumbnail_url: null,
          segmentation_status: 'not_detected',
        },
      ],
    });

    renderAt('/dashboard');

    const okBadge = await screen.findByText('Selesai');
    // Teks badge success memakai token badgeText (turunan hue success yang
    // sama) agar lolos 4.5:1 pada tint /10; border/tint tetap semantic.
    expect(okBadge.classList.contains('text-badgeText-success')).toBe(true);
    expect(okBadge.classList.contains('dark:text-badgeText-success-dark')).toBe(true);
    expect(okBadge.classList.contains('border-semantic-success/20')).toBe(true);
    expect(okBadge.classList.contains('bg-semantic-success/10')).toBe(true);
    expect(okBadge.classList.contains('text-[#39CD99]')).toBe(false);

    const badBadge = await screen.findByText('Gagal');
    expect(badBadge.classList.contains('text-badgeText-error')).toBe(true);
    expect(badBadge.classList.contains('dark:text-badgeText-error-dark')).toBe(true);
    expect(badBadge.classList.contains('border-semantic-error/20')).toBe(true);
    expect(badBadge.classList.contains('bg-semantic-error/10')).toBe(true);
    expect(badBadge.classList.contains('text-[#F06169]')).toBe(false);

    // Ikon placeholder & tautan coba-lagi di luar cakupan perbaikan badge:
    // token semantic asli tetap (ikon 32px lolos 3:1, link 4.60:1 pada putih).
    expect(document.querySelector('svg.w-8.h-8.text-semantic-error')).not.toBeNull();
    expect(screen.getByText('Coba Lagi').classList.contains('text-semantic-error')).toBe(true);

    // Nol warna referensi di seluruh dokumen yang dirender.
    expect(document.querySelector('[class*="#39CD99"]')).toBeNull();
    expect(document.querySelector('[class*="#F06169"]')).toBeNull();
    expect(document.querySelector('[class*="#FF0303"]')).toBeNull();
  });

  it('tombol Yes sign-out memakai token error StyleGuide, bukan #FF0303 referensi', () => {
    renderAt('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /Menu pengguna/i }));
    fireEvent.click(screen.getByRole('menuitem', { name: /Sign Out/i }));

    const yes = screen.getByRole('button', { name: 'Yes' });
    expect(yes.classList.contains('bg-semantic-error')).toBe(true);
    expect(yes.classList.contains('bg-[#FF0303]')).toBe(false);
    // Mode terang dialog tetap memakai permukaan putih seperti referensi.
    expect(screen.getByRole('dialog').className).toContain('bg-white');
  });
});
