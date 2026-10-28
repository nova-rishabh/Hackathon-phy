"use client";
import { useEffect, useRef, useState } from "react";
import { getJson, useApi, fmt, pct, boothNo } from "@/lib/api";
import { Display, Eyebrow } from "./Display";
import Chip from "./Chip";
import Loader from "./Loader";

type Row = { booth_id: string; n: number; hidden: number; removed_before: number; removed_after: number;
  unexplained_after: number; expected: number; q_spike: number; q_residual: number; verdict: "caught" | "flagged" | "missed";
  verdict_before: "caught" | "flagged" | "missed" };
type Sim = { hidden_total: number; with_record: boolean; spread: number; booths: Row[]; caught: number; flagged: number; already_flagged: number;
  rank: number; n_booths: number; limit: number | null; alpha: number };
type Limits = { median: number | null; min: number | null; max: number | null; median_share_of_booth: number | null;
  by_booth: Record<string, number | null> };

const SPREAD: [number, string][] = [[1, "one booth"], [10, "10 booths"], [100, "every booth"]];
const MAX: Record<number, number> = { 1: 200, 10: 600, 100: 3000 };
const CHIP: Record<Row["verdict"], [string, string]> = {
  caught: ["review", "Caught · needs human review"],
  flagged: ["benign", "Flagged · not sent to review"],
  missed: ["unprovable", "Not caught"],
};
const qf = (q: number) => (q < 0.001 ? q.toExponential(1) : q.toFixed(3));

/**
 * "Try to fool RollWatch": hide removals in a booth and watch the engine's own tests rerun (GET /simulate).
 * Every number on this panel comes from the API; the page only lays it out.
 */
export default function FoolIt() {
  const lim = useApi<Limits>("/simulate/limits");
  const [booth, setBooth] = useState(23);
  const [k, setK] = useState(0);
  const [record, setRecord] = useState(false);
  const [spread, setSpread] = useState(1);
  const [sim, setSim] = useState<Sim | null>(null);
  const [busy, setBusy] = useState(false);
  const req = useRef(0);

  useEffect(() => {
    const id = ++req.current;
    setBusy(true);
    const t = setTimeout(async () => {
      const b = `B${String(booth).padStart(3, "0")}`;
      const r = await getJson<Sim>(`/simulate?booth=${b}&k=${k}&record=${record}&spread=${spread}`);
      if (id === req.current) { if (r.data) setSim(r.data); setBusy(false); }
    }, 140);
    return () => clearTimeout(t);
  }, [booth, k, record, spread]);

  const row = sim?.booths[0];
  const already = sim?.already_flagged ?? 0; // older API (mid-deploy) does not send it
  const max = spread === 1 && row ? Math.min(MAX[1], row.n - row.removed_before) : MAX[spread];
  const limit = sim?.limit ?? null;
  const L = lim.data;

  return (
    <section className="panel mt-6" aria-labelledby="fool-title">
      <Eyebrow className="mb-5">Try to fool it.</Eyebrow>
      <Display size="section" as="h2" dim="Pick a booth and how many names to take out with no record. The engine reruns the same tests it ran on the roll.">
        <span id="fool-title">Remove names quietly. See if we notice.</span>
      </Display>

      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)] mt-8">
        <div className="card p-5 sm:p-6 grid gap-6 content-start">
          <label className="grid gap-2">
            <span className="eyebrow">Booth.</span>
            <select className="input !py-3" value={booth} onChange={(e) => setBooth(Number(e.target.value))}>
              {Array.from({ length: 100 }, (_, i) => i + 1).map((n) => <option key={n} value={n}>Booth {n}</option>)}
            </select>
          </label>

          <div className="grid gap-2">
            <div className="flex items-baseline justify-between gap-3">
              <span className="eyebrow">Names to remove{spread > 1 ? ", in total" : ""}.</span>
              <span className="mono text-[32px] leading-none tracking-[-0.03em]">{fmt(k)}</span>
            </div>
            <input type="range" className="fool-range" min={0} max={max} value={Math.min(k, max)} onChange={(e) => setK(Number(e.target.value))}
              aria-label="Names to remove" />
            {spread === 1 && limit != null && limit > 0 && (
              <button className="mono text-[12px] text-ink-2 hover:text-ink underline underline-offset-2 justify-self-start"
                onClick={() => setK(limit - 1)}>try {limit - 1}, one name under this booth&apos;s limit</button>
            )}
          </div>

          <div className="grid gap-2">
            <span className="eyebrow">Cover story.</span>
            <div className="seg" role="group" aria-label="Cover story">
              <button aria-pressed={!record} onClick={() => setRecord(false)}>no record</button>
              <button aria-pressed={record} onClick={() => setRecord(true)}>fake death records</button>
            </div>
          </div>

          <div className="grid gap-2">
            <span className="eyebrow">Where.</span>
            <div className="seg" role="group" aria-label="Spread">
              {SPREAD.map(([v, l]) => (
                <button key={v} aria-pressed={spread === v} onClick={() => { setSpread(v); setK((x) => Math.min(x, MAX[v])); }}>{l}</button>
              ))}
            </div>
          </div>
        </div>

        <div className="card p-5 sm:p-6 min-h-[340px] flex flex-col" aria-live="polite">
          {!sim || !row ? <Loader label="running the tests" /> : (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                {spread === 1
                  ? <Chip kind={CHIP[row.verdict][0]} label={CHIP[row.verdict][1]} big />
                  : <Chip kind={sim.caught ? "review" : sim.flagged ? "benign" : "unprovable"} big
                      label={`${sim.caught} of ${sim.spread} booths caught`} />}
                <span className={`mono text-[12px] text-ink-3 transition-opacity ${busy ? "opacity-100" : "opacity-0"}`}>rerunning…</span>
              </div>

              {spread === 1 ? (
                <>
                  <p className="text-[22px] leading-8 tracking-[-0.02em] mt-5">
                    Booth {boothNo(row.booth_id)}: {fmt(row.removed_after)} removed against about {fmt(row.expected)} expected
                    <span className="text-ink-3">, {fmt(row.unexplained_after)} with no record.</span>
                  </p>
                  {limit != null && limit > 0 && <Meter k={k} limit={limit} max={max} caught={row.verdict === "caught"} />}
                  <p className="text-[15px] leading-6 text-ink-2 mt-4">{story(sim, row, k, record, limit)}</p>
                </>
              ) : (
                <>
                  <p className="text-[22px] leading-8 tracking-[-0.02em] mt-5">
                    {fmt(sim.hidden_total)} names over {sim.spread} booths<span className="text-ink-3">, about {fmt(row.hidden)} from each.</span>
                  </p>
                  <div className="fool-dots mt-5" aria-hidden="true">
                    {sim.booths.map((r) => <i key={r.booth_id} className={r.verdict === r.verdict_before && r.verdict !== "missed" ? "a" : r.verdict === "caught" ? "c" : r.verdict === "flagged" ? "f" : ""} />)}
                  </div>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 mono text-[11px] text-ink-2">
                    <span className="flex items-center gap-1.5"><i className="fool-key c" />sent to review {sim.caught}</span>
                    <span className="flex items-center gap-1.5"><i className="fool-key f" />spike shown only {sim.flagged - sim.caught}</span>
                    {already > 0 && <span className="flex items-center gap-1.5"><i className="fool-key a" />already flagged on the roll {already}</span>}
                    <span className="flex items-center gap-1.5"><i className="fool-key" />not noticed {sim.spread - sim.flagged - already}</span>
                  </div>
                  <p className="text-[15px] leading-6 text-ink-2 mt-4">
                    {sim.caught === sim.spread - already
                      ? "Every booth goes to a person for review."
                      : <>Spread thin, a few names a booth hide inside normal churn: {sim.spread - already - sim.caught} of {sim.spread - already} booths are not sent for review{sim.flagged > sim.caught ? `, though ${sim.flagged - sim.caught} show a small spike on the grid` : ""}. This is what booth-level tests cannot catch, and we say so here rather than hide it.</>}
                  </p>
                </>
              )}

              <p className="mono text-[12px] leading-5 text-ink-3 mt-auto pt-5">
                {spread === 1 ? <>spike test q {qf(row.q_spike)} · leftover test q {qf(row.q_residual)} · </> : null}
                one-sided binomial against the booth&apos;s age-adjusted background, Benjamini-Hochberg across {sim.n_booths} booths, review below q {sim.alpha}
              </p>
            </>
          )}
        </div>
      </div>

      {L && L.median != null && (
        <p className="mono text-[13px] text-ink-2 mt-4">
          smallest hidden removal that reaches review, per booth: median {fmt(L.median)} names
          {L.median_share_of_booth != null && <> (about {pct(L.median_share_of_booth, 0)} of a booth)</>}, from {fmt(L.min ?? 0)} to {fmt(L.max ?? 0)} · same tests as the engine, which flags the same booths on the real roll · synthetic data
        </p>
      )}
    </section>
  );
}

/** Where k sits against this booth's limit: the tick is the first number of names that is caught. */
function Meter({ k, limit, max, caught }: { k: number; limit: number; max: number; caught: boolean }) {
  const at = (v: number) => `${Math.min(100, (v / Math.max(max, 1)) * 100)}%`;
  return (
    <div className="mt-6" aria-hidden="true">
      <div className="relative h-3 rounded-[6px] bg-panel">
        <div className={`absolute inset-y-0 left-0 rounded-[6px] fool-fill ${caught ? "bg-signal" : "bg-ink-3"}`} style={{ width: at(k) }} />
        <div className="absolute -top-1.5 -bottom-1.5 w-[2px] bg-ink" style={{ left: `calc(${at(limit)} - 1px)` }} />
      </div>
      <div className="relative h-5 mt-1.5 mono text-[11px] text-ink-3">
        <span className="absolute -translate-x-1/2 whitespace-nowrap" style={{ left: at(limit) }}>caught from {limit}</span>
      </div>
    </div>
  );
}

function story(sim: Sim, row: Row, k: number, record: boolean, limit: number | null): string {
  const b = boothNo(row.booth_id);
  if (k === 0) return `This is Booth ${b} as it is on the roll. Move the slider to take names out.`;
  if (record && row.verdict !== "caught")
    return `The removal spike still shows on the grid, but the fake death records explain it, so the booth reads as likely innocent. That is why every flag lists the records it relied on: the evidence for Booth ${b} would show ${k} removals matched to the death register, for a person to check.`;
  if (row.verdict === "caught")
    return `Booth ${b} goes to a person for review: it is now number ${sim.rank} of ${sim.n_booths} booths by how unusual its leftover is.`;
  if (row.verdict === "flagged")
    return `The removal spike shows on the grid, but the leftover with no record is not unusual enough yet to send for review.${limit ? ` From ${limit} names it is.` : ""}`;
  return `Not enough to stand out from normal churn in a booth of ${fmt(row.n)} voters.${limit ? ` Catchable from ${limit} names.` : ""}`;
}
