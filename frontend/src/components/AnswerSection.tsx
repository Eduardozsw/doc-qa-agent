import { useEffect, useRef } from 'react';
import { Bot, MessageSquare, FileText, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { Message } from '../App';

interface AnswerSectionProps {
  history: Message[];
  loading: boolean;
}

export function AnswerSection({ history, loading }: AnswerSectionProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history, loading]);

  if (!loading && history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center gap-4">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
          <MessageSquare className="w-7 h-7 text-slate-300" />
        </div>
        <div>
          <p className="text-sm font-medium text-slate-400">Nenhuma resposta ainda</p>
          <p className="text-xs text-slate-300 mt-1">Envie um PDF e faça uma pergunta para começar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4 max-h-[520px] overflow-y-auto pr-1">
      {history.map((msg, i) => (
        <div key={i} className="space-y-3">
          {/* Pergunta */}
          <div className="flex justify-end gap-2">
            <div className="max-w-[80%] bg-sky-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm shadow-sm">
              {msg.question}
            </div>
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-sky-100 flex items-center justify-center mt-0.5">
              <User className="w-4 h-4 text-sky-600" />
            </div>
          </div>

          {/* Resposta */}
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center mt-0.5">
              <Bot className="w-4 h-4 text-slate-500" />
            </div>
            <div className="flex-1 space-y-2">
              <div className="bg-white border border-slate-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                <ReactMarkdown
                  className="text-sm text-slate-700 leading-relaxed space-y-2"
                  components={{
                    h1: ({ children }) => <h1 className="text-base font-bold text-slate-800 mt-3 mb-1">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-sm font-bold text-slate-800 mt-3 mb-1">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-sm font-semibold text-slate-700 mt-2 mb-1">{children}</h3>,
                    p: ({ children }) => <p className="leading-relaxed">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc list-inside space-y-1 pl-2">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 pl-2">{children}</ol>,
                    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                    strong: ({ children }) => <strong className="font-semibold text-slate-800">{children}</strong>,
                    em: ({ children }) => <em className="italic">{children}</em>,
                    hr: () => <hr className="border-slate-200 my-2" />,
                  }}
                >
                  {msg.answer}
                </ReactMarkdown>
              </div>
              {msg.sources.length > 0 && (
                <div className="flex items-center gap-2 px-1">
                  <FileText className="w-3 h-3 text-slate-400 flex-shrink-0" />
                  <span className="text-xs text-slate-400">Fonte:</span>
                  <span className="text-xs text-slate-600 truncate max-w-[200px]">{msg.sources[0]}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}

      {/* Loading do próximo turno */}
      {loading && (
        <div className="flex gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center mt-0.5">
            <Bot className="w-4 h-4 text-slate-500" />
          </div>
          <div className="bg-white border border-slate-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
