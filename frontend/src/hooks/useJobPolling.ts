import { useEffect, useRef, useState } from 'react';

export type JobStatus = 'pending' | 'processing' | 'done' | 'error';

export interface JobState {
  job_id: string;
  filename: string;
  status: JobStatus;
  namespace?: string | null;
  error?: string | null;
}

type AuthFetch = (url: string, options?: RequestInit) => Promise<Response>;

export function useJobPolling(
  authFetch: AuthFetch,
  initialJobs: JobState[],
  onJobDone: (job: JobState) => void,
): { jobs: JobState[]; allSettled: boolean } {
  const [jobs, setJobs] = useState<JobState[]>(initialJobs);
  const onJobDoneRef = useRef(onJobDone);
  onJobDoneRef.current = onJobDone;
  const authFetchRef = useRef(authFetch);
  authFetchRef.current = authFetch;

  useEffect(() => {
    setJobs(initialJobs);
  }, [initialJobs.map(j => j.job_id).join(',')]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const activeIds = jobs
      .filter(j => j.status === 'pending' || j.status === 'processing')
      .map(j => j.job_id);

    if (!activeIds.length) return;

    const interval = setInterval(async () => {
      try {
        const res = await authFetchRef.current(`/api/ingest/status?jobs=${activeIds.join(',')}`);
        if (!res.ok) return;
        const data = await res.json();

        setJobs(prev => prev.map(j => {
          const updated = data.jobs?.[j.job_id];
          if (!updated) return j;
          const next: JobState = { ...j, status: updated.status, namespace: updated.namespace, error: updated.error };
          if (updated.status === 'done' && j.status !== 'done') {
            onJobDoneRef.current(next);
          }
          return next;
        }));
      } catch {
        // ignora falha de rede temporária
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [jobs.map(j => `${j.job_id}:${j.status}`).join(',')]); // eslint-disable-line react-hooks/exhaustive-deps

  const allSettled = jobs.every(j => j.status === 'done' || j.status === 'error');

  return { jobs, allSettled };
}
