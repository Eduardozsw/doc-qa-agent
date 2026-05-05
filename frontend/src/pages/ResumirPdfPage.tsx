import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useSummarize } from '../hooks/useSummarize';

const C = {
  bg: '#08070b',
  surface: '#100e14',
  surfaceHigh: '#18151e',
  border: 'rgba(201,169,110,0.10)',
  borderBright: 'rgba(201,169,110,0.22)',
  gold: '#c9a96e',
  goldDim: 'rgba(201,169,110,0.12)',
  goldGlow: 'rgba(201,169,110,0.06)',
  text: '#ede8e0',
  muted: '#7a7280',
  dim: '#3d3843',
  red: '#e87070',
  redDim: 'rgba(232,112,112,0.10)',
};

const fonts = `
  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=IBM+Plex+Mono:wght@400;500&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes scanline {
    0%   { top: 0%; opacity: 1; }
    90%  { opacity: 1; }
    100% { top: 100%; opacity: 0; }
  }
  @keyframes pulse-gold {
    0%, 100% { box-shadow: 0 0 0 0 rgba(201,169,110,0.0); }
    50%       { box-shadow: 0 0 24px 4px rgba(201,169,110,0.12); }
  }
  @keyframes shimmer {
    0%   { transform: translateX(-100%); }
    100% { transform: translateX(200%); }
  }
  @keyframes spin-slow {
    to { transform: rotate(360deg); }
  }
  @keyframes reveal {
    from { opacity: 0; clip-path: inset(0 100% 0 0); }
    to   { opacity: 1; clip-path: inset(0 0% 0 0); }
  }

  .fade-up { animation: fadeUp 0.55s cubic-bezier(0.22,1,0.36,1) both; }
  .fade-up-1 { animation-delay: 0.05s; }
  .fade-up-2 { animation-delay: 0.12s; }
  .fade-up-3 { animation-delay: 0.20s; }
  .fade-up-4 { animation-delay: 0.28s; }
  .fade-up-5 { animation-delay: 0.36s; }

  .drop-zone:hover { border-color: rgba(201,169,110,0.35) !important; }
  .drop-zone.active { border-color: ${C.gold} !important; animation: pulse-gold 2s infinite; }

  .cta-btn:hover { background: #d4b47a !important; transform: translateY(-1px); box-shadow: 0 8px 32px rgba(201,169,110,0.25); }
  .cta-btn:active { transform: translateY(0); }
  .secondary-btn:hover { border-color: rgba(201,169,110,0.3) !important; color: ${C.text} !important; }

  .summary-card { transition: border-color 0.2s; }
  .summary-card:hover { border-color: rgba(201,169,110,0.25) !important; }

  .prev-item:hover { background: ${C.surfaceHigh} !important; }
  .prev-item:hover .arrow { color: ${C.gold} !important; }
`;

function ScanAnimation() {
  return (
    <div style={{ position: 'relative', width: 72, height: 88, margin: '0 auto 32px', flexShrink: 0 }}>
      {/* Document layers */}
      {[2, 1, 0].map(i => (
        <div key={i} style={{
          position: 'absolute',
          width: 54 + i * 6,
          height: 68 + i * 6,
          top: i * 5,
          left: (2 - i) * 3,
          background: i === 0 ? C.surfaceHigh : C.surface,
          border: `1px solid ${i === 0 ? C.borderBright : C.border}`,
          borderRadius: 4,
        }} />
      ))}
      {/* Scanline */}
      <div style={{
        position: 'absolute', left: 3, right: 3, height: 2,
        background: `linear-gradient(90deg, transparent, ${C.gold}, transparent)`,
        animation: 'scanline 1.8s cubic-bezier(0.4,0,0.2,1) infinite',
        opacity: 0.8,
      }} />
    </div>
  );
}

function LoadingState({ status }: { status: string }) {
  const steps = [
    { key: 'ingesting', label: 'Indexando documento' },
    { key: 'summarizing', label: 'Gerando análise' },
  ];
  return (
    <div style={{ textAlign: 'center', padding: '60px 0' }} className="fade-up">
      <ScanAnimation />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'center' }}>
        {steps.map((step, i) => {
          const active = step.key === status;
          const done = steps.indexOf(steps.find(s => s.key === status)!) > i;
          return (
            <div key={step.key} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              opacity: active ? 1 : done ? 0.5 : 0.25,
              transition: 'opacity 0.4s',
            }}>
              <div style={{
                width: 6, height: 6, borderRadius: '50%',
                background: active ? C.gold : done ? C.muted : C.dim,
                transition: 'background 0.4s',
                ...(active ? { boxShadow: `0 0 8px ${C.gold}` } : {}),
              }} />
              <span style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 12,
                color: active ? C.gold : C.muted,
                letterSpacing: '0.04em',
              }}>
                {step.label}{active ? '...' : done ? ' ✓' : ''}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

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

  return (
    <div style={{ minHeight: '100vh', background: C.bg, fontFamily: "'Cormorant Garamond', Georgia, serif", color: C.text }}>
      <style>{fonts}</style>

      {/* Grain overlay */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0,
        backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 256 256\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'n\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23n)\' opacity=\'0.035\'/%3E%3C/svg%3E")',
        opacity: 0.6,
      }} />

      {/* Ambient light */}
      <div style={{
        position: 'fixed', top: '-30%', right: '-10%', width: '600px', height: '600px',
        borderRadius: '50%', background: 'radial-gradient(circle, rgba(201,169,110,0.04) 0%, transparent 70%)',
        pointerEvents: 'none', zIndex: 0,
      }} />

      {/* Header */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(8,7,11,0.88)', backdropFilter: 'blur(16px)',
        borderBottom: `1px solid ${C.border}`,
        padding: '0 32px', height: 52,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <Link to="/" style={{
          fontFamily: "'Cormorant Garamond', serif",
          fontSize: 18, fontWeight: 600, color: C.gold,
          textDecoration: 'none', letterSpacing: '0.02em',
        }}>
          MindDoc
        </Link>
        <nav style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <Link to="/app" style={{
            fontFamily: "'IBM Plex Mono', monospace",
            padding: '4px 12px', borderRadius: 4, fontSize: 11,
            color: C.muted, textDecoration: 'none',
            border: `1px solid ${C.border}`,
            letterSpacing: '0.05em', textTransform: 'uppercase',
          }}>Chat</Link>
          <span style={{
            fontFamily: "'IBM Plex Mono', monospace",
            padding: '4px 12px', borderRadius: 4, fontSize: 11,
            color: C.gold, border: `1px solid ${C.borderBright}`,
            background: C.goldDim,
            letterSpacing: '0.05em', textTransform: 'uppercase',
          }}>Resumir PDF</span>
          {!user && (
            <Link to="/login" style={{
              fontFamily: "'IBM Plex Mono', monospace",
              padding: '4px 12px', borderRadius: 4, fontSize: 11,
              color: C.muted, textDecoration: 'none',
              border: `1px solid ${C.border}`,
              letterSpacing: '0.05em', textTransform: 'uppercase',
            }}>Entrar</Link>
          )}
        </nav>
      </header>

      <main style={{ maxWidth: 680, margin: '0 auto', padding: '64px 24px 80px', position: 'relative', zIndex: 1 }}>

        {status === 'done' && summary ? (
          /* ── Estado 3: Resultado ── */
          <div>
            {/* Filename */}
            <div className="fade-up fade-up-1" style={{
              display: 'flex', alignItems: 'center', gap: 8, marginBottom: 40,
            }}>
              <span style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 11, color: C.muted, letterSpacing: '0.05em',
              }}>DOCUMENTO ANALISADO</span>
              <div style={{ flex: 1, height: 1, background: C.border }} />
              <span style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 11, color: C.gold,
              }}>{filename}</span>
            </div>

            {/* Topics */}
            <div className="fade-up fade-up-2 summary-card" style={{
              border: `1px solid ${C.border}`,
              borderRadius: 8, padding: '28px 32px', marginBottom: 16,
              background: C.surface,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
                <span style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 10, color: C.gold, letterSpacing: '0.12em', textTransform: 'uppercase',
                }}>Tópicos Abordados</span>
                <div style={{ flex: 1, height: 1, background: C.goldDim }} />
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {summary.topicos_abordados.map((t, i) => (
                  <span key={i} style={{
                    fontFamily: "'Cormorant Garamond', serif",
                    fontSize: 15, fontStyle: 'italic',
                    color: C.text, background: C.goldGlow,
                    border: `1px solid ${C.border}`,
                    borderRadius: 4, padding: '4px 12px',
                    lineHeight: 1.4,
                  }}>{t}</span>
                ))}
              </div>
            </div>

            {/* Summary */}
            <div className="fade-up fade-up-3 summary-card" style={{
              border: `1px solid ${C.border}`,
              borderRadius: 8, padding: '28px 32px', marginBottom: 32,
              background: C.surface,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
                <span style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 10, color: C.gold, letterSpacing: '0.12em', textTransform: 'uppercase',
                }}>Análise do Documento</span>
                <div style={{ flex: 1, height: 1, background: C.goldDim }} />
              </div>
              <p style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 18, lineHeight: 1.85, color: C.text,
                whiteSpace: 'pre-wrap', fontWeight: 400,
              }}>{summary.resumo}</p>
            </div>

            {/* CTAs */}
            <div className="fade-up fade-up-4" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <button
                className="cta-btn"
                onClick={() => navigate(`/app?namespace=${namespace}`)}
                style={{
                  width: '100%', background: C.gold, color: '#0a0800',
                  border: 'none', borderRadius: 6, padding: '14px 24px',
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 12, letterSpacing: '0.06em', textTransform: 'uppercase',
                  cursor: 'pointer', fontWeight: 500, transition: 'all 0.18s',
                }}
              >
                Fazer perguntas sobre este documento →
              </button>
              <button
                className="secondary-btn"
                onClick={reset}
                style={{
                  width: '100%', background: 'transparent', color: C.muted,
                  border: `1px solid ${C.border}`, borderRadius: 6, padding: '12px 24px',
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 11, letterSpacing: '0.06em', textTransform: 'uppercase',
                  cursor: 'pointer', transition: 'all 0.18s',
                }}
              >
                Analisar outro documento
              </button>
            </div>
          </div>

        ) : isLoading ? (
          /* ── Estado 2: Loading ── */
          <LoadingState status={status} />

        ) : (
          /* ── Estado 1: Upload ── */
          <div>
            {/* Hero */}
            <div className="fade-up fade-up-1" style={{ marginBottom: 56, textAlign: 'center' }}>
              <p style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 10, color: C.gold, letterSpacing: '0.16em',
                textTransform: 'uppercase', marginBottom: 16,
              }}>Inteligência Documental</p>
              <h1 style={{
                fontSize: 48, fontWeight: 500, lineHeight: 1.15,
                color: C.text, marginBottom: 16, fontStyle: 'italic',
              }}>
                Entenda qualquer<br />
                <span style={{ color: C.gold }}>documento</span> em segundos
              </h1>
              <p style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 13, color: C.muted, lineHeight: 1.7,
                maxWidth: 440, margin: '0 auto',
              }}>
                Faça upload de um PDF e receba uma análise estruturada baseada exclusivamente no conteúdo do documento — sem invenções.
              </p>
            </div>

            {/* Error */}
            {((status === 'error' && error) || fileError) && (
              <div className="fade-up" style={{
                background: C.redDim, border: `1px solid rgba(232,112,112,0.2)`,
                borderRadius: 6, padding: '12px 16px', marginBottom: 20,
                display: 'flex', alignItems: 'center', gap: 10,
              }}>
                <span style={{ color: C.red, fontSize: 14 }}>⚠</span>
                <span style={{
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 12, color: C.red,
                }}>{fileError ?? error}</span>
              </div>
            )}

            {/* Drop Zone */}
            <div className={`fade-up fade-up-2 drop-zone${dragging ? ' active' : ''}`}
              onDrop={handleDrop}
              onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onClick={user ? () => fileInputRef.current?.click() : undefined}
              style={{
                position: 'relative', overflow: 'hidden',
                border: `1.5px dashed ${dragging ? C.gold : C.borderBright}`,
                borderRadius: 10, padding: '56px 32px',
                textAlign: 'center', background: C.surface,
                marginBottom: 20, cursor: user ? 'pointer' : 'default',
                transition: 'border-color 0.2s, background 0.2s',
              }}
            >
              {/* Shimmer on drag */}
              {dragging && (
                <div style={{
                  position: 'absolute', inset: 0,
                  background: `linear-gradient(105deg, transparent 40%, ${C.goldGlow} 50%, transparent 60%)`,
                  animation: 'shimmer 1.2s infinite',
                }} />
              )}

              {/* Document stack icon */}
              <div style={{ position: 'relative', width: 56, height: 68, margin: '0 auto 24px' }}>
                {[2, 1].map(i => (
                  <div key={i} style={{
                    position: 'absolute',
                    width: 42 + i * 4, height: 52 + i * 4,
                    top: (2 - i) * 5, left: i * 3,
                    background: C.surfaceHigh,
                    border: `1px solid ${C.border}`,
                    borderRadius: 3,
                  }} />
                ))}
                <div style={{
                  position: 'absolute', width: 42, height: 52,
                  top: 10, left: 7,
                  background: C.surfaceHigh,
                  border: `1px solid ${C.borderBright}`,
                  borderRadius: 3,
                  display: 'flex', flexDirection: 'column',
                  padding: '8px 6px', gap: 4,
                }}>
                  {[80, 60, 70, 40].map((w, i) => (
                    <div key={i} style={{
                      height: 2, width: `${w}%`,
                      background: C.dim, borderRadius: 1,
                    }} />
                  ))}
                </div>
              </div>

              <p style={{
                fontFamily: "'Cormorant Garamond', serif",
                fontSize: 20, color: C.text, marginBottom: 6, fontStyle: 'italic',
              }}>
                {user ? 'Arraste seu PDF aqui' : 'Faça login para começar'}
              </p>
              <p style={{
                fontFamily: "'IBM Plex Mono', monospace",
                fontSize: 11, color: C.dim, letterSpacing: '0.04em',
              }}>
                {user ? 'ou clique para selecionar — somente PDF' : 'A análise é gratuita para usuários cadastrados'}
              </p>
            </div>

            <input
              ref={fileInputRef}
              type="file" accept="application/pdf"
              style={{ display: 'none' }}
              onChange={(e) => handleFiles(e.target.files)}
              aria-label="Selecionar arquivo PDF"
            />

            {/* CTA Button */}
            <div className="fade-up fade-up-3">
              <button
                className="cta-btn"
                onClick={handleGenerateClick}
                style={{
                  width: '100%', background: C.gold, color: '#0a0800',
                  border: 'none', borderRadius: 6, padding: '15px 24px',
                  fontFamily: "'IBM Plex Mono', monospace",
                  fontSize: 12, letterSpacing: '0.07em', textTransform: 'uppercase',
                  cursor: 'pointer', fontWeight: 500, transition: 'all 0.18s',
                  marginBottom: 12,
                }}
              >
                {user ? 'Gerar análise gratuita →' : 'Entrar para gerar análise →'}
              </button>

              {/* Usage counter */}
              {user && usage && (
                <div style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
                  marginBottom: usage.summaries.length > 0 ? 40 : 0,
                }}>
                  <div style={{ height: 1, flex: 1, background: C.border }} />
                  <span style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontSize: 10, color: C.dim, letterSpacing: '0.06em',
                  }}>
                    {usage.used_this_month}/{usage.limit} análises este mês
                  </span>
                  <div style={{ height: 1, flex: 1, background: C.border }} />
                </div>
              )}
            </div>

            {/* Previous summaries */}
            {user && usage && usage.summaries.length > 0 && (
              <div className="fade-up fade-up-4">
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
                  <span style={{
                    fontFamily: "'IBM Plex Mono', monospace",
                    fontSize: 10, color: C.dim, letterSpacing: '0.10em', textTransform: 'uppercase',
                  }}>Análises anteriores</span>
                  <div style={{ flex: 1, height: 1, background: C.border }} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {usage.summaries.map((item) => (
                    <div
                      key={item.namespace}
                      className="prev-item"
                      onClick={() => navigate(`/app?namespace=${item.namespace}`)}
                      style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: '12px 16px', borderRadius: 6,
                        border: `1px solid ${C.border}`,
                        background: C.surface, cursor: 'pointer',
                        transition: 'background 0.15s',
                      }}
                    >
                      <span style={{
                        fontFamily: "'Cormorant Garamond', serif",
                        fontSize: 15, fontStyle: 'italic', color: C.text,
                      }}>
                        {item.filename ?? 'Documento'}
                      </span>
                      <span className="arrow" style={{
                        fontFamily: "'IBM Plex Mono', monospace",
                        fontSize: 11, color: C.dim, transition: 'color 0.15s',
                      }}>→</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
