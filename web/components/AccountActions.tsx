"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { supabase, useSession } from "@/lib/supabase";
import { boothNo } from "@/lib/api";

/** "Save this check": renders nothing unless signed in. */
export function SaveCheck({ claimId, claimText, overall }: { claimId: string; claimText: string; overall: string }) {
  const { session } = useSession();
  const [state, setState] = useState<"idle" | "busy" | "saved" | "error">("idle");
  useEffect(() => setState("idle"), [claimId]);
  if (!supabase || !session) return null;
  const save = async () => {
    setState("busy");
    const { error } = await supabase!.from("saved_checks").insert({ claim_id: claimId, claim_text: claimText, overall });
    setState(error ? "error" : "saved");
  };
  return state === "saved"
    ? <span className="mono text-[13px] text-ink-2">saved · <Link href="/account" className="underline underline-offset-2 hover:text-ink">your account</Link></span>
    : <button className="btn btn--quiet" disabled={state === "busy"} onClick={save}>{state === "error" ? "Could not save. Try again" : state === "busy" ? "Saving…" : "Save this check"}</button>;
}

/** "Watch this booth": renders nothing unless signed in. */
export function WatchBooth({ boothId }: { boothId: string }) {
  const { session } = useSession();
  const [on, setOn] = useState<boolean | null>(null);
  useEffect(() => {
    if (!supabase || !session) return;
    setOn(null);
    supabase.from("watched_booths").select("booth_id").eq("booth_id", boothId).maybeSingle()
      .then(({ data }) => setOn(!!data));
  }, [boothId, session]);
  if (!supabase || !session) return null;
  const toggle = async () => {
    const was = on;
    setOn(!was);
    const q = was
      ? supabase!.from("watched_booths").delete().eq("booth_id", boothId)
      : supabase!.from("watched_booths").insert({ booth_id: boothId });
    const { error } = await q;
    if (error) setOn(was);
  };
  return (
    <button className="btn btn--quiet" disabled={on === null} onClick={toggle} aria-pressed={!!on}>
      {on ? `Watching Booth ${boothNo(boothId)} · stop` : "Watch this booth"}
    </button>
  );
}
