"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authFetch, setToken, useSession, type User } from "@/lib/auth";
import { Display, Eyebrow } from "@/components/Display";

type StartOk = { sent: true; to: string; expires_in: number };
type Err = { error?: string; retry_in?: number; attempts_left?: number };

const LEN = 6;
const RESEND = 60;

function startError(status: number, b: Err | null): string {
  if (status === 422) return "That number does not look right. Check the digits and the country code.";
  if (status === 429) return `Too many codes asked for. Try again in ${b?.retry_in ?? 60} seconds.`;
  if (status === 503) return "Our WhatsApp sender is offline right now. Try again in a minute.";
  if (status === 0) return "Could not reach RollWatch. Check your connection and try again.";
  return "Could not send the code. Try again in a minute.";
}

function verifyError(status: number, b: Err | null): string {
  if (status === 401) {
    const n = b?.attempts_left;
    if (n === 0) return "That code is wrong and no tries are left. Ask for a new code.";
    return n != null ? `That code is wrong. ${n} ${n === 1 ? "try" : "tries"} left.` : "That code is wrong. Check the message and try again.";
  }
  if (status === 410) return "That code has expired. Ask for a new one.";
  if (status === 429) return `Too many tries. Wait ${b?.retry_in ?? 60} seconds and ask for a new code.`;
  if (status === 0) return "Could not reach RollWatch. Check your connection and try again.";
  return "Could not check the code. Try again.";
}

export default function Login() {
  const { user, loading } = useSession();
  const router = useRouter();
  const [cc, setCc] = useState("+91");
  const [num, setNum] = useState("");
  const [step, setStep] = useState<"number" | "code">("number");
  const [to, setTo] = useState("");
  const [digits, setDigits] = useState<string[]>(Array(LEN).fill(""));
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [wait, setWait] = useState(0);
  const boxes = useRef<(HTMLInputElement | null)[]>([]);

  const mobile = `${cc.trim().startsWith("+") ? cc.trim() : "+" + cc.trim()}${num.replace(/\D/g, "")}`;
  const numOk = num.replace(/\D/g, "").length >= 6;

  useEffect(() => {
    if (wait <= 0) return;
    const t = setTimeout(() => setWait((w) => w - 1), 1000);
    return () => clearTimeout(t);
  }, [wait]);

  const send = async () => {
    if (!numOk || busy) return;
    setBusy(true); setMsg("");
    const r = await authFetch<StartOk & Err>("/auth/wa/start", { method: "POST", body: JSON.stringify({ mobile }) });
    setBusy(false);
    if (r.status === 200 && r.body?.sent) {
      setTo(r.body.to); setStep("code"); setDigits(Array(LEN).fill("")); setWait(RESEND);
      setTimeout(() => boxes.current[0]?.focus(), 0);
    } else {
      setMsg(startError(r.status, r.body));
      if (r.status === 429 && r.body?.retry_in) setWait(r.body.retry_in);
    }
  };

  const verify = async (code: string) => {
    if (busy) return;
    setBusy(true); setMsg("");
    const r = await authFetch<{ token: string; user: User } & Err>("/auth/wa/verify", { method: "POST", body: JSON.stringify({ mobile, code }) });
    setBusy(false);
    if (r.status === 200 && r.body?.token) { setToken(r.body.token); router.push("/account"); return; }
    setMsg(verifyError(r.status, r.body));
    setDigits(Array(LEN).fill(""));
    setTimeout(() => boxes.current[0]?.focus(), 0);
  };

  const fill = (start: number, chars: string) => {
    const next = [...digits];
    let i = start;
    for (const ch of chars) { if (i >= LEN) break; next[i++] = ch; }
    setDigits(next);
    boxes.current[Math.min(i, LEN - 1)]?.focus();
    if (next.every((d) => d)) verify(next.join(""));
  };

  const onKey = (i: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !digits[i] && i > 0) {
      e.preventDefault();
      const next = [...digits]; next[i - 1] = ""; setDigits(next);
      boxes.current[i - 1]?.focus();
    } else if (e.key === "ArrowLeft" && i > 0) boxes.current[i - 1]?.focus();
    else if (e.key === "ArrowRight" && i < LEN - 1) boxes.current[i + 1]?.focus();
  };

  return (
    <div>
      <Eyebrow className="mb-5">Account.</Eyebrow>
      <Display size="hero" dim="Save checks and watch booths. No password, just a code on WhatsApp.">Sign in.</Display>

      <section className="panel mt-16 max-w-[720px]">
        {loading ? (
          <p className="mono text-[13px] text-ink-3">loading…</p>
        ) : user ? (
          <p className="text-[18px] leading-7">
            Signed in as <span className="mono">{user.mobile_masked}</span>.{" "}
            <Link href="/account" className="underline underline-offset-2">Go to your account</Link>
          </p>
        ) : step === "number" ? (
          <form onSubmit={(e) => { e.preventDefault(); send(); }}>
            <label htmlFor="mobile" className="eyebrow block mb-4">Your mobile number.</label>
            <div className="flex gap-3 flex-col sm:flex-row">
              <div className="flex gap-2 flex-1">
                <input aria-label="Country code" className="input mono shrink-0 text-center" style={{ width: 84 }} value={cc}
                  onChange={(e) => setCc(e.target.value.replace(/[^\d+]/g, "").slice(0, 5))} inputMode="tel" />
                <input id="mobile" className="input mono" value={num} onChange={(e) => setNum(e.target.value.replace(/[^\d\s]/g, ""))}
                  placeholder="98765 41234" inputMode="numeric" autoComplete="tel-national" />
              </div>
              <button className="btn shrink-0 justify-center" style={{ height: 56 }} disabled={busy || !numOk || wait > 0}>
                {busy ? "Sending…" : wait > 0 ? `Wait ${wait} s` : "Send code on WhatsApp"}
              </button>
            </div>
            {msg && <p className="text-[14px] text-ink-2 mt-4" aria-live="polite">{msg}</p>}
            <p className="mono text-[12px] text-ink-3 mt-5">We keep your number, your saved checks and the booths you watch. Nothing else.</p>
          </form>
        ) : (
          <form onSubmit={(e) => { e.preventDefault(); if (digits.every((d) => d)) verify(digits.join("")); }}>
            <p className="eyebrow mb-2">The code we sent.</p>
            <p className="text-[15px] text-ink-2 mb-6">Six digits, sent on WhatsApp to <span className="mono text-ink">{to}</span>. It works for 5 minutes.</p>
            <div className="flex gap-2 sm:gap-3" role="group" aria-label="Six digit code">
              {digits.map((d, i) => (
                <input key={i} ref={(el) => { boxes.current[i] = el; }} value={d} aria-label={`Digit ${i + 1}`}
                  className="input mono text-center !p-0 text-[24px]" style={{ width: 52, height: 60 }}
                  inputMode="numeric" autoComplete={i === 0 ? "one-time-code" : "off"} maxLength={LEN} disabled={busy}
                  onFocus={(e) => e.target.select()}
                  onKeyDown={(e) => onKey(i, e)}
                  onPaste={(e) => { e.preventDefault(); const t = e.clipboardData.getData("text").replace(/\D/g, ""); if (t) fill(t.length >= LEN ? 0 : i, t); }}
                  onChange={(e) => {
                    const v = e.target.value.replace(/\D/g, "");
                    if (!v) { const n = [...digits]; n[i] = ""; setDigits(n); return; }
                    fill(v.length >= LEN ? 0 : i, v.length > 1 && v.length < LEN ? v.slice(-1) : v);
                  }} />
              ))}
            </div>
            {msg && <p className="text-[14px] text-ink-2 mt-4" aria-live="polite">{msg}</p>}
            {busy && <p className="mono text-[12px] text-ink-3 mt-4">checking…</p>}
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2 mt-6 mono text-[13px] text-ink-2">
              {wait > 0
                ? <span className="text-ink-3">new code in {wait} s</span>
                : <button type="button" className="underline underline-offset-2 hover:text-ink" onClick={send} disabled={busy}>send a new code</button>}
              <button type="button" className="underline underline-offset-2 hover:text-ink"
                onClick={() => { setStep("number"); setMsg(""); setWait(0); setDigits(Array(LEN).fill("")); }}>change number</button>
            </div>
            <p className="mono text-[12px] text-ink-3 mt-6">We keep your number, your saved checks and the booths you watch. Nothing else.</p>
          </form>
        )}
      </section>
    </div>
  );
}
