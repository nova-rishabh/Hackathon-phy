# Session Log #1: Problem Selection & Strategy (26 Oct 2026)

> **For the next Claude session:** this file is the complete memory of session #1. Read it first, then:
> - [`IDEATHON_STRATEGY.md`](IDEATHON_STRATEGY.md): all 6 problem statements ranked, 3 ideas each, top 10, and the validation evidence.
> - [`ROLLWATCH_PLAN.md`](ROLLWATCH_PLAN.md): the build plan for the chosen problem (for 2 humans + Claude Code), with kickoff prompts.
> - [`analysis/`](analysis/): the scripts behind the numbers below (dataset win-rate analysis and the overall-prize Monte Carlo).
>
> **No product code has been written.** The rulebook bans pre-existing work, so coding starts at the event (27 Oct).

---

## 1. Decision (locked)

**We are doing Problem Statement 1: AI for Electoral Roll Transparency.**
**Working product name: RollWatch.**

- Submitted / committing to it on 26 Oct 2026. **We cannot switch later.**
- Backup we would have used: PS2, Event Reach & Registration. It is no longer an option.
- Suggested one-liner for submission forms:
  > RollWatch: an AI tool that makes voter-roll changes auditable, explainable and accessible. It combines anomaly detection, plain-language flag explanations with confidence, a viral-claim checker, and a Hindi/English/Punjabi voice assistant, all on synthetic data and strictly non-partisan.

---

## 2. Event facts (from the official rulebook)

- **Event:** "X AI Tech Ideathon". Rulebook tagline: *Your Idea. Your Code. Your Creation.*
- **Format:** offline on campus, **27–28 Oct 2026, 24 hours**. Theme: AI.
- **Teams:** 2–5 members, no solo entries. Team composition changes need organiser approval.
- **Problem statements:** released the evening of 26 Oct. Each team picks **one**, and the solution must use AI **meaningfully**.
- **Must deliver:**
  - a working prototype
  - a live demo to the judges
  - submission within the deadline
  - every team member contributing actively
- **Disqualifiers:** plagiarism, or **claiming pre-existing work as new**.
- **Judging criteria** (no weights given, so assume equal):
  1. **Innovation**: originality and creativity
  2. **Technical Implementation**: development quality and **effective use of AI**
  3. **Problem-Solving**: relevance and effectiveness
  4. **Feasibility & Impact**: practical applicability, real-world value
  5. **Presentation**: clarity, quality of demo
- **Awards are overall, not per category** (confirmed by Rishabh). We compete against the best project across all problem statements.
- **Bring:** your own laptops, chargers and equipment. Mentors are available during the event.
- **Public web:** nothing found. I searched the event name, tagline, dates and organiser, so the rulebook is the only source.

**Our team:** Team Nova, ID **IDEAS-175**, leader Rishabh Kataria.
- 2 human members, building with **Claude Code** heavily (parallel sessions).
- The team sheet lists ~42 rows (IDEAS-150 to IDEAS-191, a few duplicates), so about 40 competing teams.

**Source documents** (organiser PDFs, kept locally in Rishabh's Downloads folder, not committed):
- `IDEATHON RULEBOOK.pdf`
- `Problem Statements X AI Tech Ideathon.pdf`
- `TEAM ID'S IDEATHON - Sheet1.pdf`
- `All_data.csv`: a reference dataset of ~6,900 Devpost projects from ~59 other hackathons. It is a reference only, not rules for this event.

---

## 3. The 6 problem statements (summary)

Common to all of them:
- synthetic or sample data only
- a 45–90 s content video with AI-made parts, owned by one member
- usable by non-technical people
- Hindi + English + one regional language, where a chat or voice element exists

### PS1: AI for Electoral Roll Transparency ⭐ (OUR PICK, full detail)

**Problem:** voter rolls are huge and technical. Revisions add or delete millions of names, citizens can't check their status, journalists can't audit at scale, and misinformation outpaces facts.

**Challenge:** an AI tool that makes voter-roll data **auditable, explainable and accessible, without taking any political side**.

**Solution modules** (at least 1; *"best teams will combine more"*):
1. **Anomaly detection:** abnormal deletions in an area, duplicate entries, impossible ages, sharp changes between two versions of a roll.
2. **Plain-language explanations:** for every flag, what was found, why it's unusual, and **what innocent explanations exist**.
3. **Citizen assistant:** a text or voice bot in **Hindi, English + one regional language** to check registration and explain next steps.
4. **Claim checker:** takes a viral allegation and returns what is **verified / disputed / cannot be proven** from public data.

**Content video:** 45–90 s. Must include behind-the-scenes footage of the team building, a hook in the first 5 s, a short demo, and AI used in making the video (voiceover, visuals, captions or editing).

**Rules:**
- Synthetic or public data only. **No real voter data.**
- Flag patterns **for human review**. **Never declare fraud or name individuals, parties or institutions.**
- **Every output must show reasoning and a confidence level.**
- **Treat claims from all sides equally.**

**Deliverables:** a working prototype (app, bot or dashboard) and a live demo on test data. **No 1-slide plan is required**, unlike PS2, PS4, PS5 and PS6.

### PS2: AI for Event Reach & Registration
- **Goal:** find the right audience, reach them on the platforms they already use (WhatsApp/Telegram/Instagram/LinkedIn/Discord), and let them register **inside chat**. Must answer "how do the first 100 registrations come from zero?"
- **Modules:** audience discovery + personalised outreach; in-chat registration/FAQ/reminders in 3 languages; growth loops (invite teammates, shareable AI team cards); team matchmaking + no-show nudges.
- **Rules:** no spam (opt-in, **human-approved before sending**), honest promos, non-technical organiser.
- **Deliverables:** a demo of event created → audience found → message sent → registered in chat, plus a **1-slide growth plan (100 → 1,000)** and the video.

### PS3: Deepfake Arena (Red vs Blue)
- **What each team builds:** a Forger (synthetic media from the *provided* personas only) and a Detective (verdict + confidence + human-readable reason), plus an explanation view and a post-game report.
- **Game:** each team submits 5 fakes, the organisers mix them with real items, everyone detects, then a live reveal and scoreboard.
- **Scoring:** fooling a team +10; catch +5; correct real +3; correct reason +3; false alarm −5; miss −3.
- **Video:** **9:16 vertical**, with AI parts labelled. Plus a 5-minute pitch.
- **Runs only if at least 2 teams pick it.** Otherwise those teams must switch.

### PS4: AI for Girls' & Women's Safety
- **Must answer:** "help when she can't call or trigger SOS".
- **Modules:** AI risk detection (route deviation, unexpected stops) with false-alarm control; discreet SOS (wearable, shortcut, voice); a safety network with escalation; safe journey + check-ins; multilingual and accessible.
- **Rules:** privacy-first consent, no surveillance, human oversight, honest AI (no false claims of auto-calling emergency services), fallbacks for poor connectivity.
- **Deliverables:** a demo of journey → trigger → SOS → location shared to a trusted contact → acknowledgement or escalation, plus a **1-slide pilot plan** and the video.

### PS5: AI-Powered Gamified Learning
- **Modules:** personalised learning, learn-by-playing, theory-to-practice simulator, AI mentor with hints (3 languages), real projects + skill proof/portfolio, collaborative learning.
- **Rules:** learning over gaming, honest evaluation (no "mastered" from quizzes alone), a working journey, not a mock-up.
- **Deliverables:** a demo of topic → AI assesses level → mission → practical challenge → AI feedback → skill unlocked, plus a **1-slide adoption plan** and the video.

### PS6: AI for Smarter Healthcare
- **Modules:** health assistant (3 languages), symptom guidance with next steps, medical report simplifier (synthetic reports), preventive care and reminders.
- **Rules:** no definitive diagnosis, emergency guidance, privacy.
- **Deliverables:** a demo of concern → guidance → next steps, plus a **1-slide impact plan** and the video.

---

## 4. How the decision was made (evidence)

### 4.1 Reference dataset (6,917 Devpost projects, base win rate 17.3%)
Directional only: different, mostly US hackathons, small samples for niche themes.

| Theme | n | Win rate |
|---|---|---|
| Election / voter | 45 | 40.0% |
| Misinformation / fact-check | 65 | 35.4% |
| Deepfake | 12 | 41.7% (tiny n) |
| Healthcare | 1,257 | 21.3% |
| Education (any) | 2,577 | 17.7% |
| Gamified learning | 148 | 14.9% |
| Women / personal safety | 31 | 16.1% |

- **Real ML / CV / audio projects won 22.9%, against 16.5% for LLM-chatbot-only projects**, about a 1.4× lift. Integration and depth beat plain LLM wrappers.
- Winners list more technologies (3.95 vs 3.26 on average) and write longer "how we built it" sections.
- Fact-check winners shared four things: one concrete user action, retrieval with citations and a confidence score, a live demo on a real claim, and a multi-step pipeline. That maps directly onto PS1's claim checker.

### 4.2 Five independent reviewers (subagents on Opus, Sonnet and Haiku)

| Reviewer | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Hackathon judge panel (Opus) | Electoral | Event | Safety | Deepfake | Learning | Health |
| Crowding + dataset analyst (Sonnet) | Electoral | Deepfake | Event | Safety | Learning | Health |
| 24h build-feasibility CTO (Opus) | Electoral | Safety | Event | Learning | Health | Deepfake |
| Current-events researcher (Sonnet, web) | Electoral | Deepfake | Event | Safety | Health | Learning |
| Devil's advocate (Haiku) | Event | Electoral | Health | Deepfake | Safety | Learning |

**Rank-sum** (lower is better): Electoral 6 · Event 12 · Safety 18 · Deepfake 18 · Learning 26 · Health 26.

**Key reviewer numbers:**
- **Judge ceilings** (best realistic 24h build, out of 50): Electoral 42, Event 41, Safety 37, Deepfake 36, Learning 35, Health 33.
- **Build risk** (1–10, lower is safer): Electoral 2, Learning 3, Health 3, Event 4, Safety 5, Deepfake 8.
- **Demo controllability** (1–10): Electoral 9, Learning 8, Health 8, Event 7, Safety 6, Deepfake 2.
- **Predicted teams per statement** (of ~42): Health ~11, Learning ~10, Safety ~9, Event ~6, Electoral ~3, Deepfake ~3. Deepfake has a 35–40% chance of not running.

**Feasibility notes from the CTO reviewer:**
- PS1 needs no external approvals and can run fully offline.
- PS2: WhatsApp Cloud API test numbers only reach pre-verified recipients and need templates. Instagram DM needs Meta app review, which isn't feasible in 24h. **Telegram is the only easy channel.**
- PS4: browser geolocation is unreliable indoors. Replay a synthetic GPS track. SMS in India hits DLT registration, so treat SMS as a designed fallback.
- PS3: GPUs needed. Off-the-shelf detectors generalise poorly.

### 4.3 Facts verified on the web this session
- **SIR Phase 3** (Special Intensive Revision of electoral rolls) covers 16 states + 3 UTs, **including Delhi**, Haryana, Punjab, Maharashtra and Karnataka.
  - Delhi's draft roll left out **about 47.6 lakh of 1.45 crore electors (around 32.8%)**.
  - Phase 3 deletions total **about 6 crore**, roughly 17% of 36 crore.
  - A claims/objections window followed. Final Delhi roll status was unconfirmed as of the search.
  - Sources: [The Wire](https://thewire.in/rights/delhi-sir-who-are-the-47-56-lakh-people-knocked-out-from-the-draft-roll) · [Deccan Herald](https://deccanherald.com/india/576-lakh-voters-added-post-ls-polls-615-crore-deleted-in-two-months-in-sir-phase-3-4136717) · [CivilsDaily](https://www.civilsdaily.com/news/sir-draft-rolls-see-over-13-cr-deletions-so-far-delhi-leads-with-33-left-out/)
  - The topic is **politically hot** (opposition parties publicly allege targeted deletions). Strict neutrality is essential.
- **Aarogya Setu 2.0** launched 29 Jun 2026 with OCR/AI "Smart Reports" that read lab reports. That undercuts PS6's report-simplifier novelty. Sources: [PIB doc](https://static.pib.gov.in/WriteReadData/specificdocs/documents/2026/jul/doc202676912801.pdf) · [Deccan Herald](https://www.deccanherald.com/technology/artificial-intelligence/aarogya-setu-20-indias-health-app-gets-googles-gen-ai-booster-dose-4057497)
- **Other context, not independently verified by me:**
  - The IT Rules amendment on synthetic media labelling was notified Feb 2026.
  - Deepfake-Eval-2024 found open-source detectors lose ~45–50% AUC in the wild.

### 4.4 Overall-prize Monte Carlo ([`analysis/sim.py`](analysis/sim.py), `sim2.py`, `sim3.py`)
- **Setup:** 20,000 runs. Our team against 41 rivals spread by predicted crowding.
- **Inputs:** judge ceilings, execution noise scaled by build risk, demo-failure chance from controllability, Deepfake cancellation (37%), a political-discomfort penalty for Electoral, and an emotional bonus for Safety.
- The numbers are **relative scores, not real odds**.

| Scenario | Electoral | Event | Safety | Learning | Deepfake | Health |
|---|---|---|---|---|---|---|
| Strong team (base) | **63** | 51 | 26 | 7 | 4.5 | 1.6 |
| Good, not elite | **27** | 18 | 6.5 | 0.6 | 0.3 | 0.1 |
| Judges wary of politics | **54** | 52 | 28 | 7 | 5 | 2 |
| Big emotional bonus for Safety | **54** | 41 | 41 | 3.5 | 2.4 | 0.6 |
| Judge ceilings very uncertain | **47** | 38 | 22 | 9 | 4.6 | 4 |
| Elite + over-scoped build | **98** | 92 | 75 | 56 | 26 | 25 |
| Electoral crowded (9 teams) | **52** | 40 | 17 | 3 | 2 | 0.6 |
| Crowded + politics penalty | **46** | 43 | 19 | 4 | 2.6 | 0.9 |

**Electoral is #1 in every scenario.** Its edge comes from the highest ceiling plus the most controllable build and demo, not only from low crowding. That matters because awards are overall.

### 4.5 Final ranking (once and final)
1. **Electoral Roll Transparency** (chosen)
2. Event Reach & Registration
3. Women's Safety
4. Gamified Learning
5. Deepfake Arena
6. Smarter Healthcare

### 4.6 Corrections the reviewers forced (already applied to the docs)
- PS1 and PS3 don't require the 1-slide plan. PS2, 4, 5 and 6 do.
- **Circular-metric trap:** accuracy on anomalies we planted ourselves looks circular. Fix: the partner plants anomalies **blind**, plus **benign look-alikes** (for example a hostel moving out), and we show they're labelled "likely benign".
- The old hook "65 lakh names" was stale (Bihar 2025) and leaned political. Use a neutral hook: *"Crores of names changed in this year's roll revision. Can you check yours, and understand why, in 10 seconds?"*
- The Deepfake "real photo + false caption" idea was removed, because it breaks the synthetic-personas-only rule.
- **Don't build 4 shallow modules.** Make anomaly detection + explanations rock-solid first, then the claim checker, then the bot.

---

## 5. What RollWatch is (short version; full spec in ROLLWATCH_PLAN.md)

**Tier A, the required modules built deep** (done by H12–14):
1. **Anomaly engine:**
   - Roll v1→v2 diff.
   - Booth deletion spikes via a binomial test against the age-adjusted expected rate, with Benjamini-Hochberg FDR correction.
   - Cross-script duplicates (Devanagari ↔ Latin): transliteration + phonetic + multilingual embeddings + clustering.
   - Rule checks: impossible ages, parent younger than child, oversized households, gender-ratio swings.
   - IsolationForest on booth features.
   - Calibrated confidence and reason codes.
2. **Flag cards:**
   - The LLM sees only computed JSON and returns found / why unusual / innocent explanations / confidence / needs human review.
   - Innocent explanations are ranked using synthetic context tables (death register, hostel list, boundary changes).
3. **Citizen bot:**
   - Telegram + web, Hindi/English/**Punjabi** (Delhi's official languages are Hindi, English, Punjabi and Urdu).
   - Voice in and out.
   - Typo- and script-tolerant name search, status + next steps, change alerts.
4. **Claim Court:**
   - Text, screenshot or voice claim → sub-claims → real pandas queries → Verified / Disputed / Unprovable, with evidence chart + confidence.

**Tier B, extras no one else will have:**
- **Neutrality Guard:** blocks "fraud" and party/person/institution names. Demo it live.
- **Mirror test:** each claim is also run in its opposite-side version, with identical treatment.
- **Blind eval panel:** precision/recall, false-positive rate on benign cases, calibration plot.
- **PDF roll ingest:** synthetic Devanagari roll pages → OCR → rows.
- **Human review queue** with an audit trail.
- **One-click audit report PDF.**

**Tier C, resilience:** offline mode (precomputed flags, cached LLM responses, local Ollama fallback), phone hotspot, backup demo video, feature freeze at H17.

**Data:** a fictional district "Sampleabad" (~100 booths, ~50k voters). **Never put flags on real constituencies.**

**Stack:**
- **Backend:** Python + FastAPI. pandas, scikit-learn, rapidfuzz, indic-transliteration, sentence-transformers (multilingual MiniLM).
- **Web:** Next.js + Tailwind + shadcn.
- **Bot:** python-telegram-bot. Voice via Sarvam STT/TTS (or Whisper).
- **LLMs:** Claude / Gemini.

---

## 6. Team setup & tools (shareable summary)

- **Humans:**
  - **A, Rishabh ("Engine"):** generator, detection engine, API/LLM/Claim Court. Also delivers the pitch.
  - **B, partner ("Product"):** dashboard, bot, video, slides, demo script. **B also writes the blind anomaly-planting config, and A never reads it.**
- **Rishabh's relevant experience:**
  - Python FastAPI, scikit-learn (SVM, regression), PuLP
  - Claude & Gemini APIs, FastMCP
  - voice AI (Faster-Whisper, **Sarvam STT**, ElevenLabs, Edge-TTS, LiveKit)
  - Next.js 15/16 + React 19 + Tailwind v4 + TypeScript
  - WhatsApp Business Cloud API, n8n
  - Streamlit + Plotly (CivicGrid-AI)
- **AI tools available:** Claude Pro + Claude Code (primary), ChatGPT Plus / Codex, Gemini (Google AI Pro) + AI Studio, GitHub Copilot, **Ollama (local models), useful for the offline demo fallback**.
- **Cloud/deploy:** Vercel, Render, Google Cloud credits, GitHub Student Pack (Azure student credit, Heroku, MongoDB Atlas, etc.), ngrok/cloudflared for exposing local servers.
- **Video:** CapCut, Vrew (AI captions), ElevenLabs (AI voiceover), Canva Pro, Adobe, OBS.
- **Environment caution:** the machine's default Python is 3.14. Create a **Python 3.11/3.12 venv** for the ML libs (torch/sentence-transformers wheels can lag new Python versions). Node and Bun are installed.
- **Design note:** Rishabh dislikes generic "AI dark mode" looks and never uses the Inter or Space Grotesk fonts. Use Plus Jakarta Sans + JetBrains Mono. His personal brand palette is for personal portfolios only, so it's optional here. A civic, trustworthy look fits PS1.

---

## 7. Open items / TODO before or at H0

- [ ] **Verify claims/objections form numbers and process** on the official ECI / CEO Delhi site before the bot cites them (Form 6 = new registration, 7 = objection/deletion, 8 = correction/shift, per general knowledge; confirm).
- [ ] Create API keys (Claude and/or Gemini, Sarvam or Bhashini) and a **Telegram bot via BotFather**. Test each one.
- [ ] Install a Python 3.12 venv + Node 20, and pull an Ollama model (e.g., a small instruct model) for the offline fallback.
- [ ] Storyboard the content video. Start recording behind-the-scenes clips at H0.
- [ ] Bring a phone hotspot, power bank and extension board.
- [ ] At H0: write `CLAUDE.md` + `contracts/` (JSON schemas for roll row, flag, claim verdict, API), then start the 5 parallel sessions (kickoff prompts are in ROLLWATCH_PLAN.md §4b).
- [ ] Confirm the partner's strengths and adjust the A/B split if needed.

## 8. Things deliberately NOT in this repo
- Rishabh's private master profile and access inventory. **This repo is public**, and they contain personal data.
- Other teams' contact numbers from the team sheet.
- The organiser PDFs and the 27 MB reference CSV.

## 9. Rules to remember while building
- Never output "fraud", "rigged", or any party, person or institution name. Flags are **for human review**.
- Every output shows **reasoning + confidence**.
- Synthetic data only, and a fictional district.
- Commit often. Git history proves the work was done during the 24h. Both humans must be able to explain every module.
- Feature freeze at H17. After that, only reliability, the video and rehearsal.

---

<a id="session-2"></a>
# Session Log #2: Validation and Locked Scope (27 Oct 2026, event day)

> The clock had already started (under 3h in). PS1 is registered and locked, and the team expects PS1 to be crowded (6–10 teams). Six independent validators reviewed the plan against the official PDFs, the dataset and the web. **The scope in this section and in [PRD](PRD.md) / [TRD](TRD.md) / [ACTION_PLAN](ACTION_PLAN.md) replaces [ROLLWATCH_PLAN.md](ROLLWATCH_PLAN.md).**

## What changed and why
- **Scope cut by about 35%.** The old plan was about 68 human-hours against about 40 available.
  - **Cut:** OCR/PDF, torch/embeddings, Ollama, isotonic calibration, review learning, alerts, voice claims, maps and IsolationForest.
  - **Why:** the machine has no usable GPU, and Ollama and Tesseract aren't installed.
- **New centrepiece: "Which Story Fits?"** Each removal is attributed to an innocent story or "unexplained", and the residual is tested. This answers PS1's "what innocent explanations exist" with numbers, which no other PS1 team is likely to have.
- **New hero: forward → fact-check card.** A screenshot of a viral claim is split into sub-claims, run as fixed queries, and returned as a stamped share card in Telegram. The mirror claim gets identical treatment.
- **Judges' red team:** the old plan scored about 32.5/50. The losses were Feasibility (no "from Monday" story) and Presentation (a feature tour and jargon). The fixes are one persona (Meena, Booth 47), a 4:00 demo, an adoption slide, and the bot tried *after* the pitch.
- **Compliance fixes:**
  - "Verified" applies only to measurable sub-claims. Intent and motive words → "cannot be proven".
  - We never infer religion, caste or community.
  - Names are masked in auditor views.
  - Demo claims are only about Sampleabad.
  - The guard applies to generated text, and procedural templates are allowlisted.
  - The mirror flips direction, never the political side.

## Corrections to session #1 numbers
- **Dataset duplicates:** the reference dataset has 6,917 rows but only **5,278 unique projects**. The base win rate is 17.4%.
- **Shifted columns:** `tech_stack` is shifted in 55% of rows, so the old tech-count figures (3.95 vs 3.26) were wrong. The repaired figures are 7.40 vs 6.11 (winners ahead in 53 of 58 hackathons).
- **Election/voter:** 36.4% (12/33, 95% CI 22–53%). The lift comes mostly from events with matching prize tracks. In selective hackathons there was **no topic edge**, so choosing PS1 doesn't by itself win.
- **What correlates with winning,** controlling for the hackathon: agents ×2.3, vision/OCR ×1.8, write-up length ×1.65 per SD, a "N%" number in the text ×1.5, and +12% odds per extra AI component. Chatbot-only projects come in at 0.75×. Multilingual, voice and "explainable" wording give no lift by themselves.
- **Claimed-but-false statements:** "Commit history proves everything was built during the 24h" is false, because the planning docs and analysis scripts predate the event. Say "all product code was written during the event."

## Facts verified on the web (27 Oct)
- **SIR Phase 3:** announced 14 May 2026, covering 16 states + 3 UTs. Final rolls are due between 1 Oct and 23 Dec.
- **Delhi draft (31 Aug):**
  - 1,45,10,299 electors, of whom 47,56,722 were left out (32.78%).
  - Shifted/absent 29.86%, dead 1.95%, duplicate 0.98%.
  - Claims are open until 30 Oct and the final roll is due **4 Dec 2026** (PTI, 26 Sep). Recheck before the demo.
- **Totals:** Phase 3 removed 6.15 crore at the draft stage (17.1%). ECI says about 13 crore were *marked* but not deleted.
- **Deletion categories:** ECI uses ASDD (Absent, Shifted, Dead, Duplicate). Notices are a separate track (unmapped, or "logical discrepancy"). On 22 Sep the Supreme Court asked for "logical discrepancy" to be defined.
- **Forms:** 6 (new / re-inclusion), 6A (overseas), 7 (objection / deletion; since 9 Oct capped at 10 per elector and 5 per month), 8 (shift / correction / EPIC). Form 6B is not reconfirmed. Plus the SIR Enumeration Form.
- **Channels:** the ECINET app (launched 22 Jan 2026; it absorbed Voter Helpline), voters.eci.gov.in and the 1950 helpline. There are fake-BLO scam calls.
- **Sarvam:** STT saaras:v4 and TTS bulbul both support Punjabi. The free credit is ₹100.

## New doc map
[PRD](PRD.md) · [TRD](TRD.md) · [Action plan](ACTION_PLAN.md) · [Design system](DESIGN_SYSTEM.md) (+ `design/tokens.css`, `design/glyphs.svg`) · [Demo & pitch](DEMO_AND_PITCH.md) · [Content video](CONTENT_VIDEO.md) · root `CLAUDE.md`.

## Open
- The submission format, deadline and demo slot length (ask the organisers).
- Disclosing AI-tool use, and whether the partner commits under their own identity (see ACTION_PLAN §7).
