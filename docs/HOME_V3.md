# RollWatch v3 home page

The home page at `/` (live at rollwatch-web.onrender.com). One scroll-driven page over a single WebGL scene, in the spirit of immersive studio sites (motion reference: activetheory.net), written from scratch for RollWatch. No third-party site code, shaders, models or audio are used.

It ships inside `web/` (`pnpm --dir web dev`); the previous Audit dashboard moved to `/audit`, and every other page is unchanged.

## What's on the page
| Chapter | What moves | Data (all live from the API) |
|---|---|---|
| Hero | Loader orb counts real loading; chrome ring with the eye hangs from a looping wire; 2,400 voter points drift | `/overview` totals |
| The rumour | Ring drifts back | `/overview` removed count |
| Audit | The points gather into the 10 x 10 booth grid, each cluster coloured by its booth's verdict | `/overview` booths |
| Which story fits | Points recolour in the booth's real story shares (Booth 47: 97% yellow) | `POST /stories/{booth}`, boundary log toggle on Booth 63 |
| Claim court | Verdict rows with the query behind each | `POST /claims/check` |
| Ask | Status card in the voter's script | `POST /citizen/ask` |
| Tested | Blind test, false alarms, try-to-fool-it slider | `/eval/blind`, `/simulate`, `/simulate/limits` |
| Scale | The field spreads wide | `/ops` projection and bench |
| Three questions, Connect | Ring returns to the centre | links to WhatsApp, Telegram, the dashboard (`/audit`), pricing |

## Files
- `web/scene/Scene.ts`: the three.js scene (custom dark light room for the chrome, background glow shader, voter-point shader with field/grid morph and colour tweening). Scroll and pointer only set targets; each frame eases toward them.
- `web/app/page.tsx`: loader inputs, scroll-to-pose mapping (`POSES`), chapter colour modes.
- `web/components/home/Chapters.tsx`: the ten chapters. `web/components/home/Chrome.tsx`: nav pill, progress, note. `web/components/home/Loader.tsx`.
- `web/lib/home-api.ts`: fetch helpers and response types. A missing value shows a dash, never a made-up number.

## Design direction (v3, approved by Rishabh on 28 Oct)
Dark and immersive: near-black page, one cool glow, frosted-glass panels, dark iridescent chrome, soft bokeh points. Only the home page uses it: its styles live in `web/app/home.css`, every rule scoped under `.v3`, so the other pages keep design v2.
Rules that still hold: Geist and Geist Mono; signal colours (yellow, mint, magenta, periwinkle) only as small chips, bar segments or point colours, always with a text label; the hatch for "unexplained"; no stock icons or emoji; no saffron/white/green combinations or party colours; every result says it needs human review; Python computes every number.
Respects `prefers-reduced-motion` (scene holds still, text shows at once) and works without WebGL (text over the plain background).
