"use client";
import { useApi, pct } from "@/lib/api";
import type { EvalResult, RuleCard, GuardLog } from "@/lib/types";
import Glyph from "@/components/Glyph";
import { Display, Eyebrow } from "@/components/Display";

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
      {e ? (
        <Display size="hero" dim={`Decoys cleared ${e.decoys_cleared} of ${e.planted_decoys}. Missed ${e.misses.length}.`}>
          We found {e.found} of {e.planted_anomalies} hidden anomalies.
        </Display>
      ) : (
        <Display size="hero" dim="The scoreboard appears once the blind eval has run.">We publish what we miss.</Display>
      )}

      <section className="panel mt-16">
        <Eyebrow className="mb-5">Scoreboard.</Eyebrow>
        {e ? (
          <>
            <p className="mono text-[clamp(28px,5vw,56px)] leading-tight tracking-[-0.03em]">
              found {e.found} / {e.planted_anomalies} <span className="text-ink-3">·</span> decoys cleared {e.decoys_cleared} / {e.planted_decoys} <span className="text-ink-3">·</span> missed {e.misses.length}
            </p>
            {e.misses.length > 0 && (
              <ul className="card mt-6">
                {e.misses.map((m) => (
                  <li key={m.plant_id} className="px-5 py-3 border-t border-line first:border-t-0 grid sm:grid-cols-[220px_1fr] gap-1">
                    <span className="mono text-[13px] text-ink-2">{m.plant_id} · {m.type}</span><span className="text-[15px]">{m.why}</span>
                  </li>
                ))}
              </ul>
            )}
            <p className="mono text-[12px] text-ink-3 mt-4">benign false-positive rate {pct(e.benign_fp_rate, 1)}</p>
          </>
        ) : <Empty what="Blind eval" />}
      </section>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr] mt-6">
        <section className="panel">
          <Eyebrow className="mb-5">Reliability. When we say 80%, are we right 80% of the time.</Eyebrow>
          {e && e.reliability.length ? <Reliability bins={e.reliability} /> : <Empty what="Reliability" />}
        </section>
        <section className="panel">
          <Eyebrow className="mb-5">Neutrality guard.</Eyebrow>
          {guard.data ? (
            <>
              <p className="mono text-[64px] leading-[64px] tracking-[-0.04em]">{guard.data.checked}</p>
              <p className="text-[15px] text-ink-2 mt-3">outbound texts checked · <span className="mono text-ink">{guard.data.blocked}</span> blocked · <span className="mono text-ink">{guard.data.rewritten}</span> rewritten</p>
            </>
          ) : <Empty what="Guard log" />}
        </section>
      </div>

      <section className="panel mt-6">
        <Eyebrow className="mb-5">Rules, with how often they fire on innocent records.</Eyebrow>
        {rules.data && rules.data.length ? (
          <div className="card overflow-x-auto">
            <table className="tbl min-w-[560px]">
              <thead><tr><th>rule</th><th>what it checks</th><th className="r">fires on benign</th><th>resolves with</th></tr></thead>
              <tbody>
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
      </section>

      <section className="panel mt-6">
        <Eyebrow className="mb-5">Ops.</Eyebrow>
        {o ? (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
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
    </div>
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
  return `scale run · ${JSON.stringify(b)}`;
}

function Reliability({ bins }: { bins: EvalResult["reliability"] }) {
  const S = 260, P = 28, maxN = Math.max(...bins.map((b) => b.n), 1);
  const x = (v: number) => P + v * (S - P * 2), y = (v: number) => S - P - v * (S - P * 2);
  return (
    <div className="card p-4">
      <svg viewBox={`0 0 ${S} ${S}`} className="w-full max-w-[320px] mx-auto block" role="img" aria-label="Reliability: stated confidence against how often it was right">
        <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(0)} stroke="var(--color-line)" />
        <line x1={x(0)} y1={y(0)} x2={x(0)} y2={y(1)} stroke="var(--color-line)" />
        <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} stroke="var(--color-ink-3)" strokeDasharray="4 4" />
        {[0, 0.5, 1].map((t) => (
          <g key={t} fontFamily="var(--font-mono)" fontSize="10" fill="var(--color-ink-3)">
            <text x={x(t)} y={S - 8} textAnchor="middle">{t * 100}%</text>
            <text x={6} y={y(t) + 3}>{t * 100}</text>
          </g>
        ))}
        {bins.map((b, i) => <circle key={i} cx={x(b.mean_conf)} cy={y(b.frac_true)} r={3 + 7 * Math.sqrt(b.n / maxN)} fill="var(--color-ink)" />)}
      </svg>
      <p className="mono text-[11px] text-ink-3 text-center mt-2">stated confidence → share that were real · dot size = n</p>
    </div>
  );
}
