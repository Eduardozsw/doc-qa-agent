import { Session } from '@supabase/supabase-js';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

export function useAuthFetch(session: Session | null) {
  return (url: string, options: RequestInit = {}): Promise<Response> =>
    fetch(`${API_BASE}${url}`, {
      ...options,
      headers: {
        ...options.headers,
        ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
      },
    });
}
