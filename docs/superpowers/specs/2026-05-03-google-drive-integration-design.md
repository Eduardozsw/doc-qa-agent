# Google Drive Integration Design

**Date:** 2026-05-03  
**Branch:** 2FA  
**Status:** Approved

## Summary

Allow authenticated users to import PDFs directly from their Google Drive into the doc-qa-agent pipeline. The user selects one or more files via the native Google Picker modal; the backend downloads each file using the user's short-lived access token and feeds it into the existing ingest pipeline unchanged.

---

## Architecture

```
Frontend                      Backend (FastAPI)             Google Drive API
────────                      ─────────────────             ────────────────
[Conectar Drive] ──OAuth──►  (token fica só no browser)
[Importar do Drive] ──────►  file_ids + access_token ───►  Download PDF bytes
                              ↓
                         validate (≤50MB, %PDF- magic bytes)
                              ↓
                         pipeline existente
                         (Supabase Storage → Redis job → worker)
                              ↓
                         job_ids ◄──────────────────────── frontend polling
```

The backend pipeline is untouched from the point the bytes are available. The only new surface is: receive file_ids + token → download from Drive → feed existing pipeline.

The access token is never persisted — it lives only in the HTTP request scope.

---

## Frontend

### `useDriveAuth` hook

Manages OAuth incremental consent using the **Google Identity Services (GIS)** library (`accounts.oauth2.initTokenClient`).

- `connectDrive()` — opens Google consent popup requesting `drive.readonly` scope
- `accessToken: string | null` — held in React state (never localStorage)
- `isConnected: boolean` — derived from token presence
- Token expires in 1 hour; on 401 response, hook triggers re-consent automatically

### `DrivePickerButton` component

- Loads `https://apis.google.com/js/api.js` dynamically on mount
- On click: opens Google Picker with `setMultiSelectEnabled(true)` and MIME type filter for `application/pdf`
- On selection: calls `POST /api/v1/ingest/from-drive` with the array of selected files + current access token
- Hands the returned `job_ids` to the existing `useJobPolling` hook — no polling changes

### UI flow

- First visit: "Importar do Google Drive" → consent popup → Picker opens → multi-select PDFs
- Subsequent visits (token still valid): Picker opens directly
- Token expired: re-consent popup → Picker opens

---

## Backend

### New endpoint: `POST /api/v1/ingest/from-drive`

**Request body:**
```json
{
  "files": [
    { "file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms", "file_name": "report.pdf" }
  ],
  "access_token": "ya29...."
}
```

**Processing per file:**
1. GET `https://www.googleapis.com/drive/v3/files/{file_id}?alt=media` with `Authorization: Bearer {access_token}`
2. Validate: size ≤ 50MB, magic bytes start with `%PDF-`
3. Inject bytes into existing ingest pipeline (same code path as multipart upload)
4. Collect `job_id`

**Response:**
```json
{ "job_ids": ["abc123", "def456"] }
```

### New module: `backend/ingestion/drive_client.py`

Single function: `download_file(file_id: str, access_token: str) -> bytes`

Isolates Drive HTTP logic from the endpoint handler. Raises `HTTPException(400)` on Drive API errors (file not found, permission denied, wrong MIME type).

---

## Validation Rules

| Rule | Value | Notes |
|------|-------|-------|
| Max file size | 50MB | Same as manual upload |
| Accepted MIME | `application/pdf` | Enforced in Picker (UI) and magic bytes check (backend) |
| Max files per request | No explicit limit | Picker UX naturally limits to reasonable numbers |

---

## Environment Variables

| Variable | Where | Purpose |
|----------|-------|---------|
| `VITE_GOOGLE_CLIENT_ID` | Frontend | Already exists; must have `drive.readonly` scope enabled |
| `VITE_GOOGLE_API_KEY` | Frontend | New — required by Picker widget (restricted to app domain) |

No new backend env vars — the access token arrives in the request body.

---

## Google Cloud Console Setup (manual steps after implementation)

1. Enable **Google Drive API** in the project
2. Enable **Google Picker API** in the project
3. Add `https://www.googleapis.com/auth/drive.readonly` to the OAuth consent screen scopes
4. Create a new **API Key**, restrict it to:
   - Application: HTTP referrers (your domain)
   - API: Google Picker API
5. Add `VITE_GOOGLE_API_KEY` to the frontend `.env`

---

## What Does NOT Change

- `/ingest` endpoint and pipeline
- Redis job queue and worker
- `useJobPolling` hook
- Supabase Storage upload logic
- SHA256 deduplication
- All existing file validation logic
