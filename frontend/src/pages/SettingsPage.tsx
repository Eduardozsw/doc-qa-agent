import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, ArrowLeft, User, Mail, Lock, Check, Eye, EyeOff,
  Loader2, AlertCircle, CheckCircle2, Link2, CreditCard,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import { DARK } from '../constants/theme';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

type Section = 'perfil' | 'assinatura' | 'senha' | 'vinculadas';

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
  { label: 'Mínimo 8 caracteres', test: (p: string) => p.length >= 8 },
  { label: 'Ao menos uma letra maiúscula', test: (p: string) => /[A-Z]/.test(p) },
  { label: 'Ao menos um caractere especial (ex: ! @ # $ % & *)', test: (p: string) => /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(p) },
];

type FeedbackState = { type: 'success' | 'error'; message: string } | null;

function Feedback({ state }: { state: FeedbackState }) {
  if (!state) return null;
  const ok = state.type === 'success';
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 8,
      padding: '8px 12px', borderRadius: 8, fontSize: 12,
      background: ok ? 'rgba(52,211,153,0.08)' : 'rgba(239,68,68,0.08)',
      border: `1px solid ${ok ? 'rgba(52,211,153,0.2)' : 'rgba(239,68,68,0.2)'}`,
      color: ok ? '#34d399' : '#f87171',
    }}>
      {ok ? <CheckCircle2 style={{ width: 14, height: 14, flexShrink: 0 }} /> : <AlertCircle style={{ width: 14, height: 14, flexShrink: 0 }} />}
      {state.message}
    </div>
  );
}

function SectionTitle({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <h2 style={{ fontSize: 22, fontWeight: 600, color: 'white', margin: 0 }}>{title}</h2>
      <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', marginTop: 4 }}>{subtitle}</p>
      <div style={{ height: 1, background: 'rgba(255,255,255,0.06)', marginTop: 20 }} />
    </div>
  );
}

function FieldLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' as const, color: 'rgba(255,255,255,0.35)', marginBottom: 7 }}>
      {children}
    </div>
  );
}

function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      style={{
        width: '100%', background: 'rgba(255,255,255,0.04)',
        border: `1px solid ${DARK.border}`, borderRadius: 10,
        padding: '10px 14px', fontSize: 13, color: DARK.text,
        outline: 'none', boxSizing: 'border-box' as const,
        fontFamily: 'inherit',
        ...props.style,
      }}
      onFocus={e => { e.target.style.border = `1px solid ${DARK.accentBorder}`; e.target.style.boxShadow = `0 0 0 3px rgba(245,158,11,0.06)`; props.onFocus?.(e); }}
      onBlur={e => { e.target.style.border = `1px solid ${DARK.border}`; e.target.style.boxShadow = 'none'; props.onBlur?.(e); }}
    />
  );
}

function BtnPrimary({ children, disabled, loading, onClick, type = 'button' }: {
  children: React.ReactNode; disabled?: boolean; loading?: boolean; onClick?: () => void; type?: 'button' | 'submit';
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '9px 18px', borderRadius: 8, fontSize: 12, fontWeight: 600,
        background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`,
        color: DARK.bg, border: 'none', cursor: disabled || loading ? 'default' : 'pointer',
        opacity: disabled || loading ? 0.4 : 1, whiteSpace: 'nowrap',
      }}
    >
      {loading && <Loader2 style={{ width: 13, height: 13 }} />}
      {children}
    </button>
  );
}

function NavItem({
  icon, label, active, onClick,
}: { icon: React.ReactNode; label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 9,
        padding: '8px 10px', borderRadius: 7, cursor: 'pointer',
        fontSize: 13, fontWeight: 500,
        color: active ? 'white' : 'rgba(255,255,255,0.45)',
        background: active ? 'rgba(255,255,255,0.06)' : 'transparent',
        border: 'none',
        borderLeft: `2px solid ${active ? DARK.accent : 'transparent'}`,
        marginLeft: -2, transition: 'all 0.15s', width: '100%', textAlign: 'left',
        fontFamily: 'inherit',
      }}
      onMouseEnter={e => { if (!active) { (e.currentTarget as HTMLButtonElement).style.background = 'rgba(255,255,255,0.04)'; (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.65)'; } }}
      onMouseLeave={e => { if (!active) { (e.currentTarget as HTMLButtonElement).style.background = 'transparent'; (e.currentTarget as HTMLButtonElement).style.color = 'rgba(255,255,255,0.45)'; } }}
    >
      {icon}
      {label}
    </button>
  );
}

const PLAN_LABEL: Record<string, string> = { free: 'Grátis', solo: 'Solo', pro: 'Pro' };

export function SettingsPage() {
  const navigate = useNavigate();
  const { user, session, profile, updateName, updateEmail, updatePassword } = useAuth();
  const plan = profile?.plan ?? 'free';
  const [activeSection, setActiveSection] = useState<Section>('perfil');

  // Assinatura
  const [portalLoading, setPortalLoading] = useState(false);
  const [portalFeedback, setPortalFeedback] = useState<FeedbackState>(null);
  const handleManageSubscription = async () => {
    if (!session) return;
    setPortalLoading(true);
    setPortalFeedback(null);
    try {
      const res = await fetch(`${API_BASE}/api/billing/portal`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${session.access_token}` },
      });
      if (res.status === 501) {
        setPortalFeedback({ type: 'error', message: 'Gerenciamento de assinatura em breve. Entre em contato pelo suporte.' });
        return;
      }
      if (!res.ok) throw new Error();
      const data = await res.json();
      window.location.href = data.url;
    } catch {
      setPortalFeedback({ type: 'error', message: 'Erro ao abrir portal. Tente novamente.' });
    } finally {
      setPortalLoading(false);
    }
  };

  // Nome
  const [name, setName] = useState(user?.user_metadata?.full_name ?? '');
  const [nameLoading, setNameLoading] = useState(false);
  const [nameFeedback, setNameFeedback] = useState<FeedbackState>(null);
  const handleSaveName = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setNameLoading(true); setNameFeedback(null);
    try {
      await updateName(name.trim());
      setNameFeedback({ type: 'success', message: 'Nome atualizado com sucesso.' });
    } catch (err) {
      setNameFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao atualizar nome.' });
    } finally { setNameLoading(false); }
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
    try {
      await updateEmail(email);
      setEmailFeedback({ type: 'success', message: 'Confirmação enviada para o novo email.' });
    } catch (err) {
      setEmailFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao atualizar email.' });
    } finally { setEmailLoading(false); }
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
      setLinkFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao vincular conta Google.' });
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
    } catch (err) {
      setPasswordFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao atualizar senha.' });
    } finally { setPasswordLoading(false); }
  };

  const iconStyle = { width: 14, height: 14, strokeWidth: 1.8, color: 'currentColor' };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: DARK.bg, fontFamily: 'inherit' }}>

      {/* Header */}
      <header style={{
        height: 56, display: 'flex', alignItems: 'center',
        padding: '0 20px', borderBottom: `1px solid ${DARK.borderLight}`,
        background: 'rgba(8,8,15,0.95)', backdropFilter: 'blur(16px)',
        flexShrink: 0, zIndex: 10, gap: 16,
      }}>
        <button
          onClick={() => navigate('/app')}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            color: 'rgba(255,255,255,0.4)', fontSize: 13, background: 'none',
            border: 'none', cursor: 'pointer', fontFamily: 'inherit',
            transition: 'color 0.15s',
          }}
          onMouseEnter={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.7)')}
          onMouseLeave={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.4)')}
        >
          <ArrowLeft style={{ width: 16, height: 16 }} />
          Voltar ao app
        </button>
        <div style={{ width: 1, height: 16, background: 'rgba(255,255,255,0.1)' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 26, height: 26, borderRadius: 7, background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Sparkles style={{ width: 13, height: 13, color: 'white' }} />
          </div>
          <span style={{ fontWeight: 600, fontSize: 14, color: 'white', letterSpacing: '-0.3px' }}>Configurações</span>
        </div>
      </header>

      {/* Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* Nav sidebar */}
        <nav style={{
          width: 200, flexShrink: 0,
          borderRight: `1px solid ${DARK.border}`,
          background: '#0d0d1a',
          padding: '20px 12px',
          display: 'flex', flexDirection: 'column', gap: 2,
          overflowY: 'auto',
        }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.2)', padding: '0 10px', marginBottom: 4 }}>
            Conta
          </div>
          <NavItem icon={<User style={iconStyle} />} label="Perfil" active={activeSection === 'perfil'} onClick={() => setActiveSection('perfil')} />
          {plan !== 'free' && (
            <NavItem icon={<CreditCard style={iconStyle} />} label="Assinatura" active={activeSection === 'assinatura'} onClick={() => setActiveSection('assinatura')} />
          )}

          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,0.2)', padding: '0 10px', marginTop: 16, marginBottom: 4 }}>
            Segurança
          </div>
          <NavItem icon={<Lock style={iconStyle} />} label="Senha" active={activeSection === 'senha'} onClick={() => setActiveSection('senha')} />
          <NavItem icon={<Link2 style={iconStyle} />} label="Contas vinculadas" active={activeSection === 'vinculadas'} onClick={() => setActiveSection('vinculadas')} />
        </nav>

        {/* Content */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <div style={{ padding: '36px 48px', maxWidth: 760 }}>

            {/* Perfil */}
            {activeSection === 'perfil' && (
              <div>
                <SectionTitle title="Perfil" subtitle="Suas informações de conta" />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
                  <form onSubmit={handleSaveName} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <FieldLabel>Nome de exibição</FieldLabel>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
                      <div style={{ flex: 1 }}>
                        <Input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Seu nome" maxLength={100} />
                      </div>
                      <BtnPrimary type="submit" loading={nameLoading} disabled={!name.trim()}>Salvar</BtnPrimary>
                    </div>
                    <Feedback state={nameFeedback} />
                  </form>

                  <form onSubmit={handleSaveEmail} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <FieldLabel>Email</FieldLabel>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
                      <div style={{ flex: 1 }}>
                        <Input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="seu@email.com" maxLength={254} />
                      </div>
                      <BtnPrimary type="submit" loading={emailLoading} disabled={email === user?.email || !email.trim()}>Salvar</BtnPrimary>
                    </div>
                    <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', lineHeight: 1.5 }}>Confirmação enviada antes da troca ser efetivada.</p>
                    <Feedback state={emailFeedback} />
                  </form>
                </div>
              </div>
            )}

            {/* Assinatura */}
            {activeSection === 'assinatura' && (
              <div>
                <SectionTitle title="Assinatura" subtitle="Plano atual e faturamento" />
                <div style={{
                  background: 'rgba(245,158,11,0.05)', border: '1px solid rgba(245,158,11,0.12)',
                  borderRadius: 12, padding: '18px 22px',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  marginBottom: 16,
                }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontSize: 14, fontWeight: 600, color: 'white' }}>Plano {PLAN_LABEL[plan]}</span>
                      <span style={{
                        fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 99,
                        background: 'rgba(52,211,153,0.1)', color: '#34d399', border: '1px solid rgba(52,211,153,0.2)',
                      }}>ATIVO</span>
                    </div>
                    <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)' }}>Gerencie sua assinatura, troque o cartão ou cancele.</p>
                  </div>
                  <button
                    onClick={handleManageSubscription}
                    disabled={portalLoading}
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 6,
                      padding: '9px 18px', borderRadius: 8, fontSize: 12, fontWeight: 500,
                      background: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.6)',
                      border: `1px solid ${DARK.border}`, cursor: portalLoading ? 'default' : 'pointer',
                      opacity: portalLoading ? 0.5 : 1, whiteSpace: 'nowrap', fontFamily: 'inherit',
                    }}
                  >
                    {portalLoading && <Loader2 style={{ width: 13, height: 13 }} />}
                    Gerenciar assinatura →
                  </button>
                </div>
                <Feedback state={portalFeedback} />
              </div>
            )}

            {/* Senha */}
            {activeSection === 'senha' && (
              <div>
                <SectionTitle title={isOAuthOnly ? 'Definir senha' : 'Alterar senha'} subtitle={isOAuthOnly ? 'Defina uma senha para entrar também com email e senha.' : 'Altere sua senha de acesso.'} />
                <form onSubmit={handleSavePassword} style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 480 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
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
                            position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                            background: 'none', border: 'none', cursor: 'pointer', color: 'rgba(255,255,255,0.3)',
                          }}
                        >
                          {showPassword ? <EyeOff style={{ width: 14, height: 14 }} /> : <Eye style={{ width: 14, height: 14 }} />}
                        </button>
                      </div>
                      {/* Password requirements */}
                      <div style={{ overflow: 'hidden', maxHeight: passwordFocused && newPassword ? 100 : 0, transition: 'max-height 0.3s', marginTop: 8 }}>
                        {PASSWORD_RULES.map(rule => {
                          const met = rule.test(newPassword);
                          return (
                            <div key={rule.label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                              <div style={{
                                width: 14, height: 14, borderRadius: '50%', flexShrink: 0,
                                background: met ? DARK.accent : 'rgba(255,255,255,0.06)',
                                border: met ? 'none' : `1px solid ${DARK.border}`,
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                              }}>
                                <Check style={{ width: 8, height: 8, color: met ? DARK.bg : 'transparent', strokeWidth: 3 }} />
                              </div>
                              <span style={{ fontSize: 11, color: met ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.3)' }}>{rule.label}</span>
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
                    </div>
                  </div>
                  <Feedback state={passwordFeedback} />
                  <div>
                    <BtnPrimary type="submit" loading={passwordLoading} disabled={!newPassword || !confirmPassword}>
                      Atualizar senha
                    </BtnPrimary>
                  </div>
                </form>
              </div>
            )}

            {/* Contas vinculadas */}
            {activeSection === 'vinculadas' && (
              <div>
                <SectionTitle title="Contas vinculadas" subtitle="Métodos de login associados à conta" />
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 0', borderBottom: `1px solid ${DARK.borderLight}` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{
                      width: 34, height: 34, borderRadius: 8,
                      background: 'rgba(255,255,255,0.04)', border: `1px solid ${DARK.border}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <GoogleIcon />
                    </div>
                    <div>
                      <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.75)', fontWeight: 500 }}>Google</p>
                      <p style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)', marginTop: 1 }}>{hasGoogle ? 'Conta vinculada' : 'Não vinculado'}</p>
                    </div>
                  </div>
                  {hasGoogle ? (
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: 5,
                      fontSize: 11, fontWeight: 500, padding: '4px 10px', borderRadius: 99,
                      background: 'rgba(52,211,153,0.08)', border: '1px solid rgba(52,211,153,0.15)',
                      color: '#34d399',
                    }}>
                      <CheckCircle2 style={{ width: 13, height: 13 }} />
                      Vinculado
                    </span>
                  ) : (
                    <BtnPrimary loading={linkLoading} onClick={handleLinkGoogle}>Vincular</BtnPrimary>
                  )}
                </div>
                <Feedback state={linkFeedback} />
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
