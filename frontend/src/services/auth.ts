import { supabase, isSupabaseConfigured } from '@/lib/supabase';
import type { User, Session, AuthChangeEvent } from '@supabase/supabase-js';

export interface AuthResponse<T = unknown> {
  data: T | null;
  error: string | null;
}

interface AuthErrorDetails {
  message: string;
  code: string;
  name: string;
  status: number;
}

function readAuthError(error: unknown): AuthErrorDetails {
  if (typeof error === 'object' && error !== null) {
    const record = error as {
      message?: unknown;
      code?: unknown;
      name?: unknown;
      status?: unknown;
    };

    return {
      message: record.message === undefined ? String(error) : String(record.message),
      code: typeof record.code === 'string' ? record.code : '',
      name: typeof record.name === 'string' ? record.name : '',
      status: typeof record.status === 'number' ? record.status : 0,
    };
  }

  return { message: String(error), code: '', name: '', status: 0 };
}

/**
 * Sanitizes Supabase Auth error messages into user-friendly messages.
 * Prevents leaking raw internal database or API details.
 *
 * Duplicate-address messages are only used when Supabase itself returns a
 * duplicate indication (e.g. `user_already_exists` / `email_exists`). When
 * e-mail confirmation is enabled, Supabase intentionally obfuscates that
 * response instead, and this function is never asked to invent one.
 */
export function formatAuthError(error: unknown): string {
  if (!error) return 'Terjadi kesalahan autentikasi.';

  const { message, code, name, status } = readAuthError(error);
  const lower = message.toLowerCase();

  if (code === 'invalid_credentials' || lower.includes('invalid login credentials') || lower.includes('invalid credentials')) {
    return 'Email atau kata sandi yang Anda masukkan salah.';
  }
  if (code === 'email_not_confirmed' || lower.includes('email not confirmed')) {
    return 'Alamat email belum dikonfirmasi. Silakan periksa kotak masuk email Anda.';
  }
  if (
    code === 'user_already_exists' ||
    code === 'email_exists' ||
    lower.includes('user already registered') ||
    lower.includes('already been registered') ||
    lower.includes('already registered')
  ) {
    return 'Alamat email sudah terdaftar. Silakan masuk atau gunakan alamat email lain.';
  }
  if (
    code === 'weak_password' ||
    lower.includes('password should be at least') ||
    lower.includes('weak password')
  ) {
    return 'Kata sandi minimal terdiri dari 6 karakter.';
  }
  if (
    code === 'email_address_invalid' ||
    code === 'validation_failed' ||
    lower.includes('invalid email') ||
    lower.includes('email address is invalid')
  ) {
    return 'Format alamat email tidak valid. Periksa kembali alamat email Anda.';
  }
  if (
    code === 'over_email_send_rate_limit' ||
    code === 'over_request_rate_limit' ||
    status === 429 ||
    lower.includes('rate limit') ||
    lower.includes('too many requests')
  ) {
    return 'Terlalu banyak percobaan. Tunggu beberapa saat lalu coba lagi.';
  }
  if (
    code === 'signup_disabled' ||
    lower.includes('signups not allowed') ||
    lower.includes('signup is disabled')
  ) {
    return 'Pendaftaran akun baru sedang tidak tersedia. Silakan hubungi administrator.';
  }
  if (
    name === 'AuthRetryableFetchError' ||
    code === 'request_timeout' ||
    lower.includes('network') ||
    lower.includes('fetch') ||
    lower.includes('timeout')
  ) {
    return 'Gagal terhubung ke server autentikasi. Periksa koneksi internet Anda.';
  }

  return 'Autentikasi gagal. Silakan periksa kembali data yang Anda masukkan.';
}

export interface RegisterResult {
  user: User | null;
  session: Session | null;
  /**
   * True when Supabase returned its anti-enumeration placeholder for an
   * address that may already be registered (`identities` is empty and no
   * session was created). Callers must keep user-facing copy identical for
   * hinted and non-hinted results; this flag only makes the obfuscated path
   * explicit and testable. It must never be used to reveal account existence.
   */
  existingAccountHint: boolean;
}

/**
 * Registers a new user account with Supabase Auth.
 *
 * This is the only account-creation path in the frontend: it calls
 * `supabase.auth.signUp` once and stores professional fields as auth metadata.
 * It never creates a second account and never writes a separate profile row,
 * so there is no orphan-profile window if presentation/state changes fail.
 */
export async function registerUser(
  email: string,
  password: string,
  fullName?: string,
  hospitalName?: string,
  doctorSpecialty?: string
): Promise<AuthResponse<RegisterResult>> {
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
          hospital: hospitalName?.trim() || '',
          hospital_name: hospitalName?.trim() || '',
          primary_specialty: doctorSpecialty?.trim() || '',
          specialty: doctorSpecialty?.trim() || '',
          doctor_profile: {
            fullName: fullName?.trim() || '',
            hospital: hospitalName?.trim() || '',
            primarySpecialty: doctorSpecialty?.trim() || '',
          },
        },
      },
    });

    if (error) {
      return { data: null, error: formatAuthError(error) };
    }

    const identities = data.user?.identities;
    const existingAccountHint = Boolean(
      data.user &&
        !data.session &&
        Array.isArray(identities) &&
        identities.length === 0
    );

    return {
      data: {
        user: data.user,
        session: data.session,
        existingAccountHint,
      },
      error: null,
    };
  } catch (err) {
    return { data: null, error: formatAuthError(err) };
  }
}

/**
 * Signs in an existing user with email and password.
 * @param selectedRole - Context-only hint (admin|doctor) from the UI role selector.
 *                       Used for pre-auth mismatch detection; not stored or authoritative.
 */
export async function loginUser(
  email: string,
  password: string,
  _selectedRole?: 'admin' | 'doctor'
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
 * target must match a URL whitelisted in the Supabase Dashboard under
 * Authentication > Settings > Redirection URLs (or the app URL if configured
 * as a redirect URL). The caller must display a neutral message.
 *
 * NOTE: this only sends the reset request. Completing the reset (setting a
 * new password) requires a recovery route/flow, which this repository now
 * includes via the /reset-password route.
 */
export async function resetPasswordUser(email: string): Promise<AuthResponse<null>> {
  if (!isSupabaseConfigured) {
    return {
      data: null,
      error: 'Layanan autentikasi Supabase belum dikonfigurasi pada environment.',
    };
  }

  try {
    // Redirect to the /reset-password route so the frontend can handle
    // the recovery session and allow the user to set a new password.
    const appOrigin = import.meta.env.VITE_APP_URL || window.location.origin;
    const redirectUrl = `${appOrigin}/reset-password`;
    const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: redirectUrl,
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
 * Fetches the doctor profile row to determine role and account_status.
 * Returns null if Supabase is not configured or the query fails.
 */
export async function fetchUserProfileStatus(user: User): Promise<{
  role: string | null;
  accountStatus: string | null;
} | null> {
  if (!isSupabaseConfigured) return null;
  try {
    const { data, error } = await supabase
      .from('doctor_profiles')
      .select('role, account_status')
      .eq('user_id', user.id)
      .maybeSingle();
    if (error || !data) return null;
    return {
      role: typeof data.role === 'string' ? data.role : 'doctor',
      accountStatus: typeof data.account_status === 'string' ? data.account_status : 'pending',
    };
  } catch {
    return null;
  }
}

/**
 * Reads app_metadata.role from the authenticated user record.
 *
 * app_metadata is server-write-only (set via the Supabase Admin API); unlike
 * user_metadata it cannot be changed by the end-user client, so it is the
 * trusted source for admin identity.
 *
 * Returns null when the user object does not carry app_metadata (rare — mostly
 * happens in test mocks or very old sessions).
 */
export function getAdminRoleFromAppMetadata(user: User): string | null {
  // app_metadata is a top-level property on the Supabase User object (JWT payload).
  const appMeta = (user as unknown as { app_metadata?: Record<string, unknown> }).app_metadata;
  if (!appMeta || typeof appMeta !== 'object') return null;
  const role = appMeta.role;
  return typeof role === 'string' ? role : null;
}

/**
 * Verifies strict equality between the selected role in the UI dropdown and the actual role resolved from auth metadata.
 * Both directions are strictly enforced:
 * - selected 'doctor' requires actual 'doctor'
 * - selected 'admin' requires actual 'admin'
 */
export function isRoleMatch(
  selected: 'admin' | 'doctor',
  actual: string | null
): boolean {
  return selected === actual;
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
