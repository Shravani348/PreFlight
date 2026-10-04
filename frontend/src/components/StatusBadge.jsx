import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';

const config = {
  PASS: {
    label: 'Passed',
    icon: CheckCircle2,
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20',
    dot: 'bg-emerald-400',
  },
  WARNING: {
    label: 'Warning',
    icon: AlertTriangle,
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/20',
    dot: 'bg-amber-400',
  },
  CRITICAL: {
    label: 'Critical',
    icon: XCircle,
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/20',
    dot: 'bg-red-400',
  },
};

export default function StatusBadge({ status, showLabel = true, size = 'sm' }) {
  const cfg = config[status] || config.PASS;
  const Icon = cfg.icon;
  const iconSize = size === 'lg' ? 20 : size === 'md' ? 16 : 14;
  const textSize = size === 'lg' ? 'text-sm' : 'text-xs';
  const padding = size === 'lg' ? 'px-3 py-1.5' : 'px-2 py-0.5';

  return (
    <span
      role="status"
      aria-label={cfg.label}
      className={`inline-flex items-center gap-1.5 rounded-full border font-semibold ${cfg.bg} ${cfg.border} ${cfg.color} ${textSize} ${padding}`}
    >
      <Icon size={iconSize} aria-hidden="true" />
      {showLabel && cfg.label}
    </span>
  );
}
