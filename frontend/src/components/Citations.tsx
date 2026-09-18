import { Check, AlertTriangle } from 'lucide-react';
import type { Citacao } from '../lib/api';
import { DARK } from '../constants/theme';

interface CitationsProps {
  citacoes: Citacao[];
  msgIndex: number;
}

export function Citations({ citacoes, msgIndex }: CitationsProps) {
  if (citacoes.length === 0) return null;

  return (
    <div
      className="rounded-xl px-3 py-2.5 text-xs font-sans space-y-1.5"
      style={{ background: 'rgba(255,255,255,0.03)', border: `1px solid ${DARK.border}` }}
    >
      <p className="font-medium" style={{ color: DARK.textMuted }}>Embasamento</p>
      <ul className="space-y-1.5">
        {citacoes.map(cit => (
          <li
            key={cit.id}
            id={`cit-${msgIndex}-${cit.id}`}
            className="flex items-start gap-2 rounded-lg px-2 py-1"
            style={{ color: DARK.text }}
          >
            {cit.verificada ? (
              <Check className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" style={{ color: DARK.emerald }} />
            ) : (
              <span title="Citação não encontrada literalmente no documento" className="flex-shrink-0 mt-0.5">
                <AlertTriangle className="w-3.5 h-3.5" style={{ color: DARK.accent }} />
              </span>
            )}
            <span className="leading-relaxed">
              <span style={{ color: DARK.textMuted }}>[{cit.id}]</span>{' '}
              <span className="font-medium">{cit.documento}</span>
              {cit.pagina != null && <span style={{ color: DARK.textMuted }}> · p. {cit.pagina}</span>}
              {' — '}
              <span style={{ color: DARK.textFaint, fontStyle: 'italic' }}>&quot;{cit.trecho}&quot;</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
