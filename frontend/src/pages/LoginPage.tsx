import { Sparkles } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

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
  const { signInWithGoogle } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-sky-50/30 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">

        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 bg-white border border-slate-200 rounded-full px-4 py-1.5 mb-5 shadow-sm">
            <Sparkles className="w-4 h-4 text-sky-500" />
            <span className="text-xs font-medium text-slate-500 tracking-wide uppercase">RAG Assistant</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Bem-vindo</h1>
          <p className="text-slate-500 mt-2 text-sm">
            Entre com sua conta para acessar o assistente de documentos.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
          <button
            onClick={signInWithGoogle}
            className="w-full flex items-center justify-center gap-3 px-4 py-3 border border-slate-200 rounded-xl text-sm font-medium text-slate-700 hover:bg-slate-50 hover:border-slate-300 active:scale-[0.98] transition-all duration-150"
          >
            <GoogleIcon />
            Entrar com Google
          </button>
        </div>

        <p className="text-center text-xs text-slate-400 mt-6">
          Ao entrar, você concorda com os termos de uso do serviço.
        </p>
      </div>
    </div>
  );
}
