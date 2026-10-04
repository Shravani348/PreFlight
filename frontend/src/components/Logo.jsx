import { ShieldCheck } from 'lucide-react';

export default function Logo({ size = 'md' }) {
  const sizes = {
    sm: { icon: 18, text: 'text-lg' },
    md: { icon: 24, text: 'text-2xl' },
    lg: { icon: 32, text: 'text-4xl' },
  };
  const s = sizes[size] || sizes.md;

  return (
    <div className="flex items-center gap-2">
      <div className="gradient-brand rounded-xl p-1.5 glow-brand flex-shrink-0">
        <ShieldCheck size={s.icon} color="white" strokeWidth={2.5} aria-hidden="true" />
      </div>
      <span className={`font-extrabold tracking-tight gradient-brand-text ${s.text}`}
            style={{ fontFamily: "'Outfit', sans-serif" }}>
        PreFlight
      </span>
    </div>
  );
}
