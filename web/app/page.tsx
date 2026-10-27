"use client";
import { useMemo, useState } from "react";
import { useApi, fmt, pct, boothNo } from "@/lib/api";
import { OVERVIEW_MOCK, FLAGS_MOCK } from "@/lib/mocks";
import type { BoothSummary, Flag, FlagList, Overview } from "@/lib/types";
import FlagDrawer, { flagKind } from "@/components/FlagDrawer";
import StoryPanel from "@/components/StoryPanel";
import { Display, Obj, BoothTile, Eyebrow } from "@/components/Display";
import { WatchBooth } from "@/components/AccountActions";
import FlagGroups from "@/components/FlagGroups";
import { Reveal, CountUp, EyeRing, Marquee } from "@/components/Motion";
import { benchSummary, big } from "@/lib/bench";

const TILE: Record<string, string> = { normal: "", unusual: "tile--unusual", likely_benign: "tile--benign", mixed: "hatch tile--mixed" };
const OUT: Record<string, string> = { normal: "neutral", unusual: "unusual, needs human review", likely_benign: "likely benign", mixed: "mixed" };
const bid = (id: string) => "B" + String(boothNo(id)).padStart(3, "0");

export default function Audit() {
  const ov = useApi<Overview>("/overview", OVERVIEW_MOCK);
  const fl = useApi<FlagList>("/flags", FLAGS_MOCK);
  const ops = useApi<{ bench?: unknown }>("/ops");
  const bench = benchSummary(ops.data?.bench);
  const [sel, setSel] = useState<string | null>(null);
  const [open, setOpen] = useState<Flag | null>(null);
  const [hover, setHover] = useState<BoothSummary | null>(null);
  const [msg, setMsg] = useState("");

  const flags = useMemo(() => fl.data?.items ?? [], [fl.data]);
  const lead = useMemo(() => {
    const spikes = flags.filter((f) => f.type === "deletion_spike" && !f.likely_benign);
    return [...spikes].sort((a, b) => b.metrics.observed - a.metrics.observed)[0] ?? flags[0];
  }, [flags]);

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
      <section className="grid gap-8 lg:grid-cols-[1fr_auto] items-center">
        <div className="min-w-0">
          <p className="eyebrow mb-5 words">
            {"Audit. Sampleabad, roll v1 to v2.".split(" ").map((w, i) => <span key={i} style={{ animationDelay: `${i * 60}ms` }}>{w}&nbsp;</span>)}
          </p>
          {booth && (
            <Reveal>
              <Display size="hero" dim={expected != null ? <>We expected about {fmt(expected)}.</> : undefined}>
                <span className="mono tracking-[-0.06em]">{sel ? fmt(removed) : <CountUp to={Math.round(removed)} />}</span> names left <Obj><BoothTile booth={booth} outcome={outcome} /></Obj> Booth {boothNo(booth)}.
              </Display>
            </Reveal>
          )}
          <Reveal delay={250}>
            <p className="mono text-[13px] text-ink-2 mt-6">
              v1 {fmt(t.v1)} → v2 {fmt(t.v2)} · removed {fmt(t.deleted)} · added {fmt(t.added)} · modified {fmt(t.modified)}
              {(ov.mocked || fl.mocked) && <span className="text-ink-3"> · mock data, api not reachable</span>}
            </p>
            <div className="flex flex-wrap gap-3 mt-8">
              <a href="#grid" className="btn">See every booth</a>
              <a href="/check" className="btn btn--quiet">Check a forwarded claim</a>
              {booth && <WatchBooth boothId={booth} />}
            </div>
          </Reveal>
        </div>
        <Reveal delay={150} className="hidden lg:block"><EyeRing size={340} /></Reveal>
      </section>

      <div className="mt-16 sm:mt-20 -mx-4">
        <Marquee items={[
          `${fmt(t.v1)} voters compared`,
          `${fmt(t.deleted)} removals, each given a story or marked unexplained`,
          `${fmt(flags.length)} patterns flagged for human review`,
          "every number computed in Python, never by the language model",
          "names masked in auditor views",
          bench ? `${big(bench.voters)} voters in ${bench.secs.toFixed(0)}s on one core` : "open engine, POST /audit",
          "Hindi · English · Punjabi",
        ]} />
      </div>

      <section id="grid" className="panel mt-16 sm:mt-20 scroll-mt-28">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,614px)_1fr]">
          <div className="min-w-0">
            <Eyebrow className="mb-5">Removal rate by booth. Tap a booth.</Eyebrow>
            <div className="grid10">
              {ov.data.booths.map((b, i) => (
                <button key={b.booth_id} className={`tile ${TILE[b.outcome]} ${b.outcome === "unusual" ? "ping" : ""}`} aria-pressed={b.booth_id === booth}
                  style={{ animationDelay: `${(Math.floor(i / 10) + (i % 10)) * 35}ms` }}
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
            <Eyebrow className="mb-5">Flags, grouped by check. Booth patterns first.</Eyebrow>
            <FlagGroups flags={flags} onOpen={(f) => { setSel(f.scope.booth_id); setOpen(f); setMsg(""); }} />
          </div>
        </div>
      </section>

      <Reveal className="mt-6">
        {bf?.stories
          ? <StoryPanel base={bf.stories} />
          : booth && <section className="panel"><Eyebrow>Which story fits.</Eyebrow><p className="mt-4 text-ink-2">No removal spike to attribute in Booth {boothNo(booth)}.</p></section>}
      </Reveal>

      <Why bench={bench} />
      <CtaRow />
      <FlagDrawer flag={open} onClose={() => setOpen(null)} />
    </div>
  );
}

const WHY = [
  {
    eyebrow: "Why outsiders build it.",
    title: "An institution can't audit itself and be believed.",
    body: "Internal checks may exist, but a claim of zero error from the keeper of the list convinces no one. Independent tools are how a democracy checks itself. And a small team ships in days, while procurement takes years.",
    points: ["Independent check, not self-audit", "Built in days, not tender cycles", "Pulls scattered PDFs and districts into one pipeline"],
  },
  {
    eyebrow: "What if the state builds its own.",
    title: "Then the benchmark moved. That is the win.",
    body: "Agencies rarely write this from scratch; they adopt a proven prototype or open a tender for it. If an official version ships with the same openness, the job is done. Until then, citizens, reporters and legal aid groups need it now.",
    points: ["Open method, adoptable as is", "Same checks for any claim, from any side", "Every flag carries its query and needs human review"],
  },
  {
    eyebrow: "Where it goes next.",
    title: "The engine isn't tied to one district.",
    body: "Diff, test, attribute, explain. The same steps run on any registry: more states, more countries, and other lists where entries appear or vanish in batches.",
    points: ["New regions: add a roll, no code change", "New domains: aid lists, procurement registers, KYC records", "API and scheduled audit reports for newsrooms and researchers"],
  },
];

function Why({ bench }: { bench: ReturnType<typeof benchSummary> }) {
  return (
    <section className="mt-24 sm:mt-32">
      <Reveal>
        <Eyebrow className="mb-5">Why this exists.</Eyebrow>
        <Display size="page" as="h2" dim="Three questions, each answered with something you can check.">
          Built to be checked.
        </Display>
      </Reveal>
      <div className="grid gap-4 mt-12 lg:grid-cols-3">
        {WHY.map((w, i) => (
          <Reveal key={w.eyebrow} delay={i * 120}>
            <article className="panel h-full flex flex-col">
              <Eyebrow>{w.eyebrow}</Eyebrow>
              <h3 className="h-section mt-4">{w.title}</h3>
              <p className="text-ink-2 mt-4 mb-6 text-[15px]">{w.body}</p>
              <ul className="card mt-auto pt-0">
                {w.points.map((p) => <li key={p} className="px-4 py-3 border-t border-line first:border-t-0 text-[14px]">{p}</li>)}
              </ul>
            </article>
          </Reveal>
        ))}
      </div>
      {bench && (
        <Reveal delay={200}>
          <div className="panel mt-4 grid gap-6 sm:grid-cols-3">
            <div>
              <Eyebrow>Voters, one run.</Eyebrow>
              <p className="mono text-[48px] leading-[52px] tracking-[-0.04em] mt-3">{big(bench.voters)}</p>
              <p className="mono text-[12px] text-ink-3 mt-1">in {bench.secs.toFixed(1)}s on one core{bench.base ? ` · ${big(bench.base.voters)} in ${bench.base.secs.toFixed(1)}s` : ""}</p>
            </div>
            <div>
              <Eyebrow>Duplicate pairs compared.</Eyebrow>
              <p className="mono text-[48px] leading-[52px] tracking-[-0.04em] mt-3">{big(bench.pairs)}</p>
              <p className="mono text-[12px] text-ink-3 mt-1">not {big(bench.naive)}: {fmt(Math.round(bench.reduction))}× fewer, by blocking</p>
            </div>
            <div>
              <Eyebrow>Cost of a claim check.</Eyebrow>
              <p className="mono text-[48px] leading-[52px] tracking-[-0.04em] mt-3">O(1)</p>
              <p className="mono text-[12px] text-ink-3 mt-1">precomputed lookups · measured on this machine, see Trust</p>
            </div>
          </div>
        </Reveal>
      )}
    </section>
  );
}

function CtaRow() {
  const items = [["/check", "Check a claim.", "Paste a forward. Get each part verified, disputed or not provable."], ["/ask", "Ask about a name.", "हिंदी · English · ਪੰਜਾਬੀ. Status, reason and the next form to file."], ["/trust", "See what we miss.", "Blind test, error rate per rule, the neutrality log."]];
  return (
    <section className="grid gap-4 mt-4 sm:grid-cols-3">
      {items.map(([h, t, d], i) => (
        <Reveal key={h} delay={i * 100}>
          <a href={h} className="panel block h-full group-row hover:bg-panel-2">
            <p className="h-section">{t} <span className="dim">→</span></p>
            <p className="text-ink-2 text-[14px] mt-3">{d}</p>
          </a>
        </Reveal>
      ))}
    </section>
  );
}
