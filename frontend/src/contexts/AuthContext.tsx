import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import {
  User,
  Session,
  Plan,
  getToken,
  setToken,
  clearToken,
  login as apiLogin,
  register as apiRegister,
  me as apiMe,
  updateMe as apiUpdateMe,
  logout as apiLogout,
} from '../lib/auth';

export type { Plan };

interface Profile {
  plan: Plan;
}

interface AuthContextType {
  user: User | null;
  session: Session | null;
  profile: Profile | null;
  loading: boolean;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, name?: string) => Promise<void>;
  signOut: () => Promise<void>;
  updateName: (name: string) => Promise<void>;
  updatePassword: (currentPassword: string, newPassword: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

function translateAuthError(message: string): string {
  const lower = message.toLowerCase();
  if (lower.includes('failed to fetch') || lower.includes('networkerror') || lower.includes('network request failed')) {
    return 'Não foi possível conectar ao servidor. Tente novamente.';
  }
  return message || 'Ocorreu um erro. Tente novamente.';
}

async function runAuthAction<T>(action: () => Promise<T>): Promise<T> {
  try {
    return await action();
  } catch (err) {
    throw new Error(translateAuthError(err instanceof Error ? err.message : String(err)));
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  const clearAuth = useCallback(() => {
    clearToken();
    setUser(null);
    setSession(null);
  }, []);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    setSession({ access_token: token });
    apiMe(token)
      .then(setUser)
      .catch(() => clearAuth())
      .finally(() => setLoading(false));
  }, [clearAuth]);

  useEffect(() => {
    const handler = () => clearAuth();
    window.addEventListener('auth:unauthorized', handler);
    return () => window.removeEventListener('auth:unauthorized', handler);
  }, [clearAuth]);

  const signInWithEmail = async (email: string, password: string) => {
    const res = await runAuthAction(() => apiLogin(email, password));
    setToken(res.access_token);
    setSession({ access_token: res.access_token });
    setUser(res.user);
  };

  const signUp = async (email: string, password: string, name?: string) => {
    const res = await runAuthAction(() => apiRegister(email, password, name));
    setToken(res.access_token);
    setSession({ access_token: res.access_token });
    setUser(res.user);
  };

  const signOut = async () => {
    const token = getToken();
    if (token) {
      try {
        await apiLogout(token);
      } catch {
        // best-effort — limpa localmente mesmo se o backend falhar
      }
    }
    clearAuth();
  };

  const updateName = async (name: string) => {
    if (!session) throw new Error('Não autenticado.');
    const updated = await runAuthAction(() => apiUpdateMe(session.access_token, { name }));
    setUser(updated);
  };

  const updatePassword = async (currentPassword: string, newPassword: string) => {
    if (!session) throw new Error('Não autenticado.');
    const updated = await runAuthAction(() =>
      apiUpdateMe(session.access_token, { password: newPassword, current_password: currentPassword }),
    );
    setUser(updated);
  };

  const profile: Profile | null = user ? { plan: user.plan } : null;

  return (
    <AuthContext.Provider
      value={{ user, session, profile, loading, signInWithEmail, signUp, signOut, updateName, updatePassword }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth deve ser usado dentro de <AuthProvider>');
  return ctx;
}
