import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes, type InitialEntry } from 'react-router-dom';
import { Login } from './Login';
import { useAuth } from '@/context/AuthContext';
import { resetPasswordUser } from '@/services/auth';
import {
  noteOpeningUnmount,
  OPENING_SESSION_STORAGE_KEY,
  REMEMBERED_EMAIL_STORAGE_KEY,
} from '@/lib/openingTimeline';

vi.mock('@/context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/services/auth', () => ({
  resetPasswordUser: vi.fn(),
}));

const signInMock = vi.fn<
  (email: string, password: string, selectedRole?: 'admin' | 'doctor') => Promise<{ error?: string }>
>();

function mockAuthContext(overrides: Partial<ReturnType<typeof useAuth>> = {}): void {
  vi.mocked(useAuth).mockReturnValue({
    user: null,
    session: null,
    loading: false,
    role: null,
    accountStatus: null,
    signIn: signInMock,
    signUp: vi.fn(),
    signOut: vi.fn(),
    ...overrides,
  } as unknown as ReturnType<typeof useAuth>);
}

function renderLogin(initialEntries: InitialEntry[] = ['/login']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<div>Dashboard Page</div>} />
        <Route path="/history" element={<div>History Page</div>} />
        <Route path="/admin" element={<div>Admin Dashboard</div>} />
      </Routes>
    </MemoryRouter>
  );
}

function fillAndSubmit(email: string, password: string): void {
  fireEvent.change(screen.getByLabelText('Email address'), { target: { value: email } });
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: password } });
  fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));
}

beforeEach(() => {
  window.sessionStorage.clear();
  window.localStorage.clear();
  // Default: the intro has already been played this tab session, so form
  // tests exercise the normal (unlocked) Login.
  window.sessionStorage.setItem(OPENING_SESSION_STORAGE_KEY, '1');

  signInMock.mockReset();
  signInMock.mockResolvedValue({});
  vi.mocked(resetPasswordUser).mockReset();
  vi.mocked(resetPasswordUser).mockResolvedValue({ data: null, error: null });
  mockAuthContext();
});

afterEach(() => {
  cleanup();
});

describe('Login — locked two-panel copy & structure', () => {
  it('menampilkan seluruh copy desain yang dikunci beserta branding panel', () => {
    renderLogin();

    expect(screen.getByRole('heading', { level: 1, name: 'Welcome Back' })).toBeTruthy();
    expect(screen.getByText('Sign in to your PIXEL-T account')).toBeTruthy();
    expect(screen.getByLabelText('Email address')).toBeTruthy();
    expect(screen.getByLabelText('Password')).toBeTruthy();
    expect(screen.getByLabelText('Remember my email')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Forgot password?' })).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeTruthy();
    expect(screen.getByText(/Don't have an account/)).toBeTruthy();

    const registerLink = screen.getByRole('link', { name: 'Register' });
    expect(registerLink.getAttribute('href')).toBe('/register');

    // Branding panel
    expect(screen.getByText('Clinical AI Analysis')).toBeTruthy();
    expect(screen.getByText(/AI-powered analysis/)).toBeTruthy();
    expect(screen.getByAltText('PIXEL-T')).toBeTruthy();
  });

  it('tetap merender form dan menyediakan fallback ketika asset logo gagal dimuat', () => {
    renderLogin();

    const logo = screen.getByAltText('PIXEL-T');
    fireEvent.error(logo);

    // Accessible text fallback replaces the broken image; form still usable.
    expect(screen.getByRole('img', { name: 'PIXEL-T' })).toBeTruthy();
    expect(screen.queryByAltText('PIXEL-T')).toBeNull();
    expect(screen.getByLabelText('Email address')).toBeTruthy();
  });
});

describe('Login — authentication flow (existing service contract)', () => {
  it('memanggil signIn existing dengan kredensial yang diketik dan redirect ke state.from', async () => {
    renderLogin([{ pathname: '/login', state: { from: { pathname: '/history' } } }]);

    fillAndSubmit('dokter@rumah-sakit.id', 'rahasia123');

    expect(signInMock).toHaveBeenCalledTimes(1);
    expect(signInMock).toHaveBeenCalledWith('dokter@rumah-sakit.id', 'rahasia123', 'doctor');
    expect(await screen.findByText('History Page')).toBeTruthy();
  });

  it('redirect ke /dashboard ketika tidak ada state.from', async () => {
    renderLogin();

    fillAndSubmit('dokter@rumah-sakit.id', 'rahasia123');

    expect(await screen.findByText('Dashboard Page')).toBeTruthy();
  });

  it('validasi berjalan — signIn tidak dipanggil saat email kosong', async () => {
    renderLogin();

    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('Silakan masukkan alamat email Anda.');
    expect(signInMock).not.toHaveBeenCalled();
  });

  it('validasi berjalan — pesan error ketika password kosong', async () => {
    renderLogin();

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'dokter@rumah-sakit.id' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('Silakan masukkan kata sandi Anda.');
    expect(signInMock).not.toHaveBeenCalled();
  });

  it('error autentikasi dari layanan ditampilkan dan user tetap di Login', async () => {
    signInMock.mockResolvedValue({
      error: 'Email atau kata sandi yang Anda masukkan salah.',
    });
    renderLogin();

    fillAndSubmit('dokter@rumah-sakit.id', 'salah');

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('Email atau kata sandi yang Anda masukkan salah.');
    expect(screen.getByRole('heading', { level: 1, name: 'Welcome Back' })).toBeTruthy();

    // P2-01: foreground alert pindah ke token badgeText (4.5:1 pada tint
    // /10 di kedua tema); latar dan border tetap memakai token semantic.
    expect(alert.className).toContain('text-badgeText-error');
    expect(alert.className).toContain('dark:text-badgeText-error-dark');
    expect(alert.className).toContain('bg-semantic-error/10');
    expect(alert.className).toContain('border-semantic-error/30');
    expect(alert.className).not.toContain('text-semantic-error');
  });

  it('loading state mencegah submit ganda', async () => {
    let resolveSignIn!: (value: { error?: string }) => void;
    signInMock.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveSignIn = resolve;
        })
    );
    renderLogin();

    fillAndSubmit('dokter@rumah-sakit.id', 'rahasia123');

    const submitButton = screen.getByRole('button', { name: 'Sign In' });
    expect((submitButton as HTMLButtonElement).disabled).toBe(true);

    fireEvent.click(submitButton);
    expect(signInMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveSignIn({});
    });
    expect(await screen.findByText('Dashboard Page')).toBeTruthy();
  });
});

describe('Login — password visibility toggle', () => {
  it('toggle show/hide password berfungsi dan punya accessible name', () => {
    renderLogin();

    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement;
    expect(passwordInput.type).toBe('password');

    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));
    expect(passwordInput.type).toBe('text');
    expect(screen.getByRole('button', { name: 'Hide password' })).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Hide password' }));
    expect(passwordInput.type).toBe('password');
  });
});

describe('Login — Remember my email (e-mail only)', () => {
  it('menyimpan email, bukan password', () => {
    renderLogin();

    fireEvent.click(screen.getByLabelText('Remember my email'));
    fillAndSubmit('dokter@rumah-sakit.id', 'rahasia123');

    expect(window.localStorage.getItem(REMEMBERED_EMAIL_STORAGE_KEY)).toBe(
      'dokter@rumah-sakit.id'
    );
    // Exactly one stored key — the password is never persisted anywhere.
    expect(window.localStorage.length).toBe(1);
    expect(window.localStorage.getItem(REMEMBERED_EMAIL_STORAGE_KEY)).not.toContain(
      'rahasia123'
    );
  });

  it('prefill email + checkbox tercentang dari penyimpanan sebelumnya', () => {
    window.localStorage.setItem(REMEMBERED_EMAIL_STORAGE_KEY, 'ingat@rumah-sakit.id');

    renderLogin();

    expect((screen.getByLabelText('Email address') as HTMLInputElement).value).toBe(
      'ingat@rumah-sakit.id'
    );
    expect((screen.getByLabelText('Remember my email') as HTMLInputElement).checked).toBe(true);
  });

  it('checkbox tidak dicentang -> email tersimpan dibersihkan', () => {
    window.localStorage.setItem(REMEMBERED_EMAIL_STORAGE_KEY, 'lama@rumah-sakit.id');

    renderLogin();
    expect((screen.getByLabelText('Remember my email') as HTMLInputElement).checked).toBe(true);

    fireEvent.click(screen.getByLabelText('Remember my email'));
    expect((screen.getByLabelText('Remember my email') as HTMLInputElement).checked).toBe(false);

    fillAndSubmit('dokter@rumah-sakit.id', 'rahasia123');

    expect(window.localStorage.getItem(REMEMBERED_EMAIL_STORAGE_KEY)).toBeNull();
  });
});

describe('Login — forgot password (real Supabase reset request)', () => {
  it('memanggil resetPasswordUser dan menampilkan pesan sukses yang netral', async () => {
    renderLogin();

    fireEvent.click(screen.getByRole('button', { name: 'Forgot password?' }));
    expect(screen.getByRole('heading', { level: 1, name: 'Reset Your Password' })).toBeTruthy();

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'dokter@rumah-sakit.id' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Send Reset Link' }));

    const status = await screen.findByRole('status');
    expect(status.textContent).toContain(
      'If an account exists for this email, a password reset link has been sent.'
    );
    expect(resetPasswordUser).toHaveBeenCalledTimes(1);
    expect(resetPasswordUser).toHaveBeenCalledWith('dokter@rumah-sakit.id');
    // Sign-in service must not be involved in the reset request.
    expect(signInMock).not.toHaveBeenCalled();

    // Kembali ke form sign-in.
    fireEvent.click(screen.getByRole('button', { name: 'Back to sign in' }));
    expect(screen.getByRole('heading', { level: 1, name: 'Welcome Back' })).toBeTruthy();
  });

  it('kegagalan request TIDAK diklaim sebagai email terkirim', async () => {
    vi.mocked(resetPasswordUser).mockResolvedValue({
      data: null,
      error: 'Gagal terhubung ke server autentikasi. Periksa koneksi internet Anda.',
    });
    renderLogin();

    fireEvent.click(screen.getByRole('button', { name: 'Forgot password?' }));
    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'dokter@rumah-sakit.id' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Send Reset Link' }));

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('Gagal terhubung ke server autentikasi');
    expect(screen.queryByRole('status')).toBeNull();
  });

  it('validasi email pada alur reset', async () => {
    renderLogin();

    fireEvent.click(screen.getByRole('button', { name: 'Forgot password?' }));
    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'bukan-email' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Send Reset Link' }));

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain('Please enter a valid email address.');
    expect(resetPasswordUser).not.toHaveBeenCalled();
  });
});

describe('Login — opening animation playback rules', () => {
  it('intro DIPUTAR pada kunjungan pertama (belum ada flag) dan form terkunci sampai reveal', () => {
    // beforeEach sets the flag; clear it to simulate a fresh tab session.
    window.sessionStorage.clear();

    renderLogin();

    const intro = document.querySelector('.pixel-t-intro');
    expect(intro).not.toBeNull();
    expect(intro?.getAttribute('aria-hidden')).toBe('true');

    // Flag recorded as early as playback starts.
    expect(window.sessionStorage.getItem(OPENING_SESSION_STORAGE_KEY)).toBe('1');

    // Form is not interactable before the reveal stage.
    const emailInput = screen.getByLabelText('Email address') as HTMLInputElement;
    expect(emailInput.disabled).toBe(true);
    // The panel is aria-hidden during the intro (role queries must opt into
    // hidden elements to even find it).
    const submitButton = screen.getByRole('button', { name: 'Sign In', hidden: true });
    expect(submitButton.getAttribute('disabled')).not.toBeNull();
  });

  it('revisit setelah flag tercatat TIDAK memutar intro lagi (mis. setelah login gagal/logout)', () => {
    // Earlier test recorded playback (in-memory) and the flag exists.
    window.sessionStorage.setItem(OPENING_SESSION_STORAGE_KEY, '1');
    // A genuine revisit happens well after the previous unmount.
    noteOpeningUnmount(Date.now() - 5_000);

    renderLogin();

    expect(document.querySelector('.pixel-t-intro')).toBeNull();
    const emailInput = screen.getByLabelText('Email address') as HTMLInputElement;
    expect(emailInput.disabled).toBe(false);
  });
});

describe('Login — role selector dropdown', () => {
  it('default role adalah doctor dan dropdown dapat dibuka', () => {
    renderLogin();

    // Default selected role should be Doctor
    expect(screen.getByText('Dokter')).toBeTruthy();

    // Dropdown button is present with label "Masuk sebagai"
    expect(screen.getByText('Masuk sebagai')).toBeTruthy();
  });

  it('dropdown terbuka dan menampilkan pilihan Admin serta Dokter', () => {
    renderLogin();

    const dropdownButton = screen.getByRole('button', { expanded: false });
    fireEvent.click(dropdownButton);

    // Both options should be visible
    expect(screen.getAllByRole('option').length).toBe(2);
  });

  it('pilihan Admin dapat dipilih dan dropdown menutup', () => {
    renderLogin();

    const dropdownButton = screen.getByRole('button', { expanded: false });
    fireEvent.click(dropdownButton);

    // Use getAllByRole and pick first option (Admin)
    const options = screen.getAllByRole('option');
    fireEvent.click(options[0]);

    // Dropdown should close (button no longer expanded)
    expect(screen.getByRole('button', { expanded: false })).toBeTruthy();
    // Button should show "Admin"
    expect(screen.getByText('Admin')).toBeTruthy();
  });

  it('pilihan Dokter dapat dipilih ulang', () => {
    renderLogin();

    // Switch to admin first
    const dropdownButton = screen.getByRole('button', { expanded: false });
    fireEvent.click(dropdownButton);
    screen.getAllByRole('option')[0].click();
    expect(screen.getByText('Admin')).toBeTruthy();

    // Switch back to doctor — click button again
    const buttonAfterAdmin = screen.getByRole('button', { expanded: true });
    fireEvent.click(buttonAfterAdmin);
    screen.getAllByRole('option')[1].click();
    expect(screen.getByText('Dokter')).toBeTruthy();
  });

  it('signIn dipanggil dengan selectedRole yang benar saat submit', async () => {
    renderLogin();

    // Select Admin role
    const dropdownButton = screen.getByRole('button', { expanded: false });
    fireEvent.click(dropdownButton);
    screen.getAllByRole('option')[0].click();
    expect(screen.getByText('Admin')).toBeTruthy();

    fillAndSubmit('admin@rumah-sakit.id', 'rahasia123');

    expect(signInMock).toHaveBeenCalledTimes(1);
    expect(signInMock).toHaveBeenCalledWith('admin@rumah-sakit.id', 'rahasia123', 'admin');
  });

  it('signIn dipanggil dengan selectedRole doctor oleh default', async () => {
    renderLogin();

    fillAndSubmit('dokter@rumah-sakit.id', 'rahasia123');

    expect(signInMock).toHaveBeenCalledTimes(1);
    expect(signInMock).toHaveBeenCalledWith('dokter@rumah-sakit.id', 'rahasia123', 'doctor');
  });
});

describe('Login — role mismatch error handling', () => {
  it('menolak login Admin ketika user sebenarnya adalah dokter', async () => {
    // signIn returns a mismatch error
    signInMock.mockResolvedValue({
      error: 'Jenis akun tidak sesuai dengan hak akses akun Anda. Silakan pilih jenis akun yang benar.',
    });
    renderLogin();

    // Select Admin role
    const dropdownButton = screen.getByRole('button', { expanded: false });
    fireEvent.click(dropdownButton);
    screen.getAllByRole('option')[0].click();

    fillAndSubmit('dokter@rumah-sakit.id', 'rahasia123');

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain(
      'Jenis akun tidak sesuai dengan hak akses akun Anda. Silakan pilih jenis akun yang benar.'
    );
    expect(screen.getByRole('heading', { level: 1, name: 'Welcome Back' })).toBeTruthy();
  });

  it('menolak login Dokter ketika user sebenarnya adalah admin', async () => {
    // signIn returns a mismatch error
    signInMock.mockResolvedValue({
      error: 'Jenis akun tidak sesuai dengan hak akses akun Anda. Silakan pilih jenis akun yang benar.',
    });
    renderLogin();

    fillAndSubmit('admin@rumah-sakit.id', 'rahasia123');

    const alert = await screen.findByRole('alert');
    expect(alert.textContent).toContain(
      'Jenis akun tidak sesuai dengan hak akses akun Anda. Silakan pilih jenis akun yang benar.'
    );
  });

  it('admin yang memilih Admin berhasil login dan diarahkan ke /admin', async () => {
    mockAuthContext({ role: 'admin', accountStatus: null });
    signInMock.mockResolvedValue({});
    renderLogin();

    // Ensure Admin is selected
    const dropdownButton = screen.getByRole('button', { expanded: false });
    fireEvent.click(dropdownButton);
    screen.getAllByRole('option')[0].click();

    fillAndSubmit('admin@rumah-sakit.id', 'rahasia123');

    expect(await screen.findByText('Admin Dashboard')).toBeTruthy();
  });

  it('dokter approved yang memilih Dokter berhasil login dan diarahkan ke /dashboard', async () => {
    mockAuthContext({ role: 'doctor', accountStatus: 'approved' });
    signInMock.mockResolvedValue({});
    renderLogin();

    fillAndSubmit('dokter@rumah-sakit.id', 'rahasia123');

    expect(await screen.findByText('Dashboard Page')).toBeTruthy();
  });

  it('dokter pending tetap melihat pesan tunggu persetujuan', async () => {
    mockAuthContext({ role: 'doctor', accountStatus: 'pending' });
    signInMock.mockResolvedValue({});
    renderLogin();

    fillAndSubmit('dokter-pending@rumah-sakit.id', 'rahasia123');

    // Should redirect back to login with pending state — look for the status box
    const pendingStatus = await screen.findByRole('status');
    expect(pendingStatus.textContent).toContain('sedang menunggu persetujuan dari administrator');
  });
});
