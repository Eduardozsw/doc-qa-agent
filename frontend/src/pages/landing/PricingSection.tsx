import { Check } from 'lucide-react';
import { DARK } from '../../constants/theme';

const PLANS = [
  {
    name: 'Grátis',
    price: 'R$0',
    period: 'para sempre',
    description: 'Para experimentar sem compromisso.',
    highlight: false,
    features: [
      '3 documentos por mês',
      '50 perguntas por mês',
      '1 usuário',
      'Respostas com fonte citada',
      'Suporte via comunidade',
    ],
    cta: 'Começar grátis',
  },
  {
    name: 'Basic',
    price: 'R$29',
    period: 'por mês',
    description: 'Para profissionais que trabalham com documentos diariamente.',
    highlight: true,
    features: [
      '20 documentos por mês',
      '500 perguntas por mês',
      'Até 3 usuários',
      'Histórico de conversas',
      'Respostas com fonte citada',
      'Suporte por e-mail',
    ],
    cta: 'Assinar Basic',
  },
  {
    name: 'Premium',
    price: 'R$79',
    period: 'por mês',
    description: 'Para equipes que precisam de escala e controle.',
    highlight: false,
    features: [
      'Documentos ilimitados',
      'Perguntas ilimitadas',
      'Usuários ilimitados',
      'Acesso à API',
      'Suporte prioritário',
      'SLA garantido',
    ],
    cta: 'Assinar Premium',
  },
];

interface PricingSectionProps {
  onCTA: () => void;
}

export function PricingSection({ onCTA }: PricingSectionProps) {
  return (
    <section id="precos" className="py-24 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16 space-y-4">
          <p className="text-xs font-sans font-semibold tracking-widest uppercase" style={{ color: DARK.accent }}>
            Preços
          </p>
          <h2 className="font-display text-3xl sm:text-4xl text-white">Comece grátis. Escale quando precisar.</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6 items-start">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className="relative rounded-2xl p-6 flex flex-col gap-6 transition-all duration-200"
              style={{
                background: plan.highlight ? 'rgba(245,158,11,0.07)' : 'rgba(255,255,255,0.03)',
                border: plan.highlight ? `1px solid rgba(245,158,11,0.35)` : `1px solid ${DARK.border}`,
                boxShadow: plan.highlight ? `0 0 60px ${DARK.accentSubtle}` : 'none',
              }}
            >
              {plan.highlight && (
                <div
                  className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-sans font-semibold"
                  style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`, color: DARK.bg }}
                >
                  Mais popular
                </div>
              )}
              <div>
                <p
                  className="font-sans font-semibold text-sm"
                  style={{ color: plan.highlight ? '#fbbf24' : DARK.textMuted }}
                >
                  {plan.name}
                </p>
                <div className="flex items-baseline gap-1 mt-2">
                  <span className="font-display text-4xl text-white">{plan.price}</span>
                  <span className="text-xs font-sans" style={{ color: 'rgba(255,255,255,0.4)' }}>/{plan.period}</span>
                </div>
                <p className="text-xs font-sans mt-2 leading-relaxed" style={{ color: 'rgba(255,255,255,0.4)' }}>
                  {plan.description}
                </p>
              </div>
              <ul className="space-y-2.5">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-xs font-sans" style={{ color: 'rgba(255,255,255,0.7)' }}>
                    <Check
                      className="w-3.5 h-3.5 shrink-0 mt-0.5"
                      style={{ color: plan.highlight ? DARK.accent : DARK.emerald }}
                    />
                    {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={onCTA}
                className="mt-auto w-full py-3 rounded-xl text-sm font-sans font-semibold transition-all duration-200 hover:opacity-90 active:scale-95"
                style={
                  plan.highlight
                    ? { background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`, color: DARK.bg }
                    : { background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.8)', border: `1px solid ${DARK.border}` }
                }
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
