"use client";
import { useEffect, useState } from "react";
import type { Flag } from "@/lib/types";
import { fmt, boothNo } from "@/lib/api";
import Chip from "./Chip";
import Glyph from "./Glyph";
import { StoryBar } from "./StoryPanel";

const TYPE_LABEL: Record<string, string> = {
  deletion_spike: "Deletion spike", addition_spike: "Addition spike", duplicate_cluster: "Duplicate cluster",
  impossible_age: "Impossible age", relation_conflict: "Relation conflict", oversized_household: "Oversized household",
  gender_ratio_swing: "Gender-ratio swing",
};
const GLYPH: Record<string, string> = { deletion_spike: "rw-spike", addition_spike: "rw-spike", duplicate_cluster: "rw-twins", oversized_household: "rw-crowd", impossible_age: "rw-age" };
export const typeLabel = (t: string) => TYPE_LABEL[t] ?? t;
export const flagKind = (f: Flag) => (f.likely_benign ? "likely_benign" : f.stories?.outcome === "mixed" ? "mixed" : "unusual");
const MASKED = ["सु*** श*** · S*** S***", "सु*** शर्*** · S*** S***", "सु*** शा*** · S*** S***"];

export default function FlagDrawer({ flag, onClose }: { flag: Flag | null; onClose: () => void }) {
  const [q, setQ] = useState(false);
  useEffect(() => setQ(false), [flag]);
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", k);
    return () => window.removeEventListener("keydown", k);
  }, [onClose]);
  if (!flag) return null;
  const c = flag.card;
  const rows: [string, string][] = c ? [
    ["what we found.", c.found],
    ["why it's unusual.", c.why_unusual],
    ["innocent explanations checked.", c.innocent_explanations.join(" · ")],
    ["how sure.", c.confidence_text],
  ] : [];
  const m = flag.metrics;
  return (
    <>
      <div className="scrim" onClick={onClose} aria-hidden />
      <aside role="dialog" aria-modal="true" aria-label={`Flag ${flag.flag_id}`} className="drawer">
        <div className="flex justify-between items-center mb-8">
          <span className="eyebrow inline-flex items-center gap-2">
            <Glyph id={GLYPH[flag.type] ?? "rw-tally"} size={18} />Booth {boothNo(flag.scope.booth_id)} · {typeLabel(flag.type).toLowerCase()}.
          </span>
          <button className="btn btn--quiet" onClick={onClose}>Close</button>
        </div>
        <p className="display h-section mb-8">
          {fmt(m.observed)} {m.unit}{m.expected != null && <> <span className="dim">against about {fmt(m.expected)} expected.</span></>}
        </p>
        <div className="panel" style={{ padding: 12, borderRadius: 20 }}>
          <div className="card p-5">
            <div className="flex justify-end mb-2"><Chip kind={flagKind(flag)} /></div>
            {rows.length ? rows.map(([k, v]) => (
              <div key={k} className="grid sm:grid-cols-[150px_1fr] gap-1 sm:gap-4 py-3 border-t border-line first:border-t-0">
                <span className="eyebrow">{k}</span>
                <span className="text-[15px] leading-6">{v}</span>
              </div>
            )) : <p className="text-ink-2 text-[14px]">No explanation card for this flag yet.</p>}
            <div className="mono text-[12px] text-ink-3 pt-4 mt-2 border-t border-line">
              flag {flag.flag_id.slice(0, 8)} ·{" "}
              <button className="underline underline-offset-2 hover:text-ink" onClick={() => setQ(!q)}>{q ? "hide query" : "view query"}</button>
            </div>
            {q && (
              <pre className="mono text-[12px] leading-5 bg-page rounded-[8px] p-3 mt-3 whitespace-pre-wrap">
                {`observed = ${fmt(m.observed)}   expected = ${m.expected ?? "n/a"}   n = ${fmt(m.n)}\np = ${m.p_value ?? "n/a"}   q = ${m.q_value ?? "n/a"}   (binomial, BH-corrected)\nscope: ${flag.scope.level} ${flag.scope.booth_id}${flag.scope.house_no ? " house " + flag.scope.house_no : ""}`}
              </pre>
            )}
          </div>
        </div>
        {flag.type === "duplicate_cluster" && (
          <section className="mt-8">
            <p className="eyebrow mb-3">Three spellings, two scripts. Names masked.</p>
            <ul className="card border border-line">
              {MASKED.map((x, i) => <li key={i} lang="hi" className="px-4 py-3 border-t border-line first:border-t-0">{x}</li>)}
            </ul>
            <p className="text-[13px] text-ink-2 mt-3">Same relation, same house <span className="mono">{flag.scope.house_no}</span>. Flagged for review, never removed.</p>
          </section>
        )}
        {flag.stories && (
          <section className="mt-8">
            <p className="eyebrow mb-3">Which story fits.</p>
            <StoryBar res={flag.stories} />
            <p className="text-[13px] text-ink-2 mt-3">Switch evidence sources on and off in the panel under the grid.</p>
          </section>
        )}
        <p className="mono text-[12px] text-ink-3 mt-8">
          needs human review · confidence {Math.round(flag.confidence * 100)}% ({flag.confidence_band}, n = {flag.confidence_n})
        </p>
      </aside>
    </>
  );
}
