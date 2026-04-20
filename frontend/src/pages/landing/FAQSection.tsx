import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { DARK } from '../../constants/theme';

const FAQ_ITEMS = [
  {
    q: 'Como funciona o processamento do documento?',
    a: 'Após o upload, o PDF é convertido em texto, dividido em blocos semânticos e indexado em um banco vetorial. Em segundos está pronto para consultas.',
  },
  {
    q: 'O que acontece se a resposta não estiver no documento?',
    a: 'O sistema responde que não encontrou a informação. Nunca inventa nem usa conhecimento externo — a resposta vem exclusivamente do conteúdo que você enviou.',
  },
  {
    q: 'Meus documentos ficam seguros?',
    a: 'Seus arquivos são armazenados com criptografia e isolados por conta. Nunca são usados para treinar modelos ou compartilhados com terceiros.',
  },
  {
    q: 'Posso consultar múltiplos documentos ao mesmo tempo?',
    a: 'Sim. Você pode fazer upload de vários PDFs e escolher quais incluir em cada consulta, para cruzar informações de diferentes fontes.',
  },
  {
    q: 'Qual é o tamanho máximo de cada arquivo?',
    a: 'Até 50MB por arquivo PDF. Para documentos maiores ou casos especiais, entre em contato com o suporte.',
  },
  {
    q: 'Posso cancelar a qualquer momento?',
    a: 'Sim, sem multa ou burocracia. Basta acessar o painel de conta e cancelar. Você mantém acesso até o fim do período pago.',
  },
];

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);

  return (
    <div
      className="rounded-xl cursor-pointer transition-all duration-200"
      style={{
        background: open ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.02)',
        border: `1px solid ${DARK.border}`,
      }}
      onClick={() => setOpen(v => !v)}
    >
      <div className="flex items-center justify-between px-6 py-5">
        <span className="text-sm font-sans font-semibold text-white/90 pr-4">{q}</span>
        <ChevronDown
          className="w-4 h-4 shrink-0 transition-transform duration-300"
          style={{ color: DARK.accent, transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }}
        />
      </div>
      {open && (
        <div className="px-6 pb-5">
          <p className="text-sm font-sans leading-relaxed" style={{ color: DARK.textMuted }}>{a}</p>
        </div>
      )}
    </div>
  );
}

export function FAQSection() {
  return (
    <section id="faq" className="py-24 px-6">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-12 space-y-4">
          <p className="text-xs font-sans font-semibold tracking-widest uppercase" style={{ color: DARK.accent }}>
            FAQ
          </p>
          <h2 className="font-display text-3xl sm:text-4xl text-white">Perguntas frequentes</h2>
        </div>
        <div className="space-y-2">
          {FAQ_ITEMS.map((item) => (
            <FAQItem key={item.q} {...item} />
          ))}
        </div>
      </div>
    </section>
  );
}
