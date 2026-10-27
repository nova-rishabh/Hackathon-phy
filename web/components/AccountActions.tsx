"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { authFetch, useSession, type WatchedBooth } from "@/lib/auth";
import { boothNo } from "@/lib/api";

const ok = (s: number) => s >= 200 && s < 300;

/** "Save this check": renders nothing unless signed in. */
export function SaveCheck({ claimId, claimText, overall }: { claimId: string; claimText: string; overall: string }) {
  const { user } = useSession();
  const [state, setState] = useState<"idle" | "busy" | "saved" | "error">("idle");
  useEffect(() => setState("idle"), [claimId]);
  if (!user) return null;
  const save = async () => {
    setState("busy");
    const r = await authFetch("/me/checks", { method: "POST", body: JSON.stringify({ claim_id: claimId, claim_text: claimText, overall }) });
    setState(ok(r.status) ? "saved" : "error");
  };
  return state === "saved"
    ? <span className="mono text-[13px] text-ink-2">saved · <Link href="/account" className="underline underline-offset-2 hover:text-ink">your account</Link></span>
    : <button className="btn btn--quiet" disabled={state === "busy"} onClick={save}>{state === "error" ? "Could not save. Try again" : state === "busy" ? "Saving…" : "Save this check"}</button>;
}

/** "Watch this booth": renders nothing unless signed in. */
export function WatchBooth({ boothId }: { boothId: string }) {
  const { user } = useSession();
  const [on, setOn] = useState<boolean | null>(null);
  useEffect(() => {
    if (!user) return;
    setOn(null);
    authFetch<WatchedBooth[]>("/me/booths").then((r) => setOn(Array.isArray(r.body) && r.body.some((b) => b.booth_id === boothId)));
  }, [boothId, user]);
  if (!user) return null;
  const toggle = async () => {
    const was = on;
    setOn(!was);
    const r = was
      ? await authFetch(`/me/booths/${encodeURIComponent(boothId)}`, { method: "DELETE" })
      : await authFetch("/me/booths", { method: "POST", body: JSON.stringify({ booth_id: boothId }) });
    if (!ok(r.status)) setOn(was);
  };
  return (
    <button className="btn btn--quiet" disabled={on === null} onClick={toggle} aria-pressed={!!on}>
      {on ? `Watching Booth ${boothNo(boothId)} · stop` : "Watch this booth"}
    </button>
  );
}

/** "Mark reviewed": a signed-in person records what they found. Written to a hash-chained audit log. */
export function ReviewFlag({ flagId, current }: { flagId: string; current?: { status: string; hash: string } | null }) {
  const { user } = useSession();
  const [note, setNote] = useState("");
  const [done, setDone] = useState<{ status: string; hash: string } | null>(current ?? null);
  const [state, setState] = useState<"idle" | "busy" | "error">("idle");
  useEffect(() => { setDone(current ?? null); setNote(""); setState("idle"); }, [flagId, current]);
  const send = async (status: "benign" | "escalated") => {
    setState("busy");
    const r = await authFetch<{ review: { status: string; hash: string } }>(`/review/${encodeURIComponent(flagId)}`,
      { method: "POST", body: JSON.stringify({ status, note }) });
    if (ok(r.status) && r.body) { setDone(r.body.review); setState("idle"); } else setState("error");
  };
  if (done)
    return (
      <p className="text-[14px] text-ink-2">
        Reviewed: <span className="text-ink">{done.status === "benign" ? "looks innocent" : "needs a field check"}</span>
        <span className="mono text-[12px] text-ink-3"> · audit hash {done.hash.slice(0, 10)}</span>
      </p>
    );
  if (!user)
    return <p className="text-[14px] text-ink-2"><Link href="/login" className="underline underline-offset-2 hover:text-ink">Sign in</Link> to record a review of this flag.</p>;
  return (
    <div className="grid gap-3">
      <input className="input" value={note} maxLength={280} onChange={(e) => setNote(e.target.value)} placeholder="What did you check? (optional, never shown publicly)" />
      <div className="flex flex-wrap gap-2">
        <button className="btn btn--quiet" disabled={state === "busy"} onClick={() => send("benign")}>Looks innocent</button>
        <button className="btn" disabled={state === "busy"} onClick={() => send("escalated")}>Needs a field check</button>
      </div>
      {state === "error" && <p className="text-[13px] text-ink-2">Could not record it. Sign in again and retry.</p>}
    </div>
  );
}
