"use client";
import { useEffect, useRef, useState } from "react";
import type { StoryResult } from "@/lib/types";
import { CTX, Ctx, STORY_ORDER, STORY_SHORT, recompute } from "@/lib/stories";
import { postJson, boothNo, fmt } from "@/lib/api";
import { Display, Obj, Eyebrow } from "./Display";
import Chip from "./Chip";
import { useInView } from "./Motion";

const FILL: Record<string, string> = {
  death_registered: "var(--color-story-death)", duplicate_cleanup: "var(--color-story-dupes)",
  boundary_change: "var(--color-story-boundary)", hostel_moveout: "var(--color-story-hostel)",
};

function useTween(target: number, ms = 300) {
  const [v, setV] = useState(target);
  const cur = useRef(target);
  useEffect(() => {
    const a = cur.current, t0 = performance.now();
    let raf = 0;
    const step = (t: number) => {
      const k = Math.min(1, (t - t0) / ms);
      const e = 1 - Math.pow(1 - k, 3);
      cur.current = a + (target - a) * e;
      setV(cur.current);
      if (k < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);
  return v;
}

type Stories = StoryResult["stories"];
const ordered = (r: StoryResult) => STORY_ORDER.map((c) => r.stories.find((s) => s.code === c)).filter(Boolean) as Stories;

export function StoryBar({ res, mini }: { res: StoryResult; mini?: boolean }) {
  const [ref, seen] = useInView<HTMLDivElement>(0.5);
  return (
    <div ref={ref} className={`${mini ? "sbar sbar-mini" : "sbar"} ${seen ? "" : "sbar--wait"}`} role="img" aria-label={ordered(res).map((s) => `${STORY_SHORT[s.code]} ${s.count}`).join(", ")}>
      {ordered(res).map((s) => (
        <div key={s.code} className={s.code === "unexplained" ? "hatch" : ""}
          style={{ width: `${s.share * 100}%`, background: s.code === "unexplained" ? undefined : FILL[s.code] }} />
      ))}
    </div>
  );
}

export default function StoryPanel({ base }: { base: StoryResult }) {
  const [res, setRes] = useState(base);
  const [on, setOn] = useState<Ctx[]>(base.context_used as Ctx[]);
  const [offline, setOffline] = useState(false);
  const [busy, setBusy] = useState(false);
  useEffect(() => { setRes(base); setOn(base.context_used as Ctx[]); setOffline(false); }, [base]);

  const un = res.stories.find((s) => s.code === "unexplained");
  const shown = useTween((un ? un.share : 0) * 100);

  // Move the bar the moment a source is toggled (local recompute from the engine's own counts), then swap in the
  // engine's exact answer when it arrives. Only the latest toggle's answer is applied, so fast clicks never stack.
  const req = useRef(0);
  const set = async (c: Ctx, val: boolean) => {
    if (on.includes(c) === val) return;
    const next = val ? [...on, c] : on.filter((x) => x !== c);
    const id = ++req.current;
    setOn(next);
    setRes(recompute(base, next));
    setBusy(true);
    try {
      const r = await postJson<StoryResult>(`/stories/${base.booth_id}`, { context_on: next }, 8000);
      if (id === req.current) { setRes(r); setOffline(false); }
    } catch {
      if (id === req.current) setOffline(true);
    }
    if (id === req.current) setBusy(false);
  };

  const p = res.residual.p_value;
  return (
    <section className="panel" aria-label="Which story fits">
      <Eyebrow className="mb-6">Which story fits.</Eyebrow>
      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <div className="min-w-0">
          <Display size="section" as="h2" dim={`Booth ${boothNo(res.booth_id)}, ${on.length} of 4 evidence sources on.`}>
            {fmt(un?.count ?? 0)} of {fmt(res.removed_total)} removals fit no story <Obj><StoryBar res={res} mini /></Obj>
          </Display>
          <div className="mt-8"><StoryBar res={res} /></div>
          <p className="mono text-[13px] leading-5 text-ink-2 mt-3">
            {ordered(res).map((s, i) => (
              <span key={s.code} className={s.code === "unexplained" ? "text-ink" : ""}>
                {i > 0 && " · "}{STORY_SHORT[s.code]} {s.count}
                {s.code === "unexplained" && ` (${Math.round(s.share * 100)}%) ±${Math.round(((s.ci_hi - s.ci_lo) / 2) * 100)}`}
              </span>
            ))}
          </p>
          <ul className="mt-8 grid gap-2 text-[14px] text-ink-2 max-w-[64ch]">
            {ordered(res).filter((s) => s.count > 0).map((s) => (
              <li key={s.code}><span className="mono text-ink">{STORY_SHORT[s.code]}.</span> {s.evidence}</li>
            ))}
          </ul>
        </div>
        <div className="card p-5 sm:p-6 self-start">
          <Eyebrow className="mb-4">Context controls.</Eyebrow>
          <div className="grid gap-3">
            {CTX.map((c) => (
              <div key={c.id} className="flex items-center justify-between gap-3">
                <span className="mono text-[13px]">{c.label}</span>
                <span className="seg" role="group" aria-label={c.label}>
                  <button aria-pressed={on.includes(c.id)} onClick={() => set(c.id, true)}>on</button>
                  <button aria-pressed={!on.includes(c.id)} onClick={() => set(c.id, false)}>off</button>
                </span>
              </div>
            ))}
          </div>
          <div className="border-t border-line mt-6 pt-5">
            <Eyebrow>Residual.</Eyebrow>
            <div className="mono text-[64px] leading-[64px] tracking-[-0.04em] mt-2" aria-live="polite">{shown.toFixed(0)}%</div>
            <p className="text-[13px] text-ink-2 mt-2">
              <span className="mono text-ink">{fmt(res.residual.count)}</span> unexplained vs about{" "}
              <span className="mono text-ink">{fmt(res.residual.expected_background)}</span> expected background.
              {!offline && <> {res.residual.significant ? "Above" : "Within"} background, p = <span className="mono">{p < 0.001 ? "<0.001" : p.toFixed(3)}</span>.</>}
            </p>
            <div className="mt-4"><Chip kind={res.outcome} /></div>
            <p className="text-[13px] leading-5 text-ink-2 mt-3">{meaning(res)}</p>
            {offline && <p className="mono text-[11px] text-ink-3 mt-3">offline estimate · api not reachable</p>}
            {busy && !offline && <p className="mono text-[11px] text-ink-3 mt-3" aria-live="polite">estimate · engine confirming</p>}
          </div>
        </div>
      </div>
    </section>
  );
}

/** What the outcome chip means for this booth, in its own numbers. */
export function meaning(r: { outcome: string; stories: { code: string; label: string; share: number }[] }) {
  const top = r.stories.filter((s) => s.code !== "unexplained").sort((a, b) => b.share - a.share)[0];
  const lead = top && top.share > 0 ? `${Math.round(top.share * 100)}% match “${top.label.toLowerCase()}”` : "";
  if (r.outcome === "likely_benign")
    return `The removals are high, but a record explains them: ${lead}. What is left is no more than a normal booth loses. A person should still confirm.`;
  if (r.outcome === "mixed")
    return `No single record explains most removals, but together they do (${lead} is the largest). What is left is no more than a normal booth loses.`;
  if (r.outcome === "unusual")
    return "After every available record is checked, more names are left unexplained than a normal booth loses. A person should look at this booth.";
  return "Removals here are in line with a normal booth.";
}
