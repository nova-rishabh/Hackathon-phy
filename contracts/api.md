# RollWatch API contract

FastAPI, `http://localhost:8000` (add 10 per extra worktree). All bodies are JSON in UTF-8. The model names refer to `contracts/models.py`. **Change this file only together with `models.py`, and only Rishabh changes it.**

Every endpoint works under `DEMO_MODE=1`. In that mode it reads only `artifacts/` and `cache/llm/`, and a cache miss falls back to the template.

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| GET | `/health` | | `Health` | `versions` = roll, engine and cache entry count |
| GET | `/overview` | | `Overview` | 100 booths, always in `booth_id` order |
| GET | `/flags` | query: `type`, `booth_id`, `band`, `likely_benign`, `status` | `FlagList` | sorted by confidence, highest first |
| GET | `/flags/{flag_id}` | | `Flag` | includes `card` and `stories` |
| POST | `/stories/{booth_id}` | `StoryToggleRequest` | `StoryResult` | the live toggle; recomputes attribution with only the listed context sources |
| POST | `/engine/run` | | `EngineRunResult` | re-runs on the frozen roll; output identical to the artifacts |
| GET | `/eval` | | `EvalResult` | 404 until the blind eval has run |
| GET | `/rules` | | `list[RuleCard]` | notice explainer and rule cards (S4, S5) |
| GET | `/search` | query: `q`, `booth_id`? | `SearchResult` | best matches; names are full here, because this is the citizen's own lookup |
| POST | `/citizen/ask` | `CitizenAsk` | `CitizenAnswer` | shared by the web chat and the bot; `answer_audio_url` is set only when the request came in as audio |
| POST | `/claims/check` | `ClaimCheckRequest` | `ClaimVerdict` | `text` or `image_b64`; the mirror is on by default; `card_png` is set when a card has been rendered |
| GET | `/cards/{claim_id}.png` | | image/png | static, rendered by headless Chrome from web `/card/{claim_id}` |
| POST | `/review/{flag_id}` | `ReviewRequest` | `ReviewResponse` | append-only, hash-chained audit log |
| GET | `/audit/log` | | `list[AuditEntry]` | |
| GET | `/guard/log` | | `GuardLog` | the counts behind the Trust page badge |
| GET | `/report` | | JSON for the `/report` print page | overview, top flags and eval in one call |

## Invariants
- No number in any response comes from the LLM.
- `Flag.needs_human_review` is always `true`.
- Auditor endpoints (`/flags`, `/overview`, `/report`) never return names, only booth, house and ids. The web app masks any name it shows.
- Every generated string in a response has already passed the Neutrality Guard (`guard.passed == true`, or it was replaced by the template).
