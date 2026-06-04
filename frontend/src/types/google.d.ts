declare global {
  interface Window {
    gapi: { load: (lib: string, cb: () => void) => void };
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
      picker: {
        PickerBuilder: new () => {
          addView: (v: unknown) => unknown;
          setOAuthToken: (t: string) => unknown;
          setDeveloperKey: (k: string) => unknown;
          setAppId: (id: string) => unknown;
          setCallback: (cb: (data: GooglePickerData) => void) => unknown;
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

  interface GooglePickerData {
    action: string;
    docs?: Array<{ id: string; name: string }>;
  }
}

export {};
