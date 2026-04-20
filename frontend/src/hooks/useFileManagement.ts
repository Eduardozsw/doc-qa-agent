import { useState } from 'react';

export type IngestStatus = 'idle' | 'loading' | 'ready' | 'error';

const MAX_FILES = 5;

type AuthFetch = (url: string, options?: RequestInit) => Promise<Response>;

export function useFileManagement(authFetch: AuthFetch) {
  const [indexedFiles, setIndexedFiles] = useState<string[]>([]);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [searchSelected, setSearchSelected] = useState<Set<string>>(new Set());
  const [ingestStatus, setIngestStatus] = useState<IngestStatus>('idle');
  const [ingestError, setIngestError] = useState<string | null>(null);

  const slotsAvailable = MAX_FILES - indexedFiles.length - pendingFiles.length;

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
    setPendingFiles(prev => [...prev, ...newFiles.slice(0, MAX_FILES - indexedFiles.length - prev.length)]);
  };

  const handleRemovePending = (index: number) =>
    setPendingFiles(prev => prev.filter((_, i) => i !== index));

  const handleIngest = async () => {
    if (!pendingFiles.length) return;

    setIngestStatus('loading');
    setIngestError(null);

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

      const added: string[] = data.arquivos ?? [];
      setIndexedFiles(prev => [...prev, ...added]);
      addToSelected(added);
      setPendingFiles([]);
      setIngestStatus('ready');
    } catch {
      setIngestStatus('error');
      setIngestError('Falha ao conectar com o servidor.');
    }
  };

  const handleRemoveIndexed = async (toRemove: string[]) => {
    try {
      const res = await authFetch('/api/ingest', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ namespaces: toRemove }),
      });

      if (!res.ok) {
        const data = await res.json();
        setIngestError(data.detail ?? 'Erro ao remover arquivos.');
        return;
      }

      setIndexedFiles(prev => prev.filter(f => !toRemove.includes(f)));
      removeFromSelected(toRemove);
      if (indexedFiles.length - toRemove.length === 0 && pendingFiles.length === 0) {
        setIngestStatus('idle');
      }
    } catch {
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
    slotsAvailable,
    handleToggleSearch,
    handleAddFiles,
    handleRemovePending,
    handleIngest,
    handleRemoveIndexed,
    loadIndexedFiles,
  };
}
