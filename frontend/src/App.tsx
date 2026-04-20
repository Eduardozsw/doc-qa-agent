import { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import { Session } from '@supabase/supabase-js';
import { PDFUpload } from './components/PDFUpload';
import { QuestionInput } from './components/QuestionInput';
import { AnswerSection } from './components/AnswerSection';
import { UserMenu } from './components/UserMenu';
import { LandingPage } from './pages/LandingPage';
import { useAuth } from './contexts/AuthContext';
import { useAuthFetch } from './hooks/useAuthFetch';
import { useFileManagement } from './hooks/useFileManagement';
import { DARK } from './constants/theme';

export type Message = { question: string; answer: string; sources: string[] };

function App() {
  const { user, session, loading: authLoading } = useAuth();

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: DARK.bg }}>
        <div className="w-6 h-6 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: `${DARK.accent} transparent transparent transparent` }} />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={user ? <Navigate to="/app" replace /> : <LandingPage />} />
      <Route path="/app" element={user ? <MainApp session={session} /> : <Navigate to="/" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function MainApp({ session }: { session: Session | null }) {
  const authFetch = useAuthFetch(session);
  const {
    indexedFiles, pendingFiles, searchSelected, ingestStatus, ingestError,
    slotsAvailable, handleToggleSearch, handleAddFiles, handleRemovePending,
    handleIngest, handleRemoveIndexed, loadIndexedFiles,
  } = useFileManagement(authFetch);

  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadIndexedFiles();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = async () => {
    if (ingestStatus !== 'ready' || !question.trim()) return;

    const currentQuestion = question.trim();
    setQuestion('');
    setLoading(true);

    const namespacesToQuery = searchSelected.size > 0 ? Array.from(searchSelected) : [];
    const historico = history.map(m => ({ pergunta: m.question, resposta: m.answer }));

    try {
      const res = await authFetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuestion, namespaces: namespacesToQuery, historico }),
      });

      if (!res.ok) throw new Error(`Erro ${res.status}`);

      const data = await res.json();
      setHistory(prev => [
        ...prev,
        { question: currentQuestion, answer: data.resposta, sources: data.fontes ?? [] },
      ]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao consultar. Tente novamente.';
      setHistory(prev => [
        ...prev,
        { question: currentQuestion, answer: `Erro: ${message}`, sources: [] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const canSubmit = ingestStatus === 'ready' && question.trim().length > 0 && !loading;

  return (
    <div className="min-h-screen font-sans" style={{ background: DARK.bg }}>
      {/* Ambient blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden>
        <div
          className="absolute rounded-full blur-3xl opacity-10"
          style={{ width: 500, height: 500, top: -150, left: -150, background: `radial-gradient(circle, ${DARK.accent}, transparent 70%)` }}
        />
        <div
          className="absolute rounded-full blur-3xl opacity-5"
          style={{ width: 400, height: 400, bottom: -100, right: -100, background: `radial-gradient(circle, ${DARK.sky}, transparent 70%)` }}
        />
      </div>

      {/* Header */}
      <header
        className="sticky top-0 z-40"
        style={{ backdropFilter: 'blur(16px)', background: 'rgba(8,8,15,0.85)', borderBottom: `1px solid ${DARK.borderLight}` }}
      >
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}
            >
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            
            <span className="font-display text-base text-white tracking-tight">DocAI</span>
            
          </div>
          <UserMenu />
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-10 sm:px-6 lg:px-8 relative">
        <div className="mb-8 text-center">
          <h1 className="font-display text-3xl sm:text-4xl text-white">Pergunte ao seu documento</h1>
          <p className="mt-2 text-sm font-sans" style={{ color: DARK.textMuted }}>
            Carregue até 5 PDFs e faça perguntas. A IA responde com base exclusiva no conteúdo.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">

          <div className="space-y-4">
            <div
              className="rounded-2xl p-6 space-y-6"
              style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}
            >
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
                isLoading={ingestStatus === 'loading'}
                ingestStatus={ingestStatus}
                ingestError={ingestError}
              />
              <div style={{ borderTop: `1px solid ${DARK.border}` }} />
              <QuestionInput
                question={question}
                onQuestionChange={setQuestion}
                onSubmit={handleSubmit}
                disabled={!canSubmit}
                loading={loading}
              />
            </div>

            {ingestStatus === 'idle' && indexedFiles.length === 0 && pendingFiles.length === 0 && (
              <div
                className="rounded-xl px-4 py-3 text-xs font-sans"
                style={{ background: 'rgba(245,158,11,0.08)', border: `1px solid ${DARK.accentBorder}`, color: '#fbbf24' }}
              >
                Selecione ao menos um arquivo PDF para habilitar o envio de perguntas.
              </div>
            )}
          </div>

          <div
            className="rounded-2xl p-6 flex flex-col"
            style={{ background: DARK.card, border: `1px solid ${DARK.border}`, minHeight: '360px' }}
          >
            <div className="flex items-center justify-between mb-5 pb-4" style={{ borderBottom: `1px solid ${DARK.border}` }}>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                <h2 className="text-sm font-sans font-semibold text-white">Conversa</h2>
              </div>
              {history.length > 0 && (
                <button
                  onClick={() => setHistory([])}
                  className="text-xs font-sans transition-colors hover:text-red-400"
                  style={{ color: DARK.textFaint }}
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
