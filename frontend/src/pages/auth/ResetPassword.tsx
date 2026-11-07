import React, { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { supabase } from '@/lib/supabase';
import '@/styles/opening.css';

export const ResetPassword: React.FC = () => {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Check for recovery state in Supabase session/URL params
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean | null>(null);
  const [newPassword, setNewPassword] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');

  useEffect(() => {
    // Check if this is a password reset flow by looking at session/URL
    // Supabase, when redirectTo is set, will persist the recovery session.
    // We check via getSession to see if we're in a recovery state.
    // If not in recovery state, redirect to sign in.
    const checkRecoverySession = async () => {
      try {
        const { data, error } = await supabase.auth.getSession();
        if (error) throw error;
        const session = data.session;

        // If no session, redirect to sign in
        if (!session) {
          signOut().then(() => {
            navigate('/login', { replace: true });
          });
          return;
        }

        // If we have a valid session, proceed
        setIsLoading(false);
      } catch (err) {
        console.error('Error checking recovery session:', err);
        setError('Terjadi kesalahan saat memeriksa sesi reset. Silakan coba lagi.');
        setIsLoading(false);
      }
    };

    checkRecoverySession();
  }, [navigate, signOut, supabase]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation: both fields must be filled
    if (!newPassword.trim()) {
      setError('Kata sandi baru wajib diisi.');
      return;
    }
    if (!confirmPassword.trim()) {
      setError('Konfirmasi kata sandi wajib diisi.');
      return;
    }
    // Validation: passwords must match
    if (newPassword !== confirmPassword) {
      setError('Kata sandi dan konfirmasi kata sandi tidak cocok.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Update the user's password via Supabase Auth
      const { error } = await supabase.auth.updateUser({
        password: newPassword.trim(),
      });

      if (error) {
        setError(
          formatSupabaseAuthError(error) || 'Gagal memperbarui kata sandi. Silakan coba lagi.'
        );
      } else {
        setSuccess(true);
        // Setelah berhasil, kembali ke halaman Sign In setelah jeda singkat
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 1500);
      }
    } catch (err) {
      setError('Terjadi kesalahan yang tidak terduga. Silakan coba lagi.');
    } finally {
      setIsLoading(false);
    }
  };

  // Format Supabase auth error into user-friendly message
  const formatSupabaseAuthError = (error: any): string | null => {
    if (!error) return null;
    const message = error.message || error.error || '';
    const lower = message.toLowerCase();

    // Common Supabase auth error codes
    if (
      lower.includes('password') &&
      lower.includes('too short')
    ) {
      return 'Kata sandi minimal terdiri dari 6 karakter.';
    }
    if (lower.includes('weak')) {
      return 'Kata sandi dianggap lemah. Gunakan kata sandi yang lebih kuat.';
    }
    if (lower.includes('rate limit') || lower.includes('too many')) {
      return 'Terlalu banyak percobaan. Tunggu beberapa saat lalu coba lagi.';
    }
    if (lower.includes('invalid')) {
      return 'Input tidak valid. Silakan periksa kembali data yang Anda masukkan.';
    }
    // Default: return the raw message or null
    return message ? message : null;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-bg p-4">
        <div className="rounded-2xl border border-dark-border/70 bg-dark-surface/80 p-8 shadow-[0_24px_70px_rgba(2,10,18,0.5)] backdrop-blur-sm">
          <Loader2 className="mx-auto h-12 w-12 text-accent-600 animate-spin" />
          <p className="mt-4 text-center text-sm text-neutral-600 dark:text-dark-textMuted">Sedang memproses reset kata sandi...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-dark-bg p-4">
      <div className="rounded-2xl border border-dark-border/70 bg-dark-surface/80 p-8 shadow-[0_24px_70px_rgba(2,10,18,0.5)] backdrop-blur-sm max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-dark-text mb-2">
            Reset Your Password
          </h1>
          <p className="text-sm leading-relaxed text-neutral-600 dark:text-dark-textMuted">
            Masukkan kata sandi baru untuk mengakses akun PIXEL-T Anda.
          </p>
        </div>

        {error && (
          <div
            role="alert"
            className="rounded-md border border-semantic-error/30 bg-semantic-error/10 p-3 text-xs text-badgeText-error dark:text-badgeText-error-dark mb-4"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
            <p className="leading-relaxed">{error}</p>
          </div>
        )}

        {success && (
          <div
            role="alert"
            className="rounded-md border border-accent-600/40 bg-accent-50 p-3 text-xs leading-relaxed text-neutral-700 dark:border-accent-500/40 dark:bg-dark-accentSurface dark:text-dark-textMuted mb-4"
          >
            <CheckCircle className="h-4 w-4 mr-2 align-middle" aria-hidden="true" />
            <p className="leading-relaxed">
              Kata sandi berhasil diperbarui. Anda sekarang dapat masuk.
            </p>
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="space-y-4"
          noValidate
        >
          <Input
            label="Kata sandi baru"
            type="password"
            placeholder="••••••••••••••••"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            autoComplete="new-password"
            disabled={isLoading}
          />

          <Input
            label="Konfirmasi kata sandi"
            type="password"
            placeholder="••••••••••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
            disabled={isLoading}
          />

          <div className="pt-2">
            <Button
              type="submit"
              variant="primary"
              size="md"
              className="w-full"
              isLoading={isLoading}
              disabled={isLoading}
            >
              Update Password
            </Button>
          </div>

          {/* Back to Sign In link - only show if we're not already on login */}
          {location.pathname !== '/login' && (
            <p className="mt-4 text-center text-sm text-neutral-600 dark:text-dark-textMuted">
              <Link
                to="/login"
                className="rounded-sm font-semibold text-accent-600 transition-colors hover:text-accent-700 focus:outline-none focus:ring-2 focus:ring-accent-600/50 dark:text-accent-500 dark:hover:text-accent-500"
              >
                Kembali ke Sign In
              </Link>
            </p>
          )}
        </form>
      </div>
    </div>
  );
};

export default ResetPassword;