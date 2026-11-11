"""Offline check of the answer-leak checker against MRBench V2's human "Revealing of the Answer" labels.

Usage (canonical workspace cwd, shared-checkout .venv, with -I):
  python -I public_leak_offline.py Directions/testsets/public_v1/leak_mrbench.jsonl [--out FILE]
Gold positive: "Yes (and the answer is correct)". "Yes (but the answer is incorrect)" is reported separately: our checker
looks for the true answer, so flagging a wrong revealed answer is not expected. Only MathDial rows, where the final answer
can be read from the ground-truth solution, are scored with mathcore.leak_check; guards.generic_leak (phrases) runs on all.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

MAIN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MAIN / "src"))
from tutor import guards, mathcore  # noqa: E402

POS = "Yes (and the answer is correct)"
WRONG = "Yes (but the answer is incorrect)"


def prf(rows, pred_key):
    tp = sum(r[pred_key] and r["gold_reveal"] == POS for r in rows)
    fp = sum(r[pred_key] and r["gold_reveal"] == "No" for r in rows)
    fn = sum((not r[pred_key]) and r["gold_reveal"] == POS for r in rows)
    tn = sum((not r[pred_key]) and r["gold_reveal"] == "No" for r in rows)
    p = tp / (tp + fp) if tp + fp else None
    rec = tp / (tp + fn) if tp + fn else None
    f1 = 2 * p * rec / (p + rec) if p and rec else None
    wrong = [r for r in rows if r["gold_reveal"] == WRONG]
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": p and round(p, 3), "recall": rec and round(rec, 3),
            "f1": f1 and round(f1, 3), "flagged_wrong_reveals": f"{sum(r[pred_key] for r in wrong)}/{len(wrong)}"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cases"); ap.add_argument("--out")
    args = ap.parse_args()
    rows = [json.loads(x) for x in Path(args.cases).read_text(encoding="utf-8").splitlines() if x.strip()]
    for r in rows:
        r["phrase_leak"] = guards.generic_leak(r["response"])
        if r["final_answer"] is not None:
            r["value_leak"] = bool(mathcore.leak_check(r["response"], {"kind": "scalar", "value": r["final_answer"]})["leak"])
            r["either_leak"] = r["value_leak"] or r["phrase_leak"]
    scored = [r for r in rows if r["final_answer"] is not None]
    out = {"rows": len(rows), "scored_with_answer": len(scored),
           "gold": dict(collections.Counter(r["gold_reveal"] for r in rows)),
           "phrase_leak_all": prf(rows, "phrase_leak"),
           "value_leak_mathdial": prf(scored, "value_leak"),
           "either_mathdial": prf(scored, "either_leak"),
           "by_tutor_gold_reveal_rate": {t: f"{sum(r['gold_reveal'] == POS for r in g)}/{len(g)}" for t, g in
                                         sorted(collections.defaultdict(list, {k: [r for r in rows if r['tutor'] == k] for k in {r['tutor'] for r in rows}}).items())}}
    print(json.dumps({k: v for k, v in out.items()}, indent=1))
    if args.out:
        Path(args.out).write_text(json.dumps({"summary": out, "rows": rows}, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
