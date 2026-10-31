"""Judge calibration (R5 with R1): sample turns for the human raters, then measure agreement.

    python -m tutor_eval.agreement sample --run var/runs/<run_id> --n 30 --out var/labels/sample.csv
    python -m tutor_eval.agreement score --raters a.csv b.csv [--judge var/runs/<run_id>/judge.jsonl] --label leak

The raters fill in copies of the sample independently (eval/judge_calibration/RATER_GUIDE.md). Scoring reports the
raters' agreement with each other, then the judge against their agreed labels, with a bootstrap 95% CI. The
pre-registered gate: kappa >= 0.6 and no worse than the raters' own agreement.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path

from tutor_eval import leakcheck

LABELS = ["leak", "targets_seeded", "mistake_identification", "revealing_of_the_answer", "providing_guidance", "actionability"]
ORDINAL = {"mistake_identification": ["No", "To some extent", "Yes"], "providing_guidance": ["No", "To some extent", "Yes"],
           "actionability": ["No", "To some extent", "Yes"], "leak": ["none", "partial", "full"]}
GATE = 0.6


def cohen_kappa(a: list, b: list) -> float | None:
    if len(a) != len(b) or not a:
        return None
    n, cats = len(a), sorted(set(a) | set(b))
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[c] * cb[c] for c in cats) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def weighted_kappa(a: list, b: list, order: list) -> float | None:
    """Quadratic-weighted kappa for ordinal labels."""
    if len(a) != len(b) or not a:
        return None
    k, n, index = len(order), len(a), {c: i for i, c in enumerate(order)}
    w = lambda i, j: ((i - j) ** 2) / ((k - 1) ** 2)
    ca, cb = Counter(index[x] for x in a), Counter(index[y] for y in b)
    observed = sum(w(index[x], index[y]) for x, y in zip(a, b)) / n
    expected = sum(ca[i] * cb[j] * w(i, j) for i in range(k) for j in range(k)) / (n * n)
    return 1.0 if expected == 0 else 1 - observed / expected


def bootstrap_ci(a: list, b: list, fn, n: int = 2000, seed: int = 0) -> tuple | None:
    if len(a) < 2:
        return None
    rng, values = random.Random(seed), []
    for _ in range(n):
        idx = [rng.randrange(len(a)) for _ in a]
        v = fn([a[i] for i in idx], [b[i] for i in idx])
        if v is not None:
            values.append(v)
    values.sort()
    return (round(values[int(0.025 * len(values))], 3), round(values[int(0.975 * len(values)) - 1], 3)) if values else None


def per_class(truth: list, pred: list) -> dict:
    out = {}
    for c in sorted(set(truth) | set(pred)):
        tp = sum(t == c and p == c for t, p in zip(truth, pred))
        out[c] = {"n": sum(t == c for t in truth), "precision": round(tp / max(1, sum(p == c for p in pred)), 3),
                  "recall": round(tp / max(1, sum(t == c for t in truth)), 3)}
    return out


def sample(run_dir: Path, n: int, out: Path, seed: int = 0, min_per_class: int = 5) -> int:
    """Up to n turns, at least min_per_class of each code-detected leak level where the run has them."""
    turns = []
    for line in (run_dir / "sessions.jsonl").read_text(encoding="utf-8").splitlines():
        s = json.loads(line)
        for t in s["turns"]:
            if t["tutor"]:
                level = max((x["level"] for x in t["leaks"]), key=ORDINAL["leak"].index, default=leakcheck.NONE)
                turns.append({"item_id": f"{s['session']}#{t['index']}", "seeded": ";".join(s["seeded"]), "level": level, **t})
    rng = random.Random(seed)
    rng.shuffle(turns)
    chosen = []
    for level in ("full", "partial", "none"):
        chosen += [t for t in turns if t["level"] == level][:min_per_class]
    chosen += [t for t in turns if t not in chosen][: max(0, n - len(chosen))]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item_id", "problem", "reference_answer", "seeded_misconceptions", "student", "tutor", *LABELS, "rater", "notes"])
        for t in chosen[:n]:
            p = t.get("problem") or {}
            w.writerow([t["item_id"], p.get("prompt", ""), p.get("answer", ""), t["seeded"], t["student"], t["tutor"],
                        *[""] * len(LABELS), "", ""])
    return min(n, len(chosen))


def _read(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return {row["item_id"]: row for row in csv.DictReader(fh)}


def score(raters: list[Path], label: str, judge: Path | None = None) -> dict:
    a, b = (_read(p) for p in raters[:2])
    ids = [i for i in a if i in b and a[i].get(label) and b[i].get(label)]
    xa, xb = [a[i][label] for i in ids], [b[i][label] for i in ids]
    kappa = (lambda x, y: weighted_kappa(x, y, ORDINAL[label])) if label in ORDINAL else cohen_kappa
    result = {"label": label, "items_rated_by_both": len(ids), "human_human_kappa": kappa(xa, xb),
              "human_human_ci95": bootstrap_ci(xa, xb, kappa), "disagreements_to_adjudicate": [i for i in ids if a[i][label] != b[i][label]]}
    if judge:
        agreed = {i: a[i][label] for i in ids if a[i][label] == b[i][label]}
        jl = {}
        for line in judge.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if "error" not in r:
                value = r.get(label)
                if label == "targets_seeded":
                    value = "yes" if r.get("targets") else "no"
                jl[f"{r['session']}#{r['turn']}"] = value
        both = [i for i in agreed if i in jl]
        truth, pred = [agreed[i] for i in both], [jl[i] for i in both]
        jk = kappa(truth, pred)
        hh = result["human_human_kappa"]
        result.update({"judge_items": len(both), "judge_kappa": jk, "judge_ci95": bootstrap_ci(truth, pred, kappa),
                       "per_class": per_class(truth, pred),
                       "gate": "pass" if jk is not None and jk >= GATE and (hh is None or jk >= hh - 1e-9) else "fail"})
    return result


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m tutor_eval.agreement", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--run", required=True, type=Path)
    s.add_argument("--n", type=int, default=30)
    s.add_argument("--out", required=True, type=Path)
    s.add_argument("--seed", type=int, default=0)
    c = sub.add_parser("score")
    c.add_argument("--raters", nargs=2, required=True, type=Path)
    c.add_argument("--label", default="leak", choices=LABELS)
    c.add_argument("--judge", type=Path)
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "sample":
        print(f"Wrote {sample(args.run, args.n, args.out, args.seed)} turns to {args.out}. Each rater fills in a copy.")
    else:
        print(json.dumps(score(args.raters, args.label, args.judge), indent=2))


if __name__ == "__main__":
    main()
