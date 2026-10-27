# RollWatch: Design System v2

> **Reference: [butter.video](https://butter.video)** (screenshot PDF shared by Rishabh, 27 Oct). It replaces the v1 "public ledger" look (warm paper, violet and brick), which Rishabh rejected as AI-looking.
> **Feel: engineered calm.** A near-white page, soft grey panels, very large regular-weight type, and two-tone headlines. Colour appears only as small signal chips. It should feel like a precise instrument, not a civic-tech template.
> Files: [`design/tokens.css`](../design/tokens.css) (Tailwind v4) · [`design/glyphs.svg`](../design/glyphs.svg) · brand and logo brief: [`BRAND.md`](BRAND.md).

---

## 1. What we take from butter.video, and what we change

| Butter does | RollWatch does |
|---|---|
| Near-white page `#F9F9F9`, grey panels `#EDEDED` with big radii | The same. Panels at 28px radius hold every product module. |
| Huge grotesk headlines at **regular weight**, tight tracking | Geist 400, −0.035em. Display at 56–96px. **Never bold headlines.** |
| Two-tone sentences: black words, then grey words | Every page title: `412 names left Booth 47.` <span>in grey:</span> `We expected about 60.` |
| Small objects inside a sentence (a dial, a slider, a 3D chip) | **A live object inside the headline:** a verdict chip, a mini story bar or a booth tile sits inline in the sentence. |
| Mono eyebrows in grey ("Infinitely customizable.") | Mono eyebrows in sentence case with a period: `Which story fits.` `Claim court.` `Blind test.` |
| Control panels with dials, sliders and segmented options | **Context controls** for "Which Story Fits?": each evidence source is a segmented on/off control, and the residual updates live. |
| A big option list where the inactive items are grey ("Remix / Describe / Code") | The three verdicts and the three surfaces (Audit / Check / Ask) use this pattern. |
| Black 8px-radius buttons | The same: `#1E1E1E`, 40px tall. |
| Dark product panels | **We stay light** (team rule: no dark UI). Product panels are `#EDEDED`, and cards inside are white. |
| Vivid 3D objects as hero art | At most **one** tactile object per page, on marketing surfaces only (the share card, the video end card). Never in the app. |

## 2. Hard rules

1. **Light only.** No dark mode, no dark sections, no dark product panels.
2. **No gradients, glows, glass or shadows.** The only pattern is the yellow/black **hatch** on "unexplained" and "mixed".
3. **No stock icons.** No lucide, heroicons, emoji, sparkles, robots or brains. Use our glyphs (§7) or a word. Most UI needs neither.
4. **Colour is a signal, never decoration.** The page is greyscale. The five signal colours appear only as chips, one story-bar segment or one booth-tile fill. **No colour ever fills a large area**, so nothing reads as a party colour. Never use saffron, tricolour combinations or election-symbol shapes.
5. **Fonts:** Geist and Geist Mono, plus Noto Sans Devanagari and Gurmukhi. **Not** Inter, Space Grotesk, Poppins, Plus Jakarta (v1) or the system default.
6. **Copy never says** "AI-powered", "smart", "magic", "revolutionary", "seamless" or "unlock". It states what happened, with numbers.

## 3. Colour

### Base
| Token | Hex | Use |
|---|---|---|
| `page` | `#F9F9F9` | Background |
| `panel` | `#EDEDED` | Module panels, quiet buttons, unprovable chip |
| `panel-2` | `#E3E3E3` | Hover on panel, inactive segment |
| `surface` | `#FFFFFF` | Cards inside panels, inputs, tables |
| `line` | `#DCDCDC` | Hairlines |
| `ink` | `#0F0F0F` | Text |
| `ink-2` | `#5C5C5C` | Secondary text (body sizes) |
| `ink-3` | `#9A9A9A` | The grey half of headlines, eyebrows (large or mono-label only) |
| `button` | `#1E1E1E` | Primary buttons |

### Signals (small fills only; each always has a text label)
| Token | Hex | Text on it | Means |
|---|---|---|---|
| `signal` | `#F6D84D` butter yellow | ink | **Unusual · needs human review**, the unexplained share, the selected booth |
| `verified` | `#1CC691` mint | ink | Claim **Verified** |
| `disputed` | `#D61F69` magenta | white | Claim **Disputed** |
| `benign` | `#B8C7FF` periwinkle | ink | **Likely benign** |
| `unprovable` | `#EDEDED` + dashed `ink-3` border | ink-2 | Claim **Cannot be proven** |

### Story bar
Innocent stories are **greys**, from dark to light: death `#2E2E2E`, duplicate `#5C5C5C`, boundary `#8C8C8C`, hostel `#BDBDBD`. **Unexplained is always last, in hatched yellow.** The eye goes straight to the part that matters.

## 4. Type

| Role | Font | Size / line | Weight | Notes |
|---|---|---|---|---|
| Hero display | Geist | 88/90 | 400 | −0.035em, two-tone, max 1 per page |
| Page title | Geist | 48/52 | 400 | two-tone |
| Section title | Geist | 28/32 | 400 | |
| Card title | Geist | 18/24 | 500 | |
| Body | Geist | 16/24 | 400 | max 64ch |
| Eyebrow | Geist Mono | 13/16 | 400 | `ink-3`, sentence case with a period |
| **Every number, ID and query** | Geist Mono | 14/20 | 400–500 | tabular-nums |
| Big stat | Geist Mono | 64/64 | 400 | e.g. `412` |
| Hindi / Punjabi | Noto Sans Devanagari / Gurmukhi | +1px, line-height 1.6 | 400/500 | `lang` attribute set |

## 5. Layout

- **Space scale:** 4, 8, 12, 16, 24, 32, 48, 72, 120. Generous vertical air between modules (72–120px), tight inside cards.
- **App shell:**
  - top bar: a floating grey pill (`panel`, 12px radius) with the wordmark at the left and the three surfaces as text tabs: **Audit · Check · Ask**, plus **Trust** at the right
  - no left rail
  - content max 1240px
- **Banner** (always visible, mono 12px, `ink-3`, under the bar): `synthetic data · sampleabad is fictional · flags are patterns for human review, not findings`
- **Mobile:** single column, 16px gutters, the bar collapses to the wordmark + a "Menu" text button.

## 6. Components

### 6.1 Headline with an inline object (the signature)
`<h1 class="display">412 names left <BoothTile 47/> Booth 47. <span class="dim">We expected about 60.</span></h1>`
The inline object is a real component at text height: a booth tile, a chip, or a 120px mini story bar. Use it on every page title.

### 6.2 Verdict chip
Mono 12px, uppercase, 26px tall, 6px radius, filled with its signal colour (§3). `NEEDS HUMAN REVIEW` uses the yellow. On the share card the chips scale to 40px tall.

### 6.3 Flag card (four lines, always in this order)
A white card (16px radius) inside a grey panel. The left column holds mono eyebrows (`what we found.` `why it's unusual.` `innocent explanations checked.` `how sure.`), and the right column holds the text with mono numbers. The chip sits top-right. The footer is `flag a3f91c02 · view query` in mono `ink-3`.

### 6.4 "Which Story Fits?" panel (hero 1)
- **Left:** a two-tone headline, the story bar (full width, 28px tall, 6px radius) and the mono legend `death 9 · dupes 3 · boundary 0 · hostel 0 · unexplained 400 (97%) ±3`.
- **Right:** **context controls**, a butter-style control stack. One row per evidence source (death register, duplicate clusters, boundary log, hostel list). Each row has a mono label and a 2-option segmented control `on | off`. Below them, a `residual` readout in 64px mono that tweens over 300ms when a control changes, and the outcome chip.

### 6.5 Booth grid (Audit overview)
- **Tiles:** 10 × 10, 56px square, 10px radius, 6px gap. Each tile shows the booth number top-left and the deletion % bottom-right, both in mono.
- **Fills:**
  - neutral: white
  - unusual: yellow
  - likely benign: periwinkle
  - mixed: hatch
- **Interaction:** the selected tile gets a 2px ink ring, and clicking a tile opens the flag drawer (a right sheet, white, 28px radius on its left corners).

### 6.6 Claim Court (hero 2)
- **Input:** a big white textarea in a grey panel, with "or drop a screenshot" as a mono hint. The button reads **Check this claim**.
- **Output:** the claim in large two-tone type. Below it, one row per sub-claim: the chip, the sub-claim text, and a mono query on the right (`count removed where booth = B047 → 412`).
- **Mirror:** two white cards side by side on one panel, joined by the mono line `identical treatment · same tools · same tolerance`.

### 6.7 Citizen chat (Ask)
- **Bubbles:** white bubbles with a 16px radius. The user's bubbles are `panel` grey. No avatars.
- **Status block:** the name in its own script at 28px, the booth in mono, the chip, the reason, numbered next steps, how sure, and the official portal line.
- **Language tabs:** `हिंदी · English · ਪੰਜਾਬੀ`, butter-style big option text (active in ink, inactive in grey).

### 6.8 Trust page
- **Scoreboard:** a big mono scoreboard, `found 21 / 24 · decoys cleared 11 / 12 · missed 3`, with each miss explained in one line.
- **Below it:**
  - reliability dots
  - the rule table with false-positive rates
  - the guard log count
  - an **ops strip:** p50 latency, cost per check in ₹, cache hit rate

### 6.9 Share card (1080×1350) and share clip
- The `page` background with one grey panel.
- The claim in 56px two-tone type, then the three verdict rows with 40px chips, then `how sure 76% · patterns for human review, not findings` and a QR code.
- This is the one place a tactile 3D object (the logo object) may appear.
- The clip version animates the chips in one by one (see the [PRD](PRD.md) S-list).

### 6.10 Buttons and inputs
- **Primary:** `button` fill, white text, 8px radius, 40px tall.
- **Quiet:** `panel` fill.
- **Inputs:** white, 1px `line`, 12px radius; on focus the border turns ink.
- No shadows.

### 6.11 Charts
- No grid. The baseline is `line`, and ticks are mono 12px in `ink-3`.
- Bars are flat with 4px radius.
- The reliability chart has a dashed diagonal and ink dots sized by n.

## 7. Glyphs (`design/glyphs.svg`)

A 24px grid with a 1.5px stroke, `currentColor` and a text label next to each glyph. Use them sparingly.
- **Glyphs:** `rw-spike` (deletion spike), `rw-twins` (duplicates), `rw-crowd` (oversized household), `rw-age` (impossible age), `rw-mirror` (mirror), `rw-tally` (eval), `rw-wave` (voice), `rw-script` (language) and `rw-stamp` (empty state).
- **`rw-mark` is retired.** Rishabh is designing the logo ([BRAND.md](BRAND.md)).
- The file is a **sprite**: opened directly it looks blank, because its symbols render only when a page references them with `<use href="/glyphs.svg#rw-spike"/>`.

## 8. Copy

- **Numbers first, then meaning, two-tone:** "412 names left. *We expected about 60.*"
- **Second person for citizens:** "Your name is in the new list."
- **Every result ends with** how sure we are and what a human should check.
- **Forbidden:** fraud, rigged, scam (except the BLO-scam warning), ghost voters (only inside a quoted claim), party, person and institution names, and "AI-powered".
- **Empty states are sentences:** "No flags in this ward. That's normal for most wards."

## 9. Accessibility
- Every signal colour also has a text label.
- Yellow, mint and periwinkle carry ink text; magenta carries white text (≥ 4.5:1).
- Keyboard access to booth tiles and segmented controls.
- `lang="hi"` / `lang="pa"` on Indic text. Tap targets ≥ 40px.
