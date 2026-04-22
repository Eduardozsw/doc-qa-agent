import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, ArrowLeft, User, Mail, Lock, Check, Eye, EyeOff, Loader2, AlertCircle, CheckCircle2, Link2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../lib/supabase';
import { DARK } from '../constants/theme';

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg" className="flex-shrink-0">
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

function PasswordRequirements({ password, visible }: { password: string; visible: boolean }) {
  return (
    <div
      className="overflow-hidden transition-all duration-300 ease-in-out"
      style={{ maxHeight: visible ? '120px' : '0', opacity: visible ? 1 : 0 }}
    >
      <div className="pt-2 pb-1 space-y-1.5">
        {PASSWORD_RULES.map((rule) => {
          const met = rule.test(password);
          return (
            <div key={rule.label} className="flex items-center gap-2">
              <div
                className="flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center transition-all duration-300"
                style={{
                  background: met ? DARK.accent : 'rgba(255,255,255,0.06)',
                  border: met ? 'none' : `1px solid ${DARK.border}`,
                  transform: met ? 'scale(1)' : 'scale(0.9)',
                }}
              >
                <Check style={{ width: 9, height: 9, color: met ? DARK.bg : 'transparent', strokeWidth: 3 }} />
              </div>
              <span className="text-xs font-sans transition-colors duration-300"
                style={{ color: met ? 'rgba(255,255,255,0.7)' : DARK.textFaint }}>
                {rule.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

type FeedbackState = { type: 'success' | 'error'; message: string } | null;

function Feedback({ state }: { state: FeedbackState }) {
  if (!state) return null;
  const isSuccess = state.type === 'success';
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-sans"
      style={{
        background: isSuccess ? 'rgba(52,211,153,0.08)' : 'rgba(239,68,68,0.08)',
        border: `1px solid ${isSuccess ? 'rgba(52,211,153,0.2)' : 'rgba(239,68,68,0.2)'}`,
        color: isSuccess ? '#34d399' : '#f87171',
      }}>
      {isSuccess ? <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" /> : <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />}
      {state.message}
    </div>
  );
}

function SectionCard({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl p-6 space-y-4" style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}>
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: 'rgba(255,255,255,0.05)', border: `1px solid ${DARK.border}` }}>
          {icon}
        </div>
        <h2 className="text-sm font-sans font-semibold text-white">{title}</h2>
      </div>
      <div style={{ borderTop: `1px solid ${DARK.border}` }} />
      {children}
    </div>
  );
}

export function SettingsPage() {
  const { user, updateName, updateEmail, updatePassword } = useAuth();

  const inputStyle = {
    background: 'rgba(255,255,255,0.05)',
    border: `1px solid ${DARK.border}`,
    color: DARK.text,
    caretColor: DARK.accent,
  };
  const focusStyle = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.border = `1px solid ${DARK.accentBorder}`;
    e.target.style.boxShadow = `0 0 0 3px ${DARK.accentSubtle}`;
  };
  const blurStyle = (e: React.FocusEvent<HTMLInputElement>) => {
    e.target.style.border = `1px solid ${DARK.border}`;
    e.target.style.boxShadow = 'none';
  };

  // --- Nome ---
  const [name, setName] = useState(user?.user_metadata?.full_name ?? '');
  const [nameLoading, setNameLoading] = useState(false);
  const [nameFeedback, setNameFeedback] = useState<FeedbackState>(null);

  const handleSaveName = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setNameLoading(true);
    setNameFeedback(null);
    try {
      await updateName(name.trim());
      setNameFeedback({ type: 'success', message: 'Nome atualizado com sucesso.' });
    } catch (err) {
      setNameFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao atualizar nome.' });
    } finally {
      setNameLoading(false);
    }
  };

  // --- Email ---
  const [email, setEmail] = useState(user?.email ?? '');
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailFeedback, setEmailFeedback] = useState<FeedbackState>(null);

  const handleSaveEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (email === user?.email) return;
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailFeedback({ type: 'error', message: 'Informe um email válido.' });
      return;
    }
    setEmailLoading(true);
    setEmailFeedback(null);
    try {
      await updateEmail(email);
      setEmailFeedback({ type: 'success', message: 'Confirmação enviada para o novo email. Verifique sua caixa de entrada.' });
    } catch (err) {
      setEmailFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao atualizar email.' });
    } finally {
      setEmailLoading(false);
    }
  };

  // --- Contas vinculadas ---
  const hasGoogle = user?.identities?.some(i => i.provider === 'google') ?? false;
  const [linkLoading, setLinkLoading] = useState(false);
  const [linkFeedback, setLinkFeedback] = useState<FeedbackState>(null);

  const handleLinkGoogle = async () => {
    setLinkLoading(true);
    setLinkFeedback(null);
    try {
      const { error } = await supabase.auth.linkIdentity({
        provider: 'google',
        options: { redirectTo: `${window.location.origin}/configuracoes` },
      });
      if (error) throw new Error(error.message);
    } catch (err) {
      setLinkFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao vincular conta Google.' });
      setLinkLoading(false);
    }
  };

  // --- Senha ---
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordFeedback, setPasswordFeedback] = useState<FeedbackState>(null);

  const validatePassword = (p: string) => {
    if (p.length < 8) return 'A senha deve ter no mínimo 8 caracteres.';
    if (!/[A-Z]/.test(p)) return 'A senha deve conter ao menos uma letra maiúscula.';
    if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(p)) return 'A senha deve conter ao menos um caractere especial (ex: ! @ # $ % & *).';
    return '';
  };

  const handleSavePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    const err = validatePassword(newPassword);
    if (err) { setPasswordFeedback({ type: 'error', message: err }); return; }
    if (newPassword !== confirmPassword) { setPasswordFeedback({ type: 'error', message: 'As senhas não coincidem.' }); return; }
    setPasswordLoading(true);
    setPasswordFeedback(null);
    try {
      await updatePassword(newPassword);
      setPasswordFeedback({ type: 'success', message: 'Senha atualizada com sucesso.' });
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPasswordFeedback({ type: 'error', message: err instanceof Error ? err.message : 'Erro ao atualizar senha.' });
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div className="min-h-screen font-sans" style={{ background: DARK.bg }}>
      <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden>
        <div className="absolute rounded-full blur-3xl opacity-10"
          style={{ width: 500, height: 500, top: -150, left: -150, background: `radial-gradient(circle, ${DARK.accent}, transparent 70%)` }} />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-40"
        style={{ backdropFilter: 'blur(16px)', background: 'rgba(8,8,15,0.85)', borderBottom: `1px solid ${DARK.borderLight}` }}>
        <div className="max-w-2xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}>
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-display text-base text-white tracking-tight">DocAI</span>
          </div>
          <Link to="/app" className="flex items-center gap-1.5 text-sm font-sans transition-colors hover:text-white"
            style={{ color: DARK.textMuted }}>
            <ArrowLeft className="w-4 h-4" />
            Voltar
          </Link>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 sm:px-6 py-10 relative space-y-5">
        <div className="mb-2">
          <h1 className="font-display text-2xl text-white">Configurações</h1>
          <p className="text-sm font-sans mt-1" style={{ color: DARK.textMuted }}>Gerencie suas informações de conta.</p>
        </div>

        {/* Nome */}
        <SectionCard icon={<User className="w-4 h-4" style={{ color: DARK.textMuted }} />} title="Nome de exibição">
          <form onSubmit={handleSaveName} className="space-y-3">
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              onFocus={focusStyle}
              onBlur={blurStyle}
              placeholder="Seu nome"
              className="w-full px-4 py-2.5 rounded-xl text-sm font-sans outline-none transition-all duration-200"
              style={inputStyle}
            />
            <Feedback state={nameFeedback} />
            <div className="flex justify-end">
              <button type="submit" disabled={nameLoading || !name.trim()}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-sans font-medium text-white transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}>
                {nameLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Salvar
              </button>
            </div>
          </form>
        </SectionCard>

        {/* Email */}
        <SectionCard icon={<Mail className="w-4 h-4" style={{ color: DARK.textMuted }} />} title="Endereço de email">
          <form onSubmit={handleSaveEmail} className="space-y-3">
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onFocus={focusStyle}
              onBlur={blurStyle}
              placeholder="seu@email.com"
              className="w-full px-4 py-2.5 rounded-xl text-sm font-sans outline-none transition-all duration-200"
              style={inputStyle}
            />
            <p className="text-xs font-sans" style={{ color: DARK.textFaint }}>
              Um email de confirmação será enviado para o novo endereço antes da troca ser efetivada.
            </p>
            <Feedback state={emailFeedback} />
            <div className="flex justify-end">
              <button type="submit" disabled={emailLoading || email === user?.email || !email.trim()}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-sans font-medium text-white transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}>
                {emailLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Salvar
              </button>
            </div>
          </form>
        </SectionCard>

        {/* Contas vinculadas */}
        <SectionCard icon={<Link2 className="w-4 h-4" style={{ color: DARK.textMuted }} />} title="Contas vinculadas">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <GoogleIcon />
              <div>
                <p className="text-sm font-sans text-white">Google</p>
                <p className="text-xs font-sans" style={{ color: DARK.textFaint }}>
                  {hasGoogle ? 'Conta vinculada' : 'Não vinculado'}
                </p>
              </div>
            </div>
            {hasGoogle ? (
              <span
                className="flex items-center gap-1.5 text-xs font-sans font-medium px-2.5 py-1 rounded-full"
                style={{ background: DARK.emeraldSubtle, color: DARK.emerald, border: `1px solid ${DARK.emeraldBorder}` }}
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Vinculado
              </span>
            ) : (
              <button
                onClick={handleLinkGoogle}
                disabled={linkLoading}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-sans font-medium text-white transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}
              >
                {linkLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Vincular
              </button>
            )}
          </div>
          <Feedback state={linkFeedback} />
        </SectionCard>

        {/* Senha */}
        <SectionCard icon={<Lock className="w-4 h-4" style={{ color: DARK.textMuted }} />} title="Alterar senha">
          <form onSubmit={handleSavePassword} className="space-y-3">
            <div className="space-y-0">
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  onFocus={e => { focusStyle(e); setPasswordFocused(true); }}
                  onBlur={e => { blurStyle(e); setPasswordFocused(false); }}
                  placeholder="Nova senha"
                  className="w-full pl-4 pr-10 py-2.5 rounded-xl text-sm font-sans outline-none transition-all duration-200"
                  style={inputStyle}
                />
                <button type="button" onClick={() => setShowPassword(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors"
                  style={{ color: DARK.textFaint }}>
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <PasswordRequirements password={newPassword} visible={passwordFocused} />
            </div>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                onFocus={focusStyle}
                onBlur={blurStyle}
                placeholder="Confirmar nova senha"
                className="w-full px-4 py-2.5 rounded-xl text-sm font-sans outline-none transition-all duration-200"
                style={inputStyle}
              />
            </div>
            <Feedback state={passwordFeedback} />
            <div className="flex justify-end">
              <button type="submit" disabled={passwordLoading || !newPassword || !confirmPassword}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-sans font-medium text-white transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}>
                {passwordLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Atualizar senha
              </button>
            </div>
          </form>
        </SectionCard>
      </main>
    </div>
  );
}
