"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";

/** Fades and lifts its children in the first time they scroll into view. */
export function Reveal({ children, delay = 0, className = "" }: { children: ReactNode; delay?: number; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setInView(true); io.disconnect(); } }, { threshold: 0.15 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return <div ref={ref} className={`reveal ${inView ? "in" : ""} ${className}`} style={{ transitionDelay: `${delay}ms` }}>{children}</div>;
}

/** Counts from 0 to `to` (a number the engine computed) over `ms`. */
export function CountUp({ to, ms = 1200 }: { to: number; ms?: number }) {
  const [v, setV] = useState(0);
  useEffect(() => {
    let raf = 0;
    const t0 = performance.now();
    const step = (t: number) => {
      const k = Math.min(1, (t - t0) / ms);
      setV(Math.round(to * (1 - Math.pow(1 - k, 3))));
      if (k < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [to, ms]);
  return <>{v.toLocaleString("en-IN")}</>;
}

/** The RollWatch mark, live: the ring of text turns, the pupil follows the pointer, and the eye blinks. */
export function EyeRing({ size = 360 }: { size?: number }) {
  const ref = useRef<SVGSVGElement>(null);
  const [p, setP] = useState({ x: 0, y: 0 });
  useEffect(() => {
    const move = (e: PointerEvent) => {
      const r = ref.current?.getBoundingClientRect();
      if (!r) return;
      const dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
      const d = Math.hypot(dx, dy) || 1, k = Math.min(1, d / 220);
      setP({ x: (dx / d) * 24 * k, y: (dy / d) * 14 * k });
    };
    window.addEventListener("pointermove", move);
    return () => window.removeEventListener("pointermove", move);
  }, []);
  return (
    <svg ref={ref} viewBox="0 0 500 500" width={size} height={size} className="eyering" aria-hidden="true">
      <defs><path id="ring" d="M250,250 m-205,0 a205,205 0 1,1 410,0 a205,205 0 1,1 -410,0" /></defs>
      <g className="eyering-spin">
        <text fill="var(--color-brand)" style={{ font: "400 44px var(--font-sans)", letterSpacing: "0.16em" }}>
          <textPath href="#ring" textLength="1285">ROLLWATCH-ROLLWATCH-</textPath>
        </text>
      </g>
      <g className="eyering-blink">
        <path d="M105,250 Q250,95 395,250 Q250,405 105,250 Z" fill="var(--color-surface)" stroke="var(--color-brand)" strokeWidth="9" />
        <g style={{ transform: `translate(${p.x}px, ${p.y}px)`, transition: "transform 70ms linear" }}>
          <circle cx="250" cy="250" r="72" fill="var(--color-brand)" />
          <circle cx="250" cy="250" r="40" fill="#2A2F33" />
          <circle cx="268" cy="232" r="13" fill="#FFFFFF" />
        </g>
      </g>
    </svg>
  );
}

/** A slow horizontal strip of short facts. */
export function Marquee({ items }: { items: string[] }) {
  const row = items.join("  ·  ") + "  ·  ";
  return (
    <div className="marquee" aria-label={items.join(". ")}>
      <div className="marquee-track" aria-hidden="true"><span>{row}</span><span>{row}</span></div>
    </div>
  );
}
