import { Stethoscope, ClipboardList, FlaskConical, Brain, HeartPulse, ShieldCheck } from 'lucide-react';
import { DARK } from '../../constants/theme';

const USECASES = [
  { icon: Stethoscope, title: 'Médicos(as)', body: 'Consulte protocolos clínicos e diretrizes durante o atendimento, sem folhear PDF.' },
  { icon: ClipboardList, title: 'Consultórios', body: 'Encontre informação em prontuários e históricos em segundos, com a fonte citada.' },
  { icon: FlaskConical, title: 'Laudos e exames', body: 'Busque achados específicos em laudos longos sem precisar reler o documento inteiro.' },
  { icon: Brain, title: 'Psicologia', body: 'Revise registros de sessão e materiais clínicos mantendo os dados do paciente protegidos.' },
  { icon: HeartPulse, title: 'Condutas e diretrizes', body: 'Tire dúvidas de condutas a partir das suas próprias referências e materiais de apoio.' },
  { icon: ShieldCheck, title: 'Dados sensíveis', body: 'Documentos de paciente isolados por conta e tratados em conformidade com a LGPD.' },
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
            Feito para a rotina de<br className="hidden sm:block" /> quem cuida de pacientes
          </h2>
          <p className="text-sm font-sans max-w-md mx-auto" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Se você perde tempo procurando uma informação pontual no meio de laudos, protocolos e prontuários, o MindDoc foi feito para você.
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
