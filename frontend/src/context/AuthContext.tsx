import React, { createContext, useContext, useEffect, useState, useMemo, useRef } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import {
  loginUser,
  registerUser,
  logoutUser,
  getCurrentSession,
  onAuthStateChange,
  fetchUserProfileStatus,
  getAdminRoleFromAppMetadata,
  isRoleMatch,
} from '@/services/auth';

/** Versioned sessionStorage key for one-time startup session reset per tab session. */
const STARTUP_RESET_KEY = 'pixel-t-startup-reset-v1';

export interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  /** 'doctor' | 'admin' | null */
  role: string | null;
  /** 'pending' | 'approved' | 'rejected' | null */
  accountStatus: string | null;
  signIn: (
    email: string,
    password: string,
    selectedRole?: 'admin' | 'doctor'
  ) => Promise<{ error?: string; role?: string | null; accountStatus?: string | null }>;
  signUp: (
    email: string,
    password: string,
    fullName?: string,
    hospitalName?: string,
    doctorSpecialty?: string
  ) => Promise<{
    error?: string;
    message?: string;
    /**
     * true when Supabase created the account but no session was returned,
     * which means the e-mail confirmation step is still pending.
     */
    requiresEmailConfirmation?: boolean;
  }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [role, setRole] = useState<string | null>(null);
  const [accountStatus, setAccountStatus] = useState<string | null>(null);
  const isVerifyingRoleRef = useRef<boolean>(false);

  useEffect(() => {
    let isMounted = true;

    // --- Startup session reset (once per tab session) ---
    const alreadyReset = sessionStorage.getItem(STARTUP_RESET_KEY);
    if (!alreadyReset) {
      sessionStorage.setItem(STARTUP_RESET_KEY, '1');
      logoutUser().then(() => {
        if (!isMounted) return;
        restoreSession();
      });
      return;
    }

    restoreSession();

    function restoreSession() {
      getCurrentSession().then((initialSession) => {
        if (!isMounted) return;
        setSession(initialSession);
        setUser(initialSession?.user ?? null);
        // Fetch role/status after restoring session.
        // Check app_metadata.role FIRST (trusted server-write-only source for admin),
        // THEN fall back to doctor_profiles lookup. This ensures admins are correctly
        // identified even though they have no doctor_profiles row.
        if (initialSession?.user) {
          const appMetaRole = getAdminRoleFromAppMetadata(initialSession.user);
          if (appMetaRole === 'admin') {
            if (!isMounted) return;
            setRole('admin');
            setAccountStatus(null);
          } else {
            fetchUserProfileStatus(initialSession.user).then((info) => {
              if (!isMounted) return;
              setRole(info?.role ?? null);
              setAccountStatus(info?.accountStatus ?? null);
            });
          }
        }
        setLoading(false);
      }).catch(() => {
        if (!isMounted) return;
        setSession(null);
        setUser(null);
        setLoading(false);
      });

      const { unsubscribe } = onAuthStateChange((_event, currentSession) => {
        if (!isMounted) return;
        if (isVerifyingRoleRef.current) {
          // Explicit signIn with role verification is actively in progress.
          // Do not update auth context state until role match is validated.
          return;
        }
        setSession(currentSession);
        setUser(currentSession?.user ?? null);
        // Fetch role/status on auth state change.
        // Same logic as restoreSession: check app_metadata.role first, then doctor_profiles.
        if (currentSession?.user) {
          const appMetaRole = getAdminRoleFromAppMetadata(currentSession.user);
          if (appMetaRole === 'admin') {
            if (!isMounted) return;
            setRole('admin');
            setAccountStatus(null);
          } else {
            fetchUserProfileStatus(currentSession.user).then((info) => {
              if (!isMounted) return;
              setRole(info?.role ?? null);
              setAccountStatus(info?.accountStatus ?? null);
            });
          }
        } else {
          setRole(null);
          setAccountStatus(null);
        }
        setLoading(false);
      });

      return () => {
        isMounted = false;
        unsubscribe();
      };
    }
  }, []);

  const signIn = async (
    email: string,
    password: string,
    selectedRole?: 'admin' | 'doctor'
  ): Promise<{ error?: string; role?: string | null; accountStatus?: string | null }> => {
    isVerifyingRoleRef.current = true;
    try {
      const result = await loginUser(email, password, selectedRole);
      if (result.error) {
        isVerifyingRoleRef.current = false;
        return { error: result.error };
      }
      if (result.data) {
        // Resolve the actual role and status from trusted sources:
        // - Admin: app_metadata.role (server-write-only)
        // - Doctor: doctor_profiles.role / account_status
        const appMetaRole = getAdminRoleFromAppMetadata(result.data.user);
        let actualRole: string | null = null;
        let actualStatus: string | null = null;

        if (appMetaRole === 'admin') {
          actualRole = 'admin';
        } else {
          const profileInfo = await fetchUserProfileStatus(result.data.user);
          actualRole = profileInfo?.role ?? 'doctor';
          actualStatus = profileInfo?.accountStatus ?? null;
        }

        // Two-way strict equality check
        const targetSelectedRole = selectedRole ?? 'doctor';
        if (!isRoleMatch(targetSelectedRole, actualRole)) {
          // Immediately purge Supabase session and reset context state
          await logoutUser();
          setUser(null);
          setSession(null);
          setRole(null);
          setAccountStatus(null);
          isVerifyingRoleRef.current = false;
          return {
            error:
              'Jenis akun yang dipilih tidak sesuai dengan akun ini. Silakan pilih jenis akun yang benar.',
          };
        }

        // Role matches: commit authenticated user and session
        setUser(result.data.user);
        setSession(result.data.session);
        setRole(actualRole);
        setAccountStatus(actualStatus);
        isVerifyingRoleRef.current = false;

        return { role: actualRole, accountStatus: actualStatus };
      }
      isVerifyingRoleRef.current = false;
      return {};
    } catch {
      await logoutUser();
      setUser(null);
      setSession(null);
      setRole(null);
      setAccountStatus(null);
      isVerifyingRoleRef.current = false;
      return { error: 'Terjadi kesalahan yang tidak terduga saat mencoba masuk.' };
    }
  };

  const signUp = async (
    email: string,
    password: string,
    fullName?: string,
    hospitalName?: string,
    doctorSpecialty?: string
  ): Promise<{
    error?: string;
    message?: string;
    requiresEmailConfirmation?: boolean;
  }> => {
    const result = await registerUser(email, password, fullName, hospitalName, doctorSpecialty);
    if (result.error) {
      return { error: result.error };
    }

    if (result.data?.session && result.data.user) {
      setUser(result.data.user);
      setSession(result.data.session);
      const info = await fetchUserProfileStatus(result.data.user);
      setRole(info?.role ?? 'doctor');
      setAccountStatus(info?.accountStatus ?? 'pending');
      return { message: 'Akun PIXEL-T Anda berhasil dibuat. Anda akan dapat mengakses aplikasi setelah akun disetujui oleh administrator rumah sakit.' };
    }

    return {
      message: 'Pendaftaran akun PIXEL-T Anda telah diproses dan sedang menunggu persetujuan administrator rumah sakit.',
      requiresEmailConfirmation: true,
    };
  };

  const signOut = async (): Promise<void> => {
    await logoutUser();
    setUser(null);
    setSession(null);
    setRole(null);
    setAccountStatus(null);
  };

  const contextValue = useMemo<AuthContextType>(
    () => ({
      user,
      session,
      loading,
      role,
      accountStatus,
      signIn,
      signUp,
      signOut,
    }),
    [user, session, loading, role, accountStatus]
  );

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
