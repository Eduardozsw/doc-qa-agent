import { Sparkles, ArrowRight } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { DARK } from '../constants/theme';
import { HeroSection } from './landing/HeroSection';
import { HowItWorksSection } from './landing/HowItWorksSection';
import { UseCasesSection } from './landing/UseCasesSection';
import { PricingSection } from './landing/PricingSection';
import { TrustBarSection } from './landing/TrustBarSection';
import { FAQSection } from './landing/FAQSection';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

export function LandingPage() {
  const { user, session } = useAuth();
  const navigate = useNavigate();

  const handleCTA = () => {
    if (user) navigate('/app');
    else navigate('/login');
  };

  const handleSelectPlan = async (plan: string, paymentMethod: 'card' | 'pix' = 'card') => {
    if (plan === 'free') {
      handleCTA();
      return;
    }

    if (!user || !session) {
      sessionStorage.setItem('pending_plan', plan);
      navigate('/login');
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/billing/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({ plan, payment_method: paymentMethod }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      window.location.href = data.url;
    } catch {
      alert('Erro ao iniciar checkout. Tente novamente.');
    }
  };

  return (
    <div className="min-h-screen font-sans antialiased" style={{ background: DARK.bg, color: DARK.text }}>
      {/* Ambient gradient blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden>
        <div
          className="absolute rounded-full blur-3xl opacity-20"
          style={{ width: 600, height: 600, top: -200, left: -200, background: `radial-gradient(circle, ${DARK.accent}, transparent 70%)` }}
        />
        <div
          className="absolute rounded-full blur-3xl opacity-10"
          style={{ width: 500, height: 500, top: 200, right: -150, background: `radial-gradient(circle, ${DARK.sky}, transparent 70%)` }}
        />
      </div>

      {/* Navbar */}
      <nav
        className="fixed top-0 inset-x-0 z-50"
        style={{ backdropFilter: 'blur(16px)', background: 'rgba(8,8,15,0.8)', borderBottom: `1px solid ${DARK.borderLight}` }}
      >
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}
            >
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-display text-lg text-white tracking-tight">MindDoc</span>
          </div>
          <div className="flex items-center gap-4">
            <a href="#precos" className="text-sm font-sans hidden sm:block transition-colors hover:text-white/90" style={{ color: DARK.textMuted }}>Preços</a>
            <a href="#faq" className="text-sm font-sans hidden sm:block transition-colors hover:text-white/90" style={{ color: DARK.textMuted }}>FAQ</a>
            <Link to="/resumir-pdf" className="text-sm font-sans hidden sm:block transition-colors hover:text-white/90" style={{ color: DARK.textMuted }}>Resumir PDF</Link>
            <button
              onClick={handleCTA}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-sans font-semibold transition-all duration-200 hover:opacity-90 active:scale-95"
              style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`, color: DARK.bg }}
            >
              {user ? 'Abrir app' : 'Entrar'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </nav>

      <HeroSection onCTA={handleCTA} isLoggedIn={!!user} />
      <HowItWorksSection />
      <UseCasesSection />
      <PricingSection onCTA={handleCTA} onSelectPlan={handleSelectPlan} />
      <TrustBarSection />
      <FAQSection />

      {/* Final CTA */}
      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <div
            className="rounded-3xl p-12 relative overflow-hidden"
            style={{ background: DARK.accentSubtle, border: `1px solid ${DARK.accentBorder}` }}
          >
            <div
              className="absolute inset-0 opacity-20"
              style={{ background: `radial-gradient(circle at 50% 100%, ${DARK.accent}, transparent 70%)` }}
            />
            <div className="relative space-y-6">
              <h2 className="font-display text-3xl sm:text-4xl text-white leading-tight">
                Pare de ler documentos inteiros.<br />
                <span style={{ color: DARK.accent }}>Comece a perguntar.</span>
              </h2>
              <p className="text-sm font-sans max-w-md mx-auto" style={{ color: DARK.textMuted }}>
                Experimente gratuitamente. Sem cartão de crédito. Login com Google em um clique.
              </p>
              <button
                onClick={handleCTA}
                className="inline-flex items-center gap-2 px-8 py-4 rounded-xl text-base font-sans font-semibold transition-all duration-200 hover:opacity-90 active:scale-95"
                style={{
                  background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
                  color: DARK.bg,
                  boxShadow: `0 0 60px ${DARK.accentGlow}`,
                }}
              >
                {user ? 'Ir para o app' : 'Começar gratuitamente'}
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 px-6" style={{ borderTop: `1px solid ${DARK.borderLight}` }}>
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div
              className="w-6 h-6 rounded-lg flex items-center justify-center"
              style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}
            >
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-display text-sm text-white">MindDoc</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/privacidade" className="text-xs font-sans transition-colors hover:text-white/50" style={{ color: 'rgba(255,255,255,0.25)' }}>
              Política de Privacidade
            </Link>
            <Link to="/termos" className="text-xs font-sans transition-colors hover:text-white/50" style={{ color: 'rgba(255,255,255,0.25)' }}>
              Termos de Serviço
            </Link>
            <p className="text-xs font-sans" style={{ color: 'rgba(255,255,255,0.25)' }}>
              © {new Date().getFullYear()} MindDoc.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
