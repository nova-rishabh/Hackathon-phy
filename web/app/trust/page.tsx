"use client";
import type { ReactNode } from "react";
import { useApi, pct } from "@/lib/api";
import { benchSummary, big } from "@/lib/bench";
import type { EvalResult, RuleCard, GuardLog } from "@/lib/types";
import Glyph from "@/components/Glyph";
import { Display, Eyebrow } from "@/components/Display";
import { CountUp, InView } from "@/components/Motion";

// /ops is not in contracts/api.md yet, so read it loosely.
type Ops = Record<string, unknown>;
const num = (o: Ops | null, ...keys: string[]) => {
  for (const k of keys) if (o && typeof o[k] === "number") return o[k] as number;
  return null;
};

const Empty = ({ what }: { what: string }) => <p className="text-ink-2 text-[15px]">{what} not computed yet.</p>;

export default function Trust() {
  const ev = useApi<EvalResult>("/eval");
  const rules = useApi<RuleCard[]>("/rules");
  const guard = useApi<GuardLog>("/guard/log");
  const ops = useApi<Ops>("/ops");
  const audit = useApi<{ ts: string; flag_id: string; action: string; hash: string }[]>("/audit/log");
  const blind = useApi<Blind>("/eval/blind");
  const b = blind.data?.eval;
  const e = ev.data;
  const o = ops.data;
  const bench = o?.bench as unknown;

  const opsCells: [string, string | null][] = [
    ["p50", fmtMs(num(o, "p50_ms", "p50"))],
    ["p95", fmtMs(num(o, "p95_ms", "p95"))],
    ["₹ per check", (() => { const v = num(o, "inr_per_check", "cost_inr_per_check", "rupees_per_check"); return v == null ? null : `₹${v.toFixed(2)}`; })()],
    ["cache hit", (() => { const v = num(o, "cache_hit_rate", "cache_hit"); return v == null ? null : pct(v); })()],
  ];

  return (
    <div>
      <Eyebrow className="mb-5 inline-flex items-center gap-2"><Glyph id="rw-tally" size={16} />Blind test.</Eyebrow>
      {b ? (
        <Display size="hero" dim={`Decoys cleared ${b.decoys_cleared} of ${b.planted_decoys}. Planted by a separate agent; we never saw the key.`}>
          We found {b.found} of {b.planted_anomalies} hidden anomalies.
        </Display>
      ) : e ? (
        <Display size="hero" dim={`Decoys cleared ${e.decoys_cleared} of ${e.planted_decoys}. Missed ${e.misses.length}.`}>
          We found {e.found} of {e.planted_anomalies} hidden anomalies.
        </Display>
      ) : (
        <Display size="hero" dim="The scoreboard appears once the blind eval has run.">We publish what we miss.</Display>
      )}

      {b && blind.data && (
        <section className="panel mt-16">
          <Eyebrow className="mb-5">Blind test scoreboard.</Eyebrow>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 stagger">
            {([
              [<CountUp key="f" to={b.found} suffix={`/${b.planted_anomalies}`} />, "hidden anomalies found"],
              [<CountUp key="d" to={b.decoys_cleared} suffix={`/${b.planted_decoys}`} />, "innocent decoys cleared"],
              [<CountUp key="m" to={b.misses.length} />, "missed"],
              [<CountUp key="w" to={Math.round(b.benign_fp_rate * 100)} suffix="%" />, "decoys wrongly flagged"],
            ] as const).map(([v, k]) => (
              <div key={k} className="card px-5 py-4">
                <p className="mono text-[32px] leading-[40px] tracking-[-0.03em]">{v}</p>
                <p className="text-[13px] text-ink-2 mt-1">{k}</p>
              </div>
            ))}
          </div>
          <div className="grid gap-3 lg:grid-cols-[3fr_2fr] mt-3">
            <Reliability bins={b.reliability} />
            <div className="card p-5">
              <p className="eyebrow mb-3">Rules on the blind district.</p>
              <ul className="stagger">
                {blind.data.rules.map((r) => (
                  <li key={r.rule} className="flex justify-between gap-3 py-1.5 border-t border-line first:border-t-0 text-[14px]">
                    <span className="mono text-[13px]">{r.rule}</span>
                    <span className="mono text-ink-2">{r.raised} raised · {pct(r.false_positive_rate ?? 0, 1)} false</span>
                  </li>
                ))}
              </ul>
              <p className="text-[13px] text-ink-2 mt-3">Weakest spot: impossible-relation checks, about a quarter of which fire on innocent records here. Every flag still goes to a person.</p>
            </div>
          </div>
          {blind.data.false_alarms && <FalseAlarms f={blind.data.false_alarms} noMisses={b.misses.length === 0} />}
          <p className="text-[13px] text-ink-2 mt-4 max-w-[80ch]">
            A separate AI agent wrote the plantings (anomalies and innocent look-alikes) for a fresh district and kept the answer key private. The engine was calibrated only on {blind.data.calibration}, and never saw the key; only this scoreboard was published.
          </p>
        </section>
      )}

      <section className={`panel ${b ? "mt-6" : "mt-16"}`}>
        <Eyebrow className="mb-5">{b ? "Demo district scoreboard (we planted it)." : "Scoreboard."}</Eyebrow>
        {e ? (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 stagger">
              {([
                [<CountUp key="f" to={e.found} suffix={`/${e.planted_anomalies}`} />, "hidden anomalies found"],
                [<CountUp key="d" to={e.decoys_cleared} suffix={`/${e.planted_decoys}`} />, "innocent decoys cleared"],
                [<CountUp key="m" to={e.misses.length} />, "missed"],
                [<CountUp key="w" to={Math.round(e.benign_fp_rate * 100)} suffix="%" />, "decoys wrongly flagged"],
              ] as const).map(([v, k]) => (
                <div key={k} className="card px-5 py-4">
                  <p className="mono text-[32px] leading-[40px] tracking-[-0.03em]">{v}</p>
                  <p className="text-[13px] text-ink-2 mt-1">{k}</p>
                </div>
              ))}
            </div>
            {e.misses.length > 0 && (
              <ul className="card mt-3">
                {e.misses.map((m) => (
                  <li key={m.plant_id} className="px-5 py-3 border-t border-line first:border-t-0 grid sm:grid-cols-[220px_1fr] gap-1">
                    <span className="mono text-[13px] text-ink-2">{m.plant_id} · {m.type}</span><span className="text-[15px]">{m.why}</span>
                  </li>
                ))}
              </ul>
            )}
            <p className="text-[13px] text-ink-2 mt-4 max-w-[70ch]">
              We plant anomalies and innocent look-alikes (deaths, hostel move-outs, boundary moves) in a synthetic district. The engine never reads the answer key; only the scorer does.
            </p>
          </>
        ) : <Empty what="Blind eval" />}
      </section>

      <div className="grid gap-6 lg:grid-cols-[3fr_2fr] mt-6">
        <section className="panel">
          <Eyebrow className="mb-5">Reliability. When we say 90%, are we right 90% of the time.</Eyebrow>
          {e && e.reliability.length ? <Reliability bins={e.reliability} /> : <Empty what="Reliability" />}
        </section>
        <section className="panel flex flex-col">
          <Eyebrow className="mb-5">Neutrality guard.</Eyebrow>
          {guard.data ? <Guard g={guard.data} /> : <Empty what="Guard log" />}
        </section>
      </div>

      <section className="panel mt-6">
        <Eyebrow className="mb-5">Rules, with how often they fire on innocent records.</Eyebrow>
        {rules.data && rules.data.length ? (
          <div className="card overflow-x-auto">
            <table className="tbl min-w-[560px]">
              <thead><tr><th>rule</th><th>what it checks</th><th className="r">fires on benign</th><th>resolves with</th></tr></thead>
              <tbody className="stagger">
                {rules.data.map((r) => (
                  <tr key={r.rule_id}>
                    <td className="mono text-[13px]">{r.rule_id}</td>
                    <td>{r.what}</td>
                    <td className="r mono">{pct(r.fires_on_benign_rate, 1)}</td>
                    <td className="text-ink-2">{r.resolves_with}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <Empty what="Rule error rates" />}
        <p className="text-[13px] text-ink-2 mt-4 max-w-[75ch]">
          Rows starting <span className="mono">official_</span> are the &ldquo;logical discrepancy&rdquo; checks reported for the 2025&ndash;26 revision (parent gap under 15 or over 50 years, six or more children, names or relation changed since the last roll, age not progressing). We run them and never raise them as flags: marriages, spelling fixes and large families trip them innocently. Sibling gaps under 9 months can&apos;t be checked from a roll, which carries ages in years. Rates here are on synthetic data.
        </p>
        <p className="mono text-[12px] text-ink-3 mt-3">
          human reviews recorded {audit.data?.length ?? 0}
          {audit.data && audit.data.length > 0 && <> · last {audit.data[audit.data.length - 1].action.replace("review:", "")} · chain head {audit.data[audit.data.length - 1].hash.slice(0, 10)}</>}
          {" "}· each review is hash-chained to the one before, so an edit breaks the chain
        </p>
      </section>

      <section className="panel mt-6">
        <Eyebrow className="mb-5">Ops.</Eyebrow>
        {o ? (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 stagger">
              {opsCells.map(([k, v]) => (
                <div key={k} className="card p-5">
                  <p className="eyebrow">{k}.</p>
                  <p className="mono text-[36px] leading-[44px] tracking-[-0.03em] mt-2">{v ?? <span className="text-ink-3 text-[15px]">not computed yet</span>}</p>
                </div>
              ))}
            </div>
            <p className="mono text-[13px] text-ink-2 mt-4">{benchLine(bench)}</p>
          </>
        ) : <Empty what="Ops numbers" />}
      </section>

      <Scale o={o} />

      <section className="panel mt-6">
        <Eyebrow className="mb-5">Why statistics, not a black box.</Eyebrow>
        <div className="grid gap-3 md:grid-cols-3 stagger">
          {([
            ["No answer key exists.", "Nobody has a labelled record of real wrongful deletions to train a large model on. A booth-level test needs none, and our confidence is calibrated on districts where the answer is known."],
            ["A notice must say why.", "“412 removed against about 25 expected; 10 match the death register; 401 match no record” can be checked and contested. A model score cannot."],
            ["Machine learning where it fits.", "Calibrated confidence, cross-script name matching and the language model are learned. The decision about a voter stays explainable."],
          ] as const).map(([h, b]) => (
            <div key={h} className="card p-5">
              <p className="text-[20px] leading-7 tracking-[-0.02em]">{h}</p>
              <p className="text-[14px] leading-6 text-ink-2 mt-2">{b}</p>
            </div>
          ))}
        </div>
        <p className="text-[13px] text-ink-2 mt-4 max-w-[80ch]">
          Research on monitoring voter-file changes found statistical models comparing districts over short spans worked best, and labelled each change&apos;s likely cause, as we do here.{" "}
          <a className="underline underline-offset-2 hover:text-ink" href="https://arxiv.org/abs/2106.15285" target="_blank" rel="noreferrer">Royston et al., 2021</a>.
        </p>
      </section>
    </div>
  );
}

type FalseAlarmStats = { flags_total: number; raised: number; raised_real: number; raised_false: number;
  real_share: number | null; cleared_likely_benign: number; cleared_on_planted_decoy: number; high_conf_flags: number;
  high_conf_real_share: number | null; by_rule: { rule: string; raised: number; false: number }[]; booth_spike_false: number };
type Blind = { eval: EvalResult; rules: { rule: string; raised: number; false_positive_rate: number | null }[];
  false_alarms?: FalseAlarmStats; planted_by: string; calibration: string };

const RULE_WORDS: Record<string, string> = {
  duplicate_cluster: "duplicate pairs", relation_conflict: "relation conflicts", impossible_age: "impossible ages",
  oversized_household: "oversized households", gender_ratio_swing: "gender swings",
  deletion_spike: "removal spikes", addition_spike: "addition spikes",
};

/** How many flags sent to a person were wrong. Counts come from the API (/eval/blind: false_alarms). */
function FalseAlarms({ f, noMisses }: { f: FalseAlarmStats; noMisses: boolean }) {
  const wrong = f.by_rule.filter((r) => r.false > 0);
  const cells: [ReactNode, string][] = [
    [<CountUp key="r" to={Math.round((f.real_share ?? 0) * 100)} suffix="%" />,
      `of the ${f.raised} flags raised for review were real (${f.raised_real}); ${f.raised_false} were false alarms.`],
    [<CountUp key="s" to={f.booth_spike_false} />,
      "false alarms on booth removal or addition spikes, the flags a rumour is built on."],
    [<CountUp key="c" to={f.cleared_likely_benign} />,
      `flags the engine marked likely innocent itself (deaths, hostels, large families)${noMisses ? "; none of them hid a planted anomaly" : ""}.`],
  ];
  return (
    <div className="card p-5 mt-3">
      <p className="eyebrow mb-4">False alarms, counted.</p>
      <div className="grid gap-x-6 gap-y-5 md:grid-cols-3 stagger">
        {cells.map(([v, k], i) => (
          <div key={i}>
            <p className="mono text-[32px] leading-[40px] tracking-[-0.03em]">{v}</p>
            <p className="text-[14px] leading-6 text-ink-2 mt-1">{k}</p>
          </div>
        ))}
      </div>
      {wrong.length > 0 && (
        <p className="text-[13px] text-ink-2 mt-5 pt-4 border-t border-line">
          The {f.raised_false} false alarms are all record-level:{" "}
          {wrong.map((r) => `${r.false} ${RULE_WORDS[r.rule] ?? r.rule.replace(/_/g, " ")}`).join(", ")}.
          {f.high_conf_real_share != null && <> At high confidence ({f.high_conf_flags} flags), {Math.round(f.high_conf_real_share * 100)}% were real.</>}
          {" "}Every flag goes to a person; none becomes a notice on its own.
        </p>
      )}
    </div>
  );
}
type Proj = { electors: number; electors_source: string; audit_core_hours: number; audit_minutes_on_64_cores: number;
  checks_per_day: number; checks_per_s_avg: number; checks_per_s_peak: number; citizen_answers_per_s_4proc: number | null;
  machines_at_peak: number | null; assumption: { share_checking: number; window_days: number; peak_factor: number };
  states?: Record<string, string | number>[]; state_cores?: number };
type Load = { routes: Record<string, { rps: number; p50_ms: number }> };

/** National scale: every number here is computed by the API (/ops: projection, loadtest) from measured runs. */
function Scale({ o }: { o: Ops | null }) {
  const p = o?.projection as Proj | undefined, lt = o?.loadtest as Record<string, Load> | undefined;
  if (!p) return null;
  const crore = (n: number) => `${(n / 1e7).toLocaleString("en-IN", { maximumFractionDigits: 1 })} crore`;
  const lakh = (n: number) => `${(n / 1e5).toLocaleString("en-IN", { maximumFractionDigits: 0 })} lakh`;
  const routes = lt?.["1"] ? Object.keys(lt["1"].routes) : [];
  return (
    <section className="panel mt-6">
      <Eyebrow className="mb-5">At national scale.</Eyebrow>
      <div className="grid gap-3 md:grid-cols-3 stagger">
        <div className="card p-5">
          <p className="mono text-[40px] leading-[48px] tracking-[-0.04em]"><CountUp to={p.audit_minutes_on_64_cores} decimals={1} suffix=" min" /></p>
          <p className="text-[14px] leading-6 text-ink-2 mt-2">to audit all {crore(p.electors)} electors on 64 cores ({p.audit_core_hours} core-hours), each constituency an independent job.</p>
        </div>
        <div className="card p-5">
          <p className="mono text-[40px] leading-[48px] tracking-[-0.04em]"><CountUp to={p.checks_per_s_peak} suffix="/s" /></p>
          <p className="text-[14px] leading-6 text-ink-2 mt-2">peak checks if {Math.round(p.assumption.share_checking * 100)}% of voters check once in {p.assumption.window_days} days ({lakh(p.checks_per_day)} a day, {p.assumption.peak_factor}× peak).</p>
        </div>
        <div className="card p-5">
          <p className="mono text-[40px] leading-[48px] tracking-[-0.04em]"><CountUp to={p.machines_at_peak ?? 0} suffix={p.machines_at_peak === 1 ? " machine" : " machines"} /></p>
          <p className="text-[14px] leading-6 text-ink-2 mt-2">cover that peak at our measured {p.citizen_answers_per_s_4proc} full answers a second per 4-process laptop, before any CDN or claim cache.</p>
        </div>
      </div>
      {routes.length > 0 && (
        <div className="card overflow-x-auto mt-3">
          <table className="tbl min-w-[520px]">
            <thead><tr><th>measured on one laptop</th><th className="r">1 process</th><th className="r">4 processes</th></tr></thead>
            <tbody className="stagger">
              {routes.map((r) => (
                <tr key={r}><td>{r}</td>
                  <td className="r mono">{lt?.["1"]?.routes[r]?.rps} /s</td>
                  <td className="r mono">{lt?.["4"]?.routes[r]?.rps ?? "–"} /s</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {p.states && p.states.length > 0 && (
        <div className="card overflow-x-auto mt-3">
          <table className="tbl min-w-[520px]">
            <thead><tr><th>largest states</th><th className="r">electors</th><th className="r">audit on one {p.state_cores}-core server</th></tr></thead>
            <tbody className="stagger">
              {p.states.slice(0, 6).map((s) => (
                <tr key={String(s.state)}><td>{s.state}</td>
                  <td className="r mono">{crore(Number(s.electors))}</td>
                  <td className="r mono">{s[`minutes_on_${p.state_cores}_cores`]} min</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="mono text-[12px] text-ink-3 mt-3">{p.electors_source} · offline mode, one test client (lower bounds) · audit assumes independent constituency jobs</p>
    </section>
  );
}

function fmtMs(v: number | null) {
  if (v == null) return null;
  return v >= 1000 ? `${(v / 1000).toFixed(1)}s` : `${Math.round(v)}ms`;
}

function benchLine(b: unknown) {
  if (!b) return "scale run not computed yet";
  if (typeof b === "string") return b;
  const o = b as Record<string, number>;
  const voters = o.voters ?? o.n_voters, secs = o.seconds ?? o.runtime_s ?? (o.runtime_ms != null ? o.runtime_ms / 1000 : undefined);
  if (voters != null && secs != null) return `scale run · ${voters.toLocaleString("en-IN")} voters in ${secs.toFixed(1)}s`;
  const s = benchSummary(b);
  if (!s) return "scale run not computed yet";
  return `scale run · ${s.voters.toLocaleString("en-IN")} voters in ${s.secs.toFixed(1)}s on one core` +
    (s.base ? ` (${s.base.voters.toLocaleString("en-IN")} in ${s.base.secs.toFixed(1)}s)` : "") +
    ` · duplicate check compares ${big(s.pairs)} pairs, not ${big(s.naive)}`;
}

const BINS = [[0, 0.25], [0.25, 0.5], [0.5, 0.75], [0.75, 1]] as const;

/** One row per confidence band: where we said we'd be (tick) against how often flags were real (bar). */
function Reliability({ bins }: { bins: EvalResult["reliability"] }) {
  const pc = (v: number) => `${Math.round(v * 100)}%`;
  return (
    <InView className="card p-5">
      <div className="grid grid-cols-[72px_1fr_88px] gap-x-4 text-[12px] mono text-ink-3 pb-3 border-b border-line">
        <span>we said</span><span>share that were real</span><span className="text-right">flags</span>
      </div>
      {BINS.map(([lo, hi]) => {
        const b = bins.find((x) => Math.abs(x.bin_lo - lo) < 1e-6);
        return (
          <div key={lo} className="grid grid-cols-[72px_1fr_88px] gap-x-4 items-center py-3 border-b border-line last:border-b-0">
            <span className="mono text-[13px]">{lo * 100}–{hi * 100}%</span>
            {b ? (
              <div className="relative h-6 rounded-[6px] bg-panel" aria-label={`said ${pc(b.mean_conf)}, real ${pc(b.frac_true)}`}>
                <div className="absolute inset-y-0 left-0 rounded-[6px] bg-ink grow-in-view" style={{ width: `max(${b.frac_true * 100}%, 2px)` }} />
                <div className="absolute -top-1 -bottom-1 w-[2px] bg-ink-3" style={{ left: `calc(${b.mean_conf * 100}% - 1px)` }} />
                <span className="absolute inset-y-0 flex items-center mono text-[12px]"
                  style={b.frac_true > 0.7 ? { right: `calc(${100 - b.frac_true * 100}% + 8px)`, color: "var(--color-surface)" } : { left: `calc(${b.frac_true * 100}% + 8px)` }}>
                  {pc(b.frac_true)}
                </span>
              </div>
            ) : <span className="text-[13px] text-ink-3">no flags in this band</span>}
            <span className="mono text-[13px] text-right">{b ? b.n.toLocaleString("en-IN") : "0"}</span>
          </div>
        );
      })}
      <p className="text-[13px] text-ink-2 mt-4">Bar: share of flags that matched a planted anomaly. Line: the confidence we stated. Bar ending near the line means the number can be taken at face value.</p>
    </InView>
  );
}

const GUARD_RULES = [
  ["fraud or rigging words", "blocked"],
  ["party names", "blocked"],
  ["public-figure names", "blocked"],
  ["institution names", "blocked"],
  ["religion, caste or community", "never inferred, blocked"],
] as const;

function Guard({ g }: { g: GuardLog }) {
  const surfaces = Object.entries(g.items.reduce<Record<string, number>>((a, i) => ({ ...a, [String(i.surface)]: (a[String(i.surface)] ?? 0) + 1 }), {}));
  return (
    <>
      <div className="flex items-baseline gap-3">
        <p className="mono text-[56px] leading-[56px] tracking-[-0.04em]">{g.checked}</p>
        <p className="text-[15px] text-ink-2">outbound texts checked since start</p>
      </div>
      <p className="mono text-[13px] text-ink-2 mt-3">
        <span className="text-ink">{g.blocked}</span> blocked · <span className="text-ink">{g.rewritten}</span> rewritten
        {surfaces.length > 0 && <> · {surfaces.map(([k, n]) => `${k.replace(/_/g, " ")} ${n}`).join(" · ")}</>}
      </p>
      <ul className="card mt-5 stagger">
        {GUARD_RULES.map(([what, act]) => (
          <li key={what} className="flex justify-between gap-4 px-4 py-[10px] border-t border-line first:border-t-0 text-[14px]">
            <span>{what}</span><span className="mono text-[12px] text-ink-2 pt-[2px] text-right">{act}</span>
          </li>
        ))}
      </ul>
      <p className="text-[13px] text-ink-2 mt-4">Every answer, chat reply and claim verdict passes this check before it leaves. If a model phrasing fails, a fixed template is sent instead.</p>
    </>
  );
}
