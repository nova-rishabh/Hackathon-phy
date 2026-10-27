# RollWatch: Product Requirements (PRD)

> Team Nova (IDEAS-175) · X AI Tech Ideathon · PS1, AI for Electoral Roll Transparency
> Status: **locked scope, v2** (27 Oct 2026, after a six-reviewer validation pass). This replaces the scope in [`ROLLWATCH_PLAN.md`](ROLLWATCH_PLAN.md).
> Companion docs: [TRD](TRD.md) · [Action plan](ACTION_PLAN.md) · [Design system](DESIGN_SYSTEM.md) · [Demo & pitch](DEMO_AND_PITCH.md) · [Content video](CONTENT_VIDEO.md)

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

### 5.2 SHOULD (after the checkpoint, before the freeze)

- **S1. Screenshot claims.** The bot or web accepts a forward image; vision extracts the text, then Claim Court runs.
- **S2. Telegram bot with a share card.** The same brain as the web chat. A claim returns a forwardable Hindi/English **fact-check card** image with a QR code to the reasoning.
- **S3. Hindi voice in and out** (Sarvam). Punjabi voice out if there's time.
- **S4. Notice explainer.** "I got a notice / logical discrepancy" brings up the rule checks such a notice may come from, how often each fires on benign records (from our own synthetic eval), the document that resolves it, and the right form.
- **S5. Rule cards page.** Each rule check is listed with what it tests, its false-positive rate on benign synthetic records, and its innocent explanations.
- **S6. Review buttons.** Benign / escalate, with an append-only audit log (hash chain).
- **S7. Print report.** A `/report` page saved to PDF from Chrome.
- **S8. Realism chart.** Sampleabad's age pyramid and death rate next to published aggregate figures (Census C-13 shape, SRS 2022 death rate of 6.8 per 1,000).

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

## 6. Key user stories and acceptance criteria

Acceptance is checked by **one manual run-through of the demo script**, not by a test suite. See TRD §9 for the five smoke checks.

| # | Story | Done when |
|---|---|---|
| U1 | Meena types "meena kumaari booth 47" | She gets मीना कुमारी, Booth 47, "not in the new list, reason category: shifted", next steps, and the confidence. The same works in Punjabi. |
| U2 | An auditor opens Booth 47 | The card reads: lost 412, expected ~60, stories checked, unexplained residual 82% ±6, "Unusual, needs human review". |
| U3 | The auditor opens Booth 12 | The card reads: lost 380, fits hostel move-out (81%), "Likely benign". |
| U4 | The auditor toggles the boundary-change log on Booth 63 | The residual drops visibly and the label changes. |
| U5 | The auditor opens a duplicate cluster | Three spellings across two scripts, masked names, "flagged for review, never removed". |
| U6 | Someone pastes "Booth 47 mein 400 naam kaat diye, sab ek community ke!" | Verified: "about 400 left Booth 47". Disputed: "cut overnight". Cannot be proven: "one community" (we never infer community). Each sub-claim shows its query. |
| U7 | A mirror claim ("ghost voters added in Booth 30") | An identical verdict structure, side by side, with "identical treatment ✓". |
| U8 | The trust panel | "Hidden by teammate: N anomalies + M decoys. Found X, cleared Y decoys, missed Z: here's why." |
| U9 | (S2) Forward a screenshot to the bot | A card image comes back within about 15 s, and its percentages match the dashboard exactly. |

## 7. Success metrics (what we show on stage)

- **Blind recall** on planted anomalies of at least 0.8, and **decoys cleared** of at least 0.8. Show the real numbers, even if lower, and explain the misses.
- **Zero** neutrality violations across all generated outputs, shown as a log count.
- **Demo:** 4:00 with the network off, run five times in a row without a failure.
- **Bot reply** under 15 s for a cached path and under 30 s live.

## 8. Adoption story (the "from Monday" slide; PS1 doesn't require it, but it wins Feasibility & Impact)

- **Wedge:** data-journalism desks and election-watch NGOs during revision windows. They run RollWatch locally on rolls they already obtain legally, and the outputs are booth-level aggregates.
- **First 100 users:** journalism schools and civic-tech groups in Delhi NCR, plus the citizen bot as a free public layer.
- **Sustainability:** an open-source core, hosted for NGOs on civic-tech grants.
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
