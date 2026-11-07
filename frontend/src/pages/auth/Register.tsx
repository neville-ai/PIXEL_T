import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { AlertCircle, ArrowRight, CheckCircle2, Mail, ShieldCheck, Eye, EyeOff } from 'lucide-react';
import doctorIcon from '@/assets/icon-doctor.png';

interface RegistrationSuccess {
  message: string;
  requiresEmailConfirmation: boolean;
}

export const Register: React.FC = () => {
  const { signUp } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [hospitalName, setHospitalName] = useState('');
  const [doctorSpecialty, setDoctorSpecialty] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [success, setSuccess] = useState<RegistrationSuccess | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccess(null);

    const trimmedName = fullName.trim();
    const trimmedEmail = email.trim();
    const trimmedHospital = hospitalName.trim();
    const trimmedSpecialty = doctorSpecialty.trim();

    if (!trimmedName) {
      setErrorMessage('Silakan masukkan nama lengkap Anda.');
      return;
    }

    if (!trimmedEmail) {
      setErrorMessage('Silakan masukkan alamat email Anda.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmedEmail)) {
      setErrorMessage('Format alamat email tidak valid.');
      return;
    }

    if (!trimmedHospital) {
      setErrorMessage('Silakan masukkan nama rumah sakit Anda.');
      return;
    }

    if (!trimmedSpecialty) {
      setErrorMessage('Silakan masukkan bidang keahlian dokter Anda.');
      return;
    }

    if (!password) {
      setErrorMessage('Silakan masukkan kata sandi Anda.');
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
      const result = await signUp(
        trimmedEmail,
        password,
        trimmedName,
        trimmedHospital,
        trimmedSpecialty
      );
      if (result.error) {
        setErrorMessage(result.error);
      } else {
        setSuccess({
          message:
            result.message ||
            'Pendaftaran akun PIXEL-T Anda telah diproses.',
          requiresEmailConfirmation: result.requiresEmailConfirmation ?? false,
        });
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

  const resetRegistrationForm = () => {
    setSuccess(null);
    setErrorMessage(null);
    setFullName('');
    setEmail('');
    setHospitalName('');
    setDoctorSpecialty('');
    setPassword('');
    setConfirmPassword('');
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh] px-4 py-8">
      <Card className="max-w-md w-full p-6 sm:p-8 space-y-6">
        {success ? (
          <>
            <div role="status" className="flex flex-col items-center text-center">
              <div className="mb-5 inline-flex h-16 w-16 items-center justify-center rounded-full border border-semantic-success/30 bg-semantic-success/10 text-badgeText-success dark:text-badgeText-success-dark">
                <CheckCircle2 className="h-8 w-8" aria-hidden="true" />
              </div>
              <h1 className="text-xl font-bold tracking-tight text-neutral-900 dark:text-dark-text sm:text-2xl">
                Registrasi Berhasil
              </h1>
              <p className="mt-2 text-sm leading-relaxed text-neutral-600 dark:text-dark-textMuted">
                {success.message}
              </p>
            </div>

            {success.requiresEmailConfirmation && (
              <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-4 dark:border-dark-border dark:bg-dark-elevated">
                <div className="flex items-start gap-2.5">
                  <Mail
                    className="mt-0.5 h-4 w-4 shrink-0 text-accent-600 dark:text-accent-500"
                    aria-hidden="true"
                  />
                  <p className="text-xs leading-relaxed text-neutral-600 dark:text-dark-textMuted">
                    Jika{' '}
                    <span className="font-semibold text-neutral-900 dark:text-dark-text">
                      {email}
                    </span>{' '}
                    belum terdaftar, akun PIXEL-T Anda telah dibuat dan tautan konfirmasi
                    telah dikirim ke alamat tersebut. Jika sudah terdaftar, silakan langsung
                    masuk.
                  </p>
                </div>
              </div>
            )}

            <div className="space-y-3 pt-1">
              <Link
                to="/login"
                className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-primary-900 px-5 text-sm font-semibold text-white transition-colors hover:bg-primary-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-700 focus-visible:ring-offset-2 dark:bg-primary-600 dark:hover:bg-primary-700 dark:focus-visible:ring-primary-600"
              >
                Masuk ke PIXEL-T
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
              <button
                type="button"
                onClick={resetRegistrationForm}
                className="w-full rounded-md px-3 py-2 text-xs font-medium text-neutral-500 transition-colors hover:bg-neutral-100 hover:text-neutral-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 dark:text-dark-textMuted dark:hover:bg-dark-elevated dark:hover:text-dark-text"
              >
                Daftar dengan akun lain
              </button>
            </div>
          </>
        ) : (
          <>
            <CardHeader className="p-0 space-y-2 text-center">
              <div className="mx-auto w-12 h-12 rounded-full bg-primary-50 dark:bg-dark-elevated flex items-center justify-center mb-2 overflow-hidden">
                <img
                  src={doctorIcon}
                  alt="Doctor Icon"
                  className="w-7 h-7 object-contain"
                />
              </div>
              <CardTitle className="text-xl font-bold tracking-tight text-neutral-900 dark:text-dark-text">
                Pendaftaran Akun PIXEL-T
              </CardTitle>
              <CardDescription className="text-xs text-neutral-600 dark:text-dark-textMuted">
                Registrasi akun pengguna untuk tenaga medis dan klinisi
              </CardDescription>
              <p className="text-xs text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/40 rounded-md px-3 py-2">
                Akun baru akan dibuat dengan status <strong>pending</strong> dan memerlukan persetujuan dari administrator rumah sakit sebelum dapat digunakan.
              </p>
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

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Nama Lengkap"
                type="text"
                placeholder="dr. Budi Pratama, Sp.PD"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={isSubmitting}
                required
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
                label="NAMA RUMAH SAKIT"
                type="text"
                placeholder="Contoh: RSUP Prof. Dr. R. D. Kandou"
                value={hospitalName}
                onChange={(e) => setHospitalName(e.target.value)}
                disabled={isSubmitting}
                required
                autoComplete="organization"
              />

              <Input
                label="BIDANG KEAHLIAN DOKTER"
                type="text"
                placeholder="Contoh: Patologi Anatomi"
                value={doctorSpecialty}
                onChange={(e) => setDoctorSpecialty(e.target.value)}
                disabled={isSubmitting}
                required
                autoComplete="organization"
              />

              <div className="relative">
                <Input
                  label="Kata Sandi"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Minimal 6 karakter"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isSubmitting}
                  required
                  autoComplete="new-password"
                  className="pr-11"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  aria-pressed={showPassword}
                  disabled={isSubmitting}
                  className="absolute bottom-1 right-1 rounded-md p-2 text-neutral-500 transition-colors hover:text-neutral-700 focus:outline-none focus:ring-2 focus:ring-primary-700/40 disabled:cursor-not-allowed dark:text-dark-textMuted dark:hover:text-dark-text"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" aria-hidden="true" />
                  ) : (
                    <Eye className="h-4 w-4" aria-hidden="true" />
                  )}
                </button>
              </div>

              <div className="relative">
                <Input
                  label="Konfirmasi Kata Sandi"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Ulangi kata sandi"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={isSubmitting}
                  required
                  autoComplete="new-password"
                  className="pr-11"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword((v) => !v)}
                  aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  aria-pressed={showConfirmPassword}
                  disabled={isSubmitting}
                  className="absolute bottom-1 right-1 rounded-md p-2 text-neutral-500 transition-colors hover:text-neutral-700 focus:outline-none focus:ring-2 focus:ring-primary-700/40 disabled:cursor-not-allowed dark:text-dark-textMuted dark:hover:text-dark-text"
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" aria-hidden="true" />
                  ) : (
                    <Eye className="h-4 w-4" aria-hidden="true" />
                  )}
                </button>
              </div>

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
          </>
        )}
      </Card>
    </div>
  );
};

export default Register;