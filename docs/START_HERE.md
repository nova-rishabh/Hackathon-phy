# RollWatch: start here

> The one page everything else follows. If a doc, slide or demo disagrees with this page, this page wins, and then we fix the other doc.
> Team Nova (IDEAS-175) · X AI Tech Ideathon, 27–28 Oct 2026 · **PS1: AI for Electoral Roll Transparency (locked)** · presentation round done, **building now**.

## 1. What we're building, in one breath

**RollWatch checks voter-roll changes and the viral claims about them, and shows its working.** It compares two versions of a roll and tests every removal against the innocent explanations on record. It also turns a forwarded rumour into a checked, shareable verdict card, with identical treatment for both sides.

**The line for the room:** *"Every team here can flag a spike. We tell you which story the spike fits, and we prove we're not guessing."*

## 2. The edge: what every PS1 team will build vs what we build

PS1 lists four modules, and every team will build all four. **The modules are table stakes. We win on how each one is done.**

| PS1 module | What most teams will build | What RollWatch does | Proof on screen |
|---|---|---|---|
| **1. Anomaly detection** | A threshold or IsolationForest on deletion counts, and a red/green map | Each booth is tested against its **expected** rate (age-adjusted binomial, BH-corrected). Duplicates are matched **across scripts** with blocking + union-find. | Booth grid, duplicate cluster, bench numbers |
| **2. Explanations** | An LLM paragraph listing "possible innocent reasons" | **Which Story Fits?** Every removal is *tested* against records (deaths, hostels, boundary changes, duplicates). The leftover is measured and tested. **Context controls let you switch a source off and watch the answer move.** | Booth 47 vs Booth 12, the toggle on Booth 63 |
| **3. Citizen assistant** | A chatbot that looks up a name | A typo- and script-tolerant lookup that says **why** your entry changed and **what to do before the deadline**, in Hindi, English and Punjabi, with Hindi voice | Meena's chat |
| **4. Claim checker** | An LLM says true or false | **Claim Court, a tool-use agent over typed tools.** Code runs every query and computes every verdict; the query is shown. **Mirror:** the opposite claim gets identical treatment. **Forward in, card out:** the verdict goes back into the chat as a share card. | Screenshot → card, mirror side by side |

**What no other team will have:**
- **Blind self-test.** One teammate hides anomalies *and* innocent decoys that the engine's author never sees. We show found, missed and decoys cleared.
- **Rules with published error rates.** Official revision software raises "logical discrepancy" flags with no published thresholds (the Supreme Court asked on 22 Sep for the term to be defined). Every RollWatch rule shows how often it fires on innocent records.
- **Ops numbers on screen:** latency, ₹ per check, cache hit rate, plus a 1M-voter scale run.

**What we keep thin (generic):** the dashboard chrome, the plain name search and the chat UI. They deliver the edge; they aren't the edge. No map, no KPI wall, no free-chat bot.

## 2a. Judges' feedback from the presentation round: "not scalable" / "can't the government just do this?"

The score isn't out yet. This was the main criticism, so **every surface now answers it**: the pitch, the Q&A, the build and one demo beat.

**1. "Can't the government do it themselves?" Yes, and they should integrate it. But they can't be the only ones running it.**
- **A self-audit settles nothing.** When the body that revised the list says the rumour about it is false, a sceptical voter has no reason to believe it. Trust needs an **independent** check that anyone can re-run, the way company accounts need an outside auditor.
- **The government has the data, not the explanation layer.** Official software already raises "logical discrepancy" flags with no published thresholds or error rates, and the Supreme Court asked on 22 Sep for the term to be defined. RollWatch's rule error rates and "which story fits" are exactly what's missing.
- **So there are two ways in, from the same open-source engine:**
  - **Inside:** an election office runs `POST /audit` on a draft before publishing it. Booths whose removals no evidence explains get a second look *before* names are deleted. That means fewer wrongful deletions and fewer claims to process.
  - **Outside:** newsrooms, observers and citizens use the same engine for claim checks and status lookups. Same code, same numbers, so the two sides can't disagree about the arithmetic.
- **If they adopt it, we win.** Being integrated is the success case. The independent public layer still has a job, because a rumour is always about the people who run the system.

**2. "It's not scalable." It scales on three axes, and we show each one with a number.**

| Axis | How | Proof we build |
|---|---|---|
| **Compute** | Every test is per booth, and booths are independent. Each step is linear or near-linear (TRD §1.1), so a state is just more booths, run in parallel per constituency. | S10 scale run: 1M voters timed, plus parallel speed-up per ward. Then extrapolate honestly to Delhi's 1.45 crore. |
| **Adoption** | No install. Answers arrive as **cards inside the chat app the rumour came from**, so each check is a shareable artifact that brings the next user. One deployment serves every state, in three languages already. | M9 forward→card, S11 group `/check` |
| **Scope** | The method isn't voter-specific. Any public list that gets "cleaned" (ration cards, pensions, scholarship beneficiaries) has the same question: *which removals are explained, and which aren't?* Story rules are **config**, so a new register or a new evidence source is a YAML file, not new code. | S12: `engine/stories.yaml`, and the demo adds an evidence source live |

**What we don't claim:** real-roll ingestion. Real rolls are published as per-part PDFs, so PDF ingestion is roadmap. We show the open input schema and the adapter interface instead.

## 3. Who we're building for: the judge

**Nishant Chahar.** These details are from a third-party profile and are not independently verified, so confirm anything we quote:
- ex-Software Engineer at Microsoft
- co-founder of AlgoPrep (an AI learning platform, reportedly acquired by Vedam School of Technology)
- linked to ShotoAI (an AI video editor) and Tayyari
- building a new startup with Entrepreneurs First
- a YouTube creator with about 560k subscribers (tech careers, DSA, startups)
- NSUT Computer Engineering, 2017–21

**What that likely means he rewards, and how we answer it:**

| He likely values | Because | So we… |
|---|---|---|
| **Algorithmic depth you can explain** | A DSA educator and ex-Microsoft engineer | State the complexity of every algorithm and show measured numbers (TRD §1.1): blocking cuts n² pairs, union-find, BH. Both of us can whiteboard any function. |
| **Not a GPT wrapper** | He builds AI products himself | "The agent plans, code decides." Show the query behind every verdict, and the template fallback. |
| **A product people would actually use and share** | A founder (AlgoPrep, EF) who thinks in distribution | **Forward in, card out** is our growth loop. The card goes back into the group the rumour came from. Have a "from Monday" slide with the first users. |
| **Unit economics and speed** | A founder who has paid for compute | The ops strip: ₹ per check, p50 latency, cache hit rate. |
| **Polish in motion and video** | He builds an AI video editor (ShotoAI) | A butter.video-style UI, the share **clip** (S9), and a content video that's genuinely well cut. |
| **Honesty about limits** | Founders hate inflated demos | The Trust page shows what we **missed**, and the limitations slide. |

## 4. The demo world (one set of numbers, used everywhere)

All of it is synthetic: the fictional district **Sampleabad** (10 wards, 100 booths, about 50k voters).

| Booth | Role | Numbers |
|---|---|---|
| **B047** | Unusual | 412 removed, ~60 expected, 400 (97%) unexplained, confidence 82%. **Unusual · needs human review.** |
| **B012** | Looks the same, but benign | 380 removed, 81% fit a hostel move-out. **Likely benign.** |
| **B063** | Live toggle | 150 removed. With the boundary-change log on, unexplained drops from 64% to 8%. |
| **B030** | The mirror claim | "Ghost voters added in Booth 30" |

- **The forward:** *"Booth 47 mein raaton-raat 400 naam kaat diye, sab ek community ke!"*
  - **Verified:** about 400 left B047
  - **Disputed:** "overnight", because the removals spread across the revision
  - **Cannot be proven:** "one community", because we never infer community
  - Card confidence 76%.
- **Citizen:** "meena kumaari booth 47" → मीना कुमारी, not in the new list, likely reason shifted, next steps, the deadline, the official portal, 1950.
- **Personas for judges:** Meena B047, Ravi Verma B012, Harpreet Kaur B063.

A1 builds `generator/demo_config.yaml` to produce exactly these numbers. The blind eval still uses the partner's private config.

## 5. Where everything lives

| Need | File |
|---|---|
| Build plan, hour by hour | [`ACTION_PLAN.md`](ACTION_PLAN.md) |
| Scope (MUST / SHOULD / CUT) | [`PRD.md`](PRD.md) |
| Architecture, algorithms, complexity | [`TRD.md`](TRD.md) · [`../contracts/`](../contracts/) |
| Look and copy (butter.video style) | [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md) · [`../design/tokens.css`](../design/tokens.css) · [`../design/glyphs.svg`](../design/glyphs.svg) |
| Logo brief and brand assets | [`BRAND.md`](BRAND.md) |
| Demo run-sheet, Q&A, slides | [`DEMO_AND_PITCH.md`](DEMO_AND_PITCH.md) |
| Content video | [`CONTENT_VIDEO.md`](CONTENT_VIDEO.md) |
| History only | [`SESSION_LOG.md`](SESSION_LOG.md) · [`IDEATHON_STRATEGY.md`](IDEATHON_STRATEGY.md) · [`ROLLWATCH_PLAN.md`](ROLLWATCH_PLAN.md) (superseded) |

## 6. Decisions we've made (don't re-open them)

- **Problem statement:** PS1 is locked. RollWatch is the product.
- **Commits:** in Rishabh Kataria's name only, **no Co-Authored-By / Claude line**. The repo is public, so private profile and access files stay off it. Don't push without asking.
- **Look:**
  - butter.video-inspired, **light only**, no dark UI
  - no stock icons (lucide, heroicons, emoji)
  - nothing that looks AI-generated
  - colour only as small signal chips
  - the v1 violet/brick palette and the v1 logo concepts are rejected
- **Logo:** Rishabh designs it ([BRAND.md](BRAND.md)). Claude does not draw logos.
- **Pitch:** no AI voice and no read-aloud script. Slides carry one headline and one visual, and we talk over them.
- **Testing:** five smoke checks plus the demo run-through. No test suites. Ship first.
- **Data:** synthetic only. Never read `private/`. Never name parties, people or communities.
- **Credits:** be efficient. Subagents only when they clearly save time. Say so before an expensive step.
