import { useState, useCallback } from 'react';
import { loadScript } from '../lib/loadScript';

import '../types/google.d.ts';

export function useDriveAuth() {
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const connectDrive = useCallback(async (): Promise<string> => {
    await loadScript('https://accounts.google.com/gsi/client');
    return new Promise((resolve, reject) => {
      const client = window.google.accounts.oauth2.initTokenClient({
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
        scope: 'https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/drive.metadata.readonly',
        callback: (response) => {
          if (response.error) { reject(new Error(response.error)); return; }
          setAccessToken(response.access_token);
          resolve(response.access_token);
        },
      });
      client.requestAccessToken({ prompt: 'consent' });
    });
  }, []);

  return { accessToken, connectDrive, isConnected: accessToken !== null };
}
