import type { StoryResult } from "./types";

export type Ctx = "death_register" | "hostel_list" | "boundary_changes" | "duplicates";
export const CTX: { id: Ctx; label: string; code: string }[] = [
  { id: "death_register", label: "Use death register", code: "death_registered" },
  { id: "hostel_list", label: "Use hostel list", code: "hostel_moveout" },
  { id: "boundary_changes", label: "Use boundary-change log", code: "boundary_change" },
  { id: "duplicates", label: "Use duplicate clean-up", code: "duplicate_cleanup" },
];
// Mock only: counts that a context source would explain if switched on (taken from "unexplained").
const LATENT: Record<string, Partial<Record<Ctx, number>>> = { B063: { boundary_changes: 84 } };

export function recompute(base: StoryResult, on: Ctx[]): StoryResult {
  const total = base.removed_total;
  const used = new Set<string>(base.context_used);
  const latent = LATENT[base.booth_id] || {};
  const counts: Record<string, number> = {};
  let un = 0;
  for (const s of base.stories) { if (s.code === "unexplained") un = s.count; else counts[s.code] = s.count; }
  for (const c of CTX) {
    const isOn = on.includes(c.id);
    if (!isOn && used.has(c.id)) { un += counts[c.code] || 0; counts[c.code] = 0; }
    if (isOn && !used.has(c.id) && latent[c.id]) { const k = Math.min(latent[c.id]!, un); counts[c.code] = (counts[c.code] || 0) + k; un -= k; }
  }
  const stories = base.stories.map((s) => {
    const k = s.code === "unexplained" ? un : counts[s.code] ?? 0;
    const sh = total ? k / total : 0;
    const h = total ? 1.96 * Math.sqrt((sh * (1 - sh)) / total) + 0.01 : 0;
    return { ...s, count: k, share: sh, ci_lo: Math.max(0, sh - h), ci_hi: Math.min(1, sh + h) };
  });
  const sh = total ? un / total : 0;
  const outcome = sh > 0.5 ? "unusual" : sh < 0.25 ? "likely_benign" : "mixed";
  return { ...base, stories, context_used: on, outcome,
    residual: { ...base.residual, count: un, significant: sh > 0.5 } };
}
