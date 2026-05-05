import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useSummarize } from '../hooks/useSummarize';

export function ResumirPdfPage() {
  const { user, session } = useAuth();
  const navigate = useNavigate();
  const { status, summary, error, filename, namespace, usage, generate, reset, loadUsage } =
    useSummarize(session);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropRef = useRef<HTMLDivElement>(null);
  const [fileError, setFileError] = useState<string | null>(null);

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
    if (!user) {
      navigate('/login?redirect=/resumir-pdf');
      return;
    }
    handleFiles(e.dataTransfer.files);
  };

  const handleGenerateClick = () => {
    if (!user) {
      navigate('/login?redirect=/resumir-pdf');
      return;
    }
    fileInputRef.current?.click();
  };

  const isLoading = status === 'ingesting' || status === 'summarizing';

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', fontFamily: 'sans-serif' }}>
      {/* Ambient blob */}
      <div style={{
        position: 'fixed', top: '-20%', left: '-10%', width: '500px', height: '500px',
        borderRadius: '50%', background: 'rgba(56,189,248,0.04)', filter: 'blur(80px)', pointerEvents: 'none',
      }} />

      {/* Header */}
      <header style={{
        position: 'sticky', top: 0, zIndex: 10,
        background: 'rgba(15,23,42,0.85)', backdropFilter: 'blur(12px)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        padding: '0 24px', height: '56px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <Link to="/" style={{ color: '#38bdf8', fontWeight: 700, fontSize: 16, textDecoration: 'none' }}>
          MindDoc
        </Link>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Link to="/app" style={{
            padding: '5px 12px', borderRadius: 6, fontSize: 13, color: '#64748b',
            textDecoration: 'none', background: '#1e293b',
          }}>Chat</Link>
          <span style={{
            padding: '5px 12px', borderRadius: 6, fontSize: 13, color: 'white',
            background: '#1d4ed8', fontWeight: 600,
          }}>Resumir PDF</span>
          {!user && (
            <Link to="/login" style={{
              padding: '5px 12px', borderRadius: 6, fontSize: 13, color: '#64748b',
              textDecoration: 'none', background: '#1e293b',
            }}>Entrar</Link>
          )}
        </div>
      </header>

      <main style={{ maxWidth: 600, margin: '0 auto', padding: '48px 24px' }}>
        {status === 'done' && summary ? (
          /* Estado 3 — Resultado */
          <div>
            <p style={{ color: '#475569', fontSize: 12, marginBottom: 20 }}>
              📄 {filename}
            </p>

            <div style={{
              background: '#1e293b', borderRadius: 12, padding: 20, marginBottom: 16,
            }}>
              <h3 style={{
                color: '#38bdf8', fontSize: 11, fontWeight: 700, letterSpacing: '0.08em',
                textTransform: 'uppercase', margin: '0 0 12px',
              }}>
                Tópicos Abordados
              </h3>
              <ul style={{ margin: 0, paddingLeft: 18, color: '#94a3b8', fontSize: 13, lineHeight: 1.7 }}>
                {summary.topicos_abordados.map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ul>
            </div>

            <div style={{
              background: '#1e293b', borderRadius: 12, padding: 20, marginBottom: 24,
            }}>
              <h3 style={{
                color: '#38bdf8', fontSize: 11, fontWeight: 700, letterSpacing: '0.08em',
                textTransform: 'uppercase', margin: '0 0 12px',
              }}>
                Resumo do PDF
              </h3>
              <p style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.8, margin: 0, whiteSpace: 'pre-wrap' }}>
                {summary.resumo}
              </p>
            </div>

            <button
              onClick={() => navigate(`/app?namespace=${namespace}`)}
              style={{
                width: '100%', background: '#1d4ed8', color: 'white', border: 'none',
                borderRadius: 8, padding: '12px 20px', fontSize: 14, cursor: 'pointer',
                fontWeight: 600, marginBottom: 12,
              }}
            >
              💬 Fazer perguntas sobre este documento →
            </button>

            <button
              onClick={reset}
              style={{
                width: '100%', background: '#1e293b', color: '#94a3b8', border: 'none',
                borderRadius: 8, padding: '10px 20px', fontSize: 13, cursor: 'pointer',
              }}
            >
              Resumir outro PDF
            </button>
          </div>
        ) : isLoading ? (
          /* Estado 2 — Loading */
          <div style={{ textAlign: 'center', padding: '60px 0' }}>
            <div
              className="animate-spin"
              style={{
                width: 40, height: 40, border: '3px solid #1e293b',
                borderTop: '3px solid #38bdf8', borderRadius: '50%',
                margin: '0 auto 20px',
              }}
            />
            <p style={{ color: '#64748b', fontSize: 14 }}>
              {status === 'ingesting' ? 'Indexando documento...' : 'Gerando resumo...'}
            </p>
          </div>
        ) : (
          /* Estado 1 — Upload */
          <div>
            <div style={{ textAlign: 'center', marginBottom: 32 }}>
              <h1 style={{ color: 'white', fontSize: 28, fontWeight: 700, margin: '0 0 8px' }}>
                Resumo de PDF com IA
              </h1>
              <p style={{ color: '#64748b', fontSize: 14, margin: 0 }}>
                Faça upload do seu PDF e receba um resumo estruturado baseado no conteúdo do documento.
              </p>
            </div>

            {((status === 'error' && error) || fileError) && (
              <div style={{
                background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: 8, padding: '10px 14px', marginBottom: 16, color: '#fca5a5', fontSize: 13,
              }}>
                {fileError ?? error}
              </div>
            )}

            <div
              ref={dropRef}
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              onClick={user ? () => fileInputRef.current?.click() : undefined}
              style={{
                border: '2px dashed #334155', borderRadius: 10, padding: '40px 20px',
                textAlign: 'center', background: '#1e293b', marginBottom: 16,
                cursor: user ? 'pointer' : 'default',
              }}
            >
              <div style={{ fontSize: 36, marginBottom: 12 }}>📄</div>
              <p style={{ color: '#94a3b8', fontSize: 13, margin: '0 0 4px' }}>
                {user
                  ? 'Arraste seu PDF aqui ou clique para selecionar'
                  : 'Faça login para selecionar um PDF'}
              </p>
              <p style={{ color: '#475569', fontSize: 11, margin: 0 }}>Somente PDF</p>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              style={{ display: 'none' }}
              onChange={(e) => handleFiles(e.target.files)}
            />

            <button
              onClick={handleGenerateClick}
              style={{
                width: '100%', background: '#1d4ed8', color: 'white', border: 'none',
                borderRadius: 8, padding: '12px 20px', fontSize: 14, cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              {user ? 'Gerar Resumo Grátis →' : 'Fazer login para continuar →'}
            </button>

            {user && usage && (
              <p style={{ textAlign: 'center', color: '#475569', fontSize: 11, marginTop: 10 }}>
                {usage.used_this_month} de {usage.limit} resumos usados este mês
              </p>
            )}

            {/* Resumos anteriores */}
            {user && usage && usage.summaries.length > 0 && (
              <div style={{ marginTop: 32 }}>
                <h3 style={{
                  color: '#475569', fontSize: 11, fontWeight: 600, letterSpacing: '0.08em',
                  textTransform: 'uppercase', marginBottom: 12,
                }}>
                  Resumos anteriores
                </h3>
                {usage.summaries.map((item) => (
                  <div
                    key={item.namespace}
                    onClick={() => navigate(`/app?namespace=${item.namespace}`)}
                    style={{
                      background: '#1e293b', borderRadius: 8, padding: '10px 14px',
                      marginBottom: 8, cursor: 'pointer',
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    }}
                  >
                    <span style={{ color: '#94a3b8', fontSize: 13 }}>📄 {item.filename ?? 'Documento'}</span>
                    <span style={{ color: '#475569', fontSize: 11 }}>Ver →</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
