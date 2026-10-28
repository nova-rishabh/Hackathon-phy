# RollWatch: final-round script (simple version)

Goes with the deck `RollWatch — Final round.pdf` (13 main slides + 6 backup). Every number below is from the live API on 28 Oct (same as the deck). Read it out loud twice before you go in; you don't have to say it word for word.

Total: about **6 minutes** (film 0:48 + talk + 2-minute live demo). If they give you 5 minutes, skip the live demo and talk over slides 5–9 instead (the "short version" lines are marked).

---

## The flow

| # | What's on screen | Time |
|---|---|---|
| 1 | **Film** (`web/public/rollwatch-film.mp4`, 48 s). Say nothing; let it play. | 0:00–0:50 |
| 2 | Slides **1 → 4** (title, problem, what we heard, how it works) | 0:50–2:20 |
| 3 | **Live demo**: Check → `/audit` → Ask → Trust | 2:20–4:20 |
| 4 | Slides **10 → 13** (official checks, three questions, who pays, ask) | 4:20–6:00 |
| 5 | Backup slides B1–B6 only when a question needs them | Q&A |

Slides 5–9 show the same things as the live demo. If the demo works, flip past them in one second each ("you just saw this"). If the Wi-Fi fails, present slides 5–9 instead of the demo; they are screenshots of the same screens.

**Which page:** do the demo on **`/audit`**, not the home page. `/audit` is where you click a booth and flip the boundary-log switch: that is the moment that proves the idea. The new home page (`/`) is a beautiful scroll story, but it repeats the deck, it needs WebGL on a projector, and scrolling it eats a minute. Use it as the front door only: have it open when you switch from slides to the browser ("this is the live site"), 5 seconds, then go to `/audit`. Show the full scroll only if a judge asks to see the site.

---

## The words

### Film (0:00) — say nothing
Just before you press play: *"Forty-eight seconds first, then I'll explain."*

### Slide 1 — Title (0:50)
"We're Team Nova. This is RollWatch.
Every change to a voter list, explained. And every rumour about it, checked.
Everything you'll see runs on a made-up district called Sampleabad. 100 booths, about 51,000 voters. The data is fake on purpose; the method and the numbers are real code output."

### Slide 2 — The problem (1:05)
"After every revision of the voter list, thousands of names change. And the rumour arrives before the facts.
A forward like this one: *'Booth 47 mein 600 naam kaat diye, sabse zyada, aur sab ek community ke.'*
Nobody can check it. Real example: in West Bengal about 1.3 crore voters were flagged, with no published error rate, and 91% of the appeals that were decided gave the voter back their name.
So the problem is not that names change. The problem is that nobody can say **why**."

### Slide 3 — What we heard in Round 1 (1:30)
"Last round you asked us four hard questions. We went back and measured each one.
*It won't scale?* All 97.8 crore voters of India in 13 and a half minutes on one 64-core machine.
*Can't the government do it?* Yes, and they can run it inside. But a self-audit can't settle a rumour about the auditor, so the same engine also has to sit outside.
*Why not machine learning?* There is no data of labelled wrong deletions to train on, and a notice must give a reason. So: statistics where a voter's rights are at stake, ML where it fits.
*Crores of requests?* Peak is about 189 a second. One laptop already does 163."

### Slide 4 — How it works (1:55)
"Simple pipeline. Old list and new list go in. Python compares them, tests every booth, finds duplicates across Hindi and English spellings, and says which story fits.
The AI only does the words: it splits a claim into parts and writes a friendly reply.
**Every number comes from code. Turn the AI off and every verdict stays the same.**"

*Now switch to the browser. Home page is open:* "This is the live site, anyone can open it." *Click to Check.*

### Live demo (2:20) — about 2 minutes

**Check** (paste the Booth 47 forward)
"Same forward. It splits into three parts.
'600 names': we count 412. **Disputed.**
'Most of any booth': true, rank 1 of 100. **Verified.**
'All one community': we never guess religion or caste from names, so **cannot be proven**, and it says why.
Under each row is the exact query that made the number. And this card goes back into the WhatsApp group the rumour came from."

**Audit** (`/audit` → Booth 47, Booth 12, Booth 63)
"To a rumour, these three booths look the same: hundreds of names gone.
Booth 12: 390 removed, but 79% are hostel students moving out. Likely innocent.
Booth 47: 412 removed, about 25 expected, and 97% match no record at all. That one needs a human.
Booth 63: switch the boundary-change record off, 64% unexplained. Switch it on, 8%. **The answer moves with the evidence.** That's what 'which story fits' means."

**Ask** (`meena kumaari booth 47` → Listen)
"Now a voter. Wrong spelling, still found. It tells her why, which form to file, the 1950 helpline, and that a BLO never asks for an OTP or money. In Hindi voice, on WhatsApp and Telegram too."

**Trust** (scroll to Try to fool it, Booth 23, slide 17 → 18)
"How do you know we're right? Another AI agent hid problems in a district we'd never seen. We found 9 of 9, cleared 6 of 6 look-alikes. Of 283 flags, 263 were real, and we list every false alarm.
And here's what we *can't* catch: hide 17 names in Booth 23, nothing. 18, it goes to review. We show our blind spot before you ask."

*Short version (no demo):* use the bold lines above over slides 5, 6, 7, 8, 9.

### Slide 10 — Official checks (4:20)
"One more thing. The official 'logical discrepancy' checks from the 2025–26 revision. We ran them on our district. Most of the time they trip on innocent people: name changed after marriage, 100% innocent. Too many children, 98% innocent.
**A check without an error rate is a notice waiting to happen.** We give every check an error rate."

### Slide 11 — The three questions (4:45)
"Three questions, three things we can show.
**Scale:** every test is per booth, so a state is just more booths in parallel. All of India in 13 and a half minutes on 64 cores. Two machines for peak citizen traffic. It spreads as share cards in the same chat as the rumour, no app to install. And it works for any cleaned list, like ration cards or pensions.
**Why not the government alone:** an election office can run it on a draft before publishing; that's our Run it page. But a self-audit can't settle a rumour about the auditor. So newsrooms and citizens run the same open engine outside. Both sides agree on the arithmetic. If they adopt it, we win.
**Future-proof:** the core is fixed and measured. The AI model, the voice, the languages, the rules are swappable parts. We swapped the model and the voice in one afternoon, and the blind test re-checks every change."

### Slide 12 — Who pays (5:25)
"Citizens never pay. Organisations build a plan: a newsroom data desk about 9,000 rupees a month, an election-watch group about 28,000, an election office about 1.8 lakh, running on their own servers. A citizen check costs us about zero."

### Slide 13 — Limits and ask (5:40)
"Honest limits: synthetic data only, confidence needs recalibration on real rolls, and removals spread very thin across booths can slip past.
Our ask: **one pilot partner**, a newsroom or an election-watch group, in the next revision.
Try it right now: the website, WhatsApp, or Telegram. Thank you."

---

## Q&A: which backup slide

| They ask | Slide | One line |
|---|---|---|
| Why statistics, not ML? | B1 | No labelled data, and a notice must give a reason. |
| Crores of users? | B2 | 189/s at peak, 163/s per laptop, audit computed once per roll. |
| Algorithms, complexity? | B3 | 9.9 million pairs instead of 521 billion; 1 million voters in 54 s on one core. |
| Is it a Gemini wrapper? | B4 | Turn the model off: same verdicts. |
| Bias, safety? | B5 | No party/person names, never guesses community, mirror test. |
| Is it just a demo? | B6 | Workspaces, API keys, review queue, PDF reading, 7 languages. |

## Before you walk in
1. `python scripts/warmup.py` 5 minutes before; every line OK. If not: `scripts\demo_local.ps1` and present from http://127.0.0.1:3000.
2. Tabs in order: film, deck, Home `/`, Check, `/audit`, Ask, Trust (scrolled to Try to fool it).
3. **Open every tab once beforehand.** The home page takes about 10 s to load its 3D scene, and `/audit` shows a 10-step tour on a browser's first visit: press **Skip tour** once and it never comes back.
4. Never say: fraud, rigging, "AI-powered", any party or person name, or that RollWatch "proves" anything.

## Clicks for the demo (checked live on 28 Oct)
- **Check:** press **try the demo claim**, then **Check this claim**. No pasting needed.
- **Audit:** the "Which story fits" panel is already on Booth 63; the boundary log switch is on its right. Booths 47 and 12: tap their squares in the grid (opens a side panel).
- **Ask:** press the **meena kumaari booth 47** chip, then **Ask**, then scroll to **Listen**. The Hindi answer is long; that's fine.
- **Trust:** press **try 17** under the slider, then press the right-arrow key once for 18.
- **Do not run "Run it" on the live site.** The free server takes about 80 s for the 10-booth sample (your laptop: 2 s). If a judge asks, say: "The same engine runs a 51,000-voter district in 2.5 s on a laptop; our demo server is a free shared one."
- **If a judge asks why Booth 63 says 68 removed in one place and 154 in another:** "68 left the roll. 86 more didn't leave; they moved to a neighbouring booth when the boundary was redrawn. That's exactly what the boundary record explains."
