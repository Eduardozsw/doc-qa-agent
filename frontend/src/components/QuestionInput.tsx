import { KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
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

  const canSend = !disabled && !loading && question.trim().length > 0;

  return (
    <div
      style={{
        display: 'flex', alignItems: 'flex-end', gap: 8,
        background: 'rgba(255,255,255,0.04)',
        border: `1px solid ${DARK.border}`,
        borderRadius: 14, padding: '10px 12px',
        transition: 'border 0.2s, box-shadow 0.2s',
      }}
      onFocus={e => {
        (e.currentTarget as HTMLDivElement).style.border = `1px solid ${DARK.accentBorder}`;
        (e.currentTarget as HTMLDivElement).style.boxShadow = `0 0 0 3px rgba(245,158,11,0.06)`;
      }}
      onBlur={e => {
        if (!e.currentTarget.contains(e.relatedTarget)) {
          (e.currentTarget as HTMLDivElement).style.border = `1px solid ${DARK.border}`;
          (e.currentTarget as HTMLDivElement).style.boxShadow = 'none';
        }
      }}
    >
      <textarea
        value={question}
        onChange={e => onQuestionChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={e => {
          const el = e.currentTarget;
          el.style.height = 'auto';
          el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
        }}
        disabled={loading}
        placeholder="Pergunte sobre os documentos selecionados..."
        maxLength={5000}
        rows={1}
        style={{
          flex: 1, background: 'none', border: 'none', outline: 'none',
          color: DARK.text, fontSize: 13, resize: 'none',
          minHeight: 20, maxHeight: 120, lineHeight: '1.5',
          fontFamily: 'inherit',
        }}
      />
      <button
        onClick={onSubmit}
        disabled={!canSend}
        style={{
          width: 32, height: 32, borderRadius: 8, flexShrink: 0,
          background: canSend ? `linear-gradient(135deg, ${DARK.accent}, #d97706)` : 'rgba(255,255,255,0.06)',
          border: 'none', cursor: canSend ? 'pointer' : 'default',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'background 0.2s',
          opacity: canSend ? 1 : 0.4,
        }}
      >
        {loading
          ? <Loader2 style={{ width: 14, height: 14, color: DARK.accent }} />
          : <Send style={{ width: 14, height: 14, color: 'white' }} />}
      </button>
    </div>
  );
}
