import { Scale, FlaskConical, Users, GraduationCap, BarChart3, Shield } from 'lucide-react';
import { DARK } from '../../constants/theme';

const USECASES = [
  { icon: Scale, title: 'Advogados', body: 'Analise contratos, petições e laudos em segundos, sem precisar ler o documento inteiro.' },
  { icon: FlaskConical, title: 'Pesquisadores', body: 'Consulte artigos e papers científicos sem ler tudo — extraia só o que é relevante.' },
  { icon: Users, title: 'Equipes de RH', body: 'Responda dúvidas sobre políticas internas, benefícios e processos de forma instantânea.' },
  { icon: GraduationCap, title: 'Estudantes', body: 'Tire dúvidas de apostilas e livros didáticos. Entenda o material antes da prova.' },
  { icon: BarChart3, title: 'Gestores', body: 'Extraia insights de relatórios financeiros e apresentações sem perder tempo.' },
  { icon: Shield, title: 'Compliance', body: 'Verifique aderência a normas e regulamentos rapidamente, com rastreabilidade da fonte.' },
];

export function UseCasesSection() {
  return (
    <section className="py-24 px-6" style={{ background: 'rgba(255,255,255,0.015)' }}>
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16 space-y-4">
          <p className="text-xs font-sans font-semibold tracking-widest uppercase" style={{ color: DARK.accent }}>
            Para quem é
          </p>
          <h2 className="font-display text-3xl sm:text-4xl text-white">
            Qualquer profissional que<br className="hidden sm:block" /> lida com documentos
          </h2>
          <p className="text-sm font-sans max-w-md mx-auto" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Se você passa horas lendo documentos para encontrar uma informação pontual, o MindDoc foi feito para você.
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {USECASES.map(({ icon: Icon, title, body }) => (
            <div
              key={title}
              className="p-5 rounded-xl hover:-translate-y-0.5 transition-transform duration-200"
              style={{ background: 'rgba(255,255,255,0.03)', border: `1px solid ${DARK.border}` }}
            >
              <div className="flex items-center gap-3 mb-3">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center"
                  style={{ background: DARK.skySubtle, border: `1px solid ${DARK.skyBorder}` }}
                >
                  <Icon className="w-4 h-4" style={{ color: '#38bdf8' }} />
                </div>
                <span className="font-sans font-semibold text-sm text-white">{title}</span>
              </div>
              <p className="text-xs font-sans leading-relaxed" style={{ color: 'rgba(255,255,255,0.45)' }}>{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
