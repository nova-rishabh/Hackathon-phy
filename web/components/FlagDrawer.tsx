"use client";
import { useEffect, useState } from "react";
import type { Flag, StoryResult } from "@/lib/types";
import { API, fmt } from "@/lib/api";
import { Ctx, recompute } from "@/lib/stories";
import Stamp from "./Stamp";
import StoryBar from "./StoryBar";
import Glyph from "./Glyph";

const TYPE_LABEL: Record<string, string> = {
  deletion_spike: "Deletion spike", addition_spike: "Addition spike", duplicate_cluster: "Duplicate cluster",
  impossible_age: "Impossible age", relation_conflict: "Relation conflict", oversized_household: "Oversized household",
  gender_ratio_swing: "Gender-ratio swing",
};
const GLYPH: Record<string, string> = { deletion_spike: "rw-spike", addition_spike: "rw-spike", duplicate_cluster: "rw-twins", oversized_household: "rw-crowd", impossible_age: "rw-age" };
export const typeLabel = (t: string) => TYPE_LABEL[t] ?? t;
const MASKED = ["सु*** श*** · S*** S***", "सु*** शर्*** · S*** S***", "सु*** शा*** · S*** S***"];

export default function FlagDrawer({ flag, onClose }: { flag: Flag | null; onClose: () => void }) {
  const [res, setRes] = useState<StoryResult | null>(null);
  const [on, setOn] = useState<Ctx[]>([]);
  const [showQuery, setShowQuery] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setRes(flag?.stories ?? null);
    setOn((flag?.stories?.context_used as Ctx[]) ?? []);
    setShowQuery(false);
  }, [flag]);
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  if (!flag) return null;

  const toggle = async (c: Ctx) => {
    if (!flag.stories) return;
    const next = on.includes(c) ? on.filter((x) => x !== c) : [...on, c];
    setOn(next);
    setBusy(true);
    try {
      const ctl = new AbortController();
      const t = setTimeout(() => ctl.abort(), 2500);
      const r = await fetch(`${API}/stories/${flag.scope.booth_id}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ context_on: next }), signal: ctl.signal });
      clearTimeout(t);
      if (!r.ok) throw new Error("bad");
      setRes(await r.json());
    } catch {
      setRes(recompute(flag.stories, next));
    }
    setBusy(false);
  };

  const outcome = res?.outcome ?? (flag.likely_benign ? "likely_benign" : "unusual");
  const border = outcome === "likely_benign" ? "var(--color-benign)" : outcome === "mixed" ? "var(--color-rule-strong)" : "var(--color-unusual)";
  const c = flag.card;
  const rows: [string, string][] = c ? [
    ["What we found", c.found],
    ["Why it's unusual", c.why_unusual],
    ["Innocent explanations", c.innocent_explanations.join(" · ")],
    ["How sure", c.confidence_text],
  ] : [];
  const boothNo = Number(flag.scope.booth_id.replace(/\D/g, ""));

  return (
    <>
      <div className="fixed inset-0 bg-ink/10 z-30" onClick={onClose} aria-hidden />
      <aside role="dialog" aria-label={`Flag ${flag.flag_id}`} className="fixed right-0 top-0 bottom-0 w-full sm:w-[480px] bg-surface border-l border-rule-strong z-40 overflow-y-auto p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-2 overline"><Glyph id={GLYPH[flag.type] ?? "rw-tally"} size={18} />Booth {boothNo} · {typeLabel(flag.type)}</div>
          <button className="btn" onClick={onClose} style={{ height: 28, lineHeight: "26px", padding: "0 8px" }}>Close</button>
        </div>
        <div className="mb-4 flex gap-3 flex-wrap">
          <Stamp kind="review" />
          {outcome === "likely_benign" && <Stamp kind="benign" />}
        </div>
        <section className="border border-rule rounded-[4px] bg-surface" style={{ borderLeft: `4px solid ${border}` }}>
          {rows.map(([k, v]) => (
            <div key={k} className="grid grid-cols-[130px_1fr] gap-3 px-3 py-2 border-b border-rule text-[14px]">
              <div className="overline pt-[2px]">{k}</div>
              <div className="font-mono text-[13px] leading-5 tabular-nums">{v}</div>
            </div>
          ))}
          <div className="px-3 py-2 font-mono text-[12px] text-ink-3 flex justify-between">
            <span>flag {flag.flag_id}</span>
            <button className="text-voter-ink hover:underline" onClick={() => setShowQuery(!showQuery)}>View query</button>
          </div>
          {showQuery && (
            <pre className="bg-sunk px-3 py-2 font-mono text-[12px] leading-5 overflow-x-auto">{`observed = ${fmt(flag.metrics.observed)}  expected = ${flag.metrics.expected ?? "n/a"}  n = ${fmt(flag.metrics.n)}\np = ${flag.metrics.p_value ?? "n/a"}  q = ${flag.metrics.q_value ?? "n/a"}\nscope: ${flag.scope.level} ${flag.scope.booth_id}${flag.scope.house_no ? " house " + flag.scope.house_no : ""}`}</pre>
          )}
        </section>

        {flag.type === "duplicate_cluster" && (
          <section className="mt-6">
            <div className="overline mb-2">Three spellings · two scripts · names masked</div>
            <ul className="border border-rule">
              {MASKED.map((m, i) => (
                <li key={i} className="px-3 py-2 border-b border-rule last:border-b-0 text-[14px]" lang="hi">{m}</li>
              ))}
            </ul>
            <p className="text-[13px] text-ink-2 mt-2">Same relation, same house <span className="font-mono">{flag.scope.house_no}</span>. Flagged for review, never removed.</p>
          </section>
        )}

        {res && (
          <section className="mt-6">
            <StoryBar res={res} on={on} onToggle={toggle} busy={busy} />
          </section>
        )}
        {!res && flag.type !== "duplicate_cluster" && (
          <p className="mt-6 text-[13px] text-ink-2">No story attribution for this flag type.</p>
        )}
        <p className="mt-6 text-[12px] text-ink-3">A pattern for human review, not a finding. Confidence <span className="font-mono">{Math.round(flag.confidence * 100)}%</span> ({flag.confidence_band}).</p>
      </aside>
    </>
  );
}
