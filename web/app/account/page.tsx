"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { authFetch, useSession, type SavedCheck, type WatchedBooth } from "@/lib/auth";
import { boothNo } from "@/lib/api";
import Chip from "@/components/Chip";
import { Display, Eyebrow } from "@/components/Display";
import Loader, { PageLoader } from "@/components/Loader";

export default function Account() {
  const { user, loading, signOut } = useSession();
  const router = useRouter();
  const [checks, setChecks] = useState<SavedCheck[] | null>(null);
  const [booths, setBooths] = useState<WatchedBooth[] | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!user) return;
    authFetch<SavedCheck[]>("/me/checks").then((r) => {
      if (r.status !== 200) setErr("saved checks did not load");
      const list = Array.isArray(r.body) ? r.body : [];
      setChecks([...list].sort((x, y) => y.created_at.localeCompare(x.created_at)));
    });
    authFetch<WatchedBooth[]>("/me/booths").then((r) => {
      if (r.status !== 200) setErr("watched booths did not load");
      const list = Array.isArray(r.body) ? r.body : [];
      setBooths([...list].sort((x, y) => boothNo(x.booth_id) - boothNo(y.booth_id)));
    });
  }, [user]);

  const unwatch = async (id: string) => {
    const r = await authFetch(`/me/booths/${encodeURIComponent(id)}`, { method: "DELETE" });
    if (r.status < 200 || r.status >= 300) setErr("that booth could not be removed");
    else setBooths((b) => (b ?? []).filter((x) => x.booth_id !== id));
  };

  if (loading) return <PageLoader label="loading your account" />;
  if (!user)
    return (
      <div>
        <Eyebrow className="mb-5">Account.</Eyebrow>
        <Display size="hero" dim="Sign in to see your saved checks.">Your account.</Display>
        <p className="mt-10"><Link href="/login" className="btn">Sign in</Link></p>
      </div>
    );

  return (
    <div>
      <Eyebrow className="mb-5">Account.</Eyebrow>
      <Display size="page" dim={user.mobile_masked}>Your account.</Display>
      <div className="mt-8">
        <button className="btn btn--quiet" onClick={() => { signOut(); router.push("/"); }}>Sign out</button>
      </div>
      {err && <p className="text-[14px] text-ink-2 mt-4">Could not load everything: {err}. Try again in a moment.</p>}

      <section className="mt-20">
        <Display size="section" as="h2" dim={checks ? `${checks.length} saved.` : undefined}>Your saved checks.</Display>
        <div className="panel mt-6" style={{ padding: 12 }}>
          {checks === null ? <div className="p-4"><Loader label="loading your saved checks" /></div>
            : checks.length === 0 ? <p className="text-ink-2 p-4">No saved checks yet. Check a claim and press Save this check.</p>
            : (
              <ul className="grid gap-3">
                {checks.map((c) => (
                  <li key={c.claim_id} className="card p-5 grid gap-3 md:grid-cols-[180px_1fr_auto] md:items-center">
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
          {booths === null ? <Loader label="loading your watched booths" />
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
