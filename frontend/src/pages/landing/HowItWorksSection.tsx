import { FileText, MessageSquare, Sparkles } from 'lucide-react';
import { DARK } from '../../constants/theme';

const STEPS = [
  {
    icon: FileText,
    step: '01',
    title: 'Envie seu PDF',
    body: 'Arraste ou selecione qualquer documento. Em segundos o conteúdo é processado e indexado.',
  },
  {
    icon: MessageSquare,
    step: '02',
    title: 'Faça uma pergunta',
    body: 'Escreva em linguagem natural, como se estivesse perguntando para uma pessoa.',
  },
  {
    icon: Sparkles,
    step: '03',
    title: 'Receba a resposta',
    body: 'A IA responde com base nos trechos exatos do documento, sempre com a fonte citada.',
  },
];

export function HowItWorksSection() {
  return (
    <section id="como-funciona" className="py-24 px-6">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16 space-y-4">
          <p className="text-xs font-sans font-semibold tracking-widest uppercase" style={{ color: DARK.accent }}>
            Como funciona
          </p>
          <h2 className="font-display text-3xl sm:text-4xl text-white">Três passos. Zero complicação.</h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {STEPS.map(({ icon: Icon, step, title, body }) => (
            <div
              key={step}
              className="relative p-6 rounded-2xl hover:-translate-y-1 transition-transform duration-200"
              style={{ background: 'rgba(255,255,255,0.03)', border: `1px solid ${DARK.border}` }}
            >
              <div className="absolute top-5 right-5 font-display text-5xl font-bold opacity-5 text-white select-none">
                {step}
              </div>
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center mb-5"
                style={{ background: DARK.accentSubtle, border: `1px solid ${DARK.accentBorder}` }}
              >
                <Icon className="w-5 h-5" style={{ color: DARK.accent }} />
              </div>
              <h3 className="font-sans font-semibold text-white mb-2">{title}</h3>
              <p className="text-sm font-sans leading-relaxed" style={{ color: 'rgba(255,255,255,0.45)' }}>{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
