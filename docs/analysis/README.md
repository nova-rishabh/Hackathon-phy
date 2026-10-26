# Analysis scripts (research only, not product code)

Written on 26 Oct 2026, before the event, to choose a problem statement. Run with Python 3 (standard library only).

| Script | What it does | Run |
|---|---|---|
| `ana.py` | Win rate by theme/tech in the reference Devpost dataset | `python ana.py All_data.csv` |
| `crowding_themes.py`, `crowding_winners.py` | Crowding analyst's theme keyword variants and winner reading | `python crowding_themes.py All_data.csv` |
| `sim.py` | Monte Carlo of the single overall prize by problem statement (base and stress scenarios) | `python sim.py` |
| `sim2.py` | Same model, with elite execution and over-scoped builds | `python sim2.py sim.py` |
| `sim3.py` | Stress test: Electoral crowded, and judges wary of politics | `python sim3.py sim.py` |

`All_data.csv` (~27 MB, about 6,900 projects from other hackathons) is not committed.
