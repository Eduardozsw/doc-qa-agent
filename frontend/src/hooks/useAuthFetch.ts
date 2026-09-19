import { Session } from '../lib/auth';
import { API_BASE } from '../lib/api';

export function useAuthFetch(session: Session | null) {
  return async (url: string, options: RequestInit = {}): Promise<Response> => {
    const res = await fetch(`${API_BASE}${url}`, {
      ...options,
      headers: {
        ...options.headers,
        ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
      },
    });
    if (res.status === 401) {
      window.dispatchEvent(new Event('auth:unauthorized'));
    }
    return res;
  };
}
