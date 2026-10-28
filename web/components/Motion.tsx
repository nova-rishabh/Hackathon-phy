"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { BoothTile } from "./Display";

/** True once the element has scrolled into view (at once without IntersectionObserver or with reduced motion). */
export function useInView<T extends Element>(threshold = 0.3) {
  const ref = useRef<T>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined" || window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) { setInView(true); return; }
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setInView(true); io.disconnect(); } }, { threshold });
    io.observe(el);
    return () => io.disconnect();
  }, [threshold]);
  return [ref, inView] as const;
}

/** Adds "in" to its wrapper once visible, so `.grow-in-view` bars inside start growing only when seen. */
export function InView({ children, className = "" }: { children: ReactNode; className?: string }) {
  const [ref, inView] = useInView<HTMLDivElement>();
  return <div ref={ref} className={`${className} ${inView ? "in" : ""}`}>{children}</div>;
}

/** A booth tile that cycles through a few booths (outcomes from the engine), swapping through a short blur. */
export function CyclingBooth({ booths, every = 2600 }: { booths: { booth: string; outcome: string }[]; every?: number }) {
  const [i, setI] = useState(0);
  const [out, setOut] = useState(false);
  useEffect(() => {
    if (booths.length < 2 || window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    let swap: ReturnType<typeof setTimeout>;
    const t = setInterval(() => {
      setOut(true);
      swap = setTimeout(() => { setI((k) => (k + 1) % booths.length); setOut(false); }, 240);
    }, every);
    return () => { clearInterval(t); clearTimeout(swap); };
  }, [booths.length, every]);
  const b = booths[i % booths.length];
  if (!b) return null;
  return <span className={`cycle-tile ${out ? "out" : ""}`}><BoothTile booth={b.booth} outcome={b.outcome} /></span>;
}

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

/** Critically damped spring step response: settles with no overshoot (closed form, as in the film). */
const settle = (t: number, f = 1.1) => { const w = 2 * Math.PI * f; return t <= 0 ? 0 : 1 - Math.exp(-w * t) * (1 + w * t); };

/** Counts from 0 to `to` (a number the engine computed) once it scrolls into view, settling on a spring. */
export function CountUp({ to, decimals = 0, suffix = "" }: { to: number; decimals?: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [v, setV] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) { setV(to); return; }
    let raf = 0, started = false;
    const fallback = setTimeout(() => { if (!started) setV(to); }, 4000); // never leave a 0 on screen
    const io = new IntersectionObserver(([e]) => {
      if (!e.isIntersecting) return;
      io.disconnect();
      started = true;
      const t0 = performance.now();
      const step = (t: number) => {
        const k = settle((t - t0) / 1000);
        setV(k > 0.999 ? to : to * k);
        if (k <= 0.999) raf = requestAnimationFrame(step);
      };
      raf = requestAnimationFrame(step);
    }, { threshold: 0.3 });
    io.observe(el);
    return () => { io.disconnect(); cancelAnimationFrame(raf); clearTimeout(fallback); };
  }, [to]);
  const shown = decimals ? v.toFixed(decimals) : Math.round(v).toLocaleString("en-IN");
  return <span ref={ref}>{shown}{suffix}</span>;
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
