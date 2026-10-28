# RollWatch: Phase 2 brief (read this before you present)

Everything either of us needs before the final round, on one page. Every number was read from the live API on 28 Oct 2026 (seed 42). The deck prompt is in [`PHASE2_DECK_PROMPT.md`](PHASE2_DECK_PROMPT.md).

**Live:** web **rollwatch-web.onrender.com** · WhatsApp **+91 80764 99841** · Telegram **@Rollwatch_bot** · API rollwatch-api.onrender.com

---

## 1. Before you walk in (demo-proofing)

1. **5 minutes before:** `python scripts/warmup.py`. Every line must say OK. The web sleeps after 15 idle minutes, and the first load takes about 30 to 60 s.
2. **If any line says FAIL, or the Wi-Fi is bad:** `powershell -File scripts\demo_local.ps1`, then `python scripts/warmup.py --local`, then present from **http://127.0.0.1:3000**. Audit, Check, Ask and Trust work offline with the same numbers. Sign-in and live voice need the internet.
3. **On the laptop:** start one WhatsApp worker and one Telegram bot. Never run two WhatsApp workers. Send the demo forward to WhatsApp yourself once, so the first reply on stage is warm.
4. **Tabs open in this order:** Audit (home), Check, Ask, Trust (scrolled to "Try to fool it"), Run it, Pricing. Keep the film (`web/public/rollwatch-film.mp4`) open as the last-resort backup.
5. **Laptop plugged in, sleep off.** The bots run on it.

---

## 2. RollWatch in 60 seconds

- **What:** RollWatch explains changes in a voter list. For each booth it says whether removals fit an innocent story (death, hostel move-out, boundary change, duplicate) or **no story**, so a person should check. It fact-checks viral claims part by part and tells any voter why their name changed and which form to file.
- **Not about voting or parties.** It checks the list of voters. It never names a party, person or institution, and never guesses religion, caste or community.
- **Synthetic data:** the fictional district Sampleabad, 100 booths, 51,036 voters. The method and every number are real code output.
- **AI's job is small:** Gemini splits a claim into parts, reads screenshots and phrases text. ElevenLabs does Hindi voice. **Python computes every number.** Turn the AI off and the verdicts don't change.
- **Every output** shows its reasoning and a confidence score, and says it needs human review.
- **The line for the room:** *"Every team can flag a spike. We tell you which story the spike fits, and we prove we're not guessing."*

---

## 3. What went wrong in Round 1, and how we answer it now

This is the most important section. The judges told us where we were weak; the final deck is built so each point is answered with something we can show.

### What the judges said

| # | When | What they said | Our answer now | What to show |
|---|---|---|---|---|
| 1 | Presentation round (27 Oct) | **"It's not scalable."** | It scales on three axes. **Compute:** every test is per booth and linear, so a state is just more booths. 10,20,720 voters in 53.9 s on one laptop core; all 97.8 crore electors in **13.5 min on 64 cores**; Uttar Pradesh in 8.5 min on one 16-core server. **Adoption:** answers go back as share cards into the chat the rumour came from, no install. **Scope:** the same method fits any "cleaned" list (ration cards, pensions), because story rules are a YAML file. | Trust → "At national scale" and "Ops" |
| 2 | Presentation round | **"Can't the government just do this, or integrate it?"** | Yes, and they should: an office runs `POST /audit` (the **Run it** page) on a draft before publishing. But **a self-audit can't settle a rumour about the auditor**, so the same open engine must also be in independent hands (newsrooms, observers, citizens). Same code, same numbers, so the two sides can't disagree about the arithmetic. If they adopt it, we win; the independent copy still has a job. | Run it page (10-booth sample, about 3 s) |
| 3 | Checkpoint (28 Oct) | **"Why not big data or machine learning instead of a small model?"** | No labelled data of real wrongful deletions exists to train on, and a notice must say *why*. "412 removed against about 25 expected; 401 match no record" can be contested; a model score can't. We use ML where it fits: calibrated confidence (Platt curves on four training districts), cross-script name matching, and the language model. Research agrees: Royston et al. (2021, with the Iowa Secretary of State) found district-comparison statistics worked best and labelled each change's likely cause, as we do. | Trust → "Why statistics, not a black box" |
| 4 | Checkpoint | **"How do you handle crores of requests?"** | If 10% of voters check once in a 30-day revision, that's 33 lakh checks a day, **about 189 a second at a 5× peak**. One laptop measured **163 full citizen answers a second on 4 processes** (a lower bound), so **2 machines** cover India's peak. The audit is computed once per roll, viral claims are cached, a name lookup is an index search, and WhatsApp state lives in Redis, so we add servers rather than rewrite. | Trust → load-test table |
| 5 | Red team (our own review before Round 1) | **Pitch was a feature tour, full of jargon, with no "from Monday" story.** | One persona carries the story (Meena, Booth 47). Every slide has one headline and one visual. A pricing slide and a concrete ask: one newsroom or election-watch pilot in the next revision. | Slides 12-13 |
| 6 | Rishabh, Round 1 | **The v1 design "looked AI"** (violet/brick, generic icons). | Rebuilt in design v2: butter.video-inspired, near-white with grey panels, Geist regular-weight two-tone headlines, colour only as small signal chips, our own glyphs, Rishabh's logo. Dark theme added as token overrides only. | The site itself |

### Problems we hit while building (and fixed); use them if asked "what was hard?"

| Problem | What we did |
|---|---|
| **"Synthetic data proves nothing."** We grade our own homework. | A **separate AI agent** planted 9 anomalies and 6 innocent look-alikes in a fresh district and kept the key. We found **9 of 9** and cleared **6 of 6**, never having seen it. |
| **"You found 9 of 9, but how many false alarms?"** | We counted them: **263 of 283** raised flags were real (93%); **0 false alarms on booth spikes**; the 20 false ones are record-level (14 duplicate pairs, 6 relation conflicts). |
| **"What can't you catch?"** | We built **"Try to fool it"**: hide names in any booth and the engine reruns its own tests live. We publish the blind spot ourselves (see §5). |
| **A helper agent's demo tour invented numbers** (53 removals, 100%, 118/118). | Removed. Replaced with a 10-stop tour that reads live engine numbers only. Rule: the LLM never makes a number. |
| **Name search matched the wrong person** (a loose match found someone else). | Every typed word must now match a name word, bar 0.85. **0 of 2,950** names not in the roll matched anyone; 381 of 400 real voters typed with a typo were still found, 0 wrong person. A first name alone asks for the surname. |
| **The first demo claim ("overnight") couldn't be checked honestly**, because rolls carry no removal dates. | Changed the claim to one where every part maps to a real tool: 600 (disputed), most of any booth (verified), one community (cannot be proven). |
| **Access-control holes** in features a second agent added (workspaces, billing). | Found in review and fixed: roles come only from membership, billing and recalibration are operator-only, jobs need a private token. **26 attack checks** pass. |
| **Free hosting sleeps;** a cold demo can stall on stage. | `scripts/warmup.py` and an offline fallback (`scripts/demo_local.ps1`, DEMO_MODE) with the same numbers. |
| **Official discrepancy checks flag innocent people** (the real-world problem behind the PS). | We ran the seven a roll supports: they trip **81-100% innocent** records on our district. We publish an error rate per rule and never raise those checks as flags. |

---

## 4. What's new since Round 1 (say "we built this after you told us X")

The presentation round showed a plan. Everything below is now live:

- **Blind test** by a separate agent: 9/9 found, 6/6 decoys cleared, 0 missed; leads the Trust page.
- **False alarms, counted:** 263 of 283 real, 0 on spikes.
- **Try to fool it:** live detection limits per booth, with the blind spot stated.
- **At national scale:** 97.8 crore in 13.5 min on 64 cores; 189/s peak; 2 machines (computed by the API from ECI's 2024 table).
- **Official checks measured:** 7 checks, 81-100% innocent.
- **Run it:** upload two roll CSVs (or the sample) and get the audit in about 3 s; `POST /audit` for offices. Also reads searchable roll PDFs.
- **WhatsApp bot** (+91 80764 99841) beside Telegram: forward a claim → share image back; Hindi voice note in → spoken Hindi reply (voice "Devi") written to be heard; sign-in codes; booth-watch alerts.
- **Documents checker** from the BLO's SIR sheet: which documents a notice asks for, by birth date (web, WhatsApp, Telegram).
- **Citizen matching hardened:** 0 wrong matches out of 2,950; "Not listed" for unknown names; Gurmukhi names.
- **Pricing and billing:** citizens free; organisations build a plan; Razorpay subscriptions (test mode) verified server-side.
- **Platform:** workspaces, roles and API keys; async constituency audits; newsroom report and CSV exports; review queue with a hash-chained history; recalibration from reviews; 7 languages in citizen answers; monitoring; link previews (a shared claim previews as its verdict card).
- **Safety:** neutrality guard on every outbound message; per-client rate limits; size caps; 26 access-control checks.
- **UI:** dark theme (sun/moon toggle), 10-stop onboarding tour (`/?tour=1`), one loader for every wait, phone layout.

---

## 5. The numbers, cold (with where they live)

| Topic | Number | Source |
|---|---|---|
| District | 51,036 → 49,675 voters; 2,966 removed, 1,605 added, 747 changed; 100 booths | `/overview` |
| Booth 47 | 412 removed vs about 25 expected; 10 deaths, 1 duplicate, **401 (97%) unexplained** → needs human review | Audit, `/stories/B047` |
| Booth 12 | 390 removed; **308 (79%) hostel move-out**, 60 deaths; 21 left vs about 39 expected → likely benign | `/stories/B012` |
| Booth 63 | 154 removed; boundary log off: 99 (64%) unexplained; on: **13 (8%)** → mixed | `/stories/B063` |
| Claim Court | 600 **disputed** (412, 46% off, 15% tolerance) · most of any booth **verified** (rank 1 of 100) · community **cannot be proven** · how sure 86% | Check |
| Blind test | **9/9** found, **6/6** decoys cleared, 0 missed | Trust, `/eval/blind` |
| False alarms | **263 of 283** real (93%); **0** on booth spikes; 20 record-level (14 duplicates, 6 relations); 11 self-cleared | Trust |
| Calibration | stated about 94% → right 93% (280 flags, blind district) | `/eval/blind` |
| Try to fool it | median **19** names (8-40, about 4% of a booth); Booth 23: 17 spike only, **18 caught**; 1,000 spread over 100 booths → 58 show a spike, **2 reach review** | Trust, `/simulate` |
| Official checks | parent gap 113 trips, 81% innocent · many children 166, 98% · name changed 196, 100% · relative's name 323, 100% · relation type 183, 100% · age not progressing 44, 100% · grandparent gap 0 | Trust |
| Real-world context | about 1.3 crore flagged in West Bengal; 91% of decided appeals restored the voter | The News Minute, IFF |
| Engine speed | 10,20,720 voters in **53.9 s** on one core; district in 2.5 s; Booth 47 bootstrap (500 resamples) 2 ms | Trust → Ops, `cache/bench.json` |
| Duplicates | 9.9M candidate pairs instead of 521B (blocking + union-find) | Trust → Ops |
| National | 97.8 crore electors, 14.4 core-hours, **13.5 min on 64 cores**; UP 8.5 min on 16 cores | `/ops` → projection |
| Traffic | 33 lakh checks/day, **189/s peak**; 163 citizen answers/s on 4 processes; **2 machines** | `/ops` |
| Load test | 1 → 4 processes: overview 131.7 → 242.1/s; name search 103.1 → 202.2/s; citizen answer 72.1 → 163/s; claim check 105.1 → 211.3/s | `/ops` |
| Cost | about ₹0 per check | Trust → Ops |
| Name matching | 0 of 2,950 unlisted names matched; 381/400 typo'd real voters found, 0 wrong | `tests/test_name_matching.py` |
| Pricing | newsroom ₹9,098/mo (50% non-profit off) · watch group ₹28,494/mo · election office ₹1,84,473/mo; yearly = 2 months free | `/billing/quote` |

**Don't quote these old numbers** (still in some older docs): "about 60 expected" (now about 25), "400 unexplained" (401), "Booth 12: 380 removed, 81%" (390, 79%), "card confidence 76%" (86%), "6 of 6 / 7 of 7" as the headline scoreboard (that's the demo district; lead with the blind test 9/9, 6/6), "PDF ingestion is roadmap" (it reads searchable PDFs now; scanned PDFs and a real constituency are roadmap).

---

## 6. The demo run (about 4 minutes, if a live demo is asked for)

| Time | Page | Do | Say |
|---|---|---|---|
| 0:00 | — | Read the forward aloud | "Forwards like this spread in hours after every revision. Nobody can check them." |
| 0:20 | **Check** | Paste the forward → three rows → point at the queries → mirror card | "Gemini only splits the sentence. Python runs a fixed query for each part. We never infer community, so that part can't be proven, and it says why." |
| 1:00 | **Audit** | Booth 47, then Booth 12, then Booth 63 and switch the boundary log | "To a rumour these look the same. Only one is unexplained. Switch a source off and the answer moves." |
| 1:50 | **Ask** | `meena kumaari booth 47` → Listen | "Wrong spelling, wrong script, still found. The reason, the form, 1950, and a BLO never asks for an OTP." |
| 2:30 | **Trust** | Scoreboard → False alarms → Try to fool it: Booth 23, slide to 17 then 18 | "A separate agent hid the problems. We found all 9. Here's every false alarm. And here's what we can't catch." |
| 3:20 | **Run it** | Run the 10-booth sample | "This is the inside path: an office checks a draft before publishing." |
| 3:40 | Slide 11 | The three questions | Scale · why not the government alone · future-proof (§7). |

Then hand judges the persona cards (Meena Kumari B047, Ravi Verma B012, Harpreet Kaur B063) and the WhatsApp number to try **after** the pitch.

---

## 7. The three questions (always answer all three, each with something we can show)

- **How does it scale?** Every test is per booth and linear, so a state is just more booths run in parallel: 1.02M voters in 53.9 s on one core, all of India in 13.5 min on 64 cores, 2 machines for peak citizen traffic. It spreads as share cards in the chat the rumour came from, with no install. The same method fits any "cleaned" list, because story rules are config. *Show: Trust → national scale.*
- **Why can't the government do this alone?** A self-audit can't settle a rumour about the auditor. They should run it before publishing (Run it, `POST /audit`), but the same open engine must also be in independent hands, so both sides agree on the arithmetic. *Show: Run it.*
- **Why is it future-proof?** The core is fixed and measured. Data (adapters to an open schema, roll PDFs), rules (YAML), model (swappable, never makes a number, template fallback), languages and channels are swappable parts. We swapped the model and the voice in an afternoon, and the blind test re-measures every change. *Show: DEMO_MODE (AI off, same verdicts) and the Trust page.*

---

## 8. Likely questions, short answers

**Depth**
- *Is this a Gemini wrapper?* No. Turn the model off and every verdict is the same. The engine is plain Python; every row shows the query behind its number.
- *Why a binomial test?* Each voter is removed or not, with a background probability from the booth's age mix: that is exactly a binomial. Benjamini-Hochberg keeps false alarms in check across 100 booths.
- *Why not compare every pair for duplicates?* 51k voters is 1.3 billion pairs. Blocking by booth/house and relation name cuts it to about 0.5 million; union-find merges matches. At 1M voters: 9.9M pairs instead of 521B.
- *What does "93%" mean?* On the blind district, flags we stated at about 94% were right 93% of the time. The curve was fit on separate training districts.
- *What if the death register is wrong?* Then the story is wrong too, and the evidence toggles show it. We show which records explain what, never a bare verdict.
- *Couldn't you hide a real problem inside a benign booth?* If the leftover after the innocent stories is still above background, the booth stays unusual. Booth 47 has 10 real deaths and 401 unexplained, and it's flagged.

**Honesty**
- *What can't you catch?* Fewer than about 19 names in a booth (8 to 40 depending on the booth). And names spread thin: 1,000 over 100 booths shows a spike in 58 booths but sends only 2 to review. A district-level test for many small spikes is the next step. Say this before they ask.
- *Synthetic data proves nothing?* It proves the method against an answer key real data can't give you. A separate agent hid the problems; we found 9 of 9. Real use needs recalibration.
- *What does "likely benign" mean?* Many names left, but a record explains most of them, and what's left is normal (Booth 12: 79% hostel move-out). A person still confirms.

**Data and neutrality**
- *Religion or caste?* Never inferred. Rolls don't carry it and we won't guess from names, so that part of a claim returns "cannot be proven".
- *How would real data get in?* Rolls are published per polling part. A newsroom or observer runs it on rolls they already get legally, through an adapter to our open schema. Public outputs are booth-level; auditor views mask names.
- *Isn't the guard just a regex?* Three layers: the model only sees computed numbers, the schemas have no field for parties or people, and a final check blocks or rewrites, logs it, and falls back to a template. The mirror test proves it behaviourally.
- *Could a card be misused as "AI proves deletions"?* Every card says "patterns for human review, not findings", shows the innocent explanations and never shows a voter's name.

**Product**
- *Who uses it first?* Data desks and election-watch groups during revision windows; citizens through the bots.
- *Who pays?* Citizens never do. Organisations build a plan: a newsroom desk about ₹9,000 a month, an election office about ₹1.8 lakh, paid via Razorpay. Open-source core; heavy users can bring their own AI key.
- *Why would a voter use this over the official app?* We don't replace it. The official app says *whether* you're listed; we say *why* you changed and *what to do*, with voice and Punjabi, and hand off to the official portal and 1950.
- *Can it be abused?* Paid and heavy endpoints have per-client limits, uploads are size-capped, WhatsApp is limited per number, payments are verified server-side.
- *Did AI write the code?* We used Claude Code as a coding assistant and say so in the README. The design, the statistics, the evaluation and the review are ours; either of us can walk through any function.
- *Another week?* Recalibrate on more districts, a district-level test for thinly spread removals, one real constituency through the PDF adapter (aggregates only), a CDN in front of the static routes.

---

## 9. Never say

- Fraud, rigging, scam (except "a BLO never asks for an OTP or money"), "ghost voters" outside a quoted claim.
- Any party, person or institution name.
- "AI-powered", "smart", "magic", "revolutionary", "seamless".
- Any number not in §5. If you don't know, say "let me show you on the Trust page".
- That RollWatch "proves" anything. It flags patterns for human review.

## 10. Honest limits (the closing slide)

- Synthetic data only; confidence needs recalibration on real rolls.
- Per-booth tests miss removals spread very thin across many booths.
- Scanned roll PDFs and a real constituency are roadmap.
- Not affiliated with any official body.
- **Ask:** one newsroom data desk or election-watch group as a pilot in the next revision.
