// Offline fallbacks. Every number here mirrors the demo world in docs/START_HERE.md §4
// (the API, when it is up, computes them for real). Shown with a "mock data" note.
import overviewMock from "@/mocks/overview.json";
import flagsMock from "@/mocks/flags.json";
import type { Overview, FlagList, ClaimVerdict, CitizenAnswer } from "@/lib/types";

export const OVERVIEW_MOCK = overviewMock as unknown as Overview;
export const FLAGS_MOCK = flagsMock as unknown as FlagList;

export const DEMO_CLAIM = "Booth 47 mein 600 naam kaat diye, sabse zyada, aur sab ek community ke!";
const guard = { passed: true, blocked_terms: [], rewritten: false };

export const CLAIM_MOCK = {
  claim_id: "demo-b047",
  input: { text: DEMO_CLAIM, source: "text", lang: "hi" },
  normalized_claim: "600 names were removed in Booth 47, the most of any booth, and all from one community.",
  sub_claims: [
    { id: "s1", text: "Booth 47 had the most removals of any booth", tool: "compare_booths", params: { metric: "deleted" },
      query_shown: "rank booths by removed → B047 is 1 of 100 (412)", claimed_value: 1, computed_value: 1, tolerance: 0.15,
      verdict: "verified", reason: "Booth 47 has 412 removals, the highest of all 100 booths.", evidence: { series: [], note: "" }, confidence: 0.9 },
    { id: "s2", text: "600 names were removed in Booth 47", tool: "deletion_count", params: { booth_id: "B047" },
      query_shown: "count removed where booth = B047 → 412", claimed_value: 600, computed_value: 412, tolerance: 0.15,
      verdict: "disputed", reason: "Computed 412 vs claimed 600: 46% off, outside the 15% tolerance.", evidence: { series: [], note: "" }, confidence: 0.86 },
    { id: "s3", text: "All of them are from one community", tool: "unanswerable", params: {},
      query_shown: "no field for community → not answerable", claimed_value: null, computed_value: null, tolerance: 0.15,
      verdict: "unprovable", reason: "The roll has no community field, and RollWatch never infers one.", evidence: { series: [], note: "" }, confidence: 1,
      settle_with: "This part cannot be settled from roll data." },
  ],
  overall: "mixed",
  confidence: 0.76,
  mirror: { claim_text: "Ghost voters added in Booth 30", sub_claim_verdicts: ["disputed", "unprovable"], identical_treatment: true },
  card_png: null,
  guard,
  cached: true,
} as unknown as ClaimVerdict;

export const MIRROR_ROWS = [
  { text: "Unusual additions in Booth 30", query: "count added where booth = B030 → 21 (expected ~24)" },
  { text: "The added names are not real people", query: "no field for identity checks → not answerable" },
];

const MEENA = { voter_id: "SBD0047213", name_dev: "मीना कुमारी", name_lat: "Meena Kumari", booth_id: "B047", status_v2: "not_in_new_list", score: 0.93 };
const TEXT: Record<string, { answer: string; steps: string[] }> = {
  hi: {
    answer: "मीना कुमारी, आपका नाम पुरानी सूची (बूथ 47) में था, पर नई सूची में नहीं है। सबसे संभावित कारण: पता बदलना (shifted)।",
    steps: ["फ़ॉर्म 6 भरकर नाम फिर से जुड़वाएँ।", "दावा-आपत्ति की आख़िरी तारीख से पहले जमा करें।", "अपने बूथ लेवल अधिकारी से पावती लें।", "मदद के लिए 1950 पर कॉल करें।"],
  },
  en: {
    answer: "Meena Kumari, your name was in the old list (Booth 47) but is not in the new list. Most likely reason: marked as shifted.",
    steps: ["Fill Form 6 to be added again.", "Submit it before the claims-and-objections deadline.", "Get an acknowledgement from your booth level officer.", "Call 1950 for help."],
  },
  pa: {
    answer: "ਮੀਨਾ ਕੁਮਾਰੀ, ਤੁਹਾਡਾ ਨਾਮ ਪੁਰਾਣੀ ਸੂਚੀ (ਬੂਥ 47) ਵਿੱਚ ਸੀ, ਪਰ ਨਵੀਂ ਸੂਚੀ ਵਿੱਚ ਨਹੀਂ ਹੈ। ਸਭ ਤੋਂ ਸੰਭਾਵਿਤ ਕਾਰਨ: ਪਤਾ ਬਦਲਣਾ।",
    steps: ["ਫ਼ਾਰਮ 6 ਭਰ ਕੇ ਨਾਮ ਮੁੜ ਜੁੜਵਾਓ।", "ਦਾਅਵੇ-ਇਤਰਾਜ਼ ਦੀ ਆਖ਼ਰੀ ਤਾਰੀਖ਼ ਤੋਂ ਪਹਿਲਾਂ ਜਮ੍ਹਾਂ ਕਰੋ।", "ਆਪਣੇ ਬੂਥ ਲੈਵਲ ਅਧਿਕਾਰੀ ਤੋਂ ਰਸੀਦ ਲਓ।", "ਮਦਦ ਲਈ 1950 'ਤੇ ਕਾਲ ਕਰੋ।"],
  },
};

export function citizenMock(text: string, lang: "hi" | "en" | "pa"): CitizenAnswer | null {
  if (!/meena|mina|मीना|ਮੀਨਾ/i.test(text)) return null;
  const t = TEXT[lang];
  return {
    lang, transcript: null, answer_text: t.answer, answer_audio_url: null, match: MEENA, status: "not_in_new_list",
    reason_category: "shifted", next_steps: t.steps, confidence: 0.78, guard,
  } as unknown as CitizenAnswer;
}
