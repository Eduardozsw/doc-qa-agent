import { Link } from 'react-router-dom';
import { Sparkles, ArrowLeft } from 'lucide-react';
import { DARK } from '../constants/theme';

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3">
      <h2 className="text-base font-display font-semibold text-white">{title}</h2>
      <div className="text-sm font-sans leading-relaxed space-y-2" style={{ color: DARK.textMuted }}>
        {children}
      </div>
    </section>
  );
}

export function TermsOfServicePage() {
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
        <div className="max-w-3xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
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

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-12 relative">
        {/* Title */}
        <div className="mb-10">
          <p className="text-xs font-sans uppercase tracking-widest mb-3" style={{ color: DARK.accent }}>
            Legal
          </p>
          <h1 className="font-display text-3xl text-white mb-3">Termos de Serviço</h1>
          <p className="text-sm font-sans" style={{ color: DARK.textMuted }}>
            Última atualização: maio de 2026
          </p>
        </div>

        {/* Content */}
        <div className="rounded-2xl p-8 space-y-8" style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}>

          <Section title="1. Aceitação dos termos">
            <p>
              Ao acessar ou utilizar o <strong className="text-white">MindDoc</strong>, você concorda com estes Termos de Serviço.
              Se não concordar com qualquer parte destes termos, não utilize o serviço.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="2. Descrição do serviço">
            <p>
              O MindDoc é um assistente de perguntas e respostas sobre documentos. O serviço permite que usuários
              cadastrados enviem arquivos PDF — por upload direto ou importação do Google Drive — e façam perguntas
              sobre o conteúdo, recebendo respostas geradas por inteligência artificial baseadas exclusivamente nos
              documentos enviados.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="3. Conta e acesso">
            <ul className="list-disc list-inside space-y-1 pl-2">
              <li>É necessário criar uma conta para utilizar o serviço</li>
              <li>Você é responsável por manter a confidencialidade das suas credenciais de acesso</li>
              <li>É proibido compartilhar sua conta com terceiros</li>
              <li>Nos reservamos o direito de suspender ou encerrar contas que violem estes termos</li>
            </ul>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="4. Uso aceitável">
            <p>Você concorda em utilizar o MindDoc apenas para finalidades lícitas. É expressamente proibido:</p>
            <ul className="list-disc list-inside space-y-1 pl-2 mt-2">
              <li>Enviar documentos com conteúdo ilegal, difamatório ou que viole direitos de terceiros</li>
              <li>Tentar contornar limites de uso, planos ou mecanismos de autenticação</li>
              <li>Usar o serviço para fins de revenda ou exploração comercial não autorizada</li>
              <li>Realizar ataques de força bruta, scraping ou sobrecarga intencional dos servidores</li>
            </ul>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="5. Documentos e conteúdo enviado">
            <p>
              Você mantém todos os direitos sobre os documentos que envia. Ao enviar um documento, você concede ao
              MindDoc uma licença limitada, não exclusiva e revogável para processar o conteúdo exclusivamente com
              o objetivo de gerar respostas às suas perguntas.
            </p>
            <p className="mt-2">
              Você declara que tem o direito de enviar os documentos e que o conteúdo não viola leis aplicáveis
              nem direitos de terceiros.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="6. Planos e pagamento">
            <ul className="list-disc list-inside space-y-1 pl-2">
              <li>O MindDoc oferece um plano gratuito com limites de uso e planos pagos com funcionalidades ampliadas</li>
              <li>Os valores dos planos pagos estão descritos na página de preços e podem ser alterados com aviso prévio de 30 dias</li>
              <li>Assinaturas são cobradas de forma recorrente conforme o ciclo escolhido (mensal ou anual)</li>
              <li>Cancelamentos encerram a cobrança no próximo ciclo; o acesso permanece até o fim do período pago</li>
              <li>Não realizamos reembolsos de períodos parciais, salvo exigência legal</li>
            </ul>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="7. Disponibilidade do serviço">
            <p>
              Nos esforçamos para manter o MindDoc disponível continuamente, mas não garantimos disponibilidade
              ininterrupta. Podemos realizar manutenções, atualizações ou suspender temporariamente o serviço
              sem aviso prévio em casos de urgência técnica.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="8. Limitação de responsabilidade">
            <p>
              O MindDoc fornece respostas geradas por inteligência artificial com base nos documentos enviados.
              Essas respostas <strong className="text-white">não constituem aconselhamento jurídico, médico, financeiro ou profissional</strong> de qualquer natureza.
            </p>
            <p className="mt-2">
              Não nos responsabilizamos por decisões tomadas com base nas respostas geradas pelo serviço,
              nem por perdas decorrentes de imprecisões ou limitações dos modelos de IA utilizados.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="9. Privacidade">
            <p>
              O tratamento dos seus dados pessoais é regido pela nossa{' '}
              <Link to="/privacidade" className="underline hover:text-white transition-colors" style={{ color: DARK.accent }}>
                Política de Privacidade
              </Link>
              , que é parte integrante destes termos.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="10. Alterações nos termos">
            <p>
              Podemos atualizar estes termos periodicamente. Alterações relevantes serão comunicadas através da
              interface do serviço ou por email. O uso continuado após as alterações implica na aceitação dos
              novos termos.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="11. Lei aplicável">
            <p>
              Estes termos são regidos pelas leis da República Federativa do Brasil. Fica eleito o foro da
              comarca de domicílio do usuário para dirimir quaisquer controvérsias decorrentes deste instrumento,
              conforme o Art. 101, I do Código de Defesa do Consumidor.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="12. Contato">
            <p>
              Para dúvidas sobre estes termos, entre em contato pelo email:{' '}
              <a href="mailto:dudusoutomaior2006@gmail.com" className="underline hover:text-white transition-colors" style={{ color: DARK.accent }}>
                dudusoutomaior2006@gmail.com
              </a>
            </p>
          </Section>

        </div>
      </main>
    </div>
  );
}
