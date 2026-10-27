"use client";
// Share card, 1080×1350. Headless Chrome screenshots this page into /cards/{claim_id}.png (TRD M9).
// Data: the verdict the Check page stored in sessionStorage, else the API, else the demo mock.
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import qrcode from "qrcode-generator";
import { getJson } from "@/lib/api";
import { CLAIM_MOCK } from "@/lib/mocks";
import type { ClaimVerdict } from "@/lib/types";
import Chip from "@/components/Chip";

function QR({ text, size = 168 }: { text: string; size?: number }) {
  const cells = useMemo(() => {
    const q = qrcode(0, "M");
    q.addData(text);
    q.make();
    const n = q.getModuleCount();
    const out: [number, number][] = [];
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (q.isDark(r, c)) out.push([c, r]);
    return { n, out };
  }, [text]);
  return (
    <svg width={size} height={size} viewBox={`-2 -2 ${cells.n + 4} ${cells.n + 4}`} role="img" aria-label="QR code to check a claim" shapeRendering="crispEdges">
      <rect x={-2} y={-2} width={cells.n + 4} height={cells.n + 4} fill="#FFFFFF" />
      {cells.out.map(([x, y]) => <rect key={`${x}-${y}`} x={x} y={y} width={1} height={1} fill="var(--color-ink)" />)}
    </svg>
  );
}

export default function Card() {
  const { id } = useParams<{ id: string }>();
  const claimId = decodeURIComponent(id ?? "");
  const [v, setV] = useState<ClaimVerdict | null>(null);
  const [done, setDone] = useState(false);
  const [origin, setOrigin] = useState("");
  // Fit the fixed 1080px card to a phone; the headless 1080px screenshot still gets scale 1.
  const [scale, setScale] = useState(1);
  useEffect(() => {
    const fit = () => setScale(Math.min(1, document.documentElement.clientWidth / 1080));
    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  useEffect(() => {
    setOrigin(window.location.origin);
    let stored: ClaimVerdict | null = null;
    try { const s = sessionStorage.getItem(`claim:${claimId}`); if (s) stored = JSON.parse(s); } catch {}
    if (stored) { setV(stored); setDone(true); return; }
    getJson<ClaimVerdict>(`/claims/${encodeURIComponent(claimId)}`).then((r) => {
      setV(r.data ?? (claimId === CLAIM_MOCK.claim_id ? CLAIM_MOCK : null));
      setDone(true);
    });
  }, [claimId]);

  const claim = v?.input.text ?? "";
  const big = claim.length > 90 ? 44 : 56;
  return (
    <div style={{ width: 1080 * scale, height: 1350 * scale, overflow: "hidden" }}>
    <div style={{ width: 1080, height: 1350, background: "var(--color-page)", padding: 48, boxSizing: "border-box", transform: `scale(${scale})`, transformOrigin: "top left" }} data-ready={done ? "1" : "0"}>
      <div className="panel" style={{ height: "100%", padding: 56, borderRadius: 28, display: "flex", flexDirection: "column" }}>
        <div className="flex justify-between items-baseline">
          <span className="text-[30px] tracking-[-0.04em]">rollwatch</span>
          <span className="eyebrow" style={{ fontSize: 18 }}>Claim court.</span>
        </div>

        {!v ? (
          <p className="display mt-24" style={{ fontSize: 56, lineHeight: 1.05 }}>
            {done ? <>This card has expired. <span className="dim">Paste the claim again to check it.</span></> : "Loading the verdict."}
          </p>
        ) : (
          <>
            <p className="display mt-16" style={{ fontSize: big, lineHeight: 1.08, letterSpacing: "-0.035em", textWrap: "balance" } as React.CSSProperties}>
              “{claim}” <span className="dim">Here is what the roll shows.</span>
            </p>
            <ul className="mt-14 grid gap-4">
              {v.sub_claims.slice(0, 3).map((s) => (
                <li key={s.id} className="card" style={{ padding: 28, borderRadius: 20 }}>
                  <div className="flex items-start gap-6">
                    <span className="shrink-0"><Chip kind={s.verdict} big /></span>
                    <span className="min-w-0">
                      <span className="block text-[28px] leading-[34px] tracking-[-0.02em]">{s.text}</span>
                      <span className="block mono text-[18px] leading-6 text-ink-2 mt-3">{s.query_shown}</span>
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}

        <div className="mt-auto flex items-end justify-between gap-8 pt-10">
          <div className="min-w-0">
            {v && <p className="mono text-[20px] leading-8">how sure {Math.round(v.confidence * 100)}% · patterns for human review, not findings</p>}
            {v?.mirror && <p className="mono text-[18px] leading-7 text-ink-2 mt-2">mirror claim checked · {v.mirror.identical_treatment ? "identical treatment · same tools · same tolerance" : "treatment differed · needs human review"}</p>}
            <p className="mono text-[16px] leading-6 text-ink-3 mt-4">synthetic data · sampleabad is fictional · check any claim at the link</p>
          </div>
          {origin && <QR text={`${origin}/check`} />}
        </div>
      </div>
    </div>
    </div>
  );
}
