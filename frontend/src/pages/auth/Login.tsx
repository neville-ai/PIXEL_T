import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { LogoPixelT } from '@/components/brand/LogoPixelT';
import { OpeningAnimation } from '@/components/auth/OpeningAnimation';
import { useOpeningAnimation } from '@/hooks/useOpeningAnimation';
import { getRememberedEmail, setRememberedEmail, stageIndex } from '@/lib/openingTimeline';
import { resetPasswordUser } from '@/services/auth';
import { AlertCircle, ArrowRight, Eye, EyeOff, Send } from 'lucide-react';
import '@/styles/opening.css';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

type LoginMode = 'signIn' | 'reset';

/**
 * Two-panel Login page.
 *
 * - Left: locked navy branding panel with the official PIXEL-T logo.
 * - Right: sign-in form (and inline forgot-password request) that follows the
 *   active light/dark theme.
 *
 * Authentication behavior (signIn, validation, error formatting, loading
 * state, redirect to `location.state.from`) is preserved from the original
 * page. The opening animation only controls presentation/timeline — it never
 * performs or simulates authentication.
 */
export const Login: React.FC = () => {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const { stage, isActive } = useOpeningAnimation();
  const idx = stageIndex(stage);
  // Captured once on first render: true when the intro was skipped entirely
  // (reduced motion or already played in this tab session).
  const [introSkipped] = useState(() => !isActive);

  const logoTargetRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // The form stays unreachable (inert + disabled) until the reveal stage has
  // fully finished, so nothing can be clicked or focused before it is ready.
  const introLocked = isActive && idx < 8;

  useEffect(() => {
    const panel = panelRef.current as (HTMLDivElement & { inert?: boolean }) | null;
    if (panel) {
      panel.inert = introLocked;
    }
  }, [introLocked]);

  const [mode, setMode] = useState<LoginMode>('signIn');
  const [email, setEmail] = useState(() => getRememberedEmail() ?? '');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(() => Boolean(getRememberedEmail()));
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Forgot-password (Supabase reset request) state.
  const [isResetting, setIsResetting] = useState(false);
  const [resetMessage, setResetMessage] = useState<string | null>(null);
  const [resetError, setResetError] = useState<string | null>(null);

  const from =
    (location.state as { from?: { pathname?: string } })?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;
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

    // Remember me stores the e-mail ONLY — never the password, and never a
    // change to Supabase session persistence. Unchecking clears the value.
    if (rememberMe) {
      setRememberedEmail(trimmedEmail);
    } else {
      setRememberedEmail(null);
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

  const handleResetRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isResetting) return;
    setResetError(null);
    setResetMessage(null);

    const trimmedEmail = email.trim();
    if (!EMAIL_PATTERN.test(trimmedEmail)) {
      setResetError('Please enter a valid email address.');
      return;
    }

    setIsResetting(true);
    try {
      const result = await resetPasswordUser(trimmedEmail);
      if (result.error) {
        setResetError(result.error);
      } else {
        // Neutral, non-enumerating confirmation: we only report that the
        // request was accepted, never whether the address is registered.
        setResetMessage(
          'If an account exists for this email, a password reset link has been sent.'
        );
      }
    } catch {
      setResetError('Something went wrong while requesting the reset. Please try again.');
    } finally {
      setIsResetting(false);
    }
  };

  const startResetFlow = () => {
    setMode('reset');
    setErrorMessage(null);
    setResetError(null);
    setResetMessage(null);
  };

  const backToSignIn = () => {
    setMode('signIn');
    setResetError(null);
    setResetMessage(null);
  };

  const revealed = !isActive || idx >= 7;
  const placeholderVisible = !isActive || idx >= 8;
  const fieldDisabled = isSubmitting || isResetting || introLocked;

  return (
    <div
      className={`pixel-t-login relative flex min-h-screen w-full flex-col lg:flex-row ${
        introSkipped ? 'pixel-t-login--enter' : ''
      }`}
    >
      {isActive && <OpeningAnimation stage={stage} targetRef={logoTargetRef} />}

      {/* ---------------- Left: branding panel (always navy) ---------------- */}
      <aside className="pixel-t-navy-surface relative flex w-full flex-col items-center justify-center overflow-hidden px-6 py-14 text-center lg:w-[47%] lg:py-16">
        <div className="relative z-10 flex w-full max-w-sm flex-col items-center gap-6">
          {/* FLIP target. `.pixel-t-logo-box` is a pure geometry wrapper (transparent,
              aspect-ratio 548/142 = the logo's real ink bounds) — it renders no
              background, no border and no shadow, so the branding panel never
              shows a white rectangle behind the artwork. */}
          <div
            ref={logoTargetRef}
            className={`pixel-t-logo-box w-[min(380px,84vw)] ${
              placeholderVisible ? '' : 'opacity-0'
            }`}
          >
            <LogoPixelT variant="light" />
          </div>
          <div className="h-px w-16 bg-accent-600" aria-hidden="true" />
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-white/85">
            Clinical AI Analysis
          </p>
          <p className="text-base font-normal leading-relaxed text-white/60">
            AI-powered analysis
            <br />
            for better clinical decisions
          </p>
        </div>
        <div className="pixel-t-brand-deco-ring" aria-hidden="true" />
        <div className="pixel-t-brand-deco-disc" aria-hidden="true" />
      </aside>

      {/* ---------------- Right: form panel (dark card, matches final reference) ---------------- */}
      <section className="dark flex flex-1 items-center justify-center bg-dark-bg px-5 py-12 sm:px-10">
        <div className="w-full max-w-md rounded-2xl border border-dark-border/70 bg-dark-surface/80 p-6 shadow-[0_24px_70px_rgba(2,10,18,0.5)] backdrop-blur-sm sm:p-8">
          <div
            ref={panelRef}
            className={`pixel-t-login__reveal flex flex-col gap-6 ${
              revealed ? 'is-revealed' : ''
            }`}
            aria-hidden={introLocked || undefined}
          >
            {/* Heading */}
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-dark-text sm:text-3xl">
                {mode === 'signIn' ? 'Welcome Back' : 'Reset Your Password'}
              </h1>
              <p className="mt-2 text-sm leading-relaxed text-neutral-600 dark:text-dark-textMuted">
                {mode === 'signIn'
                  ? 'Sign in to your PIXEL-T account'
                  : 'Enter your email and we will send you a password reset link'}
              </p>
            </div>

            {/* Messages (authentication error / reset flow feedback) */}
            {mode === 'signIn' && errorMessage && (
              <div
                role="alert"
                className="flex items-start gap-2.5 rounded-md border border-semantic-error/30 bg-semantic-error/10 p-3 text-xs text-badgeText-error dark:text-badgeText-error-dark"
              >
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
                <p className="leading-relaxed">{errorMessage}</p>
              </div>
            )}
            {mode === 'reset' && resetError && (
              <div
                role="alert"
                className="flex items-start gap-2.5 rounded-md border border-semantic-error/30 bg-semantic-error/10 p-3 text-xs text-badgeText-error dark:text-badgeText-error-dark"
              >
                <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden="true" />
                <p className="leading-relaxed">{resetError}</p>
              </div>
            )}
            {mode === 'reset' && resetMessage && (
              <div
                role="status"
                className="rounded-md border border-accent-600/40 bg-accent-50 p-3 text-xs leading-relaxed text-neutral-700 dark:border-accent-500/40 dark:bg-dark-accentSurface dark:text-dark-textMuted"
              >
                {resetMessage}
              </div>
            )}

            {mode === 'signIn' ? (
              <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                <Input
                  label="Email address"
                  type="email"
                  placeholder="name@institution.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={fieldDisabled}
                  required
                  autoComplete="email"
                />

                <div className="relative">
                  <Input
                    label="Password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={fieldDisabled}
                    required
                    autoComplete="current-password"
                    className="pr-11"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    aria-pressed={showPassword}
                    disabled={fieldDisabled}
                    className="absolute bottom-1 right-1 rounded-md p-2 text-neutral-500 transition-colors hover:text-neutral-700 focus:outline-none focus:ring-2 focus:ring-primary-700/40 disabled:cursor-not-allowed dark:text-dark-textMuted dark:hover:text-dark-text"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" aria-hidden="true" />
                    ) : (
                      <Eye className="h-4 w-4" aria-hidden="true" />
                    )}
                  </button>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <label className="flex cursor-pointer items-center gap-2 text-sm text-neutral-600 dark:text-dark-textMuted">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      disabled={fieldDisabled}
                      className="h-4 w-4 cursor-pointer rounded border-neutral-300 accent-primary-900"
                    />
                    <span>Remember me</span>
                  </label>
                  <button
                    type="button"
                    onClick={startResetFlow}
                    disabled={fieldDisabled}
                    className="rounded-sm text-sm font-medium text-accent-600 transition-colors hover:text-accent-700 focus:outline-none focus:ring-2 focus:ring-accent-600/50 disabled:cursor-not-allowed dark:text-accent-500 dark:hover:text-accent-500"
                  >
                    Forgot password?
                  </button>
                </div>

                <div className="pt-2">
                  <Button
                    type="submit"
                    variant="primary"
                    size="md"
                    className="w-full"
                    isLoading={isSubmitting}
                    disabled={introLocked}
                    rightIcon={<ArrowRight className="h-4 w-4" />}
                  >
                    Sign In
                  </Button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleResetRequest} className="space-y-4" noValidate>
                <Input
                  label="Email address"
                  type="email"
                  placeholder="name@institution.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isResetting || introLocked}
                  required
                  autoComplete="email"
                  autoFocus
                />

                <div className="pt-2">
                  <Button
                    type="submit"
                    variant="primary"
                    size="md"
                    className="w-full"
                    isLoading={isResetting}
                    disabled={introLocked}
                    rightIcon={<Send className="h-4 w-4" />}
                  >
                    Send Reset Link
                  </Button>
                </div>
              </form>
            )}

            {/* Footer */}
            {mode === 'signIn' ? (
              <p className="pt-2 text-center text-sm text-neutral-600 dark:text-dark-textMuted">
                Don't have an account?{' '}
                <Link
                  to="/register"
                  className="rounded-sm font-semibold text-accent-600 transition-colors hover:text-accent-700 focus:outline-none focus:ring-2 focus:ring-accent-600/50 dark:text-accent-500"
                >
                  Register
                </Link>
              </p>
            ) : (
              <p className="pt-2 text-center text-sm text-neutral-600 dark:text-dark-textMuted">
                <button
                  type="button"
                  onClick={backToSignIn}
                  className="rounded-sm font-semibold text-accent-600 transition-colors hover:text-accent-700 focus:outline-none focus:ring-2 focus:ring-accent-600/50 dark:text-accent-500"
                >
                  Back to sign in
                </button>
              </p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Login;
