# RollWatch: pitch prep

Three parts: **(A)** the prompt that makes the deck, **(B)** a brief so either of us can explain anything, **(C)** the questions we're likely to get, with short answers. Every number here is real engine output (seed 42, 28 Oct). Recheck on `/trust` before going on stage.

---

## A. Prompt for Claude to make the presentation

Paste everything in the box into Claude (claude.ai, with the Slides or Design artifact type if offered). Attach 3–4 screenshots: home hero, the Booth 47 story bar, Claim Court verdict rows, and the Trust scoreboard.

```
Make a 7-slide pitch deck for RollWatch, a hackathon project (X AI Tech Ideathon, PS1: AI for Electoral Roll
Transparency, Team Nova, IDEAS-175). The talk is 4 minutes; each slide carries ONE headline and ONE visual and we
talk over it. No paragraphs on slides.

WHAT ROLLWATCH IS
RollWatch compares two versions of a voter roll and tells you which story each removal fits (a registered death,
a duplicate cleanup, a boundary move, a hostel move-out, or "unexplained"), how sure it is, and that a person must
review it. It checks viral claims about the roll part by part, and tells any voter why their own name changed and
which form to file, in Hindi, English and Punjabi, with voice, on web, Telegram and WhatsApp.
All data is synthetic: a fictional district "Sampleabad", 100 booths, ~51,000 voters. No real voter data.

REAL NUMBERS (use exactly these, never invent others)
- Booth 47: 412 names removed against ~25 expected; 97% fit no innocent story -> "needs human review".
- Booth 12: 390 removed; 79% match a hostel move-out -> "likely benign". To a rumour, both look the same.
- Booth 63: 64% unexplained -> 8% when the boundary-change log is switched on.
- Claim "Booth 47 mein 600 naam kaat diye, sabse zyada, aur sab ek community ke!" -> 600: DISPUTED (computed 412,
  46% off) · "most removals": VERIFIED (rank 1 of 100) · "community": CANNOT BE PROVEN (we never infer it).
  The opposite claim is checked with the same tools and tolerance (mirror test).
- Blind-test style scoreboard on planted data: 6 of 6 anomalies found, 7 of 7 innocent decoys cleared, 0 missed.
- Calibration: when we say ~93%, flags are right 90% of the time.
- Scale: 1,020,720 voters in 54 s on ONE laptop core. Duplicate search scores 9.9 million candidate pairs instead
  of 521 billion (blocking + union-find).
- Cost: ~Rs 0 per check (free tier or the user's own key; cached answers cost nothing).

SLIDES
1. Title: "Every change to a voter roll, explained." grey second half: "And every rumour about it, checked."
   Small: RollWatch · Team Nova · IDEAS-175.
2. The problem: after every roll revision, thousands of names change and forwards like "600 names cut from one
   booth" spread in hours. Nobody can check them; official discrepancy flags publish no error rates.
   Visual: the forward as a chat bubble, then three verdict chips.
3. How it works: one left-to-right diagram. Roll v1 + v2 -> Python engine (diff, binomial test + Benjamini-
   Hochberg, cross-script duplicates, "which story fits") -> numbers + confidence -> LLM only phrases words ->
   neutrality guard -> web / Telegram / WhatsApp / share card. Label clearly: "every number comes from code".
4. Proof it works: Booth 47 vs Booth 12 story bars side by side (unexplained part in hatched yellow), plus the
   scoreboard 6/6 found · 7/7 decoys cleared · 0 missed.
5. THE THREE QUESTIONS (mandatory, one slide, three columns, each with a number or artefact):
   - How it scales: per-booth and linear; 1.02M voters in 54 s on one core; 9.9M pairs not 521B; spreads as
     share cards inside chat apps, no install; same method fits any "cleaned" list (ration cards, pensions).
   - Why the government can't do it alone: a self-audit can't settle a rumour about the auditor. Two ways in from
     one open engine: inside, an election office runs POST /audit on the draft before publishing; outside,
     newsrooms and citizens run the same code, so both sides agree on the arithmetic.
   - Why it's future-proof: core fixed and measured; data (adapters to an open schema), rules (YAML), model
     (swappable, never makes a number, template fallback), languages and channels are swappable parts. We swapped
     the model and the voice in an afternoon. Every change is re-measured by the blind eval.
6. Trust: never infers religion, caste or community; no party/person/institution names in any output (guard log);
   mirror test; every output says "needs human review"; published error rate per rule.
7. Limits + ask: synthetic data; recalibrate on real rolls; real-roll PDF ingestion is roadmap; not affiliated with
   any official body. Ask: pilot with one newsroom data desk or election-watch NGO during the next revision.
   Live: rollwatch-web.onrender.com · Telegram @Rollwatch_bot.

DESIGN (strict)
- Look: butter.video-inspired "engineered calm". Near-white page #F9F9F9, grey panels #EDEDED with 28px radius,
  white cards inside. Text #0F0F0F, secondary #5C5C5C, grey half of headlines #9A9A9A.
- Type: Geist (regular weight 400, never bold headlines, tracking -0.035em), Geist Mono for numbers and small
  sentence-case eyebrows ending in a period ("Which story fits."). Two-tone headlines: black clause, grey clause.
- Colour only as small signal chips: yellow #F6D84D = needs human review / unexplained; mint #1CC691 = verified;
  magenta #D61F69 = disputed (white text); periwinkle #B8C7FF = likely benign; dashed grey = cannot be proven.
  The ONLY pattern allowed is a yellow/black diagonal hatch for "unexplained".
- Light only. NO dark slides, gradients, shadows, glows, stock photos, emoji, icon libraries, robots, brains,
  sparkles, saffron or tricolour combinations, party colours or election symbols.
- Copy never says "AI-powered", "smart", "magic", "revolutionary", "seamless", "unlock". It never uses fraud or
  rigging words or names any party, person or institution. State what happened, with numbers.
- Leave a blank square top-left for our logo (we add it). 16:9.
```

---

## B. The brief: what to know cold

**One sentence.** RollWatch tells you which story a voter-roll change actually fits, how sure it is, and sends the answer back to where the rumour came from, in three languages, taking no side.

**The pipeline** (say it in this order):
1. **Diff.** Compare roll v1 and v2 by voter id: who was removed, added or moved. First we remove the roll-wide ageing shift (everyone is a year older).
2. **Is the booth unusual?** For each booth we expect a background removal rate from its age mix (older people die more, young people migrate more). A one-sided binomial test asks whether removals beat that. Benjamini-Hochberg corrects for testing 100 booths at once.
3. **Which story fits?** Each removed record is checked, in a fixed order, against evidence: the death register, a duplicate still in the roll, the boundary-change log, the hostel list. Whatever no record explains is "unexplained". Then we test whether *that leftover* is still above background, with a 500-resample bootstrap interval.
   - **Unusual** = the leftover is still too high. Needs human review (Booth 47).
   - **Likely benign** = the removals are high, but one record explains most of them, and what's left is no more than a normal booth loses (Booth 12 hostel, Booth 22 hostel). Still says "needs human review", because a person should confirm.
   - **Mixed** = several records together explain it (Booth 63: deaths plus a boundary move).
4. **Other rules:** cross-script duplicates (the same person in Devanagari and Latin, blocked by booth/house, scored with Jaro-Winkler + metaphone + relation name, merged with union-find), impossible ages, more than 15 electors in one house, gender-share swings, impossible relations (a parent not older than the child).
5. **Confidence:** a Platt curve per rule, fit on a *separate* training district with its own answer key. Stated ~93% → right 90% of the time.
6. **Words:** the LLM (Gemini) only splits a claim into sub-claims, reads screenshots and phrases text. Python computes every number. Everything outbound passes the neutrality guard, and procedural text (forms, helpline 1950) comes from a fixed constants file.

**The surfaces:**
- **Audit** (home): booth grid, which-story bars, evidence on/off toggles.
- **Check:** Claim Court. Paste a forward or drop a screenshot; it's split into sub-claims and each runs a fixed query (shown on screen). You get Verified / Disputed / Cannot be proven, plus the mirror claim and a share card with a QR code.
- **Ask:** citizen lookup in any script or spelling. Status, reason, Form 6/7/8, 1950, "a BLO never asks for an OTP or money", Hindi voice.
- **Trust:** scoreboard, reliability, the guard, error rate per rule (including 7 official discrepancy checks, 81–100% innocent on our data), human reviews in a hash chain, ops (latency, ₹ per check), the 1M-voter bench.
- **Run it:** drop two roll CSVs (or the 10-booth sample) and get the audit in about 3 s. This is the "inside the government" path.
- **Share card PNG:** every checked claim becomes a 1080×1350 image the bots send back into the chat.
- **WhatsApp voice:** send a Hindi voice note and get the answer as text and audio.
- **Bots:** Telegram and WhatsApp share one brain (`bot/core.py`). WhatsApp also handles sign-in codes.
- **Account:** sign in with a WhatsApp code, then save checks and watch booths (Supabase).
- **Bring your own key:** paste your own Gemini or ElevenLabs key; it stays in the browser.

**Stack:** Python 3.12 (pandas, rapidfuzz, jellyfish, indic-transliteration, scikit-learn), FastAPI, Next.js 15, Gemini, ElevenLabs, Supabase (database only, RLS on), Baileys (WhatsApp), Telegram, Docker on Render.

**What's real vs synthetic.** The district, names and rolls are synthetic, generated with seeded randomness and planted anomalies plus innocent look-alikes. The method, code, statistics and every number on screen are real.

**Honest limits:**
- The blind test (a teammate's hidden plantings) is still to run.
- The removal-spike confidence curve rests on 20 training flags.
- Real rolls are per-part PDFs; PDF ingestion is roadmap.
- Free hosting sleeps after 15 minutes, so the first load takes about a minute. Open the site before you go on.

---

## C. Questions we'll probably get

**Depth / "is it a wrapper?"**
- *Is this just a Gemini wrapper?* No. Turn the model off and every verdict is the same: the engine is plain Python and the template fallback phrases the text. The model only splits sentences and words the answer, and every row shows the query that produced its number.
- *What does AI add beyond SQL?* Turning a free-text rumour (Hinglish, a screenshot) into checkable queries, matching one person across scripts and spellings, and explaining statistics in three languages without inventing numbers.
- *Why a binomial test?* Each voter is either removed or not, with a known background probability from the booth's age mix. That's exactly a binomial. Benjamini-Hochberg keeps false alarms in check across 100 booths.
- *Why not O(n²) duplicate matching?* 51k voters would be 1.3 billion pairs. Blocking by booth/house and relation name cuts that to about 500k candidates, and union-find merges matches. At 1M voters: 9.9M pairs instead of 521B.
- *What does "93%" mean?* Of flags we stated at about 93%, 90% matched a planted anomaly. The curve was fit on a separate training district, not on the one we score.

**"Likely benign" and the stats**
- *What does "likely benign" mean?* The booth lost more names than expected, but a record explains most of them, and what's left is no more than a normal booth loses. Example: Booth 22 lost 87 against ~21 expected, and 70 of the 87 were students leaving a listed hostel at the end of the academic year. It still says "needs human review".
- *Couldn't you hide a real problem inside a benign booth?* If the leftover after the innocent stories is itself above background, the booth stays "unusual". Booth 47 has 10 real deaths *and* 401 unexplained removals, and it's flagged.
- *What if the death register itself is wrong?* Then the story is wrong too, and the evidence toggles show it. Switch a source off and watch the leftover move. We show which records explain what, never a bare verdict.

**Data and privacy**
- *Synthetic data proves nothing?* It proves the method, measured against a known answer key, which real data can't give you. The blind test with hidden plantings is the next step, and real deployment needs recalibration.
- *Do you infer religion or caste?* Never. Rolls don't contain them and we won't guess from names, so any claim that needs them returns "cannot be proven", with the reason.
- *How would real data get in?* Rolls are published per polling part. A newsroom or observer runs it locally on rolls they already get legally, through an adapter to our open schema. Public outputs are booth-level, and auditor views mask names.
- *Couldn't a card be misused as "AI proves deletions"?* Every card says "pattern for human review, not a finding", shows the innocent explanations and the query, and never shows a voter's name.

**Official checks**
- *Why not just use the official "logical discrepancy" rules?* We ran the seven that a roll can support (parent gap under 15 or over 50, six or more children, name, relative or relation changed, age not progressing). On our district they trip 81–100% innocent records: marriages, spelling fixes, big families. That's synthetic data, but the logic holds: a rule that can't tell a marriage from an anomaly needs a published error rate and a "which story fits" step before anyone gets a notice. Reported scale: about 1.3 crore electors flagged in West Bengal, and 91% of decided appeals there restored the voter (sources: The News Minute on Karnataka's criteria, Internet Freedom Foundation analysis of SIR exclusions).
- *Can you check siblings born under 9 months apart?* Not from a roll: it lists age in whole years, not birth dates. We'd need the date of birth, and we say so instead of guessing.

**Neutrality**
- *Isn't the guard just a regex?* It's three layers. The model sees only computed numbers, our schemas have no field for parties or people, and a final check blocks or rewrites, logs it, and falls back to a template. The mirror test is the behavioural proof: the opposite claim gets identical treatment.
- *What if someone asks about a specific party?* The answer drops the name and sticks to the numbers. If the claim depends on who did it, that part is "cannot be proven".

**The three questions**
- *How does it scale?* Every test is per booth, so a state is just more booths, run in parallel. 1.02M voters takes 54 s on one core. Adoption spreads as cards inside the chat the rumour came from, with no install. Scope: any "cleaned" list, like ration cards or pensions.
- *Can't the government do this?* They should, and `POST /audit` is built for it: run it on the draft before publishing. But a self-audit can't settle a rumour about the auditor, so the same open engine must also be in independent hands. Then both sides agree on the arithmetic.
- *Is it future-proof?* The core is fixed and measured. Data, rules, model, language and channel are each swappable. We swapped the model and the voice in an afternoon, and the blind eval re-measures every change.

**Product and money**
- *Who uses it?* First, data desks and election-watch NGOs during revision windows. Then citizens, through the bots.
- *Who pays?* An open-source core, a hosted version for NGOs on civic-tech grants, and a free citizen bot. Bring-your-own-key means heavy users carry their own model cost.
- *Cost and speed?* About ₹0 per check today (free tier, cache). Engine routes answer in about a millisecond. Live numbers are on the Trust page ops strip. The first request after the server sleeps is slow, which is a free-hosting cold start.
- *Why would a voter trust you over the official app?* We don't replace it. The official app says *whether* you're listed; we say *why* you changed and *what to do*, in voice and Punjabi, and we hand off to the official portal and the 1950 helpline.

**Team and build**
- *Did AI write the code?* We used Claude Code heavily and say so in the README. The design, the statistics, the evaluation and the review are ours, and either of us can walk through any function.
- *What would you do with another week?* Run the blind test, add more training districts for confidence, PDF ingestion for one real constituency (aggregates only), and WhatsApp voice notes.

**If the demo breaks:** restart the API with `DEMO_MODE=1`, which serves the same cached answers with no network. Keep the 33 s film (`web/public/rollwatch-film.mp4`) open in a tab as a backup.
