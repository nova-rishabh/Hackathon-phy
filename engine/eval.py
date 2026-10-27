"""python -m engine.eval --data <dir> --flags flags.json --key answer_key.json --out eval.json

The ONLY module that reads an answer key (passed explicitly on the CLI; also used by run.py for the
training district's calibration).
A planting matches a flag when the flag type fits the planting type and (same booth OR voter_ids overlap).
hostel_moveout / boundary_change / mass_death plantings are deletion events, so they match deletion_spike.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from contracts.models import EvalResult, Flag, Miss, Planting, ReliabilityBin, TypeScore

KIND_TO_FLAG = {"hostel_moveout": "deletion_spike", "boundary_change": "deletion_spike", "mass_death": "deletion_spike"}


def load_key(path) -> list[Planting]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Planting.model_validate(p) for p in raw]


def load_background(key_path) -> list[dict]:
    """<key>.background.json: real-looking truths the generator adds that are not plantings (e.g. cross-script
    duplicates). A flag on one is a correct catch, so it is not counted as a false positive."""
    p = Path(key_path)
    p = p.with_name(p.stem + ".background.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def on_background(f: Flag, background: list[dict]) -> bool:
    return any(f.type == b["type"] and set(f.scope.voter_ids) & set(b["voter_ids"]) for b in background)


def flag_type_of(p: Planting) -> str:
    return KIND_TO_FLAG.get(p.type, p.type)


def matches(f: Flag, p: Planting) -> bool:
    if f.type != flag_type_of(p):
        return False
    return f.scope.booth_id == p.booth_id or bool(set(f.scope.voter_ids) & set(p.voter_ids))


DECOY_STORY = {"mass_death": "death_registered", "hostel_moveout": "hostel_moveout", "boundary_change": "boundary_change"}


def decoy_cleared(p: Planting, flags: list[Flag], anomalies: list[Planting]) -> bool:
    """A decoy is cleared when no raised flag lands on it. When it shares a booth with a real anomaly, the booth
    flag is right to fire, so the decoy counts as cleared only if the engine attributes its records to the matching
    innocent story (e.g. all 10 planted deaths matched to the death register), i.e. it was not mistaken for the anomaly."""
    for f in flags:
        if not matches(f, p) or f.likely_benign:
            continue
        if not any(matches(f, a) for a in anomalies):
            return False
        code = DECOY_STORY.get(p.type)
        got = next((s.count for s in (f.stories.stories if f.stories else []) if s.code == code), 0)
        if got < 0.9 * len(p.voter_ids):
            return False
    return True


def evaluate(flags: list[Flag], key: list[Planting], background: list[dict] | None = None) -> EvalResult:
    anomalies = [p for p in key if not p.is_benign]
    decoys = [p for p in key if p.is_benign]
    found, misses = 0, []
    tp = {}
    fn = {}
    for p in anomalies:
        t = flag_type_of(p)
        hit = [f for f in flags if matches(f, p) and not f.likely_benign]
        if hit:
            found += 1
            tp[t] = tp.get(t, 0) + 1
        else:
            fn[t] = fn.get(t, 0) + 1
            any_hit = [f for f in flags if matches(f, p)]
            misses.append(Miss(plant_id=p.plant_id, type=p.type,
                               why="flagged but judged likely benign" if any_hit else "no flag of this type at the planted location"))
    cleared = sum(decoy_cleared(p, flags, anomalies) for p in decoys)
    fp = {}
    true_flags = []
    for f in flags:
        is_true = any(matches(f, p) for p in anomalies) or on_background(f, background or [])
        true_flags.append(is_true)
        if not is_true:
            fp[f.type] = fp.get(f.type, 0) + 1
    types = sorted(set(tp) | set(fn) | set(fp))
    by_type = []
    for t in types:
        a, b, c = tp.get(t, 0), fp.get(t, 0), fn.get(t, 0)
        by_type.append(TypeScore(type=t, tp=a, fp=b, fn=c, precision=a / (a + b) if a + b else 0.0,
                                 recall=a / (a + c) if a + c else 0.0))
    edges = [0.0, 0.25, 0.5, 0.75, 1.0000001]
    rel = []
    for lo, hi in zip(edges, edges[1:]):
        idx = [i for i, f in enumerate(flags) if lo <= f.confidence < hi]
        if idx:
            rel.append(ReliabilityBin(bin_lo=lo, bin_hi=min(hi, 1.0), mean_conf=sum(flags[i].confidence for i in idx) / len(idx),
                                      frac_true=sum(true_flags[i] for i in idx) / len(idx), n=len(idx)))
    return EvalResult(planted_anomalies=len(anomalies), planted_decoys=len(decoys), found=found, decoys_cleared=cleared,
                      by_type=by_type, benign_fp_rate=(len(decoys) - cleared) / len(decoys) if decoys else 0.0,
                      reliability=rel, misses=misses)


RULES = {
    "deletion_spike": "removals in a booth exceed the age-adjusted background rate (one-sided binomial, Benjamini-Hochberg q < 0.05)",
    "addition_spike": "additions in a booth exceed the background rate (one-sided binomial, Benjamini-Hochberg q < 0.05)",
    "duplicate_cluster": "two or more records in one booth with matching name across scripts (score >= 0.88), same gender, age within 1",
    "impossible_age": "elector age below 18 or above 110",
    "oversized_household": "more than 15 electors at one house number",
    "gender_ratio_swing": "female share of a booth moves by more than 8 percentage points between versions",
    "relation_conflict": "the named relative's own record is in the same house and the pair is impossible (parent not older, or husband/wife gender mismatch)",
}


def official_cards(checks: dict, anomalies: list[Planting]) -> list[dict]:
    """How often each official discrepancy check fires on records that hide no planted anomaly."""
    ids = set().union(*(set(p.voter_ids) for p in anomalies)) if anomalies else set()
    out = []
    for cid, c in checks.items():
        n = len(c["items"])
        hit = sum(bool(set(i["voter_ids"]) & ids) for i in c["items"])
        out.append({"rule": cid, "definition": f"{c['definition']} · official check, measured, never raised · trips {n:,}",
                    "flags_total": n, "flags_raised": 0, "on_planted_anomaly": hit,
                    "false_positive_rate": round((n - hit) / n, 4) if n else None})
    return out


def rule_cards(flags: list[Flag], key: list[Planting], n_voters: int | None = None, background: list[dict] | None = None,
               official: dict | None = None) -> dict:
    """Per-rule error rates (PRD M10). A flag is 'raised' unless the engine itself judged it likely benign.
    false_positive_rate = raised flags that match no planted anomaly / raised flags. Flags cleared as likely benign
    are reported separately with how many of them sit on a planted innocent decoy."""
    anomalies = [p for p in key if not p.is_benign]
    decoys = [p for p in key if p.is_benign]
    out = []
    for t in sorted(set(RULES) | {f.type for f in flags}):
        fs = [f for f in flags if f.type == t]
        raised = [f for f in fs if not f.likely_benign]
        cleared = [f for f in fs if f.likely_benign]
        tp = [f for f in raised if any(matches(f, p) for p in anomalies) or on_background(f, background or [])]
        planted = [p for p in anomalies if flag_type_of(p) == t]
        found = [p for p in planted if any(matches(f, p) and not f.likely_benign for f in flags)]
        on_decoy = [f for f in cleared if any(matches(f, p) for p in decoys)]
        fp = len(raised) - len(tp)
        out.append({
            "rule": t, "definition": RULES.get(t, ""), "flags_total": len(fs), "flags_raised": len(raised),
            "flags_cleared_likely_benign": len(cleared), "cleared_on_planted_decoy": len(on_decoy),
            "raised_matching_planting": len(tp), "raised_not_matching_planting": fp,
            "false_positive_rate": round(fp / len(raised), 4) if raised else None,
            "planted": len(planted), "planted_found": len(found),
            "recall": round(len(found) / len(planted), 4) if planted else None,
            "raised_per_10k_voters": round(10000 * len(raised) / n_voters, 2) if n_voters else None,
        })
    if official:
        out += official_cards(official, anomalies)
    return {"measured_on": "synthetic district with a planted answer key", "n_voters_v2": n_voters,
            "note": "A flag that matches no planting and no background truth (the generator's ~0.5% realistic "
                    "cross-script duplicates) is counted as a false positive. Every flag still needs human review.",
            "rules": out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")  # accepted for symmetry with engine.run; not needed
    ap.add_argument("--flags", default="artifacts/flags.json")
    ap.add_argument("--key", required=True)
    ap.add_argument("--out", default="artifacts/eval.json")
    ap.add_argument("--rules", help="per-rule error rates (PRD M10); default <out dir>/rules.json")
    a = ap.parse_args()
    flags = [Flag.model_validate(f) for f in json.loads(Path(a.flags).read_text(encoding="utf-8"))]
    bg = load_background(a.key)
    res = evaluate(flags, load_key(a.key), bg)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(res.model_dump_json(indent=1), encoding="utf-8")
    n_voters = None
    try:
        from .data import load
        n_voters = len(load(a.data or Path(a.flags).parent).v2)
    except Exception:
        pass
    op = Path(a.flags).parent / "official_checks.json"
    off = json.loads(op.read_text(encoding="utf-8")) if op.exists() else None
    cards = rule_cards(flags, load_key(a.key), n_voters, bg, off)
    rp = Path(a.rules) if a.rules else Path(a.out).parent / "rules.json"
    rp.write_text(json.dumps(cards, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in cards["rules"]:
        print(f"  {r['rule']:<20} raised={r['flags_raised']:<5} fp_rate={r['false_positive_rate']} "
              f"found={r.get('planted_found')}/{r.get('planted')} cleared_benign={r.get('flags_cleared_likely_benign')}")
    print(f"found {res.found}/{res.planted_anomalies}, decoys cleared {res.decoys_cleared}/{res.planted_decoys}")


if __name__ == "__main__":
    main()
