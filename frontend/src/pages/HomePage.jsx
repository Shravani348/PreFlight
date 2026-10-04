import { useNavigate } from 'react-router-dom';
import { ArrowRight, ShieldCheck, FileSearch, ClipboardList, CheckCircle2, Sparkles } from 'lucide-react';
import Logo from '../components/Logo';
import Button from '../components/Button';
import { usePreFlight } from '../context/PreFlightContext';

const APPLICATION_TYPES = [
  { id: 'scholarship',  label: 'Scholarship',      emoji: '🎓', available: true },
  { id: 'college',      label: 'College Admission', emoji: '🏛️', available: false },
  { id: 'exam',         label: 'Exam Registration', emoji: '📝', available: false },
  { id: 'job',          label: 'Job Application',   emoji: '💼', available: false },
  { id: 'visa',         label: 'Visa',              emoji: '✈️', available: false },
  { id: 'kyc',          label: 'KYC Verification',  emoji: '🪪', available: false },
];

const HOW_IT_WORKS = [
  { icon: FileSearch,    title: 'Upload Documents', desc: 'Upload your application form and supporting documents.' },
  { icon: Sparkles,      title: 'AI Analysis',      desc: 'PreFlight checks for mismatches, missing items, and issues.' },
  { icon: ClipboardList, title: 'Fix Plan',         desc: 'Get a prioritized list of exactly what to fix.' },
  { icon: CheckCircle2,  title: 'Recheck & Go',     desc: "Fix issues and recheck until you're ready to submit." },
];

export default function HomePage() {
  const navigate = useNavigate();
  const { state, dispatch } = usePreFlight();

  return (
    <div className="min-h-screen">
      {/* ── Hero ── */}
      <section className="relative overflow-hidden pt-20 pb-16 px-4 sm:px-6">
        {/* Background glow orb */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden>
          <div
            className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[420px] rounded-full"
            style={{ background: 'radial-gradient(ellipse at center, rgba(99,102,241,0.14) 0%, transparent 70%)' }}
          />
        </div>

        <div className="relative max-w-4xl mx-auto text-center">
          {/* Logo */}
          <div className="flex justify-center mb-8">
            <Logo size="lg" />
          </div>

          <h1
            className="text-5xl sm:text-6xl lg:text-7xl font-extrabold mb-6 leading-tight text-balance"
            style={{ fontFamily: "'Outfit', sans-serif", color: 'var(--text-primary)' }}
          >
            Check your application
            <br />
            <span className="gradient-brand-text">before you submit it.</span>
          </h1>

          <p className="text-lg sm:text-xl max-w-2xl mx-auto mb-12 text-balance"
             style={{ color: 'var(--text-secondary)' }}>
            PreFlight scans your documents for mismatches, missing items, and requirement violations —
            so you catch problems before they cause a rejection.
          </p>

          {/* Application type selector */}
          <div className="mb-10">
            <p className="text-sm font-semibold uppercase tracking-widest mb-4"
               style={{ color: 'var(--text-muted)' }}>
              Select Application Type
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-w-2xl mx-auto">
              {APPLICATION_TYPES.map((type) => (
                <button
                  key={type.id}
                  id={`app-type-${type.id}`}
                  onClick={() => type.available && dispatch({ type: 'SET_APPLICATION_TYPE', payload: type.id })}
                  disabled={!type.available}
                  aria-pressed={state.applicationType === type.id}
                  className={`
                    relative glass glass-hover rounded-2xl p-4 text-left transition-all duration-200
                    ${type.available ? 'cursor-pointer' : 'opacity-40 cursor-not-allowed'}
                    ${state.applicationType === type.id
                      ? 'border-indigo-500/60 bg-indigo-500/10 ring-2 ring-indigo-500/30'
                      : ''}
                  `}
                >
                  <span className="text-2xl block mb-1.5" aria-hidden="true">{type.emoji}</span>
                  <span className="text-sm font-semibold" style={{ color: 'var(--text-primary)' }}>
                    {type.label}
                  </span>
                  {!type.available && (
                    <span className="absolute top-2 right-2 text-[10px] font-bold uppercase tracking-wide"
                          style={{ color: 'var(--text-faint)' }}>
                      Soon
                    </span>
                  )}
                  {state.applicationType === type.id && type.available && (
                    <span className="absolute top-2 right-2">
                      <ShieldCheck size={14} className="text-indigo-400" aria-hidden="true" />
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>

          <Button
            id="start-preflight-btn"
            variant="primary"
            size="xl"
            onClick={() => navigate('/upload')}
            className="min-w-56"
          >
            Start PreFlight <ArrowRight size={20} aria-hidden="true" />
          </Button>

          <p className="mt-4 text-xs" style={{ color: 'var(--text-faint)' }}>
            Your documents are never stored beyond your session.
          </p>
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 pb-20">
        <h2 className="text-center text-2xl font-bold mb-10" style={{ color: 'var(--text-secondary)' }}>
          How it works
        </h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {HOW_IT_WORKS.map((step, i) => {
            const Icon = step.icon;
            return (
              <div key={step.title} className="glass rounded-2xl p-6 relative">
                <div className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-3">
                  Step {i + 1}
                </div>
                <Icon size={28} className="text-indigo-400 mb-3" aria-hidden="true" />
                <h3 className="font-bold mb-1" style={{ color: 'var(--text-primary)' }}>{step.title}</h3>
                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>{step.desc}</p>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
