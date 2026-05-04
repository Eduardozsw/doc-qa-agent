import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, ArrowLeft, User, Mail, Lock,
  Loader2, AlertCircle, CheckCircle2, Link2, CreditCard, Zap, Menu, X, Send,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import { DARK } from '../constants/theme';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

type Section = 'perfil' | 'assinatura' | 'senha' | 'vinculadas';

const PLAN_META: Record<string, { label: string; color: string; bg: string; border: string }> = {
  free: { label: 'Grátis', color: 'rgba(255,255,255,0.5)', bg: 'rgba(255,255,255,0.05)', border: 'rgba(255,255,255,0.1)' },
  solo: { label: 'Solo',   color: '#38bdf8',               bg: DARK.skySubtle,           border: DARK.skyBorder },
  pro:  { label: 'Pro',    color: '#fbbf24',               bg: DARK.accentSubtle,        border: DARK.accentBorder },
};

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

type FeedbackState = { type: 'success' | 'error'; message: string } | null;

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

function BtnPrimary({ children, disabled, loading, onClick, type = 'button' }: {
  children: React.ReactNode; disabled?: boolean; loading?: boolean;
  onClick?: () => void; type?: 'button' | 'submit';
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
        transition: 'filter 0.15s',
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

function NavItem({ icon, label, active, onClick }: {
  icon: React.ReactNode; label: string; active: boolean; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 9,
        padding: '8px 12px', borderRadius: 8, cursor: 'pointer',
        fontSize: 13, fontWeight: active ? 600 : 400,
        color: active ? 'white' : 'rgba(255,255,255,0.4)',
        background: active ? 'rgba(255,255,255,0.06)' : 'transparent',
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

function SettingRow({ title, description, children, last }: {
  title: string; description?: string; children: React.ReactNode; last?: boolean;
}) {
  return (
    <div style={{
      display: 'flex', gap: 40, padding: '28px 0', alignItems: 'flex-start',
      borderBottom: last ? 'none' : '1px dashed rgba(255,255,255,0.07)',
    }}>
      <div style={{ width: 200, flexShrink: 0 }}>
        <p style={{ fontSize: 14, fontWeight: 600, color: 'rgba(255,255,255,0.82)', margin: '0 0 4px' }}>{title}</p>
        {description && (
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', margin: 0, lineHeight: 1.55 }}>{description}</p>
        )}
      </div>
      <div style={{ flex: 1 }}>{children}</div>
    </div>
  );
}

export function SettingsPage() {
  const navigate = useNavigate();
  const { user, session, profile, updateName, updateEmail, requestPasswordReset } = useAuth();
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

  // Redefinição de senha por link
  const [resetLoading, setResetLoading] = useState(false);
  const [resetFeedback, setResetFeedback] = useState<FeedbackState>(null);
  const handleSendResetLink = async () => {
    if (!user?.email) return;
    setResetLoading(true); setResetFeedback(null);
    try {
      await requestPasswordReset(user.email);
      setResetFeedback({ type: 'success', message: 'Link enviado! Verifique seu email.' });
    } catch (err) {
      setResetFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao enviar link.' });
    } finally { setResetLoading(false); }
  };

  const displayName = user?.user_metadata?.full_name || user?.email || 'Usuário';
  const avatarInitial = displayName[0].toUpperCase();
  const avatarUrl: string | undefined = user?.user_metadata?.avatar_url || user?.user_metadata?.picture;
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

  const sectionMeta: Record<Section, { title: string; subtitle: string }> = {
    perfil:     { title: 'Perfil',            subtitle: 'Gerencie seu nome, email e foto de perfil' },
    assinatura: { title: 'Assinatura',        subtitle: 'Plano atual e faturamento' },
    senha:      { title: 'Redefinir senha',   subtitle: 'Enviaremos um link por email para você criar uma nova senha com segurança' },
    vinculadas: { title: 'Contas vinculadas', subtitle: 'Métodos de login associados à sua conta' },
  };

  const { title: sectionTitle, subtitle: sectionSubtitle } = sectionMeta[activeSection];

  const sidebarStyle: React.CSSProperties = isMobile ? {
    position: 'fixed', left: 0, top: 54, bottom: 0,
    width: 240, zIndex: 50,
    borderRight: `1px solid ${DARK.border}`,
    background: '#0b0b18',
    padding: '24px 14px',
    display: 'flex', flexDirection: 'column',
    overflowY: 'auto',
    transform: navOpen ? 'translateX(0)' : 'translateX(-100%)',
    transition: 'transform 0.25s ease',
  } : {
    width: 240, flexShrink: 0,
    borderRight: `1px solid ${DARK.border}`,
    background: '#0b0b18',
    padding: '24px 14px',
    display: 'flex', flexDirection: 'column',
    overflowY: 'auto',
  };

  return (
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

        {/* Sidebar */}
        <nav style={sidebarStyle}>
          <div style={{ flex: 1 }}>
            {navGroups.map(group => (
              <div key={group.label} style={{ marginBottom: 20 }}>
                <div style={{
                  fontSize: 10, fontWeight: 700, letterSpacing: '0.1em',
                  textTransform: 'uppercase' as const,
                  color: 'rgba(255,255,255,0.18)', padding: '0 12px', marginBottom: 4,
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
          </div>

          {/* User info */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            paddingTop: 16, marginTop: 8,
            borderTop: `1px solid ${DARK.border}`,
          }}>
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt={displayName}
                style={{ width: 34, height: 34, borderRadius: 8, objectFit: 'cover', flexShrink: 0, border: `1px solid ${DARK.border}` }}
              />
            ) : (
              <div style={{
                width: 34, height: 34, borderRadius: 8, flexShrink: 0,
                background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 14, fontWeight: 700, color: '#08080f',
              }}>
                {avatarInitial}
              </div>
            )}
            <div style={{ minWidth: 0 }}>
              <p style={{
                fontSize: 13, fontWeight: 600, color: 'rgba(255,255,255,0.82)',
                margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {user?.user_metadata?.full_name || 'Usuário'}
              </p>
              <span style={{
                display: 'inline-block', marginTop: 3,
                fontSize: 10, fontWeight: 700, letterSpacing: '0.06em',
                textTransform: 'uppercase' as const,
                padding: '1px 6px', borderRadius: 99,
                background: planMeta.bg, color: planMeta.color,
                border: `1px solid ${planMeta.border}`,
              }}>
                {planMeta.label}
              </span>
            </div>
          </div>
        </nav>

        {/* Content */}
        <div style={{ flex: 1, overflowY: 'auto', background: 'rgba(9,9,21,0.4)' }}>
          <div style={{ padding: '40px 56px', maxWidth: 760 }}>

            {/* Section header */}
            <div style={{ marginBottom: 8, paddingBottom: 24, borderBottom: `1px solid ${DARK.border}` }}>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: 'white', margin: '0 0 5px', letterSpacing: '-0.4px' }}>
                {sectionTitle}
              </h2>
              <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', margin: 0 }}>
                {sectionSubtitle}
              </p>
            </div>

            {/* ─── Perfil ─── */}
            {activeSection === 'perfil' && (
              <>
                <SettingRow title="Foto de perfil" description="Foto vinculada à sua conta">
                  {avatarUrl ? (
                    <img
                      src={avatarUrl}
                      alt={displayName}
                      style={{ width: 60, height: 60, borderRadius: 12, objectFit: 'cover', border: `1px solid ${DARK.border}`, display: 'block' }}
                    />
                  ) : (
                    <div style={{
                      width: 60, height: 60, borderRadius: 12,
                      background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 24, fontWeight: 700, color: '#08080f',
                    }}>
                      {avatarInitial}
                    </div>
                  )}
                </SettingRow>

                <SettingRow title="Nome de exibição" description="Seu nome visível no app">
                  <form onSubmit={handleSaveName} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ display: 'flex', gap: 10 }}>
                      <Input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Seu nome" maxLength={100} />
                      <BtnPrimary type="submit" loading={nameLoading} disabled={!name.trim()}>Salvar</BtnPrimary>
                    </div>
                    <Feedback state={nameFeedback} />
                  </form>
                </SettingRow>

                <SettingRow title="Email" description="Email de acesso à conta" last>
                  <form onSubmit={handleSaveEmail} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ display: 'flex', gap: 10 }}>
                      <Input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="seu@email.com" maxLength={254} />
                      <BtnPrimary type="submit" loading={emailLoading} disabled={email === user?.email || !email.trim()}>Salvar</BtnPrimary>
                    </div>
                    <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.22)', margin: 0, lineHeight: 1.5 }}>
                      Um email de confirmação será enviado antes da troca ser efetivada.
                    </p>
                    <Feedback state={emailFeedback} />
                  </form>
                </SettingRow>
              </>
            )}

            {/* ─── Assinatura ─── */}
            {activeSection === 'assinatura' && (
              <>
                <SettingRow title="Plano atual" description="Seu plano ativo" last={isPix}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                    <div style={{
                      width: 40, height: 40, borderRadius: 10, flexShrink: 0,
                      background: 'rgba(245,158,11,0.1)',
                      border: '1px solid rgba(245,158,11,0.2)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <Zap style={{ width: 18, height: 18, color: DARK.accent }} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <p style={{ margin: 0, fontSize: 15, fontWeight: 700, color: 'white' }}>
                        Plano {PLAN_META[plan]?.label}
                      </p>
                      {isPix && daysRemaining !== null && (
                        <p style={{ margin: '3px 0 0', fontSize: 11, color: 'rgba(255,255,255,0.35)' }}>
                          {daysRemaining} {daysRemaining === 1 ? 'dia restante' : 'dias restantes'}
                        </p>
                      )}
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
                </SettingRow>

                {!isPix && (
                  <SettingRow title="Faturamento" description="Gerencie ou cancele sua assinatura" last>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'flex-start' }}>
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
                          fontFamily: 'inherit',
                          transition: 'background 0.15s, color 0.15s',
                        }}
                        onMouseEnter={e => { if (!portalLoading) { e.currentTarget.style.background = 'rgba(255,255,255,0.08)'; e.currentTarget.style.color = 'rgba(255,255,255,0.8)'; } }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; e.currentTarget.style.color = 'rgba(255,255,255,0.55)'; }}
                      >
                        {portalLoading && <Loader2 style={{ width: 12, height: 12 }} />}
                        Gerenciar assinatura →
                      </button>
                      <Feedback state={portalFeedback} />
                    </div>
                  </SettingRow>
                )}
              </>
            )}

            {/* ─── Senha ─── */}
            {activeSection === 'senha' && (
              <SettingRow title="Link de redefinição" description="Enviado para o email da sua conta" last>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '10px 14px', borderRadius: 10,
                    background: 'rgba(255,255,255,0.03)', border: `1px solid ${DARK.border}`,
                  }}>
                    <Mail style={{ width: 13, height: 13, color: 'rgba(255,255,255,0.3)', flexShrink: 0 }} />
                    <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)' }}>{user?.email}</span>
                  </div>
                  <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.28)', margin: 0, lineHeight: 1.6 }}>
                    O link expira em 1 hora. Após clicar, você será direcionado a uma página segura para definir sua nova senha.
                  </p>
                  <Feedback state={resetFeedback} />
                  <BtnPrimary loading={resetLoading} onClick={handleSendResetLink} disabled={resetFeedback?.type === 'success'}>
                    <Send style={{ width: 12, height: 12 }} />
                    Enviar link de redefinição
                  </BtnPrimary>
                </div>
              </SettingRow>
            )}

            {/* ─── Contas vinculadas ─── */}
            {activeSection === 'vinculadas' && (
              <SettingRow
                title="Google"
                description={hasGoogle ? 'Login com Google ativo' : 'Vincule para entrar com sua conta Google'}
                last
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 38, height: 38, borderRadius: 9,
                      background: 'rgba(255,255,255,0.04)',
                      border: `1px solid ${DARK.border}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <GoogleIcon />
                    </div>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.8)', fontWeight: 600, margin: 0 }}>Google</p>
                      <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.28)', marginTop: 2, marginBottom: 0 }}>
                        {hasGoogle ? 'Conta vinculada' : 'Não vinculado'}
                      </p>
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
                </div>
              </SettingRow>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
