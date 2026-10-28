"use client";
import { useEffect, useState } from "react";

/** The RollWatch API. Every number on the page comes from here; nothing is written into the page by hand. */
export const API = (process.env.NEXT_PUBLIC_API_BASE || "https://rollwatch-api.onrender.com").replace(/\/$/, "");
export const WA_NUMBER = "918076499841";

export async function get<T>(path: string, ms = 60000): Promise<T> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), ms);
  try {
    const r = await fetch(API + path, { signal: ctl.signal });
    if (!r.ok) throw new Error(String(r.status));
    return (await r.json()) as T;
  } finally { clearTimeout(t); }
}

export async function post<T>(path: string, body: unknown, ms = 60000): Promise<T> {
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), ms);
  try {
    const r = await fetch(API + path, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: ctl.signal,
    });
    if (!r.ok) throw new Error(String(r.status));
    return (await r.json()) as T;
  } finally { clearTimeout(t); }
}

/** Fetch once on mount. data stays null until the API answers; the page shows a dash, never a made-up value. */
export function useApi<T>(fn: () => Promise<T>, deps: unknown[] = []): { data: T | null; error: boolean } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    let live = true;
    fn().then((d) => live && setData(d)).catch(() => live && setError(true));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return { data, error };
}

// ---------------------------------------------------------------- response shapes (from contracts/models.py)

export type Outcome = "normal" | "unusual" | "likely_benign" | "mixed";
export interface Booth { booth_id: string; n_v1: number; n_v2: number; del_rate: number; expected_del_rate: number; outcome: Outcome }
export interface Overview { totals: { v1: number; v2: number; added: number; deleted: number; modified: number }; booths: Booth[] }

export interface StoryShare { code: string; label: string; count: number; share: number }
export interface Story {
  booth_id: string; removed_total: number; stories: StoryShare[];
  residual: { count: number; expected_background: number; significant: boolean }; outcome: Outcome;
}
export const ALL_SOURCES = ["death_register", "hostel_list", "boundary_changes", "duplicates"];
export const story = (booth: string, sources = ALL_SOURCES) => post<Story>(`/stories/${booth}`, { context_on: sources });

export type Verdict = "verified" | "disputed" | "unprovable";
export interface SubClaim { id: string; text: string; query_shown: string; verdict: Verdict; reason: string; confidence: number }
export interface ClaimResult { claim_id: string; sub_claims: SubClaim[]; confidence: number; mirror?: { claim_text: string; sub_claim_verdicts: Verdict[] } }
export const checkClaim = (text: string) => post<ClaimResult>("/claims/check", { text });

export interface CitizenAnswer {
  lang: string; answer_text: string; status: "present" | "modified" | "not_in_new_list" | "not_found";
  match: { name_dev: string; name_lat: string; booth_id: string; voter_id: string } | null;
  next_steps: string[]; confidence: number;
}
export const ask = (text: string, lang: "hi" | "en" | "pa") => post<CitizenAnswer>("/citizen/ask", { text, lang, channel: "web" });

export interface BlindEval {
  eval: { planted_anomalies: number; planted_decoys: number; found: number; decoys_cleared: number; misses: unknown[] };
  false_alarms: { raised: number; raised_real: number; raised_false: number; real_share: number; booth_spike_false: number; cleared_likely_benign: number;
    by_rule: { rule: string; raised: number; false: number }[] };
}
export interface Limits { median: number; min: number; max: number; median_share_of_booth: number; by_booth: Record<string, number> }
export interface Sim { booth_id: string; hidden_total: number; caught: number; flagged: number; limit: number; booths: { verdict: string; removed_after: number; expected: number }[] }
export const simulate = (booth: string, k: number, spread = 1) => get<Sim>(`/simulate?booth=${booth}&k=${k}&spread=${spread}`);

export interface Ops {
  projection?: { electors: number; audit_minutes_on_64_cores: number; audit_core_hours: number; checks_per_day: number; checks_per_s_peak: number;
    citizen_answers_per_s_4proc: number; machines_at_peak: number; states: { state: string; electors: number; minutes_on_16_cores: number }[] };
  bench?: { runs: { label: string; n_v1: number; workers: number; total_ms: number }[] };
  inr_per_check?: number;
}

// ---------------------------------------------------------------- formatting

const IN = new Intl.NumberFormat("en-IN");
export const fmt = (n: number | null | undefined) => (n == null ? "—" : IN.format(n));
export const pct = (x: number | null | undefined, d = 0) => (x == null ? "—" : `${(x * 100).toFixed(d)}%`);
export const crore = (n: number) => `${(n / 1e7).toFixed(1)} crore`;
