# RollWatch: Product Requirements (PRD)

> Team Nova (IDEAS-175) · X AI Tech Ideathon · PS1, AI for Electoral Roll Transparency
> Status: **locked scope, v3** (27 Oct 2026, dev start). v3 cuts generic features, promotes the share loop, rule error rates and the ops numbers, and tunes the build to the judge (see [START_HERE §3](START_HERE.md#3-who-were-building-for-the-judge)). It replaces v2 and [`ROLLWATCH_PLAN.md`](ROLLWATCH_PLAN.md).
> Companion docs: [Start here](START_HERE.md) · [TRD](TRD.md) · [Action plan](ACTION_PLAN.md) · [Design system](DESIGN_SYSTEM.md) · [Demo & pitch](DEMO_AND_PITCH.md) · [Content video](CONTENT_VIDEO.md)

---

## 1. One line

**RollWatch tells you which story a voter-roll change actually fits, how sure it is, and sends the answer back to the group the rumour came from. It works in Hindi, English and Punjabi, and it takes no side.**

Pitch line for the room:
> "Every team here can flag a spike. We tell you which story the spike fits, with the working shown, and we treat a claim from either side exactly the same."

## 2. Why now (pitch context only, never inside the product)

- **Scale.** SIR Phase 3 covers 16 states and 3 UTs, Delhi included. Delhi's draft roll left out 47.56 lakh of 1.45 crore electors (32.78%); shifted/absent was 29.86% of electors, dead 1.95% and duplicate 0.98%.
- **Live window.** Delhi's claims window is open until 30 Oct, and the final roll is due 4 Dec 2026. Recheck that date before the demo.
- **Opaque flags.** Official revision software already raises rule-based "logical discrepancy" flags, with no published thresholds or false-positive rates. On 22 Sep the Supreme Court asked for the term to be defined.
- **The gap:** nobody can tell, for a given change, *which innocent explanation fits and how often a rule is wrong*.

Use these real numbers only in the pitch and the video, with sources ([research report summary](SESSION_LOG.md#session-2)). **The product itself runs only on the fictional district.**

## 3. Users and the job each one hires us for

| User | Job | Where they meet RollWatch |
|---|---|---|
| **Citizen** (Meena, 52, Booth 47, reads Hindi, types in Roman) | "Is my name still there? If not, why, and what do I do before the deadline?" | Web chat and Telegram, text or voice |
| **Journalist / election observer / NGO desk** | "Is this booth's drop unusual, or does an innocent story explain it? Show me the working." | Auditor dashboard |
| **Anyone who receives a viral forward** | "Is this forward true?" | Forward a screenshot to the bot and get a shareable fact-check card back |

**Out of scope as users:** election officials and parties. We never position the tool as an enforcement tool.

## 4. Product principles (from PS1 rules, made visible)

1. **Synthetic data only.** One fictional district, **Sampleabad**, with 10 wards, 100 booths and about 50k voters. Never put flags on a real place.
2. **Patterns, never verdicts on people.** Every flag says "needs human review". We never say fraud and never name a party, person or institution in generated text.
3. **Reasoning and confidence on every output.** Each output shows the numbers, the baseline, the innocent explanations checked and a confidence with its sample size.
4. **Mirror symmetry.** Every claim is also run in its opposite direction and gets an identical structure of treatment.
5. **Numbers come from Python, words come from the LLM.** The LLM never produces a number that appears on screen.
6. **No protected-attribute inference.** We never infer religion, caste or community from names. Claims that depend on it return "cannot be proven", with the reason.
7. **Names masked in auditor views.** A full name appears only in the citizen's own lookup.

## 5. Scope

### 5.1 MUST (ships by the checkpoint)

**M1. Change engine**
- **Roll diff.** Roll v1 → v2 diff, classifying each record as added, deleted or modified.
- **Booth deletion test.** Per-booth deletion rate against the age-adjusted expected rate (binomial test), with Benjamini-Hochberg FDR correction across the 100 booths.
- **Cross-script duplicates.** Matches names across Devanagari and Latin, e.g. सुनीता शर्मा = Suneeta Sarma = Sunita Sharma, same relation, same house. Method: transliteration, then a phonetic normaliser, then fuzzy matching, then clusters.
- **Rule checks:**
  - age under 18 or over 110
  - a relation conflict, where both records are in the roll
  - a household over 15 voters
  - a gender-ratio swing

**M2. "Which Story Fits?" explainer** (hero 1)
- **Attribution.** For each flagged booth, every removed record is attributed to a story: death registered, hostel move-out, boundary change, duplicate clean-up, or **unexplained**.
- **What it shows:** story shares with uncertainty bars, and the unexplained residual tested against the expected background rate.
- **Outcome:** **"Unusual, needs human review"** or **"Likely benign: fits hostel move-out (81%)"**.
- **Live toggle:** switch a context source (e.g. the boundary-change log) off or on and watch the residual change.

**M3. Flag cards**
- Four plain lines: **What we found · Why it's unusual · Innocent explanations checked · How sure we are**.
- Always closes with "Needs human review".
- Available in English and Hindi.
- A template fallback works when the LLM is down.

**M4. Claim Court** (hero 2, text input)
- **Splitting:** a pasted claim is split into sub-claims.
- **Queries:** each sub-claim maps to one of ~9 fixed queries, and the exact query and its numbers are shown.
- **Verdict:** each sub-claim gets **Verified / Disputed / Cannot be proven**. Intent and motive words always land in "cannot be proven".
- **Mirror:** the mirror claim is shown side by side.

**M5. Citizen assistant (web chat)**
- **Languages:** Hindi, English and Punjabi (Gurmukhi) text.
- **Search:** tolerant of typos and script.
- **Answer:** status and reason category, then next steps. It always hands off to the official portal and states the 1950 helpline.
- **Scam warning:** "A BLO never asks for an OTP or money."

**M6. Trust panel (blind evaluation)**
- **Planting:** the partner plants anomalies and benign decoys without the engine owner seeing them.
- **What it shows:** found / missed / decoys cleared per type, the false-positive rate on decoys, and a 3–4-bin reliability chart with counts.

**M7. Neutrality Guard**
- Runs on every generated string: a deterministic lexicon check, then an LLM rewrite, then a re-check, with a template fallback.
- Shown as a badge with a log, **not** as a live jailbreak.

**M8. Demo mode.** Frozen artifacts plus a cached LLM path, so the whole scripted demo runs with Wi-Fi unplugged.

**M9. Forward in, card out** (promoted from S1 + S2; the demo opens with it)
- A forward screenshot (Telegram bot, or dropped onto the web Claim Court) goes through a vision read → Claim Court → a 1080×1350 share card in Hindi and English with a QR code.
- The card goes back into the chat the rumour came from. **This is the distribution loop**: every check is a forwardable artifact.
- **Fallback:** a pasted text claim on the web, and the pre-rendered card.

**M10. Rule cards with published error rates** (promoted from S5, absorbs S4)
- For every rule check: what it tests, **how often it fires on innocent synthetic records** (from the eval), the innocent explanations, and the document that resolves it.
- This answers the real "logical discrepancy" gap: official flags have no published false-positive rate.

**M11. Ops strip** (new, cheap)
- On the Trust page: p50/p95 latency per surface, LLM cost per claim check in ₹, cache hit rate, and the engine run time on the full district.
- Computed from the API's own request log. Founders and engineers ask "what does one check cost?"; we answer before they ask.

### 5.2 SHOULD (after the checkpoint, before the freeze)

- **S3. Hindi voice in and out** (Sarvam) on the bot and web chat.
- **S8. Realism chart.** Sampleabad's age pyramid and death rate next to published aggregate figures (Census C-13 shape, SRS 2022 death rate of 6.8 per 1,000). It lives on the Trust page.
- **S9. Share clip.** An 8–12 s vertical MP4 of the share card with the verdict chips appearing one by one, plus an optional Hindi TTS voice line. Built from headless-Chrome frames and ffmpeg, no new library. A video travels further than an image on WhatsApp.
- **S10. Scale run.** Generate a 1M-voter district (about 20× the demo) and show the engine's wall-clock time and the duplicate-blocking pair count against the naive n² on the Trust page. Proves the algorithms, not just the demo.
- **S11. Telegram claim-check from a group.** Add the bot to a group, and `/check` on a replied-to forward returns the card into that group.
- **S12. Config-driven stories.** Move the story order and match keys from `engine/stories.py` into `engine/stories.yaml`. **Demo beat:** add a new evidence source (e.g. "objections filed", a synthetic Form 7 log) by editing YAML and re-running, and the residual drops. This proves "a new register or office plugs in without code" (judges' scalability question).

**M12. Integration endpoint** (new, small; answers "can't the government integrate it?")
- `POST /audit` takes two roll files in the **open input schema** (`contracts/` RollRow, CSV or parquet) plus optional evidence tables, and returns flags, stories and rule hits as JSON.
- Add `Dockerfile` + `docker-compose.yml` (api + web) so an office or newsroom runs it offline in one command.
- Document both in the README under "Run it on your own rolls".

**Removed in v3 (generic or low-value):** S1 and S2 (now M9), S4 notice explainer (absorbed into M10), S5 (now M10), **S6 review buttons + hash chain, S7 print report, Punjabi voice**. Punjabi text stays.

### 5.3 CUT (do not build before the freeze)

- PDF roll render and Devanagari OCR
- sentence-embeddings and torch
- the Ollama offline LLM
- IsolationForest, unless an engineer has spare time after S1–S3
- isotonic calibration
- review-queue learning
- change-alert subscriptions
- voice claims
- maps (deck.gl / Leaflet)
- WhatsApp integration (pitch roadmap only)
- a generic map, a generic KPI dashboard, a free-chat "ask anything" bot: every team will have one, and they add nothing to our edge

## 6. Key user stories and acceptance criteria

Acceptance is checked by **one manual run-through of the demo script**, not by a test suite. See TRD §9 for the five smoke checks.

| # | Story | Done when |
|---|---|---|
| U1 | Meena types "meena kumaari booth 47" | She gets मीना कुमारी, Booth 47, "not in the new list, reason category: shifted", next steps, and the confidence. The same works in Punjabi. |
| U2 | An auditor opens Booth 47 | The card reads: lost 412, expected ~60, stories checked, unexplained 400 (97%) ±3, confidence 82%, "Unusual, needs human review". |
| U3 | The auditor opens Booth 12 | The card reads: lost 380, fits hostel move-out (81%), "Likely benign". |
| U4 | The auditor toggles the boundary-change log on Booth 63 | The residual drops visibly and the label changes. |
| U5 | The auditor opens a duplicate cluster | Three spellings across two scripts, masked names, "flagged for review, never removed". |
| U6 | Someone pastes "Booth 47 mein 600 naam kaat diye, sabse zyada, aur sab ek community ke!" | Verified: "most removals of any booth" (compare_booths). Disputed: "600 names" (deletion_count = 412, outside 15%). Cannot be proven: "one community" (we never infer community). Each sub-claim shows its query. |
| U7 | A mirror claim ("ghost voters added in Booth 30") | An identical verdict structure, side by side, with "identical treatment ✓". |
| U8 | The trust panel | "Hidden by teammate: N anomalies + M decoys. Found X, cleared Y decoys, missed Z: here's why." |
| U9 | (M9) Forward a screenshot to the bot | A card image comes back within about 15 s, and its percentages match the dashboard exactly. |

## 7. Success metrics (what we show on stage)

- **Blind recall** on planted anomalies of at least 0.8, and **decoys cleared** of at least 0.8. Show the real numbers, even if lower, and explain the misses.
- **Zero** neutrality violations across all generated outputs, shown as a log count.
- **Demo:** 4:00 with the network off, run five times in a row without a failure.
- **Bot reply** under 15 s for a cached path and under 30 s live.
- **Cost per claim check** shown in ₹ (M11), with the cache hit rate.
- **Engine run** on the full district in under 10 s, and on the 1M-voter scale run (S10) with the time on screen.

## 8. Adoption and scale (the "two ways in" slide; this answers the judges' presentation-round feedback)

- **Inside (integration):** election offices run the open-source engine as a pre-publication check (`POST /audit`, M12). Booths with unexplained removals get a second look before deletion. Rule error rates are published.
- **Outside (independent layer):** data desks, election-watch groups and citizens use the same engine for claim checks and lookups. A self-audit can't settle a rumour about the auditor, so this layer exists even when the inside one does.
- **Wedge:** data-journalism desks and observer groups during revision windows. They run it locally on rolls they already obtain legally, and outputs are booth-level aggregates.
- **First 100 users:** journalism schools and civic-tech groups in Delhi NCR, plus the free citizen bot. Every card shared into a group is the next user's entry point.
- **Scale:**
  - **compute:** per booth, linear, parallel per constituency (S10)
  - **adoption:** chat cards, no install, 3 languages
  - **scope:** config-driven stories reach other public registers such as ration cards and pensions (S12)
- **Future-proof:**
  - adapters to an open input schema (new data sources)
  - config for rules, evidence and forms (new laws and revision drives)
  - an LLM behind a fallback chain that never makes numbers (new models)
  - template files per language, and thin clients per channel
  - the blind eval re-measures every change
- **Sustainability:** an open-source core, hosted for NGOs on civic-tech grants, with paid integration support for offices.
- **Never:** scraping, individual-level public outputs, inferring protected attributes.

## 9. Risks and answers (product level)

| Risk | Answer |
|---|---|
| "Synthetic data proves nothing" | The blind planting with decoys, the realism chart (S8), and "it proves the method; real use needs recalibration". |
| "The official app already searches names" | We explain *why* you changed and *what to do*, in voice and Punjabi, tolerant of script, and hand off to the official portal. |
| "What does the 78% mean?" | It is the probability that the flag is a true planted anomaly, calibrated on an independent seed and validated blind, with n shown. |
| A screenshot goes viral as "AI proves deletions" | Every card carries "pattern for human review, not a finding", plus the innocent explanations, on the same image. |
| Political discomfort | The mirror test, no actor fields in any schema, and the refusal to infer protected attributes. |

## 10. Open decisions (owner: Rishabh)

- Disclosing AI-tool use in the README and pitch, and whether the partner commits under their own identity. The compliance review recommends both.
- The submission format, the deadline and the demo slot length. Ask the organiser contact listed in the rulebook.
