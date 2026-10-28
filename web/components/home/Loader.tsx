"use client";
import { useEffect, useRef, useState } from "react";

const HATCH = Array.from({ length: 16 }, () => "/".repeat(40)).join("\n");

/**
 * A hatched orb with a counter. The count follows real work (fonts, the eye texture, the first API answer);
 * it eases toward the share done and never claims 100 before everything has arrived or the wait cap passes.
 */
export default function Loader({ done, total, onFinish }: { done: number; total: number; onFinish: () => void }) {
  const [shown, setShown] = useState(0);
  const [out, setOut] = useState(false);
  const target = useRef(0);
  target.current = Math.round((done / total) * 100);

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      setShown((s) => (s < target.current ? Math.min(target.current, s + Math.max(1, Math.round((target.current - s) * 0.12))) : s));
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    if (shown < 100 || out) return;
    const t = setTimeout(() => { setOut(true); onFinish(); }, 250);
    return () => clearTimeout(t);
  }, [shown, out, onFinish]);

  return (
    <div className={`v3loader ${out ? "done" : ""}`} aria-hidden={out} role="status" aria-label="Loading">
      <div className="v3loader-orb">
        <div className="v3loader-hatch" aria-hidden="true">{HATCH}</div>
        <span className="v3loader-count">/{String(shown).padStart(2, "0")}</span>
      </div>
    </div>
  );
}
