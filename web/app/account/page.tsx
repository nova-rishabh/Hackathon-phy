"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { supabase, useSession, signOut, type SavedCheck, type WatchedBooth } from "@/lib/supabase";
import { boothNo } from "@/lib/api";
import Chip from "@/components/Chip";
import { Display, Eyebrow } from "@/components/Display";

export default function Account() {
  const { session, ready } = useSession();
  const router = useRouter();
  const [checks, setChecks] = useState<SavedCheck[] | null>(null);
  const [booths, setBooths] = useState<WatchedBooth[] | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!supabase || !session) return;
    supabase.from("saved_checks").select("id, claim_id, claim_text, overall, created_at").order("created_at", { ascending: false })
      .then(({ data, error }) => { if (error) setErr(error.message); setChecks((data as SavedCheck[]) ?? []); });
    supabase.from("watched_booths").select("booth_id, created_at").order("booth_id")
      .then(({ data, error }) => { if (error) setErr(error.message); setBooths((data as WatchedBooth[]) ?? []); });
  }, [session]);

  const unwatch = async (id: string) => {
    if (!supabase) return;
    const { error } = await supabase.from("watched_booths").delete().eq("booth_id", id);
    if (error) setErr(error.message); else setBooths((b) => (b ?? []).filter((x) => x.booth_id !== id));
  };

  if (!supabase || (ready && !session))
    return (
      <div>
        <Eyebrow className="mb-5">Account.</Eyebrow>
        <Display size="hero" dim={supabase ? "Sign in to see your saved checks." : "Accounts not configured yet."}>Your account.</Display>
        <p className="mt-10"><Link href="/login" className="btn">Sign in</Link></p>
      </div>
    );
  if (!session) return <p className="mono text-[13px] text-ink-3">loading…</p>;

  return (
    <div>
      <Eyebrow className="mb-5">Account.</Eyebrow>
      <Display size="page" dim={session.user.email ?? ""}>Your account.</Display>
      <div className="mt-8">
        <button className="btn btn--quiet" onClick={async () => { await signOut(); router.push("/"); }}>Sign out</button>
      </div>
      {err && <p className="text-[14px] text-ink-2 mt-4">Could not load everything: {err}</p>}

      <section className="mt-20">
        <Display size="section" as="h2" dim={checks ? `${checks.length} saved.` : undefined}>Your saved checks.</Display>
        <div className="panel mt-6" style={{ padding: 12 }}>
          {checks === null ? <p className="mono text-[13px] text-ink-3 p-4">loading…</p>
            : checks.length === 0 ? <p className="text-ink-2 p-4">No saved checks yet. Check a claim and press Save this check.</p>
            : (
              <ul className="grid gap-3">
                {checks.map((c) => (
                  <li key={c.id} className="card p-5 grid gap-3 md:grid-cols-[180px_1fr_auto] md:items-center">
                    <span><Chip kind={c.overall} /></span>
                    <span className="text-[17px] leading-6 tracking-[-0.01em]">“{c.claim_text}”</span>
                    <span className="mono text-[12px] text-ink-2">
                      {new Date(c.created_at).toLocaleDateString("en-IN")} ·{" "}
                      <Link className="underline underline-offset-2 hover:text-ink" href={`/card/${encodeURIComponent(c.claim_id)}`}>card</Link>
                    </span>
                  </li>
                ))}
              </ul>
            )}
        </div>
      </section>

      <section className="mt-20">
        <Display size="section" as="h2" dim={booths ? `${booths.length} watched.` : undefined}>Booths you watch.</Display>
        <div className="panel mt-6">
          {booths === null ? <p className="mono text-[13px] text-ink-3">loading…</p>
            : booths.length === 0 ? <p className="text-ink-2">No booths yet. Open a booth on the Audit page and press Watch this booth.</p>
            : (
              <ul className="flex flex-wrap gap-2">
                {booths.map((b) => (
                  <li key={b.booth_id} className="card inline-flex items-center gap-3 pl-4 pr-2 h-10" style={{ borderRadius: 8 }}>
                    <span className="mono text-[14px]">Booth {boothNo(b.booth_id)}</span>
                    <button className="mono text-[12px] text-ink-3 hover:text-ink px-2 h-8" onClick={() => unwatch(b.booth_id)} aria-label={`Stop watching booth ${boothNo(b.booth_id)}`}>remove</button>
                  </li>
                ))}
              </ul>
            )}
        </div>
      </section>
    </div>
  );
}
