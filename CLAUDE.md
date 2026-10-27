# CLAUDE.md: RollWatch

## Product in 5 lines
RollWatch makes changes in a voter roll auditable, explainable and accessible. It works on a **synthetic** fictional district, Sampleabad (100 booths, about 50k voters).
The engine diffs roll v1→v2, tests booth deletion spikes (binomial + BH), finds cross-script duplicates and runs rule checks.
"Which Story Fits?" attributes each removal to an innocent story or "unexplained" and tests the residual.
Claim Court splits a viral claim into sub-claims, runs fixed queries and returns Verified / Disputed / Cannot be proven, plus a mirror claim.
A citizen chat (web + Telegram, Hindi/English/Punjabi, Hindi voice) explains a voter's status and next steps.

Read before coding: `docs/START_HERE.md` (what, the edge, demo numbers, decisions), `docs/TRD.md` (contracts, algorithms, complexity), `docs/DESIGN_SYSTEM.md` v2 (any UI), `docs/ACTION_PLAN.md` (what's in scope now).

## Folder ownership: only touch your folder
`contracts/` + this file: Rishabh only · `generator/`: A1 · `engine/`: A2 · `api/`: A1 (`api/citizen.py`: B2) · `web/`: B1 · `bot/`: B2 · `private/`: partner only, **never read, import or list it**.

## Non-negotiable rules
- **Python computes every number shown. The LLM only phrases text, splits claims and reads images.** It never writes code or invents numbers.
- **Neutrality:** generated text never contains fraud/rigging words or party, person or institution names. Everything outbound passes through `api/guard.py`. Procedural text comes only from `api/constants.py`.
- **Every output carries reasoning + confidence + "needs human review".**
- **No real voter data and no real places in the data.** Never infer religion, caste or community. Claims that need it return `unprovable`.
- **Auditor views mask names.** A full name appears only in the citizen's own lookup result.
- **Contracts in `contracts/models.py` are the source of truth.** Never change them; ask Rishabh.
- **UTF-8 everywhere:** `PYTHONUTF8=1`, `open(..., encoding="utf-8")`, `json.dump(..., ensure_ascii=False)`.
- **UI:** design system v2 (butter.video-inspired): light only, tokens from `design/tokens.css` v2, Geist + Geist Mono, glyphs from `design/glyphs.svg`. Colour only as small signal chips. **No lucide/heroicons/emoji icons, no gradients (except the hatch), no shadows, no dark mode or dark panels, no Inter/Space Grotesk/Plus Jakarta.** No logo drawing: Rishabh designs it.
- **Testing:** don't write test suites. Add only your one smoke check in `smoke_test.py` (TRD §9). Ship.

## Run
```
uv venv --python 3.12 .venv && .venv\Scripts\activate && uv pip install -r requirements.lock
python -m generator --config <yaml> --key <answer_key.json> --seed 42
python -m engine.run                      # writes artifacts/flags.json, stories.json
python -m engine.eval --key <answer_key.json>
uvicorn api.main:app --port 8000
python -m bot
cd web && pnpm dev                        # demo: pnpm build && pnpm start
python smoke_test.py
```
Ports: API 8000, web 3000 (+10 per extra worktree). `DEMO_MODE=1` serves only `artifacts/` + `cache/llm/`.

## Git
Commits in Rishabh Kataria's name only, with no Co-Authored-By line. Small commits with clear messages, often. They prove the work was done during the event. Commit only inside your folder, and merge to `main` at the gates in `docs/ACTION_PLAN.md`.
