"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { postJson, postBlob, getJson, ApiError, boothNo } from "@/lib/api";
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
  not_found: ["unprovable", "Not listed"],
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

  const [voiceErr, setVoiceErr] = useState<"" | "nokey" | "fail">("");
  const [rec, setRec] = useState<"idle" | "rec" | "busy">("idle");
  const recRef = useRef<MediaRecorder | null>(null);

  const onVoiceErr = (e: unknown) => setVoiceErr(e instanceof ApiError && e.status === 503 ? "nokey" : "fail");

  const speak = async () => {
    if (rec === "rec") { recRef.current?.stop(); return; }
    setVoiceErr("");
    let stream: MediaStream;
    try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); } catch { setVoiceErr("fail"); return; }
    const mr = new MediaRecorder(stream);
    const parts: Blob[] = [];
    mr.ondataavailable = (e) => { if (e.data.size) parts.push(e.data); };
    mr.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      setRec("busy");
      try {
        const mime = mr.mimeType || "audio/webm";
        const b64 = await blobToB64(new Blob(parts, { type: mime }));
        const r = await postJson<{ text: string }>("/voice/stt", { audio_b64: b64, mime, lang }, 30000);
        if (r.text?.trim()) { setText(r.text); await send(r.text); }
      } catch (e) { onVoiceErr(e); }
      setRec("idle");
    };
    recRef.current = mr;
    mr.start();
    setRec("rec");
  };

  const send = async (said?: string) => {
    const q = (said ?? text).trim();
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
            : <Status key={i} a={m.rw} mocked={m.mocked} onVoiceErr={onVoiceErr} />,
          )}
          {busy && <p className="mono text-[13px] text-ink-3">looking up the roll…</p>}
        </div>
        <form className={`composer ${log.length ? "mt-6" : "mt-4"}`} onSubmit={(e) => { e.preventDefault(); send(); }}>
          <input className="composer-input" lang={lang} value={text} onChange={(e) => setText(e.target.value)} placeholder={PLACEHOLDER[lang]} aria-label="Your question" />
          <div className="composer-actions">
            <button type="button" className="btn btn--quiet" disabled={busy || rec === "busy"} onClick={speak} aria-pressed={rec === "rec"}>
              {rec === "rec" ? "Stop" : rec === "busy" ? "Listening…" : "Speak"}
            </button>
            <button className="btn" disabled={busy || !text.trim()}>Ask</button>
          </div>
        </form>
        {voiceErr && (
          <p className="text-[14px] text-ink-2 mt-3" aria-live="polite">
            {voiceErr === "nokey"
              ? <>Voice needs an ElevenLabs key: add one in <Link href="/settings" className="underline underline-offset-2 text-ink">Keys</Link>.</>
              : "Voice did not work this time. Type your question instead."}
          </p>
        )}
      </section>

      <Documents lang={lang} />
    </div>
  );
}

type Docs = { bracket: string | null; lines: string[]; other: string[]; list: string; source: string };
const DOCS_UI: Record<Lang, { eyebrow: string; title: string; dim: string; label: string; all: string }> = {
  hi: { eyebrow: "दस्तावेज़।", title: "नोटिस आए तो कौन-से दस्तावेज़?", dim: "अपनी जन्म-तिथि डालें।", label: "जन्म-तिथि", all: "सभी स्थितियाँ देखें" },
  en: { eyebrow: "Documents.", title: "Got a notice? Which documents.", dim: "Enter your date of birth.", label: "Date of birth", all: "Show every case" },
  pa: { eyebrow: "ਦਸਤਾਵੇਜ਼।", title: "ਨੋਟਿਸ ਆਵੇ ਤਾਂ ਕਿਹੜੇ ਦਸਤਾਵੇਜ਼?", dim: "ਆਪਣੀ ਜਨਮ-ਤਾਰੀਖ਼ ਪਾਓ।", label: "ਜਨਮ-ਤਾਰੀਖ਼", all: "ਸਾਰੀਆਂ ਸਥਿਤੀਆਂ ਵੇਖੋ" },
};

/** From the BLO's SIR information sheet: the API decides the bracket from the date of birth. */
function Documents({ lang }: { lang: Lang }) {
  const [dob, setDob] = useState("");
  const [d, setD] = useState<Docs | null>(null);
  const ui = DOCS_UI[lang];
  const shown = useRef(false);
  useEffect(() => { if (shown.current) load(dob); }, [lang]); // eslint-disable-line react-hooks/exhaustive-deps
  const load = async (v: string) => {
    shown.current = true;
    const q = new URLSearchParams({ lang, ...(v ? { dob: v } : {}) });
    const r = await getJson<Docs>(`/documents?${q}`);
    setD(r.data);
  };
  return (
    <section id="documents" className="panel mt-6 scroll-mt-24">
      <Eyebrow className="mb-4">{ui.eyebrow}</Eyebrow>
      <Display size="section" as="h2" dim={ui.dim}>{ui.title}</Display>
      <div className="flex flex-wrap items-center gap-3 mt-6">
        <label className="flex items-center gap-3">
          <span className="text-[15px] text-ink-2" lang={lang}>{ui.label}</span>
          <input type="date" className="input" style={{ width: 220, padding: "10px 14px" }} value={dob} min="1900-01-01" max="2010-12-31"
            onChange={(e) => { setDob(e.target.value); if (e.target.value) load(e.target.value); }} />
        </label>
        <button className="btn btn--quiet !bg-panel-2" onClick={() => { setDob(""); load(""); }} lang={lang}>{ui.all}</button>
      </div>
      {d && (
        <div className="card p-5 mt-5 stagger" lang={lang}>
          {d.lines.map((l, i) => <p key={i} className={i === 0 ? "text-[15px] text-ink-2" : "text-[18px] leading-7 tracking-[-0.01em] mt-2"}>{l}</p>)}
          <p className="text-[14px] leading-6 text-ink-2 mt-4">{d.list}</p>
          <ul className="mt-3 grid gap-1">{d.other.map((o) => <li key={o} className="text-[14px] text-ink-2">{o}</li>)}</ul>
          <p className="mono text-[12px] text-ink-3 mt-4">{d.source}</p>
        </div>
      )}
    </section>
  );
}

const blobToB64 = (b: Blob) => new Promise<string>((ok, no) => {
  const r = new FileReader();
  r.onload = () => ok(String(r.result).split(",")[1] ?? "");
  r.onerror = no;
  r.readAsDataURL(b);
});

function Listen({ text, lang, onErr }: { text: string; lang: string; onErr: (e: unknown) => void }) {
  const [state, setState] = useState<"idle" | "busy" | "play">("idle");
  const audio = useRef<HTMLAudioElement | null>(null);
  const url = useRef<string>("");
  const play = async () => {
    if (state === "play") { audio.current?.pause(); setState("idle"); return; }
    try {
      if (!url.current) {
        setState("busy");
        url.current = URL.createObjectURL(await postBlob("/voice/tts", { text, lang }));
      }
      const el = audio.current ?? new Audio();
      audio.current = el;
      el.src = url.current;
      el.onended = () => setState("idle");
      await el.play();
      setState("play");
    } catch (e) { setState("idle"); onErr(e); }
  };
  return (
    <button type="button" className="btn btn--quiet" onClick={play} disabled={state === "busy"} aria-pressed={state === "play"}>
      {state === "busy" ? "Loading…" : state === "play" ? "Stop" : "Listen"}
    </button>
  );
}

function Status({ a, mocked, onVoiceErr }: { a: CitizenAnswer; mocked: boolean; onVoiceErr: (e: unknown) => void }) {
  const [kind, label] = STATUS[a.status] ?? ["unprovable", a.status];
  const m = a.match;
  const scriptLang = a.lang === "en" ? "en" : "hi";
  return (
    <div className="bubble bubble--rw stagger" style={{ maxWidth: 720 }}>
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
        {a.match ? `how sure ${Math.round(a.confidence * 100)}%` : "no name matched closely enough"} · needs human review · confirm on the official voter portal or call 1950
        {mocked && " · mock data, api not reachable"}
      </p>
      {a.answer_audio_url
        ? <audio className="mt-3 w-full" controls src={a.answer_audio_url} />
        : <div className="mt-4"><Listen text={a.answer_text} lang={a.lang} onErr={onVoiceErr} /></div>}
    </div>
  );
}
