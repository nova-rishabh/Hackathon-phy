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
