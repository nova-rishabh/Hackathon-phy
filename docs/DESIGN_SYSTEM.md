# RollWatch: Design System

> Look and feel: **a well-kept public ledger.** Warm paper, black ink, one violet taken from the indelible ink mark on a voter's finger, and rubber-stamp verdicts. Civic and calm. It should read like something a newsroom would trust, not an AI demo.
> Files to copy: [`design/tokens.css`](../design/tokens.css) (Tailwind v4 theme) · [`design/glyphs.svg`](../design/glyphs.svg) (custom glyph sprite).

---

## 1. Hard rules (these are what keep it from looking AI-generated)

1. **Light theme only.** No dark mode, no dark hero sections, no black dashboards.
2. **No gradients, glows, glass, blur or drop shadows** beyond a 1px hairline. Flat fills and rules only.
3. **No stock icon set.** Don't use lucide, heroicons, emoji, sparkles ✨, robots, brains or "magic" wands. Use the custom glyphs in §6, or a plain text label. Most UI needs no icon.
4. **No party-coded imagery.** Avoid saffron (#FF9933 range), avoid tricolour combinations, and **never** use a lotus, hand, broom, bicycle, elephant, clock, arrow or other election-symbol shapes, even by accident.
5. **Fonts:** Plus Jakarta Sans and JetBrains Mono, plus Noto Sans Devanagari and Gurmukhi for Indic scripts. **Never Inter, Space Grotesk, Poppins or the system default.**
6. **Corners at 4px** (cards), 2px for inputs and 3px for stamps. No pill-shaped everything, and no `rounded-2xl`.
7. **Density over air.** Use the layout of a newspaper data page: hairline rules, tight tables, numbers aligned right in mono. Avoid big empty hero cards.
8. **Copy never says "AI-powered", "smart", "magic", "revolutionary", "seamless" or "unlock".** It says what happened, with numbers.

## 2. Colour

All colours are flat. Text contrast is at least 4.5:1 on its own background.

### Base
| Token | Hex | Use |
|---|---|---|
| `paper` | `#F7F4EE` | App background (warm roll-paper) |
| `surface` | `#FFFFFF` | Cards, tables, drawers |
| `sunk` | `#EFEBE3` | Table header rows, code/query blocks, inactive tiles |
| `rule` | `#DDD7CB` | Hairlines, borders (1px) |
| `rule-strong` | `#BDB5A6` | Focus outline base, dividers between sections |
| `ink` | `#1D1C1A` | Primary text |
| `ink-2` | `#4A4741` | Secondary text |
| `ink-3` | `#77726A` | Captions, axis labels (large text only) |

### Brand
| Token | Hex | Use |
|---|---|---|
| `voter-ink` | `#4C2A85` | Brand accent: wordmark mark, primary buttons, links, focus ring, selected nav |
| `voter-ink-soft` | `#EEE8F6` | Banner strip, selected row, hover |
| `voter-ink-deep` | `#36195F` | Button pressed |

### Meaning (every one also carries a text label; colour is never the only signal)
| Token | Hex | Soft | Meaning |
|---|---|---|---|
| `unusual` | `#A3402B` (brick) | `#F6E5DF` | Flag outcome "Unusual, needs human review"; claim verdict **Disputed** |
| `benign` | `#2E5E78` (steel blue) | `#E3EDF2` | Outcome "Likely benign" |
| `verified` | `#1F6A50` (deep teal) | `#E2F0EA` | Claim verdict **Verified** |
| `unprovable` | `#56606D` (slate) | `#E8EBEF` | Claim verdict **Cannot be proven**; "unexplained" story share |
| `mixed` | brick on paper, hatched | | Outcome "Mixed" (see the booth grid) |

### Story colours (stacked bars in "Which Story Fits?")
| Story | Hex |
|---|---|
| Death registered | `#6B5B45` (umber) |
| Hostel move-out | `#2E5E78` (steel) |
| Boundary change | `#7A6A9E` (lilac grey) |
| Duplicate clean-up | `#8A8270` (stone) |
| **Unexplained** | `#A3402B` (brick), always the last segment |

## 3. Type

| Role | Font | Size/line | Weight | Notes |
|---|---|---|---|---|
| Display (page title) | Plus Jakarta Sans | 32/38 | 700 | tracking −0.015em, max 1 per page |
| H2 section | Plus Jakarta Sans | 20/26 | 700 | |
| H3 card title | Plus Jakarta Sans | 16/22 | 600 | |
| Body | Plus Jakarta Sans | 15/23 | 400 | max 68ch |
| Small / caption | Plus Jakarta Sans | 13/18 | 500 | `ink-2` |
| Label (overline) | Plus Jakarta Sans | 11/14 | 700 | UPPERCASE, tracking 0.08em, `ink-2` |
| **Numbers, IDs, queries** | JetBrains Mono | 14/20 | 500 | `font-variant-numeric: tabular-nums`. Every number on screen uses this. |
| Big stat | JetBrains Mono | 44/48 | 600 | e.g. `412` deleted |
| Hindi text | Noto Sans Devanagari | +1px vs Latin, line-height 1.6 | 400/600 | |
| Punjabi text | Noto Sans Gurmukhi | +1px, line-height 1.6 | 400/600 | |

Font stack: `"Plus Jakarta Sans", "Noto Sans Devanagari", "Noto Sans Gurmukhi", sans-serif`. Mono: `"JetBrains Mono", ui-monospace, monospace`.

## 4. Space and layout

- **Space scale (4px base):** 4, 8, 12, 16, 24, 32, 48. Nothing in between.
- **App shell:** top bar 56px (wordmark at the left, environment strip at the right), a left rail 200px wide with **text-only** nav, and content capped at 1200px wide.
- **Nav labels:** Overview · Flags · Which story fits? · Claim Court · Citizen · Trust · Report.
- **Banner strip** (always visible, under the top bar): 32px tall, `voter-ink-soft` background, mono 12px text:
  `SYNTHETIC DATA · SAMPLEABAD IS FICTIONAL · FLAGS ARE PATTERNS FOR HUMAN REVIEW, NOT FINDINGS`
- **Grid:** 12 columns with 24px gutters. Flag drawers open from the right, 480px wide.
- **Mobile** (judges on phones for the citizen chat): a single column with 16px gutters, and the rail collapses into a top text menu.

## 5. Components

### 5.1 Verdict stamp (the signature element)
A rubber-stamp label, not a pill.
```
border: 2px solid currentColor; border-radius: 3px; padding: 2px 8px;
font: 700 12px/16px "Plus Jakarta Sans"; letter-spacing: .1em; text-transform: uppercase;
transform: rotate(-1.5deg); background: transparent;
```
- Variants: `VERIFIED` (verified) · `DISPUTED` (unusual) · `CANNOT BE PROVEN` (unprovable) · `NEEDS HUMAN REVIEW` (voter-ink) · `LIKELY BENIGN` (benign).
- On the share card, scale the stamp to 28px text and add a hairline inner border (double-rule stamp).

### 5.2 Flag card (four lines, always this order)
```
┌ BOOTH 47 · DELETION SPIKE                       [NEEDS HUMAN REVIEW] ┐
│ WHAT WE FOUND         412 names left between v1 and v2.              │
│ WHY IT'S UNUSUAL      For this age mix we'd expect about 60 (q < 0.001)│
│ INNOCENT EXPLANATIONS Deaths 9 · Hostel 0 · Boundary 0 · Duplicates 3 │
│ HOW SURE              82% (high) · based on 140 test plantings        │
└──────────────────────────────────────────────────────────────────────┘
```
- The left column holds overline labels, 160px wide. The right column holds body text, with every number in mono.
- A 4px left border in the outcome colour.
- The footer hairline shows `flag a3f91c02e4b1` in mono `ink-3`, followed by "View query".

### 5.3 Story bar ("Which Story Fits?")
- One horizontal stacked bar, 100% wide and 20px tall, in the story colours. Unexplained is always last and in brick.
- Below it, a mono legend row: `Death 9 (2%) · Hostel 0 · Boundary 0 · Dupes 3 (1%) · Unexplained 400 (97%) ±3`.
- CI whiskers are thin `ink` lines on each segment end.
- Toggles for the context sources are text checkboxes ("☐ Use boundary-change log"), styled as square 14px boxes with a `voter-ink` check. The residual number animates over 300ms when a toggle changes, using a plain linear tween with no bounce.

### 5.4 Booth grid (Overview)
- 10 × 10 tiles, 64px square, 4px gap. Each tile shows the booth number top-left in mono 12px and the deletion % bottom-right in mono 13px.
- **Fills:**
  - neutral → `surface` with a `rule` border
  - unusual → `unusual-soft` fill with a 2px `unusual` border
  - likely benign → `benign-soft` fill
  - **mixed → diagonal hatching** (`repeating-linear-gradient(135deg, unusual-soft 0 4px, surface 4px 8px)`); this is the one allowed "gradient", and it is a pattern, not a glow
- **Hover:** the outline becomes `voter-ink` and a tooltip card appears. **Click** opens the flag drawer.
- A legend sits under the grid, each entry a text label with a swatch.

### 5.5 Claim Court
- **Input:** a textarea with a 2px `rule` border; focus turns it `voter-ink`. The button reads "Check this claim".
- **Output:**
  - the normalised claim in italic `ink-2`
  - then one row per sub-claim: `[stamp] sub-claim text` and a mono "query" chip on the right (`count deleted where booth = B047 → 412`)
  - an evidence mini-chart that expands under the row
- **Mirror:** two columns with a 1px dashed `rule-strong` axis between them and the mirror glyph at the top. Under the columns, a line reads `IDENTICAL TREATMENT ✓ 3 sub-claims · same tools · same tolerance`.

### 5.6 Citizen chat
- Bubbles are rectangles with 4px corners. User bubbles use `voter-ink-soft`; RollWatch bubbles use `surface` with a `rule` border. No avatars and no bot face.
- **Status answer block:** the name in its own script at 20px, then the booth (mono), then the status stamp, the reason category, a numbered "Next steps" list, a "How sure" line and the official portal line.
- **Language switcher:** three text tabs, `हिंदी · English · ਪੰਜਾਬੀ`, each in its own script.
- **Voice reply:** the waveform glyph followed by "Play reply (0:12)".

### 5.7 Share card (1080×1350 PNG for Telegram)
- `paper` background, a 48px margin and a hairline frame.
- **Top:** the wordmark plus "Fact check · synthetic demo district".
- **Middle:** the claim in quotes at 40px, then three stamped rows (Verified / Disputed / Cannot be proven), each with one line of evidence in mono.
- **Bottom:** "How sure: 76% · Patterns for human review, not findings", a QR code to `/claims/{id}` and "Treated the same as its mirror claim ✓".
- Hindi and English versions; render with headless Chrome.

### 5.8 Tables
- The header row sits on `sunk`, with the 11px uppercase label style.
- Rows are 40px tall with hairline separators and no zebra stripes.
- Numbers are right-aligned in mono.
- Names are **masked** in auditor views: `मी*** कु*** · M*** K***`.

### 5.9 Buttons
- **Primary:** `voter-ink` background with `#fff` text, a 4px radius, 36px tall, 600 14px text.
- **Secondary:** `surface` background with a 1px `rule-strong` border and `ink` text.
- **Quiet:** text in `voter-ink` with an underline on hover.
- **Focus:** a 2px `voter-ink` outline with a 2px offset. No shadows.

### 5.10 Charts (Recharts, restyled)
- No grid lines, only a baseline in `rule-strong`. Ticks are mono 11px in `ink-3`. Bars are flat, with no rounded tops.
- The reliability chart has a dashed diagonal "perfect" line in `rule-strong`, dots in `voter-ink` sized by n, and the n written next to each dot.
- Animations are off, except the story residual tween.

## 6. Custom glyphs (in `design/glyphs.svg`)

All glyphs are drawn on a 24px grid with a 1.5px stroke, square caps and `currentColor`. They are **ours**: use them sparingly, with a text label next to every glyph.

| id | Drawing | Used for |
|---|---|---|
| `rw-mark` | a fingertip outline with a short vertical ink stroke in `voter-ink` | Logo mark, favicon |
| `rw-spike` | a baseline with five short bars and one tall bar | Deletion/addition spike type |
| `rw-twins` | two offset name-slip rectangles sharing one line | Duplicate cluster type |
| `rw-crowd` | a door frame filled with a 4×4 dot grid | Oversized household |
| `rw-age` | the text "110+" inside a thin box | Impossible age |
| `rw-mirror` | two half-columns with a dashed vertical axis | Mirror test |
| `rw-tally` | four vertical strokes crossed by a diagonal | Counts / eval |
| `rw-wave` | five vertical bars of varying height | Voice reply |
| `rw-script` | the three letters "अ ਅ A" | Language switcher |
| `rw-stamp` | a rotated rectangle with a double border | Empty-state illustration |

## 7. Voice and copy

- **Numbers first, then meaning.** "412 names left. We'd expect about 60."
- **Second person for citizens and plain verbs:** "Your name is in the new list." / "Your name is not in the new list. The likely reason is: shifted."
- Every result ends with **how sure we are** and **what a human should check**.
- **Forbidden in UI copy:** fraud, rigged, scam (except in the BLO scam warning), ghost voters (allowed only inside quoted user claims), "AI-powered", "smart", "magic", party, person and institution names.
- **Allowed procedural text** (template-only): "official voter portal", "Form 6 / 7 / 8", "helpline 1950", "your Booth Level Officer (BLO)".
- **Empty states** are honest sentences, not illustrations: "No flags in this ward. That's normal for most wards."

## 8. Accessibility (no extra build time if followed from the start)
- Every colour meaning also has a text label or stamp.
- Visible focus rings, and keyboard access to the grid tiles (`button` elements).
- `lang="hi"` / `lang="pa"` on Indic text nodes so screen readers switch voice.
- Minimum tap target 40px in the citizen chat.
