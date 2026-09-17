import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles, ArrowLeft, User, Lock,
  Loader2, AlertCircle, CheckCircle2, Menu, X,
} from 'lucide-react';
import { useAuth, Plan } from '../contexts/AuthContext';
import { DARK } from '../constants/theme';

type Section = 'perfil' | 'senha';

const SECTION_ANIM = `
  @keyframes _sec-in {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0);    }
  }
`;

type FeedbackState = { type: 'success' | 'error'; message: string } | null;

const PLAN_META: Record<Plan, { label: string; color: string; bg: string; border: string }> = {
  free:  { label: 'Grátis', color: 'rgba(255,255,255,0.5)',  bg: 'rgba(255,255,255,0.05)', border: 'rgba(255,255,255,0.1)' },
  solo:  { label: 'Solo',   color: '#38bdf8',                bg: DARK.skySubtle,           border: DARK.skyBorder },
  pro:   { label: 'Pro',    color: '#fbbf24',                bg: DARK.accentSubtle,        border: DARK.accentBorder },
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

export function SettingsPage() {
  const navigate = useNavigate();
  const { user, profile, updateName, updatePassword } = useAuth();
  const plan: Plan = profile?.plan ?? 'free';
  const planMeta = PLAN_META[plan];
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

  // Nome
  const [name, setName] = useState(user?.name ?? '');
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

  // Senha
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordFeedback, setPasswordFeedback] = useState<FeedbackState>(null);
  const handleSavePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordFeedback(null);
    if (newPassword.length < 8) { setPasswordFeedback({ type: 'error', message: 'A nova senha deve ter no mínimo 8 caracteres.' }); return; }
    if (newPassword !== confirmPassword) { setPasswordFeedback({ type: 'error', message: 'As senhas não coincidem.' }); return; }
    setPasswordLoading(true);
    try {
      await updatePassword(currentPassword, newPassword);
      setPasswordFeedback({ type: 'success', message: 'Senha atualizada.' });
      setCurrentPassword(''); setNewPassword(''); setConfirmPassword('');
    } catch (err) {
      setPasswordFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao atualizar senha.' });
    } finally { setPasswordLoading(false); }
  };

  const displayName = user?.name || user?.email || 'Usuário';
  const avatarInitial = displayName[0].toUpperCase();
  const iconStyle = { width: 14, height: 14, strokeWidth: 1.7 };

  const navGroups = [
    {
      label: 'Conta',
      items: [
        { id: 'perfil' as Section, icon: <User style={iconStyle} />, label: 'Perfil' },
      ],
    },
    {
      label: 'Segurança',
      items: [
        { id: 'senha' as Section, icon: <Lock style={iconStyle} />, label: 'Senha' },
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
                  {displayName}
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
                  <SectionHeader title="Perfil" subtitle="Seu nome de exibição" />
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
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', borderRadius: 10, background: 'rgba(255,255,255,0.03)', border: `1px solid ${DARK.border}` }}>
                        <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.55)' }}>{user?.email}</span>
                      </div>
                    </Card>

                  </div>
                </div>
              )}

              {/* ─── Senha ─── */}
              {activeSection === 'senha' && (
                <div>
                  <SectionHeader title="Senha" subtitle="Altere a senha usada para acessar sua conta" />
                  <Card style={{ maxWidth: 500 }}>
                    <form onSubmit={handleSavePassword} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      <div>
                        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' as const, color: 'rgba(255,255,255,0.3)', marginBottom: 7 }}>Senha atual</div>
                        <Input type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} placeholder="Senha atual" maxLength={128} required />
                      </div>
                      <div>
                        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' as const, color: 'rgba(255,255,255,0.3)', marginBottom: 7 }}>Nova senha</div>
                        <Input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} placeholder="Mínimo 8 caracteres" maxLength={128} required />
                      </div>
                      <div>
                        <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' as const, color: 'rgba(255,255,255,0.3)', marginBottom: 7 }}>Confirmar nova senha</div>
                        <Input type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder="Repita a nova senha" maxLength={128} required />
                      </div>
                      <Feedback state={passwordFeedback} />
                      <BtnPrimary type="submit" loading={passwordLoading} disabled={!currentPassword || !newPassword || !confirmPassword}>
                        Atualizar senha
                      </BtnPrimary>
                    </form>
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
