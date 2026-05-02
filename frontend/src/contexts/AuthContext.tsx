import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';

export type Plan = 'free' | 'solo' | 'pro';

interface Profile {
  plan: Plan;
  subscription_id: string | null;
  current_period_end: string | null;
}

interface AuthContextType {
  user: User | null;
  session: Session | null;
  profile: Profile | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  verifyOtp: (email: string, token: string) => Promise<void>;
  requestPasswordReset: (email: string) => Promise<void>;
  updateName: (name: string) => Promise<void>;
  updateEmail: (email: string) => Promise<void>;
  updatePassword: (password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

function translateAuthError(message: string): string {
  if (message.includes('Invalid login credentials')) return 'Email ou senha incorretos. Se você entrou com o Google, use o botão "Continuar com Google".';
  if (message.includes('User already registered')) return 'Este email já está cadastrado.';
  if (message.includes('Password should be at least')) return 'A senha deve ter no mínimo 6 caracteres.';
  if (message.includes('Unable to validate email')) return 'Email inválido.';
  if (message.includes('Email not confirmed')) return 'Confirme seu email antes de entrar.';
  if (message.includes('Token has expired') || message.includes('token is invalid') || message.includes('Invalid token')) return 'Código inválido ou expirado. Tente novamente.';
  if (message.includes('same password')) return 'A nova senha deve ser diferente da atual.';
  if (message.includes('For security purposes') || message.includes('email rate limit')) return 'Muitas tentativas. Aguarde alguns minutos e tente novamente.';
  return 'Ocorreu um erro. Tente novamente.';
}

async function fetchProfile(userId: string): Promise<Profile | null> {
  const { data, error } = await supabase
    .from('profiles')
    .select('plan, subscription_id, current_period_end')
    .eq('id', userId)
    .single();

  if (error) {
    console.error('Erro ao buscar perfil do usuário:', error);
    return null;
  }
  return data as Profile;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  const updateSession = async (newSession: Session | null) => {
    setSession(newSession);
    setUser(newSession?.user ?? null);
    setProfile(newSession?.user ? await fetchProfile(newSession.user.id) : null);
  };

  useEffect(() => {
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      await updateSession(session);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      updateSession(session);
    });

    return () => subscription.unsubscribe();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const signInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/app` },
    });
  };

  const signInWithEmail = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw new Error(translateAuthError(error.message));
  };

  const signUp = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (error) throw new Error(translateAuthError(error.message));
    if (!data.user) throw new Error('EMAIL_ALREADY_EXISTS');
  };

  const signOut = async () => {
    try {
      await supabase.auth.signOut();
    } catch {
      // ignora erro do servidor
    }
    setUser(null);
    setSession(null);
    setProfile(null);
  };

  const verifyOtp = async (email: string, token: string) => {
    const { error } = await supabase.auth.verifyOtp({ email, token, type: 'signup' });
    if (error) throw new Error(translateAuthError(error.message));
  };

  const requestPasswordReset = async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/redefinir-senha`,
    });
    if (error) throw new Error(translateAuthError(error.message));
  };

  const updateName = async (name: string) => {
    const { error } = await supabase.auth.updateUser({ data: { full_name: name } });
    if (error) throw new Error(translateAuthError(error.message));
  };

  const updateEmail = async (email: string) => {
    const { error } = await supabase.auth.updateUser({ email });
    if (error) throw new Error(translateAuthError(error.message));
  };

  const updatePassword = async (password: string) => {
    const { error } = await supabase.auth.updateUser({ password });
    if (error) throw new Error(translateAuthError(error.message));
  };

  return (
    <AuthContext.Provider value={{ user, session, profile, loading, signInWithGoogle, signInWithEmail, signUp, signOut, verifyOtp, requestPasswordReset, updateName, updateEmail, updatePassword }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth deve ser usado dentro de <AuthProvider>');
  return ctx;
}
