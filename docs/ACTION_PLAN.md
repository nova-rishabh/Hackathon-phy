# RollWatch: Action Plan (ship in 21 hours)

> **R0 = the moment you start H0 below** (about 3h after the event clock started). Write the real clock times in the right-hand column once you know the submission deadline.
> Scope: [PRD](PRD.md) · how: [TRD](TRD.md) · look: [Design system](DESIGN_SYSTEM.md) · stage: [Demo & pitch](DEMO_AND_PITCH.md).
> **Ship over polish, polish over tests.** Five smoke checks plus the demo run-through are the whole QA budget (TRD §9).

---

## 0. People and sessions (4 Claude Code sessions at most)

| | Human A: Rishabh, "Engine" | Human B: partner, "Product" |
|---|---|---|
| Session 1 | **A1** generator, then api + LLM + Claim Court | **B1** web (Next.js) |
| Session 2 | **A2** engine (diff, stats, stories, duplicates, eval) | **B2** citizen chat backend, then bot, then voice |
| Also owns | contracts, merges, pitch delivery, tech Q&A | blind planting config, content video, slides, design QA, impact Q&A |

- **Worktrees:** `git worktree add ../rw-a1 -b a1`, and likewise for `a2`, `b1` and `b2`.
- **Merges:** merge into `main` at R5, R9.5 and R13. Never merge without a `next build` and one boot of the API.
- **Code review:** each human spends 10 minutes per module reading what Claude wrote. Both must be able to explain any function on stage.

## 1. H0: the first 45 minutes (R0 → R0.75), in parallel

**A (contracts first, before any session starts):**
- [ ] `.gitignore`: `.venv/ node_modules/ .env cache/llm/ private/ cards/*.png` (unignore `cards` at the freeze)
- [ ] `contracts/models.py`: RollRow, context tables, Flag, StoryResult, ClaimVerdict, citizen and API I/O, exactly as in TRD §3
- [ ] `contracts/export.py` → `*.schema.json` → `web/lib/types.ts`
- [ ] `contracts/api.md` (TRD §3.5)
- [ ] `contracts/fixtures/`: a hand-made 20-row v1/v2 with 1 cross-script duplicate, 1 impossible age, 1 hostel move-out, 1 boundary move and 1 death
- [ ] Root `CLAUDE.md` (already written, so just review it)

**B (environment and keys):**
- [ ] `uv venv --python 3.12 .venv`, then `uv pip install …` (TRD §2), then `uv pip freeze > requirements.lock`. **Do this now, while the Wi-Fi works.**
- [ ] `web/`: `pnpm dlx create-next-app@15 . --ts --tailwind --app --no-src-dir`, then shadcn init. Paste `design/tokens.css` into `globals.css` and copy `design/glyphs.svg` into `web/public/`.
- [ ] Download the four fonts (woff2) into `web/public/fonts/`.
- [ ] Smoke-test the keys:
  - [ ] Claude JSON call
  - [ ] Gemini call
  - [ ] Sarvam STT on a 10 s Hindi voice note, and TTS in `hi-IN` and `pa-IN`
  - [ ] a Telegram echo bot on **venue Wi-Fi**, and again on the **hotspot**
- [ ] Verify Form 6 / 7 / 8, the 1950 helpline and the ECINET app name on the official portal, and write them into `api/constants.py`
- [ ] Write `private/planting_config.yaml`, about 24 anomalies plus 12 benign decoys. **Never show it to A.**
- [ ] Record behind-the-scenes clip #1

**R0.75:** create the 4 worktrees and paste the kickoff prompts (§4).

## 2. Timeline

| R | A1 | A2 | B1 (web) | B2 (citizen/bot) | Clock |
|---|---|---|---|---|---|
| 0–0.75 | H0 | H0 | H0 | H0 | |
| 0.75–2.5 | Generator v0: 100 booths, households, Devanagari+Latin names, churn, context tables, `SEED=42` | Diff, rule checks, binomial + BH on fixtures | Shell, banner, nav, booth grid on fixture mocks | `/search` normaliser + `/citizen/ask` on fixtures (EN/HI/PA templates) | |
| 2.5–5 | Planting from config, answer key, training district `SEED=7`. **B runs it with the private config.** | Story attribution (§4.2) + `stories.json`, then `flags.json` v0. **R4.5: export real mocks to web.** | Flags queue + flag card drawer + story bar | Web chat page wiring, status block, language tabs | |
| **R5 gate** | Do the generator and flags v0 exist? If not, cut S8 and S5 now. | | | | |
| 5–7.5 | API serving artifacts, `llm.py` (cache + guard + fallback), flag-card batch | Cross-script duplicates + clusters, `/stories/{booth}` toggle | Overview totals, story toggle UI, duplicate card | Telegram bot (long polling) on the same API | |
| 7.5–9.5 | Claim Court: splitter + tool menu + verdict rule + hard rules | Platt calibration, `engine.eval`, `/eval`, `/rules` | Claim Court page + Trust page | Sarvam Hindi voice in/out (S3) | |
| **9.5–10.5** | **CHECKPOINT:** merge everything, live API, `next build`, **B reveals the blind eval**. All 4 modules run end to end. Film it. | | | | |
| 10.5–13 | Mirror test, then screenshot claims (S1) | Fix the 2 worst eval misses, then the notice explainer data (S4) | `/card/[id]` share card + Chrome render script, review buttons (S6) | Bot share-card reply (S2), notice explainer replies, Punjabi TTS | |
| **R13 gate** | Merge. Anything not working end to end is cut, not fixed. | | | | |
| 13–14 | `DEMO_MODE`, cache every scripted path, pre-render cards and TTS | Freeze artifacts | `/report` print page (S7), polish pass against the design system | Cached voice path | |
| **R14** | **FEATURE FREEZE.** Commit `artifacts/`, `cache/` and `cards/`, then tag `demo-v1`. | | | | |
| 14–16.5 | Bug bash, the Wi-Fi-unplugged run, a cold reboot run, README + limitations + model card | | Backup demo screen recording, slides | Content video edit | |
| 16.5–19.5 | **Rehearse the 4:00 demo ×4 with a timer, plus a Q&A drill** (each human explains 3 random functions) | | | Final video export | |
| 19.5–21 | Buffer, submission, laptop + phone charged, hotspot on | | | | |

## 3. Cut order (cut from the top at any gate where you're late)
1. Screenshot claims (S1). Keep text.
2. Punjabi voice. Keep Punjabi text.
3. Print report (S7).
4. Review buttons (S6). Mention the audit-hash idea on a slide instead.
5. The notice explainer and rule cards (S4, S5). Keep one rule card as a static example.
6. The live mirror run. Show one precomputed mirror pair instead.
7. Telegram voice.
8. The Telegram bot entirely. Use the web citizen chat only and show the share card PNG on screen.

**Never cut:**
- the diff, BH test and cross-script duplicates
- **Which Story Fits?** with the toggle
- flag cards with the template fallback
- text Claim Court with its hard rules
- the Trust panel (blind eval)
- the Neutrality Guard log
- the web citizen chat in HI/EN/PA
- `DEMO_MODE`

**Already cut, don't revive:** OCR/PDF, torch/embeddings, Ollama, isotonic calibration, review learning, alerts, voice claims, maps, IsolationForest (unless everything else is done).

## 4. Kickoff prompts (paste one per session at R0.75)

Every session reads `CLAUDE.md` and `docs/TRD.md` first. Each prompt ends with: *"Plan in 5 bullets, wait for OK, then build. Only touch your folder. Add at most the smoke check named for you in TRD §9."*

- **A1, generator:** "Build `generator/` per TRD §3.1 and §4.6. Create a fictional district Sampleabad with 10 wards, 100 booths and about 50k voters. Each household needs Devanagari and Latin names (with realistic Latin spelling variants), relation names, an age pyramid shaped like Census C-13, and gender. Churn from v1 to v2 covers age-specific deaths (shape of SRS 2022, about 6.8 per 1,000 overall), shifting, and new 18-year-olds. Write the context tables: death register, hostel list and boundary changes. Plantings are read **only** from a YAML path given on the CLI, and the answer key is written to the path given. Also write a training district with random auto-plantings using `--seed 7`. Output parquet and CSV files to `artifacts/`."
- **A2, engine:** "Build `engine/` per TRD §4. It covers the diff, binomial + BH for deletion and addition spikes, the 'Which Story Fits?' attribution with a bootstrap CI and residual test, cross-script duplicates (normaliser + rapidfuzz + metaphone, union-find), rule checks, Platt calibration on the training district, and `engine.eval` against an answer-key path. Output `flags.json`, `stories.json` and `eval.json` matching `contracts/`. The engine must never import or read anything under `private/`."
- **A1 (after the generator), API:** "Build `api/` (FastAPI, :8000) per TRD §3.5, §5, §6, §7 and §8. Serve the artifacts from memory. In `llm.py`, use Claude via tool use at temperature 0, with a disk cache keyed by sha256, a Gemini fallback and a template fallback. Build the Neutrality Guard with `guard_lexicon.yaml` and a log. Build Claim Court with a fixed tool menu, the hard rules in code, a deterministic verdict and the mirror. Put verified procedural text in `constants.py`. `DEMO_MODE=1` serves only artifacts and the cache."
- **B1, web:** "Build `web/` (Next 15, client components only, fetching `http://localhost:8000`) strictly to `docs/DESIGN_SYSTEM.md`. That means light only, our tokens and glyphs, no lucide/heroicons, no gradients and no dark mode. Pages: Overview (booth grid), Flags (queue + drawer with the 4-line card and story bar with toggles), Claim Court (sub-claim stamps, query chips, mirror columns), Citizen (chat), Trust (eval + reliability + guard log), `/card/[id]` (1080×1350 share card) and `/report` (print CSS). Use `web/lib/types.ts` and the mocks in `web/mocks/` until the checkpoint."
- **B2, citizen and bot:** "Build the citizen flow in `api/citizen.py` (coordinate with A1; you own only this file plus `bot/`) per TRD §7: script-tolerant search, status and reason category, and template next steps in hi, en and pa. Then build `bot/` with python-telegram-bot long polling as a thin client of `/citizen/ask` and `/claims/check`. It replies with text, sends the share card PNG for claims, and handles Sarvam voice in and out (ffmpeg OGG→WAV). Always end with the official portal line and the BLO-scam line."

## 5. Partner checklist (outside code)
- [ ] The blind planting config at H0. Include **decoys that look scary**, such as a hostel emptying and a boundary redraw.
- [ ] Behind-the-scenes clips at R0, R3, R6, the checkpoint (the eval reveal), late night and the freeze ([content video plan](CONTENT_VIDEO.md)).
- [ ] 6 slides by R15 ([demo & pitch §4](DEMO_AND_PITCH.md#4-slides-6)).
- [ ] Persona cards for judges to try after the pitch, printed or on a phone: 3 synthetic voters, each with a QR code to the web chat.
- [ ] Optional: a printed booth QR poster as a table prop.

## 6. Things to ask the organisers early (a mentor or the rulebook contact)
1. The submission format and deadline, and the length of the demo slot.
2. Whether AI coding assistants are allowed. Disclose it either way.
3. Whether a backup screen recording is acceptable if the venue network fails.
4. Whether real *aggregate* public figures may appear in the pitch. They never appear in the product.

## 7. Open decisions for Rishabh
- [ ] Disclose AI-tool use in the README and pitch? (Recommended.)
- [ ] Should the partner commit under their own git identity? (Recommended, because it proves both members contributed.)
