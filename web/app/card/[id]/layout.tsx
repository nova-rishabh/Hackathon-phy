// A shared claim link previews as that claim's own verdict card (the PNG drawn by ./png/route.tsx).
import type { Metadata } from "next";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  let claim = "";
  try {
    const r = await fetch(`${API}/claims/${encodeURIComponent(id)}`, { next: { revalidate: 3600 } });
    if (r.ok) claim = ((await r.json()) as { input?: { text?: string } }).input?.text ?? "";
  } catch { /* preview falls back to the generic text */ }
  const title = claim ? `“${claim.length > 90 ? claim.slice(0, 87) + "…" : claim}”: checked` : "A claim, checked";
  const description = "Each part checked against the roll: verified, disputed or cannot be proven, with the query shown. Patterns for human review, not findings.";
  const image = { url: `/card/${encodeURIComponent(id)}/png`, width: 1080, height: 1350, alt: "RollWatch verdict card" };
  return {
    title, description,
    openGraph: { type: "article", title, description, images: [image] },
    twitter: { card: "summary_large_image", title, description, images: [image.url] },
  };
}

export default function CardLayout({ children }: { children: React.ReactNode }) {
  return children;
}
