"use client";
import { useMemo, useState } from "react";
import { useApi, fmt, pct, boothNo } from "@/lib/api";
import { OVERVIEW_MOCK, FLAGS_MOCK } from "@/lib/mocks";
import type { BoothSummary, Flag, FlagList, Overview } from "@/lib/types";
import FlagDrawer, { typeLabel, flagKind } from "@/components/FlagDrawer";
import StoryPanel from "@/components/StoryPanel";
import Chip from "@/components/Chip";
import { Display, Obj, BoothTile, Eyebrow } from "@/components/Display";

const TILE: Record<string, string> = { normal: "", unusual: "tile--unusual", likely_benign: "tile--benign", mixed: "hatch tile--mixed" };
const OUT: Record<string, string> = { normal: "neutral", unusual: "unusual, needs human review", likely_benign: "likely benign", mixed: "mixed" };
const bid = (id: string) => "B" + String(boothNo(id)).padStart(3, "0");

export default function Audit() {
  const ov = useApi<Overview>("/overview", OVERVIEW_MOCK);
  const fl = useApi<FlagList>("/flags", FLAGS_MOCK);
  const [sel, setSel] = useState<string | null>(null);
  const [open, setOpen] = useState<Flag | null>(null);
  const [hover, setHover] = useState<BoothSummary | null>(null);
  const [msg, setMsg] = useState("");

  const flags = useMemo(() => fl.data?.items ?? [], [fl.data]);
  const lead = useMemo(() => {
    const spikes = flags.filter((f) => f.type === "deletion_spike" && !f.likely_benign);
    return [...spikes].sort((a, b) => b.metrics.observed - a.metrics.observed)[0] ?? flags[0];
  }, [flags]);
  const byConf = useMemo(() => [...flags].sort((a, b) => b.confidence - a.confidence), [flags]);

  if (!ov.data) return <p className="eyebrow">Loading roll comparison.</p>;
  const t = ov.data.totals;
  const booth = sel ?? lead?.scope.booth_id ?? null;
  const flagFor = (id: string) => flags.find((x) => x.scope.booth_id === id && x.stories) ?? flags.find((x) => x.scope.booth_id === id);
  const bf = booth ? flagFor(booth) : undefined;
  const bs = ov.data.booths.find((b) => b.booth_id === booth);

  // Headline numbers come straight from engine output (flag metrics, else the booth summary).
  const removed = bf?.metrics.observed ?? (bs ? bs.del_rate * bs.n_v1 : 0);
  const expected = bf?.metrics.expected ?? (bs ? bs.expected_del_rate * bs.n_v1 : null);
  const outcome = bs?.outcome ?? (bf ? flagKind(bf) : "normal");

  const click = (b: BoothSummary) => {
    setSel(b.booth_id);
    const f = flagFor(b.booth_id);
    if (f) { setOpen(f); setMsg(""); } else setMsg(`No flags in Booth ${boothNo(b.booth_id)}. That's normal for most booths.`);
  };

  return (
    <div>
      <Eyebrow className="mb-5">Audit. Sampleabad, roll v1 to v2.</Eyebrow>
      {booth && (
        <Display size="hero" dim={expected != null ? `We expected about ${fmt(expected)}.` : undefined}>
          {fmt(removed)} names left <Obj><BoothTile booth={booth} outcome={outcome} /></Obj> Booth {boothNo(booth)}.
        </Display>
      )}
      <p className="mono text-[13px] text-ink-2 mt-6">
        v1 {fmt(t.v1)} → v2 {fmt(t.v2)} · removed {fmt(t.deleted)} · added {fmt(t.added)} · modified {fmt(t.modified)}
        {(ov.mocked || fl.mocked) && <span className="text-ink-3"> · mock data, api not reachable</span>}
      </p>

      <section className="panel mt-16 sm:mt-24">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,614px)_1fr]">
          <div className="min-w-0">
            <Eyebrow className="mb-5">Removal rate by booth. Tap a booth.</Eyebrow>
            <div className="grid10">
              {ov.data.booths.map((b) => (
                <button key={b.booth_id} className={`tile ${TILE[b.outcome]}`} aria-pressed={b.booth_id === booth}
                  onClick={() => click(b)} onMouseEnter={() => setHover(b)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(b)} onBlur={() => setHover(null)}
                  aria-label={`Booth ${boothNo(b.booth_id)}, ${pct(b.del_rate, 1)} removed, ${OUT[b.outcome]}`}>
                  <span className="a">{boothNo(b.booth_id)}</span>
                  <span className="b">{Math.round(b.del_rate * 100)}%</span>
                </button>
              ))}
            </div>
            <p className="mono text-[12px] text-ink-2 mt-4 min-h-10">
              {hover
                ? <>{bid(hover.booth_id)} · {hover.ward_id} · {fmt(hover.n_v1)} → {fmt(hover.n_v2)} · removed {pct(hover.del_rate, 1)} vs {pct(hover.expected_del_rate, 1)} expected · {OUT[hover.outcome]}</>
                : msg || "yellow unusual · periwinkle likely benign · hatched mixed · white neutral"}
            </p>
          </div>
          <div className="min-w-0">
            <Eyebrow className="mb-5">Flags, most confident first.</Eyebrow>
            <ul className="card">
              {byConf.map((f) => (
                <li key={f.flag_id} className="border-t border-line first:border-t-0">
                  <button onClick={() => { setSel(f.scope.booth_id); setOpen(f); setMsg(""); }}
                    className="w-full text-left px-4 py-3 flex items-center justify-between gap-3 hover:bg-page rounded-[16px]">
                    <span className="min-w-0">
                      <span className="block text-[15px]">{typeLabel(f.type)}</span>
                      <span className="block mono text-[12px] text-ink-3">{bid(f.scope.booth_id)}{f.scope.house_no ? ` · house ${f.scope.house_no}` : ""} · {fmt(f.metrics.observed)} obs · {Math.round(f.confidence * 100)}%</span>
                    </span>
                    <Chip kind={f.likely_benign ? "likely_benign" : "review"} label={f.likely_benign ? "Likely benign" : "Review"} />
                  </button>
                </li>
              ))}
              {flags.length === 0 && <li className="px-4 py-3 text-ink-2">No flags in this roll. That&apos;s normal for most districts.</li>}
            </ul>
          </div>
        </div>
      </section>

      <div className="mt-6">
        {bf?.stories
          ? <StoryPanel base={bf.stories} />
          : booth && <section className="panel"><Eyebrow>Which story fits.</Eyebrow><p className="mt-4 text-ink-2">No removal spike to attribute in Booth {boothNo(booth)}.</p></section>}
      </div>
      <FlagDrawer flag={open} onClose={() => setOpen(null)} />
    </div>
  );
}
