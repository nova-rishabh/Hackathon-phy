# RollWatch: final brief

Live: **rollwatch-web.onrender.com** · WhatsApp **+91 80764 99841** · Telegram **@Rollwatch_bot** · API rollwatch-api.onrender.com
Before presenting: open the site 2 minutes early (first load can take ~40 s), keep the laptop on (WhatsApp + Telegram run on it).

---

## 1. Prompt to update the slides (paste into Claude with the current deck PDF attached)

```
Update the attached RollWatch pitch deck. Keep the existing design exactly (near-white page, grey panels,
Geist regular-weight two-tone headlines, small colour chips only, light only, no gradients, shadows, emoji,
stock icons or party colours). Change only content. Use only these numbers; never invent any.

1. Keep the title slide.
2. Problem slide: add the real context. In the 2025-26 voter-list revision, software flagged crores of
   electors as "logical discrepancies" (~1.3 crore in West Bengal) with no published error rates, and 91% of
   decided appeals in West Bengal restored the voter. Rumours like "600 names cut from one booth" spread in hours.
3. How it works (one diagram): old roll + new roll -> Python engine (diff, binomial test + Benjamini-Hochberg,
   cross-script duplicates, "which story fits") -> numbers + confidence -> AI only phrases words -> neutrality
   guard -> web / WhatsApp / Telegram / share card. Label: "every number comes from code".
4. Proof: Booth 47: 412 removed vs ~25 expected, 97% unexplained -> needs human review. Booth 12: 79% match a
   hostel move-out -> likely benign. Scoreboard: 6/6 anomalies found, 7/7 innocent decoys cleared, 0 missed.
   When we say ~93%, we are right 90% of the time.
5. NEW slide "We tested the official checks": we ran 7 reported discrepancy checks on our district. They flag
   81-100% innocent records (marriages, spelling fixes, big families). Parent-gap check: 113 tripped, 81%
   innocent; name changed: 196, 100% innocent. Footnote: synthetic data. Point: a check without a published
   error rate creates notices and fear; RollWatch publishes one per rule.
6. Claim Court: "Booth 47 mein 600 naam kaat diye, sabse zyada, aur sab ek community ke!" -> 600 DISPUTED
   (412 computed, 46% off) · most removals VERIFIED (rank 1 of 100) · community CANNOT BE PROVEN (we never
   infer it). Mirror claim gets the same treatment. Every result becomes a share image sent back into the chat.
7. THE THREE QUESTIONS (one slide, three columns):
   - Scales: per-booth and linear; 1.02M voters in 54 s on one laptop core; 9.9M pairs instead of 521B;
     WhatsApp/Telegram, no install; same method fits ration-card or pension lists.
   - Why the government can't do it alone: a self-audit can't settle a rumour about the auditor. Inside: an
     office runs it on a draft before publishing ("Run it" page). Outside: newsrooms and citizens run the same
     open engine, so both sides agree on the numbers.
   - Future-proof: data, rules, AI model, language and channel are swappable parts; we swapped the model and
     voice in an afternoon; every change is re-measured by the blind test.
8. Citizen: name in any script or spelling -> status, likely reason, Form 6/8, 1950 helpline, "a BLO never asks
   for OTP or money". Hindi, English, Punjabi, with Hindi voice notes on WhatsApp.
9. Limits + ask: synthetic data only; needs real-roll calibration; not affiliated with any official body.
   Ask: one newsroom or election-watch NGO pilot in the next revision. Show the live links and WhatsApp number.
```

---

## 2. What to know (60-second version)

- **What:** RollWatch explains changes in a voter list. For each booth it says whether removals have an innocent reason (death, hostel move-out, boundary change, duplicate) or **no explanation**, so a person should check. It also fact-checks viral claims and tells a voter why their name changed and which form to fill.
- **Not about voting or parties.** It checks the *list of voters*, never names a party or person, and never guesses religion or caste.
- **Data is synthetic** (fictional district "Sampleabad", ~51,000 voters). The method and every number are real code output.
- **AI's job is small:** Gemini only splits a claim into parts and phrases text; ElevenLabs does voice. **Python computes every number.** Turn the AI off and the verdicts don't change.
- **Every output** says "needs human review", shows its reasoning and a confidence.
- **Pages:** Audit (home) · Check (claims) · Ask (your name) · Run it (upload your own roll) · Trust (our error rates, the official checks, the neutrality guard).

## 3. Top questions (short answers)

1. **Is this just a ChatGPT/Gemini wrapper?** No. The statistics engine is plain Python; the AI only splits sentences and writes the words. Every row shows the query that produced its number.
2. **Can't the government do this?** They should, and can run it before publishing ("Run it" page). But a self-audit can't settle a rumour about the auditor, so the same open tool must also be with citizens and newsrooms.
3. **Does it scale?** Yes: 1.02 million voters in 54 seconds on one laptop core; a state is just more booths in parallel.
4. **Fake data proves nothing?** It proves the method against a known answer key: we found 6 of 6 hidden problems and cleared 7 of 7 innocent look-alikes. Real data would need recalibration.
5. **What does "likely benign" mean?** The booth lost many names, but a record explains them (e.g. students leaving a hostel) and what's left is normal. A person should still confirm.
6. **How is this better than the official checks?** We ran 7 of them: 81-100% of what they flag is innocent on our data. We publish an error rate for every rule and explain *which story fits* before anyone gets a notice.
7. **Do you infer religion or caste?** Never. That part of a claim returns "cannot be proven".
8. **What does 93% confidence mean?** Flags we rate ~93% turned out right 90% of the time on a separate test district.
9. **Cost?** About ₹0 per check (free tier, caching, or the user's own key).
10. **Did AI write the code?** We used Claude Code as a coding assistant and say so in the README. The design, statistics and review are ours.
