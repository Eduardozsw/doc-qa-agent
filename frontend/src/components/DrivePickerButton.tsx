import { useRef } from 'react';
import { useDriveAuth } from '../hooks/useDriveAuth';
import { DARK } from '../constants/theme';

declare global {
  interface Window {
    gapi: { load: (lib: string, cb: () => void) => void };
    google: {
      picker: {
        PickerBuilder: new () => {
          addView: (v: unknown) => unknown;
          setOAuthToken: (t: string) => unknown;
          setDeveloperKey: (k: string) => unknown;
          setCallback: (cb: (data: PickerData) => void) => unknown;
          enableFeature: (f: string) => unknown;
          build: () => { setVisible: (v: boolean) => void };
        };
        View: new (id: string) => { setMimeTypes: (m: string) => unknown };
        ViewId: { DOCS: string };
        Action: { PICKED: string };
        Feature: { MULTISELECT_ENABLED: string };
      };
    };
  }
}

interface PickerData {
  action: string;
  docs?: Array<{ id: string; name: string }>;
}

interface DrivePickerButtonProps {
  onFilesSelected: (files: Array<{ id: string; name: string }>, accessToken: string) => void;
  disabled?: boolean;
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
      .setDeveloperKey(import.meta.env.VITE_GOOGLE_API_KEY as string)
      .setCallback((data: PickerData) => {
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
    if (!pickerReady.current) {
      await loadScript('https://apis.google.com/js/api.js');
      await loadPickerLib();
      pickerReady.current = true;
    }
    const token = accessToken ?? await connectDrive();
    openPicker(token);
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
