# RollWatch: Demo, Pitch and Q&A

> **Every version of the pitch answers the three questions: scalable, why the government can't do this alone, and future-proof** ([START_HERE §2a](START_HERE.md#2a-the-three-questions-we-always-answer-scalable-why-not-the-government-future-proof)).
> Rules for the demo: everything is precomputed and cached, the network is optional, and a backup recording is ready. One persona carries the story: **Meena, Booth 47, Sampleabad** (fictional). The judge tries the bot **after** the pitch, not during it.

---

## 1. The 4:00 demo

| Time | Beat | On screen | Say |
|---|---|---|---|
| 0:00–0:12 | **Hook** | A synthetic forward on a phone (mirrored): *"Booth 47 mein raaton-raat 400 naam kaat diye, sab ek community ke!"* | "Crores of names changed in this year's roll revisions. Forwards like this spread in hours, and nobody can check them. Watch." |
| 0:12–0:45 | **Hero: forward → fact-check card** | Forward the screenshot to the RollWatch bot. About 15 s later a card comes back: **VERIFIED** "about 400 names left Booth 47" · **DISPUTED** "cut overnight" · **CANNOT BE PROVEN** "one community". 76%. | "It read the forward, split it into three checkable pieces and ran a real query for each. The part about a community? We never guess religion or caste from names, so it says cannot be proven, and tells you why." |
| 0:45–1:00 | **Mirror** | The opposite forward ("ghost voters added in Booth 30") with the same structure side by side. `IDENTICAL TREATMENT ✓` | "Same tools, same tolerance, same treatment, whichever side the claim comes from." |
| 1:00–2:05 | **Which story fits?** | Click Booth 47: the story bar is 97% unexplained, against ~60 expected removals. **NEEDS HUMAN REVIEW**. Click Booth 12: 380 left, 81% fits a hostel move-out. **LIKELY BENIGN**. Then Booth 63: toggle the boundary-change log on and watch the unexplained share fall from 64% to 8%. | "To a rumour, these two booths look the same. Only one is actually unusual. And you can see *why* we think so: switch a source on or off and the answer moves." |
| 2:05–2:25 | **Duplicates** | A cluster card: सुनीता शर्मा / Suneeta Sarma / Sunita Sharma, with masked names, same relation, same house. | "Same person, three spellings, two scripts. It's flagged for review, never removed." |
| 2:25–3:00 | **Citizen** | Web chat: type "meena kumaari booth 47" and it finds मीना कुमारी. Status: *not in the new list · likely reason: shifted*. Next steps, how sure, official portal. Tap play for the reply in Punjabi. | "Typo, wrong script, still found. It tells her why, what to do before the deadline, and always sends her to the official portal." |
| 3:00–3:35 | **Trust** | Trust page: "Hidden by teammate: 24 anomalies + 12 decoys. Found 21. Cleared 11 decoys. Missed 3. Here's why." Reliability chart with n. Guard log: `0 violations shipped`. | "We didn't grade our own homework. My teammate hid anomalies and innocent look-alikes that I never saw." |
| 3:35–4:00 | **Two ways in + close** | The Trust page bench line (1M voters in N s), then the "two ways in" slide (inside: `POST /audit` before publishing · outside: the same engine for newsrooms and citizens) | "An election office can run this before it publishes, and should. But a rumour is always about the people who run the system, so the same engine also has to be in everyone else's hands. Auditable. Explainable. Accessible. On no one's side." |

**Fallbacks:**
- **Telegram down:** run the same forward through the web Claim Court and show the pre-rendered card.
- **LLM down:** `DEMO_MODE=1` serves the identical cached output.
- **Laptop dies:** play the backup recording from the phone.

## 2. After the pitch: "try it yourself"
Hand judges a persona card (*Ravi Verma, Booth 12*, *Harpreet Kaur, Booth 63*, *Meena Kumari, Booth 47*). They scan the QR code to the web chat, or message the bot, in any of the three languages.

## 3. Q&A: the answers to rehearse

| Question | Answer (≤2 sentences) |
|---|---|
| Synthetic data proves nothing? | It proves the method. A teammate hid anomalies and innocent decoys the engine's author never saw, and the district's age and death profile is fitted to published aggregate figures (we show the chart). |
| Will you infer religion or caste? | **Never.** Rolls don't contain them and we refuse to guess from names, so any claim that depends on them returns "cannot be proven", with the reason shown. |
| 78% of what? | It's the probability that a flag is a true anomaly rather than an innocent pattern. It was calibrated on a separate synthetic district and checked blind on my teammate's plantings, and the n is on screen. |
| The official app already searches names. Why yours? | It tells you *whether* you're listed; we tell you *why* you changed and *what to do next*, in voice and Punjabi, tolerant of typos and script, and we always hand off to the official portal. |
| Is the Neutrality Guard just a regex? | There are three layers: the model only sees computed numbers, our schemas have no field for actors, and a final check rewrites and logs. The mirror test is the behavioural proof. |
| What does AI add beyond SQL? | Matching one person across scripts and spellings, turning a free-text rumour into checkable queries, and explaining statistics in three languages without inventing numbers. |
| A flag card goes viral as "AI proves deletions"? | Every card and every share image says "pattern for human review, not a finding", shows the innocent explanations, and never shows individual names in public views. |
| How does real data get in? | Accredited observers and newsrooms run it locally on rolls they already obtain legally, and the outputs are booth-level aggregates. We never scrape. |
| The LLM splits a claim wrong? | Every sub-claim shows the exact query it ran, so a human sees it. If a claim doesn't map to data we have, the answer is "cannot be proven", never a guess. |
| Can't the government just do this, or build it in? | They should, and `POST /audit` is built for exactly that: run it on the draft before publishing. But a self-audit can't settle a rumour about the auditor, so the same open engine also has to be in independent hands. |
| Is it scalable? | Every test is per booth and linear, so a state is just more booths in parallel. Here's 1M voters in N seconds. Adoption scales through cards inside chat apps, with no install. And the story rules are config, so the same method covers ration-card or pension lists. |
| Is it future-proof? | The core is fixed and tested, and everything that changes is a swappable part. Data comes in through adapters to an open schema, rules and forms are config, the LLM sits behind a fallback chain and never makes a number, and a new language or channel is a template or a thin client. The blind eval re-measures every change. |
| Who uses it, and who pays? | Data desks and election-watch NGOs during revision windows. It would be an open-source core, hosted for NGOs on civic-tech grants, with the citizen bot free. |
| What does one check cost, and how fast is it? | Show the ops strip: p50 latency, ₹ per claim check and the cache hit rate, measured from our own request log. |
| How does it scale to a real state? | The scale run: 1M voters in N seconds. Duplicate blocking scores only a fraction of the n² pairs, and union-find merges them in near-linear time. |
| Isn't this just a GPT wrapper? | No. The agent only plans which typed tool to call. Code runs every query and computes every verdict, and you can see the query behind each line. |
| Did Claude Code write this? | We used AI coding assistants heavily and say so. The design, the statistics and the review are ours, and either of us can explain any function. |

## 4. Slides (6)
1. **Title.** RollWatch, the one-line pitch, Team Nova IDEAS-175.
2. **The problem in numbers.** The real SIR aggregates, with sources and neutral wording. "Flags with no published false-positive rate."
3. **How it works.** One diagram: roll v1/v2 → engine (numbers) → stories + confidence → words (LLM) → guard → web, bot and card.
4. **Why trust it.** The blind eval, the mirror test, the guard log, and "never infers protected attributes".
5. **Scale · why not the government · future-proof** (the three questions, always on one slide; see START_HERE §2a). **Two ways in, and scale.** Inside: election offices run it before publishing. Outside: newsrooms, observers and citizens. Then the three scale axes with their numbers (compute, adoption, scope), the first 100 users and sustainability.
6. **Limitations + ask.** Synthetic data, recalibration needed on real data, not affiliated with any official body. Thank-you.

Slides use [design system v2](DESIGN_SYSTEM.md) (butter.video style): a near-white page, grey panels, big regular-weight two-tone Geist headlines and yellow signal chips. No stock photos, no gradient title slides, no script read aloud: each slide carries one headline and one visual, and we talk over it.
