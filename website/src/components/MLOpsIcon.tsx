import './MLOpsIcon.css'

interface Props {
  size?: number
  className?: string
}

/**
 * Animated neural-network SVG that serves as the MLOps Playbook brand icon.
 * Three-layer architecture: input → hidden → output nodes connected by
 * animated data-flow edges.
 */
export function MLOpsIcon({ size = 30, className = '' }: Props) {
  return (
    <svg
      className={`mlops-icon ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
    >
      <defs>
        <radialGradient id="ml-ng1" cx="40%" cy="35%" r="65%">
          <stop offset="0%" stopColor="#c4b5fd" />
          <stop offset="100%" stopColor="#7c3aed" />
        </radialGradient>
        <radialGradient id="ml-ng2" cx="40%" cy="35%" r="65%">
          <stop offset="0%" stopColor="#7dd3fc" />
          <stop offset="100%" stopColor="#0369a1" />
        </radialGradient>
        <filter id="ml-glow" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur in="SourceGraphic" stdDeviation="1.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* ── Connections: Input → Hidden ─────────────────────────────── */}
      <line className="ml-conn ml-c1"  x1="7"    y1="10"   x2="14.5" y2="6.5"  stroke="#a78bfa" strokeWidth="0.9" strokeDasharray="2 2" />
      <line className="ml-conn ml-c2"  x1="7"    y1="10"   x2="14.5" y2="16"   stroke="#a78bfa" strokeWidth="0.9" strokeDasharray="2 2" />
      <line className="ml-conn ml-c3"  x1="7"    y1="10"   x2="14.5" y2="25.5" stroke="#a78bfa" strokeWidth="0.9" strokeDasharray="2 2" />
      <line className="ml-conn ml-c4"  x1="7"    y1="22"   x2="14.5" y2="6.5"  stroke="#a78bfa" strokeWidth="0.9" strokeDasharray="2 2" />
      <line className="ml-conn ml-c5"  x1="7"    y1="22"   x2="14.5" y2="16"   stroke="#a78bfa" strokeWidth="0.9" strokeDasharray="2 2" />
      <line className="ml-conn ml-c6"  x1="7"    y1="22"   x2="14.5" y2="25.5" stroke="#a78bfa" strokeWidth="0.9" strokeDasharray="2 2" />

      {/* ── Connections: Hidden → Output ─────────────────────────────── */}
      <line className="ml-conn ml-c7"  x1="17.5" y1="6.5"  x2="25"   y2="11.5" stroke="#38bdf8" strokeWidth="0.9" strokeDasharray="2 2" />
      <line className="ml-conn ml-c8"  x1="17.5" y1="6.5"  x2="25"   y2="21.5" stroke="#38bdf8" strokeWidth="0.9" strokeDasharray="2 2" />
      <line className="ml-conn ml-c9"  x1="17.5" y1="16"   x2="25"   y2="11.5" stroke="#38bdf8" strokeWidth="0.9" strokeDasharray="2 2" />
      <line className="ml-conn ml-c10" x1="17.5" y1="16"   x2="25"   y2="21.5" stroke="#38bdf8" strokeWidth="0.9" strokeDasharray="2 2" />
      <line className="ml-conn ml-c11" x1="17.5" y1="25.5" x2="25"   y2="11.5" stroke="#38bdf8" strokeWidth="0.9" strokeDasharray="2 2" />
      <line className="ml-conn ml-c12" x1="17.5" y1="25.5" x2="25"   y2="21.5" stroke="#38bdf8" strokeWidth="0.9" strokeDasharray="2 2" />

      {/* ── Input layer nodes ────────────────────────────────────────── */}
      <circle className="ml-node ml-n1" cx="6"  cy="10"   r="2.6" fill="url(#ml-ng1)" filter="url(#ml-glow)" />
      <circle className="ml-node ml-n2" cx="6"  cy="22"   r="2.6" fill="url(#ml-ng1)" filter="url(#ml-glow)" />

      {/* ── Hidden layer nodes ───────────────────────────────────────── */}
      <circle className="ml-node ml-n3" cx="16" cy="6.5"  r="2.6" fill="url(#ml-ng1)" filter="url(#ml-glow)" />
      <circle className="ml-node ml-n4" cx="16" cy="16"   r="3.2" fill="url(#ml-ng1)" filter="url(#ml-glow)" />
      <circle className="ml-node ml-n5" cx="16" cy="25.5" r="2.6" fill="url(#ml-ng1)" filter="url(#ml-glow)" />

      {/* ── Output layer nodes ───────────────────────────────────────── */}
      <circle className="ml-node ml-n6" cx="26" cy="11.5" r="2.6" fill="url(#ml-ng2)" filter="url(#ml-glow)" />
      <circle className="ml-node ml-n7" cx="26" cy="21.5" r="2.6" fill="url(#ml-ng2)" filter="url(#ml-glow)" />
    </svg>
  )
}
