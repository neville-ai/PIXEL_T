import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { LogIn, ArrowRight, AlertCircle, ShieldCheck } from 'lucide-react';

export const Login: React.FC = () => {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      setErrorMessage('Silakan masukkan alamat email Anda.');
      return;
    }
    if (!password) {
      setErrorMessage('Silakan masukkan kata sandi Anda.');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await signIn(trimmedEmail, password);
      if (result.error) {
        setErrorMessage(result.error);
        setIsSubmitting(false);
      } else {
        // Clear password from component state
        setPassword('');
        navigate(from, { replace: true });
      }
    } catch {
      setErrorMessage('Terjadi kesalahan yang tidak terduga saat mencoba masuk.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[60vh] px-4 py-8">
      <Card className="max-w-md w-full p-6 sm:p-8 space-y-6">
        <CardHeader className="p-0 space-y-2 text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary-50 dark:bg-dark-elevated flex items-center justify-center text-primary-900 dark:text-accent-500 mb-2">
            <LogIn className="w-6 h-6" />
          </div>
          <div className="flex justify-center">
            <Badge variant="accent">Supabase Auth</Badge>
          </div>
          <CardTitle className="text-xl font-bold tracking-tight text-neutral-900 dark:text-dark-text">
            Masuk ke PIXEL-T
          </CardTitle>
          <CardDescription className="text-xs text-neutral-600 dark:text-dark-textMuted">
            Akses sistem analisis citra polip kolonoskopi berbasis deep learning
          </CardDescription>
        </CardHeader>

        {errorMessage && (
          <div
            role="alert"
            className="p-3 rounded-md bg-semantic-error/10 border border-semantic-error/30 text-xs text-semantic-error flex items-start gap-2.5"
          >
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <p className="leading-relaxed">{errorMessage}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Pengguna"
            type="email"
            placeholder="dokter@rumah-sakit.id"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={isSubmitting}
            helperText="Gunakan email tenaga medis terdaftar"
            required
            autoComplete="email"
          />

          <Input
            label="Kata Sandi"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={isSubmitting}
            required
            autoComplete="current-password"
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
              Masuk
            </Button>
          </div>
        </form>

        <div className="p-3 rounded-md bg-neutral-50 dark:bg-dark-elevated border border-neutral-200 dark:border-dark-border text-xs text-neutral-600 dark:text-dark-textMuted flex items-start gap-2.5">
          <ShieldCheck className="w-4 h-4 text-accent-600 dark:text-accent-500 flex-shrink-0 mt-0.5" />
          <p>
            Kredensial diamankan melalui enkripsi Supabase Auth dan diverifikasi secara ketat server-side.
          </p>
        </div>

        <div className="text-center text-xs text-neutral-600 dark:text-dark-textMuted pt-2 border-t border-neutral-100 dark:border-dark-border space-y-2">
          <p>
            Belum memiliki akun?{' '}
            <Link to="/register" className="text-accent-600 dark:text-accent-500 font-semibold hover:underline">
              Daftar di sini
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
};

export default Login;
