"use client";
// Run the open engine on your own two roll versions (POST /audit, PRD M12): the "inside" path, where an office
// checks a draft before publishing. Files never leave the request; nothing is stored.
import { useState } from "react";
import { postJson, fmt, boothNo } from "@/lib/api";
import type { Flag, StoryResult } from "@/lib/types";
import Chip from "@/components/Chip";
import { StoryBar, meaning } from "@/components/StoryPanel";
import { Display, Eyebrow } from "@/components/Display";

type Audit = { flags: Flag[]; stories: StoryResult[]; by_type: Record<string, number>; flags_total: number; runtime_ms: number };
const FILES = [
  ["roll_v1", "Old roll", true],
  ["roll_v2", "New roll", true],
  ["death_register", "Death register", false],
  ["hostel_list", "Hostel list", false],
  ["boundary_changes", "Boundary changes", false],
] as const;
type Key = (typeof FILES)[number][0];
const TYPE: Record<string, string> = {
  deletion_spike: "removal spike", addition_spike: "addition spike", duplicate_cluster: "duplicate", impossible_age: "impossible age",
  oversized_household: "oversized house", gender_ratio_swing: "gender share swing", relation_conflict: "impossible relation",
};

export default function Run() {
  const [files, setFiles] = useState<Partial<Record<Key, { name: string; text: string }>>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [res, setRes] = useState<Audit | null>(null);

  const pick = async (k: Key, f: File | undefined) => {
    if (!f) return;
    const text = await f.text();
    setFiles((s) => ({ ...s, [k]: { name: f.name, text } }));
  };
  const sample = async () => {
    setErr("");
    const got = await Promise.all(FILES.map(async ([k]) => [k, await (await fetch(`/sample/${k}.csv`)).text()] as const));
    setFiles(Object.fromEntries(got.map(([k, text]) => [k, { name: `sample ${k}.csv`, text }])));
  };
  const run = async () => {
    if (!files.roll_v1?.text || !files.roll_v2?.text) return setErr("Add both roll versions first.");
    setBusy(true); setErr(""); setRes(null);
    try {
      const body: Record<string, string> = { roll_v1_csv: files.roll_v1.text, roll_v2_csv: files.roll_v2.text };
      for (const k of ["death_register", "hostel_list", "boundary_changes"] as const) if (files[k]?.text) body[`${k}_csv`] = files[k]!.text;
      setRes(await postJson<Audit>("/audit", body, 120000));
    } catch (e) {
      setErr(String(e instanceof Error ? e.message : e).includes("422") ? "The files don't match the open roll schema. Start from the sample to see the columns." : "The audit did not finish. Try again in a minute.");
    } finally { setBusy(false); }
  };

  const spiked = new Set(res?.flags.filter((f) => f.type === "deletion_spike").map((f) => f.scope.booth_id));
  const booths = res ? res.stories.filter((s) => spiked.has(s.booth_id))
    .sort((a, b) => (a.outcome === "unusual" ? 0 : 1) - (b.outcome === "unusual" ? 0 : 1) || b.removed_total - a.removed_total).slice(0, 8) : [];
  const raised = res ? res.flags.filter((f) => !f.likely_benign) : [];

  return (
    <div>
      <Eyebrow className="mb-5">Run it yourself.</Eyebrow>
      <Display size="hero" dim="Before a revised list is published, check which changes no record explains.">Audit your own roll.</Display>

      <section className="panel mt-16">
        <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
          <div className="card p-5 sm:p-6">
            <Eyebrow className="mb-4">Your files.</Eyebrow>
            <ul className="grid gap-2">
              {FILES.map(([k, label, req]) => (
                <li key={k} className="grid grid-cols-[150px_1fr] gap-3 items-center py-2 border-t border-line first:border-t-0">
                  <span className="text-[15px]">{label}{!req && <span className="text-ink-3"> · optional</span>}</span>
                  <label className="flex items-center gap-3 min-w-0 cursor-pointer">
                    <span className="btn btn--quiet shrink-0">{files[k] ? "Replace" : "Choose CSV"}</span>
                    <span className="mono text-[12px] text-ink-2 truncate">{files[k]?.name ?? "none"}</span>
                    <input type="file" accept=".csv,text/csv" className="sr-only" onChange={(e) => pick(k, e.target.files?.[0])} />
                  </label>
                </li>
              ))}
            </ul>
            <div className="flex flex-wrap items-center gap-3 mt-5">
              <button className="btn" disabled={busy} onClick={run}>{busy ? "Running the engine…" : "Run the audit"}</button>
              <button className="btn btn--quiet" disabled={busy} onClick={sample}>Use the sample (10 booths)</button>
              {err && <span className="text-[14px] text-ink-2">{err}</span>}
            </div>
          </div>
          <div className="text-[14px] leading-6 text-ink-2 grid content-start gap-3">
            <p>Same open engine as the public audit: binomial test per booth with Benjamini-Hochberg, which-story-fits, cross-script duplicates and the rule checks.</p>
            <p>Columns follow the open roll schema (<a className="underline underline-offset-2 hover:text-ink" href="/sample/roll_v1.csv" download>see the sample</a>). Files are used for this one run and not stored.</p>
            <p className="mono text-[12px] text-ink-3">synthetic sample · booths 41–50 of Sampleabad</p>
          </div>
        </div>
      </section>

      {res && (
        <section className="mt-16">
          <Display size="page" as="h2" dim={`${fmt(res.flags_total)} patterns found in ${(res.runtime_ms / 1000).toFixed(1)} s; ${fmt(res.flags_total - raised.length)} explained by a record.`}>
            {raised.length} need human review.
          </Display>
          <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr] mt-8">
            <div className="panel">
              <Eyebrow className="mb-5">Booths with unusual removals.</Eyebrow>
              {booths.length ? (
                <ul className="grid gap-3 stagger">
                  {booths.map((s) => (
                    <li key={s.booth_id} className="card p-5">
                      <div className="flex items-center justify-between gap-3 mb-3">
                        <span className="text-[18px] tracking-[-0.02em]">Booth {boothNo(s.booth_id)} <span className="text-ink-3">· {fmt(s.removed_total)} removed</span></span>
                        <Chip kind={s.outcome} />
                      </div>
                      <StoryBar res={s} mini />
                      <p className="text-[13px] leading-5 text-ink-2 mt-3">{meaning(s)}</p>
                    </li>
                  ))}
                </ul>
              ) : <p className="text-[15px] text-ink-2">No booth lost more names than its age mix explains.</p>}
            </div>
            <div className="panel">
              <Eyebrow className="mb-5">All patterns, by rule.</Eyebrow>
              <ul className="card stagger">
                {Object.entries(res.by_type).sort((a, b) => b[1] - a[1]).map(([t, n]) => (
                  <li key={t} className="flex justify-between px-4 py-3 border-t border-line first:border-t-0 text-[15px]">
                    <span>{TYPE[t] ?? t.replace(/_/g, " ")}</span><span className="mono">{fmt(n)}</span>
                  </li>
                ))}
              </ul>
              <p className="text-[13px] text-ink-2 mt-4">Error rates for each rule are published on the Trust page. Every pattern is for human review, not a finding.</p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
