"use client";
import { useState } from "react";
import { useApi, fmt, pct } from "@/lib/api";
import { OVERVIEW_MOCK, FLAGS_MOCK } from "@/components/data";
import type { BoothSummary, Flag } from "@/lib/types";
import FlagDrawer from "@/components/FlagDrawer";

const TILE: Record<string, string> = { normal: "", unusual: "tile--unusual", likely_benign: "tile--benign", mixed: "tile--mixed" };
const OUT_LABEL: Record<string, string> = { normal: "Neutral", unusual: "Unusual, needs human review", likely_benign: "Likely benign", mixed: "Mixed" };

export default function Overview() {
  const ov = useApi("/overview", OVERVIEW_MOCK);
  const fl = useApi("/flags", FLAGS_MOCK);
  const [open, setOpen] = useState<Flag | null>(null);
  const [hover, setHover] = useState<BoothSummary | null>(null);
  const [msg, setMsg] = useState("");
  const d = ov.data;
  if (!d) return <p className="text-ink-2">Loading roll comparison…</p>;
  const t = d.totals;
  const click = (b: BoothSummary) => {
    const items = fl.data?.items ?? [];
    const f = items.find((x) => x.scope.booth_id === b.booth_id && x.stories) ?? items.find((x) => x.scope.booth_id === b.booth_id);
    if (f) { setOpen(f); setMsg(""); } else setMsg(`No flags in booth ${Number(b.booth_id.slice(1))}. That's normal for most booths.`);
  };
  const stat: [string, number][] = [["Roll v1", t.v1], ["Roll v2", t.v2], ["Deleted", t.deleted], ["Added", t.added], ["Modified", t.modified]];
  return (
    <div>
      <h1 className="text-[32px] leading-[38px] font-bold tracking-[-0.015em]">Overview</h1>
      <p className="text-ink-2 mb-4">Sampleabad · 100 booths · roll v1 compared with v2.{ov.mocked && <span className="font-mono text-[12px] ml-2 text-ink-3">[mock data: API not reachable]</span>}</p>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-px bg-rule border border-rule mb-6">
        {stat.map(([k, v]) => (
          <div key={k} className="bg-surface p-3">
            <div className="overline">{k}</div>
            <div className="font-mono text-[32px] md:text-[40px] leading-[48px] font-semibold tabular-nums">{fmt(v)}</div>
          </div>
        ))}
      </div>

      <h2 className="text-[20px] leading-[26px] font-bold mb-2">Deletion rate by booth</h2>
      <div className="grid gap-1 max-w-[700px]" style={{ gridTemplateColumns: "repeat(10, minmax(0, 1fr))" }}>
        {d.booths.map((b) => (
          <button key={b.booth_id} className={`tile ${TILE[b.outcome]}`}
            onClick={() => click(b)} onMouseEnter={() => setHover(b)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(b)} onBlur={() => setHover(null)}
            aria-label={`Booth ${Number(b.booth_id.slice(1))}, ${pct(b.del_rate, 1)} deleted, ${OUT_LABEL[b.outcome]}`}>
            <span className="a">{Number(b.booth_id.slice(1))}</span>
            <span className="b">{(b.del_rate * 100).toFixed(0)}%</span>
          </button>
        ))}
      </div>
      <div className="min-h-16 mt-2 max-w-[700px]">
        {hover ? (
          <div className="border border-rule bg-surface p-2 text-[13px] inline-block">
            <span className="font-mono">{hover.booth_id}</span> · {hover.ward_id} · <span className="font-mono">{fmt(hover.n_v1)}</span> → <span className="font-mono">{fmt(hover.n_v2)}</span> names ·
            deleted <span className="font-mono">{pct(hover.del_rate, 1)}</span>, expected <span className="font-mono">{pct(hover.expected_del_rate, 1)}</span> · {OUT_LABEL[hover.outcome]}
          </div>
        ) : <span className="text-[13px] text-ink-3">{msg || "Hover or focus a tile for details. Click to open the flag."}</span>}
      </div>
      <ul className="flex flex-wrap gap-x-6 gap-y-1 text-[13px] mt-2">
        <li><i className="inline-block w-4 h-4 align-middle mr-2 bg-surface border border-rule" />Neutral</li>
        <li><i className="inline-block w-4 h-4 align-middle mr-2 bg-unusual-soft border-2 border-unusual" />Unusual, needs human review</li>
        <li><i className="inline-block w-4 h-4 align-middle mr-2 bg-benign-soft border border-benign" />Likely benign</li>
        <li><i className="tile--mixed inline-block w-4 h-4 align-middle mr-2 border border-unusual" />Mixed (hatched)</li>
      </ul>
      <FlagDrawer flag={open} onClose={() => setOpen(null)} />
    </div>
  );
}
