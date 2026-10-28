"use client";
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";

/** One stop: the element to light up (CSS selector), and what to say about it. Numbers in `body` come from the API. */
export type TourStep = { target: string; title: string; body: ReactNode; onEnter?: () => void };

type Box = { x: number; y: number; w: number; h: number };
const PAD = 8, GAP = 14, HEADER = 116, SHEET = 280;
const reduced = () => typeof window !== "undefined" && !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
const phone = () => typeof window !== "undefined" && window.innerWidth < 640;

function visibleEl(sel: string): HTMLElement | null {
  for (const el of Array.from(document.querySelectorAll<HTMLElement>(sel))) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0) return el;
  }
  return null;
}

/** Scroll so the element sits in the free part of the screen: centred if it fits, else its top under the header. */
function bring(el: HTMLElement) {
  const r = el.getBoundingClientRect();
  if (el.closest("header")) return; // the sticky header is always on screen
  const bottom = window.innerHeight - (phone() ? SHEET : 0);
  const room = bottom - HEADER;
  const top = window.scrollY + r.top - (r.height + 2 * PAD <= room ? HEADER + (room - r.height) / 2 : HEADER + PAD);
  window.scrollTo({ top: Math.max(0, top), behavior: reduced() ? "auto" : "smooth" });
}

/**
 * Onboarding tour: dims the page, cuts a spotlight around one element at a time and explains it in a card beside it.
 * The spotlight is an SVG cut-out (no shadows); clicks inside it reach the page, so the highlighted thing stays usable.
 * Esc closes, arrow keys step. On phones the card is a bottom sheet.
 */
export default function Tour({ steps, open, onClose }: { steps: TourStep[]; open: boolean; onClose: () => void }) {
  const [i, setI] = useState(0);
  const [box, setBox] = useState<Box | null>(null);
  const [card, setCard] = useState<{ left: number; top: number } | null>(null);
  const shown = useRef<Box | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const nextRef = useRef<HTMLButtonElement>(null);
  const step = steps[Math.min(i, steps.length - 1)];
  const stepsRef = useRef(steps);
  stepsRef.current = steps; // steps are rebuilt every render; the effect below must only re-run when the stop changes

  useEffect(() => { if (open) setI(0); }, [open]);

  // On each step: run its hook, bring the element into view, then follow it every frame (scroll, resize, reflow),
  // easing the spotlight toward it so it glides from one stop to the next.
  useEffect(() => {
    const st = stepsRef.current[i];
    if (!open || !st) return;
    st.onEnter?.();
    let raf = 0, el: HTMLElement | null = null, tries = 0;
    const find = () => {
      el = visibleEl(st.target);
      if (el) bring(el);
      else if (tries++ < 20) raf = requestAnimationFrame(find); // the page may still be rendering this element
    };
    const t = setTimeout(find, 60);
    const loop = () => {
      const target = el ? (() => {
        const r = el!.getBoundingClientRect();
        const y0 = Math.max(r.top - PAD, 4), y1 = Math.min(r.bottom + PAD, window.innerHeight - 4);
        return { x: r.left - PAD, y: y0, w: r.width + 2 * PAD, h: Math.max(y1 - y0, 0) };
      })() : null;
      const cur = shown.current;
      const next = !target ? null : !cur || reduced() ? target : {
        x: cur.x + (target.x - cur.x) * 0.22, y: cur.y + (target.y - cur.y) * 0.22,
        w: cur.w + (target.w - cur.w) * 0.22, h: cur.h + (target.h - cur.h) * 0.22,
      };
      shown.current = next;
      setBox(next);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    nextRef.current?.focus({ preventScroll: true });
    return () => { clearTimeout(t); cancelAnimationFrame(raf); };
  }, [open, i]);

  // Place the card beside the spotlight: below, above, right, left; else over the bottom of the screen.
  useLayoutEffect(() => {
    if (!open || phone()) { setCard(null); return; }
    const c = cardRef.current;
    if (!c) return;
    const cw = c.offsetWidth, ch = c.offsetHeight, W = window.innerWidth, H = window.innerHeight;
    const clampX = (x: number) => Math.min(Math.max(x, 16), W - cw - 16);
    const clampY = (y: number) => Math.min(Math.max(y, 16), H - ch - 16);
    if (!box) { setCard({ left: (W - cw) / 2, top: (H - ch) / 2 }); return; }
    const below = box.y + box.h + GAP, above = box.y - GAP - ch;
    if (below + ch <= H - 16) setCard({ left: clampX(box.x), top: below });
    else if (above >= 16) setCard({ left: clampX(box.x), top: above });
    else if (box.x + box.w + GAP + cw <= W - 16) setCard({ left: box.x + box.w + GAP, top: clampY(box.y) });
    else if (box.x - GAP - cw >= 16) setCard({ left: box.x - GAP - cw, top: clampY(box.y) });
    else setCard({ left: clampX(box.x + 24), top: H - ch - 24 }); // tall target: its lower left, away from the side panel
  }, [open, box, i]);

  const go = useCallback((d: number) => {
    const n = i + d;
    if (n >= steps.length) onClose();
    else if (n >= 0) setI(n);
  }, [i, steps.length, onClose]);

  useEffect(() => {
    if (!open) return;
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowRight") go(1);
      else if (e.key === "ArrowLeft") go(-1);
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [open, go, onClose]);

  useEffect(() => { if (!open) shown.current = null; }, [open]);

  if (!open || !step) return null;
  const W = typeof window !== "undefined" ? window.innerWidth : 0, H = typeof window !== "undefined" ? window.innerHeight : 0;
  const hole = box ? `M${box.x + 12},${box.y} h${box.w - 24} a12,12 0 0 1 12,12 v${Math.max(box.h - 24, 0)} a12,12 0 0 1 -12,12 h${-(box.w - 24)} a12,12 0 0 1 -12,-12 v${-Math.max(box.h - 24, 0)} a12,12 0 0 1 12,-12 Z` : "";
  const last = i === steps.length - 1;

  return (
    <div className="tour" role="dialog" aria-modal="true" aria-labelledby="tour-title" aria-describedby="tour-body">
      <svg className="tour-dim" width={W} height={H} aria-hidden="true">
        <path d={`M0,0 H${W} V${H} H0 Z ${hole}`} fillRule="evenodd" />
      </svg>
      {box && <div className="tour-ring" style={{ left: box.x, top: box.y, width: box.w, height: box.h }} aria-hidden="true" />}
      <div ref={cardRef} className={`tour-card ${card || phone() ? "in" : ""}`} style={card ? { left: card.left, top: card.top } : undefined}>
        <div className="flex items-center justify-between gap-3">
          <p className="eyebrow">Step {i + 1} of {steps.length}.</p>
          <button className="mono text-[12px] text-ink-2 hover:text-ink" onClick={onClose}>Skip tour</button>
        </div>
        <div aria-live="polite">
          <h2 id="tour-title" className="text-[21px] leading-[26px] tracking-[-0.02em] mt-3">{step.title}</h2>
          <div id="tour-body" className="text-[14px] leading-[22px] text-ink-2 mt-2">{step.body}</div>
        </div>
        <div className="flex items-center justify-between gap-3 mt-5">
          <div className="flex gap-1" aria-hidden="true">
            {steps.map((_, k) => <i key={k} className={`tour-pip ${k === i ? "on" : k < i ? "done" : ""}`} />)}
          </div>
          <div className="flex gap-2">
            {i > 0 && <button className="btn btn--quiet !h-9" onClick={() => go(-1)}>Back</button>}
            <button ref={nextRef} className="btn !h-9" onClick={() => go(1)}>{last ? "Done" : "Next"}</button>
          </div>
        </div>
      </div>
    </div>
  );
}
