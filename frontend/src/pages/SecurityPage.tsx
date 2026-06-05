import { Link } from 'react-router-dom';
import {
  Sparkles, ArrowLeft, ShieldCheck, Lock, KeyRound, Server,
  Gauge, Filter, EyeOff, FileX, MapPin,
} from 'lucide-react';
import { DARK } from '../constants/theme';

const MEASURES = [
  {
    icon: ShieldCheck,
    title: 'Isolamento por conta',
    body: 'Cada documento fica vinculado à conta que o enviou. Toda consulta valida no servidor se os documentos pertencem ao usuário — uma conta nunca acessa ou cruza dados de outra.',
  },
  {
    icon: KeyRound,
    title: 'Autenticação em cada requisição',
    body: 'Todo acesso à API exige um token de autenticação válido (JWT), verificado a cada requisição. Tokens têm expiração e são renovados automaticamente.',
  },
  {
    icon: Lock,
    title: 'Criptografia em trânsito',
    body: 'Todo o tráfego entre o navegador e os servidores é cifrado via HTTPS. Senhas nunca são armazenadas em texto puro — são protegidas com hash bcrypt.',
  },
  {
    icon: EyeOff,
    title: 'Seus dados não treinam IA',
    body: 'Os documentos enviados não são lidos por humanos, não são compartilhados com terceiros e não são utilizados para treinar modelos de inteligência artificial.',
  },
  {
    icon: FileX,
    title: 'PDFs não ficam armazenados',
    body: 'Os arquivos originais são processados em memória e descartados após a extração do texto. Apenas as representações vetoriais usadas na busca ficam indexadas na sua conta.',
  },
  {
    icon: Gauge,
    title: 'Limites de uso e proteção contra abuso',
    body: 'Os endpoints têm limites de requisição (rate limiting) que protegem o serviço contra uso abusivo e tentativas automatizadas.',
  },
  {
    icon: Filter,
    title: 'Sanitização de entrada',
    body: 'O conteúdo enviado nas consultas é sanitizado antes do processamento, reduzindo a superfície para ataques de injeção.',
  },
  {
    icon: Server,
    title: 'Respostas ancoradas na fonte',
    body: 'A IA responde exclusivamente com base nos trechos dos seus documentos, sempre com a fonte citada. Um guardrail bloqueia respostas sem base no material enviado.',
  },
];

function MeasureCard({ icon: Icon, title, body }: typeof MEASURES[number]) {
  return (
    <div className="rounded-2xl p-6 space-y-3" style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}>
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center"
        style={{ background: DARK.accentSubtle, border: `1px solid ${DARK.accentBorder}` }}
      >
        <Icon className="w-5 h-5" style={{ color: DARK.accent }} />
      </div>
      <h3 className="font-sans font-semibold text-white">{title}</h3>
      <p className="text-sm font-sans leading-relaxed" style={{ color: DARK.textMuted }}>{body}</p>
    </div>
  );
}

export function SecurityPage() {
  return (
    <div className="min-h-screen font-sans" style={{ background: DARK.bg }}>
      {/* Ambient blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden>
        <div className="absolute rounded-full blur-3xl opacity-10"
          style={{ width: 500, height: 500, top: -150, left: -150, background: `radial-gradient(circle, ${DARK.accent}, transparent 70%)` }} />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-40 flex-shrink-0"
        style={{ backdropFilter: 'blur(16px)', background: 'rgba(8,8,15,0.85)', borderBottom: `1px solid ${DARK.borderLight}` }}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}>
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-display text-base text-white tracking-tight">MindDoc</span>
          </div>
          <Link to="/"
            className="flex items-center gap-1.5 text-sm font-sans transition-colors hover:text-white"
            style={{ color: DARK.textMuted }}>
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-12 relative">
        {/* Title */}
        <div className="mb-10 max-w-2xl">
          <p className="text-xs font-sans uppercase tracking-widest mb-3" style={{ color: DARK.accent }}>
            Segurança e privacidade
          </p>
          <h1 className="font-display text-3xl sm:text-4xl text-white mb-4">
            Dados sensíveis exigem proteção à altura.
          </h1>
          <p className="text-sm font-sans leading-relaxed" style={{ color: DARK.textMuted }}>
            Dado de paciente é dado pessoal sensível pela LGPD e merece o nível máximo de cuidado.
            Abaixo estão as medidas técnicas que já protegem cada documento que você envia ao MindDoc.
          </p>
        </div>

        {/* Measures grid */}
        <div className="grid sm:grid-cols-2 gap-4">
          {MEASURES.map((m) => (
            <MeasureCard key={m.title} {...m} />
          ))}
        </div>

        {/* Data location */}
        <div className="mt-4 rounded-2xl p-6 space-y-3" style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}>
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: DARK.accentSubtle, border: `1px solid ${DARK.accentBorder}` }}
            >
              <MapPin className="w-5 h-5" style={{ color: DARK.accent }} />
            </div>
            <h3 className="font-sans font-semibold text-white">Onde seus dados ficam</h3>
          </div>
          <ul className="text-sm font-sans leading-relaxed space-y-1.5 list-disc list-inside pl-1" style={{ color: DARK.textMuted }}>
            <li>
              <strong className="text-white">Autenticação e perfil</strong> — armazenados no Supabase,
              com servidores no <strong className="text-white">Brasil (São Paulo)</strong>.
            </li>
            <li>
              <strong className="text-white">Vetores de busca</strong> — armazenados no Pinecone (Estados Unidos),
              com transferência internacional em conformidade com o Art. 33 da LGPD.
            </li>
          </ul>
        </div>

        {/* Footer note */}
        <p className="mt-8 text-xs font-sans leading-relaxed" style={{ color: DARK.textFaint }}>
          Para detalhes sobre coleta, retenção e seus direitos, consulte a{' '}
          <Link to="/privacidade" className="underline hover:text-white" style={{ color: DARK.textMuted }}>
            Política de Privacidade
          </Link>
          . É controladora dos dados de seus pacientes a clínica ou profissional que os trata; o MindDoc atua como
          operador, processando os dados conforme as instruções do usuário.
        </p>
      </main>
    </div>
  );
}
