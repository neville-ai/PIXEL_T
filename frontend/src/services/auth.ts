import { supabase, isSupabaseConfigured } from '@/lib/supabase';
import type { User, Session, AuthChangeEvent } from '@supabase/supabase-js';

export interface AuthResponse<T = unknown> {
  data: T | null;
  error: string | null;
}

/**
 * Sanitizes Supabase Auth error messages into user-friendly clinical messages.
 * Prevents leaking raw internal database or API details.
 */
export function formatAuthError(error: unknown): string {
  if (!error) return 'Terjadi kesalahan autentikasi.';

  const message = typeof error === 'object' && error !== null && 'message' in error
    ? String((error as { message: unknown }).message)
    : String(error);

  const lower = message.toLowerCase();

  if (lower.includes('invalid login credentials') || lower.includes('invalid credentials')) {
    return 'Email atau kata sandi yang Anda masukkan salah.';
  }
  if (lower.includes('email not confirmed')) {
    return 'Alamat email belum dikonfirmasi. Silakan periksa kotak masuk email Anda.';
  }
  if (lower.includes('user already registered') || lower.includes('already registered')) {
    return 'Alamat email sudah terdaftar. Silakan gunakan email lain atau masuk.';
  }
  if (lower.includes('password should be at least')) {
    return 'Kata sandi minimal terdiri dari 6 karakter.';
  }
  if (lower.includes('network') || lower.includes('fetch')) {
    return 'Gagal terhubung ke server autentikasi. Periksa koneksi internet Anda.';
  }

  return 'Autentikasi gagal. Silakan periksa kembali data yang Anda masukkan.';
}

/**
 * Registers a new user account with Supabase Auth.
 */
export async function registerUser(
  email: string,
  password: string,
  fullName?: string
): Promise<AuthResponse<{ user: User | null; session: Session | null }>> {
  if (!isSupabaseConfigured) {
    return {
      data: null,
      error: 'Layanan autentikasi Supabase belum dikonfigurasi pada environment.',
    };
  }

  try {
    const { data, error } = await supabase.auth.signUp({
      email: email.trim(),
      password,
      options: {
        data: {
          full_name: fullName?.trim() || '',
        },
      },
    });

    if (error) {
      return { data: null, error: formatAuthError(error) };
    }

    return { data: { user: data.user, session: data.session }, error: null };
  } catch (err) {
    return { data: null, error: formatAuthError(err) };
  }
}

/**
 * Signs in an existing user with email and password.
 */
export async function loginUser(
  email: string,
  password: string
): Promise<AuthResponse<{ user: User; session: Session }>> {
  if (!isSupabaseConfigured) {
    return {
      data: null,
      error: 'Layanan autentikasi Supabase belum dikonfigurasi pada environment.',
    };
  }

  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    });

    if (error) {
      return { data: null, error: formatAuthError(error) };
    }

    if (!data.user || !data.session) {
      return { data: null, error: 'Sesi autentikasi tidak berhasil dibuat.' };
    }

    return { data: { user: data.user, session: data.session }, error: null };
  } catch (err) {
    return { data: null, error: formatAuthError(err) };
  }
}

/**
 * Requests a Supabase password-reset e-mail for the given address.
 *
 * Uses the official `supabase.auth.resetPasswordForEmail` API. The redirect
 * target is the current application origin (no fabricated production URL).
 * Success does NOT reveal whether the address is registered — the caller
 * must display a neutral message.
 *
 * NOTE: this only sends the reset request. Completing the reset (setting a
 * new password) requires a recovery route/flow, which this repository does
 * not yet include — see the implementation report.
 */
export async function resetPasswordUser(email: string): Promise<AuthResponse<null>> {
  if (!isSupabaseConfigured) {
    return {
      data: null,
      error: 'Layanan autentikasi Supabase belum dikonfigurasi pada environment.',
    };
  }

  try {
    const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: window.location.origin,
    });

    if (error) {
      return { data: null, error: formatAuthError(error) };
    }

    return { data: null, error: null };
  } catch (err) {
    return { data: null, error: formatAuthError(err) };
  }
}

/**
 * Signs out the current authenticated user and clears Supabase session.
 */
export async function logoutUser(): Promise<{ error: string | null }> {
  try {
    const { error } = await supabase.auth.signOut();
    if (error) {
      return { error: formatAuthError(error) };
    }
    return { error: null };
  } catch (err) {
    return { error: formatAuthError(err) };
  }
}

/**
 * Retrieves the current active user from Supabase session.
 */
export async function getCurrentUser(): Promise<User | null> {
  try {
    const { data } = await supabase.auth.getUser();
    return data.user ?? null;
  } catch {
    return null;
  }
}

/**
 * Retrieves the current active session from Supabase client.
 */
export async function getCurrentSession(): Promise<Session | null> {
  try {
    const { data } = await supabase.auth.getSession();
    return data.session ?? null;
  } catch {
    return null;
  }
}

/**
 * Registers a listener for Supabase authentication state changes.
 */
export function onAuthStateChange(
  callback: (event: AuthChangeEvent, session: Session | null) => void
): { unsubscribe: () => void } {
  const { data: { subscription } } = supabase.auth.onAuthStateChange(callback);
  return {
    unsubscribe: () => subscription.unsubscribe(),
  };
}
