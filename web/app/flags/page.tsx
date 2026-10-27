"use client";
import { useMemo, useState } from "react";
import { useApi, fmt } from "@/lib/api";
import { FLAGS_MOCK } from "@/components/data";
import type { Flag } from "@/lib/types";
import FlagDrawer, { typeLabel } from "@/components/FlagDrawer";
import Stamp from "@/components/Stamp";

export default function Flags() {
  const { data, mocked } = useApi("/flags", FLAGS_MOCK);
  const [type, setType] = useState("all");
  const [band, setBand] = useState("all");
  const [open, setOpen] = useState<Flag | null>(null);
  const items = useMemo(() => (data?.items ?? []).filter((f) => (type === "all" || f.type === type) && (band === "all" || f.confidence_band === band)), [data, type, band]);
  const types = Array.from(new Set((data?.items ?? []).map((f) => f.type)));
  const sel = "h-8 ml-2 border border-rule-strong rounded-[2px] bg-surface px-2 text-[14px] normal-case tracking-normal font-medium text-ink";
  return (
    <div>
      <h1 className="text-[32px] leading-[38px] font-bold tracking-[-0.015em]">Flags</h1>
      <p className="text-ink-2 mb-4">Review queue, highest confidence first.{mocked && <span className="font-mono text-[12px] ml-2 text-ink-3">[mock data: API not reachable]</span>}</p>
      <div className="flex flex-wrap gap-4 mb-3 items-center">
        <label className="overline">Type <select className={sel} value={type} onChange={(e) => setType(e.target.value)}><option value="all">All</option>{types.map((t) => <option key={t} value={t}>{typeLabel(t)}</option>)}</select></label>
        <label className="overline">Confidence <select className={sel} value={band} onChange={(e) => setBand(e.target.value)}>{["all", "high", "medium", "low"].map((b) => <option key={b} value={b}>{b === "all" ? "All" : b[0].toUpperCase() + b.slice(1)}</option>)}</select></label>
        <span className="font-mono text-[13px] text-ink-2">{items.length} of {data?.total ?? 0}</span>
      </div>
      <div className="overflow-x-auto">
        <table className="tbl">
          <thead><tr><th>Flag</th><th>Type</th><th>Booth</th><th className="r">Observed</th><th className="r">Expected</th><th className="r">q</th><th className="r">Sure</th><th>Outcome</th></tr></thead>
          <tbody>
            {items.map((f) => (
              <tr key={f.flag_id} className={open?.flag_id === f.flag_id ? "sel" : ""} tabIndex={0} onClick={() => setOpen(f)} onKeyDown={(e) => e.key === "Enter" && setOpen(f)}>
                <td className="font-mono text-[12px] text-ink-2">{f.flag_id.slice(0, 8)}</td>
                <td>{typeLabel(f.type)}</td>
                <td className="font-mono">{Number(f.scope.booth_id.slice(1))}{f.scope.house_no ? ` / ${f.scope.house_no}` : ""}</td>
                <td className="r font-mono">{fmt(f.metrics.observed)}</td>
                <td className="r font-mono">{f.metrics.expected == null ? "–" : f.metrics.expected.toFixed(0)}</td>
                <td className="r font-mono">{f.metrics.q_value == null ? "–" : f.metrics.q_value < 0.001 ? "<0.001" : f.metrics.q_value.toFixed(3)}</td>
                <td className="r font-mono">{Math.round(f.confidence * 100)}%</td>
                <td>{f.likely_benign ? <Stamp kind="benign" /> : <Stamp kind="review" label="Needs review" />}</td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={8} className="text-ink-2">No flags match. That&apos;s normal for most filters.</td></tr>}
          </tbody>
        </table>
      </div>
      <FlagDrawer flag={open} onClose={() => setOpen(null)} />
    </div>
  );
}
