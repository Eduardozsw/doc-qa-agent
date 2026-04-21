import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, Mail, Lock, Eye, EyeOff, Loader2, Check } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { DARK } from '../constants/theme';

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
                <Check
                  className="transition-all duration-300"
                  style={{
                    width: 9,
                    height: 9,
                    color: met ? DARK.bg : 'transparent',
                    strokeWidth: 3,
                  }}
                />
              </div>
              <span
                className="text-xs font-sans transition-colors duration-300"
                style={{ color: met ? 'rgba(255,255,255,0.7)' : DARK.textFaint }}
              >
                {rule.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

type Mode = 'login' | 'register';

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
      <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.716v2.259h2.908C16.658 14.215 17.64 11.907 17.64 9.2z" fill="#4285F4"/>
      <path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/>
      <path d="M3.964 10.706A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.038l3.007-2.332z" fill="#FBBC05"/>
      <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.962L3.964 7.294C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/>
    </svg>
  );
}

export function LoginPage() {
  const { signInWithGoogle, signInWithEmail, signUp } = useAuth();

  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [confirmPassword, setConfirmPassword] = useState('');
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const switchMode = (next: Mode) => {
    setMode(next);
    setError('');
    setPassword('');
    setConfirmPassword('');
    setConsent(false);
  };

  const validateEmail = (value: string) => {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value))
      return 'Informe um email válido.';
    return '';
  };

  const validatePassword = (value: string) => {
    if (value.length < 8) return 'A senha deve ter no mínimo 8 caracteres.';
    if (!/[A-Z]/.test(value)) return 'A senha deve conter ao menos uma letra maiúscula.';
    if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(value))
      return 'A senha deve conter ao menos um caractere especial (ex: ! @ # $ % & *).';
    return '';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const emailErr = validateEmail(email);
    if (emailErr) { setError(emailErr); return; }

    if (mode === 'register') {
      const passwordErr = validatePassword(password);
      if (passwordErr) { setError(passwordErr); return; }
      if (password !== confirmPassword) { setError('As senhas não coincidem.'); return; }
      if (!consent) { setError('Você precisa aceitar a política de privacidade.'); return; }
    }

    setLoading(true);
    try {
      if (mode === 'login') {
        await signInWithEmail(email, password);
      } else {
        await signUp(email, password);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Ocorreu um erro.');
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: DARK.bg }}>
      {/* Ambient blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden>
        <div className="absolute rounded-full blur-3xl opacity-10"
          style={{ width: 500, height: 500, top: -150, left: -150, background: `radial-gradient(circle, ${DARK.accent}, transparent 70%)` }} />
        <div className="absolute rounded-full blur-3xl opacity-5"
          style={{ width: 400, height: 400, bottom: -100, right: -100, background: `radial-gradient(circle, ${DARK.sky}, transparent 70%)` }} />
      </div>

      <div className="w-full max-w-sm relative">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}>
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-display text-lg text-white tracking-tight">DocAI</span>
          </div>
          <h1 className="text-2xl font-display text-white">
            {mode === 'login' ? 'Bem-vindo de volta' : 'Criar conta'}
          </h1>
          <p className="mt-2 text-sm font-sans" style={{ color: DARK.textMuted }}>
            {mode === 'login'
              ? 'Entre para acessar seus documentos.'
              : 'Comece a perguntar aos seus documentos.'}
          </p>
        </div>

        {/* Card */}
        <div className="rounded-2xl p-6 space-y-5" style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}>

          {/* Tabs */}
          <div className="flex rounded-xl p-1 gap-1" style={{ background: 'rgba(255,255,255,0.04)' }}>
            {(['login', 'register'] as Mode[]).map((m) => (
              <button
                key={m}
                onClick={() => switchMode(m)}
                className="flex-1 py-2 text-sm font-sans font-medium rounded-lg transition-all duration-200"
                style={{
                  background: mode === m ? DARK.accentSubtle : 'transparent',
                  color: mode === m ? DARK.accent : DARK.textMuted,
                  border: mode === m ? `1px solid ${DARK.accentBorder}` : '1px solid transparent',
                }}
              >
                {m === 'login' ? 'Entrar' : 'Criar conta'}
              </button>
            ))}
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-3">
            {/* Email */}
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: DARK.textFaint }} />
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                onFocus={focusStyle}
                onBlur={blurStyle}
                required
                className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm font-sans outline-none transition-all duration-200"
                style={inputStyle}
              />
            </div>

            {/* Password + requirements (agrupados para não criar gap extra no space-y-3) */}
            <div className="space-y-0">
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: DARK.textFaint }} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Senha"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  onFocus={e => { focusStyle(e); if (mode === 'register') setPasswordFocused(true); }}
                  onBlur={e => { blurStyle(e); setPasswordFocused(false); }}
                  required
                  className="w-full pl-10 pr-10 py-2.5 rounded-xl text-sm font-sans outline-none transition-all duration-200"
                  style={inputStyle}
                />
                <button type="button" onClick={() => setShowPassword(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors"
                  style={{ color: DARK.textFaint }}>
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {mode === 'register' && (
                <PasswordRequirements password={password} visible={passwordFocused} />
              )}
            </div>

            {/* Confirm password */}
            {mode === 'register' && (
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: DARK.textFaint }} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Confirmar senha"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  onFocus={focusStyle}
                  onBlur={blurStyle}
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm font-sans outline-none transition-all duration-200"
                  style={inputStyle}
                />
              </div>
            )}

            {/* Consent */}
            {mode === 'register' && (
              <label className="flex items-start gap-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={e => setConsent(e.target.checked)}
                  className="mt-0.5 accent-amber-500"
                />
                <span className="text-xs font-sans leading-relaxed" style={{ color: DARK.textMuted }}>
                  Li e concordo com a{' '}
                  <Link to="/privacidade" target="_blank"
                    className="underline underline-offset-2 transition-colors hover:text-amber-400"
                    style={{ color: DARK.accent }}>
                    Política de Privacidade
                  </Link>
                </span>
              </label>
            )}

            {/* Error */}
            {error && (
              <p className="text-xs font-sans px-3 py-2 rounded-lg"
                style={{ background: 'rgba(239,68,68,0.08)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)' }}>
                {error}
              </p>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl text-sm font-sans font-medium text-white transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {mode === 'login' ? 'Entrar' : 'Criar conta'}
            </button>
          </form>

          {/* Divider */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px" style={{ background: DARK.border }} />
            <span className="text-xs font-sans" style={{ color: DARK.textFaint }}>ou</span>
            <div className="flex-1 h-px" style={{ background: DARK.border }} />
          </div>

          {/* Google */}
          <button
            onClick={signInWithGoogle}
            className="w-full flex items-center justify-center gap-3 py-2.5 rounded-xl text-sm font-sans font-medium transition-all duration-200 hover:opacity-80"
            style={{ background: 'rgba(255,255,255,0.06)', border: `1px solid ${DARK.border}`, color: DARK.text }}
          >
            <GoogleIcon />
            Continuar com Google
          </button>
        </div>

        <p className="text-center text-xs font-sans mt-5" style={{ color: DARK.textFaint }}>
          Ao criar uma conta, você concorda com nossa{' '}
          <Link to="/privacidade" className="underline underline-offset-2 hover:text-amber-400 transition-colors" style={{ color: DARK.textMuted }}>
            Política de Privacidade
          </Link>
        </p>
      </div>
    </div>
  );
}
