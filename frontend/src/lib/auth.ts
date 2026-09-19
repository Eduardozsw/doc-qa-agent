import { apiFetch, readError } from './api';

export type Plan = 'free' | 'solo' | 'pro';

export interface User {
  id: string;
  email: string;
  name: string;
  plan: Plan;
}

export interface Session {
  access_token: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

const TOKEN_KEY = 'access_token';

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // localStorage indisponível (modo privado, etc.) — segue sem persistir
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignora
  }
}

async function parseAuthResponse(res: Response): Promise<AuthResponse> {
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await apiFetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return parseAuthResponse(res);
}

export async function register(email: string, password: string, name?: string): Promise<AuthResponse> {
  const res = await apiFetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, ...(name ? { name } : {}) }),
  });
  return parseAuthResponse(res);
}

export async function me(token: string): Promise<User> {
  const res = await apiFetch('/api/auth/me', {}, token);
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function updateMe(
  token: string,
  data: { name?: string; password?: string; current_password?: string },
): Promise<User> {
  const res = await apiFetch(
    '/api/auth/me',
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    },
    token,
  );
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function logout(token: string): Promise<void> {
  const res = await apiFetch('/api/auth/logout', { method: 'POST' }, token);
  if (!res.ok && res.status !== 204) throw new Error(await readError(res));
}
