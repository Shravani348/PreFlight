/**
 * Reusable Button component.
 * Variants: 'primary' | 'secondary' | 'danger' | 'ghost'
 */
export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  onClick,
  type = 'button',
  className = '',
  id,
  ...props
}) {
  const base =
    'inline-flex items-center justify-center gap-2 font-semibold rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-transparent cursor-pointer select-none';

  const variants = {
    primary:
      'gradient-brand text-white glow-brand hover:opacity-90 active:scale-95 focus:ring-indigo-500',
    secondary:
      'glass text-primary border border-subtle hover:bg-white/10 active:scale-95 focus:ring-indigo-500',
    danger:
      'bg-red-500/20 text-red-300 border border-red-500/30 hover:bg-red-500/30 active:scale-95 focus:ring-red-500',
    ghost:
      'text-secondary hover:text-primary hover:bg-white/5 active:scale-95 focus:ring-indigo-500',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-5 py-2.5 text-sm',
    lg: 'px-7 py-3.5 text-base',
    xl: 'px-9 py-4 text-lg',
  };

  const disabledStyle = disabled || loading ? 'opacity-50 cursor-not-allowed pointer-events-none' : '';

  return (
    <button
      id={id}
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      aria-disabled={disabled || loading}
      aria-busy={loading}
      className={`${base} ${variants[variant]} ${sizes[size]} ${disabledStyle} ${className}`}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
        </svg>
      )}
      {children}
    </button>
  );
}
