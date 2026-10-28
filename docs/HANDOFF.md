# Handoff prompt for Phase 2 (paste into a new Claude Code session on this repo)

```
You are taking over RollWatch for Phase 2 of a hackathon. Phase 1 is complete, live and verified. Rishabh Kataria
(the owner) will tell you what Phase 2 requires right after this message. Your first job is to get oriented and
organised, not to build. Do not start any feature until he has given you the Phase 2 requirements.

Repo: C:\Users\Admin\Desktop\phy-hacl\Hackathon-phy (GitHub nova-rishabh/Hackathon-phy, branch main).

STEP 1: READ, IN THIS ORDER (do not re-derive numbers; they come from the engine)
1. CLAUDE.md: the binding rules (summarised below; CLAUDE.md wins on any conflict).
2. docs/SESSION_LOG.md: read the last two entries ("28 Oct 2026: final day" and "late session").
3. README.md: what exists and where.
4. docs/START_HERE.md §2a: the three questions every pitch must answer.
5. docs/FINAL_BRIEF.md: the 60-second brief, the demo-proof checklist and the deck-update prompt (§1).
6. docs/PITCH_PREP.md: likely judge questions with answers and measured numbers.
7. docs/DESIGN_SYSTEM.md: UI rules (v2, light plus a token-only dark theme).

STEP 2: ORGANISE, THEN REPORT BACK BEFORE BUILDING
- Run `git status` and `git log --oneline -15`. Untracked: deliver/score2.wav, deliver/voice-samples/, .claude/
  (leave them; ask Rishabh before committing audio).
- Check the live system once (no polling loops; Rishabh dislikes them):
  `python scripts/warmup.py` (every line should say OK), then GET /health, /eval/blind and /simulate/limits on the API.
- Give Rishabh a short status: what is live, what is open, and any risk you see for Phase 2. Then ask for the
  Phase 2 requirements if he has not given them yet.
- When he gives them: restate them as a numbered plan with what "done" means for each. Ask only about real
  ambiguities, then build in small commits.

WHAT IS LIVE (Phase 1)
- Web https://rollwatch-web.onrender.com (Next.js 15, web/). API https://rollwatch-api.onrender.com (FastAPI, Docker;
  it builds the synthetic district plus 4 training districts at image build). Render auto-deploys every push to main
  (API about 4 min, web about 3 min; the web goes live about a minute before the API, so new UI must tolerate the
  older API response).
- WhatsApp +91 80764 99841 (wa/worker.js, Baileys) and Telegram @Rollwatch_bot (`python -m bot`) run on Rishabh's
  laptop with API_BASE=https://rollwatch-api.onrender.com. Never run two WhatsApp workers at once.
- Supabase (accounts), Upstash Redis (shared state), Razorpay (test mode), Gemini (claim splitting and phrasing
  only), ElevenLabs (Hindi voice "Devi").
- Pages: Audit (home: booth grid, Which Story Fits, flags, 10-stop onboarding tour, `/?tour=1`), Check (Claim
  Court plus share card), Ask (citizen lookup in hi/en/pa, voice, documents checker), Run it (upload a roll), Trust
  (blind test, false alarms counted, "Try to fool it", rule error rates, official checks, national scale),
  Pricing, Account, Keys. Dark theme via a sun/moon icon in the header.

KEY NUMBERS (engine output, seed 42; recheck on /trust before quoting)
- Booth 47: 412 removed vs about 25 expected, 401 (97%) unexplained, needs human review. Booth 12: 79% hostel
  move-out, likely benign. Booth 63: mixed.
- Blind test (planted by a separate agent): 9 of 9 found, 6 of 6 decoys cleared. Of 283 flags raised for review,
  263 were real (93%); 0 false alarms on booth spikes; the 20 false ones are 14 duplicate pairs and 6 relation
  conflicts.
- Try to fool it: a booth needs a median of 19 hidden names (8 to 40) to reach review. Booth 23: 17 shows a
  spike, 18 is caught. Spread 1,000 names over all 100 booths and only 2 new booths reach review (the honest
  blind spot; say it before a judge does).
- Scale: 97.8 crore electors audited in about 13.5 min on 64 cores; peak citizen traffic (about 190 checks/s) on
  2 machines; 163 citizen answers/s measured on 4 processes.
- Name matching: 0 of 2,950 names not in the roll matched anyone; unmatched names say "Not listed".

RULES (from CLAUDE.md; binding)
- Commits in Rishabh Kataria's name only. Never add a Co-Authored-By line or any Claude/AI attribution.
- Python computes every number shown. The LLM only phrases text, splits claims and reads images; it never
  invents numbers. Procedural text lives in api/constants.py (en/hi/pa); outbound text passes api/guard.py.
- Neutrality: never name parties, people or institutions; no fraud/rigging words. Never infer religion, caste or
  community. Synthetic data only; no real voter data or real places. Auditor views mask names.
- Every output carries reasoning, confidence and "needs human review".
- Never read, list or import private/ (the blind-test key lives there).
- UI: docs/DESIGN_SYSTEM.md. Geist and Geist Mono, colour only as small signal chips, glyphs only from
  design/glyphs.svg (draw new ones in the same style if needed). No icon libraries, emoji, gradients (except the
  hatch) or decorative shadows. Dark mode is token overrides only. Check every UI change at 1366x768 and 375 px,
  in light and dark.
- Contracts in contracts/models.py are the source of truth; ask Rishabh before changing them.
- Secrets live only in .env, web/.env.local and Render. Never print, commit or paste them. Before every push,
  scan `git log -p origin/main..main` for any .env value.
- Before pushing: `python smoke_test.py`, `python -m bot.smoke_checks`, `python tests/test_name_matching.py`
  (use .venv\Scripts\python.exe, PYTHONUTF8=1, PYTHONPATH=.) and `pnpm --dir web build`.
- Push only when Rishabh says so. If he says "freeze before the pitch", commit locally and do not push. After a
  push, check the live site once (wait about 6 minutes, then one check), never in a loop.

WORKING NOTES THAT SAVE TIME
- Do not run `pnpm --dir web build` while the dev server (`web-check` in .claude/launch.json, port 3010 against the
  API on 8010) is running: they share web/.next and the dev server breaks. Stop it first; if it already broke,
  delete web/.next and restart it.
- If the in-app browser pane is hidden, pages stall on the route loader and screenshots fail. Use headless
  Playwright from the system Python instead (`python` has playwright; the .venv does not).
- On Windows use 127.0.0.1, not localhost, for scripted local requests (localhost adds about 2 s per call).
- Demo-proofing: `python scripts/warmup.py` 5 minutes before any pitch; if anything fails or Wi-Fi is bad,
  `powershell -File scripts\demo_local.ps1`, then `python scripts/warmup.py --local`, then present from
  http://127.0.0.1:3000.

PITCH DECK (Phase 2 may require it)
The deck is not in the repo; Rishabh has it. If Phase 2 needs slides, or anything you build changes a number or a
feature that the deck shows, you must update the deck:
1. Ask Rishabh for the latest deck file (PDF or PPTX) and keep its design exactly: near-white page, grey panels,
   Geist regular-weight two-tone headlines, small colour chips only, no gradients, shadows, emoji, stock icons or
   party colours. Change content, not design. If he says the deck should be dark, use the site's dark tokens.
2. Start from the deck-update prompt in docs/FINAL_BRIEF.md §1 and bring every number up to date from the live
   API (/trust, /eval/blind, /simulate/limits) and docs/PITCH_PREP.md. Never invent a number.
3. Add or refresh these slides: "We tested ourselves" (blind test plus false alarms counted: 263 of 283 real, 0
   on spikes); "Try to fool it" (detection limit per booth, the Booth 23 17 vs 18 moment, and the spread-thin
   blind spot stated openly); any Phase 2 feature with a screenshot from the live site.
4. Every deck must answer the three questions with something we can show: how it scales, why the government
   can't do this alone, and why it's future-proof (docs/START_HERE.md §2a).
5. Keep the closing "Limits + ask" slide honest: synthetic data, needs real-roll calibration, not affiliated with
   any official body.
6. Deliver the deck the way Rishabh asks (PPTX or PDF), and say which slides changed and why.

WHEN YOU FINISH ANY PIECE OF WORK
Report what you verified live versus only locally, what you could not check, and anything Rishabh must do
himself (for example run a Razorpay test checkout, start the WhatsApp worker, or rotate a key). Append a short
dated entry to docs/SESSION_LOG.md.
```
