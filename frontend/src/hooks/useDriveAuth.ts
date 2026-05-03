import { useState, useCallback } from 'react';

declare global {
  interface Window {
    google: {
      accounts: {
        oauth2: {
          initTokenClient: (config: {
            client_id: string;
            scope: string;
            callback: (response: { error?: string; access_token: string }) => void;
          }) => { requestAccessToken: (opts: { prompt: string }) => void };
        };
      };
    };
  }
}

function loadScript(src: string): Promise<void> {
  return new Promise((resolve) => {
    if (document.querySelector(`script[src="${src}"]`)) { resolve(); return; }
    const s = document.createElement('script');
    s.src = src;
    s.onload = () => resolve();
    document.head.appendChild(s);
  });
}

export function useDriveAuth() {
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const connectDrive = useCallback(async (): Promise<string> => {
    await loadScript('https://accounts.google.com/gsi/client');
    return new Promise((resolve, reject) => {
      const client = window.google.accounts.oauth2.initTokenClient({
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID as string,
        scope: 'https://www.googleapis.com/auth/drive.readonly',
        callback: (response) => {
          if (response.error) { reject(new Error(response.error)); return; }
          setAccessToken(response.access_token);
          resolve(response.access_token);
        },
      });
      client.requestAccessToken({ prompt: '' });
    });
  }, []);

  return { accessToken, connectDrive, isConnected: accessToken !== null };
}
