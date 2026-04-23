import { useState } from 'react';
import { LogOut, ChevronDown, Settings } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth, Plan } from '../contexts/AuthContext';
import { DARK } from '../constants/theme';

const planStyle: Record<Plan, { bg: string; color: string; label: string }> = {
  free:  { bg: 'rgba(255,255,255,0.07)', color: 'rgba(255,255,255,0.5)', label: 'Free' },
  solo:  { bg: DARK.skySubtle,           color: '#38bdf8',               label: 'Solo' },
  pro:   { bg: DARK.accentSubtle,        color: '#fbbf24',               label: 'Pro' },
};

export function UserMenu() {
  const { user, profile, signOut } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const displayName = user?.user_metadata?.full_name || user?.email || '';
  const initial = displayName[0]?.toUpperCase() ?? '?';
  const plan: Plan = profile?.plan ?? 'free';
  const { bg, color, label } = planStyle[plan];

  const handleLogout = () => {
    setOpen(false);
    signOut();
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 rounded-full pl-1 pr-3 py-1 transition-all hover:opacity-80"
        style={{ background: 'rgba(255,255,255,0.07)', border: `1px solid ${DARK.border}` }}
      >
        <div
          className="w-7 h-7 rounded-full text-xs font-sans font-semibold flex items-center justify-center shrink-0"
          style={{ background: `linear-gradient(135deg, ${DARK.accent}, #d97706)`, color: DARK.bg }}
        >
          {initial}
        </div>
        <span className="text-sm font-sans font-medium hidden sm:block max-w-[140px] truncate" style={{ color: DARK.text }}>
          {displayName}
        </span>
        <span
          className="text-xs font-sans font-semibold px-2 py-0.5 rounded-full hidden sm:block"
          style={{ background: bg, color }}
        >
          {label}
        </span>
        <ChevronDown className="w-3.5 h-3.5" style={{ color: DARK.textFaint }} />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div
            className="absolute right-0 top-10 z-20 w-52 rounded-xl p-1"
            style={{ background: '#111122', border: `1px solid ${DARK.border}`, boxShadow: '0 8px 32px rgba(0,0,0,0.4)' }}
          >
            <div className="px-3 py-2 mb-1" style={{ borderBottom: `1px solid ${DARK.border}` }}>
              <p className="text-xs font-sans truncate" style={{ color: DARK.textFaint }}>{user?.email}</p>
              <span
                className="mt-1.5 inline-block text-xs font-sans font-semibold px-2 py-0.5 rounded-full"
                style={{ background: bg, color }}
              >
                Plano {label}
              </span>
            </div>
            <button
              onClick={() => { setOpen(false); navigate('/configuracoes'); }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm font-sans rounded-lg transition-colors hover:bg-white/5"
              style={{ color: DARK.textMuted }}
            >
              <Settings className="w-4 h-4" />
              Configurações
            </button>
            <div style={{ borderTop: `1px solid ${DARK.border}`, margin: '4px 0' }} />
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm font-sans rounded-lg transition-colors hover:bg-red-500/10"
              style={{ color: '#f87171' }}
            >
              <LogOut className="w-4 h-4" />
              Sair
            </button>
          </div>
        </>
      )}
    </div>
  );
}
