import { Lock, ShieldCheck, Infinity } from 'lucide-react';
import { DARK } from '../../constants/theme';

const ITEMS = [
  { icon: ShieldCheck, label: 'Conformidade com a LGPD', sub: 'Dados sensíveis tratados com nível máximo de proteção' },
  { icon: Lock, label: 'Isolados por conta', sub: 'Os documentos de um usuário nunca se misturam com outros' },
  { icon: Infinity, label: 'Sem alucinação', sub: 'Só responde com base no que está no documento' },
];

export function TrustBarSection() {
  return (
    <section
      className="py-14 px-6"
      style={{
        background: 'rgba(255,255,255,0.02)',
        borderTop: `1px solid ${DARK.borderLight}`,
        borderBottom: `1px solid ${DARK.borderLight}`,
      }}
    >
      <div className="max-w-5xl mx-auto">
        <div className="grid sm:grid-cols-3 gap-8 text-center">
          {ITEMS.map(({ icon: Icon, label, sub }) => (
            <div key={label} className="flex flex-col items-center gap-2">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center"
                style={{ background: DARK.accentSubtle, border: `1px solid ${DARK.accentBorder}` }}
              >
                <Icon className="w-5 h-5" style={{ color: DARK.accent }} />
              </div>
              <span className="font-sans font-semibold text-sm text-white">{label}</span>
              <span className="text-xs font-sans" style={{ color: DARK.textFaint }}>{sub}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
