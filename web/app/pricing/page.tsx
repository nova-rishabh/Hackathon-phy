"use client";
// Pricing and a custom subscription builder. Every price is quoted by the API (/billing/quote); payment is a
// Razorpay subscription created server-side for exactly that plan, and its signature is verified server-side.
import { useEffect, useRef, useState } from "react";
import { getJson, postJson, fmt } from "@/lib/api";
import { Display, Eyebrow } from "@/components/Display";
import Loader from "@/components/Loader";

type Plan = { constituencies: number; whatsapp: boolean; languages: number; reviewers: number; voice_replies: number;
  onprem: boolean; nonprofit: boolean; annual: boolean };
type Preset = Omit<Plan, "annual"> & { label: string };
type Config = { enabled: boolean; key_id: string | null; test_mode: boolean; presets: Record<string, Preset>; free: string[];
  limits: Record<string, [number, number]>; prices: Record<string, { label: string; inr: number; unit?: string }>;
  discounts: { annual_months_free: number; nonprofit_off: number } };
type Quote = { lines: { key: string; label: string; qty: number; inr: number }[]; list_monthly_inr: number; nonprofit_discount: number;
  monthly_inr: number; period: "monthly" | "yearly"; charge_inr: number; effective_monthly_inr: number; annual_months_free: number };
type RzpResponse = { razorpay_payment_id: string; razorpay_subscription_id: string; razorpay_signature: string };
declare global { interface Window { Razorpay?: new (o: Record<string, unknown>) => { open: () => void } } }

const START: Plan = { constituencies: 5, whatsapp: true, languages: 0, reviewers: 3, voice_replies: 2000, onprem: false, nonprofit: true, annual: false };
const inr = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;

function loadCheckout(): Promise<void> {
  if (window.Razorpay) return Promise.resolve();
  return new Promise((ok, no) => {
    const s = document.createElement("script");
    s.src = "https://checkout.razorpay.com/v1/checkout.js";
    s.onload = () => ok();
    s.onerror = () => no(new Error("checkout script"));
    document.body.appendChild(s);
  });
}

export default function Pricing() {
  const [cfg, setCfg] = useState<Config | null>(null);
  const [plan, setPlan] = useState<Plan>(START);
  const [preset, setPreset] = useState<string>("newsroom");
  const [q, setQ] = useState<Quote | null>(null);
  const [org, setOrg] = useState("");
  const [pay, setPay] = useState<{ state: "idle" | "busy" | "done" | "error"; msg?: string }>({ state: "idle" });
  const seq = useRef(0);

  useEffect(() => { getJson<Config>("/billing/config").then((r) => setCfg(r.data)); }, []);
  useEffect(() => { // quote from the API; only the latest request's answer is shown
    const id = ++seq.current;
    const t = setTimeout(async () => {
      try { const r = await postJson<Quote>("/billing/quote", plan, 15000); if (id === seq.current) setQ(r); } catch { /* keep last quote */ }
    }, 120);
    return () => clearTimeout(t);
  }, [plan]);

  const set = <K extends keyof Plan>(k: K, v: Plan[K]) => { setPlan((p) => ({ ...p, [k]: v })); setPreset(""); };
  const usePreset = (k: string) => {
    const p = cfg?.presets[k];
    if (!p) return;
    const { label: _label, ...rest } = p;
    setPlan((cur) => ({ ...rest, annual: cur.annual }));
    setPreset(k);
  };
  const lim = (k: string): [number, number] => cfg?.limits[k] ?? [0, 1000];

  const subscribe = async () => {
    setPay({ state: "busy" });
    try {
      const s = await postJson<{ subscription_id: string; key_id: string; charge_inr: number; period: string }>("/billing/subscribe", { plan, org }, 30000);
      await loadCheckout();
      if (!window.Razorpay) throw new Error("checkout");
      new window.Razorpay({
        key: s.key_id, subscription_id: s.subscription_id, name: "RollWatch",
        description: `Custom plan · ${inr(s.charge_inr)} ${s.period === "yearly" ? "a year" : "a month"}`,
        theme: { color: "#1E1E1E" },
        modal: { ondismiss: () => setPay({ state: "idle" }) },
        handler: async (r: RzpResponse) => {
          try { await postJson("/billing/verify", r, 15000); setPay({ state: "done", msg: r.razorpay_subscription_id }); }
          catch { setPay({ state: "error", msg: "Payment received, but we could not verify it. Contact us with your payment ID." }); }
        },
      }).open();
    } catch (e) {
      const m = String(e instanceof Error ? e.message : e);
      setPay({ state: "error", msg: m.includes("503") ? "Payments are being set up. Your quote is saved on this page; try again shortly." : "Could not start the payment. Try again in a minute." });
    }
  };

  return (
    <div>
      <Eyebrow className="mb-5">Pricing.</Eyebrow>
      <Display size="hero" dim="Organisations build the plan they need.">Free for every voter.</Display>

      <section className="panel mt-16">
        <Eyebrow className="mb-5">Always free, for citizens.</Eyebrow>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 stagger">
          {(cfg?.free ?? []).map((f) => (
            <div key={f} className="card p-5"><p className="mono text-[28px] leading-8 tracking-[-0.03em]">₹0</p><p className="text-[15px] text-ink-2 mt-2">{f}</p></div>
          ))}
        </div>
      </section>

      <section className="mt-16">
        <Eyebrow className="mb-5">Build your plan.</Eyebrow>
        <div className="flex flex-wrap gap-x-8 gap-y-2 mb-8">
          {Object.entries(cfg?.presets ?? {}).map(([k, p]) => (
            <button key={k} className="opt" aria-pressed={preset === k} onClick={() => usePreset(k)}>{p.label}</button>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-[1fr_400px] items-start">
          <div className="panel grid gap-3 min-w-0">
            <Row label="Constituencies audited" hint={`${inr(cfg?.prices.constituency?.inr ?? 0)} each · audited on every roll revision`}>
              <Num v={plan.constituencies} min={lim("constituencies")[0]} max={lim("constituencies")[1]} onChange={(v) => set("constituencies", v)} slider />
            </Row>
            <Row label="WhatsApp bot on your own number" hint={inr(cfg?.prices.whatsapp?.inr ?? 0)}>
              <Seg on={plan.whatsapp} onChange={(v) => set("whatsapp", v)} />
            </Row>
            <Row label="Extra languages" hint={`beyond Hindi, English, Punjabi · ${inr(cfg?.prices.language?.inr ?? 0)} each`}>
              <Num v={plan.languages} min={lim("languages")[0]} max={lim("languages")[1]} onChange={(v) => set("languages", v)} />
            </Row>
            <Row label="Human-review seats" hint={`${inr(cfg?.prices.reviewer?.inr ?? 0)} each · hash-chained review log`}>
              <Num v={plan.reviewers} min={lim("reviewers")[0]} max={lim("reviewers")[1]} onChange={(v) => set("reviewers", v)} />
            </Row>
            <Row label="Voice replies a month" hint={`₹${cfg?.prices.voice?.inr ?? 0} each · natural Hindi voice`}>
              <Num v={plan.voice_replies} min={0} max={lim("voice_replies")[1]} step={500} onChange={(v) => set("voice_replies", v)} slider sliderMax={100000} />
            </Row>
            <Row label="Run on your own servers" hint={`${inr(cfg?.prices.onprem?.inr ?? 0)} · private deployment and support`}>
              <Seg on={plan.onprem} onChange={(v) => set("onprem", v)} />
            </Row>
            <Row label="Newsroom, NGO or research group" hint={`${Math.round((cfg?.discounts.nonprofit_off ?? 0) * 100)}% off`}>
              <Seg on={plan.nonprofit} onChange={(v) => set("nonprofit", v)} />
            </Row>
          </div>

          <aside className="card p-6 lg:sticky lg:top-24 min-w-0">
            <div className="flex items-center justify-between">
              <Eyebrow>Your plan.</Eyebrow>
              <span className="seg" role="group" aria-label="Billing">
                <button aria-pressed={!plan.annual} onClick={() => set("annual", false)}>monthly</button>
                <button aria-pressed={plan.annual} onClick={() => set("annual", true)}>yearly</button>
              </span>
            </div>
            {q ? (
              <>
                <p className="mono text-[48px] leading-[56px] tracking-[-0.04em] mt-5">{inr(q.effective_monthly_inr)}<span className="text-[18px] text-ink-3">/month</span></p>
                <p className="text-[14px] text-ink-2 mt-1">
                  {q.period === "yearly" ? `${inr(q.charge_inr)} billed yearly · ${q.annual_months_free} months free` : `${inr(q.charge_inr)} billed monthly`}
                  {q.nonprofit_discount > 0 && ` · ${Math.round(q.nonprofit_discount * 100)}% nonprofit discount`}
                </p>
                <ul className="mt-5 border-t border-line">
                  {q.lines.map((l) => (
                    <li key={l.key} className="flex justify-between gap-4 py-2 border-b border-line text-[14px]">
                      <span className="text-ink-2">{l.label}{l.qty > 1 && <span className="mono text-ink-3"> × {fmt(l.qty)}</span>}</span>
                      <span className="mono">{inr(l.inr)}</span>
                    </li>
                  ))}
                  <li className="flex justify-between py-2 text-[14px]"><span className="text-ink-2">List price a month</span><span className="mono">{inr(q.list_monthly_inr)}</span></li>
                </ul>
                <input className="input mt-4" style={{ padding: "12px 14px" }} placeholder="Organisation name (optional)" value={org} maxLength={80} onChange={(e) => setOrg(e.target.value)} />
                <button className="btn w-full justify-center mt-3" disabled={pay.state === "busy" || !cfg?.enabled} onClick={subscribe}>
                  {pay.state === "busy" ? "Opening checkout…" : `Subscribe · ${inr(q.charge_inr)}`}
                </button>
                <p className="mono text-[11px] text-ink-3 mt-3">
                  {!cfg?.enabled ? "payments are being set up · the quote above is live" : cfg.test_mode ? "razorpay test mode · no real money moves" : "secure checkout by razorpay · cancel any time"}
                </p>
                {pay.state === "done" && <p className="text-[14px] mt-3">Subscribed. Reference <span className="mono">{pay.msg}</span>. We will be in touch to set up your constituencies.</p>}
                {pay.state === "error" && <p className="text-[14px] text-ink-2 mt-3">{pay.msg}</p>}
              </>
            ) : <Loader className="mt-5" label="working out your price…" />}
          </aside>
        </div>
      </section>
    </div>
  );
}

function Row({ label, hint, children }: { label: string; hint: string; children: React.ReactNode }) {
  return (
    <div className="card px-5 py-4 flex flex-wrap items-center justify-between gap-4">
      <div className="min-w-0"><p className="text-[16px]">{label}</p><p className="mono text-[12px] text-ink-3 mt-1">{hint}</p></div>
      {children}
    </div>
  );
}

function Seg({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <span className="seg" role="group">
      <button aria-pressed={!on} onClick={() => onChange(false)}>off</button>
      <button aria-pressed={on} onClick={() => onChange(true)}>on</button>
    </span>
  );
}

function Num({ v, min, max, step = 1, onChange, slider, sliderMax }: { v: number; min: number; max: number; step?: number;
  onChange: (v: number) => void; slider?: boolean; sliderMax?: number }) {
  const clamp = (x: number) => Math.max(min, Math.min(max, Math.round(x)));
  return (
    <div className="flex items-center gap-3">
      {slider && <input type="range" min={min} max={sliderMax ?? max} step={step} value={Math.min(v, sliderMax ?? max)}
        onChange={(e) => onChange(clamp(Number(e.target.value)))} className="w-[160px] accent-[var(--color-button)] hidden sm:block" aria-label="amount" />}
      <span className="seg">
        <button onClick={() => onChange(clamp(v - step))} aria-label="less">−</button>
        <input type="number" value={v} min={min} max={max} onChange={(e) => onChange(clamp(Number(e.target.value) || 0))}
          className="mono text-[14px] w-[84px] text-center bg-transparent outline-none" aria-label="value" />
        <button onClick={() => onChange(clamp(v + step))} aria-label="more">+</button>
      </span>
    </div>
  );
}
