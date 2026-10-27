# RollWatch: Technical Requirements (TRD)

> Scope comes from the [PRD](PRD.md). Order of work comes from the [action plan](ACTION_PLAN.md).
> Rule of the build: **Python computes every number. The LLM only phrases, splits claims and reads images.** Everything the demo shows is precomputed and frozen.

---

## 1. Architecture

```
generator/  batch CLI ──writes──▶ artifacts/roll_v1.parquet, roll_v2.parquet, context/*.csv
engine/     batch CLI ──reads/writes──▶ artifacts/flags.json, stories.json, eval.json, cards.json
api/        FastAPI, one process, :8000
              serves artifacts from memory (pandas)
              llm.py  = one client + disk cache + Neutrality Guard + template fallback
              claims.py = splitter → fixed tool menu → deterministic verdict
              citizen.py = search + status + next steps (+ Sarvam voice)
bot/        python-telegram-bot, long polling, thin client of api/ (no logic)
web/        Next.js 15 (App Router), client components only, fetches http://localhost:8000
cards/      share-card PNGs rendered by headless Chrome from web /card/[id]
```

- **One brain, two surfaces:** the bot and the web chat both call `/citizen/ask` and `/claims/check`.
- **The engine is batch, not a live service.** `POST /engine/run` re-runs it on the frozen roll in about 5 s and returns identical flags.
- **Where the LLM appears (only these 5 places):**
  1. flag-card phrasing (batch)
  2. claim splitting (live, cached)
  3. screenshot reading (live, cached)
  4. citizen answer phrasing (live, cached, template fallback)
  5. guard rewrite

### 1.1 Engineering depth: complexity, scale and cost (v3, judge-facing)

Every algorithm has a stated complexity and a measured number. Both go on the Trust page (M11) and in the README. Measure them, don't estimate.

| Step | Approach | Complexity | Show on stage |
|---|---|---|---|
| Roll diff | hash join on `voter_id` (pandas merge) | O(n) | time for 50k and for 1M |
| Booth tests | binomial per booth + Benjamini-Hochberg | O(m log m), m = 100 booths | q-values in the flag card |
| Cross-script duplicates | **blocking** on (booth, house) and (booth, relation prefix) → score pairs inside blocks → **union-find** | O(Σ bᵢ²) instead of O(n²); union-find ≈ O(α(n)) per merge | "pairs scored: 0.4M instead of 1.25B" (use the real count) |
| Story attribution | dictionary lookups per removed record, in a fixed order | O(r) per booth | instant toggle |
| Bootstrap CI | 500 resamples, vectorised with numpy | O(B·r) | "500 resamples in < 50 ms" |
| Claim tools | precomputed aggregates per booth/ward, O(1) lookups | O(1) per sub-claim | the query chip |

**Scale run (S10).** `python -m generator --households-scale 20 --seed 11` gives about 1M voters. `python -m engine.run --bench` prints the wall time per stage and the pair counts to `artifacts/bench.json`. If the generator is too slow at 1M, scale by cloning the 100 booths with new IDs: that's still a fair test of the engine.

**Request log → ops strip (M11).** A FastAPI middleware appends `{route, ms, llm_tokens_in, llm_tokens_out, model, cache_hit}` to `artifacts/ops.jsonl`. `/ops` returns p50, p95, ₹ per claim check (tokens × the current per-token price in `constants.py`) and the cache hit rate.

**Claim Court is a tool-use agent with a typed tool menu.** Claude plans which of the ~9 tools to call and with which parameters, and it may call several. **Code executes every tool and code computes the verdict.** "The agent plans, code decides": that's the one-line answer to "isn't this a GPT wrapper?"

## 2. Environment

| Item | Choice |
|---|---|
| Python | `uv venv --python 3.12 .venv` (3.12.13 is already in uv). **Never use the system 3.14.** |
| Python packages | `numpy<2.3 pandas pyarrow scipy statsmodels scikit-learn rapidfuzz jellyfish indic-transliteration fastapi uvicorn pydantic>=2 python-telegram-bot>=21 httpx anthropic google-genai python-dotenv qrcode pillow`. **No torch.** Run `uv pip freeze > requirements.lock` at H0. |
| Node | Node 24 + **pnpm** only. Next 15, Tailwind v4, shadcn (restyled per the [design system](DESIGN_SYSTEM.md)). |
| Fonts | Self-hosted in `web/public/fonts`: Geist, Geist Mono (from the `geist` npm package or Vercel's GitHub release), Noto Sans Devanagari, Noto Sans Gurmukhi. **Not `next/font/google`**, because it fetches at build time. |
| Encoding | `PYTHONUTF8=1` in `.env`. Pass `encoding="utf-8"` to every `open()` and `ensure_ascii=False` to every `json.dump`. |
| Ports | API 8000, web 3000. Each worktree adds 10 to both. |
| `.env` | `ANTHROPIC_API_KEY, GEMINI_API_KEY, SARVAM_API_KEY, TELEGRAM_BOT_TOKEN, PYTHONUTF8=1, DEMO_MODE=0, SEED=42` |
| LLMs | Claude (`claude-sonnet-5-5`) for splitting and vision; `claude-haiku-5-5` for phrasing. Temperature 0 and JSON via tool use. Gemini as fallback. |
| Voice | Sarvam STT (saaras) and TTS (bulbul) with `hi-IN`, `pa-IN`, `en-IN`. Convert OGG to 16 kHz mono WAV with ffmpeg first. Verify the model names and the audio length cap at H0. |

## 3. Data contracts (`contracts/models.py` is the single source)

Pydantic models are exported to `contracts/*.schema.json`, and from there to `web/lib/types.ts` via `json-schema-to-typescript`. **Only the contract owner (Rishabh) changes contracts.**

### 3.1 RollRow (`roll_v1.parquet`, `roll_v2.parquet`)
```
voter_id: str          # "SBD1234567". The same person keeps it across v1/v2.
                       # Duplicates get DIFFERENT ids. Modified records keep theirs.
roll_version: "v1"|"v2"
ward_id: str           # W01..W10
booth_id: str          # B001..B100
serial_no: int
house_no: str
name_dev: str          # Devanagari
name_lat: str          # Latin as printed (spelling variants allowed)
relation_type: "father"|"husband"|"mother"|"other"
relation_name_dev: str
relation_name_lat: str
age: int
gender: "M"|"F"|"T"
```
**Context tables** (`artifacts/context/`):
- `death_register.csv`: `booth_id, house_no, name_lat, age, date`
- `hostel_list.csv`: `booth_id, house_no, capacity, academic_year_end`
- `boundary_changes.csv`: `change_id, from_booth, to_booth, house_from, house_to, effective_date`

**Private answer key** (in `private/`, gitignored, owned by the partner): `[{plant_id, type, is_benign, booth_id, voter_ids[], note}]`.

### 3.2 Flag
```
flag_id: str                     # sha256(type+scope+evidence)[:12]
type: "deletion_spike"|"addition_spike"|"duplicate_cluster"|"impossible_age"
    |"relation_conflict"|"oversized_household"|"gender_ratio_swing"
scope: {level: "booth"|"household"|"record", booth_id, house_no: str|null, voter_ids: [str]}  # voter_ids never rendered
metrics: {observed, expected, n, p_value, q_value, unit}
reason_codes: [str]              # DEL_RATE_GT_EXPECTED_BH05, XSCRIPT_NAME_MATCH, SAME_RELATION_SAME_HOUSE …
stories: StoryResult | null      # §4.2, deletion/addition spikes only
confidence: float                # calibrated P(true non-benign anomaly)
confidence_band: "low"|"medium"|"high"
confidence_n: int                # how many training plantings back this estimate
likely_benign: bool
needs_human_review: true
card: {found, why_unusual, innocent_explanations: [str], confidence_text, lang} | null
guard: {passed, blocked_terms: [str], rewritten: bool}
review: {status: "open"|"benign"|"escalated", ts, hash} 
```

### 3.3 StoryResult
```
stories: [{code: "death_registered"|"hostel_moveout"|"boundary_change"|"duplicate_cleanup"|"unexplained",
           label: str, count: int, share: float, ci_lo: float, ci_hi: float, evidence: str}]
residual: {count, expected_background, p_value, significant: bool}
context_used: [str]              # which context tables were switched on
outcome: "unusual"|"likely_benign"|"mixed"
```

### 3.4 ClaimVerdict
```
claim_id: str
input: {text, source: "text"|"image", lang: "hi"|"en"|"pa"}
normalized_claim: str            # neutral restatement, guard-checked
sub_claims: [{id, text,
  tool: "deletion_count"|"deletion_rate"|"addition_count"|"duplicate_count"|"age_distribution"
       |"gender_ratio"|"compare_booths"|"story_shares"|"unanswerable",
  params: {}, query_shown: str,           # human-readable query, e.g. "count deleted where booth=B047"
  claimed_value: float|null, computed_value: float|null, tolerance: float,
  verdict: "verified"|"disputed"|"unprovable",
  reason: str, evidence: {series: [{label, value}], note}, confidence: float,
  settle_with: str|null}]
overall: "verified"|"disputed"|"unprovable"|"mixed"
confidence: float
mirror: {claim_text, sub_claim_verdicts: [str], identical_treatment: bool} | null
card_png: str|null               # /cards/{claim_id}.png
guard: {...}, cached: bool
```

### 3.5 API (`contracts/api.md`)
```
GET  /health                     {ok, demo_mode, versions}
GET  /overview                   {totals:{v1,v2,added,deleted,modified}, booths:[{booth_id, ward_id, n_v1, n_v2, del_rate, expected_del_rate, q_value, flag_count, outcome}]}
GET  /flags?type=&booth_id=&band=&likely_benign=   {items:[Flag], total}
GET  /flags/{id}                 Flag
POST /stories/{booth_id} {context_on:[str]}        StoryResult   # the live toggle
POST /engine/run                 {flags_total, by_type, runtime_ms}
GET  /eval                       {by_type:[{type,tp,fp,fn,precision,recall}], decoys_cleared, benign_fp_rate, reliability:[{bin_lo,bin_hi,mean_conf,frac_true,n}], misses:[{plant_id,type,why}]}
GET  /rules                      [{rule_id, what, fires_on_benign_rate, innocent_explanations, resolves_with}]   # S4/S5
GET  /search?q=&booth_id=        {matches:[{voter_id, name_dev, name_lat, booth_id, status_v2, score}], query_normalized}
POST /citizen/ask {text?, audio_b64?, lang?, channel}  {lang, transcript?, answer_text, answer_audio_url?, status, reason_category, next_steps:[str], confidence, guard}
POST /claims/check {text?, image_b64?, mirror:true}    ClaimVerdict
POST /review/{flag_id} {status, note}                  {review, audit_hash}
GET  /audit/log                  [{ts, flag_id, action, hash, prev_hash}]
GET  /guard/log                  {checked, blocked, rewritten, items:[...]}
GET  /report                     data for the print page
```

## 4. Engine algorithms

### 4.1 Booth deletion test
- **Expected deletions** per booth: `Σ_age-band n_band × p_band`. `p_band` is the district-wide background removal rate by age band, taken from the generator's churn model and documented as "fitted to the SRS age-specific death rate shape plus a migration rate".
- **Test:** `scipy.stats.binomtest(observed, n_v1, p_expected, alternative="greater")`, then `statsmodels.stats.multitest.multipletests(p, method="fdr_bh")`.
- **Flag** a booth when q < 0.05. Additions get the same test, mirrored.

### 4.2 "Which Story Fits?" (the hero). Deterministic attribution, then a residual test
1. **Removed set:** take every record in v1 and not in v2 for the booth.
2. **Attribute** each record to the first story whose evidence matches, in this order:
   - `death_registered`: same booth, house_no and normalised name, with age within ±2 in the death register.
   - `duplicate_cleanup`: the record belonged to a v1 duplicate cluster and another member survives in v2.
   - `boundary_change`: the house_no falls in a `boundary_changes` range from this booth, and the record reappears in the `to_booth` in v2.
   - `hostel_moveout`: the house_no is in `hostel_list` and the age is 18–25.
   - otherwise `unexplained`.
3. **Shares with a 90% bootstrap CI:** 500 resamples of the removed set. It is cheap, and say so on stage.
4. **Residual test:** a binomial test of the `unexplained` count against the expected background deletions. If it is significant (q < 0.05), the outcome is `unusual`. If not, and one innocent story's share is at least 60%, it is `likely_benign`. Otherwise it is `mixed`.
5. **Live toggle:** `POST /stories/{booth}` re-runs steps 2–4 with selected context tables switched off. This shows *why* the system believes what it believes.

### 4.3 Cross-script duplicates
- **Blocking:** pairs are only compared within the same (booth, house_no), or the same (booth, first 3 characters of the normalised relation name).
- **Normalise:**
  - convert Devanagari with `indic_transliteration` to ITRANS, then lowercase
  - strip diacritics
  - `aa→a, ee/ii→i, oo/uu→u, w→v, ph→f, sh→s, z→j`
  - drop a final schwa `a` and collapse double letters
- **Score:** `0.5·JaroWinkler(name) + 0.3·token_set_ratio(relation) + 0.2·(metaphone equal)`, plus same-age-±1 and same-gender gates. Threshold 0.88, tuned on the fixtures.
- **Cluster:** union-find into clusters. Emit a flag only for clusters of 2 or more.
- On the slide, call it "character-n-gram similarity". **No embeddings.**

### 4.4 Rule checks
`age<18 | age>110` → `impossible_age`. A household of more than 15 → `oversized_household`. A booth gender ratio that changes by more than 8 points between versions → `gender_ratio_swing`. `relation_conflict` only when the relative's own record is found in the same house; the card says so.

### 4.5 Confidence
- **Training data:** the generator also writes a **training district** (`SEED=7`) with random auto-plantings.
- **Model:** fit a **Platt** curve per flag type (logistic, 2 parameters) mapping the raw score (−log10 q, or the match score) to P(true anomaly).
- **Display:** show `confidence` as a % plus a band (low < 0.5 ≤ medium < 0.8 ≤ high), with `confidence_n`.
- **Reliability chart:** plotted only on the partner's **blind** plantings, in 3–4 bins with counts. If it isn't diagonal, say so.

### 4.6 Blind evaluation
- The partner writes `private/planting_config.yaml`, which sets per booth: the type, size, and whether the planting is benign.
- The partner runs `python -m generator --config private/planting_config.yaml` and commits only the roll and context CSVs.
- At the checkpoint, the partner runs `python -m engine.eval --key private/answer_key.json` → `artifacts/eval.json`. Rishabh never opens `private/`.

## 5. Claim Court

1. **Input.** The input is text, or an image. For images, a vision call returns `{text, lang}`.
2. **Party and person names → placeholders** (`[GROUP A]`, `[PERSON]`) before anything else runs.
3. **Split.** One LLM tool call returns `sub_claims[{text, tool, params, claimed_value}]`, and the tool must come from the fixed menu (§3.4). **The LLM never writes code.**
4. **Hard rules applied after the split (in code, not in the prompt):**
   - Intent/motive words (`targeted, deliberately, rigged, conspiracy, साजिश, जानबूझकर …`) → `unanswerable`, with reason "motive can't be measured from roll data".
   - Religion, caste or community → `unanswerable`, with reason "we never infer religion, caste or community from names".
   - Real place names outside Sampleabad → `unanswerable`, with reason "this tool only has data for the demo district".
5. **Execute** each tool against the frozen roll and keep `query_shown`.
6. **Verdict rule (deterministic):**
   - `|claimed − computed| ≤ tolerance` (default 15% relative) → **verified**
   - otherwise → **disputed**
   - no claimed value, or `unanswerable` → **unprovable**
   - **Confidence** comes from the margin against the tolerance and from n.
7. **Mirror.** Flip the direction (deleted ↔ added, booth A ↔ the paired booth), re-run, and compare the verdict structure. Never label anything by political side.
8. **Phrase** each verdict (LLM, cached), run it through the guard, and render the card.

**Share card (M9).** Web route `/card/[claim_id]`, 1080×1350. The bot replies with the PNG into the same chat, and with S11 into the same group. Render it with headless Chrome:
`chrome --headless=new --screenshot=cards/{id}.png --window-size=1080,1350 http://localhost:3000/card/{id}`.
Chrome shapes Devanagari correctly; Pillow and satori don't. Precompute cards for every scripted claim.

**Share clip (S9).** Render 4 states of `/card/[id]?step=0..3` (claim only → +verified → +disputed → +cannot be proven) with headless Chrome, then
`ffmpeg -framerate 1/2 -i cards/{id}_%d.png -vf "fps=30,format=yuv420p,pad=1080:1920:0:285:color=F9F9F9" cards/{id}.mp4`. Add Sarvam TTS audio if S3 is done.

## 6. Neutrality Guard
Layers, applied to every **generated** string. Fixed procedural templates in `api/constants.py`, such as official portal names, are exempt and allowlisted.
1. **Structural:** the LLM only sees computed JSON, and no schema has an actor field.
2. **Lexicon + regex** (`api/guard_lexicon.yaml`), all in EN, HI and PA:
   - fraud/rigging words
   - party names and abbreviations
   - institution names
   - person names from the generator's name list plus a public-figures list
3. **If blocked:** one LLM rewrite ("rewrite neutrally, no actors, keep numbers"), then re-check. If it still fails, use the template.
4. **Log** every check to `/guard/log`. The UI shows "Neutrality check: 1,284 outputs · 0 violations shipped · 17 rewrites".

## 7. Citizen assistant
- **Language detection:** by script (Devanagari → hi, Gurmukhi → pa). For Latin script, the LLM classifies "hinglish" vs English.
- **Search:** the same normaliser as §4.3 against the name and relation name. A booth number or age narrows the results. Return the single best match only, with its score.
- **Status:** present / modified / not in the new list, with a reason category from the stories (shifted, death registered, duplicate clean-up, boundary change, unexplained → "please check with your BLO").
- **Next steps** come from a template per status, in `constants.py`. **Verify every form number on voters.eci.gov.in at H0.**
  - Form 6: new or re-inclusion.
  - Form 7: objection or deletion.
  - Form 8: shift or correction.
  - Helpline 1950.
  - "A BLO never asks for an OTP or money."
- **Voice (S3):** Telegram voice → ffmpeg → Sarvam STT → same flow → Sarvam TTS → reply as a voice note. TTS for the scripted replies is pre-generated.

## 8. Demo mode and resilience
- `DEMO_MODE=1`: the API serves only `artifacts/` plus `cache/llm/` (keyed by `sha256(model+prompt+input)`), and any cache miss falls back to the template.
- **Freeze:** at feature freeze, commit `artifacts/` plus the cache and tag `demo-v1`. Demo from `next build && next start`, never from dev.
- **Telegram:** long polling, tested at H0 on venue Wi-Fi and then on the hotspot. The web chat is the fallback for every bot beat.

## 9. Testing policy: ship first
No test suite and no frontend tests. **Five smoke checks**, in one file `smoke_test.py`, run in under 10 s against `contracts/fixtures/`:
1. The cross-script duplicate in the fixture is clustered.
2. The fixture hostel move-out comes out `likely_benign`.
3. The guard blocks 5 seeded bad strings (fraud word, party name, person name, HI and PA variants).
4. The claim verdict rule maps claimed vs computed as expected (one verified, one disputed, one unprovable).
5. The API boots and `/overview` returns 100 booths.

Also run `next build` once at each merge. The real test is **the demo script run end to end**.

## 10. Folder ownership

| Folder | Owner (human / session) |
|---|---|
| `contracts/`, `CLAUDE.md` | Rishabh (A) only |
| `generator/` | A1 |
| `engine/` | A2 |
| `api/` | A1 after the generator is done |
| `web/` | B1 |
| `bot/` | B2 |
| `private/` | Partner (B) only, gitignored |
| `artifacts/`, `cache/` | Written by scripts, committed at the freeze |
