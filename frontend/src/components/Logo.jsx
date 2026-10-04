import { useTheme } from '../context/ThemeContext';
import logoDark from '../assets/logo-dark-transparent.png';
import logoLight from '../assets/logo-light-transparent.png';

export default function Logo({ size = 'md', className = '' }) {
  const { theme } = useTheme();

  const heights = {
    sm: 'h-7 sm:h-8',
    md: 'h-9 sm:h-10',
    lg: 'h-16 sm:h-20',
  };

  const hClass = heights[size] || heights.md;
  const currentLogo = theme === 'light' ? logoLight : logoDark;

  return (
    <div className={`inline-flex items-center select-none ${className}`}>
      <img
        src={currentLogo}
        alt="PreFlight Logo"
        className={`${hClass} w-auto max-w-full object-contain drop-shadow-sm transition-opacity duration-200`}
        style={{ aspectRatio: '1024 / 341' }}
        loading="eager"
      />
    </div>
  );
}
