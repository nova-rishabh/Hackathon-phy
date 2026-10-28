"use client";

export const CHAPTERS = [
  { id: "top", label: "RollWatch" },
  { id: "problem", label: "The rumour" },
  { id: "audit", label: "Audit" },
  { id: "story", label: "Which story fits" },
  { id: "check", label: "Claim court" },
  { id: "ask", label: "Ask" },
  { id: "tested", label: "Tested" },
  { id: "scale", label: "Scale" },
  { id: "why", label: "Three questions" },
  { id: "connect", label: "Connect" },
] as const;

const NAV: [string, string, boolean][] = [["audit", "Audit", false], ["check", "Check", false], ["ask", "Ask", false], ["tested", "Trust", true], ["connect", "Connect", false]];

export function TopBar({ active }: { active: number }) {
  const at = CHAPTERS[active]?.id;
  return (
    <header className="top">
      <a href="#top" aria-label="RollWatch, back to the top">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/logo-word.png" alt="RollWatch" className="logo" />
      </a>
      <nav className="navpill glass" aria-label="Chapters">
        {NAV.map(([id, label, opt], i) => (
          <span key={id} className={`row ${opt ? "opt" : ""}`} style={{ gap: 0 }}>
            {i > 0 && <span className="sep" aria-hidden="true" />}
            <a href={`#${id}`} aria-current={at === id || (id === "tested" && at === "scale") ? "true" : undefined}>{label}</a>
          </span>
        ))}
      </nav>
    </header>
  );
}

export function Progress({ active, frac }: { active: number; frac: number }) {
  return (
    <div className="progress" aria-hidden="true">
      <span className="mono" style={{ fontSize: 12, color: "var(--ink)" }}>/{String(active).padStart(2, "0")}</span>
      <span className="progress-bar"><i style={{ transform: `scaleX(${frac})` }} /></span>
      <span className="eyebrow">{CHAPTERS[active]?.label}</span>
    </div>
  );
}

export function Note() {
  return <p className="note">synthetic data · Sampleabad is fictional · flags are patterns for human review, not findings</p>;
}
