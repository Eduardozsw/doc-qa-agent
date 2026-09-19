import { isValidElement, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { Bot, MessageSquare, FileText, User, Copy, Check, AlertTriangle, Clock, ThumbsUp, ThumbsDown, Database, GitCompare } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { Message } from '../App';
import type { Citacao } from '../lib/api';
import { DARK } from '../constants/theme';
import { Citations } from './Citations';
import type { PdfViewerRequest } from './PdfViewer';

type AuthFetch = (url: string, options?: RequestInit) => Promise<Response>;

function displayName(namespace: string): string {
  const parts = namespace.split('_');
  return parts.length > 2 ? parts.slice(2).join('_') : namespace;
}

interface AnswerSectionProps {
  history: Message[];
  loading: boolean;
  authFetch: AuthFetch;
  onFeedback: (index: number, score: 1 | -1) => void;
  onOpenPdf: (req: PdfViewerRequest) => void;
}

/**
 * Troca marcadores `[n]` por links markdown `[n](#cit-<msgIndex>-<n>)`, mas só quando `n`
 * existe em `citacoes`. Durante o streaming (antes do `done`), `citacoes` está vazio e o
 * texto é deixado cru.
 */
function linkifyCitations(text: string, msgIndex: number, citacoes: Citacao[]): string {
  if (citacoes.length === 0) return text;
  const validIds = new Set(citacoes.map(c => c.id));
  return text.replace(/\[(\d+)\]/g, (match, numStr: string) => {
    const n = Number(numStr);
    if (!validIds.has(n)) return match;
    return `[${n}](#cit-${msgIndex}-${n})`;
  });
}

function extractPlainText(node: ReactNode): string {
  if (typeof node === 'string') return node;
  if (typeof node === 'number') return String(node);
  if (Array.isArray(node)) return node.map(extractPlainText).join('');
  if (isValidElement(node)) {
    const props = node.props as { children?: ReactNode };
    return extractPlainText(props.children);
  }
  return '';
}

function handleCitationClick(href: string) {
  const el = document.getElementById(href.slice(1));
  if (!el) return;
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  const prevBackground = el.style.background;
  const prevTransition = el.style.transition;
  el.style.transition = 'background 0.3s ease';
  el.style.background = 'rgba(245,158,11,0.18)';
  window.setTimeout(() => {
    el.style.background = prevBackground;
    el.style.transition = prevTransition;
  }, 1200);
}

const baseMarkdownComponents = {
  h1: ({ children }: { children?: React.ReactNode }) => <h1 className="text-base font-bold mt-3 mb-1" style={{ color: 'rgba(255,255,255,0.9)' }}>{children}</h1>,
  h2: ({ children }: { children?: React.ReactNode }) => <h2 className="text-sm font-bold mt-3 mb-1" style={{ color: 'rgba(255,255,255,0.9)' }}>{children}</h2>,
  h3: ({ children }: { children?: React.ReactNode }) => <h3 className="text-sm font-semibold mt-2 mb-1" style={{ color: 'rgba(255,255,255,0.8)' }}>{children}</h3>,
  p: ({ children }: { children?: React.ReactNode }) => <p className="leading-relaxed">{children}</p>,
  ul: ({ children }: { children?: React.ReactNode }) => <ul className="list-disc list-inside space-y-1 pl-2">{children}</ul>,
  ol: ({ children }: { children?: React.ReactNode }) => <ol className="list-decimal list-inside space-y-1 pl-2">{children}</ol>,
  li: ({ children }: { children?: React.ReactNode }) => <li className="leading-relaxed">{children}</li>,
  strong: ({ children }: { children?: React.ReactNode }) => <strong className="font-semibold" style={{ color: 'rgba(255,255,255,0.95)' }}>{children}</strong>,
  em: ({ children }: { children?: React.ReactNode }) => <em className="italic">{children}</em>,
  hr: () => <hr className="my-2" style={{ borderColor: DARK.border }} />,
};

/** Componentes de markdown específicos por mensagem: chips de citação e blockquote de correção. */
function buildMarkdownComponents() {
  return {
    ...baseMarkdownComponents,
    a: ({ href, children }: { href?: string; children?: React.ReactNode }) => {
      if (href?.startsWith('#cit-')) {
        return (
          <sup>
            <a
              href={href}
              onClick={e => {
                e.preventDefault();
                handleCitationClick(href);
              }}
              style={{
                color: DARK.accent,
                textDecoration: 'none',
                fontWeight: 600,
                padding: '0 1px',
                cursor: 'pointer',
              }}
            >
              {children}
            </a>
          </sup>
        );
      }
      return (
        <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: DARK.sky }}>
          {children}
        </a>
      );
    },
    blockquote: ({ children }: { children?: React.ReactNode }) => {
      const isCorrecao = extractPlainText(children).trim().startsWith('Correção:');
      if (isCorrecao) {
        return (
          <blockquote
            className="my-2 rounded-md px-3 py-2 flex items-start gap-2"
            style={{
              borderLeft: `3px solid ${DARK.accent}`,
              background: 'rgba(245,158,11,0.08)',
              color: DARK.text,
            }}
          >
            <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 mt-1" style={{ color: DARK.accent }} />
            <div>{children}</div>
          </blockquote>
        );
      }
      return (
        <blockquote
          className="my-2 pl-3"
          style={{ borderLeft: `3px solid ${DARK.border}`, color: DARK.textMuted }}
        >
          {children}
        </blockquote>
      );
    },
  };
}

/** Card de divergência entre documentos: uma descrição por conflito, com chips `[n]` que
 * rolam até a citação correspondente no bloco "Embasamento" (mesmo mecanismo dos links `[n]` do texto). */
function ConflictCard({ conflitos, msgIndex }: { conflitos: Message['conflitos']; msgIndex: number }) {
  return (
    <div
      className="rounded-xl px-3 py-2.5 text-xs font-sans space-y-2"
      style={{ background: 'rgba(245,158,11,0.06)', border: `1px solid ${DARK.accentBorder}` }}
    >
      <p className="font-medium flex items-center gap-1.5" style={{ color: DARK.accent }}>
        <GitCompare className="w-3.5 h-3.5 flex-shrink-0" />
        Divergência entre documentos
      </p>
      <ul className="space-y-1.5">
        {conflitos.map((conflito, idx) => (
          <li key={idx} className="leading-relaxed" style={{ color: DARK.text }}>
            <span>{conflito.descricao}</span>{' '}
            {conflito.ids.map(id => (
              <a
                key={id}
                href={`#cit-${msgIndex}-${id}`}
                onClick={e => {
                  e.preventDefault();
                  handleCitationClick(`#cit-${msgIndex}-${id}`);
                }}
                style={{ color: DARK.accent, fontWeight: 600, textDecoration: 'none', marginRight: 4 }}
              >
                [{id}]
              </a>
            ))}
          </li>
        ))}
      </ul>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(`${text}\n\n— Gerado pelo MindDoc · minddoc.com.br`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={handleCopy}
      title="Copiar resposta"
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 4,
        padding: '3px 8px', borderRadius: 6, fontSize: 11, fontWeight: 500,
        background: 'transparent', border: `1px solid ${DARK.border}`,
        color: copied ? DARK.emerald : 'rgba(255,255,255,0.3)',
        cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'inherit',
      }}
      onMouseEnter={e => { if (!copied) e.currentTarget.style.color = 'rgba(255,255,255,0.6)'; }}
      onMouseLeave={e => { if (!copied) e.currentTarget.style.color = 'rgba(255,255,255,0.3)'; }}
    >
      {copied
        ? <><Check style={{ width: 11, height: 11 }} />Copiado</>
        : <><Copy style={{ width: 11, height: 11 }} />Copiar</>}
    </button>
  );
}

function FeedbackButtons({
  msg, msgIndex, authFetch, onFeedback,
}: {
  msg: Message;
  msgIndex: number;
  authFetch: AuthFetch;
  onFeedback: (index: number, score: 1 | -1) => void;
}) {
  const [sending, setSending] = useState<1 | -1 | null>(null);
  const chosen = msg.feedback;

  const handleClick = async (score: 1 | -1) => {
    if (chosen || sending) return;
    setSending(score);
    try {
      const res = await authFetch('/api/query/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          trace_id: msg.traceId,
          score,
          pergunta: msg.question,
          resposta: msg.answer,
        }),
      });
      if (!res.ok) throw new Error(`Erro ${res.status}`);
      onFeedback(msgIndex, score);
    } catch (err) {
      console.warn('Falha ao enviar feedback:', err);
    } finally {
      setSending(null);
    }
  };

  const buttonStyle = (active: boolean, activeColor: string) => ({
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    padding: '4px 7px', borderRadius: 6,
    background: 'transparent', border: `1px solid ${DARK.border}`,
    color: active ? activeColor : 'rgba(255,255,255,0.3)',
    cursor: chosen ? 'default' : 'pointer',
    opacity: chosen && !active ? 0.4 : 1,
    transition: 'all 0.15s', fontFamily: 'inherit',
  });

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => handleClick(1)}
        disabled={!!chosen}
        title="Resposta útil"
        style={buttonStyle(chosen === 1, DARK.emerald)}
      >
        <ThumbsUp style={{ width: 11, height: 11 }} />
      </button>
      <button
        onClick={() => handleClick(-1)}
        disabled={!!chosen}
        title="Resposta não útil"
        style={buttonStyle(chosen === -1, '#f87171')}
      >
        <ThumbsDown style={{ width: 11, height: 11 }} />
      </button>
    </div>
  );
}

export function AnswerSection({ history, loading, authFetch, onFeedback, onOpenPdf }: AnswerSectionProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history, loading]);

  if (!loading && history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center gap-4">
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center"
          style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${DARK.border}` }}
        >
          <MessageSquare className="w-7 h-7" style={{ color: 'rgba(255,255,255,0.15)' }} />
        </div>
        <div>
          <p className="text-sm font-sans font-medium" style={{ color: 'rgba(255,255,255,0.3)' }}>Nenhuma resposta ainda</p>
          <p className="text-xs font-sans mt-1" style={{ color: 'rgba(255,255,255,0.2)' }}>Envie um PDF e faça uma pergunta para começar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 pr-1">
      {history.map((msg, i) => {
        const isLast = i === history.length - 1;
        const showStatus = loading && isLast && !!msg.status;
        const displayedAnswer = linkifyCitations(msg.answer, i, msg.citacoes);

        return (
          <div key={i} className="space-y-3">
            {/* User message */}
            <div className="flex justify-end gap-2">
              <div
                className="max-w-[80%] rounded-2xl rounded-tr-sm px-4 py-3 text-sm font-sans leading-relaxed"
                style={{ background: DARK.accentSubtle, color: '#fcd34d', border: `1px solid ${DARK.accentBorder}` }}
              >
                {msg.question}
              </div>
              <div
                className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-0.5"
                style={{ background: DARK.accentSubtle, border: `1px solid ${DARK.accentBorder}` }}
              >
                <User className="w-4 h-4" style={{ color: DARK.accent }} />
              </div>
            </div>

            {/* AI message */}
            {msg.answer && (
              <div className="flex gap-3">
                <div
                  className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-0.5"
                  style={{ background: 'rgba(255,255,255,0.05)', border: `1px solid ${DARK.border}` }}
                >
                  <Bot className="w-4 h-4" style={{ color: DARK.textMuted }} />
                </div>
                <div className="flex-1 space-y-2">
                  <div
                    className="rounded-2xl rounded-tl-sm px-4 py-3"
                    style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${DARK.border}`, color: DARK.text }}
                  >
                    <ReactMarkdown
                      className="text-sm font-sans leading-relaxed space-y-2"
                      components={buildMarkdownComponents()}
                    >
                      {displayedAnswer}
                    </ReactMarkdown>
                  </div>

                  {showStatus && (
                    <div
                      className="flex items-center gap-1.5 px-1 text-xs font-sans"
                      style={{ color: DARK.textFaint }}
                    >
                      <Clock className="w-3 h-3 flex-shrink-0" />
                      <span>{msg.status}</span>
                    </div>
                  )}

                  <div className="flex items-center gap-2 flex-wrap">
                    {msg.sources.length > 0 && (
                      <div
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg w-fit text-xs font-sans"
                        style={{ background: DARK.emeraldSubtle, color: DARK.emerald, border: `1px solid ${DARK.emeraldBorder}` }}
                      >
                        <FileText className="w-3 h-3 flex-shrink-0" />
                        <span className="truncate max-w-[200px]">{displayName(msg.sources[0])}</span>
                      </div>
                    )}
                    {msg.unverified && (
                      <div
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg w-fit text-xs font-sans"
                        style={{ background: 'rgba(245,158,11,0.08)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.2)' }}
                      >
                        <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                        <span>Não verificado nos documentos</span>
                      </div>
                    )}
                    {msg.cached && (
                      <div
                        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg w-fit text-xs font-sans"
                        style={{ background: 'rgba(255,255,255,0.04)', color: DARK.textFaint, border: `1px solid ${DARK.border}` }}
                      >
                        <Database className="w-3 h-3 flex-shrink-0" />
                        <span>Resposta em cache</span>
                      </div>
                    )}
                    {msg.modelo && msg.modelo !== 'gpt-4o-mini' && (
                      <span
                        title="Pergunta encaminhada ao modelo mais forte"
                        className="px-2 py-0.5 rounded-full text-[10px] font-sans font-medium w-fit"
                        style={{ background: 'rgba(255,255,255,0.04)', color: DARK.textFaint, border: `1px solid ${DARK.border}` }}
                      >
                        {msg.modelo}
                      </span>
                    )}
                    <CopyButton text={msg.answer} />
                    {!(loading && isLast) && (
                      <FeedbackButtons msg={msg} msgIndex={i} authFetch={authFetch} onFeedback={onFeedback} />
                    )}
                  </div>

                  {msg.conflitos.length > 0 && (
                    <ConflictCard conflitos={msg.conflitos} msgIndex={i} />
                  )}

                  <Citations citacoes={msg.citacoes} msgIndex={i} onOpenPdf={onOpenPdf} />
                </div>
              </div>
            )}
          </div>
        );
      })}

      {loading && history[history.length - 1]?.answer === '' && (
        <div className="flex gap-3">
          <div
            className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-0.5"
            style={{ background: 'rgba(255,255,255,0.05)', border: `1px solid ${DARK.border}` }}
          >
            <Bot className="w-4 h-4" style={{ color: DARK.textMuted }} />
          </div>
          <div
            className="rounded-2xl rounded-tl-sm px-4 py-3"
            style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${DARK.border}` }}
          >
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full animate-bounce [animation-delay:0ms]" style={{ background: DARK.accent }} />
              <span className="w-2 h-2 rounded-full animate-bounce [animation-delay:150ms]" style={{ background: DARK.accent }} />
              <span className="w-2 h-2 rounded-full animate-bounce [animation-delay:300ms]" style={{ background: DARK.accent }} />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
