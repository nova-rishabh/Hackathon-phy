# X AI Tech Ideathon — Winning Strategy (Team Nova, IDEAS-175)

Event: 27–28 Oct 2026 · 24h · offline · ~42 registered teams (IDEAS-150 → 191)
Judging (equal weight assumed): Innovation · Technical Implementation (effective AI) · Problem-Solving · Feasibility & Impact · Presentation
Every problem also requires a working prototype, a live demo and a 45–90s AI-assisted content video.
A **1-slide 100→1,000 plan is required only for PS 2, 4, 5 and 6.** Electoral (PS1) and Deepfake (PS3) don't need it. Deepfake instead requires a 9:16 vertical video with AI parts labelled, plus a 5-minute pitch.

---

## 🏁 ONCE-AND-FINAL RANKING (one overall 1st prize, not per category)

With a single overall prize, crowding matters less. You aren't fighting for a category slot. You have to beat the single best project in the room. Crowding still hurts in one way: the 10th health chatbot looks generic, so it scores lower on Innovation.

What decides the winner is:
- the **ceiling** of the best possible 24h build
- how **reliably** you hit that ceiling
- **demo control**
- a few **judge biases**

I simulated this: 20,000 runs of 41 rival teams against us. Inputs:
- judge-reviewer ceilings: Electoral 42, Event 41, Safety 37, Deepfake 36, Learning 35, Health 33
- feasibility-reviewer build risk and demo control
- crowding-reviewer team counts
- 37% chance Deepfake is dropped
- a 25% chance that a judge discounts Electoral for politics
- an emotional bonus for Women's Safety

Script: [`analysis/sim.py`](analysis/sim.py).

| Scenario | Electoral | Event | Safety | Learning | Deepfake | Health |
|---|---|---|---|---|---|---|
| Strong team (base) | **63** | 51 | 26 | 7 | 4.5 | 1.6 |
| Good, not elite team | **27** | 18 | 6.5 | 0.6 | 0.3 | 0.1 |
| Judges very wary of politics | **54** | 52 | 28 | 7 | 5 | 2 |
| Big emotional bonus for Safety | **54** | 41 | 41 | 3.5 | 2.4 | 0.6 |
| Judge ceilings very uncertain | **47** | 38 | 22 | 9 | 4.6 | 4 |

The numbers are relative, not real odds. The absolute values depend on how good I assume the rivals are.

**Electoral is #1 in every scenario.** Event Reach is the only close challenger, and it only draws level if the judges are wary of politics.

**FINAL:**
1. Electoral Roll Transparency
2. Event Reach & Registration
3. Women's Safety
4. Gamified Learning
5. Deepfake Arena
6. Smarter Healthcare

Deepfake drops to 5th because it has the least demo control, it may be dropped, and the per-game scoreboard isn't the judging rubric.

The public web has nothing on this event (I searched the name, the tagline, the dates and the organiser), so the rulebook is the only source.

## ✅ VALIDATED RANKING (5 independent reviewers + my own checks)

Five reviewers each ranked all 6 statements without seeing my ranking. The only exception was the devil's advocate, which was given my ranking so it could attack it. The reviewers ran on three different models (Opus, Sonnet and Haiku), each with a different perspective.

| Reviewer (model) | 1st | 2nd | 3rd | 4th | 5th | 6th |
|---|---|---|---|---|---|---|
| Hackathon judge panel (Opus) | Electoral | Event | Safety | Deepfake | Learning | Health |
| Competition-crowding analyst (Sonnet + dataset) | Electoral | Deepfake | Event | Safety | Learning | Health |
| 24h build-feasibility CTO (Opus) | Electoral | Safety | Event | Learning | Health | Deepfake |
| Current-events researcher (Sonnet + web) | Electoral | Deepfake | Event | Safety | Health | Learning |
| Devil's advocate (Haiku, attacking my ranking) | Event | Electoral | Health | Deepfake | Safety | Learning |
| My original ranking | Electoral | Event | Safety | Deepfake | Learning | Health |

**Rank-sum across the 5 independent reviewers (lower = better):**
- Electoral **6**
- Event Reach **12**
- Women's Safety 18
- Deepfake 18
- Gamified Learning 26
- Healthcare 26

### FINAL RANKING

1. **Electoral Roll Transparency**
   - 4 of 5 reviewers put it #1, and the 5th put it #2.
   - **Lowest build risk** (2/10, since there are no external APIs or approvals) and **highest demo control** (9/10).
   - Judge score 42/50.
   - Likely ~3 competing teams.
   - Its real ML (anomaly scoring, entity resolution) is what the dataset rewards: real-ML projects won 22.9% vs 16.5% for LLM-chat-only.
   - **Verified this session:** Delhi is in SIR Phase 3. Its draft roll left out about 47.6 lakh of 1.45 crore electors (around 32.8%). Phase 3 deletions total about 6 crore. So the problem is live news in the judges' own city.
2. **Event Reach & Registration**
   - Judge score 41/50, one point behind Electoral.
   - Best participatory demo, and the judges know this pain first-hand.
   - No political risk.
   - Telegram is the only channel you can build in 24h. WhatsApp and Instagram need Meta approval.
   - Weakness: AI depth is thin, and "audience discovery" without real data risks breaking the honesty rule.
3. **Women's Safety**
   - Biggest emotional pull, but about 9 teams are expected.
   - Winners in this space use a discreet or novel trigger, not a plain SOS button.
   - The privacy rules are strict.
4. **Deepfake Arena**
   - Biggest spectacle.
   - Roughly 35–40% chance it is dropped, which forces a mid-event switch.
   - Your score depends on other teams' fakes.
   - The research shows open-source detectors lose about 45–50% accuracy on in-the-wild fakes.
5. **Gamified Learning**
   - About 10 teams expected.
   - Dataset win rate is below baseline (15%).
   - The statement has six modules, which pushes teams toward broad, shallow builds.
6. **Healthcare**
   - Most crowded, at about 11 teams.
   - **Verified:** the government's Aarogya Setu 2.0 (launched 29 Jun 2026) already reads lab reports with AI ("Smart Reports"), which kills the novelty of a report simplifier.

**Condition on #1:** pick Electoral only if at least one teammate is solid in Python/pandas. A team without one should pick **Event Reach**, which is the devil's-advocate view. If more than 6 teams pick Electoral on release night, switch to Event Reach too.

### Corrections to my first draft (found by the reviewers)
- **Wrong:** I said "most problems need a 1-slide plan". Electoral and Deepfake don't, which is a small extra edge for Electoral.
- **Removed:** the "real photo + false caption" cheapfake idea. It risks breaking the "synthetic personas only" rule.
- **Stale hook:** "65 lakh names" was Bihar 2025. Use a neutral current hook instead (see the build section).
- **Circular-metrics trap:** precision/recall on anomalies you planted yourself looks circular. Fix it like this:
  - One teammate plants the anomalies blind.
  - Also plant innocent look-alikes, such as a whole hostel shifting out.
  - Show that the system labels those "likely benign".
- **Pre-existing work rule:** write no code before the 27th. Ideas and notes are fine.
- **Scope:** don't try to build all 4 modules shallowly. Build anomaly detection + explanations rock-solid first, then the claim checker, then the bot.

---

## How I judged "winnable"

The score for each category comes from 5 factors:

1. **Crowding.** How many of the ~42 teams will pick it. Fewer competitors means fewer good teams to beat.
2. **Wrapper risk.** Can judges dismiss it as "ChatGPT with a UI"? You score high on Technical Implementation only with real ML plus an LLM.
3. **Demo control.** Can you script a demo on synthetic data that never fails on stage?
4. **Wow and relevance.** Is there a current, emotional hook that the judges already feel?
5. **Scope fit.** Can 3–5 people build the full required journey in 24h?

### What the reference dataset says (6,917 Devpost projects, base win rate 17.3%)
*Directional only. Different events, judges and rules.*

| Theme | Projects | Win rate |
|---|---|---|
| Election / voter | 45 | **40.0%** |
| Deepfake | 12 | **41.7%** |
| Misinformation / fact-check | 65 | **35.4%** |
| Anomaly detection | 16 | 31.2% |
| Wearable | 76 | 44.7% |
| Healthcare | 1,257 | 21.3% |
| Education (any) | 2,577 | 17.7% |
| Gamified learning | 148 | 14.9% |
| Women / personal safety | 31 | 16.1% |
| Multilingual / Hindi | 216 | 23.1% |
| Stack: FastAPI / OpenCV / Next.js | — | 31% / 34% / 27% |
| Stack: plain React / Flutter | — | 17% / 16% |

Two patterns stand out:
- Rare, civic, trust-and-safety themes win about twice as often as crowded consumer themes like health and education.
- Projects with real CV/ML in the backend beat projects that are only a frontend.

---

## 1–2. Category ranking (most → least winnable)

| Rank | Category | Expected teams* | Why |
|---|---|---|---|
| **#1** | **1. Electoral Roll Transparency** | 3–5 | Least crowded. It is the hardest category to dismiss as a wrapper, because anomaly detection is real ML. Synthetic data means the demo is 100% under your control. The hook is very current (SIR revisions, "names deleted" allegations). The PS says "best teams will combine more modules", so it rewards exactly the ambitious team. |
| **#2** | **2. Event Reach & Registration** | 4–6 | **The judges and organisers are student event organisers, so they live this pain.** The live demo can involve the judges: they scan a QR code, register in Telegram in 20s, and watch the counter go up. Risk: easy to build a shallow version, so depth must come from the audience-discovery AI and the growth loop. |
| **#3** | **4. Girls' & Women's Safety** | 8–10 | Most emotional and relatable, and judges love it. But it is crowded, and most teams will build "SOS button + share location". Winnable only with a sharp differentiator (see S1). |
| **#4** | **3. Deepfake Arena** | 0–4 | Highest ceiling, because the live scoreboard is pure theatre. But a lot sits outside your control: it is cancelled if fewer than 2 teams pick it, other teams' fakes decide your detector score, and detecting state-of-the-art fakes is genuinely hard in 24h. Pick it only if you have strong CV/audio ML people. |
| **#5** | **5. Gamified Learning** | 9–11 | Crowded. The scope is huge (6 modules plus a full journey). Judges will have seen "quiz + XP + chatbot" many times. |
| **#6** | **6. Smarter Healthcare** | 10–12 | Most crowded. It is the easiest category to build, so every team builds the same "symptom chatbot + report explainer". Heavy wrapper risk, and medical-safety rules limit how bold you can be. |

*My guess from typical Indian college ideathon behaviour: familiar, easy themes attract most teams.*

> **Verdict:** Go for **Problem 1 — Electoral Roll Transparency**. Keep **Problem 2 — Event Reach** as the backup if your team is weak on data/ML but strong on bots and product.

---

## 3–6. Three ideas per category, ranked within each

### #1 · Electoral Roll Transparency
1. **🥇 RollWatch: an all-in-one roll auditor**
   - **Data:** a synthetic roll generator with planted anomalies, plus a two-version diff engine.
   - **Detection:** Isolation Forest and z-score flags booth-level deletion spikes, impossible ages, and 40+ voters at one address. Fuzzy and transliteration-aware duplicate matching works across Hindi and English names.
   - **Explanation:** an LLM writes a "flag card" for each flag: what was found, why it is unusual, innocent explanations (death, migration, delimitation), and a confidence %. A booth heatmap shows where flags cluster.
   - **Bolt-ons:** idea 2's Claim Court and idea 3's citizen bot. That covers all 4 modules.
2. **🥈 Claim Court: viral claim checker**
   - **Input:** paste a WhatsApp forward, screenshot (OCR) or voice note.
   - **How it works:** the LLM extracts the measurable claim, converts it to a query over roll data, and returns ✅ Verified / ⚠️ Disputed / ❓ Unprovable, with the evidence chart and reasoning.
   - **Demo:** two opposing-side claims run through the same pipeline. This proves neutrality.
3. **🥉 Mera Naam Bot: citizen assistant**
   - **Channel:** a Telegram/WhatsApp text and voice bot in Hindi, English and Bhojpuri (or Tamil).
   - **Features:** typo- and transliteration-tolerant name search, explanation of your status, Form 6/7/8 next steps, and an alert if your entry changes between roll versions.

### #2 · Event Reach & Registration
1. **🥇 First100: an AI growth agent for zero-follower organisers**
   - **Setup:** the organiser types one sentence about the event. AI scores communities (colleges, clubs, Discord, Telegram) from a seeded directory and drafts a personalised DM for each, which a human approves.
   - **Registration:** happens fully inside a Telegram bot (EN/HI plus one regional language).
   - **Growth loop:** the bot auto-generates a team card image with an "invite 2 teammates" referral link. A live K-factor dashboard tracks it.
   - **Drop-off:** a no-show risk model sends nudges.
   - **Demo:** judges register live.
2. **🥈 Ambassador Loop**
   - **How it works:** every registrant becomes a campus ambassador with an AI-made personalised poster or reel and a referral leaderboard.
   - **Why it matters:** this answers the 100 → 1,000 slide directly.
3. **🥉 TeamForge**
   - **Matching:** solo participants are matched into balanced teams using skill vectors and complementary roles.
   - **In chat:** the bot auto-creates the group chat and runs a "complete your team" nudge flow.

### #3 · Girls' & Women's Safety
1. **🥇 Silent Guardian: journey mode with a duress PIN**
   - **Risk engine:** flags route deviation from the planned polyline, unexpected stops, speed anomalies, and time and area context.
   - **Check-in:** a soft "Are you okay?" prompt. Entering the **duress PIN** looks like a cancel on screen but silently fires the SOS. That directly answers "can't safely trigger SOS".
   - **Escalation:** an expiring live-location link, then contact 1 → contact 2 → campus security, with acknowledgements.
   - **Fallback:** offline SMS.
2. **🥈 Codeword SOS**
   - **Triggers:** an on-device Hindi or regional voice codeword ("Didi, khana bana diya?"), a power-button pattern, or a fake incoming call screen.
   - **Audio:** distress and scream detection with a 10s cancel window to limit false alarms.
3. **🥉 Campus Safe-Walk Network**
   - **Responders:** verified volunteers and guards, dispatched by nearest available responder.
   - **Privacy:** location is visible only during an active alert and expires automatically.

### #4 · Deepfake Arena (you must build both Red and Blue)
1. **🥇 Forensic Detective ensemble (Blue)**
   - **Image:** ELA, FFT artefacts, metadata/C2PA checks and a pretrained detector.
   - **Audio:** spectral anti-spoof features.
   - **Video:** lip-sync and blink checks.
   - **Text:** stylometry against the persona's real corpus.
   - **Output:** a vision-LLM writes the human reason, and a heatmap shows what triggered suspicion.
   - **Strategy:** a false alarm costs −5 but a miss costs only −3, so tune the threshold for that asymmetry.
2. **🥈 Persona-consistent Forger (Red)**
   - **Focus:** subtle, in-character fakes that match each persona's real style. Use small inpainted edits, audio and text, all built only from the provided synthetic personas. Detectors are weakest on these.
   - **Points:** each team fooled is worth +10.
3. **🥉 Post-game Intelligence Report**
   - **Content:** an auto-generated analysis of which fakes slipped past, why, and the detector fixes needed. The PS requires it, and it is an easy deliverable to win on polish.

### #5 · Gamified Learning
1. **🥇 Bug Dungeon: code concepts → boss fights**
   - **Setup:** upload a chapter. AI builds a skill graph and a diagnostic test.
   - **Gameplay:** each level is working code where the AI planted concept-specific bugs. A Socratic hint mentor (Hindi/English) helps, and a skill-proof portfolio scores the process (attempts, hints used), not just answers.
2. **🥈 Teach-the-Bot (Feynman mode)**
   - **How it works:** the student teaches a deliberately confused AI student, and the AI grades depth of understanding.
   - **Social:** a team tournament mode.
3. **🥉 Startup Simulator**
   - **How it works:** AI-NPC customers and investors react to the business decisions students make.

### #6 · Smarter Healthcare
1. **🥇 Report Saathi**
   - **Input:** a photo of a lab report goes through OCR and structured extraction.
   - **Output:** colour-coded values against reference ranges, a Hindi or regional voice explanation, trends across past reports, a critical-value "go to hospital now" triage, and a list of questions to ask your doctor.
2. **🥈 Voice-first WhatsApp Triage**
   - **Audience:** low-literacy users.
   - **Logic:** protocol-based red-flag rules plus an LLM explanation, with emergency escalation and the nearest PHC.
3. **🥉 Prescription → Adherence**
   - **Features:** photograph a prescription to get a schedule, reminders, interaction warnings and a caregiver loop.

---

## Top 10 projects overall (ranked by chance of 1st prize)

| # | Project | Category | Why it can win |
|---|---|---|---|
| 1 | **RollWatch (all 4 modules)** | Electoral | Real ML plus explainable AI plus multilingual bot in an uncrowded, high-impact category |
| 2 | **First100** | Event Reach | Judges personally feel the pain, and they take part in the live demo |
| 3 | **Silent Guardian (duress PIN)** | Women's Safety | One memorable trick that beats the crowd of SOS buttons |
| 4 | **Claim Court** (standalone) | Electoral | The misinformation angle has a high win rate, and the demo is strong |
| 5 | **Forensic Detective + Forger** | Deepfake | Biggest stage moment, if the category survives |
| 6 | **Codeword SOS** | Women's Safety | Voice codeword in a regional language works as a live demo |
| 7 | **Bug Dungeon** | Learning | Only a learning idea with a real simulator stands out |
| 8 | **Ambassador Loop** | Event Reach | Strong growth story, but a weaker AI core |
| 9 | **Report Saathi** | Healthcare | Best health idea, but it will have many near-copies |
| 10 | **Mera Naam Bot** (standalone) | Electoral | Solid, but just a bot without the anomaly engine |

---

## If we pick RollWatch: winning shape for 24h

- **Data (hour 0–3):** a Python generator for 2 synthetic roll versions (~50k voters, ~100 booths), with *planted* anomalies and the ground truth kept aside. Show precision and recall of the detector on stage. Judges rarely see measured accuracy.
- **Engine (3–12):** FastAPI with pandas, scikit-learn IsolationForest, rapidfuzz plus indic-transliteration for duplicates, and rule checks for age and household size. Every flag gets a reason code and a confidence score.
- **LLM layer (8–16):** flag cards (what / why unusual / innocent explanations / confidence), Claim Court (claim → structured query → 3-way verdict), and a citizen bot (Telegram, EN/HI plus one regional language, voice via Whisper or a speech API).
- **UI (10–20):** a Next.js dashboard with a booth heatmap, a version-diff timeline, a flag queue with "send to human reviewer", and a neutrality badge on every output.
- **Pitch and video (owned by 1 person from hour 0):**
  - **Hook (first 5s):** keep it neutral: "Crores of names changed in this year's roll revision. Can you check yours, and understand why, in 10 seconds?" Never imply who is to blame.
  - **Footage:** behind-the-scenes clips, an AI voiceover, auto-captions and an "AI-assisted" label.
- **Guardrails that score points:** the system never says "fraud", never names a party or person, treats both sides' claims the same way, and reasons plus confidence are always visible. The rules require this, so show it on purpose.
