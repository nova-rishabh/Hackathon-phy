# RollWatch: 6 pm checkpoint demo (about 4 min)

> A progress demo, not the final. Show what runs end to end on the synthetic district, say plainly what is next.
> Numbers below are what the engine computes on the current data (seed 42). Recheck them on screen before you start.
> Every beat answers one of the three questions: **scalable**, **why not the government alone**, **future-proof**.

## Before you start (5 min earlier)
- API: `.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000` (with `.env` keys) · web: http://localhost:3001
- Open tabs: Audit, Check, Ask, Trust, Account. Sign in once so the Account page has data.
- Backup: if the Wi-Fi or Gemini free tier fails, restart the API with `DEMO_MODE=1`: same cached answers, no network.

## The run

| Time | Beat | On screen | Say |
|---|---|---|---|
| 0:00–0:20 | **Hook** | The demo forward: *"Booth 47 mein 600 naam kaat diye, sabse zyada, aur sab ek community ke!"* | "Forwards like this spread in hours after every roll revision. Nobody can check them. We built the thing that checks them." |
| 0:20–1:00 | **Claim Court** (Check) | Paste it → three rows: **DISPUTED** 600 (computed 412, 46% off, outside 15% tolerance) · **VERIFIED** most removals of any booth (rank 1 of 100) · **CANNOT BE PROVEN** the community part. Each row shows its query. Then the mirror card. | "Gemini only splits the sentence. Python runs a fixed query for each part, and that is where every number comes from. We never infer community from names, so that part is 'cannot be proven', and it says why. The opposite claim gets the same tools and tolerance." |
| 1:00–2:00 | **Which story fits?** (Audit) | Hero: 412 names left Booth 47, ~25 expected. Booth grid: 47 and 12 both stand out. Booth 47: 97% unexplained → **needs human review**. Booth 12: 79% fits a hostel move-out → **likely benign**. Booth 63: switch the boundary log on, unexplained drops 64% → 8%. | "To a rumour these two booths look the same. Only one is unusual, and you can see why: switch an evidence source and the answer moves." |
| 2:00–2:40 | **Citizen** (Ask) | Type मीना कुमारी बूथ 47 → not in the new list, reason unexplained, Form 6 / Form 7, 1950, BLO never asks for OTP or money. Press **Listen** (ElevenLabs voice). | "Wrong spelling, wrong script, still found. She gets the reason, the form to file, and the official portal. Hindi, English, Punjabi, with voice." |
| 2:40–3:10 | **Accounts + bring your own key** | Account page: saved checks, watched booths (Supabase). Keys page: paste your own Gemini or ElevenLabs key, stays in the browser. | "Anyone can run it on their own free key, so cost never blocks a newsroom or a volunteer group. That's how it spreads without us paying for it." |
| 3:10–3:40 | **Trust + scale** | Trust: found 6 of 6 planted anomalies, cleared 7 of 7 decoys, rule error rates per rule, neutrality log, ops strip. Homepage bench: **1.02M voters in 54 s on one core**; duplicate check compares 9.9M pairs, not 521B. | "We publish what we miss and how often each rule fires on innocent records. And it's linear: a whole state is just more booths." |
| 3:40–4:00 | **Close: the three questions** | Homepage "Why this exists" section | "**Why not the government alone?** A self-audit can't settle a rumour about the auditor. They should run `POST /audit` before publishing, and the same open engine stays in independent hands. **Future-proof:** model, voice, data, rules and channels are swappable parts. We just swapped the model and the voice in an afternoon." |

## Say honestly if asked
- Data is fully synthetic (Sampleabad is fictional). No real voter data, by design.
- Still to do by the final: the teammate's blind test (hidden anomalies we never saw), the Telegram bot live, more training districts for the confidence curves (removal spikes rest on 20 flags). Decoys: 7 of 7 cleared.

## Likely questions
- **"Is this just a Gemini wrapper?"** No. Gemini never produces a number. The engine (diff, binomial tests with Benjamini-Hochberg, cross-script duplicate blocking, story attribution, bootstrap) is plain Python and runs with the model switched off.
- **"Cost?"** About ₹0 per check on the free tier or the user's own key; cached answers cost nothing.
- **"What if it's wrong?"** Every output says "needs human review", shows its query, and the Trust page shows each rule's error rate.
