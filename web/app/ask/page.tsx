"use client";
import { useState } from "react";
import { postJson, boothNo } from "@/lib/api";
import { citizenMock } from "@/lib/mocks";
import type { CitizenAnswer } from "@/lib/types";
import Chip from "@/components/Chip";
import { Display, Eyebrow } from "@/components/Display";

type Lang = "hi" | "en" | "pa";
const LANGS: [Lang, string][] = [["hi", "हिंदी"], ["en", "English"], ["pa", "ਪੰਜਾਬੀ"]];
const STATUS: Record<string, [string, string]> = {
  present: ["verified", "In the new list"],
  modified: ["review", "Details changed"],
  not_in_new_list: ["review", "Not in the new list"],
  not_found: ["unprovable", "No match found"],
};
const REASON: Record<string, string> = {
  shifted: "Marked as shifted to another address.",
  death_registered: "Matched to an entry in the death register.",
  duplicate_cleanup: "Treated as a duplicate of another entry.",
  boundary_change: "The house moved to another booth in a boundary change.",
  unexplained: "No record explains this change. A human should check it.",
  none: "No change to explain.",
};
const PLACEHOLDER: Record<Lang, string> = {
  hi: "अपना नाम और बूथ लिखें, जैसे: मीना कुमारी बूथ 47",
  en: "Your name and booth, e.g. meena kumaari booth 47",
  pa: "ਆਪਣਾ ਨਾਮ ਅਤੇ ਬੂਥ ਲਿਖੋ",
};

type Msg = { me: string } | { rw: CitizenAnswer; mocked: boolean } | { err: string };

export default function Ask() {
  const [lang, setLang] = useState<Lang>("hi");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState<Msg[]>([]);

  const send = async () => {
    const q = text.trim();
    if (!q) return;
    setLog((l) => [...l, { me: q }]);
    setText(""); setBusy(true);
    try {
      const a = await postJson<CitizenAnswer>("/citizen/ask", { text: q, lang, channel: "web" }, 20000);
      setLog((l) => [...l, { rw: a, mocked: false }]);
    } catch {
      const m = citizenMock(q, lang);
      setLog((l) => [...l, m ? { rw: m, mocked: true } : { err: "The lookup service is not reachable right now. Try again in a minute." }]);
    }
    setBusy(false);
  };

  return (
    <div>
      <Eyebrow className="mb-5">Ask. For voters.</Eyebrow>
      <Display size="hero" dim="Type your name and booth. We tell you why, and what to do next.">Is my name still on the list?</Display>

      <div className="mt-16 flex flex-wrap gap-x-8 gap-y-2" role="group" aria-label="Language">
        {LANGS.map(([k, l]) => (
          <button key={k} className="opt" lang={k} aria-pressed={lang === k} onClick={() => setLang(k)}>{l}</button>
        ))}
      </div>

      <section className="panel mt-8">
        <div className="grid gap-4" aria-live="polite">
          {log.length === 0 && <p className="text-ink-2 text-[15px]">Try <button className="mono underline underline-offset-2 text-ink" onClick={() => setText("meena kumaari booth 47")}>meena kumaari booth 47</button></p>}
          {log.map((m, i) =>
            "me" in m ? <p key={i} className="bubble bubble--me">{m.me}</p>
            : "err" in m ? <p key={i} className="bubble bubble--rw text-ink-2">{m.err}</p>
            : <Status key={i} a={m.rw} mocked={m.mocked} />,
          )}
          {busy && <p className="mono text-[13px] text-ink-3">looking up the roll…</p>}
        </div>
        <form className="mt-6 flex gap-3 flex-col sm:flex-row" onSubmit={(e) => { e.preventDefault(); send(); }}>
          <input className="input" lang={lang} value={text} onChange={(e) => setText(e.target.value)} placeholder={PLACEHOLDER[lang]} aria-label="Your question" />
          <button className="btn shrink-0 justify-center" style={{ height: 56 }} disabled={busy || !text.trim()}>Ask</button>
        </form>
      </section>
    </div>
  );
}

function Status({ a, mocked }: { a: CitizenAnswer; mocked: boolean }) {
  const [kind, label] = STATUS[a.status] ?? ["unprovable", a.status];
  const m = a.match;
  const scriptLang = a.lang === "en" ? "en" : "hi";
  return (
    <div className="bubble bubble--rw" style={{ maxWidth: 720 }}>
      {m && (
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <p className="text-[28px] leading-9 tracking-[-0.02em]" lang={scriptLang}>{a.lang === "en" ? m.name_lat : m.name_dev}</p>
          <p className="mono text-[13px] text-ink-2">booth {String(boothNo(m.booth_id)).padStart(3, "0")} · {m.voter_id}</p>
        </div>
      )}
      <div className="mt-3"><Chip kind={kind} label={label} /></div>
      <p className="mt-4 text-[16px] leading-7" lang={a.lang}>{a.answer_text}</p>
      {a.reason_category !== "none" && <p className="mt-2 text-[14px] text-ink-2"><span className="eyebrow">why. </span>{REASON[a.reason_category]}</p>}
      {a.next_steps.length > 0 && (
        <>
          <p className="eyebrow mt-5 mb-2">Next steps.</p>
          <ol className="grid gap-2" lang={a.lang}>
            {a.next_steps.map((s, i) => (
              <li key={i} className="grid grid-cols-[28px_1fr] text-[15px]"><span className="mono text-ink-3">{i + 1}.</span><span>{s}</span></li>
            ))}
          </ol>
        </>
      )}
      <p className="mono text-[12px] text-ink-3 mt-5 pt-4 border-t border-line">
        how sure {Math.round(a.confidence * 100)}% · needs human review · confirm on the official voter portal or call 1950
        {mocked && " · mock data, api not reachable"}
      </p>
      {a.answer_audio_url && <audio className="mt-3 w-full" controls src={a.answer_audio_url} />}
    </div>
  );
}
