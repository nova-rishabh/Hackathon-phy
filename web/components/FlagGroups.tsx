"use client";
import { useMemo, useState } from "react";
import type { Flag } from "@/lib/types";
import { fmt, boothNo } from "@/lib/api";
import { typeLabel } from "@/components/FlagDrawer";
import Chip from "@/components/Chip";

// Booth-level patterns first; record-level checks (many small flags) fold below them.
const ORDER = ["deletion_spike", "addition_spike", "gender_ratio_swing", "impossible_age", "oversized_household", "duplicate_cluster", "relation_conflict"];
const PAGE = 8;
// One plain line per check, so a reader knows what each group means before opening it.
const HELP: Record<string, string> = {
  deletion_spike: "far more removals than the booth's ages predict",
  addition_spike: "far more additions than the district rate",
  gender_ratio_swing: "the share of women moved sharply between lists",
  impossible_age: "an age below 18 or above 110",
  oversized_household: "more than 15 voters at one house number",
  duplicate_cluster: "the same person may appear twice, in two spellings or scripts",
  relation_conflict: "a family link that can't be right, e.g. a parent younger than the child",
};
const bid = (id: string) => "B" + String(boothNo(id)).padStart(3, "0");

export default function FlagGroups({ flags, onOpen }: { flags: Flag[]; onOpen: (f: Flag) => void }) {
  const groups = useMemo(() => {
    const by = new Map<string, Flag[]>();
    for (const f of flags) by.set(f.type, [...(by.get(f.type) ?? []), f]);
    const rank = (t: string) => (ORDER.indexOf(t) < 0 ? 99 : ORDER.indexOf(t));
    return [...by.entries()]
      .sort((a, b) => rank(a[0]) - rank(b[0]))
      .map(([type, items]) => ({ type, items: [...items].sort((a, b) => b.confidence - a.confidence) }));
  }, [flags]);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [shown, setShown] = useState<Record<string, number>>({});
  const isOpen = (t: string, n: number) => open[t] ?? (t.endsWith("_spike") || n <= 3);

  if (flags.length === 0) return <p className="card px-4 py-3 text-ink-2">No flags in this roll. That&apos;s normal for most districts.</p>;

  return (
    <div className="card flaglist">
      {groups.map(({ type, items }) => {
        const o = isOpen(type, items.length);
        const review = items.filter((f) => !f.likely_benign).length;
        const k = shown[type] ?? PAGE;
        return (
          <div key={type} className="border-t border-line first:border-t-0">
            <button onClick={() => setOpen({ ...open, [type]: !o })} aria-expanded={o}
              className="group-row w-full text-left px-4 py-4 flex items-center justify-between gap-3 rounded-[16px]">
              <span className="flex items-start gap-3 min-w-0">
                <span className="caret mono text-ink-3 mt-0.5" data-open={o}>›</span>
                <span className="min-w-0">
                  <span className="block text-[17px]">{typeLabel(type)}</span>
                  {HELP[type] && <span className="block text-[13px] text-ink-3 mt-0.5">{HELP[type]}</span>}
                </span>
              </span>
              <span className="mono text-[12px] text-ink-3 shrink-0">{fmt(items.length)} · {fmt(review)} to review</span>
            </button>
            {o && (
              <ul className="pb-2">
                {items.slice(0, k).map((f) => (
                  <li key={f.flag_id}>
                    <button onClick={() => onOpen(f)} className="group-row w-full text-left pl-10 pr-4 py-2.5 flex items-center justify-between gap-3 rounded-[12px]">
                      <span className="mono text-[12px] text-ink-2 min-w-0 truncate">
                        {bid(f.scope.booth_id)}{f.scope.house_no ? ` · house ${f.scope.house_no}` : ""} · {fmt(f.metrics.observed)} obs · {Math.round(f.confidence * 100)}%
                      </span>
                      <Chip kind={f.likely_benign ? "likely_benign" : "review"} label={f.likely_benign ? "Likely benign" : "Review"} />
                    </button>
                  </li>
                ))}
                {items.length > k && (
                  <li className="pl-10 pr-4 py-2">
                    <button className="mono text-[12px] text-ink-2 underline underline-offset-4" onClick={() => setShown({ ...shown, [type]: k + 25 })}>
                      show {Math.min(25, items.length - k)} more of {fmt(items.length - k)}
                    </button>
                  </li>
                )}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}
