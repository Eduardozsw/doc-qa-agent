import { CheckCircle2, ArrowRight, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { DARK } from '../constants/theme';

export function SuccessPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col items-center justify-center font-sans px-6" style={{ background: DARK.bg }}>
      <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden>
        <div
          className="absolute rounded-full blur-3xl opacity-20"
          style={{ width: 500, height: 500, top: -150, left: '50%', transform: 'translateX(-50%)', background: `radial-gradient(circle, ${DARK.emerald}, transparent 70%)` }}
        />
      </div>

      <div className="relative text-center space-y-6 max-w-md">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto"
          style={{ background: DARK.emeraldSubtle, border: `1px solid ${DARK.emeraldBorder}` }}
        >
          <CheckCircle2 className="w-8 h-8" style={{ color: DARK.emerald }} />
        </div>

        <div className="space-y-2">
          <h1 className="font-display text-3xl text-white">Assinatura ativada!</h1>
          <p className="text-sm font-sans" style={{ color: DARK.textMuted }}>
            Seu plano foi atualizado. Pode demorar alguns instantes para refletir no app.
          </p>
        </div>

        <button
          onClick={() => navigate('/app')}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-sans font-semibold transition-all duration-200 hover:opacity-90 active:scale-95"
          style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`, color: DARK.bg }}
        >
          <Sparkles className="w-4 h-4" />
          Ir para o app
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
