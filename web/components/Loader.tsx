/** The RollWatch eye, blinking: the one loader used everywhere a wait is visible. */
export function Eye({ size = 28 }: { size?: number }) {
  return (
    <svg viewBox="0 0 500 500" width={size} height={size} aria-hidden="true" className="shrink-0">
      <g className="eyering-blink loader-blink">
        <path d="M105,250 Q250,95 395,250 Q250,405 105,250 Z" fill="#FFFFFF" stroke="var(--color-brand)" strokeWidth="18" />
        <circle cx="250" cy="250" r="72" fill="var(--color-brand)" />
        <circle cx="250" cy="250" r="40" fill="#2A2F33" />
      </g>
    </svg>
  );
}

/** Inline loader: the eye, a short label, and a hairline that sweeps underneath. */
export default function Loader({ label, size = 28, className = "" }: { label: string; size?: number; className?: string }) {
  return (
    <div className={`loader ${className}`} role="status" aria-live="polite">
      <Eye size={size} />
      <span className="mono text-[13px] text-ink-2">{label}</span>
      <span className="loader-sweep" aria-hidden="true"><i /></span>
    </div>
  );
}

/** Where an answer is about to land: a card the shape of the answer, with the loader and resting bars. */
export function AnswerPending({ label, lines = 3, className = "" }: { label: string; lines?: number; className?: string }) {
  return (
    <div className={`pending ${className}`}>
      <Loader label={label} />
      <div className="mt-5 grid gap-2.5" aria-hidden="true">
        {Array.from({ length: lines }, (_, i) => <i key={i} className="pending-bar" style={{ width: `${[92, 78, 54, 66][i % 4]}%`, animationDelay: `${i * 120}ms` }} />)}
      </div>
    </div>
  );
}

/** Full-area loader for a page's first data: centred eye with a label. */
export function PageLoader({ label }: { label: string }) {
  return (
    <div className="pageload" role="status" aria-live="polite">
      <div className="pageload-mark">
        <Eye size={72} />
        <p className="mono text-[12px] text-ink-3 mt-3">{label}</p>
      </div>
    </div>
  );
}
