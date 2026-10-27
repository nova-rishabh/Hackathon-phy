import type { StoryResult } from "./types";

export type Ctx = "death_register" | "hostel_list" | "boundary_changes" | "duplicates";
export const CTX: { id: Ctx; label: string; code: string }[] = [
  { id: "death_register", label: "death register", code: "death_registered" },
  { id: "duplicates", label: "duplicate clusters", code: "duplicate_cleanup" },
  { id: "boundary_changes", label: "boundary log", code: "boundary_change" },
  { id: "hostel_list", label: "hostel list", code: "hostel_moveout" },
];
export const STORY_ORDER = ["death_registered", "duplicate_cleanup", "boundary_change", "hostel_moveout", "unexplained"];
export const STORY_SHORT: Record<string, string> = {
  death_registered: "death", duplicate_cleanup: "dupes", boundary_change: "boundary", hostel_moveout: "hostel", unexplained: "unexplained",
};

/**
 * Offline fallback only (the API's POST /stories/{booth} is the real computation).
 * Starts from the base result the engine produced and moves every story whose source is
 * switched off into "unexplained". It never invents counts a source did not already explain.
 */
export function recompute(base: StoryResult, on: Ctx[]): StoryResult {
  const total = base.removed_total;
  const off = new Set(CTX.filter((c) => !on.includes(c.id)).map((c) => c.code));
  let un = 0;
  const counts: Record<string, number> = {};
  for (const s of base.stories) {
    if (s.code === "unexplained" || off.has(s.code)) un += s.count;
    else counts[s.code] = s.count;
  }
  const stories = base.stories.map((s) => {
    const k = s.code === "unexplained" ? un : counts[s.code] ?? 0;
    const sh = total ? k / total : 0;
    const h = total ? 1.96 * Math.sqrt((sh * (1 - sh)) / total) + 0.01 : 0;
    return { ...s, count: k, share: sh, ci_lo: Math.max(0, sh - h), ci_hi: Math.min(1, sh + h) };
  });
  const sh = total ? un / total : 0;
  const outcome = sh > 0.5 ? "unusual" : sh < 0.25 ? "likely_benign" : "mixed";
  return {
    ...base, stories, context_used: on, outcome,
    residual: { ...base.residual, count: un, significant: un > 2 * base.residual.expected_background },
  } as StoryResult;
}
