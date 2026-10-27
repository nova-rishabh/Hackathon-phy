"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Glyph from "./Glyph";

const NAV = [
  ["/", "Overview"], ["/flags", "Flags"], ["/stories", "Which story fits?"], ["/claims", "Claim Court"],
  ["/citizen", "Citizen"], ["/trust", "Trust"], ["/report", "Report"],
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const active = (h: string) => (h === "/" ? path === "/" : path.startsWith(h));
  return (
    <div className="min-h-screen flex flex-col">
      <header className="h-14 shrink-0 flex items-center justify-between px-4 bg-surface border-b border-rule">
        <Link href="/" className="flex items-center gap-2 text-ink no-underline">
          <Glyph id="rw-mark" size={28} />
          <span className="text-[20px] font-bold tracking-[-0.01em]">RollWatch</span>
        </Link>
        <span className="font-mono text-[12px] text-ink-2 hidden sm:block">Sampleabad · roll v1 → v2</span>
      </header>
      <div className="h-8 shrink-0 flex items-center px-4 bg-voter-ink-soft font-mono text-[12px] leading-4 text-ink overflow-hidden whitespace-nowrap" role="note">
        SYNTHETIC DATA · SAMPLEABAD IS FICTIONAL · FLAGS ARE PATTERNS FOR HUMAN REVIEW, NOT FINDINGS
      </div>
      <div className="flex flex-1 flex-col md:flex-row">
        <nav aria-label="Main" className="md:w-[200px] shrink-0 md:border-r border-b md:border-b-0 border-rule bg-paper p-2 md:p-4 flex md:flex-col gap-1 overflow-x-auto">
          {NAV.map(([h, l]) => (
            <Link key={h} href={h}
              className={`px-3 py-2 text-[14px] whitespace-nowrap rounded-[4px] border-l-[3px] ${active(h) ? "border-voter-ink bg-voter-ink-soft text-voter-ink font-bold" : "border-transparent text-ink-2 font-medium hover:bg-sunk"}`}>
              {l}
            </Link>
          ))}
        </nav>
        <main className="flex-1 min-w-0 p-4 md:p-6"><div className="max-w-[1200px]">{children}</div></main>
      </div>
    </div>
  );
}
