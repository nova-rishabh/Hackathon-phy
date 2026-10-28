"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useSession } from "@/lib/auth";
import { WA_NUMBER, useSlowApi } from "@/lib/api";
import { I18nProvider, useI18n } from "@/lib/i18n";

function ShellInner({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [menu, setMenu] = useState(false);
  const { user } = useSession();
  const { t } = useI18n();

  const TABS: [string, string][] = [
    ["/", t("nav_audit")],
    ["/check", t("nav_check")],
    ["/ask", t("nav_ask")],
    ["/run", t("nav_run")],
  ];

  const acct: [string, string] = user ? ["/account", t("nav_account")] : ["/login", t("nav_signin")];
  const RIGHT: [string, string][] = [
    ["/pricing", t("nav_pricing")],
    ["/trust", t("nav_trust")],
    ["/settings", t("nav_keys")],
    acct,
  ];

  if (path.startsWith("/card")) return <>{children}</>;
  const active = (h: string) => (h === "/" ? path === "/" : path.startsWith(h));
  const tab = (h: string, l: string) => (
    <Link
      key={h}
      href={h}
      onClick={() => setMenu(false)}
      aria-current={active(h) ? "page" : undefined}
      className={`px-3 h-10 inline-flex items-center rounded-[8px] text-[15px] ${
        active(h) ? "text-ink bg-surface" : "text-ink-2 hover:text-ink"
      }`}
    >
      {l}
    </Link>
  );

  return (
    <div className="min-h-screen">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-3 focus:py-1.5 focus:bg-ink focus:text-surface focus:rounded-[8px] text-sm font-medium"
      >
        {t("skip_to_content")}
      </a>
      <div className="sticky top-0 z-20 px-4 pt-3 bg-page">
        <header className="mx-auto max-w-[1240px] bg-panel rounded-[12px] h-14 px-2 sm:px-3 flex items-center justify-between">
          <Link href="/" className="px-2 flex items-center" aria-label="RollWatch home">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo-word.png" alt="RollWatch" className="h-9 w-auto" />
          </Link>
          <nav aria-label="Main" className="hidden sm:flex items-center gap-1">
            {TABS.map(([h, l]) => tab(h, l))}
          </nav>
          <div className="hidden sm:flex items-center gap-2">
            <nav aria-label="Trust and account" className="flex items-center gap-1">
              {RIGHT.map(([h, l]) => tab(h, l))}
            </nav>
            <ThemeToggle />
          </div>
          <div className="sm:hidden flex items-center gap-2">
            <ThemeToggle />
            <button
              className="px-3 h-10 text-[15px] rounded-[8px] border border-line"
              aria-expanded={menu}
              aria-label="Toggle navigation menu"
              onClick={() => setMenu(!menu)}
            >
              {menu ? "Close" : "Menu"}
            </button>
          </div>
        </header>
        {menu && (
          <nav aria-label="Mobile menu" className="sm:hidden mt-2 bg-panel rounded-[12px] p-2 flex flex-col">
            {[...TABS, ...RIGHT].map(([h, l]) => tab(h, l))}
          </nav>
        )}
        <p role="note" className="mx-auto max-w-[1240px] mono text-[12px] leading-4 text-ink-3 py-3 px-2">
          {t("banner_note")}
        </p>
      </div>
      <main id="main-content" tabIndex={-1} className="mx-auto max-w-[1240px] px-4 pb-24 pt-6 sm:pt-12 focus:outline-none">
        {children}
      </main>
      <Waking />
      <Footer />
    </div>
  );
}

export default function Shell({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider>
      <ShellInner>{children}</ShellInner>
    </I18nProvider>
  );
}

/** Light or dark. Starts from the system setting; a click pins the choice (layout.tsx applies it before paint). */
function ThemeToggle() {
  const [dark, setDark] = useState<boolean | null>(null);
  useEffect(() => {
    const set = document.documentElement.dataset.theme;
    setDark(set ? set === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches);
  }, []);
  if (dark === null) return <span className="w-[52px]" aria-hidden="true" />;
  const flip = () => {
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("rw_theme", next); } catch { /* private mode: still switches for this visit */ }
    setDark(!dark);
  };
  return (
    <button onClick={flip} aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      className="px-3 h-10 inline-flex items-center rounded-[8px] mono text-[13px] text-ink-2 hover:text-ink">
      {dark ? "Light" : "Dark"}
    </button>
  );
}

const API_DOCS = (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000") + "/docs";
const WA = WA_NUMBER;
const COLS: [string, [string, string][]][] = [
  ["Product", [["/", "Audit"], ["/check", "Check a claim"], ["/ask", "Ask about a name"], ["/trust", "Trust and error rates"]]],
  ["Use it", [["/login", "Sign in"], ["/settings", "Bring your own keys"], ["https://t.me/Rollwatch_bot", "Telegram bot"], ...(WA ? [[`https://wa.me/${WA}`, "WhatsApp bot"] as [string, string]] : []), [API_DOCS, "Open API"]]],
  ["Project", [["https://github.com/nova-rishabh/Hackathon-phy", "Source code"], ["/trust", "What we miss"], ["https://voters.eci.gov.in", "Official voter portal"]]],
];

function Footer() {
  return (
    <footer className="px-4 pb-6">
      <div className="mx-auto max-w-[1240px] bg-panel rounded-[28px] p-8 sm:p-12">
        <div className="grid gap-10 lg:grid-cols-[1.3fr_1fr_1fr_1fr]">
          <div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo-word.png" alt="RollWatch" className="h-16 w-auto -ml-1" />
            <p className="text-[24px] leading-[30px] tracking-[-0.03em] mt-5 max-w-[22ch]">
              Auditable. Explainable. Accessible. <span className="text-ink-3">On no one&apos;s side.</span>
            </p>
          </div>
          {COLS.map(([title, links]) => (
            <nav key={title} aria-label={title}>
              <p className="eyebrow mb-4">{title}.</p>
              <ul className="space-y-2.5">
                {links.map(([h, l]) => (
                  <li key={l}>
                    <a href={h} {...(h.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {})}
                      className="text-[15px] text-ink-2 hover:text-ink">{l}</a>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>
        <div className="border-t border-line mt-10 pt-6 flex flex-col gap-2 sm:flex-row sm:justify-between">
          <p className="mono text-[12px] text-ink-3">synthetic data · Sampleabad is a fictional district · flags are patterns for human review, not findings</p>
          <p className="mono text-[12px] text-ink-3">not an official service · check your name at voters.eci.gov.in or call 1950</p>
        </div>
      </div>
    </footer>
  );
}

/** Shown while an API request is slow: the free server sleeps when idle and needs ~30 s to wake. */
function Waking() {
  const slow = useSlowApi();
  return (
    <div aria-live="polite" className={`waking ${slow ? "in" : ""}`} role="status">
      {slow && <>
        <span className="waking-bar" aria-hidden="true"><i /></span>
        <span className="mono text-[12px] text-ink-2">waking the server · free hosting · about 30 seconds</span>
      </>}
    </div>
  );
}
