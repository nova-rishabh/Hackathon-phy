# Handoff prompt (paste into a new Claude Code session on this repo)

```
You're continuing RollWatch, a hackathon project that is feature-complete and live. Your job is to keep it stable
for the final presentation and finish a short list of loose ends. Repo: C:\Users\Admin\Desktop\phy-hacl\Hackathon-phy
(GitHub nova-rishabh/Hackathon-phy, branch main). Owner: Rishabh Kataria.

READ FIRST: CLAUDE.md (rules), README.md (what exists), docs/FINAL_ACTION_PLAN.md (done/remaining),
docs/FINAL_BRIEF.md and docs/PITCH_PREP.md (pitch facts). Do not re-derive numbers; they come from the engine.

RULES (from CLAUDE.md, binding)
- Commits in Rishabh Kataria's name only, never a Co-Authored-By or any Claude attribution.
- Python computes every number shown; the LLM only phrases text. Procedural text lives in api/constants.py;
  outbound text passes api/guard.py. Never name parties, people or institutions; no fraud/rigging words.
- Never read, list or import private/ (the blind-test key lives there). artifacts_blind/ is git-ignored.
- No real voter data. Never infer religion, caste or community.
- UI: design system v2 (docs/DESIGN_SYSTEM.md): light + dark theme (tokens only), Geist/Geist Mono, colour only as small chips,
  no icon libraries, emoji, gradients (except the hatch) or shadows. Check UI at 1366x768 and 375 px; measure.
- Secrets live only in .env, web/.env.local and Render. Never print, commit or paste them. Before every push,
  scan `git log -p origin/main..main` for any .env value.
- Tests: no test suites. Run `python smoke_test.py` and `python -m bot.smoke_checks` (use .venv\Scripts\python.exe,
  PYTHONUTF8=1) and `pnpm --dir web build` before pushing. Keep web/pnpm-lock.yaml in sync.
- Render auto-deploys every push to main (API ~4 min, web ~3 min). If the owner says "freeze before the pitch",
  commit locally only and do not push.
- The owner dislikes long polling loops: check live endpoints once, not in a loop.

WHAT'S LIVE
- Web https://rollwatch-web.onrender.com (Next.js 15 in web/), API https://rollwatch-api.onrender.com (FastAPI,
  Docker; builds the synthetic district + 4 training districts at image build).
- WhatsApp +91 80764 99841: wa/worker.js (Baileys) runs on the owner's laptop:
  `cd wa; $env:API_BASE='https://rollwatch-api.onrender.com'; node worker.js`. Never run two workers at once
  (they fight over the session; stop the old one first).
- Telegram @Rollwatch_bot: `.venv\Scripts\python.exe -m bot` with API_BASE set the same way, on the laptop.
- Supabase (accounts), Upstash Redis (optional shared state via REDIS_URL), Razorpay (test keys on Render),
  Gemini + ElevenLabs (voice "Devi"). The keep-awake GitHub workflow stops itself after 29 Oct.

LOOSE ENDS, IN ORDER
1. Verify the latest deploy once: GET /health, /eval/blind (9/9, 6/6), /wa/status (connected), /billing/config
   (enabled, test_mode), and that home "/" HTML has og:image and a /card/<id> page has its own og:image.
2. Redis: done (live /wa/status shows "shared_state": "redis").
3. Razorpay: the owner runs one test checkout on /pricing with a Razorpay test card; confirm the page shows
   "Subscribed. Reference sub_..." (server verified the signature). Nothing is stored yet: optionally add a
   Supabase table + POST /billing/webhook (verify X-Razorpay-Signature) for renewals/cancellations.
4. Small polish (optional): the cycling booth tile (47 -> 12 -> 63) inside the home headline.
5. After the event: owner resets the Upstash password (it was pasted in chat), deletes
   .github/workflows/keepalive.yml, and rotates any key that appeared in chat.

ALSO DONE (28 Oct evening): monitoring (/ops/monitoring), Razorpay webhook + lifecycle, PDF ingestion, async
jobs with private job tokens, reports + review history + recalibration, workspaces/roles/API keys (roles from
membership), caching + incremental audits, 7 languages (header picker removed 28 Oct), access-control fixes (tests/test_access_control.py).
Redis is live. tests/ exists now; run them with PYTHONPATH=. .venv\Scripts\python.exe tests/test_<name>.py.

DONE: KEEP AS IS UNLESS ASKED
Engine (diff, binomial + BH, which-story-fits, cross-script duplicates, rule checks, 7 official discrepancy
checks measured not raised, calibration on 4 training districts), blind test, Claim Court + share card PNG,
citizen answers (hi/en/pa, Gurmukhi names, voice, documents guide by date of birth), Run it (/audit), Trust
(blind test, rules, official checks, national scale from ECI 2024 table, why statistics), Pricing + Razorpay
subscriptions, booth watch alerts, human review (hash chain), rate limits/size caps (api/limits.py), shared
state (api/shared.py), link previews, loaders, 48 s film (deliver/), real-roll adapter (engine/adapters/inrolls.py).

When you finish, report what you verified live (and what you only tested locally), and anything the owner must do.
```
