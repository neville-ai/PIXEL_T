import React, { createContext, useContext, useEffect, useState, useMemo } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import {
  loginUser,
  registerUser,
  logoutUser,
  getCurrentSession,
  onAuthStateChange,
} from '@/services/auth';

export interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string, fullName?: string) => Promise<{ error?: string; message?: string }>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;

    // 1. Initial session restoration
    getCurrentSession().then((initialSession) => {
      if (!isMounted) return;
      setSession(initialSession);
      setUser(initialSession?.user ?? null);
      setLoading(false);
    }).catch(() => {
      if (!isMounted) return;
      setSession(null);
      setUser(null);
      setLoading(false);
    });

    // 2. Single auth state change listener
    const { unsubscribe } = onAuthStateChange((_event, currentSession) => {
      if (!isMounted) return;
      setSession(currentSession);
      setUser(currentSession?.user ?? null);
      setLoading(false);
    });

    return () => {
      isMounted = false;
      unsubscribe();
    };
  }, []);

  const signIn = async (email: string, password: string): Promise<{ error?: string }> => {
    const result = await loginUser(email, password);
    if (result.error) {
      return { error: result.error };
    }
    if (result.data) {
      setUser(result.data.user);
      setSession(result.data.session);
    }
    return {};
  };

  const signUp = async (
    email: string,
    password: string,
    fullName?: string
  ): Promise<{ error?: string; message?: string }> => {
    const result = await registerUser(email, password, fullName);
    if (result.error) {
      return { error: result.error };
    }
    if (result.data?.session) {
      setUser(result.data.user);
      setSession(result.data.session);
      return { message: 'Registrasi berhasil. Sesi aktif dibuat.' };
    }
    return {
      message: 'Registrasi berhasil. Silakan periksa email Anda jika konfirmasi email diaktifkan, atau silakan masuk.',
    };
  };

  const signOut = async (): Promise<void> => {
    await logoutUser();
    setUser(null);
    setSession(null);
  };

  const contextValue = useMemo<AuthContextType>(
    () => ({
      user,
      session,
      loading,
      signIn,
      signUp,
      signOut,
    }),
    [user, session, loading]
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
