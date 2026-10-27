// Share card as a 1080×1350 PNG (TRD M9), drawn with next/og so no headless browser is needed.
// The API's /cards/{id}.png fetches and caches this, so the Telegram and WhatsApp bots can send it as an image.
import { ImageResponse } from "next/og";
import { CLAIM_MOCK } from "@/lib/mocks";
import type { ClaimVerdict } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const C = { page: "#F9F9F9", panel: "#EDEDED", surface: "#FFFFFF", ink: "#0F0F0F", ink2: "#5C5C5C", ink3: "#9A9A9A" };
const CHIP: Record<string, { bg: string; fg: string; label: string; dashed?: boolean }> = {
  verified: { bg: "#1CC691", fg: C.ink, label: "Verified" },
  disputed: { bg: "#D61F69", fg: "#FFFFFF", label: "Disputed" },
  unprovable: { bg: C.panel, fg: C.ink2, label: "Cannot be proven", dashed: true },
};

/** Google Fonts serves TTF to a non-browser user agent; subset to the glyphs we draw. */
async function font(family: string, text: string): Promise<ArrayBuffer | null> {
  try {
    const css = await (await fetch(`https://fonts.googleapis.com/css2?family=${family}&text=${encodeURIComponent(text)}`)).text();
    const url = css.match(/src: url\((.+?)\) format\('(opentype|truetype)'\)/)?.[1];
    return url ? await (await fetch(url)).arrayBuffer() : null;
  } catch {
    return null;
  }
}

export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let v: ClaimVerdict | null = null;
  try {
    const r = await fetch(`${API}/claims/${encodeURIComponent(id)}`, { cache: "no-store" });
    if (r.ok) v = await r.json();
  } catch {}
  if (!v && id === CLAIM_MOCK.claim_id) v = CLAIM_MOCK;
  if (!v) return new Response("unknown claim", { status: 404 });

  const claim = v.input.text ?? "";
  const subs = v.sub_claims.slice(0, 3);
  const foot = `how sure ${Math.round(v.confidence * 100)}% · patterns for human review, not findings`;
  const mirror = v.mirror ? (v.mirror.identical_treatment ? "mirror claim checked · identical treatment · same tools · same tolerance" : "mirror claim checked · treatment differed · needs human review") : "";
  const site = "synthetic data · sampleabad is fictional · rollwatch-web.onrender.com/check";
  const all = ["rollwatch Claim court. Here is what the roll shows.", claim, ...subs.map((s) => s.text + s.query_shown), foot, mirror, site,
    ...Object.values(CHIP).map((c) => c.label), "“”"].join(" ");
  const [sans, mono, deva] = await Promise.all([font("Geist", all), font("Geist+Mono", all), font("Noto+Sans+Devanagari", all)]);
  const fonts = [
    sans && { name: "Geist", data: sans, weight: 400 as const },
    mono && { name: "Geist Mono", data: mono, weight: 400 as const },
    deva && { name: "Noto Sans Devanagari", data: deva, weight: 400 as const },
  ].filter(Boolean) as { name: string; data: ArrayBuffer; weight: 400 }[];
  const big = claim.length > 90 ? 44 : 56;

  return new ImageResponse(
    (
      <div style={{ width: 1080, height: 1350, background: C.page, padding: 48, display: "flex", fontFamily: "Geist, Noto Sans Devanagari" }}>
        <div style={{ flex: 1, background: C.panel, borderRadius: 28, padding: 56, display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
            <span style={{ fontSize: 30, letterSpacing: "-0.04em", color: C.ink }}>rollwatch</span>
            <span style={{ fontSize: 18, fontFamily: "Geist Mono", color: C.ink3 }}>Claim court.</span>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", marginTop: 64, fontSize: big, lineHeight: 1.08, letterSpacing: "-0.035em", color: C.ink }}>
            <span>“{claim}”&nbsp;</span><span style={{ color: C.ink3 }}>Here is what the roll shows.</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", marginTop: 56 }}>
            {subs.map((s) => {
              const c = CHIP[s.verdict] ?? CHIP.unprovable;
              return (
                <div key={s.id} style={{ display: "flex", background: C.surface, borderRadius: 20, padding: 28, marginBottom: 16, alignItems: "flex-start" }}>
                  <div style={{ display: "flex", width: 196, flexShrink: 0, marginRight: 20 }}>
                    <div style={{ display: "flex", height: 40, padding: "0 16px", alignItems: "center", borderRadius: 8, fontSize: 18,
                      background: c.bg, color: c.fg, border: c.dashed ? `1.5px dashed ${C.ink3}` : "none" }}>{c.label}</div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", flex: 1 }}>
                    <span style={{ fontSize: 28, lineHeight: "34px", letterSpacing: "-0.02em", color: C.ink }}>{s.text}</span>
                    <span style={{ fontSize: 18, lineHeight: "24px", fontFamily: "Geist Mono", color: C.ink2, marginTop: 12 }}>{s.query_shown}</span>
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{ display: "flex", flexDirection: "column", marginTop: "auto", fontFamily: "Geist Mono" }}>
            <span style={{ fontSize: 20, lineHeight: "32px", color: C.ink }}>{foot}</span>
            {mirror && <span style={{ fontSize: 18, lineHeight: "28px", color: C.ink2, marginTop: 8 }}>{mirror}</span>}
            <span style={{ fontSize: 16, lineHeight: "24px", color: C.ink3, marginTop: 16 }}>{site}</span>
          </div>
        </div>
      </div>
    ),
    { width: 1080, height: 1350, fonts, headers: { "Cache-Control": "public, max-age=86400" } },
  );
}
