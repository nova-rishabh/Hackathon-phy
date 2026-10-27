// Reads engine/bench.py output (served inside GET /ops as `bench`). All numbers are measured by Python.
type Run = { label: string; n_v1: number; workers: number; total_ms: number; duplicate_pairs?: { v1?: { candidate_pairs: number; naive_pairs: number; reduction_x: number } } };

export type BenchSummary = { voters: number; secs: number; pairs: number; naive: number; reduction: number; base?: { voters: number; secs: number } };

export function benchSummary(b: unknown): BenchSummary | null {
  const runs = (b as { runs?: Run[] } | null)?.runs;
  if (!runs?.length) return null;
  const serial = runs.filter((r) => r.workers === 1);
  const pick = (serial.length ? serial : runs).reduce((a, r) => (r.n_v1 > a.n_v1 ? r : a));
  const base = (serial.length ? serial : runs).reduce((a, r) => (r.n_v1 < a.n_v1 ? r : a));
  const d = pick.duplicate_pairs?.v1;
  return {
    voters: pick.n_v1, secs: pick.total_ms / 1000,
    pairs: d?.candidate_pairs ?? 0, naive: d?.naive_pairs ?? 0,
    reduction: d ? d.naive_pairs / Math.max(d.candidate_pairs, 1) : 0,
    base: base !== pick ? { voters: base.n_v1, secs: base.total_ms / 1000 } : undefined,
  };
}

export const big = (n: number) =>
  n >= 1e9 ? `${(n / 1e9).toFixed(0)}B` : n >= 1e6 ? `${(n / 1e6).toFixed(n >= 1e7 ? 0 : 1)}M` : n >= 1e3 ? `${Math.round(n / 1e3)}k` : String(n);
