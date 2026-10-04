/**
 * PreFlight icon SVG — matches the brand logo: purple rounded-square,
 * shield with checkmark, airplane silhouette, swoosh wings.
 */
export default function PreFlightIcon({ size = 40 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="pf-bg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#5B54E8" />
          <stop offset="100%" stopColor="#7B6FF0" />
        </linearGradient>
        <linearGradient id="pf-shield" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="1" />
          <stop offset="100%" stopColor="#c4bbff" stopOpacity="0.95" />
        </linearGradient>
        <linearGradient id="pf-wing" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.7" />
          <stop offset="100%" stopColor="#a89ef8" stopOpacity="0.4" />
        </linearGradient>
        <filter id="pf-glow">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Rounded square background */}
      <rect width="100" height="100" rx="22" fill="url(#pf-bg)" />

      {/* Inner subtle highlight */}
      <rect width="100" height="100" rx="22" fill="url(#pf-bg)" opacity="0.3" />
      <rect x="1" y="1" width="98" height="50" rx="22" fill="white" opacity="0.06" />

      {/* Left swoosh wing */}
      <path
        d="M14 72 Q22 62 34 68 Q26 74 14 72Z"
        fill="url(#pf-wing)"
      />
      <path
        d="M10 78 Q22 66 38 74 Q28 82 10 78Z"
        fill="url(#pf-wing)"
        opacity="0.6"
      />

      {/* Right swoosh wing */}
      <path
        d="M86 72 Q78 62 66 68 Q74 74 86 72Z"
        fill="url(#pf-wing)"
      />
      <path
        d="M90 78 Q78 66 62 74 Q72 82 90 78Z"
        fill="url(#pf-wing)"
        opacity="0.6"
      />

      {/* Shield body */}
      <path
        d="M50 16 L68 24 L68 44 C68 56 60 65 50 70 C40 65 32 56 32 44 L32 24 Z"
        fill="url(#pf-shield)"
        filter="url(#pf-glow)"
      />

      {/* Shield inner gradient overlay */}
      <path
        d="M50 20 L65 27 L65 44 C65 54.5 58 62.5 50 67 C42 62.5 35 54.5 35 44 L35 27 Z"
        fill="none"
        stroke="rgba(99,102,241,0.25)"
        strokeWidth="1"
      />

      {/* Checkmark */}
      <path
        d="M41 43 L47.5 50 L60 36"
        stroke="#5B54E8"
        strokeWidth="4.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Airplane (top-right of shield) */}
      <g transform="translate(57, 22) rotate(-35)">
        <path
          d="M0 0 L8 -3 L10 0 L8 3 Z"
          fill="#5B54E8"
          opacity="0.9"
        />
        <path d="M4 -0.5 L10 -5 L11 -3.5 L5 0Z" fill="#5B54E8" opacity="0.7" />
        <path d="M4 0.5 L10 5 L11 3.5 L5 0Z" fill="#5B54E8" opacity="0.7" />
        <path d="M7 -0.3 L11 -2 L11.5 -0.3 L9 0Z" fill="#5B54E8" opacity="0.5" />
        <path d="M7 0.3 L11 2 L11.5 0.3 L9 0Z" fill="#5B54E8" opacity="0.5" />
      </g>
    </svg>
  );
}
