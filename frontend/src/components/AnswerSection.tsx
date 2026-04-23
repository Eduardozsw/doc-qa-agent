import { useEffect, useRef } from 'react';
import { Bot, MessageSquare, FileText, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { Message } from '../App';
import { DARK } from '../constants/theme';

interface AnswerSectionProps {
  history: Message[];
  loading: boolean;
}

const markdownComponents = {
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

export function AnswerSection({ history, loading }: AnswerSectionProps) {
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
      {history.map((msg, i) => (
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
                    components={markdownComponents}
                  >
                    {msg.answer}
                  </ReactMarkdown>
                </div>
                {msg.sources.length > 0 && (
                  <div
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg w-fit text-xs font-sans"
                    style={{ background: DARK.emeraldSubtle, color: DARK.emerald, border: `1px solid ${DARK.emeraldBorder}` }}
                  >
                    <FileText className="w-3 h-3 flex-shrink-0" />
                    <span className="truncate max-w-[200px]">{msg.sources[0]}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ))}

      {loading && (
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
