"use client";
import { useEffect, useRef, useState } from "react";
import type { StoryResult } from "@/lib/types";
import { CTX, Ctx } from "@/lib/stories";
import { pct } from "@/lib/api";

const COLOR: Record<string, string> = {
  death_registered: "var(--color-story-death)", hostel_moveout: "var(--color-story-hostel)",
  boundary_change: "var(--color-story-boundary)", duplicate_cleanup: "var(--color-story-dupes)",
  unexplained: "var(--color-story-unexplained)",
};
const SHORT: Record<string, string> = { death_registered: "Death", hostel_moveout: "Hostel", boundary_change: "Boundary", duplicate_cleanup: "Dupes", unexplained: "Unexplained" };

function useTween(target: number, ms = 300) {
  const [v, setV] = useState(target);
  const from = useRef(target);
  useEffect(() => {
    const a = from.current, t0 = performance.now();
    let raf = 0;
    const step = (t: number) => {
      const k = Math.min(1, (t - t0) / ms);
      const cur = a + (target - a) * k;
      setV(cur); from.current = cur;
      if (k < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);
  return v;
}

export default function StoryBar({ res, on, onToggle, busy }: { res: StoryResult; on: Ctx[]; onToggle: (c: Ctx) => void; busy?: boolean }) {
  const un = res.stories.find((s) => s.code === "unexplained");
  const shown = useTween(un ? un.share * 100 : 0);
  const ordered = [...res.stories.filter((s) => s.code !== "unexplained"), ...res.stories.filter((s) => s.code === "unexplained")];
  return (
    <div>
      <div className="overline mb-2">Which story fits? · {res.removed_total} removed</div>
      <div className="relative h-5 w-full bg-sunk border border-rule flex" role="img"
        aria-label={ordered.map((s) => `${s.label} ${s.count}`).join(", ")}>
        {ordered.map((s) => (
          <div key={s.code} className="relative h-full" style={{ width: `${s.share * 100}%`, background: COLOR[s.code], transition: "width 300ms linear" }}>
            {s.count > 0 && <span className="absolute top-[-3px] bottom-[-3px] w-px bg-ink" style={{ right: 0 }} />}
          </div>
        ))}
      </div>
      <p className="font-mono text-[12px] leading-5 mt-2 text-ink-2">
        {ordered.map((s, i) => (
          <span key={s.code}>{i > 0 && " · "}{SHORT[s.code]} {s.count}{s.count > 0 ? ` (${pct(s.share)})` : ""}
            {s.code === "unexplained" && ` ±${((s.ci_hi - s.ci_lo) * 50).toFixed(0)}`}</span>
        ))}
      </p>
      <div className="mt-3 flex items-baseline gap-3">
        <span className="font-mono text-[44px] leading-[48px] font-semibold text-unusual tabular-nums">{shown.toFixed(0)}%</span>
        <span className="text-[13px] text-ink-2 leading-[18px]">unexplained · residual <span className="font-mono">{res.residual.count}</span> vs about <span className="font-mono">{res.residual.expected_background.toFixed(0)}</span> expected<br />
          {res.residual.significant ? "Still above background" : "Within background"} (p = <span className="font-mono">{res.residual.p_value < 0.001 ? "<0.001" : res.residual.p_value.toFixed(3)}</span>)</span>
      </div>
      <fieldset className="mt-3 border-t border-rule pt-3" disabled={busy}>
        <legend className="overline pr-2">Context sources</legend>
        {CTX.map((c) => (
          <label key={c.id} className="block text-[14px] py-1 cursor-pointer">
            <input type="checkbox" className="chk" checked={on.includes(c.id)} onChange={() => onToggle(c.id)} />{c.label}
          </label>
        ))}
      </fieldset>
    </div>
  );
}
