import { Session } from '@supabase/supabase-js';

export function useAuthFetch(session: Session | null) {
  return (url: string, options: RequestInit = {}): Promise<Response> =>
    fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
      },
    });
}
