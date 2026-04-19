import { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import { PDFUpload } from './components/PDFUpload';
import { QuestionInput } from './components/QuestionInput';
import { AnswerSection } from './components/AnswerSection';
import { UserMenu } from './components/UserMenu';
import { LoginPage } from './pages/LoginPage';
import { useAuth } from './contexts/AuthContext';

type IngestStatus = 'idle' | 'loading' | 'ready' | 'error';

export type Message = { question: string; answer: string; sources: string[] };

const MAX_FILES = 5;

function App() {
  const { user, session, loading: authLoading } = useAuth();

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50/30 flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) return <LoginPage />;

  return <MainApp session={session} />;
}

function MainApp({ session }: { session: import('@supabase/supabase-js').Session | null }) {
  const authFetch = (url: string, options: RequestInit = {}) =>
    fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        ...(session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {}),
      },
    });

  const [indexedFiles, setIndexedFiles] = useState<string[]>([]);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [searchSelected, setSearchSelected] = useState<Set<string>>(new Set());
  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [ingestStatus, setIngestStatus] = useState<IngestStatus>('idle');
  const [ingestError, setIngestError] = useState<string | null>(null);

  useEffect(() => {
    authFetch('/api/ingest')
      .then((res) => res.json())
      .then((data) => {
        const files: string[] = data.arquivos ?? [];
        setIndexedFiles(files);
        setSearchSelected(new Set(files));
        if (files.length > 0) setIngestStatus('ready');
      })
      .catch(() => {});
  }, []);

  const slotsAvailable = MAX_FILES - indexedFiles.length - pendingFiles.length;

  const handleToggleSearch = (name: string) => {
    setSearchSelected((prev) => {
      const next = new Set(prev);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  };

  const handleAddFiles = (newFiles: File[]) => {
    const nonPdfs = newFiles.filter((f) => f.type !== 'application/pdf');
    if (nonPdfs.length) {
      setIngestError('Apenas arquivos PDF são aceitos.');
      return;
    }
    setIngestError(null);
    setPendingFiles((prev) => {
      const slots = MAX_FILES - indexedFiles.length - prev.length;
      return [...prev, ...newFiles.slice(0, slots)];
    });
  };

  const handleRemovePending = (index: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleIngest = async () => {
    if (!pendingFiles.length) return;

    setIngestStatus('loading');
    setIngestError(null);

    const formData = new FormData();
    pendingFiles.forEach((file) => formData.append('files', file));

    try {
      const res = await authFetch('/api/ingest', { method: 'POST', body: formData });
      const data = await res.json();

      if (!res.ok) {
        setIngestStatus('error');
        setIngestError(data.detail ?? `Erro ${res.status}`);
        return;
      }

      const added: string[] = data.arquivos ?? [];
      setIndexedFiles((prev) => [...prev, ...added]);
      setSearchSelected((prev) => {
        const next = new Set(prev);
        added.forEach((n) => next.add(n));
        return next;
      });
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

      setIndexedFiles((prev) => prev.filter((f) => !toRemove.includes(f)));
      setSearchSelected((prev) => {
        const next = new Set(prev);
        toRemove.forEach((n) => next.delete(n));
        return next;
      });
      if (indexedFiles.length - toRemove.length === 0 && pendingFiles.length === 0) {
        setIngestStatus('idle');
      }
    } catch {
      setIngestError('Falha ao conectar com o servidor.');
    }
  };

  const handleSubmit = async () => {
    if (ingestStatus !== 'ready' || !question.trim()) return;

    const currentQuestion = question.trim();
    setQuestion('');
    setLoading(true);

    const namespacesToQuery = searchSelected.size > 0 ? Array.from(searchSelected) : [];
    const historico = history.map((m) => ({ pergunta: m.question, resposta: m.answer }));

    try {
      const res = await authFetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuestion, namespaces: namespacesToQuery, historico }),
      });

      if (!res.ok) throw new Error(`Erro ${res.status}`);

      const data = await res.json();
      setHistory((prev) => [
        ...prev,
        { question: currentQuestion, answer: data.resposta, sources: data.fontes ?? [] },
      ]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao consultar. Tente novamente.';
      setHistory((prev) => [
        ...prev,
        { question: currentQuestion, answer: `Erro: ${message}`, sources: [] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const canSubmit = ingestStatus === 'ready' && question.trim().length > 0 && !loading;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50/30">
      <div className="max-w-5xl mx-auto px-4 py-10 sm:px-6 lg:px-8">

        <header className="mb-10">
          <div className="flex items-center justify-between mb-6">
            <div className="inline-flex items-center gap-2 bg-white border border-slate-200 rounded-full px-4 py-1.5 shadow-sm">
              <Sparkles className="w-4 h-4 text-sky-500" />
              <span className="text-xs font-medium text-slate-500 tracking-wide uppercase">RAG Assistant</span>
            </div>
            <UserMenu />
          </div>
          <div className="text-center">
            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
              Pergunte ao seu documento
            </h1>
            <p className="text-slate-500 mt-2 text-sm max-w-md mx-auto">
              Carregue até 5 PDFs e faça perguntas. A IA vai ler o conteúdo e responder com base nele.
            </p>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

          <div className="space-y-5">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 space-y-6">
              <PDFUpload
                indexedFiles={indexedFiles}
                pendingFiles={pendingFiles}
                searchSelected={searchSelected}
                onToggleSearch={handleToggleSearch}
                onAddFiles={handleAddFiles}
                onRemovePending={handleRemovePending}
                onRemoveIndexed={handleRemoveIndexed}
                onSubmit={handleIngest}
                slotsAvailable={slotsAvailable}
                ingestStatus={ingestStatus}
                ingestError={ingestError}
              />
              <div className="border-t border-slate-100" />
              <QuestionInput
                question={question}
                onQuestionChange={setQuestion}
                onSubmit={handleSubmit}
                disabled={!canSubmit}
                loading={loading}
              />
            </div>

            {ingestStatus === 'idle' && indexedFiles.length === 0 && pendingFiles.length === 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-xs text-amber-700">
                Selecione ao menos um arquivo PDF para habilitar o envio de perguntas.
              </div>
            )}
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 min-h-[320px] flex flex-col">
            <div className="flex items-center justify-between mb-5 pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                <h2 className="text-sm font-semibold text-slate-700">Conversa</h2>
              </div>
              {history.length > 0 && (
                <button
                  onClick={() => setHistory([])}
                  className="text-xs text-slate-400 hover:text-red-400 transition-colors"
                >
                  Limpar
                </button>
              )}
            </div>
            <div className="flex-1">
              <AnswerSection history={history} loading={loading} />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

export default App;
