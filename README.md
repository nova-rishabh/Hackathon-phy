# RollWatch

**Every change to a voter roll, explained. And every rumour about it, checked.**

RollWatch compares two versions of a voter roll and tells you which story each removal fits: a registered death, a duplicate cleanup, a boundary change, a hostel move-out, or *unexplained*. It checks viral claims against the same numbers, and it tells a citizen their own status and the form to file, in Hindi, English or Punjabi, with voice. Every output carries its reasoning and a confidence score, and says it needs human review.

All data is synthetic. Sampleabad is a fictional district: 100 booths, about 51,000 voters. No real voter data is used, and the system never infers religion, caste or community.

Team Nova (IDEAS-175) · X AI Tech Ideathon, 27–28 Oct 2026 · PS1, AI for Electoral Roll Transparency.

| | |
|---|---|
| Web | https://rollwatch-web.onrender.com (free plan: the first load after 15 idle minutes takes about a minute) |
| API | https://rollwatch-api.onrender.com · `GET /overview`, `POST /audit`, `POST /claims/check`, `GET /eval` |
| Chat | Telegram [@Rollwatch_bot](https://t.me/Rollwatch_bot) · WhatsApp sign-in and chat through the same bot core |

## What it does, with the demo numbers

All numbers below come from the engine, seed 42.

- **Which story fits?** Booth 47 lost 412 names against about 25 expected, and 97% of them fit no innocent story, so it gets **needs human review**. Booth 12 looks just as big to a rumour, but 79% of its removals fit a hostel move-out, so it's **likely benign**. In Booth 63, 64% of removals are unexplained. Switch on the boundary log and that drops to 8%.
- **Claim court.** *"Booth 47 mein 600 naam kaat diye, sabse zyada, aur sab ek community ke!"* is split into three sub-claims. "600" is **disputed** (computed 412, 46% off). "Most removals" is **verified** (rank 1 of 100). "Community" **cannot be proven**, because we never infer it from names. The opposite claim is checked with the same tools and the same tolerance.
- **Run it on your own roll** (`/run`, `POST /audit`). Drop two roll CSVs, or use the 10-booth sample. The same engine flags Booth 47 in about 3 seconds. This is how an office would check a draft before publishing.
- **Human review.** Signed-in reviewers mark a flag "looks innocent" or "needs a field check". Each review joins a hash chain, so editing an entry breaks the chain.
- **Citizen lookup.** Search a name in any script, even misspelled. You get your status, the likely reason, Form 6 or Form 7, the 1950 helpline, and a reminder that a BLO never asks for an OTP or money. Hindi answers can be read aloud.
- **WhatsApp (+91 80764 99841) and Telegram.** Say "hi", type a name, forward a claim (the verdict comes back with a share image), or send a Hindi voice note: it is transcribed and answered with a spoken reply in a native Hindi voice, written to be heard, not the card read aloud.
- **Watch a booth.** Signed-in users get its current state on WhatsApp, and a message whenever a new audit changes it.
- **Which documents if a notice comes.** For anyone off the list or with changed details, the answer says what a notice would ask for, from their age on the qualifying date (the SIR information sheet BLOs hand out): born before 1 July 1987, one document for yourself; 1987 to 2 December 2004, yourself and one parent; after that, yourself and both parents. Near a cutoff it shows both cases.

## The three questions

### 1. How does it scale?
- **Compute.** Every test is per booth and booths are independent, so a state is just more booths. Measured on one laptop core: **1,020,720 voters in 54 s**. Duplicate search compares **9.9 million candidate pairs instead of 521 billion**. The numbers are in `cache/bench.json`, with the machine recorded.
- **All of India.** From the Election Commission's own Lok Sabha 2024 state-wise table (97.8 crore electors, `api/data/`), the API computes: **13.5 minutes on 64 cores** for the whole country, and **Uttar Pradesh (15.4 crore) in 8.5 minutes on one 16-core server**.
- **Requests.** If one in ten voters checks during a 30-day revision, that's about 33 lakh checks a day, or **about 190 a second at peak**. One laptop measured **163 full answers a second on four processes** (a lower bound; `python -m engine.loadtest`, results in `cache/`), so two machines cover the peak. Precomputed answers are served as cached bytes, and WhatsApp state can live in Redis (`REDIS_URL`) so any number of instances can run.
- **Adoption.** No install. Answers go back as a share card into the chat the rumour came from (web, Telegram, WhatsApp), and each card brings the next user. Bring-your-own-key headers (`X-Gemini-Key`, `X-ElevenLabs-Key`) mean cost never blocks a newsroom or a volunteer group.
- **Scope.** The method fits any public list that gets "cleaned", like ration cards, pensions or scholarships. Story rules are config (`engine/stories.yaml`), not code.

| Step | Method | Complexity | Measured (1.02M voters, one core) |
|---|---|---|---|
| Roll diff | hash join on voter id | O(n) | part of 54 s total |
| Booth tests | one-sided binomial + Benjamini-Hochberg | O(m log m), m booths | 2,000 booths |
| Cross-script duplicates | blocking by booth/house and relation, score inside blocks, union-find | O(Σ bᵢ²) instead of O(n²) | 9.9M candidate pairs instead of 521B |
| Story attribution | fixed-order lookups per removed record | O(r) per booth | instant toggle in the UI |
| Bootstrap interval | 500 resamples, vectorised | O(B·r) | 2 ms for Booth 47 |
| Claim tools | precomputed booth/ward aggregates | O(1) per sub-claim | the query is shown on every row |

### 2. Why can't the government do this alone?
A self-audit can't settle a rumour about the auditor. When the body that revised the list says the rumour is false, a sceptical voter has no reason to believe it. So the same open engine has two ways in:
- **Inside:** an election office runs `POST /audit` on a draft roll before publishing. Booths whose removals no evidence explains get a second look before names are deleted.
- **Outside:** newsrooms, observers and citizens run the same code for claim checks and lookups. The arithmetic is the same on both sides, so they can't disagree about it.

If an office adopts it, that's the success case. The independent copy still has a job.

### 3. Why is it future-proof?
The core is fixed and measured. Everything that changes over time is a swappable part.

| What will change | How RollWatch absorbs it |
|---|---|
| Data source (PDF rolls today, APIs tomorrow) | An open input schema (`contracts/models.py`, `RollRow`) plus adapters. `engine/adapters/inrolls.py` already converts parsed roll CSVs (the open in-rolls parser's format); a synthetic round trip gives identical results. The engine doesn't change. |
| Process and evidence (new forms, new revision drives) | Story rules and evidence sources in `engine/stories.yaml`. Forms and helplines in `api/constants.py`. |
| AI models | The model only splits claims and phrases text. Every number comes from Python. The model sits behind one client with a template fallback, so swapping it changes wording, never a verdict. We swapped both the model and the voice in an afternoon. |
| Languages and channels | Per-language templates. Web, Telegram and WhatsApp are thin clients over one bot core (`bot/core.py`). |
| Trust over time | Every change is re-measured by the blind eval and published on the Trust page. |

## What we publish about our own errors
Measured on the synthetic district with a planted answer key (`python -m engine.eval`), and shown live on `/trust`:
- **Blind test:** a separate AI agent planted anomalies and innocent look-alikes in a fresh district and kept the key. The engine, calibrated only on four public training districts, found **9 of 9** and cleared **6 of 6**, with nothing missed and no decoy wrongly flagged. Flags stated at about 94% were right 93% of the time. Its weakest rule: impossible-relation checks (26% false on that district). Published scoreboard: `api/data/blind_eval.json`, `/eval/blind`.
- On our own demo district: found **6 of 6** planted anomalies. Cleared **7 of 7** innocent decoys (deaths, hostel move-outs, a boundary move). A removal spike is cleared only when what's left after the innocent stories is no higher than background. A decoy that shares a booth with a real anomaly counts as cleared only if its records are matched to the innocent story.
- False-positive rate per raised flag: duplicates 9.8%, relation conflicts 11%, removal spikes 0% (1 raised, 8 cleared as likely benign), addition spikes 50% (2 raised), impossible age / oversized household / gender swing 0%.
- Confidence is a Platt curve per rule, fit on four separate training districts (seeds 7–10). When we say about 93%, the flags are right 90% of the time. For removal spikes the input is the leftover after innocent stories, not the raw spike.
- **The official "logical discrepancy" checks** reported for the 2025–26 revision are run and published, never raised as flags (`engine/official.py`). On our district:

  | Check | Trips | Innocent |
  |---|---|---|
  | parent under 15 or over 50 years older | 113 | 81% |
  | six or more children of one parent | 166 | 98% |
  | own name changed since the last roll | 196 | 100% |
  | relative's name changed | 323 | 100% |
  | relation type changed (marriage) | 183 | 100% |
  | age didn't progress | 44 | 100% |
  | grandparent under 40 years older | 0 | – |

  These are synthetic rates: they depend on the innocent churn the generator models (marriages, spelling fixes, typos, large families). The point stands: none of these checks can tell a marriage from an anomaly. Sibling gaps under 9 months can't be checked from a roll, because it carries ages in years, not birth dates.
- The generator also adds realistic background noise (about 0.5% cross-script duplicates). It writes these to `<key>.background.json`, so a correct catch of one isn't counted as an error.
- Confidence curves are fit on four synthetic training districts (98 removal-spike flags); real lists would need recalibration.

## Platform features (for organisations)
- **Workspaces, roles and API keys** (`/orgs`): owner, admin, auditor, reviewer, viewer. Roles come from membership in that workspace; keys are hashed, expire, and work only in their own workspace.
- **Async constituency audits** (`POST /jobs/audit`): returns a private job token; progress, result and cancel need it.
- **Reports:** newsroom briefing (Markdown, HTML), CSV exports of flags and booths, data-quality and provenance reports (`/reports/*`).
- **Review workflow:** review queue, batch reviews (signed in), a tamper-evident hash-chained history with a verify endpoint, and recalibration of confidence from reviewed outcomes (operator only).
- **Public-roll PDF ingestion:** `engine/adapters/inrolls.py` reads searchable roll PDFs as well as parsed CSVs.
- **Caching and incremental audits:** ETag/304 responses and re-running only changed booths (`/audit/incremental`).
- **Monitoring:** `/ops/monitoring` (status of web, API, Redis, Telegram, WhatsApp); writes and error details are operator only.
- **Seven languages** in citizen answers: Hindi, English, Punjabi, Bengali, Marathi, Tamil, Telugu; skip link and reduced-motion support; light and dark themes (follows the system, with a header toggle).
- **Deployment and rollback:** `docs/DEPLOYMENT_AND_ROLLBACK.md` and `scripts/deployment_check.py`.

## Who pays
- **Citizens never pay:** name lookup on the web, WhatsApp and Telegram, claim checks with the share image, the documents guide, three languages with voice.
- **Organisations build a plan** on `/pricing`: platform, constituencies audited, their own WhatsApp number, extra languages, reviewer seats, voice replies, or a private deployment. Newsrooms and NGOs get 50% off, and yearly billing gets two months free. Prices are quoted by the API (`api/billing.py`, list prices in `api/constants.py`), and payment is a Razorpay subscription created server-side for exactly that plan, with its signature verified server-side.

## Safety of the service
- Per-client rate limits on the endpoints that cost money or CPU, input size caps, strict ids, the engine rerun operator-only, and a per-number limit on WhatsApp (`api/limits.py`). Counts live in Redis when `REDIS_URL` is set.
- Access control (`tests/test_access_control.py`, 26 attack checks): no anonymous workspace access, no cross-workspace keys, no granting above your own role, billing records and cancellation, recalibration and monitoring writes are operator only, jobs need their private token, batch reviews need sign-in.
- Sign-in codes are hashed and rate-limited; tokens are HMAC-signed; worker and payment secrets are compared in constant time; secrets live only in the environment.
- Shared links preview with a proper card, and a shared claim previews as its own verdict card.

## Run it
```
uv venv --python 3.12 .venv && .venv\Scripts\activate && uv pip install -r requirements.lock
set PYTHONUTF8=1
python -m generator --auto-plant 60 --seed 7 --out artifacts
python -m generator --config generator/demo_config.yaml --key artifacts/answer_key.json --seed 42 --out artifacts
python -m engine.run --data artifacts --out artifacts --train-data artifacts/training --train-key artifacts/training/answer_key.json
python -m engine.eval --key artifacts/answer_key.json
uvicorn api.main:app --port 8000
cd web && pnpm install && pnpm dev
python smoke_test.py
```
`DEMO_MODE=1` serves only precomputed artifacts and cached model answers, with no network. Keys go in `.env` (see `render.yaml` for the variable names) and are never committed.

## AI use, disclosed
- **In the product:** Gemini splits a forwarded claim into sub-claims, reads screenshots and phrases text. It never produces a number that is shown, and with the model off, template fallbacks give the same verdicts. ElevenLabs reads Hindi answers aloud and transcribes voice. All outbound text passes a neutrality guard (`api/guard.py`): no party, person or institution names, and no fraud or rigging words.
- **In the build:** the team used Claude Code as a coding assistant. The statistics, thresholds, evaluation design and every decision were reviewed by the team, and the smoke checks (`smoke_test.py`, `python -m bot.smoke_checks`) gate every deploy.

## Docs
[`docs/START_HERE.md`](docs/START_HERE.md) (start here) · [`docs/PRD.md`](docs/PRD.md) · [`docs/TRD.md`](docs/TRD.md) · [`docs/DESIGN_SYSTEM.md`](docs/DESIGN_SYSTEM.md) · [`docs/DEMO_6PM.md`](docs/DEMO_6PM.md) · [`docs/SESSION_LOG.md`](docs/SESSION_LOG.md)
