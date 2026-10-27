# RollWatch: Development Plan v3

> **D0 = the moment we start building after the presentation round** (27 Oct). Write the real clock times in the right-hand column once the submission deadline is confirmed.
> What: [START_HERE](START_HERE.md) · scope: [PRD v3](PRD.md) · how: [TRD](TRD.md) · look: [Design system v2](DESIGN_SYSTEM.md) · brand: [BRAND](BRAND.md) · stage: [Demo & pitch](DEMO_AND_PITCH.md).
> **Ship over polish, polish over tests.** Five smoke checks plus the demo run-through are the whole QA budget (TRD §9).

---

## 0. Where we start (already on `main`)

| Done | Not done |
|---|---|
| `contracts/` (models, schemas, fixtures, API spec) | API server (`api/main.py`, `llm.py`, `claims.py`, `guard.py`) |
| `generator/` (Sampleabad, churn, plantings, answer key, training district) | `demo_config.yaml` for the demo booths (B047/B012/B063/B030) |
| `engine/` (diff, BH, stories, duplicates, rules, Platt, eval); smoke checks 1–2 pass | Engine run on the full district, the bench, rule error rates |
| `web/` shell, booth grid, flags + drawer + story bar **on mocks**, v1 look | Web on the live API, v2 look, Claim Court / Ask / Trust / card pages |
| `api/citizen.py` search + templated answers (hi/en/pa) | Telegram bot, share card, voice, demo mode |

## 1. People and sessions (4 Claude Code sessions at most)

| | Rishabh, "Engine" | Partner, "Product" |
|---|---|---|
| Session 1 | **A1:** demo config, then API + LLM + Claim Court agent + guard + ops | **B1:** web v2 (all pages) |
| Session 2 | **A2:** engine finish, eval, rule error rates, bench | **B2:** citizen chat, Telegram bot, share card/clip, voice |
| Also owns | contracts, merges, logo, tech Q&A | blind planting config, content video, slides, design QA |

Worktrees: `a1`, `a2`, `b1`, `b2` (already created at H0; `git worktree list` to check). Merge to `main` at the gates only, after `next build` passes and the API boots once.

## 2. D0: the first 45 minutes, in parallel

**Rishabh:**
- [ ] Commit the v3 docs on `main` (Rishabh's name only, no co-author line).
- [ ] Verify Form 6 / 7 / 8, helpline 1950 and the ECINET app name on voters.eci.gov.in, then update `api/constants.py` and remove the `# VERIFY` marks.
- [ ] Key smoke tests on **venue Wi-Fi and then the hotspot**:
  - Claude tool-use JSON call
  - Gemini call
  - Sarvam STT on a 10 s Hindi note and TTS in `hi-IN`
  - a Telegram echo bot
- [ ] Start the logo ([BRAND.md](BRAND.md) §3). It's needed by the B1 polish pass at D13.

**Partner:**
- [ ] Write `private/planting_config.yaml`: about 24 anomalies and 12 decoys that **look scary** (a hostel emptying, a boundary redraw, a mass death). **Never show it to Rishabh.**
- [ ] Run the generator with it and commit only the roll and context files.
- [ ] Behind-the-scenes clip #1.

**Sessions:** paste the kickoff prompts (§5) at D0.75.

## 3. Timeline

| D | A1 (api) | A2 (engine) | B1 (web) | B2 (citizen/bot) | Clock |
|---|---|---|---|---|---|
| 0.75–2.5 | `generator/demo_config.yaml` → the exact demo numbers in START_HERE §4; re-run; **export real `flags.json` / `stories.json` mocks to web** | Run on the full district, fix whatever breaks; smoke checks 3–5 placeholders → real | **v2 restyle:** Geist fonts, `tokens.css` v2, floating bar, two-tone headlines, chips. Remove the LATENT table in `lib/stories.ts` | Citizen chat page logic on fixtures; Hindi/Punjabi/English templates final | |
| 2.5–5 | `api/main.py`: serve artifacts; `/overview`, `/flags`, `/stories/{booth}` toggle, `/search`, `/citizen/ask`; ops middleware | Rule false-positive rates per rule from the eval (M10) → `rules.json`; `engine.run --bench` → `bench.json` | Audit page on the live API: booth grid, drawer, **context controls** with the residual tween | Telegram bot skeleton (long polling) calling `/citizen/ask` | |
| **D5 gate** | Does the web show real flags from the API? If not, B1 stays on exported mocks and A1 fixes the API first. | | | | |
| 5–7.5 | `llm.py` (Claude tool use, temp 0, disk cache, Gemini + template fallback); **Claim Court agent** with the typed tool menu, hard rules and deterministic verdict | Platt calibration check; duplicates on the full district; pair-count numbers for the bench | Claim Court page: claim → sub-claim rows with chips and query chips; mirror cards | Vision read of forward screenshots → `/claims/check`; bot returns text verdicts | |
| 7.5–9.5 | `guard.py` + lexicon (EN/HI/PA) + `/guard/log`; mirror; `/ops` | Help A1: precomputed aggregates for the claim tools (O(1) lookups) | `/card/[id]` share card (1080×1350) + Chrome render script; Ask page | **Bot sends the share card PNG** (M9); `/check` in groups (S11) if easy | |
| **9.5–10.5** | **CHECKPOINT:** merge everything; live API; `next build`; **the partner reveals the blind eval**. All four modules plus M9–M11 run end to end. Film the reveal. | | | | |
| 10.5–13 | Fix the 2 worst eval misses with A2; **`POST /audit` + Dockerfile + compose (M12)**; cache every scripted LLM path | Scale run (S10) at 1M with per-ward parallel speed-up; **`stories.yaml` (S12)** + a synthetic "objections filed" evidence table; realism chart data (S8) | Trust page: scoreboard, reliability, rule table, guard count, **ops strip** | Sarvam Hindi voice in/out (S3); share clip (S9) with A1's ffmpeg command | |
| **D13 gate** | Merge. Anything not working end to end is **cut, not fixed**. Logo goes in now. | | | | |
| 13–14 | `DEMO_MODE=1`; pre-render cards, clips and TTS for the script | Freeze artifacts | Polish pass against the design system v2; logo, favicon, OG image | Cached voice path; bot avatar | |
| **D14** | **FEATURE FREEZE.** Commit `artifacts/`, `cache/` and `cards/`, then tag `demo-v1`. | | | | |
| 14–16.5 | Wi-Fi-unplugged run; cold-reboot run; README with limitations, complexity table and AI-use disclosure | | Backup screen recording; slides (v2 style) | Content video edit | |
| 16.5–19.5 | **Rehearse the 4:00 demo ×4 with a timer**, plus a Q&A drill (each of us explains 3 random functions and their complexity) | | | Final video export | |
| 19.5–21 | Buffer, submission, laptop and phone charged, hotspot on | | | | |

## 4. Cut order (cut from the top at any gate where we're late)
1. S11 group `/check`
2. The live S12 YAML edit on stage (keep `stories.yaml`, show the file instead)
3. S9 share clip (keep the PNG card)
4. S3 voice (keep text)
5. S8 realism chart
6. The live mirror run (show one precomputed pair)
7. The Telegram bot (web Claim Court + web chat, and show the card PNG on screen)

**Now never cut either** (the judges' feedback): M12 `POST /audit`, plus at least the 50k bench numbers. The S10 1M run is cut only as a last resort, because it answers "not scalable" directly.

**Never cut:**
- Which Story Fits? with the live context controls
- Claim Court with query chips and the hard rules
- M9 card output (on the web at least)
- M10 rule error rates
- the blind-eval Trust page with the ops strip
- the Neutrality Guard log
- the web citizen chat in HI/EN/PA
- `DEMO_MODE`

**Already cut, don't revive:**
- OCR/PDF rolls, torch/embeddings, Ollama, isotonic calibration, review-queue learning, alerts
- voice claims, maps, IsolationForest
- review buttons + hash chain, the print report, Punjabi voice
- a generic dashboard or free-chat bot

## 5. Kickoff prompts (paste one per session at D0.75)

Every session reads `CLAUDE.md`, `docs/START_HERE.md` and `docs/TRD.md` first. Each prompt ends with: *"Plan in 5 bullets, wait for OK, then build. Only touch your folder. Add at most the smoke check named for you in TRD §9. Commit small and often."*

- **A1:** "First, add `generator/demo_config.yaml` so the demo booths match START_HERE §4 exactly (B047 unusual, B012 hostel benign, B063 boundary toggle, B030 mirror), re-run the generator and export the real `flags.json` / `stories.json` into `web/mocks/`. Then build `api/` per TRD §1.1, §3.5, §5, §6 and §8: FastAPI on :8000 serving artifacts from memory, an ops middleware to `artifacts/ops.jsonl` and `/ops`, `llm.py` (Claude tool use at temperature 0, sha256 disk cache, Gemini then template fallback), a Claim Court tool-use agent over the fixed typed tool menu with the hard rules in code and a deterministic verdict, the mirror, `guard.py` with the EN/HI/PA lexicon and its log, and `DEMO_MODE=1`."
- **A2:** "Finish `engine/` per TRD §1.1 and §4. Run it on the full district and fix what breaks. Add per-rule false-positive rates from the eval (`rules.json`, PRD M10), `python -m engine.run --bench` writing the stage times and duplicate pair counts to `bench.json`, the scale run at 1M voters (S10), and the precomputed aggregates the claim tools need for O(1) lookups. Never read anything under `private/`."
- **B1:** "Restyle and finish `web/` to **docs/DESIGN_SYSTEM.md v2** (butter.video-inspired): Geist fonts self-hosted, `design/tokens.css` v2 in `globals.css`, a floating grey bar with Audit · Check · Ask · Trust, two-tone regular-weight headlines with an inline object, mono eyebrows and signal chips. Light only, no lucide/heroicons/emoji, no gradients except the hatch. Pages: Audit (booth grid, drawer with the 4-line card, story bar and context controls), Check (Claim Court with query chips and the mirror), Ask (citizen chat), Trust (scoreboard, reliability, rule table, guard count, ops strip), `/card/[id]` (1080×1350). Switch from mocks to `http://localhost:8000` as soon as A1's endpoints exist; delete the LATENT table."
- **B2:** "Finish the citizen flow in `api/citizen.py` (you own only that file plus `bot/`) per TRD §7. Then build `bot/` with python-telegram-bot long polling as a thin client of `/citizen/ask` and `/claims/check`. It accepts forward screenshots, replies with the share-card PNG (PRD M9), supports `/check` on a replied-to message in groups if time allows (S11), and handles Sarvam Hindi voice in and out (ffmpeg OGG→WAV). Always end with the official portal line and the BLO-scam line."

## 6. Partner checklist (outside code)
- [ ] The blind planting config at D0, with scary-looking decoys.
- [ ] Behind-the-scenes clips at D0, D3, D6, **the checkpoint reveal**, late night and the freeze ([content video](CONTENT_VIDEO.md)).
- [ ] Final slides in the v2 style by D15: one headline and one visual per slide, no script.
- [ ] Persona cards (Meena B047, Ravi B012, Harpreet B063) with a QR code to the web chat.

## 7. Open items
- [ ] Submission format, deadline and demo slot length: ask the organiser.
- [ ] Disclose AI-tool use in the README and pitch. (Recommended.)
- [ ] Partner commits under their own git identity. (Recommended: it proves both of us built it.)
- [ ] The logo and the final palette check, once Rishabh's logo is in.
