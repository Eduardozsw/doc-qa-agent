import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, FileText, ArrowRight, Loader2, AlertCircle, Check, MessageSquare, RotateCcw } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useSummarize } from '../hooks/useSummarize';
import { UserMenu } from '../components/UserMenu';
import { DARK } from '../constants/theme';

export function ResumirPdfPage() {
  const { user, session } = useAuth();
  const navigate = useNavigate();
  const { status, summary, error, filename, namespace, usage, generate, reset, loadUsage } =
    useSummarize(session);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    if (user) loadUsage();
  }, [user, loadUsage]);

  const handleFiles = (files: FileList | null) => {
    if (!files || !files[0]) return;
    const file = files[0];
    if (file.type !== 'application/pdf') {
      setFileError('Apenas arquivos PDF são aceitos.');
      return;
    }
    setFileError(null);
    generate(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (!user) { navigate('/login?redirect=/resumir-pdf'); return; }
    handleFiles(e.dataTransfer.files);
  };

  const handleGenerateClick = () => {
    if (!user) { navigate('/login?redirect=/resumir-pdf'); return; }
    fileInputRef.current?.click();
  };

  const isLoading = status === 'ingesting' || status === 'summarizing';
  const usedRatio = usage ? usage.used_this_month / usage.limit : 0;

  return (
    <div className="min-h-screen font-sans antialiased" style={{ background: DARK.bg, color: DARK.text }}>

      {/* Ambient blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden>
        <div
          className="absolute rounded-full blur-3xl opacity-20"
          style={{ width: 600, height: 600, top: -200, left: -200, background: `radial-gradient(circle, ${DARK.accent}, transparent 70%)` }}
        />
        <div
          className="absolute rounded-full blur-3xl opacity-10"
          style={{ width: 500, height: 500, bottom: -150, right: -100, background: `radial-gradient(circle, ${DARK.sky}, transparent 70%)` }}
        />
      </div>

      {/* Navbar */}
      <nav
        className="fixed top-0 inset-x-0 z-50"
        style={{ backdropFilter: 'blur(16px)', background: 'rgba(8,8,15,0.85)', borderBottom: `1px solid ${DARK.borderLight}` }}
      >
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2" style={{ textDecoration: 'none' }}>
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}
            >
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-display text-lg text-white tracking-tight">MindDoc</span>
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Link
              to="/app"
              style={{
                fontSize: 12, fontWeight: 500,
                color: DARK.textMuted,
                textDecoration: 'none',
                padding: '5px 10px',
                transition: 'color 0.2s',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.color = 'white'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.color = DARK.textMuted; }}
            >
              Chat
            </Link>
            <span style={{
              fontSize: 12, fontWeight: 500,
              color: DARK.accent,
              padding: '5px 10px',
              borderRadius: 20,
              border: `1px solid ${DARK.accentBorder}`,
              background: DARK.accentSubtle,
              whiteSpace: 'nowrap',
            }}>
              Resumir PDF
            </span>
            {user ? (
              <UserMenu />
            ) : (
              <Link
                to="/login?redirect=/resumir-pdf"
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-sans font-semibold transition-all duration-200 hover:opacity-90 active:scale-95"
                style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`, color: DARK.bg, textDecoration: 'none' }}
              >
                Entrar
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            )}
          </div>
        </div>
      </nav>

      {/* Main */}
      <main className="pt-32 pb-24 px-6 relative z-10">
        <div className="max-w-2xl mx-auto">

          {/* ── Estado 2: Loading ── */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6"
                style={{ background: DARK.accentSubtle, border: `1px solid ${DARK.accentBorder}` }}
              >
                <FileText className="w-7 h-7" style={{ color: DARK.accent }} />
              </div>
              <h2 className="font-display text-2xl text-white mb-2">
                {status === 'ingesting' ? 'Indexando documento...' : 'Gerando resumo...'}
              </h2>
              <p className="text-sm font-sans mb-8" style={{ color: DARK.textMuted }}>
                {status === 'ingesting'
                  ? 'Processando o conteúdo do PDF para análise.'
                  : 'A IA está lendo e sintetizando o documento.'}
              </p>

              {/* Step indicator */}
              <div className="flex flex-col gap-3 items-start w-48">
                {[
                  { key: 'ingesting', label: 'Indexando documento' },
                  { key: 'summarizing', label: 'Gerando resumo' },
                ].map((step, i) => {
                  const isActive = step.key === status;
                  const isDone = (step.key === 'ingesting' && status === 'summarizing');
                  return (
                    <div key={step.key} className="flex items-center gap-3">
                      <div
                        className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300"
                        style={{
                          background: isDone ? DARK.emeraldSubtle : isActive ? DARK.accentSubtle : 'rgba(255,255,255,0.04)',
                          border: `1px solid ${isDone ? DARK.emeraldBorder : isActive ? DARK.accentBorder : DARK.border}`,
                        }}
                      >
                        {isDone ? (
                          <Check className="w-3 h-3" style={{ color: DARK.emerald }} />
                        ) : isActive ? (
                          <Loader2 className="w-3 h-3 animate-spin" style={{ color: DARK.accent }} />
                        ) : (
                          <div className="w-1.5 h-1.5 rounded-full" style={{ background: DARK.borderLight }} />
                        )}
                      </div>
                      <span
                        className="text-sm font-sans transition-colors duration-300"
                        style={{ color: isDone ? DARK.emerald : isActive ? DARK.text : DARK.textFaint }}
                      >
                        {step.label}
                      </span>
                    </div>
                  );
                })}
              </div>

              {filename && (
                <div
                  className="mt-8 flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-sans"
                  style={{ background: DARK.skySubtle, color: '#38bdf8', border: `1px solid ${DARK.skyBorder}` }}
                >
                  <FileText className="w-3.5 h-3.5" />
                  {filename}
                </div>
              )}
            </div>
          )}

          {/* ── Estado 3: Resultado ── */}
          {status === 'done' && summary && (
            <div>
              {/* File header */}
              <div className="flex items-center gap-3 mb-8">
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: DARK.accentSubtle, border: `1px solid ${DARK.accentBorder}` }}
                >
                  <FileText className="w-4 h-4" style={{ color: DARK.accent }} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-sans mb-0.5" style={{ color: DARK.textFaint }}>Documento analisado</p>
                  <p className="text-sm font-sans text-white truncate">{filename}</p>
                </div>
                {summary.cached && (
                  <div
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-sans"
                    style={{ background: DARK.emeraldSubtle, color: DARK.emerald, border: `1px solid ${DARK.emeraldBorder}` }}
                  >
                    <Check className="w-3 h-3" />
                    Cached
                  </div>
                )}
              </div>

              {/* Topics card */}
              <div
                className="rounded-2xl p-6 mb-4"
                style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}
              >
                <p
                  className="text-xs font-sans font-semibold uppercase tracking-widest mb-4"
                  style={{ color: DARK.accent }}
                >
                  Tópicos Abordados
                </p>
                <div className="flex flex-wrap gap-2">
                  {summary.topicos_abordados.map((topic, i) => (
                    <span
                      key={i}
                      className="text-sm font-sans px-3 py-1.5 rounded-lg"
                      style={{
                        background: DARK.accentSubtle,
                        color: DARK.text,
                        border: `1px solid ${DARK.accentBorder}`,
                      }}
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>

              {/* Summary card */}
              <div
                className="rounded-2xl p-6 mb-6"
                style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}
              >
                <p
                  className="text-xs font-sans font-semibold uppercase tracking-widest mb-4"
                  style={{ color: DARK.accent }}
                >
                  Resumo do Documento
                </p>
                <p
                  className="text-sm font-sans leading-relaxed whitespace-pre-wrap"
                  style={{ color: DARK.text }}
                >
                  {summary.resumo}
                </p>
              </div>

              {/* CTAs */}
              <div className="flex flex-col gap-3">
                <button
                  onClick={() => navigate(`/app?namespace=${namespace}`)}
                  className="w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-sm font-sans font-semibold transition-all duration-200 hover:opacity-90 active:scale-95"
                  style={{
                    background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
                    color: DARK.bg,
                    boxShadow: `0 0 40px ${DARK.accentGlow}`,
                  }}
                >
                  <MessageSquare className="w-4 h-4" />
                  Fazer perguntas sobre este documento
                  <ArrowRight className="w-4 h-4" />
                </button>
                <button
                  onClick={reset}
                  className="w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-sm font-sans font-semibold transition-all duration-200 hover:bg-white/5 active:scale-95"
                  style={{ color: DARK.textMuted, border: `1px solid ${DARK.border}` }}
                >
                  <RotateCcw className="w-4 h-4" />
                  Resumir outro PDF
                </button>
              </div>
            </div>
          )}

          {/* ── Estado 1: Upload ── */}
          {!isLoading && status !== 'done' && (
            <div>
              {/* Hero */}
              <div className="text-center mb-10">
                <div
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-sans font-medium mb-6"
                  style={{ background: DARK.accentSubtle, color: '#fbbf24', border: `1px solid ${DARK.accentBorder}` }}
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Análise gratuita com IA
                </div>
                <h1
                  className="font-display leading-tight text-white mb-4"
                  style={{ fontSize: 'clamp(2rem, 5vw, 3rem)' }}
                >
                  Resumo estruturado<br />
                  <span style={{ color: DARK.accent }}>do seu PDF.</span>
                </h1>
                <p className="text-sm font-sans leading-relaxed max-w-md mx-auto" style={{ color: DARK.textMuted }}>
                  Faça upload de um PDF e receba tópicos abordados e um resumo organizado — gerado exclusivamente a partir do conteúdo do documento, sem invenções.
                </p>
              </div>

              {/* Error */}
              {((status === 'error' && error) || fileError) && (
                <div
                  className="flex items-start gap-3 px-4 py-3 rounded-xl mb-4 text-sm font-sans"
                  style={{ background: 'rgba(239,68,68,0.08)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)' }}
                >
                  <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  {fileError ?? error}
                </div>
              )}

              {/* Drop zone */}
              <div
                onDrop={handleDrop}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onClick={user ? () => fileInputRef.current?.click() : undefined}
                className="rounded-2xl p-10 text-center mb-4 transition-all duration-200"
                style={{
                  border: `1.5px dashed ${dragging ? DARK.accent : DARK.border}`,
                  background: dragging ? DARK.accentSubtle : DARK.card,
                  cursor: user ? 'pointer' : 'default',
                }}
              >
                <div
                  className="w-12 h-12 rounded-2xl flex items-center justify-center mx-auto mb-4"
                  style={{
                    background: dragging ? DARK.accentSubtle : 'rgba(255,255,255,0.04)',
                    border: `1px solid ${dragging ? DARK.accentBorder : DARK.border}`,
                  }}
                >
                  <FileText className="w-6 h-6 transition-colors duration-200" style={{ color: dragging ? DARK.accent : DARK.textFaint }} />
                </div>
                <p className="text-sm font-sans font-medium text-white mb-1">
                  {user ? 'Arraste seu PDF aqui' : 'Faça login para começar'}
                </p>
                <p className="text-xs font-sans" style={{ color: DARK.textFaint }}>
                  {user ? 'ou clique para selecionar — somente PDF' : 'A análise é gratuita para todos os planos'}
                </p>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={(e) => handleFiles(e.target.files)}
                aria-label="Selecionar arquivo PDF"
              />

              {/* CTA */}
              <button
                onClick={handleGenerateClick}
                className="w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-sm font-sans font-semibold transition-all duration-200 hover:opacity-90 active:scale-95 mb-4"
                style={{
                  background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
                  color: DARK.bg,
                  boxShadow: `0 0 40px ${DARK.accentGlow}`,
                }}
              >
                {user ? 'Selecionar PDF e gerar resumo' : 'Entrar para gerar resumo'}
                <ArrowRight className="w-4 h-4" />
              </button>

              {/* Usage counter */}
              {user && usage && (
                <div className="mb-8">
                  <div className="flex items-center justify-between text-xs font-sans mb-2" style={{ color: DARK.textFaint }}>
                    <span>{usage.used_this_month} de {usage.limit} resumos usados este mês</span>
                    <span>{Math.round(usedRatio * 100)}%</span>
                  </div>
                  <div className="h-1 rounded-full overflow-hidden" style={{ background: DARK.border }}>
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(usedRatio * 100, 100)}%`,
                        background: usedRatio >= 0.9
                          ? `linear-gradient(90deg, #f59e0b, #ef4444)`
                          : `linear-gradient(90deg, ${DARK.accent}, #d97706)`,
                      }}
                    />
                  </div>
                </div>
              )}

              {/* Previous summaries */}
              {user && usage && usage.summaries.length > 0 && (
                <div>
                  <p
                    className="text-xs font-sans font-semibold uppercase tracking-widest mb-3"
                    style={{ color: DARK.textFaint }}
                  >
                    Resumos anteriores
                  </p>
                  <div className="flex flex-col gap-2">
                    {usage.summaries.map((item) => (
                      <button
                        key={item.namespace}
                        onClick={() => navigate(`/app?namespace=${item.namespace}`)}
                        className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-150 hover:bg-white/5 active:scale-95"
                        style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}
                      >
                        <div
                          className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                          style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${DARK.border}` }}
                        >
                          <FileText className="w-3.5 h-3.5" style={{ color: DARK.textFaint }} />
                        </div>
                        <span className="text-sm font-sans text-white flex-1 truncate">
                          {item.filename ?? 'Documento'}
                        </span>
                        <ArrowRight className="w-3.5 h-3.5 flex-shrink-0" style={{ color: DARK.textFaint }} />
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

        </div>
      </main>
    </div>
  );
}
