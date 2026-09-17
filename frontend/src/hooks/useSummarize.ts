import { useState, useCallback, useRef } from 'react';
import { Session } from '../lib/auth';
import { useAuthFetch } from './useAuthFetch';

export type SummarizeStatus = 'idle' | 'ingesting' | 'summarizing' | 'done' | 'error';

export interface SummaryResult {
  topicos_abordados: string[];
  resumo: string;
  cached: boolean;
}

export interface PreviousSummary {
  namespace: string;
  filename: string | null;
  summary: SummaryResult;
}

export interface SummarizeUsage {
  used_this_month: number;
  limit: number;
  summaries: PreviousSummary[];
}

export function useSummarize(session: Session | null) {
  const authFetch = useAuthFetch(session);
  const [status, setStatus] = useState<SummarizeStatus>('idle');
  const [summary, setSummary] = useState<SummaryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  const [namespace, setNamespace] = useState<string | null>(null);
  const [usage, setUsage] = useState<SummarizeUsage | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const loadUsage = useCallback(async () => {
    try {
      const res = await authFetch('/api/summarize');
      if (!res.ok) return;
      const data = await res.json();
      setUsage(data);
    } catch {
      // silent — usage counter is non-critical
    }
  }, [authFetch]);

  const generate = useCallback(async (file: File) => {
    setStatus('ingesting');
    setError(null);
    setSummary(null);
    setFilename(file.name);
    setNamespace(null);

    try {
      const formData = new FormData();
      formData.append('files', file);
      const ingestRes = await authFetch('/api/ingest', { method: 'POST', body: formData });
      if (!ingestRes.ok) {
        const err = await ingestRes.json();
        throw new Error(err.detail ?? 'Erro ao enviar arquivo');
      }
      const ingestData = await ingestRes.json();
      const jobs: Array<{ job_id: string }> = ingestData.jobs ?? [];
      if (!jobs.length) throw new Error('Nenhum job retornado');
      const jobId = jobs[0].job_id;

      const ns = await new Promise<string>((resolve, reject) => {
        let elapsed = 0;
        pollingRef.current = setInterval(async () => {
          elapsed += 2000;
          if (elapsed > 120_000) {
            stopPolling();
            reject(new Error('Tempo limite de processamento atingido'));
            return;
          }
          try {
            const statusRes = await authFetch(`/api/ingest/status?jobs=${jobId}`);
            const statusData = await statusRes.json();
            const job = statusData.jobs?.[jobId];
            if (!job) return;
            if (job.status === 'done') {
              stopPolling();
              resolve(job.namespace);
            } else if (job.status === 'error') {
              stopPolling();
              reject(new Error(job.error ?? 'Erro ao processar arquivo'));
            }
          } catch (e) {
            stopPolling();
            reject(e);
          }
        }, 2000);
      });

      setNamespace(ns);
      setStatus('summarizing');

      const sumRes = await authFetch('/api/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ namespace: ns }),
      });
      if (!sumRes.ok) {
        const err = await sumRes.json();
        throw new Error(err.detail ?? 'Erro ao gerar resumo');
      }
      const sumData: SummaryResult = await sumRes.json();
      setSummary(sumData);
      setStatus('done');
      loadUsage();
    } catch (e: unknown) {
      stopPolling();
      setError(e instanceof Error ? e.message : 'Erro desconhecido');
      setStatus('error');
    }
  }, [authFetch, stopPolling, loadUsage]);

  const reset = useCallback(() => {
    stopPolling();
    setStatus('idle');
    setSummary(null);
    setError(null);
    setFilename(null);
    setNamespace(null);
  }, [stopPolling]);

  return { status, summary, error, filename, namespace, usage, generate, reset, loadUsage };
}
