export const API_BASE = import.meta.env.VITE_API_URL ?? '';

export type Citacao = {
  id: number;
  documento: string;
  namespace: string;
  pagina: number | null;
  trecho: string;
  verificada: boolean;
};

export async function apiFetch(path: string, init: RequestInit = {}, token?: string | null): Promise<Response> {
  return fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...init.headers,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
}

export async function readError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (data && typeof data.detail === 'string') return data.detail;
  } catch {
    // corpo não é JSON ou está vazio
  }
  return `Erro ${res.status}`;
}
