# generator

Synthetic roll generator for the fictional district Sampleabad (10 wards, 100 booths, ~50k electors).

```
python -m generator --config <yaml> --key <answer_key.json> [--seed 42] [--out artifacts]
python -m generator --auto-plant N --seed 7 [--out artifacts]   # training district -> artifacts/training/
```
Outputs: `roll_v1/v2.parquet` + `.csv`, `context/{death_register,hostel_list,boundary_changes}.csv`,
`churn_params.json` (background removal rate by age band, for the engine's expected-deletion model),
and the answer key (JSON list of `contracts.models.Planting`). Auto mode writes its own `answer_key.json` next to the rolls.

## Planting config schema
```yaml
plantings:
  - {plant_id: P01, type: deletion_spike, booth_id: B017, size: 45, is_benign: false}
```
Fields: `plant_id`, `type`, `booth_id`, `size`, `is_benign` (all required); `to_booth` optional (boundary_change).

| type | `size` means | effect |
|---|---|---|
| deletion_spike | records removed | unexplained bulk removal in v2 |
| addition_spike | records added | bulk new electors in new houses in v2 |
| duplicate_cluster | originals duplicated | variant-spelling duplicates with new ids, kept in v2 |
| impossible_age | records | age <18 or >110 in both versions |
| oversized_household | household members | one house with `size` electors (use >15) |
| gender_ratio_swing | F records flipped to M in v2 | booth gender ratio swing |
| hostel_moveout | students removed | students (18-25) in one hostel house leave; `is_benign: true` lists it in hostel_list.csv, false leaves it unlisted (stays unexplained) |
| boundary_change | records moved | houses move to the next booth keeping voter_id; `is_benign: true` lists it in boundary_changes.csv |
| mass_death | deaths | clustered deaths among 50+; `is_benign: true` registers them in death_register.csv |

Background: ~6.8/1000 age-specific deaths (80% registered), ~3% shift-outs, ~3% new electors, ~0.5% cross-script
duplicates (half cleaned in v2), 4 background hostels, 2-3 boundary changes in total, ~0.4% spelling corrections.
Every survivor ages +1 in v2. The real blind config lives in `private/` and is never committed.
