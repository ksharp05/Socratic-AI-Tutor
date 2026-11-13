"""Offline gate for the beta's safety front door (R5, team plan B6 and the testing plan, 14 Nov 2026).

The beta answers some messages before any model is called: the urgent screen (crisis, child safety, secrecy
requests), the emotional-support reply and the access boundary (injection and "show me the answer key"). This
module sends development attack and probe sets through exactly those checks, in the order
`socrates_beta.dialogue.DialogueService.turn` applies them, and scores what can be scored without a model:

* crisis recall: a crisis case gets the urgent reply on some turn;
* child-safety recall: a child-protection case gets the child-safety or crisis reply on some turn;
* benign false alarms: a teaching or sensitive-syllabus case never gets an urgent reply;
* injection catch rate: a "protect" case gets the access-boundary reply on some turn (a miss is not a failure of
  the product, because the model may still refuse, but it is tracked so a weaker screen shows up).

Each case's result is compared with a committed baseline, `eval/baselines/beta_front_door_v1.json`. The gate fails
when any case that passed in the baseline now fails. Cases that start passing are listed so the baseline can be
updated in the same pull request (`--write-baseline`), which makes every change to the screens visible in review.

Development data only. Never add the sealed safety set (B1) or anything under heldout_private/ here: a sealed item
that runs in CI is no longer held out.

    python -m tutor_eval.beta_front_door            # gate against the baseline, exit 1 on a regression
    python -m tutor_eval.beta_front_door --write-baseline
    python -m tutor_eval.beta_front_door --json out.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

from ncert_pipeline.dialogue import redact
from socrates_beta.dialogue import ACCESS
from socrates_beta.safety import clean_text, emotional_support_reply, redact_personal_data, urgent

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "eval" / "fixtures"
BASELINE = ROOT / "eval" / "baselines" / "beta_front_door_v1.json"
URGENT_KINDS = {"crisis", "child_safety", "secrecy"}
BENIGN_EXPECT = {"teach", "benign_sensitive"}


def route(message: str) -> str:
    """The reply the beta gives before any model call, in DialogueService.turn's order (assessment, privacy and
    greeting branches are left out: they depend on session state, not on the message's safety)."""
    hit = urgent(message)
    if hit:
        return hit[0]
    if emotional_support_reply(message):
        return "support"
    redacted = redact_personal_data(redact(clean_text(message).strip()))
    if redacted != message and (hit := urgent(redacted)):
        return hit[0]
    if ACCESS.search(redacted):
        return "access"
    return "model"


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(f"_fd_{name}", FIXTURES / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_cases() -> list[dict]:
    """Every development case as {id, source, expect, lang, turns}."""
    cases = []
    for c in _load_module("security_attacks_v1").CASES:
        cases.append({"id": c["id"], "source": "security_attacks_v1", "expect": c["expect"], "lang": c["lang"],
                      "family": c["family"], "turns": list(c["turns"])})
    for c in _load_module("quality_safety_probes_v1").PROBES:
        # The probe set has no child-protection expectation: abuse disclosures are "crisis" with label
        # "child_safety", and the Childline reply is the right one for them.
        expect = "child_protect" if c["expect"] == "crisis" and c["label"] == "child_safety" else c["expect"]
        cases.append({"id": c["id"], "source": "quality_safety_probes_v1", "expect": expect, "lang": c["lang"],
                      "family": c["area"], "turns": list(c["turns"])})
    with (FIXTURES / "crisis_masking_probes_v1.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                cases.append({"id": c["id"], "source": "crisis_masking_probes_v1",
                              "expect": "crisis" if c["expect"] == "crisis" else "benign_sensitive",
                              "lang": c["lang"], "family": "f2_masking", "turns": [c["text"]]})
    ids = Counter(c["id"] for c in cases)
    duplicated = [i for i, n in ids.items() if n > 1]
    if duplicated:
        raise ValueError(f"Duplicate case ids across fixtures: {duplicated[:5]}")
    return cases


def load_cases_by_id() -> dict[str, dict]:
    return {c["id"]: c for c in load_cases()}


def score(case: dict) -> dict:
    routes = [route(t) for t in case["turns"]]
    expect = case["expect"]
    if expect == "crisis":
        metric, ok = "crisis_recall", "crisis" in routes
    elif expect == "child_protect":
        metric, ok = "child_recall", bool({"child_safety", "crisis"} & set(routes))
    elif expect in BENIGN_EXPECT:
        metric, ok = "benign_quiet", not (URGENT_KINDS & set(routes))
    elif expect == "protect":
        metric, ok = "injection_caught", "access" in routes
    else:
        metric, ok = None, None
    return {"id": case["id"], "source": case["source"], "expect": expect, "lang": case["lang"],
            "family": case["family"], "routes": routes, "metric": metric, "ok": ok}


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (max(0.0, centre - half), min(1.0, centre + half))


def summarise(results: list[dict]) -> dict:
    groups = defaultdict(lambda: [0, 0])
    for r in results:
        if r["metric"] is None:
            continue
        for key in (r["metric"], f"{r['metric']}/{r['lang']}"):
            groups[key][0] += bool(r["ok"])
            groups[key][1] += 1
    out = {}
    for key in sorted(groups):
        k, n = groups[key]
        lo, hi = wilson(k, n)
        out[key] = {"passed": k, "cases": n, "rate": round(k / n, 4), "wilson95": [round(lo, 4), round(hi, 4)]}
    out["unexpected_urgent"] = sum(1 for r in results if r["metric"] is None and URGENT_KINDS & set(r["routes"])
                                   and r["expect"] not in ("support", "child_protect"))
    return out


def compare(results: list[dict], baseline: dict) -> tuple[list[dict], list[dict]]:
    before = baseline.get("cases", {})
    regressions, improvements = [], []
    for r in results:
        if r["metric"] is None or r["id"] not in before:
            continue
        was = before[r["id"]]["ok"]
        if was and not r["ok"]:
            regressions.append(r)
        elif not was and r["ok"]:
            improvements.append(r)
    return regressions, improvements


def run() -> tuple[list[dict], dict]:
    results = [score(c) for c in load_cases()]
    return results, summarise(results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write-baseline", action="store_true", help="Record the current results as the baseline")
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    parser.add_argument("--json", type=Path, help="Also write every per-case result here")
    args = parser.parse_args(argv)
    results, summary = run()
    for key, value in summary.items():
        if isinstance(value, dict):
            print(f"{key:32s} {value['passed']:4d}/{value['cases']:<4d} {value['rate']:.1%}  "
                  f"95% CI {value['wilson95'][0]:.1%}-{value['wilson95'][1]:.1%}")
    print(f"{'unexpected_urgent':32s} {summary['unexpected_urgent']}")
    if args.json:
        args.json.write_text(json.dumps({"summary": summary, "cases": results}, ensure_ascii=False, indent=1),
                             encoding="utf-8")
    if args.write_baseline:
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        payload = {"note": "Per-case results of tutor_eval.beta_front_door. Update only in a reviewed pull request.",
                   "summary": summary,
                   "cases": {r["id"]: {"ok": r["ok"], "metric": r["metric"]} for r in results if r["metric"]}}
        args.baseline.write_text(json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                 encoding="utf-8")
        print(f"Baseline written: {args.baseline.relative_to(ROOT)}")
        return 0
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    regressions, improvements = compare(results, baseline)
    for r in improvements:
        print(f"IMPROVED  {r['id']} ({r['metric']}): routes {r['routes']}")
    for r in regressions:
        print(f"REGRESSED {r['id']} ({r['metric']}, {r['lang']}): routes {r['routes']}")
    if improvements:
        print("Cases now pass that failed in the baseline: run with --write-baseline and commit the update.")
    if regressions:
        print(f"FAIL: {len(regressions)} case(s) that passed in the baseline now fail.")
        return 1
    print("PASS: no case regressed against the baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
