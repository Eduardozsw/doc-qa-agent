import { useEffect } from 'react';
import { FileText, Lock, X } from 'lucide-react';
import { DARK } from '../constants/theme';

interface PlanLimitModalProps {
  warning: string;
  onClose: () => void;
  onUpgrade: () => void;
}

const STYLES = `
  @keyframes _modal-backdrop { from { opacity: 0 } to { opacity: 1 } }
  @keyframes _modal-card {
    from { opacity: 0; transform: translateY(16px) scale(0.95); }
    to   { opacity: 1; transform: translateY(0)   scale(1);    }
  }
  @keyframes _slot-in {
    from { opacity: 0; transform: scale(0.75) translateY(6px); }
    to   { opacity: 1; transform: scale(1)    translateY(0);   }
  }
  @keyframes _locked-bob {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-3px); }
  }
  @keyframes _btn-glow {
    0%, 100% { box-shadow: 0 0 18px rgba(245,158,11,0.35), 0 4px 14px rgba(0,0,0,0.4); }
    50%       { box-shadow: 0 0 32px rgba(245,158,11,0.55), 0 4px 20px rgba(0,0,0,0.5); }
  }
`;

function BoldPlans({ text }: { text: string }) {
  const parts = text.split(/(plano free|plano Solo|plano Pro)/gi);
  return (
    <>
      {parts.map((part, i) =>
        /plano (free|solo|pro)/i.test(part)
          ? <strong key={i} style={{ color: '#fff', fontWeight: 650 }}>{part}</strong>
          : part
      )}
    </>
  );
}

export function PlanLimitModal({ warning, onClose, onUpgrade }: PlanLimitModalProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <>
      <style>{STYLES}</style>

      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 1000,
          background: 'rgba(4,4,10,0.75)',
          backdropFilter: 'blur(6px)',
          WebkitBackdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          animation: '_modal-backdrop 0.2s ease both',
        }}
      >
        {/* Card */}
        <div
          onClick={e => e.stopPropagation()}
          style={{
            position: 'relative',
            width: '90%', maxWidth: 348,
            background: 'linear-gradient(160deg, #111124 0%, #0b0b1a 60%, #090913 100%)',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: 22,
            padding: '32px 28px 28px',
            boxShadow: '0 32px 80px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.03)',
            animation: '_modal-card 0.32s cubic-bezier(0.34,1.4,0.64,1) both',
            overflow: 'hidden',
          }}
        >
          {/* Ambient glow blob */}
          <div style={{
            position: 'absolute', top: -60, left: '50%',
            transform: 'translateX(-50%)',
            width: 220, height: 120,
            background: 'radial-gradient(ellipse, rgba(245,158,11,0.12) 0%, transparent 70%)',
            pointerEvents: 'none',
          }} />

          {/* Top accent line */}
          <div style={{
            position: 'absolute', top: 0, left: '15%', right: '15%', height: 1,
            background: 'linear-gradient(90deg, transparent, rgba(245,158,11,0.5), transparent)',
          }} />

          {/* Close */}
          <button
            onClick={onClose}
            style={{
              position: 'absolute', top: 14, right: 14,
              width: 26, height: 26, borderRadius: 7,
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.07)',
              cursor: 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'rgba(255,255,255,0.35)',
              transition: 'background 0.15s, color 0.15s',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.1)';
              e.currentTarget.style.color = 'rgba(255,255,255,0.7)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.background = 'rgba(255,255,255,0.05)';
              e.currentTarget.style.color = 'rgba(255,255,255,0.35)';
            }}
          >
            <X style={{ width: 11, height: 11 }} />
          </button>

          {/* Slot visualizer */}
          <div style={{ display: 'flex', gap: 7, justifyContent: 'center', marginBottom: 26 }}>
            {[0, 1, 2].map(i => (
              <div
                key={i}
                style={{
                  width: 54, height: 66, borderRadius: 11,
                  background: 'rgba(245,158,11,0.07)',
                  border: '1px solid rgba(245,158,11,0.22)',
                  display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center', gap: 5,
                  animation: `_slot-in 0.35s cubic-bezier(0.34,1.4,0.64,1) ${i * 0.07}s both`,
                }}
              >
                <FileText style={{ width: 15, height: 15, color: DARK.accent }} />
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3, alignItems: 'center' }}>
                  <div style={{ width: 26, height: 2, borderRadius: 2, background: 'rgba(245,158,11,0.28)' }} />
                  <div style={{ width: 18, height: 2, borderRadius: 2, background: 'rgba(245,158,11,0.16)' }} />
                </div>
              </div>
            ))}

            {/* Locked slot */}
            <div
              style={{
                width: 54, height: 66, borderRadius: 11,
                background: 'rgba(255,255,255,0.025)',
                border: '1px dashed rgba(255,255,255,0.1)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                animation: `_slot-in 0.35s cubic-bezier(0.34,1.4,0.64,1) 0.21s both, _locked-bob 3s ease-in-out 0.6s infinite`,
              }}
            >
              <Lock style={{ width: 14, height: 14, color: 'rgba(255,255,255,0.18)' }} />
            </div>
          </div>

          {/* Badge */}
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 10 }}>
            <span style={{
              fontSize: 10, fontWeight: 700, letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: DARK.accent, opacity: 0.85,
              background: 'rgba(245,158,11,0.08)',
              border: '1px solid rgba(245,158,11,0.15)',
              borderRadius: 20, padding: '3px 10px',
            }}>
              Limite atingido
            </span>
          </div>

          {/* Message */}
          <p style={{
            color: 'rgba(255,255,255,0.62)',
            fontSize: 13.5, lineHeight: 1.65,
            textAlign: 'center',
            margin: '0 0 24px',
          }}>
            <BoldPlans text={warning} />{' '}
            Assine o <strong style={{ color: '#fff', fontWeight: 650 }}>plano Solo</strong> para ter documentos ilimitados.
          </p>

          {/* CTA */}
          <button
            onClick={onUpgrade}
            style={{
              width: '100%',
              padding: '13px 0',
              borderRadius: 11,
              background: `linear-gradient(135deg, ${DARK.accent} 0%, #d97706 100%)`,
              color: '#08080f',
              border: 'none',
              fontSize: 13.5, fontWeight: 700,
              cursor: 'pointer',
              letterSpacing: '0.01em',
              animation: '_btn-glow 2.5s ease-in-out 0.5s infinite',
              transition: 'filter 0.15s, transform 0.1s',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.filter = 'brightness(1.1)';
              e.currentTarget.style.transform = 'translateY(-1px)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.filter = 'brightness(1)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
            onMouseDown={e => { e.currentTarget.style.transform = 'translateY(0) scale(0.98)'; }}
            onMouseUp={e => { e.currentTarget.style.transform = 'translateY(-1px) scale(1)'; }}
          >
            plano Solo
          </button>
        </div>
      </div>
    </>
  );
}
