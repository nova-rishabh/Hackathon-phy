# RollWatch: action plan for the final presentation

Written 28 Oct after the checkpoint pitch. Everything below is either done (with proof), or a task with an owner.
Every slide and answer still covers the three questions: **how it scales, why not the government alone, why it's future-proof.**

---

## 1. What the judges asked, and our answers (with numbers we measured)

### "Why not use big data / machine learning instead of a small model?"
**Short answer:** "We do use ML where it helps, and we use statistics where a voter's rights are at stake. There is no labelled data of real wrongful deletions to train a big model on, and a notice has to say *why*. A booth-level test plus 'which story fits' gives a reason a person can check. A black-box score can't."

The longer points:
- **No ground truth to learn from.** Nobody has a labelled dataset of real wrongful deletions. A 2021 study of voter-file change monitoring (Royston et al., used with the Iowa Secretary of State) names this as the core difficulty, and found that statistical models comparing districts over short time spans worked best for surfacing anomalies. They also labelled each change's likely root cause, which is our "which story fits".
- **Explainability is a legal need, not a nice-to-have.** A deletion notice must cite a reason a voter can contest. Our output is "412 removed vs about 25 expected; 10 match the death register; 401 have no record". A model score can't be appealed.
- **We already use ML where it is the right tool:** Platt-calibrated confidence (logistic regression, fit on four training districts, 98 cases for removal spikes); fuzzy cross-script name matching; an LLM to split claims and phrase answers.
- **It is big-data ready:** the engine is linear and per booth. ECI's official Lok Sabha 2024 state-wise table sums to **97.8 crore electors** (99.1 crore by 2025). At our measured **1.02M voters in 54 s on one core**, all of India is about **14.4 core-hours, or 13.5 minutes on 64 cores**. Per state, on one 16-core server: **Uttar Pradesh (15.4 crore) in 8.5 minutes**, Maharashtra 5.1, Bihar 4.3, West Bengal 4.2.
- **Where ML goes next (roadmap):** with real data, learn the background removal rate per area (migration, deaths) instead of a fixed age model, and train a classifier on reviewed outcomes. The human-review log we now record is exactly that training data.

### "How do you handle crores of requests? What if everyone uses it?"
**Short answer:** "If one in ten voters checks during a revision, that's about 190 checks a second at peak. We measured one laptop answering 163 a second on four processes, so two machines cover India's peak, and most answers never touch the engine: the audit is precomputed once per roll, viral claims are cached, and a name lookup is an index search."

Measured (`python -m engine.loadtest`, results in `cache/loadtest_1w.json`, `cache/loadtest_4w.json`; offline mode, localhost, laptop):

| Route | 1 process | 4 processes |
|---|---|---|
| Overview (precomputed) | ~132 req/s with one client; ~580 req/s with three clients | |
| Name search | 103 req/s | 202 req/s |
| Full citizen answer | 72 req/s | 163 req/s |
| Claim check (cached split) | 105 req/s | 211 req/s |

The 4-process figures are **lower bounds**: our single test client saturates at about 170–200 req/s; three clients together pulled about 580 req/s from the same server.

**Sizing for a revision window** (computed by the API at `/ops` → `projection`): if 10% of 99.1 crore electors check once in 30 days, that's about **33 lakh checks a day**, or **about 38 per second on average** and **about 190 per second at a 5× peak**. Our laptop measured 163 full answers a second on four processes (a lower bound), so **two such machines cover the peak**, before any CDN or claim caching, because:
- **The audit is computed once per roll**, not per request (static JSON, now served as pre-built bytes with cache headers so a CDN can answer it).
- **Viral claims repeat.** The same forward gets the same cached verdict, and the model is never called twice for it.
- **The model is only used for phrasing**, with a 5 s cap and a template fallback. Under load we can switch phrasing off and answers stay correct.
- **A name lookup is an index search** within one booth or ward, sharded by constituency.

What still has to change for real scale (honest list):
- WhatsApp sign-in codes and the outbox live in one process's memory. Move them to Redis to run several API instances.
- Put a CDN (e.g. Cloudflare) in front of the static routes and the share images.
- Run the engine per constituency in parallel (a job queue), writing per-booth results to object storage.
- Rate-limit per phone number on WhatsApp (sign-in is already rate-limited).

---

## 2. Blind test: prompt for another AI agent (paste as is)

Run this in a **separate** Claude Code session on this repo. That agent writes the hidden plantings and runs the scorer. We only ever see the scoreboard.

```
You are running a blind test for RollWatch, a hackathon project in this repo (synthetic voter-roll audit).
The engine's author must never see what you plant. Follow these rules exactly.

GOAL
Write a hidden planting config, generate a fresh synthetic district from it, run the engine (which must not
see the key), score it, and report ONLY the scoreboard.

RULES
- Write only inside private/ (git-ignored) and artifacts_blind/. Never commit, push, or print the contents of
  private/ or the answer key. Never paste plant IDs, booth IDs or sizes of plantings in your final message.
- Do not modify any code in engine/, api/, generator/ or contracts/.
- Use PYTHONUTF8=1 and the repo's virtualenv: .venv\Scripts\python.exe (Windows).

STEP 1: Read generator/README.md (the planting schema and what each type does) and generator/example_config.yaml.
Design a realistic, hard blind config at private/planting_config.yaml with 12 to 16 plantings:
- Mix anomalies (is_benign: false) and innocent decoys (is_benign: true), roughly half and half.
- Use every type at least once: deletion_spike, addition_spike, duplicate_cluster, impossible_age,
  oversized_household, gender_ratio_swing, hostel_moveout, boundary_change, mass_death.
- Include tricky cases: a hostel_moveout with is_benign: false (unlisted hostel, should stay unexplained), a
  mass_death with is_benign: false (deaths not registered), a small deletion_spike close to the noise level
  (size 25-35), and a benign decoy in the same booth as an anomaly.
- Pick booth IDs B001-B100 at random (avoid B047, B012, B063, B030: those are the public demo). Don't put two
  plantings of the same type in one booth. For boundary_change, set to_booth to the next booth.
- Use plant_id values P01, P02, ...; sizes within the ranges the README implies.

STEP 2: Generate with a seed only you know (pick any integer 1000-9999, do not report it):
  .venv\Scripts\python.exe -m generator --config private/planting_config.yaml --key private/answer_key.json --seed <your seed> --out artifacts_blind

STEP 3: Run the engine. It never reads the key; calibration comes from the public training districts:
  .venv\Scripts\python.exe -m engine.run --data artifacts_blind --out artifacts_blind --train-data artifacts/training,artifacts/training_8,artifacts/training_9,artifacts/training_10 --train-key artifacts/training/answer_key.json,artifacts/training_8/answer_key.json,artifacts/training_9/answer_key.json,artifacts/training_10/answer_key.json
  (If artifacts/training_8 etc. don't exist, first run for s in 8 9 10:
   .venv\Scripts\python.exe -m generator --auto-plant 60 --seed s --out artifacts --name training_s)

STEP 4: Score:
  .venv\Scripts\python.exe -m engine.eval --key private/answer_key.json --flags artifacts_blind/flags.json --out artifacts_blind/eval.json --data artifacts_blind

STEP 5: Report back ONLY:
- From artifacts_blind/eval.json: planted_anomalies, found, planted_decoys, decoys_cleared, benign_fp_rate,
  and for each miss its "type" and "why" (no booth IDs, no plant IDs).
- The reliability bins (mean_conf, frac_true, n).
- The per-rule table printed by engine.eval (rule, raised, fp_rate).
- One line: "Config and key are in private/, not shown."
Then copy artifacts_blind/eval.json and artifacts_blind/rules.json to artifacts_blind/public/ so the team can
publish them. Do not copy anything from private/.
```

After it reports: we publish the scoreboard on Trust as "Blind test (planted by a separate agent; we never saw it)".

---

## 3. Everything to do before the final

### Done since the checkpoint (live)
- [x] Share image in WhatsApp and Telegram claim replies.
- [x] Native Hindi voice (Devi) with a reply written to be heard; full-sentence voice notes now find the voter.
- [x] Proper voice-note bubbles (ffmpeg on the server).
- [x] Confidence fit on four training districts (Booth 47: 97%, 98 cases).
- [x] Booth watch alerts on WhatsApp; help reply for stickers and documents.
- [x] API keys rotated.
- [x] Load test and pre-built cached responses (this document, §1).

### Done on 28 Oct (after the checkpoint)
- [x] **Documents guide from the BLO's SIR sheet.** For anyone off the list or with changed details, the answer says which documents a notice would ask for, from their age on the qualifying date (before 1 Jul 1987: self; 1987–2004: self + one parent; after 2 Dec 2004: self + both parents). Near a cutoff it shows both cases.
- [x] **Real-data adapter** `engine/adapters/inrolls.py`: parsed roll CSVs (the in-rolls open parser's columns) to our schema. A synthetic round trip gives identical demo results (412 / 401 unexplained; 79% hostel; mixed 63).
- [x] **Trust:** "At national scale" (13.6 min on 64 cores; 191 checks/s peak; 2 machines) and "Why statistics, not a black box".
- [x] **Realism anchors** (public polling-station metadata, counts only, no names): a real assembly constituency has about 200–260 booths and about 1.7 lakh electors (about 870 per booth; Punjab, West Bengal, Karnataka). Sampleabad (100 booths, 51k) is a scaled-down constituency, and the 1M run is about six constituencies.

### Product (in order)
1. **Blind test** (§2). Owner: agent + Rishabh. Then publish on Trust.
2. **Website animation pass** (§4). Owner: Claude.
3. **Scale section on Trust:** show the load-test table and the "all of India in about 14 minutes on 64 cores" line. Owner: Claude.
4. **"Why statistics, not a black box" card** on Trust, with the research citation. Owner: Claude.
5. **Redis for WhatsApp state**, then two API instances behind Render. Owner: Claude (needs a Redis URL; Upstash free tier).
6. **Real-data path (roadmap slide only):** PDF-to-roll adapter for one constituency, aggregates only.

### Pitch
1. Add a **"Judges asked"** slide pair: *Why statistics, not big ML* and *Crores of requests*, using §1's short answers and tables.
2. Replace "blind test pending" with the blind-test scoreboard.
3. Update Booth 47 confidence to 97% (98 training cases).
4. Re-render the film's last 15 s if the numbers change (sources in `deliver/`).
5. Rehearse to 4:00, with the film first.

### Risks to watch
- Render free plan sleeps: the keep-awake workflow runs until 29 Oct. Extend it, or upgrade, for the final day.
- The WhatsApp worker runs on the laptop: keep it plugged in and awake.
- ElevenLabs credits: check the key's limit the morning of the final.

---

## 4. Website animation pass (design system v2: springs, no bounce, no glows)
- **Hero:** two-tone headline words rise in with a small blur on load (already), plus a live booth tile that cycles 47 → 12 → 63 inside the headline.
- **Numbers count up** with springs when they scroll into view (412, 97%, 6/6, 7/7, 1.02M).
- **Story bars fill** segment by segment when visible; the hatched "unexplained" segment fills last.
- **Booth grid cascades** in on the diagonal, like the film.
- **Trust:** reliability bars and official-check bars grow when visible; scoreboard numbers count up.
- **Check page:** verdict rows slam in one by one when the result arrives (the chip scales from 1.7 to 1 on a spring).
- **Respect `prefers-reduced-motion`:** everything shows instantly.

---

## Sources
- ECI, General Elections 2024, statistical report 9, State-wise number of electors (`api/data/electors_2024_states.csv`; totals verified against the report's TOTAL row)
- ECI electorate, 2025 (99.1 crore): [News Arena](https://www.newsarenaindia.com/nation/india-s-voter-count-reaches-99-1-crore/34469), [Deccan Herald](https://www.deccanherald.com/india/india-now-has-991-crore-voters-election-commission-3368788); 2024: [ECI Atlas 2024](https://www.eci.gov.in/EBooks/atlas-2024/files/basic-html/page71.html)
- Royston et al., *Anomaly Detection and Automated Labeling for Voter Registration File Changes* (2021): [arXiv 2106.15285](https://arxiv.org/abs/2106.15285)
- Anwar, Jain, Kettler, *Detecting anomalies in voter registration data* (2024): [Boise State](https://experts.boisestate.edu/en/publications/detecting-anomalies-in-voter-registration-data-2024-esra-issue/)
- Polling-station metadata and roll parser (aggregates only, no personal data used): Sood and Dhingra, *Indian Electoral Rolls PDF Corpus*, [Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/OG47IV); [in-rolls/electoral_rolls_parse_searchable](https://github.com/in-rolls/electoral_rolls_parse_searchable)
- SIR documents: the Information Sheet for Enumeration Form (handed out by BLOs)
- Logical-discrepancy criteria: [The News Minute](https://www.thenewsminute.com/karnataka/karnataka-sir-age-gaps-name-mismatches-among-criteria-as-20-lakh-voters-face-notices), [Internet Freedom Foundation](https://internetfreedom.in/analysis-and-explainer-on-how-the-sir-excluded-voters-at-scale/)
