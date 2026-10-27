"use client";
import { useState } from "react";
import Link from "next/link";
import { supabase, useSession } from "@/lib/supabase";
import { Display, Eyebrow } from "@/components/Display";

export default function Login() {
  const { session } = useSession();
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const send = async () => {
    if (!supabase || !email.trim()) return;
    setBusy(true); setMsg("");
    const { error } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { emailRedirectTo: `${window.location.origin}/account` },
    });
    setBusy(false);
    setMsg(error ? `Could not send the link: ${error.message}` : `Link sent to ${email.trim()}. Open it on this device to sign in.`);
  };

  return (
    <div>
      <Eyebrow className="mb-5">Account.</Eyebrow>
      <Display size="hero" dim="Save checks and watch booths. No password, just an email link.">Sign in.</Display>

      <section className="panel mt-16 max-w-[720px]">
        {!supabase ? (
          <>
            <p className="text-[18px] leading-7">Accounts not configured yet.</p>
            <p className="text-[15px] text-ink-2 mt-2">Everything else works without an account. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to turn accounts on.</p>
          </>
        ) : session ? (
          <p className="text-[18px] leading-7">
            Signed in as <span className="mono">{session.user.email}</span>.{" "}
            <Link href="/account" className="underline underline-offset-2">Go to your account</Link>
          </p>
        ) : (
          <form onSubmit={(e) => { e.preventDefault(); send(); }}>
            <label htmlFor="email" className="eyebrow block mb-4">Your email.</label>
            <div className="flex gap-3 flex-col sm:flex-row">
              <input id="email" type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" />
              <button className="btn shrink-0 justify-center" style={{ height: 56 }} disabled={busy || !email.trim()}>{busy ? "Sending…" : "Email me a link"}</button>
            </div>
            {msg && <p className="text-[14px] text-ink-2 mt-4" aria-live="polite">{msg}</p>}
            <p className="mono text-[12px] text-ink-3 mt-5">we store your email, your saved checks and the booths you watch · nothing else</p>
          </form>
        )}
      </section>
    </div>
  );
}
