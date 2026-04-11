import { Bot, MessageSquare } from 'lucide-react';

interface AnswerSectionProps {
  answer: string | null;
  loading: boolean;
  question: string | null;
}

export function AnswerSection({ answer, loading, question }: AnswerSectionProps) {
  if (!loading && !answer) {
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
    <div className="space-y-4">
      {question && (
        <div className="flex justify-end">
          <div className="max-w-[80%] bg-sky-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm shadow-sm">
            {question}
          </div>
        </div>
      )}

      <div className="flex gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center mt-0.5">
          <Bot className="w-4 h-4 text-slate-500" />
        </div>
        <div className="flex-1 bg-white border border-slate-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
          {loading ? (
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:0ms]" />
              <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:150ms]" />
              <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
          ) : (
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{answer}</p>
          )}
        </div>
      </div>
    </div>
  );
}
