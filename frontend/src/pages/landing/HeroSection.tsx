import { useState, useEffect } from 'react';
import { FileText, Check, Zap, ArrowRight } from 'lucide-react';
import { DARK } from '../../constants/theme';

const CONVERSATIONS = [
  {
    file: 'Contrato_Servicos_2024.pdf',
    question: 'Qual é o prazo de vigência do contrato?',
    answer: 'O contrato tem vigência de 12 meses, iniciando em 1º de janeiro de 2024. Pode ser renovado automaticamente por períodos iguais com notificação de 30 dias.',
    source: 'Cláusula 4.1 — Vigência',
  },
  {
    file: 'Relatorio_Financeiro_Q3.pdf',
    question: 'Qual foi o lucro líquido no terceiro trimestre?',
    answer: 'O lucro líquido no Q3 foi de R$ 4,2 milhões, crescimento de 18% em relação ao mesmo período do ano anterior, conforme demonstrativo de resultados.',
    source: 'Pág. 12 — Demonstrativo de Resultados',
  },
  {
    file: 'Manual_Produto_v3.pdf',
    question: 'Como configurar a integração com o sistema ERP?',
    answer: 'Acesse Configurações → Integrações → ERP. Insira a URL base e a chave de API do seu sistema. A conexão usa REST com autenticação OAuth 2.0.',
    source: 'Seção 8.3 — Integrações',
  },
];

const TIMINGS = {
  initialDelay: 1400,
  wordDelay: 55,
  completionDelay: 800,
  cycleDelay: 3000,
};

function useHeroAnimation() {
  const [convIdx, setConvIdx] = useState(0);
  const [displayedAnswer, setDisplayedAnswer] = useState('');
  const [phase, setPhase] = useState<'question' | 'typing' | 'done'>('question');

  useEffect(() => {
    const conv = CONVERSATIONS[convIdx];

    if (phase === 'question') {
      const t = setTimeout(() => setPhase('typing'), TIMINGS.initialDelay);
      return () => clearTimeout(t);
    }

    if (phase === 'typing') {
      setDisplayedAnswer('');
      const words = conv.answer.split(' ');
      let idx = 0;
      const interval = setInterval(() => {
        idx++;
        setDisplayedAnswer(words.slice(0, idx).join(' '));
        if (idx >= words.length) {
          clearInterval(interval);
          setTimeout(() => setPhase('done'), TIMINGS.completionDelay);
        }
      }, TIMINGS.wordDelay);
      return () => clearInterval(interval);
    }

    if (phase === 'done') {
      const t = setTimeout(() => {
        setConvIdx(i => (i + 1) % CONVERSATIONS.length);
        setDisplayedAnswer('');
        setPhase('question');
      }, TIMINGS.cycleDelay);
      return () => clearTimeout(t);
    }
  }, [convIdx, phase]);

  return { conv: CONVERSATIONS[convIdx], displayedAnswer, phase, convIdx };
}

function HeroMockup() {
  const { conv, displayedAnswer, phase, convIdx } = useHeroAnimation();

  return (
    <div
      className="relative w-full max-w-md mx-auto rounded-2xl overflow-hidden shadow-2xl"
      style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}
    >
      <div
        className="flex items-center gap-1.5 px-4 py-3"
        style={{ background: '#0a0a16', borderBottom: `1px solid ${DARK.borderLight}` }}
      >
        <span className="w-3 h-3 rounded-full bg-red-500/70" />
        <span className="w-3 h-3 rounded-full bg-yellow-500/70" />
        <span className="w-3 h-3 rounded-full bg-green-500/70" />
        <span className="ml-3 text-xs font-sans" style={{ color: DARK.textFaint }}>MindDoc</span>
      </div>

      <div className="p-5 space-y-4">
        <div className="flex items-center gap-2">
          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-sans font-medium transition-all duration-300"
            style={{ background: DARK.skySubtle, color: '#38bdf8', border: `1px solid ${DARK.skyBorder}` }}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>{conv.file}</span>
          </div>
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        </div>

        <div className="flex justify-end">
          <div
            className="max-w-[85%] rounded-2xl rounded-tr-sm px-4 py-3 text-sm font-sans leading-relaxed"
            style={{ background: DARK.accentSubtle, color: '#fcd34d', border: `1px solid ${DARK.accentBorder}` }}
          >
            {conv.question}
          </div>
        </div>

        <div className="flex justify-start">
          <div
            className="max-w-[90%] rounded-2xl rounded-tl-sm px-4 py-3 text-sm font-sans leading-relaxed"
            style={{ background: 'rgba(255,255,255,0.05)', color: DARK.text, border: `1px solid ${DARK.border}`, minHeight: '80px' }}
          >
            {phase === 'question' ? (
              <span className="opacity-40 italic text-xs">Processando...</span>
            ) : (
              <>
                {displayedAnswer}
                {phase === 'typing' && (
                  <span className="inline-block w-0.5 h-4 bg-amber-400 ml-0.5 animate-pulse align-middle" />
                )}
              </>
            )}
          </div>
        </div>

        {phase === 'done' && (
          <div
            className="flex items-center gap-1.5 text-xs font-sans px-2.5 py-1.5 rounded-lg w-fit"
            style={{ background: DARK.emeraldSubtle, color: DARK.emerald, border: `1px solid ${DARK.emeraldBorder}` }}
          >
            <Check className="w-3 h-3" />
            <span>Fonte: {conv.source}</span>
          </div>
        )}

        <div className="flex items-center justify-center gap-1.5 pt-1">
          {CONVERSATIONS.map((_, i) => (
            <span
              key={i}
              className="rounded-full transition-all duration-300"
              style={{
                width: i === convIdx ? '16px' : '6px',
                height: '6px',
                background: i === convIdx ? DARK.accent : 'rgba(255,255,255,0.2)',
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface HeroSectionProps {
  onCTA: () => void;
  isLoggedIn: boolean;
}

export function HeroSection({ onCTA, isLoggedIn }: HeroSectionProps) {
  return (
    <section className="pt-36 pb-28 px-6 relative">
      <div className="max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="space-y-8">
            <div
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-sans font-medium"
              style={{ background: DARK.accentSubtle, color: '#fbbf24', border: `1px solid ${DARK.accentBorder}` }}
            >
              <Zap className="w-3.5 h-3.5" />
              <span>Respostas precisas, sem alucinação</span>
            </div>

            <h1
              className="font-display leading-[1.12] text-white"
              style={{ fontSize: 'clamp(2.4rem, 5vw, 3.6rem)' }}
            >
              Pergunte ao seu<br />
              <span style={{ color: DARK.accent }}>documento.</span><br />
              Obtenha respostas.
            </h1>

            <p className="text-base font-sans leading-relaxed max-w-lg" style={{ color: DARK.textMuted }}>
              Carregue qualquer PDF e faça perguntas em linguagem natural. A IA responde com base exclusiva no conteúdo — com a fonte citada. Nunca inventa.
            </p>

            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={onCTA}
                className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-sm font-sans font-semibold transition-all duration-200 hover:opacity-90 active:scale-95"
                style={{
                  background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
                  color: DARK.bg,
                  boxShadow: `0 0 40px ${DARK.accentGlow}`,
                }}
              >
                {isLoggedIn ? 'Abrir o app' : 'Começar gratuitamente'}
                <ArrowRight className="w-4 h-4" />
              </button>
              <a
                href="#como-funciona"
                className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl text-sm font-sans font-semibold transition-all duration-200 hover:bg-white/5"
                style={{ color: 'rgba(255,255,255,0.7)', border: `1px solid ${DARK.border}` }}
              >
                Como funciona
              </a>
            </div>

            <div className="flex items-center gap-6 text-xs font-sans" style={{ color: DARK.textFaint }}>
              <div className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5 text-emerald-400" /> Sem cartão de crédito</div>
              <div className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5 text-emerald-400" /> Login com Google</div>
              <div className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5 text-emerald-400" /> Grátis para começar</div>
            </div>
          </div>

          <div className="relative">
            <div
              className="absolute inset-0 rounded-3xl blur-2xl opacity-30 -z-10"
              style={{ background: `radial-gradient(circle at center, ${DARK.accent}, transparent 70%)` }}
            />
            <HeroMockup />
          </div>
        </div>
      </div>
    </section>
  );
}
