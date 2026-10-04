import PreFlightIcon from './PreFlightIcon';

export default function Logo({ size = 'md' }) {
  const sizes = {
    sm: { iconPx: 28, text: 'text-xl' },
    md: { iconPx: 36, text: 'text-2xl' },
    lg: { iconPx: 56, text: 'text-5xl' },
  };
  const s = sizes[size] || sizes.md;

  return (
    <div className="flex items-center gap-3">
      <div className="flex-shrink-0 drop-shadow-lg">
        <PreFlightIcon size={s.iconPx} />
      </div>
      <span
        className={`font-extrabold tracking-tight ${s.text}`}
        style={{
          fontFamily: "'Outfit', sans-serif",
          background: 'linear-gradient(135deg, #7B6FF0 0%, #A89EF8 50%, #C4BBFF 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}
      >
        PreFlight
      </span>
    </div>
  );
}
