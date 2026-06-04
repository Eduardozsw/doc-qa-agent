import { useRef } from 'react';
import { useDriveAuth } from '../hooks/useDriveAuth';
import { loadScript } from '../lib/loadScript';

import '../types/google.d.ts';

interface DrivePickerButtonProps {
  onFilesSelected: (files: Array<{ id: string; name: string }>, accessToken: string) => void;
  disabled?: boolean;
}

function loadPickerLib(): Promise<void> {
  return new Promise((resolve) => window.gapi.load('picker', () => resolve()));
}

export function DrivePickerButton({ onFilesSelected, disabled }: DrivePickerButtonProps) {
  const { accessToken, connectDrive } = useDriveAuth();
  const pickerReady = useRef(false);

  const openPicker = (token: string) => {
    const view = new window.google.picker.View(window.google.picker.ViewId.DOCS)
      .setMimeTypes('application/pdf');

    const picker = new window.google.picker.PickerBuilder()
      .addView(view)
      .setOAuthToken(token)
      .setDeveloperKey(import.meta.env.VITE_GOOGLE_API_KEY)
      .setAppId('673862576917')
      .setCallback((data: GooglePickerData) => {
        if (data.action === window.google.picker.Action.PICKED && data.docs) {
          onFilesSelected(
            data.docs.map(d => ({ id: d.id, name: d.name })),
            token,
          );
        }
      })
      .enableFeature(window.google.picker.Feature.MULTISELECT_ENABLED)
      .build();
    picker.setVisible(true);
  };

  const handleClick = async () => {
    if (disabled) return;
    try {
      if (!pickerReady.current) {
        await loadScript('https://apis.google.com/js/api.js');
        await loadPickerLib();
        pickerReady.current = true;
      }
      const token = accessToken ?? await connectDrive();
      openPicker(token);
    } catch (err) {
      console.error('[DrivePickerButton] failed to open picker:', err);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      title="Importar do Google Drive"
      style={{
        width: 24, height: 24, borderRadius: 6,
        background: 'rgba(66,133,244,0.1)', border: '1px solid rgba(66,133,244,0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        cursor: disabled ? 'default' : 'pointer',
        color: '#4285f4', opacity: disabled ? 0.5 : 1, flexShrink: 0,
      }}
    >
      <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
        <path d="M6.28 3L1 12l4.28 7h13.44L23 12 17.72 3H6.28zM12 8.5l4.28 7H7.72L12 8.5z" />
      </svg>
    </button>
  );
}
