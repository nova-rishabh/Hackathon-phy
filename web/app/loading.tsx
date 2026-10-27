// Shown by Next.js while a page loads: a thin bar along the top and the RollWatch eye, blinking.
export default function Loading() {
  return (
    <div className="pageload" role="status" aria-label="Loading">
      <span className="pageload-bar" aria-hidden="true"><i /></span>
      <div className="pageload-mark" aria-hidden="true">
        <svg viewBox="0 0 500 500" width="72" height="72">
          <g className="eyering-blink">
            <path d="M105,250 Q250,95 395,250 Q250,405 105,250 Z" fill="var(--color-surface)" stroke="var(--color-brand)" strokeWidth="14" />
            <circle cx="250" cy="250" r="72" fill="var(--color-brand)" />
            <circle cx="250" cy="250" r="40" fill="#2A2F33" />
          </g>
        </svg>
        <p className="mono text-[12px] text-ink-3 mt-3">loading</p>
      </div>
    </div>
  );
}
