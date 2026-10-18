import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { UserPlus, ArrowRight, AlertCircle, CheckCircle, ShieldCheck } from 'lucide-react';

export const Register: React.FC = () => {
  const { signUp } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    const trimmedName = fullName.trim();
    const trimmedEmail = email.trim();

    if (!trimmedEmail) {
      setErrorMessage('Silakan masukkan alamat email Anda.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmedEmail)) {
      setErrorMessage('Format alamat email tidak valid.');
      return;
    }

    if (!password) {
      setErrorMessage('Silakan masukkan kata sandi.');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Kata sandi harus memiliki minimal 6 karakter.');
      return;
    }

    if (password !== confirmPassword) {
      setErrorMessage('Konfirmasi kata sandi tidak cocok dengan kata sandi.');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await signUp(trimmedEmail, password, trimmedName);
      if (result.error) {
        setErrorMessage(result.error);
      } else {
        setSuccessMessage(
          result.message || 'Pendaftaran berhasil. Silakan periksa email Anda atau masuk dengan akun baru.'
        );
        // Clean passwords from state immediately
        setPassword('');
        setConfirmPassword('');
      }
    } catch {
      setErrorMessage('Terjadi kesalahan yang tidak terduga saat melakukan pendaftaran.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh] px-4 py-8">
      <Card className="max-w-md w-full p-6 sm:p-8 space-y-6">
        <CardHeader className="p-0 space-y-2 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary-50 dark:bg-dark-elevated flex items-center justify-center text-primary-900 dark:text-accent-500 mb-2">
            <UserPlus className="w-6 h-6" />
          </div>
          <div className="flex justify-center">
            <Badge variant="accent">Supabase Auth</Badge>
          </div>
          <CardTitle className="text-xl font-bold tracking-tight text-neutral-900 dark:text-dark-text">
            Pendaftaran Akun PIXEL-T
          </CardTitle>
          <CardDescription className="text-xs text-neutral-600 dark:text-dark-textMuted">
            Registrasi akun pengguna untuk tenaga medis dan klinisi
          </CardDescription>
        </CardHeader>

        {errorMessage && (
          <div
            role="alert"
            className="p-3 rounded-md bg-semantic-error/10 border border-semantic-error/30 text-xs text-badgeText-error dark:text-badgeText-error-dark flex items-start gap-2.5"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">{errorMessage}</p>
          </div>
        )}

        {successMessage && (
          <div
            role="status"
            className="p-3 rounded-md bg-semantic-success/10 border border-semantic-success/30 text-xs text-badgeText-success dark:text-badgeText-success-dark flex items-start gap-2.5"
          >
            <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-semibold">Registrasi Berhasil</p>
              <p className="leading-relaxed">{successMessage}</p>
              <div className="pt-2">
                <Link to="/login" className="inline-flex items-center font-semibold underline gap-1">
                  Lanjut ke Halaman Masuk &rarr;
                </Link>
              </div>
            </div>
          </div>
        )}

        {!successMessage && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Nama Lengkap"
              type="text"
              placeholder="dr. Budi Pratama, Sp.PD"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={isSubmitting}
              autoComplete="name"
            />

            <Input
              label="Email Pengguna"
              type="email"
              placeholder="dokter@rumah-sakit.id"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isSubmitting}
              required
              autoComplete="email"
            />

            <Input
              label="Kata Sandi"
              type="password"
              placeholder="Minimal 6 karakter"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isSubmitting}
              required
              autoComplete="new-password"
            />

            <Input
              label="Konfirmasi Kata Sandi"
              type="password"
              placeholder="Ulangi kata sandi"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isSubmitting}
              required
              autoComplete="new-password"
            />

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                size="md"
                className="w-full"
                isLoading={isSubmitting}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Daftar
              </Button>
            </div>
          </form>
        )}

        <div className="p-3 rounded-md bg-neutral-50 dark:bg-dark-elevated border border-neutral-200 dark:border-dark-border text-xs text-neutral-600 dark:text-dark-textMuted flex items-start gap-2.5">
          <ShieldCheck className="w-4 h-4 text-accent-600 dark:text-accent-500 flex-shrink-0 mt-0.5" />
          <p>
            Akun Anda dilindungi oleh arsitektur keamanan Supabase Auth. Password tidak pernah disimpan dalam plain text.
          </p>
        </div>

        <div className="text-center text-xs text-neutral-600 dark:text-dark-textMuted pt-2 border-t border-neutral-100 dark:border-dark-border space-y-2">
          <p>
            Sudah memiliki akun terdaftar?{' '}
            <Link to="/login" className="text-accent-600 dark:text-accent-500 font-semibold hover:underline">
              Masuk di sini
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Register;
