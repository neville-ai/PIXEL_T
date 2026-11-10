import { beforeEach, describe, expect, it, vi } from 'vitest';
import { formatAuthError, registerUser, isRoleMatch } from './auth';

const { signUpMock } = vi.hoisted(() => ({ signUpMock: vi.fn() }));

vi.mock('@/lib/supabase', () => ({
  isSupabaseConfigured: true,
  supabase: {
    auth: {
      signUp: signUpMock,
    },
  },
}));

function makeUser(overrides: Record<string, unknown> = {}) {
  return {
    id: 'user-1',
    email: 'dokter@rumah-sakit.id',
    identities: [{ id: 'identity-1' }],
    ...overrides,
  };
}

describe('registerUser', () => {
  beforeEach(() => {
    signUpMock.mockReset();
  });

  it('uses a single supabase.auth.signUp call and forwards professional metadata', async () => {
    signUpMock.mockResolvedValue({
      data: { user: makeUser(), session: null },
      error: null,
    });

    const result = await registerUser(
      '  dokter@rumah-sakit.id  ',
      'rahasia123',
      'dr. Alexander',
      'RSUP Prof. Dr. R. D. Kandou',
      'Patologi Anatomi'
    );

    expect(signUpMock).toHaveBeenCalledTimes(1);
    expect(signUpMock).toHaveBeenCalledWith({
      email: 'dokter@rumah-sakit.id',
      password: 'rahasia123',
      options: {
        data: {
          full_name: 'dr. Alexander',
          hospital: 'RSUP Prof. Dr. R. D. Kandou',
          hospital_name: 'RSUP Prof. Dr. R. D. Kandou',
          primary_specialty: 'Patologi Anatomi',
          specialty: 'Patologi Anatomi',
          doctor_profile: {
            fullName: 'dr. Alexander',
            hospital: 'RSUP Prof. Dr. R. D. Kandou',
            primarySpecialty: 'Patologi Anatomi',
          },
        },
      },
    });

    expect(result.error).toBeNull();
    expect(result.data?.existingAccountHint).toBe(false);
  });

  it('detects the anti-enumeration placeholder for a possibly existing address', async () => {
    signUpMock.mockResolvedValue({
      data: { user: makeUser({ identities: [] }), session: null },
      error: null,
    });

    const result = await registerUser('existing@rumah-sakit.id', 'rahasia123');

    expect(result.error).toBeNull();
    expect(result.data?.existingAccountHint).toBe(true);
    // Still exactly one account-creation call — no second account/profile write.
    expect(signUpMock).toHaveBeenCalledTimes(1);
  });

  it('does not flag a real new registration as existing', async () => {
    signUpMock.mockResolvedValue({
      data: { user: makeUser(), session: { access_token: 'token' } },
      error: null,
    });

    const result = await registerUser('new@rumah-sakit.id', 'rahasia123');

    expect(result.data?.existingAccountHint).toBe(false);
  });

  it('maps a duplicate e-mail error returned by Supabase to a safe message', async () => {
    signUpMock.mockResolvedValue({
      data: { user: null, session: null },
      error: { code: 'user_already_exists', message: 'User already registered', status: 422 },
    });

    const result = await registerUser('existing@rumah-sakit.id', 'rahasia123');

    expect(result.error).toContain('sudah terdaftar');
    expect(result.data).toBeNull();
  });
});

describe('formatAuthError', () => {
  it.each([
    ['user_already_exists', 'User already registered'],
    ['email_exists', 'A user with this email address has already been registered'],
  ])('maps duplicate-address code %s', (code, message) => {
    expect(formatAuthError({ code, message, status: 422 })).toContain('sudah terdaftar');
  });

  it('maps invalid credentials separately from duplicate accounts', () => {
    expect(
      formatAuthError({ code: 'invalid_credentials', message: 'Invalid login credentials' })
    ).toContain('kata sandi');
  });

  it('distinguishes a network failure from an authentication error', () => {
    expect(
      formatAuthError({
        name: 'AuthRetryableFetchError',
        message: 'TypeError: Failed to fetch',
        status: 0,
      })
    ).toContain('Gagal terhubung ke server autentikasi');
  });

  it('maps rate limiting to a retry instruction', () => {
    expect(
      formatAuthError({
        code: 'over_email_send_rate_limit',
        message: 'Email rate limit exceeded',
        status: 429,
      })
    ).toContain('Terlalu banyak percobaan');
  });

  it('maps server-side e-mail validation errors', () => {
    expect(
      formatAuthError({ code: 'email_address_invalid', message: 'Email address is invalid' })
    ).toContain('Format alamat email tidak valid');
  });

  it('falls back to a generic message without leaking raw details', () => {
    const message = formatAuthError({ message: 'unexpected internal database detail' });
    expect(message).toBe(
      'Autentikasi gagal. Silakan periksa kembali data yang Anda masukkan.'
    );
    expect(message).not.toContain('internal database');
  });
});

describe('isRoleMatch', () => {
  it('returns true when selected and actual role match strictly', () => {
    expect(isRoleMatch('admin', 'admin')).toBe(true);
    expect(isRoleMatch('doctor', 'doctor')).toBe(true);
  });

  it('returns false when selected role does not match actual role (two-way enforcement)', () => {
    expect(isRoleMatch('admin', 'doctor')).toBe(false);
    expect(isRoleMatch('doctor', 'admin')).toBe(false);
  });

  it('returns false when actual role is null or unknown', () => {
    expect(isRoleMatch('admin', null)).toBe(false);
    expect(isRoleMatch('doctor', null)).toBe(false);
    expect(isRoleMatch('doctor', 'patient')).toBe(false);
  });
});
