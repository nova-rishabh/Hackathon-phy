"use client";
import { useRef, useState } from "react";
import Link from "next/link";
import { postJson } from "@/lib/api";
import { CLAIM_MOCK, DEMO_CLAIM, MIRROR_ROWS } from "@/lib/mocks";
import type { ClaimVerdict } from "@/lib/types";
import Chip from "@/components/Chip";
import Glyph from "@/components/Glyph";
import { SaveCheck } from "@/components/AccountActions";
import { Display, Eyebrow } from "@/components/Display";

const toB64 = (f: File) => new Promise<string>((ok, no) => {
  const r = new FileReader();
  r.onload = () => ok(String(r.result).split(",")[1] ?? "");
  r.onerror = no;
  r.readAsDataURL(f);
});

export default function Check() {
  const [text, setText] = useState("");
  const [img, setImg] = useState<{ name: string; b64: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<ClaimVerdict | null>(null);
  const [mocked, setMocked] = useState(false);
  const [err, setErr] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const takeFile = async (f?: File | null) => {
    if (f && f.type.startsWith("image/")) setImg({ name: f.name, b64: await toB64(f) });
  };

  const run = async (claim = text) => {
    if (!claim.trim() && !img) return;
    setBusy(true); setErr("");
    try {
      const v = await postJson<ClaimVerdict>("/claims/check", img ? { image_b64: img.b64, mirror: true } : { text: claim, mirror: true }, 30000);
      setRes(v); setMocked(false);
      try { sessionStorage.setItem(`claim:${v.claim_id}`, JSON.stringify(v)); } catch {}
    } catch {
      const isDemo = /booth\s*47/i.test(claim) && /600/.test(claim);
      if (isDemo) { setRes(CLAIM_MOCK); setMocked(true); }
      else { setRes(null); setErr("The claim checker is not reachable right now. The scripted demo claim still works offline."); }
    }
    setBusy(false);
  };

  const subs = res?.sub_claims ?? [];
  const mirror = res?.mirror;
  return (
    <div>
      <Eyebrow className="mb-5">Claim court.</Eyebrow>
      <Display size="hero" dim="We split it, run the numbers, and show the query.">Paste a forwarded claim.</Display>

      <section className="panel mt-16"
        onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); takeFile(e.dataTransfer.files?.[0]); }}>
        <label htmlFor="claim" className="eyebrow block mb-4">The claim.</label>
        <textarea id="claim" className="input text-[20px] sm:text-[24px] leading-snug tracking-[-0.02em] min-h-[160px] resize-y"
          value={text} onChange={(e) => setText(e.target.value)} placeholder="Booth 47 mein 600 naam kaat diye…"
          onPaste={(e) => takeFile(e.clipboardData.files?.[0])} />
        <div className="flex flex-wrap items-center justify-between gap-4 mt-4">
          <div className="flex flex-wrap items-center gap-3">
            <button className="mono text-[13px] text-ink-3 hover:text-ink" onClick={() => (img ? setImg(null) : fileRef.current?.click())}>
              {img ? `image: ${img.name} · remove` : "or drop a screenshot"}
            </button>
            <input ref={fileRef} type="file" accept="image/*" hidden onChange={(e) => takeFile(e.target.files?.[0])} />
            <button className="mono text-[13px] text-ink-3 hover:text-ink underline underline-offset-2" onClick={() => { setText(DEMO_CLAIM); setImg(null); run(DEMO_CLAIM); }}>
              try the demo claim
            </button>
          </div>
          <button className="btn" disabled={busy || (!text.trim() && !img)} onClick={() => run()}>{busy ? "Checking…" : "Check this claim"}</button>
        </div>
        {err && <p className="text-[14px] text-ink-2 mt-4">{err}</p>}
      </section>

      {res && (
        <section className="mt-24" aria-live="polite">
          <Eyebrow className="mb-5">The verdict.{mocked && " Mock data, api not reachable."}</Eyebrow>
          <Display size="page" as="h2" dim={res.normalized_claim !== res.input.text ? res.normalized_claim : undefined}>
            “{res.input.text}”
          </Display>
          <ul className="panel mt-10 grid gap-3 stagger" style={{ padding: 12 }}>
            {subs.map((s) => (
              <li key={s.id} className="card p-5 grid gap-3 md:grid-cols-[180px_1fr_minmax(0,320px)] md:items-start">
                <span><Chip kind={s.verdict} /></span>
                <span>
                  <span className="block text-[18px] leading-6 tracking-[-0.01em]">{s.text}</span>
                  <span className="block text-[14px] text-ink-2 mt-1">{s.reason}</span>
                </span>
                <code className="mono text-[12px] leading-5 bg-page rounded-[8px] px-3 py-2 text-ink-2 break-words">{s.query_shown}</code>
              </li>
            ))}
          </ul>
          <p className="mono text-[13px] text-ink-2 mt-4">
            how sure {Math.round(res.confidence * 100)}% · patterns for human review, not findings ·{" "}
            <Link className="underline underline-offset-2 hover:text-ink" href={`/card/${encodeURIComponent(res.claim_id)}`}>open share card</Link>
            {!mocked && <> · <a className="underline underline-offset-2 hover:text-ink" href={`/card/${encodeURIComponent(res.claim_id)}/png`} download={`rollwatch-${res.claim_id}.png`}>save as image</a></>}
          </p>
          {!mocked && <div className="mt-4"><SaveCheck claimId={res.claim_id} claimText={res.input.text || String(res.normalized_claim ?? "")} overall={res.overall} /></div>}

          {mirror && (
            <section className="mt-24">
              <Eyebrow className="mb-5 inline-flex items-center gap-2"><Glyph id="rw-mirror" size={16} />Mirror.</Eyebrow>
              <Display size="section" as="h2" dim="The opposite claim gets the same tools and the same tolerance.">We checked the other side too.</Display>
              <div className="panel mt-8" style={{ padding: 12 }}>
                <div className="grid gap-3 md:grid-cols-2">
                  <MirrorCard title={res.input.text} verdicts={subs.map((s) => s.verdict)} rows={subs.map((s) => s.text)} />
                  <MirrorCard title={mirror.claim_text} verdicts={mirror.sub_claim_verdicts}
                    rows={mirrorRows(mirror.claim_text, mirror.sub_claim_verdicts.length, mocked)} />
                </div>
                <p className="mono text-[12px] text-ink-3 text-center pt-4 pb-2">
                  {mirror.identical_treatment ? "identical treatment · same tools · same tolerance" : "treatment differed · needs human review"}
                </p>
              </div>
            </section>
          )}
        </section>
      )}
    </div>
  );
}

// The API joins one restatement per sub-claim with "; " (api/claims.py mirror_of), so split it back.
function mirrorRows(text: string, n: number, mocked: boolean): string[] {
  const parts = text.split("; ").map((t) => t.charAt(0).toUpperCase() + t.slice(1));
  return Array.from({ length: n }, (_, i) => (mocked ? MIRROR_ROWS[i]?.text : null) ?? (parts.length === n ? parts[i] : `Part ${i + 1} of the opposite claim`));
}

function MirrorCard({ title, verdicts, rows }: { title: string; verdicts: string[]; rows: string[] }) {
  return (
    <div className="card p-5 sm:p-6">
      <p className="text-[20px] leading-7 tracking-[-0.02em] mb-5">“{title}”</p>
      <ul className="grid gap-2">
        {verdicts.map((v, i) => (
          <li key={i} className="flex items-start gap-3"><Chip kind={v} /><span className="text-[14px] text-ink-2 pt-[3px]">{rows[i]}</span></li>
        ))}
      </ul>
    </div>
  );
}
