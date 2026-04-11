import { KeyboardEvent } from 'react';
import { Send } from 'lucide-react';

interface QuestionInputProps {
  question: string;
  onQuestionChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  loading: boolean;
}

export function QuestionInput({ question, onQuestionChange, onSubmit, disabled, loading }: QuestionInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!disabled && !loading && question.trim()) onSubmit();
    }
  };

  return (
    <div className="w-full">
      <label className="block text-sm font-medium text-slate-600 mb-2">
        Sua pergunta
      </label>
      <div className="relative">
        <textarea
          value={question}
          onChange={(e) => onQuestionChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          placeholder="O que você quer saber sobre o documento?"
          rows={4}
          className="w-full resize-none rounded-xl border border-slate-200 bg-white px-4 py-3 pr-14 text-sm text-slate-800 placeholder-slate-400 shadow-sm transition-all duration-200 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-100 disabled:opacity-60"
        />
        <button
          onClick={onSubmit}
          disabled={disabled || loading || !question.trim()}
          className="absolute bottom-3 right-3 w-9 h-9 rounded-lg bg-sky-600 hover:bg-sky-700 disabled:bg-slate-200 flex items-center justify-center transition-all duration-200 shadow-sm disabled:shadow-none disabled:cursor-not-allowed group"
        >
          {loading ? (
            <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Send className="w-4 h-4 text-white group-disabled:text-slate-400 transition-colors" />
          )}
        </button>
      </div>
      <p className="text-xs text-slate-400 mt-2">Enter para enviar &bull; Shift + Enter para nova linha</p>
    </div>
  );
}
