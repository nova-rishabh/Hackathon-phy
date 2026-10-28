# RollWatch: Phase 2 deck prompt (for Claude Design)

How to use: open Claude Design, attach the screenshots listed at the bottom (from `deliver/deck-screens/`) and the two logo files (`web/public/logo-word.png`, `web/public/logo-mark.png`), then paste everything inside the box. Every number below was read from the live API on 28 Oct 2026 (seed 42). If the engine is rerun, recheck `/trust`, `/eval/blind` and `/simulate/limits` first.

```
Make the final-round pitch deck for RollWatch. 16:9. A main deck of 13 slides (about 6 minutes of talk) plus
6 backup slides for questions. Each slide carries ONE headline and ONE visual; we talk over it. No paragraphs.

====================================================================================================
WHO WE ARE
Team Nova (IDEAS-175) · X AI Tech Ideathon, 27-28 Oct 2026 · PS1: AI for Electoral Roll Transparency.
Two people built it in about 30 hours. It is live:
  web  rollwatch-web.onrender.com   ·  WhatsApp +91 80764 99841  ·  Telegram @Rollwatch_bot
  API  rollwatch-api.onrender.com

WHAT ROLLWATCH IS (one breath)
RollWatch compares two versions of a voter roll and tells you which story each removal fits (a registered
death, a duplicate cleanup, a boundary move, a hostel move-out, or "unexplained"), how sure it is, and that a
person must review it. It checks viral claims about the roll part by part and sends the verdict back into the
chat as an image. It tells any voter why their own name changed and which form to file, in Hindi, English and
Punjabi, with Hindi voice, on web, WhatsApp and Telegram.
Line for the room: "Every team can flag a spike. We tell you which story the spike fits, and we prove we're
not guessing."

All data is synthetic: the fictional district "Sampleabad", 100 booths, 51,036 voters before and 49,675 after
(2,966 removed, 1,605 added, 747 changed). No real voter data. It never infers religion, caste or community.

====================================================================================================
NUMBERS (use exactly these; never invent, round up or combine numbers)

Audit
- Booth 47: 412 removed against about 25 expected. 10 match the death register, 1 a duplicate cleanup,
  401 (97%) match no record -> UNUSUAL · NEEDS HUMAN REVIEW.
- Booth 12: 390 removed. 308 (79%) match a hostel move-out, 60 deaths; 21 left against about 39 expected
  -> LIKELY BENIGN. To a rumour, Booth 47 and Booth 12 look the same.
- Booth 63: 154 removed. Boundary log off: 99 (64%) unexplained -> unusual. Boundary log on: 86 explained by
  a boundary move, 13 (8%) left -> MIXED, no longer unusual. "Switch a source off and watch the answer move."

Claim Court (live result)
- Forward: "Booth 47 mein 600 naam kaat diye, sabse zyada, aur sab ek community ke!"
  - "600 names": DISPUTED. Computed 412, 46% off, outside the 15% tolerance.
    Query shown: count v1 records where booth=B047 and voter_id not in v2
  - "the most of any booth": VERIFIED. Rank 1 of 100.
  - "all one community": CANNOT BE PROVEN. We never infer religion, caste or community from names.
  - How sure: 86%. Mirror claim ("600 names added in Booth 30") is checked with the same tools and tolerance.
  - The verdict becomes a share image (1080x1350) sent back into WhatsApp/Telegram, and a shared link previews
    as its own verdict card.

Blind test (planted by a separate AI agent; we never saw the key)
- 9 of 9 planted anomalies found. 6 of 6 innocent look-alikes cleared. 0 missed.
- False alarms, counted: of 283 flags raised for review, 263 were real (93%). 0 false alarms on booth
  removal or addition spikes (the flags a rumour is built on). The 20 false ones are record-level: 14 duplicate
  pairs, 6 relation conflicts. 11 more the engine marked "likely innocent" itself; none hid a planted anomaly.
- Calibration: flags stated at about 94% were right 93% of the time (280 flags).

Try to fool it (live on the Trust page; the engine reruns its own tests)
- A booth needs a median of 19 hidden names (about 4% of the booth; 8 to 40 across booths) to reach review.
- Booth 23: hide 17 names -> a spike shows but it is not sent to review. Hide 18 -> sent to review.
- Honest blind spot: spread 1,000 names over all 100 booths (10 each) -> 58 booths show a spike, but only 2
  new booths reach review. Per-booth tests can't see a few names per booth. We show this before anyone asks.

Official checks (the 2025-26 revision's "logical discrepancy" checks, run on our district, never raised)
- parent under 15 or over 50 years older: 113 trips, 81% innocent
- six or more children of one parent: 166 trips, 98% innocent
- own name changed: 196, 100% innocent · relative's name changed: 323, 100% · relation type changed
  (marriage): 183, 100% · age didn't progress: 44, 100% · grandparent under 40 years older: 0
- Footnote: synthetic rates. Point: a check without a published error rate creates notices and fear.
- Real-world context (sourced): about 1.3 crore electors flagged as discrepancies in West Bengal; 91% of decided
  appeals there restored the voter (The News Minute; Internet Freedom Foundation).

Scale
- Engine: 10,20,720 voters in 53.9 s on ONE laptop core (the 51,036-voter district in 2.5 s).
  Duplicate search scores 9.9 million candidate pairs instead of 521 billion (blocking + union-find).
- All of India (ECI Lok Sabha 2024 state table, 97.8 crore electors): 14.4 core-hours = 13.5 minutes on
  64 cores, each constituency an independent job. Uttar Pradesh (15.4 crore) in 8.5 min on one 16-core server.
- Citizen traffic: if 10% of voters check once in a 30-day revision -> 33 lakh checks a day, about 189 a
  second at a 5x peak. One laptop measured 163 full citizen answers a second on 4 processes (a lower bound)
  -> 2 machines cover India's peak.
- Cost: about Rs 0 per check (cached answers, free tiers, or the user's own key).

Citizen
- "meena kumaari booth 47" (misspelt, Latin script) -> मीना कुमारी, booth 047, NOT IN THE NEW LIST, reason,
  Form 6 / Form 7, the 1950 helpline, "a BLO never asks for an OTP or money", Hindi voice reply.
- Name matching: 0 of 2,950 names that are not in the roll matched anyone; 381 of 400 real voters typed
  with a typo were found, 0 wrong person. Unmatched names say "Not listed".
- Documents checker (from the SIR information sheet BLOs hand out): born before 1 Jul 1987 -> one document
  for yourself; 1987 to 2 Dec 2004 -> yourself + one parent; after that -> yourself + both parents.

Money
- Citizens never pay. Organisations build a monthly plan on the Pricing page (Razorpay, verified server-side):
  newsroom data desk Rs 9,098 a month (after 50% non-profit discount), election-watch group Rs 28,494,
  election office (check drafts before publishing, on its own servers) Rs 1,84,473. Yearly = 2 months free.

====================================================================================================
SLIDES (main deck)

1. TITLE. "Every change to a voter roll, explained." grey second clause: "And every rumour about it, checked."
   Logo (attached) top-left. Small mono line: RollWatch · Team Nova · IDEAS-175 · live links.

2. THE PROBLEM. Headline: "After every revision, thousands of names change. The rumour arrives first."
   Visual: the forward as a chat bubble. Under it, two facts: ~1.3 crore flagged in West Bengal with no
   published error rate; 91% of decided appeals restored the voter.

3. WHAT WE HEARD IN ROUND 1, AND WHAT WE BUILT. A clean two-column table, 4 rows, each answer with a number:
   - "It won't scale." -> 13.5 min for all 97.8 crore electors on 64 cores; 2 machines for peak traffic.
   - "Can't the government just do this?" -> Yes, inside: Run it / POST /audit on a draft. But a self-audit
     can't settle a rumour about the auditor, so the same open engine sits outside too.
   - "Why not big data / ML?" -> No labelled wrongful deletions exist, and a notice must say why. ML where it
     fits (calibration, name matching, language); statistics where a voter's rights are at stake.
   - "Crores of requests?" -> about 189/s at peak; measured 163/s per laptop; the audit is computed once per roll.
   This slide is the spine of the talk: say "you told us, we measured it".

4. HOW IT WORKS. One left-to-right diagram: roll v1 + roll v2 -> Python engine (diff, age-adjusted binomial test
   + Benjamini-Hochberg, cross-script duplicates, "which story fits", bootstrap) -> numbers + confidence ->
   AI only phrases words -> neutrality guard -> web / WhatsApp / Telegram / share card.
   Label in mono: "every number comes from code". Small note: turn the AI off and every verdict stays the same.

5. WHICH STORY FITS. Booth 47 vs Booth 12 story bars side by side (greys for innocent stories, the
   unexplained part in yellow/black hatch). Booth 47: 97% hatch -> NEEDS HUMAN REVIEW chip. Booth 12: 79%
   hostel grey -> LIKELY BENIGN chip. Below, a small Booth 63 strip: 64% -> 8% with the boundary log on.
   Headline: "Same size to a rumour." grey: "Only one of them is unexplained."

6. CLAIM COURT. The forward in large two-tone type, then three verdict rows (chip, sub-claim, mono query on the
   right): DISPUTED 600 (412, 46% off) · VERIFIED rank 1 of 100 · CANNOT BE PROVEN community. A small
   mirror card. Phone mock with the share image coming back into a chat. Headline: "The agent plans."
   grey: "Code decides."

7. FOR VOTERS. Phone mock of the WhatsApp chat: misspelt name -> status card in Devanagari, the NOT IN THE NEW
   LIST chip, Form 6 / 7, 1950, the voice-note bubble. Side strip: Hindi · English · ਪੰਜਾਬੀ, documents checker,
   0 of 2,950 wrong matches. Headline: "Why your name changed." grey: "And what to do before the deadline."

8. WE TESTED OURSELVES. Big mono scoreboard: 9/9 found · 6/6 decoys cleared · 0 missed. Second row:
   263 of 283 flags real (93%) · 0 false alarms on booth spikes · 20 record-level (14 duplicates, 6 relations).
   Small line: planted by a separate AI agent; we never saw the key. Headline: "We tested ourselves."
   grey: "And counted every false alarm."

9. TRY TO FOOL IT. A slider visual for Booth 23: 17 -> "spike, not sent to review"; 18 -> NEEDS HUMAN REVIEW.
   Stat: median 19 names (8 to 40) per booth. A clearly marked "blind spot" box: 1,000 names spread over 100
   booths -> 58 show a spike, only 2 reach review. Headline: "Here is what we can't catch." grey: "Before you ask."

10. THE OFFICIAL CHECKS. Horizontal bars: share of trips that are innocent, per official check (81% to 100%).
    Headline: "A check without an error rate." grey: "Is a notice waiting to happen." Footnote: synthetic data.

11. THE THREE QUESTIONS (mandatory; three columns, each with something we can show):
    - HOW IT SCALES: per booth and linear -> 1.02M voters in 53.9 s on one core; 13.5 min for all of India on
      64 cores; 2 machines for peak citizen traffic; spreads as share cards in the chat the rumour came from,
      no install; the same method fits any "cleaned" list (ration cards, pensions) because story rules are a
      YAML file.
    - WHY THE GOVERNMENT CAN'T DO IT ALONE: a self-audit can't settle a rumour about the auditor. Inside: an
      office runs POST /audit (the Run it page) on a draft before publishing. Outside: newsrooms, observers and
      citizens run the same open engine, so both sides agree on the arithmetic. If they adopt it, we win; the
      independent copy still has a job.
    - WHY IT'S FUTURE-PROOF: a fixed, measured core; data (adapters to an open schema, incl. roll PDFs), rules
      (YAML), model (swappable, never makes a number, template fallback), languages and channels are swappable
      parts. We swapped the model and the voice in an afternoon. The blind test re-measures every change.

12. WHO PAYS. Citizens never pay. Three plan cards: newsroom Rs 9,098/mo · watch group Rs 28,494/mo ·
    election office Rs 1,84,473/mo. Small line: built on the Pricing page, paid via Razorpay, open-source core.
    Under it: "From Monday": one newsroom data desk or election-watch group pilot in the next revision.

13. LIMITS + ASK. Honest limits: synthetic data only; confidence needs recalibration on real rolls; per-booth
    tests miss names spread very thin; not affiliated with any official body. Ask: one pilot partner.
    Live links + WhatsApp number + a QR code to rollwatch-web.onrender.com.

BACKUP SLIDES (after a divider "Questions."; same design, denser is fine)
B1. Why statistics, not a black box: no ground truth to train on; a notice must cite a reason; ML where it
    fits; Royston et al. (2021, used with the Iowa Secretary of State) found district-comparison statistics
    worked best for voter-file anomalies and labelled likely causes, as we do.
B2. Crores of requests: the load-test table (1 vs 4 processes): overview 131.7 -> 242.1/s, name search
    103.1 -> 202.2/s, citizen answer 72.1 -> 163/s, claim check 105.1 -> 211.3/s. Lower bounds (one test
    client). Audit computed once per roll; viral claims cached; WhatsApp state in Redis, so we add servers.
B3. Algorithms and complexity table: diff O(n) hash join · booth tests O(m log m), binomial + BH · duplicates
    O(sum of block sizes squared) with blocking + union-find (9.9M pairs, not 521B) · stories O(r) per booth ·
    bootstrap 500 resamples in 2 ms for Booth 47 · claim tools O(1) on precomputed aggregates.
B4. Is it a wrapper? Gemini only splits the claim, reads screenshots and phrases text; ElevenLabs only does
    voice. Python computes every number. With the model off (DEMO_MODE) every verdict is identical.
B5. Neutrality and safety: no party, person or institution names in any output (neutrality guard on every
    outbound message); no actor fields in any schema; the mirror test; never infers religion, caste or
    community; auditor views mask names; 26 access-control attack checks pass; per-client rate limits.
B6. Platform for organisations: workspaces with roles and API keys, async constituency audits, newsroom
    report and CSV exports, review queue with a hash-chained history, roll-PDF ingestion, 7 languages in
    citizen answers, dark theme, 10-stop onboarding tour.

====================================================================================================
DESIGN (strict; this matches the live site, which judges will also see)

Look: butter.video-inspired "engineered calm". Precise instrument, not a civic-tech template.
- Page #F9F9F9 (near-white). Panels #EDEDED, 28px radius. Cards inside panels #FFFFFF, 16px radius.
  Hairlines #DCDCDC. Hover/inactive #E3E3E3.
- Text #0F0F0F; secondary #5C5C5C; the grey half of two-tone headlines #9A9A9A.
- Type: Geist for everything, regular weight 400, tight tracking -0.035em, line-height ~1.02 on big type.
  NEVER bold headlines. Geist Mono for every number, ID, query and for small eyebrows in sentence case that end
  with a period ("Which story fits." "Claim court." "Blind test."), colour #9A9A9A. Big stats in Geist Mono 400.
  Hindi/Punjabi in Noto Sans Devanagari / Gurmukhi.
- Two-tone headlines on every slide: a black clause, then a grey clause.
- The signature move: a small live object inside a headline at text height (a booth tile, a verdict chip,
  a mini story bar), e.g. "412 names left [B47 tile] Booth 47. We expected about 25."
- Colour ONLY as small signal chips or one bar segment / tile, always with a text label:
    yellow  #F6D84D  ink text   = UNUSUAL · NEEDS HUMAN REVIEW / unexplained / selected booth
    mint    #1CC691  ink text   = VERIFIED
    magenta #D61F69  white text = DISPUTED
    periwinkle #B8C7FF ink text = LIKELY BENIGN
    grey #EDEDED with a dashed #9A9A9A border, #5C5C5C text = CANNOT BE PROVEN
  Chips: Geist Mono 12px uppercase, 6px radius (scale up proportionally on slides).
- Story bars: innocent stories in greys, dark to light: death #2E2E2E, duplicate #5C5C5C, boundary #8C8C8C,
  hostel #BDBDBD. Unexplained is always LAST, in a yellow/black diagonal hatch (135deg, yellow 5px, ink 1.5px).
  The hatch is the only pattern allowed.
- Booth tiles: rounded squares (10px radius), booth number top-left and % bottom-right in mono. Neutral white,
  unusual yellow, benign periwinkle, mixed = hatch.
- Buttons/pills: #1E1E1E fill, white text, 8px radius.
- Charts: no grid, baseline #DCDCDC, mono ticks 12px #9A9A9A, flat bars with 4px radius.
- Logo: use the attached files exactly (a bronze eye in a ring of "ROLLWATCH" letters, and a script
  wordmark). The bronze appears ONLY in the logo, never as a slide colour. Do not redraw or recolour it.
- Phone mocks: plain rounded rectangles in #EDEDED/#FFFFFF with the real screenshot inside; no device chrome
  photos.
- Generous air: big margins, one idea per slide.
- Light deck. (If we ask for a dark version later: page #0F0F0F, panel #1A1A1A, surface #222222, line #2F2F2F,
  ink #EDEDED, ink-2 #A6A6A6, ink-3 #707070, story greys reversed #D9D9D9/#A6A6A6/#7A7A7A/#4F4F4F; chips keep
  their fills and dark text.)

NEVER: gradients (except the hatch), shadows, glows, glass, stock photos, emoji, icon libraries (lucide,
heroicons), robots, brains, sparkles, saffron or tricolour combinations, party colours, election symbols,
maps of India, ballot boxes, inked fingers, Inter / Poppins / Space Grotesk / Plus Jakarta.

COPY RULES
- Never "AI-powered", "smart", "magic", "revolutionary", "seamless", "unlock", "game-changer".
- Never fraud, rigging, scam or "ghost voters" (except inside a quoted claim), and never name any party,
  person or institution. State what happened, with numbers.
- Every result slide carries "needs human review" or "patterns for human review, not findings".
- A small footer on every slide in mono #9A9A9A: "synthetic data · Sampleabad is fictional".

Use the attached screenshots inside slides 5-10 and 12 where a real screen is stronger than a drawing.
```

## Screenshots to attach (all in `deliver/deck-screens/`, taken from the live site on 28 Oct)

| File | Use on slide |
|---|---|
| `01-home-hero-light.png`, `01-home-hero-dark.png` | 1 (title backdrop or closing), proof the site is live |
| `02-which-story-fits.png` | 5 |
| `03-claim-court-verdicts.png`, `04-mirror.png` | 6 |
| `05-ask-meena.png` | 7 |
| `06-trust-top.png`, `07-false-alarms.png` | 8 |
| `08-try-to-fool-it.png` | 9 |
| `10-official-checks.png` | 10 |
| `09-national-scale.png` | 11, B2 |
| `11-run-it.png` | 11 (the "inside" path) |
| `12-pricing.png` | 12 |
| `13-phone-home.png` | 7 or 13 (phone view) |
| `web/public/logo-word.png`, `web/public/logo-mark.png` | every slide (logo) |

WhatsApp chat screenshots are not here: take two on your phone (the demo forward with its share image, and a Hindi voice note with the spoken reply) and attach them for slides 6 and 7.
