import Logo from './Logo';
import { DEMO_MODE } from '../api/apiService';

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-[#0a0b14]/80 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Logo size="md" />
        {DEMO_MODE && (
          <span className="text-xs font-semibold px-3 py-1 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/25">
            🎭 DEMO MODE
          </span>
        )}
      </div>
    </header>
  );
}
