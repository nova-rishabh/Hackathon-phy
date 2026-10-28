"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ALL_SOURCES, WA_NUMBER, ask, checkClaim, crore, fmt, get, pct, simulate, story, useApi,
  type BlindEval, type CitizenAnswer, type ClaimResult, type Limits, type Ops, type Overview, type Sim, type Story, type Verdict,
} from "@/lib/home-api";

const DEMO_CLAIM = "Booth 47 mein 600 naam kaat diye, sabse zyada, aur sab ek community ke!";

/** Words that rise in one after another. */
function Rise({ text, start = 0, className = "" }: { text: string; start?: number; className?: string }) {
  return <>{text.split(" ").map((w, i) => (
    <span key={i} className={`rise ${className}`} style={{ "--i": start + i, display: "inline-block", whiteSpace: "pre" } as React.CSSProperties}>{w + " "}</span>
  ))}</>;
}

function Chip({ kind, children }: { kind: "review" | "verified" | "disputed" | "benign" | "unprovable" | "quiet"; children: React.ReactNode }) {
  return <span className={`chip chip--${kind}`}>{children}</span>;
}
const OUTCOME_CHIP: Record<string, [Parameters<typeof Chip>[0]["kind"], string]> = {
  unusual: ["review", "Unusual · needs human review"], likely_benign: ["benign", "Likely benign"], mixed: ["quiet", "Mixed"], normal: ["quiet", "Normal"],
};
const VERDICT_CHIP: Record<Verdict, [Parameters<typeof Chip>[0]["kind"], string]> = {
  verified: ["verified", "Verified"], disputed: ["disputed", "Disputed"], unprovable: ["unprovable", "Cannot be proven"],
};

// ---------------------------------------------------------------- 0. hero

export function Hero({ ov }: { ov: Overview | null }) {
  return (
    <section id="top" className="chapter">
      <div className="wrap"><div className="col col--wide">
        <p className="eyebrow rise">Voter roll transparency.</p>
        <h1 className="display"><Rise text="Every change to a voter roll, explained." start={1} /><span className="dim"><Rise text="And every rumour about it, checked." start={8} /></span></h1>
        <p className="lede rise" style={{ "--i": 15 } as React.CSSProperties}>
          RollWatch compares two versions of a voter list, tells you which removals have an innocent explanation and which don&apos;t, checks
          viral claims part by part, and tells any voter why their own name changed.
        </p>
        <p className="foot rise" style={{ "--i": 16 } as React.CSSProperties}>
          synthetic data · Sampleabad is a fictional district of {fmt(ov?.totals.v1)} voters in 100 booths
        </p>
        <div className="scrollcue rise" style={{ "--i": 17 } as React.CSSProperties}><span className="eyebrow">Scroll down</span><span /></div>
      </div></div>
    </section>
  );
}

// ---------------------------------------------------------------- 1. the rumour

export function Problem({ ov }: { ov: Overview | null }) {
  return (
    <section id="problem" className="chapter">
      <div className="wrap"><div className="col">
        <p className="eyebrow rise">The rumour.</p>
        <h2 className="title"><Rise text={`${fmt(ov?.totals.deleted)} names left the roll.`} /><span className="dim"><Rise text="The forward arrived first." start={5} /></span></h2>
        <div className="v3bubble glass rise" style={{ "--i": 9 } as React.CSSProperties} lang="hi">
          {DEMO_CLAIM}
          <div className="foot" style={{ marginTop: 8 }}>forwarded many times</div>
        </div>
        <p className="lede rise" style={{ "--i": 10 } as React.CSSProperties}>
          After every revision, names are added, moved and removed. A forward says what it likes, and spreads in hours. Nobody can check it.
          So we built the thing that checks it, on the same numbers for everyone.
        </p>
      </div></div>
    </section>
  );
}

// ---------------------------------------------------------------- 2. audit

export function Audit({ ov }: { ov: Overview | null }) {
  const counts = useMemo(() => {
    const c: Record<string, number> = { unusual: 0, likely_benign: 0, mixed: 0, normal: 0 };
    ov?.booths.forEach((b) => { c[b.outcome] = (c[b.outcome] ?? 0) + 1; });
    return c;
  }, [ov]);
  const b47 = ov?.booths.find((b) => b.booth_id === "B047");
  return (
    <section id="audit" className="chapter chapter--tall">
      <div className="wrap"><div className="col" style={{ maxWidth: 520 }}>
        <p className="eyebrow rise">Audit. 100 booths.</p>
        <h2 className="title"><Rise text="Every booth, tested against what's expected." /><span className="dim"><Rise text={`${ov ? counts.unusual : "—"} need a person to look.`} start={6} /></span></h2>
        <p className="lede rise" style={{ "--i": 12 } as React.CSSProperties}>
          Each booth&apos;s removals are tested against the rate its age mix predicts (a one-sided binomial test, corrected for testing 100 booths at once).
          {b47 && <> Booth 47 lost <span className="num">{pct(b47.del_rate)}</span> of its voters; about <span className="num">{pct(b47.expected_del_rate)}</span> was expected.</>}
        </p>
        <div className="legend rise" style={{ "--i": 13 } as React.CSSProperties}>
          <span><i style={{ background: "var(--signal)" }} />needs human review {ov ? counts.unusual : "—"}</span>
          <span><i style={{ background: "var(--benign)" }} />likely benign {ov ? counts.likely_benign : "—"}</span>
          <span><i className="hatch" />mixed {ov ? counts.mixed : "—"}</span>
          <span><i style={{ background: "#5d6470" }} />normal {ov ? counts.normal : "—"}</span>
        </div>
        <p className="foot rise" style={{ "--i": 14 } as React.CSSProperties}>each point is a voter · each cluster is a booth · colour is the engine&apos;s verdict</p>
      </div></div>
    </section>
  );
}

// ---------------------------------------------------------------- 3. which story fits

const STORY_COL: Record<string, string> = {
  death_registered: "var(--story-death)", duplicate_cleanup: "var(--story-dupes)", boundary_change: "var(--story-boundary)", hostel_moveout: "var(--story-hostel)",
};
const STORY_SHORT: Record<string, string> = {
  death_registered: "death", duplicate_cleanup: "dupes", boundary_change: "boundary", hostel_moveout: "hostel", unexplained: "unexplained",
};

export function WhichStory({ onStory }: { onStory: (s: Story) => void }) {
  const [booth, setBooth] = useState("B047");
  const [boundary, setBoundary] = useState(true);
  const [s, setS] = useState<Story | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => {
    let live = true;
    const src = boundary ? ALL_SOURCES : ALL_SOURCES.filter((x) => x !== "boundary_changes");
    story(booth, src).then((d) => { if (live) { setS(d); setErr(false); onStory(d); } }).catch(() => live && setErr(true));
    return () => { live = false; };
  }, [booth, boundary, onStory]);
  const un = s?.stories.find((x) => x.code === "unexplained");
  const chip = s ? OUTCOME_CHIP[s.outcome] : null;
  return (
    <section id="story" className="chapter chapter--tall">
      <div className="wrap"><div className="col">
        <p className="eyebrow rise">Which story fits.</p>
        <div className="v3seg rise" style={{ "--i": 1, alignSelf: "flex-start" } as React.CSSProperties} role="group" aria-label="Booth">
          {["B047", "B012", "B063"].map((b) => (
            <button key={b} aria-pressed={booth === b} onClick={() => { setBooth(b); setBoundary(true); }}>Booth {Number(b.slice(1))}</button>
          ))}
        </div>
        <h2 className="title" aria-live="polite">
          {s && un ? <>{fmt(un.count)} of {fmt(s.removed_total)} removals fit no story. <span className="dim">Booth {Number(booth.slice(1))}, about {fmt(Math.round(s.residual.expected_background))} expected to go anyway.</span></>
            : <span className="dim">{err ? "The engine didn't answer. Try again in a moment." : "Asking the engine…"}</span>}
        </h2>
        {s && <div className="glass v3card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="v3bar" role="img" aria-label="Story shares">
            {s.stories.filter((x) => x.count > 0).map((x) => (
              <div key={x.code} className={x.code === "unexplained" ? "hatch" : ""} style={{ flexGrow: x.count, background: STORY_COL[x.code] }} />
            ))}
          </div>
          <div className="legend">
            {s.stories.map((x) => <span key={x.code}>{STORY_SHORT[x.code] ?? x.code} <span className="num" style={{ color: "var(--ink)" }}>{fmt(x.count)}</span>{x.code === "unexplained" && <> ({pct(x.share)})</>}</span>)}
          </div>
          <hr className="hair" />
          <div className="row" style={{ justifyContent: "space-between" }}>
            {chip && <Chip kind={chip[0]}>{chip[1]}</Chip>}
            {booth === "B063" && (
              <div className="v3seg" role="group" aria-label="Boundary-change log">
                <button aria-pressed={boundary} onClick={() => setBoundary(true)}>Boundary log on</button>
                <button aria-pressed={!boundary} onClick={() => setBoundary(false)}>Off</button>
              </div>
            )}
          </div>
          <p className="small" style={{ margin: 0 }}>
            Every removed record is checked, in a fixed order, against the death register, a duplicate still on the roll, the boundary-change log and the hostel list.
            Whatever no record explains is tested again against background. Needs human review either way.
          </p>
        </div>}
      </div></div>
    </section>
  );
}

// ---------------------------------------------------------------- 4. claim court

export function ClaimCourt({ visible }: { visible: boolean }) {
  const [text, setText] = useState(DEMO_CLAIM);
  const [res, setRes] = useState<ClaimResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(false);
  const ran = useRef(false);
  const run = (t: string) => {
    setBusy(true); setErr(false);
    checkClaim(t).then(setRes).catch(() => setErr(true)).finally(() => setBusy(false));
  };
  useEffect(() => { if (visible && !ran.current) { ran.current = true; run(DEMO_CLAIM); } }, [visible]);
  return (
    <section id="check" className="chapter chapter--tall">
      <div className="wrap"><div className="col col--wide">
        <p className="eyebrow rise">Claim court.</p>
        <h2 className="title"><Rise text="The agent plans." /><span className="dim"><Rise text="Code decides." start={3} /></span></h2>
        <form className="glass v3card" style={{ display: "flex", flexDirection: "column", gap: 12 }} onSubmit={(e) => { e.preventDefault(); if (text.trim()) run(text.trim()); }}>
          <label className="eyebrow" htmlFor="claim">Paste a forward</label>
          <textarea id="claim" className="field" rows={2} value={text} onChange={(e) => setText(e.target.value)} maxLength={600} />
          <div className="row"><button className="btn btn--solid" disabled={busy}>{busy ? "Checking…" : "Check this claim"}</button>
            <span className="foot">the model only splits the sentence · every number comes from a fixed query</span></div>
        </form>
        {err && <p className="small">The engine didn&apos;t answer. Try again in a moment.</p>}
        {res && <div className="glass v3card" aria-live="polite">
          {res.sub_claims.map((c) => {
            const [k, l] = VERDICT_CHIP[c.verdict];
            return (
              <div key={c.id} className="vrow">
                <div><Chip kind={k}>{l}</Chip></div>
                <div><div>{c.text}</div><div className="small">{c.reason}</div><div className="query">{c.query_shown}</div></div>
              </div>
            );
          })}
          <hr className="hair" style={{ margin: "8px 0 14px" }} />
          <p className="foot" style={{ margin: 0 }}>
            how sure {pct(res.confidence)} · patterns for human review, not findings
            {res.mirror && <> · mirror claim checked with the same tools and tolerance: {res.mirror.sub_claim_verdicts.join(", ")}</>}
          </p>
        </div>}
      </div></div>
    </section>
  );
}

// ---------------------------------------------------------------- 5. ask

const STATUS_CHIP: Record<CitizenAnswer["status"], [Parameters<typeof Chip>[0]["kind"], string]> = {
  present: ["verified", "In the new list"], modified: ["benign", "Details changed"], not_in_new_list: ["review", "Not in the new list"], not_found: ["quiet", "Not listed"],
};
const PROMPT: Record<"hi" | "en" | "pa", string> = { hi: "meena kumaari booth 47", en: "meena kumaari booth 47", pa: "harpreet kaur booth 63" };

export function Ask() {
  const [lang, setLang] = useState<"hi" | "en" | "pa">("hi");
  const [text, setText] = useState(PROMPT.hi);
  const [res, setRes] = useState<CitizenAnswer | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(false);
  const go = () => { if (!text.trim()) return; setBusy(true); setErr(false); ask(text.trim(), lang).then(setRes).catch(() => setErr(true)).finally(() => setBusy(false)); };
  const chip = res ? STATUS_CHIP[res.status] : null;
  return (
    <section id="ask" className="chapter chapter--tall">
      <div className="wrap"><div className="col">
        <p className="eyebrow rise">Ask. For voters.</p>
        <h2 className="title"><Rise text="Is my name still on the list?" /><span className="dim"><Rise text="Why it changed, and what to do next." start={6} /></span></h2>
        <div className="v3seg rise" style={{ "--i": 12, alignSelf: "flex-start" } as React.CSSProperties} role="group" aria-label="Language">
          {([["hi", "हिंदी"], ["en", "English"], ["pa", "ਪੰਜਾਬੀ"]] as const).map(([k, l]) => (
            <button key={k} aria-pressed={lang === k} onClick={() => { setLang(k); setText(PROMPT[k]); setRes(null); }} lang={k}>{l}</button>
          ))}
        </div>
        <form className="row" onSubmit={(e) => { e.preventDefault(); go(); }}>
          <input className="field" style={{ flex: 1, minWidth: 220 }} value={text} onChange={(e) => setText(e.target.value)} aria-label="Your name and booth" maxLength={120} />
          <button className="btn btn--solid" disabled={busy}>{busy ? "Looking…" : "Ask"}</button>
        </form>
        {err && <p className="small">The engine didn&apos;t answer. Try again in a moment.</p>}
        {res && <div className="glass v3card" style={{ display: "flex", flexDirection: "column", gap: 12 }} aria-live="polite">
          {res.match && <div className="row" style={{ justifyContent: "space-between" }}>
            <span style={{ fontSize: 26 }} lang="hi">{res.match.name_dev}</span>
            <span className="foot">booth {res.match.booth_id.slice(1)} · {res.match.voter_id}</span>
          </div>}
          {chip && <div><Chip kind={chip[0]}>{chip[1]}</Chip></div>}
          <p style={{ margin: 0, color: "var(--ink-2)" }} lang={res.lang}>{res.answer_text}</p>
          <p className="foot" style={{ margin: 0 }}>how sure {pct(res.confidence)} · a BLO never asks for an OTP or money · helpline 1950</p>
        </div>}
        <p className="foot">also on WhatsApp +91 80764 99841 and Telegram @Rollwatch_bot, with Hindi voice notes</p>
      </div></div>
    </section>
  );
}

// ---------------------------------------------------------------- 6. tested

export function Tested() {
  const blind = useApi<BlindEval>(() => get("/eval/blind"));
  const lim = useApi<Limits>(() => get("/simulate/limits"));
  const thin = useApi<Sim>(() => simulate("B001", 1000, 100));
  const [booth, setBooth] = useState("B023");
  const [k, setK] = useState(0);
  const [sim, setSim] = useState<Sim | null>(null);
  useEffect(() => {
    let live = true;
    const t = setTimeout(() => simulate(booth, k).then((d) => live && setSim(d)).catch(() => {}), 220);
    return () => { live = false; clearTimeout(t); };
  }, [booth, k]);
  const e = blind.data?.eval, fa = blind.data?.false_alarms;
  const RULE: Record<string, string> = { duplicate_cluster: "duplicate pairs", relation_conflict: "relation conflicts", oversized_household: "oversized households" };
  const record = fa?.by_rule.filter((r) => r.false > 0).map((r) => `${r.false} ${RULE[r.rule] ?? r.rule.replace(/_/g, " ")}`).join(", ");
  const b = sim?.booths?.[0];
  return (
    <section id="tested" className="chapter chapter--tall">
      <div className="wrap"><div className="col col--wide">
        <p className="eyebrow rise">Blind test.</p>
        <h2 className="title"><Rise text="We tested ourselves." /><span className="dim"><Rise text="And counted every false alarm." start={3} /></span></h2>
        <div className="grid3">
          <div className="glass stat"><span className="big-num">{e ? `${e.found}/${e.planted_anomalies}` : "—"}</span><span className="small">planted problems found. A separate agent hid them and kept the key.</span></div>
          <div className="glass stat"><span className="big-num">{e ? `${e.decoys_cleared}/${e.planted_decoys}` : "—"}</span><span className="small">innocent look-alikes cleared, nothing wrongly flagged.</span></div>
          <div className="glass stat"><span className="big-num">{fa ? pct(fa.real_share) : "—"}</span><span className="small">of {fmt(fa?.raised)} flags raised for review were real ({fmt(fa?.raised_real)}).</span></div>
        </div>
        {fa && <p className="small" style={{ margin: 0 }}>{fa.booth_spike_false} false alarms on booth spikes, the flags a rumour is built on. The {fa.raised_false} false ones are record-level: {record}.</p>}

        <div className="glass v3card" style={{ display: "flex", flexDirection: "column", gap: 14, marginTop: 12 }}>
          <p className="eyebrow" style={{ margin: 0 }}>Try to fool it.</p>
          <p style={{ margin: 0, fontSize: 22, lineHeight: 1.25, letterSpacing: "-.02em" }}>Remove names quietly. <span className="dim">The engine reruns the same tests it ran on the roll.</span></p>
          <div className="row">
            <select className="field" style={{ width: "auto", minHeight: 40, padding: "6px 12px" }} value={booth} onChange={(ev) => { setBooth(ev.target.value); setK(0); }} aria-label="Booth">
              {Array.from({ length: 100 }, (_, i) => `B${String(i + 1).padStart(3, "0")}`).filter((x) => x !== "B047").map((x) => <option key={x} value={x}>Booth {Number(x.slice(1))}</option>)}
            </select>
            <span className="mono small">hide <span style={{ color: "var(--ink)" }}>{k}</span> names</span>
            {sim && <Chip kind={sim.caught ? "review" : "quiet"}>{sim.caught ? "Caught · needs human review" : sim.flagged ? "Spike, not sent to review" : "Not caught"}</Chip>}
          </div>
          <input type="range" className="range" min={0} max={60} value={k} onChange={(ev) => setK(Number(ev.target.value))} aria-label="Names to hide" />
          {b && <p className="foot" style={{ margin: 0 }}>{fmt(b.removed_after)} removed against about {b.expected.toFixed(0)} expected · this booth is caught from {sim?.limit} hidden names</p>}
          <hr className="hair" />
          <p className="small" style={{ margin: 0 }}>
            Across booths a median of <span className="num" style={{ color: "var(--ink)" }}>{lim.data?.median ?? "—"}</span> hidden names
            ({lim.data ? `${lim.data.min} to ${lim.data.max}` : "—"}) reaches review.
            {thin.data && <> The blind spot, said out loud: spread 1,000 names over all 100 booths and {thin.data.flagged} booths show a spike, but only {thin.data.caught} reach review.</>}
          </p>
        </div>
      </div></div>
    </section>
  );
}

// ---------------------------------------------------------------- 7. scale

export function Scale() {
  const ops = useApi<Ops>(() => get("/ops"));
  const p = ops.data?.projection;
  const big = ops.data?.bench?.runs.filter((r) => r.workers === 1).sort((a, b) => b.n_v1 - a.n_v1)[0];
  return (
    <section id="scale" className="chapter chapter--tall">
      <div className="wrap"><div className="col col--wide">
        <p className="eyebrow rise">Scale.</p>
        <h2 className="title"><Rise text="A state is just more booths." /><span className="dim"><Rise text="Each one an independent job." start={6} /></span></h2>
        <div className="grid3">
          <div className="glass stat"><span className="big-num">{p ? `${p.audit_minutes_on_64_cores} min` : "—"}</span><span className="small">to audit all {p ? crore(p.electors) : "—"} electors on 64 cores (ECI&apos;s 2024 state table).</span></div>
          <div className="glass stat"><span className="big-num">{p ? `${Math.round(p.checks_per_s_peak)}/s` : "—"}</span><span className="small">peak checks if one voter in ten checks once in a 30-day revision ({p ? `${(p.checks_per_day / 1e5).toFixed(0)} lakh a day` : "—"}).</span></div>
          <div className="glass stat"><span className="big-num">{p ? p.machines_at_peak : "—"}</span><span className="small">machines cover that peak, at {p ? p.citizen_answers_per_s_4proc : "—"} full answers a second measured on one 4-process laptop.</span></div>
        </div>
        {big && <p className="foot">measured · {fmt(big.n_v1)} voters in {(big.total_ms / 1000).toFixed(1)} s on one core · duplicate search uses blocking and union-find, not every pair</p>}
      </div></div>
    </section>
  );
}

// ---------------------------------------------------------------- 8. the three questions

export function Why() {
  const cols: [string, string, string][] = [
    ["How it scales.", "Every test is per booth and linear, so a state is just more booths run in parallel.",
      "It spreads as a share card into the chat the rumour came from, with no install, and the same method fits any list that gets cleaned: ration cards, pensions. Story rules are a config file."],
    ["Why not the government alone.", "A self-audit can't settle a rumour about the auditor.",
      "An office should run it on a draft before publishing (POST /audit). The same open engine stays with newsrooms, observers and citizens, so both sides agree on the arithmetic."],
    ["Why it's future-proof.", "A fixed, measured core. Everything that changes is a swappable part.",
      "Data comes in through adapters, rules live in config, the model only phrases words and never makes a number, and languages and channels are thin layers. The blind test re-measures every change."],
  ];
  return (
    <section id="why" className="chapter">
      <div className="wrap"><div className="col" style={{ maxWidth: 1180 }}>
        <p className="eyebrow rise">Three questions.</p>
        <div className="grid3">
          {cols.map(([e, h, b], i) => (
            <div key={e} className="glass stat rise" style={{ "--i": i * 2 } as React.CSSProperties}>
              <span className="eyebrow">{e}</span>
              <span style={{ fontSize: 24, lineHeight: 1.2, letterSpacing: "-.02em" }}>{h}</span>
              <span className="small">{b}</span>
            </div>
          ))}
        </div>
      </div></div>
    </section>
  );
}

// ---------------------------------------------------------------- 9. connect

export function Connect() {
  return (
    <section id="connect" className="chapter" style={{ minHeight: "110vh", alignItems: "flex-end" }}>
      <div className="wrap"><div className="col center" style={{ maxWidth: 820 }}>
        <p className="eyebrow rise">Connect.</p>
        <h2 className="title"><Rise text="Check it where the rumour arrives." /><span className="dim"><Rise text="WhatsApp, Telegram, or the web." start={6} /></span></h2>
        <div className="links rise" style={{ "--i": 11, justifyContent: "center" } as React.CSSProperties}>
          <a className="btn btn--solid" href={`https://wa.me/${WA_NUMBER}`} target="_blank" rel="noreferrer">WhatsApp</a>
          <a className="btn" href="https://t.me/Rollwatch_bot" target="_blank" rel="noreferrer">Telegram</a>
          <a className="btn" href="/audit">Open the dashboard</a>
          <a className="btn" href="/pricing">For organisations</a>
          <a className="btn" href="https://github.com/nova-rishabh/Hackathon-phy" target="_blank" rel="noreferrer">Source</a>
        </div>
        <p className="foot rise" style={{ "--i": 12 } as React.CSSProperties}>
          synthetic data only · needs calibration on real rolls · not an official service and not affiliated with any official body ·
          check your name at voters.eci.gov.in or call 1950
        </p>
      </div></div>
    </section>
  );
}
