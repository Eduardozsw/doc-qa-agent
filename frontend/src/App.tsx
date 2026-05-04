import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Sparkles, FileText, X } from 'lucide-react';
import { Session } from '@supabase/supabase-js';
import { PDFUpload } from './components/PDFUpload';
import { PlanLimitModal } from './components/PlanLimitModal';
import { QuestionInput } from './components/QuestionInput';
import { AnswerSection } from './components/AnswerSection';
import { UserMenu } from './components/UserMenu';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { PrivacyPolicyPage } from './pages/PrivacyPolicyPage';
import { TermsOfServicePage } from './pages/TermsOfServicePage';
import { SettingsPage } from './pages/SettingsPage';
import { SuccessPage } from './pages/SuccessPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { useAuth } from './contexts/AuthContext';
import { useAuthFetch } from './hooks/useAuthFetch';
import { useFileManagement } from './hooks/useFileManagement';
import { useJobPolling } from './hooks/useJobPolling';
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
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={user ? <Navigate to="/app" replace /> : <LoginPage />} />
      <Route path="/app" element={user ? <MainApp session={session} /> : <Navigate to="/login" replace />} />
      <Route path="/configuracoes" element={user ? <SettingsPage /> : <Navigate to="/login" replace />} />
      <Route path="/privacidade" element={<PrivacyPolicyPage />} />
      <Route path="/termos" element={<TermsOfServicePage />} />
      <Route path="/sucesso" element={<SuccessPage />} />
      <Route path="/redefinir-senha" element={<ResetPasswordPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

const PLAN_MAX_FILES: Record<string, number> = { free: 3, solo: 10, pro: 20 };

function MainApp({ session }: { session: Session | null }) {
  const navigate = useNavigate();
  const { profile } = useAuth();
  const authFetch = useAuthFetch(session);
  const maxFiles = PLAN_MAX_FILES[profile?.plan ?? 'free'] ?? 3;
  const {
    indexedFiles, pendingFiles, searchSelected, ingestStatus, ingestError, ingestWarning,
    slotsAvailable, activeJobs, handleJobDone, handleToggleSearch, handleAddFiles, handleRemovePending,
    handleIngest, handleIngestFromDrive, handleRemoveIndexed, loadIndexedFiles, dismissWarning,
  } = useFileManagement(authFetch, maxFiles);

  const { jobs: jobStatuses } = useJobPolling(authFetch, activeJobs, handleJobDone);

  const [question, setQuestion] = useState('');
  const [history, setHistory] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 768);

  useEffect(() => {
    loadIndexedFiles();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 767px)');
    const handler = (e: MediaQueryListEvent) => {
      setIsMobile(e.matches);
      if (!e.matches) setSidebarOpen(false);
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const handleSubmit = async () => {
    if (ingestStatus !== 'ready' || !question.trim()) return;

    const currentQuestion = question.trim();
    setQuestion('');
    setLoading(true);

    setHistory(prev => [...prev, { question: currentQuestion, answer: '', sources: [] }]);

    const namespacesToQuery = searchSelected.size > 0 ? Array.from(searchSelected) : [];

    try {
      const res = await authFetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: currentQuestion, namespaces: namespacesToQuery }),
      });

      if (!res.ok) throw new Error(`Erro ${res.status}`);

      const data = await res.json();
      setHistory(prev => prev.map((m, i) =>
        i === prev.length - 1 ? { ...m, answer: data.resposta, sources: data.fontes ?? [] } : m
      ));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Erro ao consultar. Tente novamente.';
      setHistory(prev => prev.map((m, i) =>
        i === prev.length - 1 ? { ...m, answer: `Erro: ${message}`, sources: [] } : m
      ));
    } finally {
      setLoading(false);
    }
  };

  const canSubmit = (ingestStatus === 'ready' || ingestStatus === 'partial') && question.trim().length > 0 && !loading;

  const handleUpgradeSolo = async () => {
    try {
      const res = await authFetch('/api/billing/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan: 'solo' }),
      });
      const data = await res.json();
      if (data.url) window.location.href = data.url;
    } catch {
      // mantém o modal aberto
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: DARK.bg, fontFamily: 'inherit' }}>

      {/* Header */}
      <header style={{
        height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 16px', flexShrink: 0, zIndex: 10,
        borderBottom: `1px solid ${DARK.borderLight}`,
        background: 'rgba(8,8,15,0.95)',
        backdropFilter: 'blur(16px)',
      }}>
        <button
          onClick={() => navigate('/')}
          style={{ display: 'flex', alignItems: 'center', gap: 8, background: 'none', border: 'none', cursor: 'pointer' }}
        >
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Sparkles style={{ width: 14, height: 14, color: 'white' }} />
          </div>
          <span style={{ fontWeight: 600, fontSize: 14, color: 'white', letterSpacing: '-0.3px' }}>MindDoc</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {isMobile && (
            <button
              onClick={() => setSidebarOpen(v => !v)}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                background: sidebarOpen ? 'rgba(245,158,11,0.12)' : 'rgba(255,255,255,0.06)',
                border: `1px solid ${sidebarOpen ? DARK.accentBorder : DARK.border}`,
                borderRadius: 8, padding: '5px 10px', cursor: 'pointer',
                color: sidebarOpen ? DARK.accent : DARK.textMuted,
                fontSize: 12, fontWeight: 500, transition: 'all 0.2s',
              }}
            >
              {sidebarOpen
                ? <X style={{ width: 14, height: 14 }} />
                : <FileText style={{ width: 14, height: 14 }} />}
              {sidebarOpen ? 'Fechar' : 'Documentos'}
            </button>
          )}
          <UserMenu />
        </div>
      </header>

      {/* Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden', position: 'relative' }}>

        {/* Overlay mobile */}
        {isMobile && sidebarOpen && (
          <div
            onClick={() => setSidebarOpen(false)}
            style={{
              position: 'fixed', inset: 0, top: 56,
              background: 'rgba(0,0,0,0.55)', zIndex: 40,
              backdropFilter: 'blur(2px)',
            }}
          />
        )}

        {/* Sidebar */}
        <aside style={isMobile ? {
          position: 'fixed', left: 0, top: 56, bottom: 0,
          width: 280, zIndex: 50,
          borderRight: `1px solid ${DARK.border}`,
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
          background: '#0d0d1a',
          transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
          transition: 'transform 0.25s ease',
        } : {
          width: 260, flexShrink: 0,
          borderRight: `1px solid ${DARK.border}`,
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
          background: '#0d0d1a',
        }}>
          <PDFUpload
            indexedFiles={indexedFiles}
            pendingFiles={pendingFiles}
            searchSelected={searchSelected}
            onToggleSearch={handleToggleSearch}
            onAddFiles={handleAddFiles}
            onRemovePending={handleRemovePending}
            onRemoveIndexed={handleRemoveIndexed}
            onIngestFromDrive={handleIngestFromDrive}
            onSubmit={handleIngest}
            slotsAvailable={slotsAvailable}
            isLoading={ingestStatus === 'loading'}
            ingestStatus={ingestStatus}
            ingestError={ingestError}
            jobStatuses={jobStatuses}
          />
        </aside>

        {/* Chat */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: '#0a0a14' }}>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: isMobile ? '16px' : '24px 32px', position: 'relative' }}>
            {history.length > 0 && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
                <button
                  onClick={() => setHistory([])}
                  style={{
                    fontSize: 11, color: 'rgba(255,255,255,0.25)',
                    background: 'none', border: 'none', cursor: 'pointer',
                    transition: 'color 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.color = '#f87171')}
                  onMouseLeave={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.25)')}
                >
                  Limpar conversa
                </button>
              </div>
            )}
            <AnswerSection history={history} loading={loading} />
          </div>

          {/* Input */}
          <div style={{
            flexShrink: 0,
            padding: isMobile ? '12px 16px 16px' : '16px 24px 20px',
            borderTop: `1px solid ${DARK.border}`,
          }}>
            <QuestionInput
              question={question}
              onQuestionChange={setQuestion}
              onSubmit={handleSubmit}
              disabled={!canSubmit}
              loading={loading}
            />
          </div>
        </div>
      </div>

      {/* Modal de limite de documentos */}
      {ingestWarning && ingestStatus === 'partial' && (
        <PlanLimitModal
          warning={ingestWarning}
          onClose={dismissWarning}
          onUpgrade={handleUpgradeSolo}
        />
      )}
    </div>
  );
}

export default App;
