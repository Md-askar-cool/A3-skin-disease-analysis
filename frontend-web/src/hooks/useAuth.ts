// ============================================================
// SafeSkin AI – useAuth Hook
// Wraps Supabase auth with typed state management
// ============================================================
import { useState, useEffect, useCallback } from 'react';
import type { Session, AuthError } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  session: Session | null;
  loading: boolean;
}

interface AuthActions {
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>;
  signUp: (
    email: string,
    password: string,
    fullName: string,
  ) => Promise<{ error: AuthError | null }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: AuthError | null }>;
  updatePassword: (newPassword: string) => Promise<{ error: AuthError | null }>;
}

export type UseAuthReturn = AuthState & AuthActions;

/**
 * Custom hook for Supabase authentication.
 * Subscribes to auth state changes and exposes typed actions.
 */
export function useAuth(): UseAuthReturn {
  const [state, setState] = useState<AuthState>({
    user: null,
    session: null,
    loading: true,
  });

  // ── Map Supabase user to our User type ──────────────────────
  const mapUser = (supaUser: typeof state.user | null): User | null => {
    if (!supaUser) return null;
    return supaUser;
  };

  // ── Fetch current session on mount ──────────────────────────
  useEffect(() => {
    let mounted = true;

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!mounted) return;
      setState({
        session,
        user: session?.user
          ? ({
              id: session.user.id,
              email: session.user.email ?? '',
              full_name: session.user.user_metadata?.full_name as string,
              avatar_url: session.user.user_metadata?.avatar_url as string,
              role: (session.user.user_metadata?.role as User['role']) ?? 'user',
              created_at: session.user.created_at,
            } satisfies User)
          : null,
        loading: false,
      });
    });

    // ── Listen for auth state changes ─────────────────────────
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!mounted) return;
      setState({
        session,
        user: session?.user
          ? ({
              id: session.user.id,
              email: session.user.email ?? '',
              full_name: session.user.user_metadata?.full_name as string,
              avatar_url: session.user.user_metadata?.avatar_url as string,
              role: (session.user.user_metadata?.role as User['role']) ?? 'user',
              created_at: session.user.created_at,
            } satisfies User)
          : null,
        loading: false,
      });
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  // ── Sign in with email/password ──────────────────────────────
  const signIn = useCallback(
    async (email: string, password: string) => {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      return { error };
    },
    [],
  );

  // ── Sign up ──────────────────────────────────────────────────
  const signUp = useCallback(
    async (email: string, password: string, fullName: string) => {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { full_name: fullName, role: 'user' },
          emailRedirectTo: `${window.location.origin}/login`,
        },
      });
      return { error };
    },
    [],
  );

  // ── Sign out ─────────────────────────────────────────────────
  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
  }, []);

  // ── Reset password (sends email) ─────────────────────────────
  const resetPassword = useCallback(async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    return { error };
  }, []);

  // ── Update password ──────────────────────────────────────────
  const updatePassword = useCallback(async (newPassword: string) => {
    const { error } = await supabase.auth.updateUser({ password: newPassword });
    return { error };
  }, []);

  // Suppress unused variable warning for mapUser
  void mapUser;

  return {
    ...state,
    signIn,
    signUp,
    signOut,
    resetPassword,
    updatePassword,
  };
}

export default useAuth;
