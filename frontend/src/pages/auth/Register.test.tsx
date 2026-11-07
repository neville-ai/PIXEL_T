import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { Register } from './Register';
import { useAuth } from '@/context/AuthContext';

vi.mock('@/context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const signUpMock = vi.fn<
  (
    email: string,
    password: string,
    fullName?: string,
    hospitalName?: string,
    doctorSpecialty?: string
  ) => Promise<{
    error?: string;
    message?: string;
    requiresEmailConfirmation?: boolean;
  }>
>();

function mockAuthContext(): void {
  vi.mocked(useAuth).mockReturnValue({
    user: null,
    session: null,
    loading: false,
    signIn: vi.fn(),
    signUp: signUpMock,
    signOut: vi.fn(),
    role: null,
    accountStatus: null,
  } as unknown as ReturnType<typeof useAuth>);
}

function renderRegister() {
  return render(
    <MemoryRouter initialEntries={['/register']}>
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('Register Page — Design & Structure', () => {
  beforeEach(() => {
    signUpMock.mockReset();
    mockAuthContext();
  });

  afterEach(() => {
    cleanup();
  });

  it('renders doctor icon as main header image', () => {
    renderRegister();
    const doctorImg = screen.getByAltText('Doctor Icon');
    expect(doctorImg).toBeTruthy();
    expect(doctorImg.getAttribute('src')).toBeTruthy();
  });

  it('does NOT render the Supabase Auth badge', () => {
    renderRegister();
    expect(screen.queryByText(/^SUPABASE AUTH$/i)).toBeNull();
  });

  it('renders title and clinical description correctly', () => {
    renderRegister();
    expect(screen.getByRole('heading', { name: 'Pendaftaran Akun PIXEL-T' })).toBeTruthy();
    expect(screen.getByText('Registrasi akun pengguna untuk tenaga medis dan klinisi')).toBeTruthy();
  });

  it('renders all required form inputs including hospital name and doctor specialty', () => {
    renderRegister();
    expect(screen.getByLabelText('Nama Lengkap')).toBeTruthy();
    expect(screen.getByLabelText('Email Pengguna')).toBeTruthy();
    expect(screen.getByLabelText('NAMA RUMAH SAKIT')).toBeTruthy();
    expect(screen.getByPlaceholderText('Contoh: RSUP Prof. Dr. R. D. Kandou')).toBeTruthy();
    expect(screen.getByLabelText('BIDANG KEAHLIAN DOKTER')).toBeTruthy();
    expect(screen.getByPlaceholderText('Contoh: Patologi Anatomi')).toBeTruthy();
    expect(screen.getByLabelText('Kata Sandi')).toBeTruthy();
    expect(screen.getByLabelText('Konfirmasi Kata Sandi')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Daftar' })).toBeTruthy();
  });

  it('validates empty inputs and enforces required professional fields', async () => {
    renderRegister();
    const submitBtn = screen.getByRole('button', { name: 'Daftar' });

    // 1. Empty full name
    fireEvent.submit(submitBtn.closest('form')!);
    expect((await screen.findByRole('alert')).textContent).toContain('Silakan masukkan nama lengkap Anda.');

    // 2. Fill name, empty email
    fireEvent.change(screen.getByLabelText('Nama Lengkap'), { target: { value: 'dr. Jane Doe' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Daftar' }).closest('form')!);
    expect((await screen.findByRole('alert')).textContent).toContain('Silakan masukkan alamat email Anda.');

    // 3. Invalid email
    fireEvent.change(screen.getByLabelText('Email Pengguna'), { target: { value: 'invalid-email' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Daftar' }).closest('form')!);
    expect((await screen.findByRole('alert')).textContent).toContain('Format alamat email tidak valid.');

    // 4. Empty hospital
    fireEvent.change(screen.getByLabelText('Email Pengguna'), { target: { value: 'jane@hospital.com' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Daftar' }).closest('form')!);
    expect((await screen.findByRole('alert')).textContent).toContain('Silakan masukkan nama rumah sakit Anda.');

    // 5. Empty specialty
    fireEvent.change(screen.getByLabelText('NAMA RUMAH SAKIT'), { target: { value: 'RSUP Dr. Sardjito' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Daftar' }).closest('form')!);
    expect((await screen.findByRole('alert')).textContent).toContain('Silakan masukkan bidang keahlian dokter Anda.');

    // 6. Empty password
    fireEvent.change(screen.getByLabelText('BIDANG KEAHLIAN DOKTER'), { target: { value: 'Gastroenterologi' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Daftar' }).closest('form')!);
    expect((await screen.findByRole('alert')).textContent).toContain('Silakan masukkan kata sandi Anda.');

    // 7. Password too short (< 6 chars)
    fireEvent.change(screen.getByLabelText('Kata Sandi'), { target: { value: '123' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Daftar' }).closest('form')!);
    expect((await screen.findByRole('alert')).textContent).toContain('Kata sandi harus memiliki minimal 6 karakter.');

    // 8. Password mismatch
    fireEvent.change(screen.getByLabelText('Kata Sandi'), { target: { value: 'Secret123' } });
    fireEvent.change(screen.getByLabelText('Konfirmasi Kata Sandi'), { target: { value: 'Mismatch999' } });
    fireEvent.submit(screen.getByRole('button', { name: 'Daftar' }).closest('form')!);
    expect((await screen.findByRole('alert')).textContent).toContain('Konfirmasi kata sandi tidak cocok dengan kata sandi.');

    // Client-side validation never reaches the auth service.
    expect(signUpMock).not.toHaveBeenCalled();
  });

  it('submits registration and renders a focused success card with login as primary action', async () => {
    signUpMock.mockResolvedValueOnce({
      message: 'Pendaftaran akun PIXEL-T Anda telah diproses.',
      requiresEmailConfirmation: true,
    });

    renderRegister();

    fireEvent.change(screen.getByLabelText('Nama Lengkap'), { target: { value: 'dr. Alexander' } });
    fireEvent.change(screen.getByLabelText('Email Pengguna'), { target: { value: 'alex@hospital.org' } });
    fireEvent.change(screen.getByLabelText('NAMA RUMAH SAKIT'), { target: { value: 'RSUP Prof. Dr. R. D. Kandou' } });
    fireEvent.change(screen.getByLabelText('BIDANG KEAHLIAN DOKTER'), { target: { value: 'Patologi Anatomi' } });
    fireEvent.change(screen.getByLabelText('Kata Sandi'), { target: { value: 'PasswordSecure1' } });
    fireEvent.change(screen.getByLabelText('Konfirmasi Kata Sandi'), { target: { value: 'PasswordSecure1' } });

    fireEvent.submit(screen.getByRole('button', { name: 'Daftar' }).closest('form')!);

    await waitFor(() => {
      expect(signUpMock).toHaveBeenCalledWith(
        'alex@hospital.org',
        'PasswordSecure1',
        'dr. Alexander',
        'RSUP Prof. Dr. R. D. Kandou',
        'Patologi Anatomi'
      );
    });

    // Title is the primary focus and uses a single, clear success status.
    const heading = await screen.findByRole('heading', { level: 1, name: 'Registrasi Berhasil' });
    expect(heading).toBeTruthy();
    const status = screen.getByRole('status');
    expect(status.textContent).toContain('Registrasi Berhasil');
    expect(status.textContent).toContain('Pendaftaran akun PIXEL-T Anda telah diproses.');

    // Neutral e-mail confirmation instruction including the submitted address.
    const emailSpan = screen.getByText('alex@hospital.org');
    const note = emailSpan.closest('p');
    expect(note?.textContent).toContain('belum terdaftar');
    expect(note?.textContent).toContain('tautan konfirmasi');
    expect(note?.textContent).toContain('Jika sudah terdaftar, silakan langsung masuk');

    // Single primary CTA to Login, and no duplicated "already have an account" CTA.
    const loginLink = screen.getByRole('link', { name: /Masuk ke PIXEL-T/i });
    expect(loginLink.getAttribute('href')).toBe('/login');
    expect(screen.queryByText('Sudah memiliki akun terdaftar?')).toBeNull();

    // Alternative action returns to an empty registration form.
    fireEvent.click(screen.getByRole('button', { name: 'Daftar dengan akun lain' }));
    expect(screen.getByRole('button', { name: 'Daftar' })).toBeTruthy();
    expect((screen.getByLabelText('Email Pengguna') as HTMLInputElement).value).toBe('');
  });

  it('omits the e-mail confirmation note when a session is created immediately', async () => {
    signUpMock.mockResolvedValueOnce({
      message: 'Akun PIXEL-T Anda berhasil dibuat dan sesi Anda sudah aktif.',
      requiresEmailConfirmation: false,
    });

    renderRegister();

    fireEvent.change(screen.getByLabelText('Nama Lengkap'), { target: { value: 'dr. Alexander' } });
    fireEvent.change(screen.getByLabelText('Email Pengguna'), { target: { value: 'active@hospital.org' } });
    fireEvent.change(screen.getByLabelText('NAMA RUMAH SAKIT'), { target: { value: 'RSUP Dr. Sardjito' } });
    fireEvent.change(screen.getByLabelText('BIDANG KEAHLIAN DOKTER'), { target: { value: 'Gastroenterologi' } });
    fireEvent.change(screen.getByLabelText('Kata Sandi'), { target: { value: 'PasswordSecure1' } });
    fireEvent.change(screen.getByLabelText('Konfirmasi Kata Sandi'), { target: { value: 'PasswordSecure1' } });

    fireEvent.submit(screen.getByRole('button', { name: 'Daftar' }).closest('form')!);

    await screen.findByRole('heading', { level: 1, name: 'Registrasi Berhasil' });
    expect(screen.queryByText(/Tautan konfirmasi/)).toBeNull();
  });

  it('shows error banner when signUp returns an error', async () => {
    signUpMock.mockResolvedValueOnce({
      error: 'Alamat email sudah terdaftar. Silakan masuk atau gunakan alamat email lain.',
    });

    renderRegister();

    fireEvent.change(screen.getByLabelText('Nama Lengkap'), { target: { value: 'dr. Alexander' } });
    fireEvent.change(screen.getByLabelText('Email Pengguna'), { target: { value: 'registered@hospital.org' } });
    fireEvent.change(screen.getByLabelText('NAMA RUMAH SAKIT'), { target: { value: 'RSUP Hasan Sadikin' } });
    fireEvent.change(screen.getByLabelText('BIDANG KEAHLIAN DOKTER'), { target: { value: 'Bedah Digestif' } });
    fireEvent.change(screen.getByLabelText('Kata Sandi'), { target: { value: 'PasswordSecure1' } });
    fireEvent.change(screen.getByLabelText('Konfirmasi Kata Sandi'), { target: { value: 'PasswordSecure1' } });

    fireEvent.submit(screen.getByRole('button', { name: 'Daftar' }).closest('form')!);

    const alertBanner = await screen.findByRole('alert');
    expect(alertBanner.textContent).toContain(
      'Alamat email sudah terdaftar. Silakan masuk atau gunakan alamat email lain.'
    );
  });
});

describe('Register Page — Show/Hide Password', () => {
  beforeEach(() => {
    signUpMock.mockReset();
    mockAuthContext();
  });

  afterEach(() => {
    cleanup();
  });

  it('password fields are hidden by default', () => {
    renderRegister();
    const passwordInput = screen.getByLabelText('Kata Sandi') as HTMLInputElement;
    const confirmInput = screen.getByLabelText('Konfirmasi Kata Sandi') as HTMLInputElement;
    expect(passwordInput.type).toBe('password');
    expect(confirmInput.type).toBe('password');
  });

  it('toggles password visibility when the eye icon is clicked', async () => {
    renderRegister();
    const passwordInput = screen.getByLabelText('Kata Sandi') as HTMLInputElement;
    const showBtn = screen.getByRole('button', { name: 'Show password' });

    expect(passwordInput.type).toBe('password');
    fireEvent.click(showBtn);
    expect(passwordInput.type).toBe('text');
    expect(showBtn.getAttribute('aria-label')).toBe('Hide password');
    expect(showBtn.getAttribute('aria-pressed')).toBe('true');

    // Hide again
    fireEvent.click(showBtn);
    expect(passwordInput.type).toBe('password');
    expect(showBtn.getAttribute('aria-label')).toBe('Show password');
    expect(showBtn.getAttribute('aria-pressed')).toBe('false');
  });

  it('toggles confirm password visibility independently', async () => {
    renderRegister();
    const confirmInput = screen.getByLabelText('Konfirmasi Kata Sandi') as HTMLInputElement;
    const showBtn = screen.getByRole('button', { name: 'Show confirm password' });

    expect(confirmInput.type).toBe('password');
    fireEvent.click(showBtn);
    expect(confirmInput.type).toBe('text');

    // Password field unaffected
    const passwordInput = screen.getByLabelText('Kata Sandi') as HTMLInputElement;
    expect(passwordInput.type).toBe('password');
  });

  it('both toggle buttons exist and work simultaneously', async () => {
    renderRegister();
    const passwordInput = screen.getByLabelText('Kata Sandi') as HTMLInputElement;
    const confirmInput = screen.getByLabelText('Konfirmasi Kata Sandi') as HTMLInputElement;
    const passwordBtn = screen.getByRole('button', { name: 'Show password' });
    const confirmBtn = screen.getByRole('button', { name: 'Show confirm password' });

    // Show both
    fireEvent.click(passwordBtn);
    fireEvent.click(confirmBtn);
    expect(passwordInput.type).toBe('text');
    expect(confirmInput.type).toBe('text');

    // Hide only password
    fireEvent.click(passwordBtn);
    expect(passwordInput.type).toBe('password');
    expect(confirmInput.type).toBe('text');
  });

  it('typing after toggling preserves the value', async () => {
    renderRegister();
    const passwordInput = screen.getByLabelText('Kata Sandi') as HTMLInputElement;
    const showBtn = screen.getByRole('button', { name: 'Show password' });

    fireEvent.change(passwordInput, { target: { value: 'TestPass123' } });
    fireEvent.click(showBtn);
    expect(passwordInput.type).toBe('text');
    expect(passwordInput.value).toBe('TestPass123');
  });

  it('clicking toggle button does not submit the form', async () => {
    signUpMock.mockResolvedValueOnce({ message: 'success' });
    renderRegister();

    const showBtn = screen.getByRole('button', { name: 'Show password' });
    fireEvent.click(showBtn);

    expect(signUpMock).not.toHaveBeenCalled();
  });
});
