import { beforeEach, describe, expect, it, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import React from 'react';
import { AuthProvider, useAuth } from './AuthContext';
import * as authService from '@/utils/auth';
import type { User, Session } from '@supabase/supabase-js';

vi.mock('@/utils/auth', () => ({
  loginUser: vi.fn(),
  registerUser: vi.fn(),
  logoutUser: vi.fn(),
  getCurrentSession: vi.fn(),
  onAuthStateChange: vi.fn(),
  fetchUserProfileStatus: vi.fn(),
  getAdminRoleFromAppMetadata: vi.fn(),
  isRoleMatch: vi.fn((selected, actual) => selected === actual),
}));

function makeUser(id: string, appMetaRole?: string): User {
  return {
    id,
    app_metadata: appMetaRole ? { role: appMetaRole } : {},
    user_metadata: {},
    aud: 'authenticated',
    created_at: new Date().toISOString(),
  } as unknown as User;
}

function makeSession(user: User): Session {
  return {
    access_token: 'valid-token',
    token_type: 'bearer',
    expires_in: 3600,
    refresh_token: 'refresh-token',
    user,
  } as unknown as Session;
}

describe('AuthContext — two-way role match enforcement and session cleanup', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.sessionStorage.clear();
    // Mark startup reset done so restoreSession runs
    window.sessionStorage.setItem('pixel-t-startup-reset-v1', '1');

    vi.mocked(authService.getCurrentSession).mockResolvedValue(null);
    vi.mocked(authService.onAuthStateChange).mockReturnValue({
      unsubscribe: vi.fn(),
    });
    vi.mocked(authService.logoutUser).mockResolvedValue({ error: null });
  });

  it('pilih Dokter + akun admin -> GAGAL, logoutUser dipanggil, state user/session null', async () => {
    const adminUser = makeUser('admin-1', 'admin');
    const adminSession = makeSession(adminUser);

    vi.mocked(authService.loginUser).mockResolvedValue({
      data: { user: adminUser, session: adminSession },
      error: null,
    });
    vi.mocked(authService.getAdminRoleFromAppMetadata).mockReturnValue('admin');

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    let signInResult: { error?: string } = {};
    await act(async () => {
      signInResult = await result.current.signIn('admin@rs.id', 'rahasia123', 'doctor');
    });

    // 1. Error message must match required neutral string
    expect(signInResult.error).toBe(
      'Jenis akun yang dipilih tidak sesuai dengan akun ini. Silakan pilih jenis akun yang benar.'
    );

    // 2. logoutUser / signOut must have been called
    expect(authService.logoutUser).toHaveBeenCalledTimes(1);

    // 3. Context state must be completely cleared (null)
    expect(result.current.user).toBeNull();
    expect(result.current.session).toBeNull();
    expect(result.current.role).toBeNull();
    expect(result.current.accountStatus).toBeNull();
  });

  it('pilih Admin + akun dokter -> GAGAL, logoutUser dipanggil, state user/session null', async () => {
    const doctorUser = makeUser('doc-1');
    const doctorSession = makeSession(doctorUser);

    vi.mocked(authService.loginUser).mockResolvedValue({
      data: { user: doctorUser, session: doctorSession },
      error: null,
    });
    vi.mocked(authService.getAdminRoleFromAppMetadata).mockReturnValue(null);
    vi.mocked(authService.fetchUserProfileStatus).mockResolvedValue({
      role: 'doctor',
      accountStatus: 'approved',
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    let signInResult: { error?: string } = {};
    await act(async () => {
      signInResult = await result.current.signIn('dokter@rs.id', 'rahasia123', 'admin');
    });

    expect(signInResult.error).toBe(
      'Jenis akun yang dipilih tidak sesuai dengan akun ini. Silakan pilih jenis akun yang benar.'
    );
    expect(authService.logoutUser).toHaveBeenCalledTimes(1);
    expect(result.current.user).toBeNull();
    expect(result.current.session).toBeNull();
    expect(result.current.role).toBeNull();
    expect(result.current.accountStatus).toBeNull();
  });

  it('pilih Dokter + akun dokter approved -> BERHASIL, state tersimpan', async () => {
    const doctorUser = makeUser('doc-1');
    const doctorSession = makeSession(doctorUser);

    vi.mocked(authService.loginUser).mockResolvedValue({
      data: { user: doctorUser, session: doctorSession },
      error: null,
    });
    vi.mocked(authService.getAdminRoleFromAppMetadata).mockReturnValue(null);
    vi.mocked(authService.fetchUserProfileStatus).mockResolvedValue({
      role: 'doctor',
      accountStatus: 'approved',
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    let signInResult: { error?: string; role?: string | null; accountStatus?: string | null } = {};
    await act(async () => {
      signInResult = await result.current.signIn('dokter@rs.id', 'rahasia123', 'doctor');
    });

    expect(signInResult.error).toBeUndefined();
    expect(signInResult.role).toBe('doctor');
    expect(signInResult.accountStatus).toBe('approved');
    expect(authService.logoutUser).not.toHaveBeenCalled();
    expect(result.current.user?.id).toBe('doc-1');
    expect(result.current.role).toBe('doctor');
    expect(result.current.accountStatus).toBe('approved');
  });

  it('pilih Admin + akun admin -> BERHASIL, state tersimpan', async () => {
    const adminUser = makeUser('admin-1', 'admin');
    const adminSession = makeSession(adminUser);

    vi.mocked(authService.loginUser).mockResolvedValue({
      data: { user: adminUser, session: adminSession },
      error: null,
    });
    vi.mocked(authService.getAdminRoleFromAppMetadata).mockReturnValue('admin');

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    let signInResult: { error?: string; role?: string | null; accountStatus?: string | null } = {};
    await act(async () => {
      signInResult = await result.current.signIn('admin@rs.id', 'rahasia123', 'admin');
    });

    expect(signInResult.error).toBeUndefined();
    expect(signInResult.role).toBe('admin');
    expect(authService.logoutUser).not.toHaveBeenCalled();
    expect(result.current.user?.id).toBe('admin-1');
    expect(result.current.role).toBe('admin');
    expect(result.current.accountStatus).toBeNull();
  });

  it('pilih Dokter + akun dokter pending -> BERHASIL role match tapi status pending tetap dipertahankan', async () => {
    const doctorUser = makeUser('doc-pending');
    const doctorSession = makeSession(doctorUser);

    vi.mocked(authService.loginUser).mockResolvedValue({
      data: { user: doctorUser, session: doctorSession },
      error: null,
    });
    vi.mocked(authService.getAdminRoleFromAppMetadata).mockReturnValue(null);
    vi.mocked(authService.fetchUserProfileStatus).mockResolvedValue({
      role: 'doctor',
      accountStatus: 'pending',
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    let signInResult: { error?: string; role?: string | null; accountStatus?: string | null } = {};
    await act(async () => {
      signInResult = await result.current.signIn('pending@rs.id', 'rahasia123', 'doctor');
    });

    expect(signInResult.error).toBeUndefined();
    expect(signInResult.role).toBe('doctor');
    expect(signInResult.accountStatus).toBe('pending');
    expect(authService.logoutUser).not.toHaveBeenCalled();
    expect(result.current.user?.id).toBe('doc-pending');
    expect(result.current.accountStatus).toBe('pending');
  });

  it('kredensial salah -> pesan lama tidak berubah dan tidak mengubah state', async () => {
    vi.mocked(authService.loginUser).mockResolvedValue({
      data: null,
      error: 'Email atau kata sandi yang Anda masukkan salah.',
    });

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    );

    const { result } = renderHook(() => useAuth(), { wrapper });

    let signInResult: { error?: string } = {};
    await act(async () => {
      signInResult = await result.current.signIn('wrong@rs.id', 'wrongpass', 'doctor');
    });

    expect(signInResult.error).toBe('Email atau kata sandi yang Anda masukkan salah.');
    expect(authService.logoutUser).not.toHaveBeenCalled();
    expect(result.current.user).toBeNull();
    expect(result.current.session).toBeNull();
  });
});

