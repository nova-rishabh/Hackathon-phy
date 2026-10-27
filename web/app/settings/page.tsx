"use client";
import { useEffect, useState } from "react";
import { getJson } from "@/lib/api";
import { getKey, setKey, type KeyName } from "@/lib/keys";
import Chip from "@/components/Chip";
import { Display, Eyebrow } from "@/components/Display";

type Src = "byok" | "server" | "none";
type Status = Record<KeyName, Src>;
const ROWS: [KeyName, string, string][] = [
  ["gemini", "Gemini API key", "Phrases answers, splits claims and reads screenshots. Numbers are always computed in Python."],
  ["elevenlabs", "ElevenLabs API key", "Voice on the Ask page: Listen and Speak."],
];
const SRC: Record<Src, [string, string]> = {
  byok: ["verified", "Using your key"],
  server: ["benign", "Using the server key"],
  none: ["unprovable", "No key"],
};

export default function Settings() {
  const [status, setStatus] = useState<Status | null>(null);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    getJson<Status>("/keys/status").then((r) => setStatus(r.data));
  }, [tick]);

  return (
    <div>
      <Eyebrow className="mb-5">Keys.</Eyebrow>
      <Display size="hero" dim="Use your own Gemini and ElevenLabs keys. They stay in this browser.">Bring your own keys.</Display>
      <p className="text-[16px] text-ink-2 mt-8 max-w-[64ch]">
        Keys are saved only in this browser&apos;s local storage. They never leave it, except as request headers
        (X-Gemini-Key, X-ElevenLabs-Key) to the RollWatch API. We never store them in a database.
      </p>

      <section className="panel mt-12 grid gap-3" style={{ padding: 12 }}>
        {ROWS.map(([k, label, why]) => (
          <KeyRow key={k} k={k} label={label} why={why} src={status?.[k]} onChange={() => setTick((t) => t + 1)} />
        ))}
      </section>
      <p className="mono text-[12px] text-ink-3 mt-4">
        {status ? "status from GET /keys/status" : "api not reachable · status unknown"}
      </p>
    </div>
  );
}

function KeyRow({ k, label, why, src, onChange }: { k: KeyName; label: string; why: string; src?: Src; onChange: () => void }) {
  const [val, setVal] = useState("");
  const [saved, setSaved] = useState("");
  const [show, setShow] = useState(false);
  useEffect(() => { const v = getKey(k); setVal(v); setSaved(v); }, [k]);
  const save = (v: string) => { setKey(k, v); setVal(v.trim()); setSaved(v.trim()); onChange(); };

  return (
    <div className="card p-5 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <label htmlFor={`key-${k}`} className="text-[18px] font-medium">{label}</label>
        {src && <Chip kind={SRC[src][0]} label={SRC[src][1]} />}
      </div>
      <p className="text-[14px] text-ink-2 mt-1">{why}</p>
      <div className="flex gap-3 flex-col sm:flex-row mt-4">
        <input id={`key-${k}`} className="input mono" type={show ? "text" : "password"} value={val} autoComplete="off" spellCheck={false}
          onChange={(e) => setVal(e.target.value)} placeholder="paste key" />
        <div className="flex gap-2 shrink-0">
          <button className="btn btn--quiet" type="button" onClick={() => setShow(!show)}>{show ? "Hide" : "Show"}</button>
          <button className="btn" type="button" disabled={val.trim() === saved} onClick={() => save(val)}>Save</button>
          <button className="btn btn--quiet" type="button" disabled={!saved && !val} onClick={() => save("")}>Clear</button>
        </div>
      </div>
      <p className="mono text-[12px] text-ink-3 mt-3">{saved ? `saved in this browser · ends ${saved.slice(-4)}` : "not set in this browser"}</p>
    </div>
  );
}
