# RollWatch: the overboard plan (PS1, AI for Electoral Roll Transparency)

> Goal: be the obvious #1 in the room, not just the best electoral project. We ship **all 4 required modules** plus **6 extras that no other team will have**, and we make every rule in the problem statement visible on screen.
>
> Honest note: nothing can guarantee a win, because judging is human. This plan removes every controllable reason to lose.

---

## 0. One-line pitch
**"RollWatch turns a 50,000-row voter roll into answers anyone can trust: what changed, why it might have changed, and how sure we are. It works in Hindi, English and Punjabi, and it never takes a side."**

Why Punjabi: Delhi's official languages are Hindi, English, Punjabi and Urdu. Punjab and Haryana are also in SIR Phase 3, so Punjabi is locally relevant. Urdu is a valid alternative.

---

## 1. Architecture

```
┌──────────────── DATA ────────────────┐   ┌──────────── INTELLIGENCE ─────────────┐   ┌────────── SURFACES ──────────┐
│ Synthetic Roll Generator (v1 → v2)   │   │ Diff engine (add/delete/modify)       │   │ Auditor dashboard (Next.js)  │
│  • fictional district "Sampleabad"   │──▶│ Booth stats: binomial test vs         │──▶│  • booth heatmap + timeline  │
│  • Devanagari + Latin names          │   │   demographic-expected deletions,     │   │  • flag queue + review       │
│  • realistic churn (deaths, moves,   │   │   Benjamini-Hochberg FDR correction   │   │  • eval / calibration panel  │
│    new 18-yr-olds)                   │   │ Entity resolution (duplicates):       │   │ Citizen bot (Telegram + web) │
│  • BLIND planted anomalies           │   │   blocking → transliteration →        │   │  • HI / EN / PA, voice in/out│
│  • BENIGN look-alikes                │   │   phonetic → multilingual embeddings  │   │ Claim Court (text/img/voice) │
│ PDF roll renderer + OCR ingest       │   │   → pairwise classifier → clusters    │   │ Audit report PDF export      │
│ Context tables (synthetic death reg.,│   │ Rule checks (age, relations, house-   │   └──────────────────────────────┘
│  hostel list, boundary change log)   │   │   hold size, gender ratio)            │
└──────────────────────────────────────┘   │ IsolationForest on booth features     │
                                           │ Benign-explanation matcher (context)  │
                                           │ Confidence calibration (isotonic)     │
                                           │ LLM: grounded flag cards (JSON-only)  │
                                           │ Neutrality Guard (blocks bias words)  │
                                           │ Claim agent: claim→sub-claims→pandas  │
                                           └───────────────────────────────────────┘
```

**Stack:**
- **Backend:** Python + FastAPI. Data work with pandas, scikit-learn, rapidfuzz, indic-transliteration and sentence-transformers (multilingual MiniLM).
- **Frontend:** Next.js + Tailwind + shadcn. Charts with Recharts, maps with deck.gl or Leaflet.
- **Citizen bot:** python-telegram-bot. Voice via Sarvam (STT/TTS) or Whisper.
- **LLMs:** Claude or Gemini for the main features. A local Ollama fallback for the offline demo.

---

## 2. Feature list (tiered)

### Tier A: required modules, built deep (must ship by hour 14)

1. **Anomaly detection**
   - **Version diff:** compares roll v1 and v2. Each booth's deletion rate is tested against its *expected* rate given its age mix (binomial test), with a false-discovery correction (Benjamini-Hochberg) so we don't cry wolf across 100 booths.
   - **Duplicates:** entity resolution that catches "सुनीता शर्मा / Suneeta Sarma / Sunita Sharma, same father, same house". It uses transliteration, phonetic matching and embeddings, then groups matches into clusters.
   - **Impossible records:** ages over 110 or under 18, a parent younger than their child, 60+ voters at one address, sudden gender-ratio swings.
   - **Booth-level outliers:** IsolationForest over booth features.
2. **Plain-language flag cards.** For every flag:
   - **What we found.**
   - **Why it's unusual,** with the number and the expected baseline.
   - **Innocent explanations,** ranked by likelihood using context tables: deaths, hostel move-outs, boundary changes.
   - **Confidence %** and **"Needs human review"**.
   - **Grounding:** the LLM only receives computed JSON, never raw data, so it can't invent numbers.
3. **Citizen assistant** (Telegram + web, HI/EN/PA, voice notes in and out)
   - Finds your entry even with typos or the wrong script.
   - Explains your status: present, modified or not in draft, plus the reason category.
   - Gives step-by-step next actions: the claims/objections window and which form to use. **Verify form numbers against the ECI site before the demo.**
   - Lets you subscribe to alerts if your entry changes in the next version.
4. **Claim Court: claim checker**
   - **Input:** text, a WhatsApp screenshot (vision OCR) or a Hindi voice note.
   - **How it works:** an agent splits the claim into checkable sub-claims and runs real pandas queries.
   - **Verdict:** ✅ Verified / ⚠️ Disputed / ❓ Cannot be proven from public data, with an evidence chart, confidence and "what data would settle this".

### Tier B: overboard extras (hours 14–19)

5. **Neutrality Guard:** a post-filter on every LLM output. It blocks "fraud", "rigged", party names, person names and institution names, then rewrites in neutral language. **Demo it live:** force a biased prompt and show the guard catching it.
6. **Mirror-test for claims:** every claim is also run as its politically mirrored version, and we show both got identical treatment. This proves "treat claims from all sides equally" instead of just asserting it.
7. **Blind evaluation panel:**
   - **Blind planting:** the video owner plants anomalies the detector team never saw, plus benign look-alikes.
   - **On screen:** precision, recall, false-positive rate on benign cases, and a calibration plot (a "70% confident" flag is right about 70% of the time).
   - **Why it matters:** this answers the "circular metric" attack, and no other team will have it.
8. **PDF roll ingest:** real rolls are published as Devanagari image PDFs. We render synthetic roll pages in that style and OCR them back into rows on stage. That shows the pipeline would work on the real format.
9. **Human-review queue + feedback loop:**
   - A reviewer marks each flag "benign" or "escalate".
   - Thresholds and innocent-explanation priors update.
   - Everything is logged in an audit trail with a hash for every flag.
10. **Audit report export:** a one-click PDF for journalists and observers with methodology, every flag, its reasoning and confidence, limitations and a model card.

### Tier C: resilience (hours 19–21)
- **Offline demo mode:**
  - Precomputed flags.
  - Cached LLM responses for the scripted path.
  - A local Ollama model for anything new.
  - A phone hotspot.
- **Backup demo video** of the full journey, recorded at hour 20.
- **Limitations page:**
  - "Synthetic data. Flags are not findings."
  - "Not affiliated with ECI."
  - "Not a replacement for official verification."

---

## 3. Team: 2 humans + Claude Code

With Claude Code writing most of the code, the bottleneck moves away from typing. It is now:
1. clear specs
2. merge conflicts between parallel sessions
3. **humans checking that the output is actually right**
4. demo polish, the video and the pitch

So each human acts as a **tech lead running 2–3 Claude Code sessions in parallel**, each in its own git worktree, on separate folders.

| Human | Owns (drives Claude Code sessions for) | Also owns |
|---|---|---|
| **A: Rishabh, "Engine"** | S1 generator + blind eval · S2 detection engine · S3 API + LLM + Claim Court + Neutrality Guard | Pitch delivery. Must be able to explain every algorithm on stage. |
| **B: Partner, "Product"** | S4 dashboard frontend · S5 Telegram bot + voice + PDF ingest | Content video (records behind-the-scenes clips all day), slides, demo script |

**Blind planting with 2 people:**
- Partner B writes the anomaly-planting config: which booths, what type, how many, plus benign look-alikes.
- B gives that config to a Claude session that A never reads.
- A's detector never sees the answer key until the evaluation runs.
- That keeps the evaluation honestly blind.

**Rulebook safety:**
- AI-assisted coding is not banned. The rules ban plagiarism and pre-existing work.
- Commit often, so the git history proves everything was built during the 24h.
- Both humans must be able to explain any part of the code when asked. Spend 10 minutes per module reading what Claude wrote.

---

## 4. 24-hour timeline (2 humans, 5 parallel sessions)

| Hour | A (Engine) | B (Product) |
|---|---|---|
| H0–1 | **Together:** repo, `CLAUDE.md`, `contracts/` (JSON schemas for roll row, flag, claim verdict, API endpoints). This is the single most important hour, because it lets the sessions run in parallel without collisions. | Same, plus first behind-the-scenes clip |
| H1–4 | S1: generator v1 (two roll versions, churn). S2: diff + rule checks. | S4: dashboard skeleton on mock JSON from the contracts. S5: bot replies in HI/EN/PA. B writes the blind planting config. |
| H4–8 | S2: booth stats + FDR, duplicate entity resolution. S3: flag cards + Neutrality Guard. | S4: flag cards UI + heatmap. S5: fuzzy name search + status explainer. |
| H8–12 | S2: IsolationForest + benign matcher + calibration. S3: Claim Court (text then screenshot). | S4: claim UI + review queue. S5: voice in/out. Video: rough cut v0. |
| H12–13 | **CHECKPOINT:** swap the frontend from mock JSON to the live API. Run the blind eval. All 4 modules must work end to end. | Same |
| H13–17 | S3: mirror test, audit report PDF. S2: fix the worst eval errors. | S4: eval/calibration panel, polish. S5: PDF ingest, change alerts. |
| H17 | **FEATURE FREEZE** | |
| H17–20 | Offline mode, LLM response cache, local Ollama fallback, bug bash | Record backup demo video. Content video final edit. Slides. |
| H20–23 | Rehearse the 4-minute demo ×5 with a timer. Q&A drill (A answers tech, B answers impact and design). | Same |
| H23–24 | Buffer + submit | |

**Cut list if behind (cut from the top):**
1. PDF ingest
2. Review-queue learning (keep the queue, drop the learning)
3. Audit PDF export
4. Punjabi *voice* (keep Punjabi text)
5. Screenshot/voice claims (keep text)

**Never cut:** the 4 modules, flag cards with confidence, the Neutrality Guard, the blind eval, the offline demo mode.

---

## 4b. Claude Code playbook

- **One worktree per session:** `git worktree add ../rw-engine -b engine`, and likewise for `generator`, `api`, `web` and `bot`. Each session touches only its own folder: `generator/`, `engine/`, `api/`, `web/`, `bot/`. Merge into `main` every 2–3 hours.
- **`CLAUDE.md` at the repo root** (written at H0) holds:
  - the product in 5 lines
  - the folder ownership map
  - "contracts/ are the source of truth; never change them without telling the other human"
  - neutrality rules (never output "fraud" or party, person or institution names)
  - "every flag has reasoning + confidence"
  - run and test commands
- **Ask for tests with every module.** Have Claude write pytest checks for the engine, such as "planted duplicate across scripts is found" and "benign hostel move-out is labelled benign". This catches regressions when sessions merge.
- **Plan first for big pieces.** For S2 and S3, ask Claude to plan before writing code, and review the plan in 2 minutes. It's cheaper than undoing a wrong design.
- **Keep demo data frozen.** After H17, fix the random seed and the dataset. The demo must give the same result every run.

### Kickoff prompts to paste at H0+1 (adapt freely)

- **S1, generator:** "Build `generator/`: a synthetic electoral-roll generator for a fictional district 'Sampleabad' (~100 booths, ~50k voters). It produces roll_v1 and roll_v2 following contracts/roll_row.schema.json. Use Devanagari + Latin names, relation names, households and realistic churn (age-based mortality, migration, new 18-year-olds). Read anomaly and benign-look-alike injections ONLY from planting_config.yaml and write the answer key to eval/answer_key.json. The answer key must not be imported anywhere in engine/. Add tests."
- **S2, engine:** "Build `engine/`: given roll_v1/v2, output flags per contracts/flag.schema.json. Detect booth deletion spikes (binomial test vs age-adjusted expected rate, Benjamini-Hochberg FDR), cross-script duplicates (indic transliteration + phonetic + multilingual embeddings + clustering), rule violations (impossible ages, relation-age conflicts, oversized households, gender-ratio swings), and booth outliers (IsolationForest). Attach reason codes, ranked benign explanations from context tables, and isotonic-calibrated confidence. Add pytest. Plan first."
- **S3, API + LLM:** "Build `api/` (FastAPI) per contracts/api.md. Flag cards: the LLM receives only the flag JSON and returns {found, why_unusual, innocent_explanations[], confidence, needs_human_review:true}. Neutrality Guard: post-filter that blocks fraud/rigging language and any party/person/institution names, then rewrites neutrally. Log every block. Claim Court: claim → sub-claims → pandas queries on the roll → verdict Verified/Disputed/Unprovable + evidence + confidence; also run the mirrored claim and return both. Cache all LLM responses to disk."
- **S4, web:** "Build `web/` (Next.js + Tailwind + shadcn). Pages: Overview (booth heatmap, v1→v2 timeline), Flags (filterable queue, flag card modal, review buttons), Claim Court, Evaluation (precision/recall, FP on benign, calibration plot), Citizen (web chat). Use mock JSON from contracts/ until H12. Clean, trustworthy civic design, with a 'Synthetic data · flags are not findings' banner."
- **S5, bot:** "Build `bot/` (python-telegram-bot). Hindi/English/Punjabi, auto-detected. Voice notes in/out via Sarvam (or Whisper + TTS fallback). Typo- and script-tolerant name search via the API, status explanation, next steps for claims/objections, and subscribe-to-change alerts. Every answer shows confidence and a 'verify on the official portal' line."

---

## 5. Demo script (about 4 minutes)

1. **Hook (0:00–0:10):** "Crores of names changed in this year's roll revision. If yours was one of them, could you find out why in 10 seconds?"
2. **Citizen (0:10–0:50):** a judge scans a QR code and sends a Hindi voice note with a misspelled name. The bot finds the entry and explains its status and next steps. A Punjabi reply is shown.
3. **Auditor (0:50–2:00):**
   - Load roll v2 and watch the diff run.
   - Open a deletion-spike flag card: what was found, why it's unusual, innocent explanations, 78% confidence, "Needs human review".
   - Show a **duplicate cluster across scripts**.
   - Show a **benign look-alike correctly labelled "likely hostel move-out"**. This proves restraint.
4. **Claim Court (2:00–2:50):** paste a viral forward to get "Disputed" with an evidence chart. Paste its mirror claim from the other side to get identical treatment.
5. **Trust layer (2:50–3:30):**
   - Force a biased prompt; the Neutrality Guard blocks it.
   - Eval panel: blind precision/recall and the calibration plot.
6. **Close (3:30–4:00):** export the audit PDF. "Auditable. Explainable. Accessible. On no one's side."

---

## 6. Judge Q&A (prepare these answers)

**"Is synthetic data realistic?"**
- Generated from published aggregate patterns: age pyramid, mortality, migration.
- PDF ingest shows the real format works.
- Real data is not allowed by the rules.

**"Isn't this political?"**
- Mirror test, Neutrality Guard, no party, person or institution names.
- Flags ask for human review and never conclude anything.

**"False positives hurt real people."**
- That's why we use FDR correction, benign look-alike testing, calibrated confidence, a human review queue, and never show individual names publicly.

**"How is AI used meaningfully, beyond a chatbot?"**
- Statistical tests, entity resolution with embeddings, IsolationForest, calibration, an agentic claim checker and multilingual voice.

**"Scale?"**
- Booth-parallel processing. The 50k demo runs in seconds, and a full constituency runs in minutes.
- Deploy for journalists, observers and civil-society groups first.

**"What did you build here vs before?"**
- Everything during the 24 hours. Commit history proves it.

---

## 7. Content video (owner: #5)

- **Hook (0–5s):** "Is your name still on the voter roll?"
- **Then:** problem, then behind-the-scenes, then demo, then close.
- **AI used:** AI voiceover (ElevenLabs or Sarvam Hindi), auto-captions (CapCut), AI b-roll.
- **Labels:** mark AI parts as "Made with AI".
- **Shooting:** record clips every 3–4 hours from H0, including the night shift, and the moment the blind evaluation passes.

---

## 8. Tonight (allowed before the 27th: no project code)

- [ ] Create API keys (Claude/Gemini, Sarvam or Bhashini) and a Telegram bot via BotFather. Test that each works.
- [ ] Install Python 3.11, Node 20, and pip packages. Pull an Ollama model.
- [ ] Read the ECI claims/objections process and form numbers. Save notes.
- [ ] Storyboard the video. Plan the slide outline.
- [ ] Charge everything. Bring a phone hotspot, an extension board and a power bank.
- [ ] Release night: check how many teams pick PS1. **If 6 or more, discuss switching to Event Reach.**
