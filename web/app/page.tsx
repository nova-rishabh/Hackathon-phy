"use client";
import { useEffect, useMemo, useState } from "react";
import { useApi, fmt, pct, boothNo, WA_NUMBER } from "@/lib/api";
import { OVERVIEW_MOCK, FLAGS_MOCK } from "@/lib/mocks";
import type { BoothSummary, Flag, FlagList, Overview } from "@/lib/types";
import FlagDrawer, { flagKind } from "@/components/FlagDrawer";
import StoryPanel from "@/components/StoryPanel";
import { Display, Obj, BoothTile, Eyebrow } from "@/components/Display";
import { WatchBooth } from "@/components/AccountActions";
import FlagGroups from "@/components/FlagGroups";
import { Reveal, CountUp, EyeRing, Marquee, CyclingBooth } from "@/components/Motion";
import { benchSummary, big } from "@/lib/bench";
import Tour, { type TourStep } from "@/components/Tour";
import { PageLoader } from "@/components/Loader";

const TILE: Record<string, string> = { normal: "", unusual: "tile--unusual", likely_benign: "tile--benign", mixed: "hatch tile--mixed" };
const OUT: Record<string, string> = { normal: "neutral", unusual: "unusual, needs human review", likely_benign: "likely benign", mixed: "mixed" };
// The demo's three booths: unexplained (47), hostel move-out (12), mixed (63).
const HERO_BOOTHS = ["B047", "B012", "B063"];
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
  const [tour, setTour] = useState(false);

  // First visit (or ?tour=1): start the guided tour once the real numbers are in.
  const ready = !!ov.data && !ov.mocked && !!fl.data && !fl.mocked;
  useEffect(() => {
    if (!ready) return;
    let seen = true;
    try { seen = !!localStorage.getItem("rw_tour_seen"); } catch { /* storage blocked: don't auto-start */ }
    if (new URLSearchParams(window.location.search).get("tour") === "1") seen = false;
    if (seen) return;
    const t = setTimeout(() => setTour(true), 1200);
    return () => clearTimeout(t);
  }, [ready]);
  const endTour = () => { setTour(false); try { localStorage.setItem("rw_tour_seen", "1"); } catch { /* fine */ } };

  const flags = useMemo(() => fl.data?.items ?? [], [fl.data]);
  const lead = useMemo(() => {
    const spikes = flags.filter((f) => f.type === "deletion_spike" && !f.likely_benign);
    return [...spikes].sort((a, b) => b.metrics.observed - a.metrics.observed)[0] ?? flags[0];
  }, [flags]);

  if (!ov.data) return <PageLoader label="comparing the two rolls" />;
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

  // Tour text. Every number is engine output (flag metrics and story counts), read from the API like the rest of the page.
  const tourSteps = (): TourStep[] => {
    const leadId = lead?.scope.booth_id;
    const lf = leadId ? flagFor(leadId) : undefined;
    const lun = lf?.stories?.stories.find((x) => x.code === "unexplained");
    const benign = ov.data!.booths.find((b) => b.outcome === "likely_benign" && flagFor(b.booth_id)?.stories);
    const bfl = benign ? flagFor(benign.booth_id) : undefined;
    const top = bfl?.stories ? [...bfl.stories.stories].filter((x) => x.code !== "unexplained").sort((a, b) => b.count - a.count)[0] : undefined;
    const STORY: Record<string, string> = { hostel_moveout: "a hostel move-out", death_registered: "a registered death",
      boundary_change: "a boundary change", duplicate_cleanup: "a duplicate cleanup" };
    const toLead = () => { if (leadId) { setSel(leadId); setOpen(null); } };
    const s: TourStep[] = [
      { target: '[data-tour="hero"]', title: "Welcome to RollWatch.",
        body: "When a voter list is revised, names are added, moved and removed. RollWatch shows which changes have an innocent explanation and which don't. This takes about a minute." },
      { target: '[data-tour="grid"]', title: "Every booth, at a glance.",
        body: "Each square is one polling booth, and the number is the share of its voters removed. Yellow: more removals than expected and no record explains them. Blue: unusual, but an innocent record does. Hatched: partly explained." },
    ];
    if (lf && leadId) s.push({ target: `[data-booth="${leadId}"]`, onEnter: toLead, title: `Booth ${boothNo(leadId)} stands out.`,
      body: <>{fmt(lf.metrics.observed)} names were removed against about {fmt(lf.metrics.expected)} expected for its size and ages. Tap any booth to see its full story.</> });
    if (benign && bfl && top) s.push({ target: `[data-booth="${benign.booth_id}"]`, title: `Booth ${boothNo(benign.booth_id)} looks the same to a rumour.`,
      body: <>{fmt(bfl.metrics.observed)} names removed too, but {Math.round(top.share * 100)}% of them match {STORY[top.code] ?? "an innocent record"}, so it is marked likely benign, not unusual.</> });
    if (lf?.stories) s.push(
      { target: '[data-tour="story"]', onEnter: toLead, title: "Which story fits.",
        body: <>Every removal in Booth {boothNo(lf.stories.booth_id)} is checked against deaths, hostels, boundary moves and duplicate cleanups. {fmt(lun?.count ?? 0)} of {fmt(lf.stories.removed_total)} match none of them, so a person should look.</> },
      { target: '[data-tour="sources"]', onEnter: toLead, title: "Switch the evidence yourself.",
        body: "Turn a source off and watch the answer move. Nothing is hidden: you can see exactly what each record explains." });
    s.push(
      { target: '[data-tour="flags"]', title: "Every flag goes to a person.",
        body: <>{fmt(flags.length)} patterns, grouped by check, each with its confidence. A flag is never a finding on its own.</> },
      { target: 'header a[href="/check"], header button[aria-expanded]', title: "Check a forwarded claim.",
        body: "Paste a viral message or drop a screenshot. It is split into parts, and each part is checked against the roll with a fixed query you can read." },
      { target: 'header a[href="/ask"], header button[aria-expanded]', title: "Is my name on the list?",
        body: "Any voter can search in Hindi, English or Punjabi, in any spelling, and see their status, the likely reason and which form to file." },
      { target: 'header a[href="/trust"], header button[aria-expanded]', title: "What we miss.",
        body: "A blind test planted by a separate agent, false alarms counted, and the error rate of every rule. That's the tour." });
    return s;
  };

  return (
    <div>
      <section className="hero grid gap-8 lg:grid-cols-[1fr_auto] items-center">
        <div className="min-w-0">
          <p className="eyebrow mb-5 words">
            {"Voter roll transparency.".split(" ").map((w, i) => <span key={i} style={{ animationDelay: `${i * 60}ms` }}>{w}&nbsp;</span>)}
          </p>
          <Reveal>
            <div data-tour="hero">
            <Display size="hero" dim="And every rumour about it, checked.">
              Every change to a voter <span className="whitespace-nowrap">roll<Obj><CyclingBooth booths={HERO_BOOTHS.map((id) => ({ booth: id,
                outcome: ov.data!.booths.find((b) => b.booth_id === id)?.outcome ?? "normal" }))} /></Obj>,</span> explained.
            </Display>
            </div>
          </Reveal>
          <Reveal delay={200}>
            <p className="text-ink-2 text-[18px] leading-[28px] mt-6 max-w-[60ch]">
              When a voter list is revised, thousands of names are added, moved or removed, and forwards claiming
              &ldquo;600 names cut from one booth&rdquo; spread in hours. RollWatch compares the two versions of the list,
              tells you which changes have an innocent explanation and which don&apos;t, checks viral claims part by part,
              and helps any voter find out why their own name changed.
            </p>
            <div className="flex flex-wrap gap-3 mt-8">
              <a href="#example" className="btn">See a live example</a>
              <a href="/check" className="btn btn--quiet">Check a forwarded claim</a>
              <a href="/ask" className="btn btn--quiet">Is my name on the list?</a>
              <button className="btn btn--quiet" onClick={() => setTour(true)}>Take the 1-minute tour</button>
            </div>
          </Reveal>
        </div>
        <Reveal delay={150} className="hidden lg:block"><EyeRing size={340} /></Reveal>
      </section>

      <section>
        <div className="grid gap-4 lg:grid-cols-2 items-stretch">
          <div className="min-w-0 flex flex-col">
            <Reveal><Eyebrow className="mb-5">How it works.</Eyebrow></Reveal>
            <div className="grid gap-4 sm:grid-cols-2 flex-1 auto-rows-fr">
              {STEPS.map(([n, title, body], i) => (
                <Reveal key={n} delay={i * 100} className="h-full">
                  <article className="panel h-full !p-6">
                    <p className="mono text-[13px] text-ink-3">{n}</p>
                    <h3 className="text-[21px] leading-[26px] tracking-[-0.02em] mt-4">{title}</h3>
                    <p className="text-ink-2 text-[14px] leading-[21px] mt-2">{body}</p>
                  </article>
                </Reveal>
              ))}
            </div>
          </div>
          <div className="min-w-0 flex flex-col">
            <Reveal><Eyebrow className="mb-5">Watch it in 48 seconds.</Eyebrow></Reveal>
            <Reveal delay={150}>
              <div className="panel !p-3">
                <video className="w-full rounded-[20px] block bg-surface" src="/rollwatch-film.mp4" poster="/film-poster.jpg"
                  controls playsInline preload="metadata" />
              </div>
            </Reveal>
            <Reveal delay={250} className="flex-1 flex mt-4">
              <div className="panel !p-5 flex-1 flex flex-col">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <Eyebrow>Try it yourself.</Eyebrow>
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="mono text-[11px] text-ink-3">try:</span>
                    {[["Meena Kumari", "47"], ["Ravi Verma", "12"], ["Harpreet Kaur", "63"]].map(([n, d]) => (
                      <a key={n} href="/ask" className="card px-2.5 py-1 group-row">
                        <span className="text-[13px]">{n}</span> <span className="mono text-[10px] text-ink-3">{d}</span>
                      </a>
                    ))}
                  </div>
                </div>
                <div className="grid gap-2.5 sm:grid-cols-2 mt-3 flex-1 content-end">
                  {[
                    ["https://t.me/Rollwatch_bot", "Telegram bot", "@Rollwatch_bot · name or forward", true],
                    ...(WA_NUMBER ? [[`https://wa.me/${WA_NUMBER}`, "WhatsApp", "same bot · voice notes too", true]] : []),
                    ["/ask", "Ask on the web", "3 languages · documents", false],
                    ["/run", "Run it on your own list", "two roll CSVs or the sample", false],
                  ].map(([href, title, hint, ext]) => (
                    <a key={String(href)} href={String(href)} {...(ext ? { target: "_blank", rel: "noreferrer" } : {})} className="card px-4 py-3 group-row block">
                      <p className="text-[15px]">{title} <span className="dim">→</span></p>
                      <p className="mono text-[11px] text-ink-3 mt-0.5 truncate">{hint}</p>
                    </a>
                  ))}
                </div>
              </div>
            </Reveal>
          </div>
        </div>
        <Reveal delay={200}>
          <p className="mono text-[12px] text-ink-3 mt-4">
            every number is computed in plain Python · the AI only splits sentences and words replies · every output says &ldquo;needs human review&rdquo; · no real voter data: Sampleabad is a fictional district
          </p>
        </Reveal>
      </section>

      <section id="example" className="mt-16 scroll-mt-28">
        <Reveal><Eyebrow className="mb-5">A live example. Sampleabad, roll v1 to v2.</Eyebrow></Reveal>
        {booth && (
          <Reveal>
            <Display size="page" as="h2" dim={expected != null ? <>We expected about {fmt(expected)}. Here is how we tell if that matters.</> : undefined}>
              <span className="mono tracking-[-0.06em]">{sel ? fmt(removed) : <CountUp to={Math.round(removed)} />}</span> names left <Obj><BoothTile booth={booth} outcome={outcome} /></Obj> Booth {boothNo(booth)}.
            </Display>
          </Reveal>
        )}
        <Reveal delay={150}>
          <p className="mono text-[13px] text-ink-2 mt-6">
            v1 {fmt(t.v1)} → v2 {fmt(t.v2)} · removed {fmt(t.deleted)} · added {fmt(t.added)} · modified {fmt(t.modified)}
            {(ov.mocked || fl.mocked) && <span className="text-ink-3"> · mock data, api not reachable</span>}
          </p>
          <div className="flex flex-wrap gap-3 mt-6">
            <a href="#grid" className="btn">See every booth</a>
            {booth && <WatchBooth boothId={booth} />}
          </div>
        </Reveal>
      </section>

      <div className="mt-16 -mx-4">
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

      <section id="grid" className="panel mt-16 scroll-mt-28">
        <div className="mb-8 max-w-[72ch]">
          <Eyebrow className="mb-3">Every booth, at a glance.</Eyebrow>
          <h2 className="h-section">Each square is one polling booth. <span className="dim">The number is the share of its voters removed between the two lists.</span></h2>
          <div className="flex flex-wrap gap-x-5 gap-y-2 mt-5 mono text-[12px] text-ink-2">
            <span className="flex items-center gap-2"><i className="inline-block w-4 h-4 rounded-[4px] bg-signal" />unusual, needs human review</span>
            <span className="flex items-center gap-2"><i className="inline-block w-4 h-4 rounded-[4px] bg-benign" />unusual, but an innocent record explains it</span>
            <span className="flex items-center gap-2"><i className="inline-block w-4 h-4 rounded-[4px] hatch" />partly explained</span>
            <span className="flex items-center gap-2"><i className="inline-block w-4 h-4 rounded-[4px] bg-surface border border-line" />normal for its size and ages</span>
          </div>
        </div>
        <div className="grid gap-10 lg:grid-cols-[minmax(0,614px)_1fr] lg:items-stretch">
          <div className="min-w-0">
            <Eyebrow className="mb-5">Tap a booth to see why.</Eyebrow>
            <div className="grid10" data-tour="grid">
              {ov.data.booths.map((b, i) => (
                <button key={b.booth_id} data-booth={b.booth_id} className={`tile ${TILE[b.outcome]} ${b.outcome === "unusual" ? "ping" : ""}`} aria-pressed={b.booth_id === booth}
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
                : msg || "hover a booth for its numbers · tap it for the full story"}
            </p>
          </div>
          <div className="min-w-0 flex flex-col lg:relative">
            <Eyebrow className="mb-5">What the engine flagged, by check. Tap one to see why.</Eyebrow>
            <div className="flex-1 min-h-[420px] lg:min-h-0 lg:relative" data-tour="flags">
              <div className="lg:absolute lg:inset-0 flex">
                <FlagGroups flags={flags} onOpen={(f) => { setSel(f.scope.booth_id); setOpen(f); setMsg(""); }} />
              </div>
            </div>
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
      <Tour open={tour && !open} onClose={endTour} steps={tourSteps()} />
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
    <section className="mt-16">
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

const STEPS: [string, string, string][] = [
  ["01", "Compare the two lists.", "We line up the old and new voter list and count, booth by booth, who was added, removed or changed, against what a normal year looks like."],
  ["02", "Find the story behind each removal.", "Each removal is matched to an innocent record: a registered death, a hostel emptying, a boundary redraw, a duplicate cleanup. What's left is marked unexplained."],
  ["03", "Check the viral claim.", "Paste a forward. It is split into parts, and each part gets a real query: verified, disputed, or cannot be proven, with the reason shown."],
  ["04", "Tell the voter what to do.", "Anyone types their name, in Hindi, English or Punjabi, by text or voice, and gets their status, the likely reason, and the official form to file."],
];
