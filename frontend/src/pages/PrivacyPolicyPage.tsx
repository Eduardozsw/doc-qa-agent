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

export function PrivacyPolicyPage() {
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
            Conformidade LGPD
          </p>
          <h1 className="font-display text-3xl text-white mb-3">Política de Privacidade</h1>
          <p className="text-sm font-sans" style={{ color: DARK.textMuted }}>
            Última atualização: abril de 2026
          </p>
        </div>

        {/* Content */}
        <div className="rounded-2xl p-8 space-y-8" style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}>

          <Section title="1. Quem somos">
            <p>
              O <strong className="text-white">MindDoc</strong> é um assistente de perguntas e respostas sobre documentos.
              Permite que usuários enviem arquivos PDF e façam perguntas sobre o conteúdo,
              recebendo respostas baseadas exclusivamente nos documentos enviados.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="2. Dados coletados">
            <p>Coletamos apenas os dados estritamente necessários para o funcionamento do serviço:</p>
            <ul className="list-disc list-inside space-y-1 pl-2">
              <li><strong className="text-white">Email</strong> — usado exclusivamente para autenticação e identificação da conta</li>
              <li><strong className="text-white">Documentos PDF</strong> — enviados pelo próprio usuário para consulta, seja por upload direto ou importação do Google Drive</li>
              <li><strong className="text-white">Histórico de perguntas</strong> — mantido temporariamente na sessão ativa, não armazenado permanentemente</li>
            </ul>
            <p className="mt-2">
              Não coletamos nome, CPF, telefone, localização ou qualquer outro dado pessoal além do email.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="3. Integração com Google Drive (opcional)">
            <p>
              O MindDoc oferece a opção de importar arquivos PDF diretamente do Google Drive do usuário.
              Esta funcionalidade é <strong className="text-white">estritamente opcional</strong> e requer consentimento explícito a cada uso.
            </p>
            <ul className="list-disc list-inside space-y-1 pl-2 mt-2">
              <li>O acesso é concedido com o escopo <strong className="text-white">por arquivo</strong> (<code>drive.file</code>), limitado exclusivamente aos arquivos que o próprio usuário seleciona no seletor do Google</li>
              <li>O token de acesso OAuth é utilizado <strong className="text-white">apenas para baixar o arquivo selecionado</strong> e descartado imediatamente após o download</li>
              <li>O token <strong className="text-white">não é armazenado</strong> em nenhum banco de dados ou sistema de cache</li>
              <li>Nenhum outro arquivo do Drive é acessado além dos explicitamente selecionados pelo usuário</li>
              <li>O MindDoc não acessa, indexa nem monitora o Google Drive do usuário de forma contínua ou automática</li>
            </ul>
            <p className="mt-2">
              O uso dos dados obtidos via Google Drive segue as mesmas regras aplicadas aos documentos enviados diretamente:
              não são lidos por humanos, não são compartilhados e não são usados para treinar modelos de IA.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="4. Finalidade do tratamento">
            <p>Os dados são tratados com as seguintes finalidades:</p>
            <ul className="list-disc list-inside space-y-1 pl-2">
              <li><strong className="text-white">Email</strong> — autenticar o usuário e associar documentos à conta correta</li>
              <li><strong className="text-white">Documentos PDF</strong> — extrair texto e gerar representações vetoriais para viabilizar as respostas da IA</li>
              <li><strong className="text-white">Token Google Drive</strong> — baixar o arquivo selecionado pelo usuário; descartado imediatamente após o uso</li>
            </ul>
            <p className="mt-2">
              Os documentos enviados <strong className="text-white">não são lidos por humanos</strong>,
              não são compartilhados com terceiros e <strong className="text-white">não são utilizados para treinar modelos de inteligência artificial</strong>.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="5. Armazenamento e localização dos dados">
            <ul className="list-disc list-inside space-y-2 pl-2">
              <li>
                <strong className="text-white">Autenticação e perfil</strong> — armazenados no Supabase,
                com servidores localizados no <strong className="text-white">Brasil (sa-east-1 — São Paulo)</strong>
              </li>
              <li>
                <strong className="text-white">Vetores de busca</strong> — armazenados no Pinecone,
                com servidores nos <strong className="text-white">Estados Unidos</strong>.
                Esta transferência internacional está declarada em conformidade com o Art. 33 da LGPD,
                dado que o Pinecone adota salvaguardas adequadas de proteção de dados
              </li>
            </ul>
            <p className="mt-2">
              Os arquivos PDF originais <strong className="text-white">não são armazenados permanentemente</strong> —
              são processados em memória e descartados após a extração do texto.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="6. Retenção dos dados">
            <ul className="list-disc list-inside space-y-1 pl-2">
              <li>Dados de autenticação (email) — mantidos enquanto a conta estiver ativa</li>
              <li>Vetores de documentos — mantidos enquanto o documento estiver indexado na conta. Após remoção pelo usuário, o cache é invalidado em até 30 dias</li>
              <li>Histórico de conversa — não é armazenado entre sessões</li>
            </ul>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="7. Segurança">
            <ul className="list-disc list-inside space-y-1 pl-2">
              <li>Senhas nunca armazenadas em texto puro — protegidas com hash bcrypt pelo Supabase</li>
              <li>Todo o tráfego entre o navegador e os servidores é cifrado via HTTPS</li>
              <li>Tokens de autenticação têm tempo de expiração e são renovados automaticamente</li>
            </ul>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="8. Seus direitos (Art. 18 da LGPD)">
            <p>Você tem direito a:</p>
            <ul className="list-disc list-inside space-y-1 pl-2">
              <li>Confirmar a existência de tratamento dos seus dados</li>
              <li>Acessar os dados que temos sobre você</li>
              <li>Corrigir dados incompletos ou incorretos</li>
              <li>Solicitar a exclusão dos seus dados e conta</li>
              <li>Revogar o consentimento a qualquer momento</li>
              <li>Portabilidade dos seus dados</li>
            </ul>
            <p className="mt-2">
              Para exercer qualquer um desses direitos, entre em contato pelo email:{' '}
              <span className="px-2 py-0.5 rounded text-xs" style={{ background: 'rgba(255,255,255,0.06)', color: DARK.textMuted }}>
                em breve
              </span>
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="9. Cookies e rastreamento">
            <p>
              O MindDoc utiliza apenas cookies de sessão estritamente necessários para manter o usuário autenticado.
              Não utilizamos cookies de rastreamento, publicidade ou analytics de terceiros.
            </p>
          </Section>

          <div style={{ borderTop: `1px solid ${DARK.border}` }} />

          <Section title="10. Alterações nesta política">
            <p>
              Eventuais alterações nesta política serão comunicadas através da interface do serviço.
              O uso continuado após as alterações implica na aceitação dos novos termos.
            </p>
          </Section>

        </div>
      </main>
    </div>
  );
}
