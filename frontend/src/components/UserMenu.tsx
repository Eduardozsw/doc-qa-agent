import { useState } from 'react';
import { LogOut, ChevronDown } from 'lucide-react';
import { useAuth, Plan } from '../contexts/AuthContext';

const planStyle: Record<Plan, string> = {
  free: 'bg-slate-100 text-slate-600',
  basic: 'bg-sky-100 text-sky-700',
  premium: 'bg-amber-100 text-amber-700',
};

export function UserMenu() {
  const { user, profile, signOut } = useAuth();
  const [open, setOpen] = useState(false);

  const displayName = user?.user_metadata?.full_name || user?.email || '';
  const initial = displayName[0]?.toUpperCase() ?? '?';
  const plan: Plan = profile?.plan ?? 'free';

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 bg-white border border-slate-200 rounded-full pl-1 pr-3 py-1 shadow-sm hover:border-slate-300 transition-all"
      >
        <div className="w-7 h-7 rounded-full bg-sky-500 text-white text-xs font-semibold flex items-center justify-center shrink-0">
          {initial}
        </div>
        <span className="text-sm text-slate-700 font-medium hidden sm:block max-w-[140px] truncate">
          {displayName}
        </span>
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full hidden sm:block ${planStyle[plan]}`}>
          {plan}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-10 z-20 w-52 bg-white border border-slate-100 rounded-xl shadow-lg p-1">
            <div className="px-3 py-2 border-b border-slate-100 mb-1">
              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
              <span className={`mt-1 inline-block text-xs font-semibold px-2 py-0.5 rounded-full ${planStyle[plan]}`}>
                Plano {plan}
              </span>
            </div>
            <button
              onClick={() => { setOpen(false); signOut(); }}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
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
