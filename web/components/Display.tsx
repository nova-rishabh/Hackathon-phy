import type { ReactNode } from "react";
import { boothNo } from "@/lib/api";

/** Two-tone headline: children in ink, `dim` in grey. Put a live object inline via <Obj>. */
export function Display({ children, dim, size = "page", as: Tag = "h1" }: { children: ReactNode; dim?: ReactNode; size?: "hero" | "page" | "section"; as?: "h1" | "h2" | "p" }) {
  return (
    <Tag className={`display ${size === "hero" ? "h-hero" : size === "page" ? "h-page" : "h-section"}`} style={{ textWrap: "balance" } as React.CSSProperties}>
      {children}{dim && <> <span className="dim">{dim}</span></>}
    </Tag>
  );
}

export function Obj({ children }: { children: ReactNode }) {
  return <span className="inline-obj" aria-hidden="true">{children}</span>;
}

const FILL: Record<string, string> = { unusual: "tile--unusual", likely_benign: "tile--benign", mixed: "hatch", normal: "" };
export function BoothTile({ booth, outcome = "unusual" }: { booth: string; outcome?: string }) {
  return <span className={`tile tile-inline ${FILL[outcome] ?? ""}`} style={{ border: outcome === "normal" ? "1px solid var(--color-line)" : 0 }}>{boothNo(booth)}</span>;
}

export function Eyebrow({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <p className={`eyebrow ${className}`}>{children}</p>;
}
