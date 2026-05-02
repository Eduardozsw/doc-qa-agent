import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, ArrowLeft, User, Mail, Lock, Check, Eye, EyeOff,
  Loader2, AlertCircle, CheckCircle2, Link2, CreditCard, Zap, Menu, X,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import { DARK } from '../constants/theme';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

type Section = 'perfil' | 'assinatura' | 'senha' | 'vinculadas';

const SECTION_ANIM = `
  @keyframes _sec-in {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0);    }
  }
`;

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0 }}>
      <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.716v2.259h2.908C16.658 14.215 17.64 11.907 17.64 9.2z" fill="#4285F4"/>
      <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
      <path d="M3.964 10.706A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.038l3.007-2.332z" fill="#FBBC05"/>
      <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.962L3.964 7.294C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
    </svg>
  );
}

const PASSWORD_RULES = [
  { label: 'Mínimo 8 caracteres',        test: (p: string) => p.length >= 8 },
  { label: 'Ao menos uma maiúscula',      test: (p: string) => /[A-Z]/.test(p) },
  { label: 'Ao menos um caractere especial', test: (p: string) => /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(p) },
];

type FeedbackState = { type: 'success' | 'error'; message: string } | null;

const PLAN_META: Record<string, { label: string; color: string; bg: string; border: string }> = {
  free:  { label: 'Grátis', color: 'rgba(255,255,255,0.5)',  bg: 'rgba(255,255,255,0.05)', border: 'rgba(255,255,255,0.1)' },
  solo:  { label: 'Solo',   color: DARK.accent,              bg: 'rgba(245,158,11,0.1)',   border: 'rgba(245,158,11,0.25)' },
  pro:   { label: 'Pro',    color: DARK.emerald,             bg: DARK.emeraldSubtle,       border: DARK.emeraldBorder },
};

function Feedback({ state }: { state: FeedbackState }) {
  if (!state) return null;
  const ok = state.type === 'success';
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '9px 12px', borderRadius: 8, fontSize: 12,
      background: ok ? 'rgba(52,211,153,0.07)' : 'rgba(239,68,68,0.07)',
      border: `1px solid ${ok ? 'rgba(52,211,153,0.18)' : 'rgba(239,68,68,0.18)'}`,
      color: ok ? '#34d399' : '#f87171',
    }}>
      {ok
        ? <CheckCircle2 style={{ width: 13, height: 13, flexShrink: 0 }} />
        : <AlertCircle  style={{ width: 13, height: 13, flexShrink: 0 }} />}
      {state.message}
    </div>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
      textTransform: 'uppercase' as const,
      color: 'rgba(255,255,255,0.3)', marginBottom: 7,
    }}>
      {children}
    </div>
  );
}

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      style={{
        width: '100%',
        background: 'rgba(255,255,255,0.03)',
        border: `1px solid ${DARK.border}`,
        borderRadius: 10,
        padding: '10px 14px',
        fontSize: 13,
        color: DARK.text,
        outline: 'none',
        boxSizing: 'border-box' as const,
        fontFamily: 'inherit',
        transition: 'border 0.15s, box-shadow 0.15s',
        ...props.style,
      }}
      onFocus={e => {
        e.target.style.border = `1px solid ${DARK.accentBorder}`;
        e.target.style.boxShadow = `0 0 0 3px rgba(245,158,11,0.07)`;
        props.onFocus?.(e);
      }}
      onBlur={e => {
        e.target.style.border = `1px solid ${DARK.border}`;
        e.target.style.boxShadow = 'none';
        props.onBlur?.(e);
      }}
    />
  );
}

function BtnPrimary({ children, disabled, loading, onClick, type = 'button', fullWidth }: {
  children: React.ReactNode; disabled?: boolean; loading?: boolean;
  onClick?: () => void; type?: 'button' | 'submit'; fullWidth?: boolean;
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      style={{
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
        padding: '10px 20px', borderRadius: 9, fontSize: 12, fontWeight: 600,
        background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
        color: DARK.bg, border: 'none',
        cursor: disabled || loading ? 'default' : 'pointer',
        opacity: disabled || loading ? 0.4 : 1,
        whiteSpace: 'nowrap' as const,
        width: fullWidth ? '100%' : undefined,
        transition: 'filter 0.15s, transform 0.1s',
        fontFamily: 'inherit',
      }}
      onMouseEnter={e => { if (!disabled && !loading) e.currentTarget.style.filter = 'brightness(1.1)'; }}
      onMouseLeave={e => { e.currentTarget.style.filter = 'brightness(1)'; }}
    >
      {loading && <Loader2 style={{ width: 13, height: 13, animation: 'spin 1s linear infinite' }} />}
      {children}
    </button>
  );
}

function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.025)',
      border: `1px solid ${DARK.border}`,
      borderRadius: 14,
      padding: '22px 24px',
      ...style,
    }}>
      {children}
    </div>
  );
}

function NavItem({ icon, label, active, onClick }: {
  icon: React.ReactNode; label: string; active: boolean; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 9,
        padding: '8px 10px', borderRadius: 8, cursor: 'pointer',
        fontSize: 13, fontWeight: active ? 600 : 400,
        color: active ? 'white' : 'rgba(255,255,255,0.4)',
        background: active ? 'rgba(245,158,11,0.08)' : 'transparent',
        border: 'none',
        borderLeft: `2px solid ${active ? DARK.accent : 'transparent'}`,
        marginLeft: -2, width: '100%', textAlign: 'left' as const,
        fontFamily: 'inherit',
        transition: 'all 0.15s',
      }}
      onMouseEnter={e => { if (!active) e.currentTarget.style.color = 'rgba(255,255,255,0.65)'; }}
      onMouseLeave={e => { if (!active) e.currentTarget.style.color = 'rgba(255,255,255,0.4)'; }}
    >
      {icon}
      {label}
    </button>
  );
}

function SectionHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <h2 style={{ fontSize: 20, fontWeight: 700, color: 'white', margin: '0 0 4px', letterSpacing: '-0.3px' }}>{title}</h2>
      <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', margin: 0 }}>{subtitle}</p>
    </div>
  );
}

function PasswordStrength({ password }: { password: string }) {
  const score = PASSWORD_RULES.filter(r => r.test(password)).length;
  const colors = ['transparent', '#f87171', DARK.accent, DARK.emerald];
  const labels = ['', 'Fraca', 'Média', 'Forte'];
  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ display: 'flex', gap: 4, marginBottom: 6 }}>
        {[0, 1, 2].map(i => (
          <div key={i} style={{
            flex: 1, height: 3, borderRadius: 99,
            background: i < score ? colors[score] : 'rgba(255,255,255,0.08)',
            transition: 'background 0.3s',
          }} />
        ))}
      </div>
      {password && (
        <span style={{ fontSize: 10, color: colors[score], fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' as const }}>
          {labels[score]}
        </span>
      )}
    </div>
  );
}

export function SettingsPage() {
  const navigate = useNavigate();
  const { user, session, profile, updateName, updateEmail, updatePassword } = useAuth();
  const plan = profile?.plan ?? 'free';
  const planMeta = PLAN_META[plan] ?? PLAN_META.free;
  const isPix = plan !== 'free' && !profile?.subscription_id;
  const daysRemaining = (() => {
    if (!isPix || !profile?.current_period_end) return null;
    const diff = new Date(profile.current_period_end).getTime() - Date.now();
    return Math.max(0, Math.ceil(diff / 86_400_000));
  })();
  const [activeSection, setActiveSection] = useState<Section>('perfil');
  const [navOpen, setNavOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(() => window.innerWidth < 768);

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 767px)');
    const handler = (e: MediaQueryListEvent) => {
      setIsMobile(e.matches);
      if (!e.matches) setNavOpen(false);
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  // Assinatura
  const [portalLoading, setPortalLoading] = useState(false);
  const [portalFeedback, setPortalFeedback] = useState<FeedbackState>(null);
  const handleManageSubscription = async () => {
    if (!session) return;
    setPortalLoading(true); setPortalFeedback(null);
    try {
      const res = await fetch(`${API_BASE}/api/billing/portal`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.status === 501) { setPortalFeedback({ type: 'error', message: 'Gerenciamento de assinatura em breve. Entre em contato pelo suporte.' }); return; }
      if (!res.ok) throw new Error();
      const data = await res.json();
      window.location.href = data.url;
    } catch { setPortalFeedback({ type: 'error', message: 'Erro ao abrir portal. Tente novamente.' }); }
    finally { setPortalLoading(false); }
  };

  // Nome
  const [name, setName] = useState(user?.user_metadata?.full_name ?? '');
  const [nameLoading, setNameLoading] = useState(false);
  const [nameFeedback, setNameFeedback] = useState<FeedbackState>(null);
  const handleSaveName = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setNameLoading(true); setNameFeedback(null);
    try { await updateName(name.trim()); setNameFeedback({ type: 'success', message: 'Nome atualizado.' }); }
    catch (err) { setNameFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao atualizar nome.' }); }
    finally { setNameLoading(false); }
  };

  // Email
  const [email, setEmail] = useState(user?.email ?? '');
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailFeedback, setEmailFeedback] = useState<FeedbackState>(null);
  const handleSaveEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (email === user?.email) return;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setEmailFeedback({ type: 'error', message: 'Informe um email válido.' }); return; }
    setEmailLoading(true); setEmailFeedback(null);
    try { await updateEmail(email); setEmailFeedback({ type: 'success', message: 'Confirmação enviada para o novo email.' }); }
    catch (err) { setEmailFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao atualizar email.' }); }
    finally { setEmailLoading(false); }
  };

  // Contas vinculadas
  const hasGoogle = user?.identities?.some(i => i.provider === 'google') ?? false;
  const [linkLoading, setLinkLoading] = useState(false);
  const [linkFeedback, setLinkFeedback] = useState<FeedbackState>(null);
  const handleLinkGoogle = async () => {
    setLinkLoading(true); setLinkFeedback(null);
    try {
      const { error } = await supabase.auth.linkIdentity({ provider: 'google', options: { redirectTo: `${window.location.origin}/configuracoes` } });
      if (error) throw new Error(error.message);
    } catch (err) {
      setLinkFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao vincular.' });
      setLinkLoading(false);
    }
  };

  const isOAuthOnly = !user?.identities?.some(i => i.provider === 'email');

  // Senha
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordFeedback, setPasswordFeedback] = useState<FeedbackState>(null);
  const validatePassword = (p: string) => {
    if (p.length < 8) return 'A senha deve ter no mínimo 8 caracteres.';
    if (!/[A-Z]/.test(p)) return 'A senha deve conter ao menos uma letra maiúscula.';
    if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(p)) return 'A senha deve conter ao menos um caractere especial.';
    return '';
  };
  const handleSavePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    const err = validatePassword(newPassword);
    if (err) { setPasswordFeedback({ type: 'error', message: err }); return; }
    if (newPassword !== confirmPassword) { setPasswordFeedback({ type: 'error', message: 'As senhas não coincidem.' }); return; }
    setPasswordLoading(true); setPasswordFeedback(null);
    try {
      await updatePassword(newPassword);
      setPasswordFeedback({ type: 'success', message: 'Senha atualizada com sucesso.' });
      setNewPassword(''); setConfirmPassword('');
    } catch (err) { setPasswordFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao atualizar senha.' }); }
    finally { setPasswordLoading(false); }
  };

  const displayName = user?.user_metadata?.full_name || user?.email || 'Usuário';
  const avatarInitial = displayName[0].toUpperCase();
  const iconStyle = { width: 14, height: 14, strokeWidth: 1.7 };

  const navGroups = [
    {
      label: 'Conta',
      items: [
        { id: 'perfil' as Section, icon: <User style={iconStyle} />, label: 'Perfil' },
        ...(plan !== 'free' ? [{ id: 'assinatura' as Section, icon: <CreditCard style={iconStyle} />, label: 'Assinatura' }] : []),
      ],
    },
    {
      label: 'Segurança',
      items: [
        { id: 'senha' as Section, icon: <Lock style={iconStyle} />, label: 'Senha' },
        { id: 'vinculadas' as Section, icon: <Link2 style={iconStyle} />, label: 'Contas vinculadas' },
      ],
    },
  ];

  return (
    <>
      <style>{SECTION_ANIM}</style>
      <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: DARK.bg, fontFamily: 'inherit' }}>

        {/* Header */}
        <header style={{
          height: 54, display: 'flex', alignItems: 'center', padding: '0 20px',
          borderBottom: `1px solid ${DARK.borderLight}`,
          background: 'rgba(8,8,15,0.96)', backdropFilter: 'blur(16px)',
          flexShrink: 0, zIndex: 10, gap: 14,
        }}>
          <button
            onClick={() => navigate('/app')}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              color: 'rgba(255,255,255,0.35)', fontSize: 13,
              background: 'none', border: 'none', cursor: 'pointer',
              fontFamily: 'inherit', transition: 'color 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.7)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.35)')}
          >
            <ArrowLeft style={{ width: 15, height: 15 }} />
            Voltar
          </button>
          <div style={{ width: 1, height: 14, background: 'rgba(255,255,255,0.08)' }} />
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{
                width: 26, height: 26, borderRadius: 7,
                background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Sparkles style={{ width: 13, height: 13, color: 'white' }} />
              </div>
              <span style={{ fontWeight: 600, fontSize: 14, color: 'white', letterSpacing: '-0.3px' }}>
                Configurações
              </span>
            </div>
            {isMobile && (
              <button
                onClick={() => setNavOpen(v => !v)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  background: navOpen ? 'rgba(245,158,11,0.12)' : 'rgba(255,255,255,0.06)',
                  border: `1px solid ${navOpen ? DARK.accentBorder : DARK.border}`,
                  borderRadius: 8, padding: '5px 10px', cursor: 'pointer',
                  color: navOpen ? DARK.accent : DARK.textMuted,
                  fontSize: 12, fontWeight: 500, transition: 'all 0.2s',
                }}
              >
                {navOpen ? <X style={{ width: 14, height: 14 }} /> : <Menu style={{ width: 14, height: 14 }} />}
                {navOpen ? 'Fechar' : 'Menu'}
              </button>
            )}
          </div>
        </header>

        <div style={{ display: 'flex', flex: 1, overflow: 'hidden', position: 'relative' }}>

          {/* Overlay mobile */}
          {isMobile && navOpen && (
            <div
              onClick={() => setNavOpen(false)}
              style={{
                position: 'fixed', inset: 0, top: 54,
                background: 'rgba(0,0,0,0.55)', zIndex: 40,
                backdropFilter: 'blur(2px)',
              }}
            />
          )}

          {/* Sidebar / Drawer */}
          <nav style={isMobile ? {
            position: 'fixed', left: 0, top: 54, bottom: 0,
            width: 260, zIndex: 50,
            borderRight: `1px solid ${DARK.border}`,
            background: '#0b0b18',
            padding: '20px 14px',
            display: 'flex', flexDirection: 'column', gap: 0,
            overflowY: 'auto',
            transform: navOpen ? 'translateX(0)' : 'translateX(-100%)',
            transition: 'transform 0.25s ease',
          } : {
            width: 220, flexShrink: 0,
            borderRight: `1px solid ${DARK.border}`,
            background: '#0b0b18',
            padding: '20px 14px',
            display: 'flex', flexDirection: 'column', gap: 0,
            overflowY: 'auto',
          }}>
            {/* User card */}
            <div style={{
              background: 'rgba(255,255,255,0.03)',
              border: `1px solid ${DARK.border}`,
              borderRadius: 12,
              padding: '14px 14px',
              marginBottom: 20,
              display: 'flex', alignItems: 'center', gap: 11,
            }}>
              {/* Avatar */}
              <div style={{
                width: 38, height: 38, borderRadius: 10, flexShrink: 0,
                background: `linear-gradient(135deg, ${DARK.accent} 0%, #d97706 100%)`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 16, fontWeight: 700, color: '#08080f',
                boxShadow: '0 4px 12px rgba(245,158,11,0.25)',
              }}>
                {avatarInitial}
              </div>
              <div style={{ minWidth: 0 }}>
                <p style={{
                  fontSize: 13, fontWeight: 600, color: 'rgba(255,255,255,0.88)',
                  margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  {user?.user_metadata?.full_name || 'Usuário'}
                </p>
                {/* Plan chip */}
                <span style={{
                  display: 'inline-block', marginTop: 5,
                  fontSize: 10, fontWeight: 700, letterSpacing: '0.07em',
                  textTransform: 'uppercase' as const,
                  padding: '2px 7px', borderRadius: 99,
                  background: planMeta.bg, color: planMeta.color,
                  border: `1px solid ${planMeta.border}`,
                }}>
                  {planMeta.label}
                </span>
              </div>
            </div>

            {/* Nav groups */}
            {navGroups.map(group => (
              <div key={group.label} style={{ marginBottom: 20 }}>
                <div style={{
                  fontSize: 10, fontWeight: 700, letterSpacing: '0.1em',
                  textTransform: 'uppercase' as const,
                  color: 'rgba(255,255,255,0.18)', padding: '0 10px', marginBottom: 6,
                }}>
                  {group.label}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {group.items.map(item => (
                    <NavItem
                      key={item.id}
                      icon={item.icon}
                      label={item.label}
                      active={activeSection === item.id}
                      onClick={() => { setActiveSection(item.id); setNavOpen(false); }}
                    />
                  ))}
                </div>
              </div>
            ))}
          </nav>

          {/* Content */}
          <div style={{ flex: 1, overflowY: 'auto', background: '#09091566' }}>
            <div
              key={activeSection}
              style={{
                padding: '40px 48px', maxWidth: 680,
                animation: '_sec-in 0.22s ease both',
              }}
            >

              {/* ─── Perfil ─── */}
              {activeSection === 'perfil' && (
                <div>
                  <SectionHeader title="Perfil" subtitle="Seu nome e email de acesso" />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

                    <Card>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 18 }}>
                        <User style={{ width: 13, height: 13, color: 'rgba(255,255,255,0.3)' }} />
                        <span style={{ fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.08em', textTransform: 'uppercase' as const }}>Nome de exibição</span>
                      </div>
                      <form onSubmit={handleSaveName} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                          <div style={{ flex: 1 }}>
                            <Input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Seu nome" maxLength={100} />
                          </div>
                          <BtnPrimary type="submit" loading={nameLoading} disabled={!name.trim()}>Salvar</BtnPrimary>
                        </div>
                        <Feedback state={nameFeedback} />
                      </form>
                    </Card>

                    <Card>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 18 }}>
                        <Mail style={{ width: 13, height: 13, color: 'rgba(255,255,255,0.3)' }} />
                        <span style={{ fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.3)', letterSpacing: '0.08em', textTransform: 'uppercase' as const }}>Email</span>
                      </div>
                      <form onSubmit={handleSaveEmail} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                          <div style={{ flex: 1 }}>
                            <Input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="seu@email.com" maxLength={254} />
                          </div>
                          <BtnPrimary type="submit" loading={emailLoading} disabled={email === user?.email || !email.trim()}>Salvar</BtnPrimary>
                        </div>
                        <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.22)', lineHeight: 1.5, margin: 0 }}>
                          Um email de confirmação será enviado antes da troca ser efetivada.
                        </p>
                        <Feedback state={emailFeedback} />
                      </form>
                    </Card>

                  </div>
                </div>
              )}

              {/* ─── Assinatura ─── */}
              {activeSection === 'assinatura' && (
                <div>
                  <SectionHeader title="Assinatura" subtitle="Plano atual e faturamento" />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

                    {/* Plan card */}
                    <div style={{
                      position: 'relative', overflow: 'hidden',
                      background: 'rgba(245,158,11,0.04)',
                      border: '1px solid rgba(245,158,11,0.14)',
                      borderRadius: 16, padding: '22px 24px',
                    }}>
                      {/* Glow top */}
                      <div style={{
                        position: 'absolute', top: 0, left: 0, right: 0, height: 1,
                        background: 'linear-gradient(90deg, transparent 10%, rgba(245,158,11,0.4) 50%, transparent 90%)',
                      }} />
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <div style={{
                            width: 40, height: 40, borderRadius: 10,
                            background: 'rgba(245,158,11,0.1)',
                            border: '1px solid rgba(245,158,11,0.2)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                          }}>
                            <Zap style={{ width: 18, height: 18, color: DARK.accent }} />
                          </div>
                          <div>
                            <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'white' }}>
                              Plano {PLAN_META[plan]?.label}
                            </p>
                            <p style={{ margin: '3px 0 0', fontSize: 11, color: 'rgba(255,255,255,0.35)' }}>
                              Gerencie sua assinatura
                            </p>
                          </div>
                        </div>
                        <span style={{
                          fontSize: 10, fontWeight: 700, padding: '3px 9px', borderRadius: 99,
                          background: 'rgba(52,211,153,0.1)', color: '#34d399',
                          border: '1px solid rgba(52,211,153,0.2)', letterSpacing: '0.06em',
                          textTransform: 'uppercase' as const,
                        }}>
                          Ativo
                        </span>
                      </div>
                      {isPix ? (
                        <div style={{
                          display: 'inline-flex', alignItems: 'center', gap: 8,
                          padding: '9px 14px', borderRadius: 8, fontSize: 12,
                          background: 'rgba(245,158,11,0.06)',
                          border: '1px solid rgba(245,158,11,0.18)',
                          color: 'rgba(255,255,255,0.55)',
                        }}>
                          <span style={{ fontWeight: 700, color: DARK.accent, fontSize: 14 }}>
                            {daysRemaining !== null ? daysRemaining : '—'}
                          </span>
                          {daysRemaining === 1 ? 'dia restante' : 'dias restantes'}
                        </div>
                      ) : (
                        <button
                          onClick={handleManageSubscription}
                          disabled={portalLoading}
                          style={{
                            display: 'inline-flex', alignItems: 'center', gap: 6,
                            padding: '9px 16px', borderRadius: 8, fontSize: 12, fontWeight: 500,
                            background: 'rgba(255,255,255,0.05)',
                            color: 'rgba(255,255,255,0.55)',
                            border: `1px solid ${DARK.border}`,
                            cursor: portalLoading ? 'default' : 'pointer',
                            opacity: portalLoading ? 0.5 : 1,
                            whiteSpace: 'nowrap' as const,
                            fontFamily: 'inherit',
                            transition: 'background 0.15s, color 0.15s',
                          }}
                          onMouseEnter={e => { if (!portalLoading) { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.color = 'rgba(255,255,255,0.8)'; } }}
                          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; e.currentTarget.style.color = 'rgba(255,255,255,0.55)'; }}
                        >
                          {portalLoading && <Loader2 style={{ width: 12, height: 12 }} />}
                          Gerenciar assinatura →
                        </button>
                      )}
                    </div>

                    <Feedback state={portalFeedback} />
                  </div>
                </div>
              )}

              {/* ─── Senha ─── */}
              {activeSection === 'senha' && (
                <div>
                  <SectionHeader
                    title={isOAuthOnly ? 'Definir senha' : 'Alterar senha'}
                    subtitle={isOAuthOnly ? 'Defina uma senha para entrar com email e senha.' : 'Atualize sua senha de acesso.'}
                  />
                  <Card style={{ maxWidth: 500 }}>
                    <form onSubmit={handleSavePassword} style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

                        <div>
                          <FieldLabel>Nova senha</FieldLabel>
                          <div style={{ position: 'relative' }}>
                            <Input
                              type={showPassword ? 'text' : 'password'}
                              value={newPassword}
                              onChange={e => setNewPassword(e.target.value)}
                              onFocus={() => setPasswordFocused(true)}
                              onBlur={() => setPasswordFocused(false)}
                              placeholder="••••••••"
                              maxLength={128}
                              style={{ paddingRight: 40 }}
                            />
                            <button
                              type="button"
                              onClick={() => setShowPassword(p => !p)}
                              style={{
                                position: 'absolute', right: 11, top: '50%', transform: 'translateY(-50%)',
                                background: 'none', border: 'none', cursor: 'pointer',
                                color: 'rgba(255,255,255,0.3)', display: 'flex', alignItems: 'center',
                              }}
                            >
                              {showPassword ? <EyeOff style={{ width: 14, height: 14 }} /> : <Eye style={{ width: 14, height: 14 }} />}
                            </button>
                          </div>

                          {/* Strength bar */}
                          {newPassword.length > 0 && <PasswordStrength password={newPassword} />}

                          {/* Rules */}
                          <div style={{
                            overflow: 'hidden',
                            maxHeight: passwordFocused && newPassword ? 90 : 0,
                            transition: 'max-height 0.3s ease',
                            marginTop: newPassword ? 10 : 0,
                          }}>
                            {PASSWORD_RULES.map(rule => {
                              const met = rule.test(newPassword);
                              return (
                                <div key={rule.label} style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 5 }}>
                                  <div style={{
                                    width: 14, height: 14, borderRadius: '50%', flexShrink: 0,
                                    background: met ? DARK.accent : 'rgba(255,255,255,0.05)',
                                    border: met ? 'none' : `1px solid ${DARK.border}`,
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    transition: 'background 0.2s',
                                  }}>
                                    <Check style={{ width: 7, height: 7, color: met ? DARK.bg : 'transparent', strokeWidth: 3.5 }} />
                                  </div>
                                  <span style={{ fontSize: 11, color: met ? 'rgba(255,255,255,0.6)' : 'rgba(255,255,255,0.25)', transition: 'color 0.2s' }}>
                                    {rule.label}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        <div>
                          <FieldLabel>Confirmar senha</FieldLabel>
                          <Input
                            type={showPassword ? 'text' : 'password'}
                            value={confirmPassword}
                            onChange={e => setConfirmPassword(e.target.value)}
                            placeholder="••••••••"
                            maxLength={128}
                          />
                          {confirmPassword && newPassword && (
                            <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                              {confirmPassword === newPassword
                                ? <><CheckCircle2 style={{ width: 12, height: 12, color: DARK.emerald }} /><span style={{ fontSize: 11, color: DARK.emerald }}>Senhas coincidem</span></>
                                : <><AlertCircle  style={{ width: 12, height: 12, color: '#f87171' }} /><span style={{ fontSize: 11, color: '#f87171' }}>Senhas não coincidem</span></>
                              }
                            </div>
                          )}
                        </div>
                      </div>

                      <Feedback state={passwordFeedback} />
                      <BtnPrimary type="submit" loading={passwordLoading} disabled={!newPassword || !confirmPassword}>
                        Atualizar senha
                      </BtnPrimary>
                    </form>
                  </Card>
                </div>
              )}

              {/* ─── Contas vinculadas ─── */}
              {activeSection === 'vinculadas' && (
                <div>
                  <SectionHeader title="Contas vinculadas" subtitle="Métodos de login associados à sua conta" />
                  <Card>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{
                          width: 38, height: 38, borderRadius: 9,
                          background: 'rgba(255,255,255,0.04)',
                          border: `1px solid ${DARK.border}`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                          <GoogleIcon />
                        </div>
                        <div>
                          <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)', fontWeight: 600, margin: 0 }}>Google</p>
                          <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.28)', marginTop: 2, marginBottom: 0 }}>
                            {hasGoogle ? 'Conta vinculada' : 'Não vinculado'}
                          </p>
                        </div>
                      </div>
                      {hasGoogle ? (
                        <span style={{
                          display: 'inline-flex', alignItems: 'center', gap: 5,
                          fontSize: 11, fontWeight: 600, padding: '4px 10px', borderRadius: 99,
                          background: 'rgba(52,211,153,0.08)',
                          border: '1px solid rgba(52,211,153,0.15)',
                          color: '#34d399',
                        }}>
                          <CheckCircle2 style={{ width: 12, height: 12 }} />
                          Vinculado
                        </span>
                      ) : (
                        <BtnPrimary loading={linkLoading} onClick={handleLinkGoogle}>Vincular</BtnPrimary>
                      )}
                    </div>
                    <Feedback state={linkFeedback} />
                  </Card>
                </div>
              )}

            </div>
          </div>
        </div>
      </div>
    </>
  );
}
