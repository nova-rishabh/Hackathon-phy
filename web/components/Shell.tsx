"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { supabase, useSession } from "@/lib/supabase";

const TABS = [["/", "Audit"], ["/check", "Check"], ["/ask", "Ask"]] as const;

export default function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [menu, setMenu] = useState(false);
  const { session } = useSession();
  const acct: readonly [string, string] = supabase && session ? ["/account", "Account"] : ["/login", "Sign in"];
  const RIGHT = [["/trust", "Trust"], ["/settings", "Keys"], acct] as const;
  if (path.startsWith("/card")) return <>{children}</>;
  const active = (h: string) => (h === "/" ? path === "/" : path.startsWith(h));
  const tab = (h: string, l: string) => (
    <Link key={h} href={h} onClick={() => setMenu(false)} aria-current={active(h) ? "page" : undefined}
      className={`px-3 h-10 inline-flex items-center rounded-[8px] text-[15px] ${active(h) ? "text-ink bg-surface" : "text-ink-2 hover:text-ink"}`}>{l}</Link>
  );
  return (
    <div className="min-h-screen">
      <div className="sticky top-0 z-20 px-4 pt-3 bg-page">
        <header className="mx-auto max-w-[1240px] bg-panel rounded-[12px] h-14 px-2 sm:px-3 flex items-center justify-between">
          <Link href="/" className="px-2 flex items-center" aria-label="RollWatch home">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo-word.png" alt="RollWatch" className="h-12 w-auto -my-1" />
          </Link>
          <nav aria-label="Main" className="hidden sm:flex items-center gap-1">
            {TABS.map(([h, l]) => tab(h, l))}
          </nav>
          <nav aria-label="Trust and account" className="hidden sm:flex items-center gap-1">{RIGHT.map(([h, l]) => tab(h, l))}</nav>
          <button className="sm:hidden px-3 h-10 text-[15px]" aria-expanded={menu} onClick={() => setMenu(!menu)}>{menu ? "Close" : "Menu"}</button>
        </header>
        {menu && (
          <nav aria-label="Main" className="sm:hidden mt-2 bg-panel rounded-[12px] p-2 flex flex-col">
            {[...TABS, ...RIGHT].map(([h, l]) => tab(h, l))}
          </nav>
        )}
        <p role="note" className="mx-auto max-w-[1240px] mono text-[12px] leading-4 text-ink-3 py-3 px-2">
          synthetic data · sampleabad is fictional · flags are patterns for human review, not findings
        </p>
      </div>
      <main className="mx-auto max-w-[1240px] px-4 pb-32 pt-6 sm:pt-12">{children}</main>
    </div>
  );
}
