import { Moon, Sun } from 'lucide-react';
import Logo from './Logo';
import { useTheme } from '../context/ThemeContext';

export default function Navbar() {
  const { theme, toggle } = useTheme();

  return (
    <header className="sticky top-0 z-50 nav-bg">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Logo size="md" />

        {/* Theme toggle */}
        <button
          id="theme-toggle-btn"
          onClick={toggle}
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          className="w-9 h-9 rounded-full flex items-center justify-center glass glass-hover cursor-pointer transition-all"
        >
          {theme === 'dark'
            ? <Sun size={17} className="text-amber-300" aria-hidden />
            : <Moon size={17} className="text-indigo-500" aria-hidden />
          }
        </button>
      </div>
    </header>
  );
}
