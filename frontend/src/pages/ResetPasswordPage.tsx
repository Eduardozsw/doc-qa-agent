import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Lock, Eye, EyeOff, Loader2, Check } from 'lucide-react';
import { supabase } from '../lib/supabase';
import { DARK } from '../constants/theme';

const PASSWORD_RULES = [
  { label: 'Mínimo 8 caracteres',             test: (p: string) => p.length >= 8 },
  { label: 'Ao menos uma letra maiúscula',     test: (p: string) => /[A-Z]/.test(p) },
  { label: 'Ao menos um caractere especial',   test: (p: string) => /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(p) },
];

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const [ready, setReady] = useState(false);
  const [invalid, setInvalid] = useState(false);
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) { setReady(true); return; }
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'PASSWORD_RECOVERY' && session) {
        setReady(true);
      }
    });

    const timeout = setTimeout(() => {
      if (!ready) setInvalid(true);
    }, 3000);

    return () => { subscription.unsubscribe(); clearTimeout(timeout); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const validate = (p: string) => {
    if (p.length < 8) return 'A senha deve ter no mínimo 8 caracteres.';
    if (!/[A-Z]/.test(p)) return 'A senha deve conter ao menos uma letra maiúscula.';
    if (!/[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?]/.test(p)) return 'A senha deve conter ao menos um caractere especial.';
    return '';
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const err = validate(password);
    if (err) { setError(err); return; }
    if (password !== confirm) { setError('As senhas não coincidem.'); return; }
    setError('');
    setLoading(true);
    try {
      const { error } = await supabase.auth.updateUser({ password });
      if (error) throw new Error(error.message);
      setSuccess(true);
      setTimeout(() => navigate('/app'), 2000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erro ao atualizar senha.');
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

  const score = PASSWORD_RULES.filter(r => r.test(password)).length;
  const strengthColors = ['transparent', '#f87171', DARK.accent, DARK.emerald];

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: DARK.bg }}>
      <div className="fixed inset-0 overflow-hidden pointer-events-none" aria-hidden>
        <div className="absolute rounded-full blur-3xl opacity-10"
          style={{ width: 500, height: 500, top: -150, left: -150, background: `radial-gradient(circle, ${DARK.accent}, transparent 70%)` }} />
        <div className="absolute rounded-full blur-3xl opacity-5"
          style={{ width: 400, height: 400, bottom: -100, right: -100, background: `radial-gradient(circle, ${DARK.sky}, transparent 70%)` }} />
      </div>

      <div className="w-full max-w-sm relative">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)` }}>
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-display text-lg text-white tracking-tight">MindDoc</span>
          </div>
          <h1 className="text-2xl font-display text-white">Nova senha</h1>
          <p className="mt-2 text-sm font-sans" style={{ color: DARK.textMuted }}>
            {success ? 'Senha atualizada! Redirecionando…' : 'Escolha uma senha forte para sua conta.'}
          </p>
        </div>

        <div className="rounded-2xl p-6" style={{ background: DARK.card, border: `1px solid ${DARK.border}` }}>
          {/* Loading state */}
          {!ready && !invalid && (
            <div className="flex flex-col items-center gap-3 py-4">
              <Loader2 className="w-5 h-5 animate-spin" style={{ color: DARK.accent }} />
              <p className="text-xs font-sans" style={{ color: DARK.textMuted }}>Verificando link…</p>
            </div>
          )}

          {/* Invalid link */}
          {invalid && !ready && (
            <div className="text-center space-y-4 py-2">
              <p className="text-sm font-sans" style={{ color: '#f87171' }}>
                Link inválido ou expirado.
              </p>
              <button
                onClick={() => navigate('/login')}
                className="text-xs font-sans underline underline-offset-2 transition-colors hover:text-amber-400"
                style={{ color: DARK.accent, background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Solicitar novo link
              </button>
            </div>
          )}

          {/* Success */}
          {success && (
            <div className="flex flex-col items-center gap-3 py-4">
              <div className="w-10 h-10 rounded-full flex items-center justify-center"
                style={{ background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.2)' }}>
                <Check className="w-5 h-5" style={{ color: DARK.emerald }} />
              </div>
              <p className="text-sm font-sans text-center" style={{ color: '#34d399' }}>
                Senha atualizada com sucesso!
              </p>
            </div>
          )}

          {/* Form */}
          {ready && !success && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-0">
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: DARK.textFaint }} />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Nova senha"
                    maxLength={128}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    onFocus={e => { focusStyle(e); setPasswordFocused(true); }}
                    onBlur={e => { blurStyle(e); setPasswordFocused(false); }}
                    required
                    className="w-full pl-10 pr-10 py-2.5 rounded-xl text-sm font-sans outline-none transition-all duration-200"
                    style={inputStyle}
                  />
                  <button type="button" onClick={() => setShowPassword(p => !p)}
                    className="absolute right-3 top-1/2 -translate-y-1/2"
                    style={{ color: DARK.textFaint, background: 'none', border: 'none', cursor: 'pointer' }}>
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>

                {/* Strength bar */}
                {password.length > 0 && (
                  <div className="pt-2">
                    <div className="flex gap-1 mb-1.5">
                      {[0, 1, 2].map(i => (
                        <div key={i} style={{
                          flex: 1, height: 3, borderRadius: 99,
                          background: i < score ? strengthColors[score] : 'rgba(255,255,255,0.08)',
                          transition: 'background 0.3s',
                        }} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Rules */}
                <div style={{
                  overflow: 'hidden',
                  maxHeight: passwordFocused && password ? 90 : 0,
                  transition: 'max-height 0.3s ease',
                  marginTop: password ? 8 : 0,
                }}>
                  {PASSWORD_RULES.map(rule => {
                    const met = rule.test(password);
                    return (
                      <div key={rule.label} className="flex items-center gap-2 mb-1.5">
                        <div style={{
                          width: 14, height: 14, borderRadius: '50%', flexShrink: 0,
                          background: met ? DARK.accent : 'rgba(255,255,255,0.05)',
                          border: met ? 'none' : `1px solid ${DARK.border}`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          transition: 'background 0.2s',
                        }}>
                          <Check style={{ width: 7, height: 7, color: met ? DARK.bg : 'transparent', strokeWidth: 3.5 }} />
                        </div>
                        <span className="text-xs font-sans" style={{ color: met ? 'rgba(255,255,255,0.6)' : 'rgba(255,255,255,0.25)' }}>
                          {rule.label}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none" style={{ color: DARK.textFaint }} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Confirmar nova senha"
                  maxLength={128}
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                  onFocus={focusStyle}
                  onBlur={blurStyle}
                  required
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm font-sans outline-none transition-all duration-200"
                  style={inputStyle}
                />
              </div>

              {error && (
                <p className="text-xs font-sans px-3 py-2 rounded-lg"
                  style={{ background: 'rgba(239,68,68,0.08)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)' }}>
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 rounded-xl text-sm font-sans font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`, color: DARK.bg }}
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Salvar nova senha
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
