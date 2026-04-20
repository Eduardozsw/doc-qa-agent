import { KeyboardEvent } from 'react';
import { Send } from 'lucide-react';
import { DARK } from '../constants/theme';

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
      <div className="relative">
        <textarea
          value={question}
          onChange={(e) => onQuestionChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          placeholder="O que você quer saber sobre o documento?"
          rows={3}
          className="w-full resize-none rounded-xl px-4 py-3 pr-14 text-sm font-sans leading-relaxed transition-all duration-200 focus:outline-none disabled:opacity-50"
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: `1px solid ${DARK.border}`,
            color: DARK.text,
            caretColor: DARK.accent,
          }}
          onFocus={e => { e.target.style.border = `1px solid ${DARK.accentBorder}`; e.target.style.boxShadow = `0 0 0 3px ${DARK.accentSubtle}`; }}
          onBlur={e => { e.target.style.border = `1px solid ${DARK.border}`; e.target.style.boxShadow = 'none'; }}
        />
        <button
          onClick={onSubmit}
          disabled={disabled || loading || !question.trim()}
          className="absolute bottom-3 right-3 w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-30"
          style={{
            background: disabled || loading || !question.trim()
              ? 'rgba(255,255,255,0.08)'
              : `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
          }}
        >
          {loading ? (
            <span className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: `${DARK.accent} transparent transparent transparent` }} />
          ) : (
            <Send className="w-4 h-4 text-white" />
          )}
        </button>
      </div>
      <p className="text-xs font-sans mt-2" style={{ color: DARK.textFaint }}>
        Enter para enviar &bull; Shift + Enter para nova linha
      </p>
    </div>
  );
}
