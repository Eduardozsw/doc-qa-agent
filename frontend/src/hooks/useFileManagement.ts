import { useState, useCallback } from 'react';
import { JobState } from './useJobPolling';

export type IngestStatus = 'idle' | 'loading' | 'ready' | 'error' | 'partial';

type AuthFetch = (url: string, options?: RequestInit) => Promise<Response>;

export function useFileManagement(authFetch: AuthFetch, maxFiles: number) {
  const [indexedFiles, setIndexedFiles] = useState<string[]>([]);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [searchSelected, setSearchSelected] = useState<Set<string>>(new Set());
  const [ingestStatus, setIngestStatus] = useState<IngestStatus>('idle');
  const [ingestError, setIngestError] = useState<string | null>(null);
  const [ingestWarning, setIngestWarning] = useState<string | null>(null);
  const [activeJobs, setActiveJobs] = useState<JobState[]>([]);

  const slotsAvailable = maxFiles - indexedFiles.length - pendingFiles.length;

  const addToSelected = (names: string[]) =>
    setSearchSelected(prev => {
      const next = new Set(prev);
      names.forEach(n => next.add(n));
      return next;
    });

  const removeFromSelected = (names: string[]) =>
    setSearchSelected(prev => {
      const next = new Set(prev);
      names.forEach(n => next.delete(n));
      return next;
    });

  const handleToggleSearch = (name: string) =>
    setSearchSelected(prev => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });

  const handleAddFiles = (newFiles: File[]) => {
    if (newFiles.some(f => f.type !== 'application/pdf')) {
      setIngestError('Apenas arquivos PDF são aceitos.');
      return;
    }
    setIngestError(null);
    setPendingFiles(prev => [...prev, ...newFiles.slice(0, maxFiles - indexedFiles.length - prev.length)]);
  };

  const handleRemovePending = (index: number) =>
    setPendingFiles(prev => prev.filter((_, i) => i !== index));

  const handleJobDone = useCallback((job: JobState) => {
    if (job.namespace) {
      setIndexedFiles(prev => {
        if (prev.includes(job.namespace!)) return prev;
        return [...prev, job.namespace!];
      });
      addToSelected([job.namespace!]);
    }
    setActiveJobs(prev => {
      const updated = prev.map(j => j.job_id === job.job_id ? job : j);
      const stillActive = updated.filter(j => j.status === 'pending' || j.status === 'processing');
      if (stillActive.length === 0) {
        const hasError = updated.some(j => j.status === 'error');
        setIngestStatus(hasError ? 'partial' : 'ready');
        return [];
      }
      return updated;
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleIngest = async () => {
    if (!pendingFiles.length) return;

    setIngestStatus('loading');
    setIngestError(null);
    setIngestWarning(null);

    const formData = new FormData();
    pendingFiles.forEach(file => formData.append('files', file));

    try {
      const res = await authFetch('/api/ingest', { method: 'POST', body: formData });
      const data = await res.json();

      if (!res.ok) {
        setIngestStatus('error');
        setIngestError(data.detail ?? `Erro ${res.status}`);
        return;
      }

      const jobs: Array<{ job_id: string; filename: string }> = data.jobs ?? [];
      const skipped: string[] = data.skipped ?? [];

      const initialJobs: JobState[] = jobs.map(j => ({
        job_id: j.job_id,
        filename: j.filename,
        status: 'pending',
      }));

      setPendingFiles([]);
      setActiveJobs(initialJobs);

      if (skipped.length > 0) {
        setIngestWarning(`Arquivos ignorados por limite do plano: ${skipped.join(', ')}`);
      }

      if (initialJobs.length === 0) {
        setIngestStatus(skipped.length > 0 ? 'partial' : 'ready');
      }
    } catch {
      setIngestStatus('error');
      setIngestError('Falha ao conectar com o servidor.');
    }
  };

  const dismissWarning = () => {
    setIngestWarning(null);
    setIngestStatus(prev => prev === 'partial' ? 'ready' : prev);
  };

  const handleIngestFromDrive = async (
    driveFiles: Array<{ id: string; name: string }>,
    accessToken: string,
  ) => {
    setIngestStatus('loading');
    setIngestError(null);
    setIngestWarning(null);

    try {
      const res = await authFetch('/api/ingest/from-drive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          files: driveFiles.map(f => ({ file_id: f.id, file_name: f.name })),
          access_token: accessToken,
        }),
      });
      const data = await res.json();

      if (!res.ok) {
        setIngestStatus('error');
        setIngestError(data.detail ?? `Erro ${res.status}`);
        return;
      }

      const jobs: Array<{ job_id: string; filename: string }> = data.jobs ?? [];
      const skipped: string[] = data.skipped ?? [];

      const initialJobs: JobState[] = jobs.map(j => ({
        job_id: j.job_id,
        filename: j.filename,
        status: 'pending',
      }));

      setActiveJobs(initialJobs);

      if (skipped.length > 0) {
        setIngestWarning(`Arquivos ignorados por limite do plano: ${skipped.join(', ')}`);
      }

      if (initialJobs.length === 0) {
        setIngestStatus(skipped.length > 0 ? 'partial' : 'ready');
      }
    } catch {
      setIngestStatus('error');
      setIngestError('Falha ao conectar com o servidor.');
    }
  };

  const handleRemoveIndexed = async (toRemove: string[]) => {
    setIndexedFiles(prev => prev.filter(f => !toRemove.includes(f)));
    removeFromSelected(toRemove);
    if (indexedFiles.length - toRemove.length === 0 && pendingFiles.length === 0) {
      setIngestStatus('idle');
    }

    try {
      const res = await authFetch('/api/ingest', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ namespaces: toRemove }),
      });

      if (!res.ok) {
        const data = await res.json();
        setIndexedFiles(prev => [...prev, ...toRemove]);
        addToSelected(toRemove);
        setIngestError(data.detail ?? 'Erro ao remover arquivos.');
      }
    } catch {
      setIndexedFiles(prev => [...prev, ...toRemove]);
      addToSelected(toRemove);
      setIngestError('Falha ao conectar com o servidor.');
    }
  };

  const loadIndexedFiles = async () => {
    try {
      const res = await authFetch('/api/ingest');
      const data = await res.json();
      const files: string[] = data.arquivos ?? [];
      setIndexedFiles(files);
      addToSelected(files);
      if (files.length > 0) setIngestStatus('ready');
    } catch (err) {
      console.error('Erro ao buscar arquivos indexados:', err);
    }
  };

  return {
    indexedFiles,
    pendingFiles,
    searchSelected,
    ingestStatus,
    ingestError,
    ingestWarning,
    slotsAvailable,
    activeJobs,
    handleJobDone,
    handleToggleSearch,
    handleAddFiles,
    handleRemovePending,
    handleIngest,
    handleIngestFromDrive,
    handleRemoveIndexed,
    loadIndexedFiles,
    dismissWarning,
  };
}
