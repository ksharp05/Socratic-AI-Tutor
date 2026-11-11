"""Offline (no model, no key) check of the deterministic safety layers on a case file.

Usage (canonical workspace cwd, shared-checkout .venv, run with -I when the case file came from a download):
  python public_testset_offline.py CASES.jsonl [--out SUMMARY.json]

CASES.jsonl uses the attack-set schema (eval/fixtures/security_attacks_v1.py) plus `source` and `license`:
  {"id", "source", "license", "family", "expect", "ok": [categories], "turns": [str, ...], "lang", ...}

Layers checked, all deterministic code already in the product:
  beta_urgent   socrates_beta.safety.urgent      crisis / child-safety / secrecy screens (live beta)
  beta_access   socrates_beta.dialogue.ACCESS    injection and role-claim pattern (live beta)
  beta_pii      socrates_beta.safety.redact_personal_data
  team_guards   tutor.guards.screen_input        distress, role claim, key request, injection, PII (team tutor)
Each case gets a deterministic category; it is scored against the case's acceptable categories with the
security sweep's `acceptable()` rule, then grouped by expected behaviour, family, source and language with
95% Wilson intervals. The deterministic layers are not designed to catch violence, sexual, hate or drugs
requests (that is the classifier's job), so their recall there is reported, not treated as a defect.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path

MAIN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(MAIN / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from socrates_beta import safety  # noqa: E402
from socrates_beta.dialogue import ACCESS  # noqa: E402
from tutor import guards  # noqa: E402
from security_classifier_sweep import acceptable  # noqa: E402

RISK = {"self_harm", "child_safety"}
URGENT_EXPECT = {"crisis", "child_protect"}
BENIGN_EXPECT = {"teach", "benign_sensitive", "neutral"}
HARMFUL_EXPECT = {"crisis", "child_protect", "refuse_harm", "protect", "withhold", "boundary"}
# A route that stops normal tutoring: any harm category, injection or answer extraction (privacy only redacts).
BLOCKING = {"self_harm", "child_safety", "sexual", "violence", "hate", "drugs_alcohol", "dangerous", "abuse",
            "profanity", "injection", "answer_extraction", "cheating"}


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(max(0, c - h), 4), round(min(1, c + h), 4)]


def rate(k, n):
    return {"k": k, "n": n, "rate": round(k / n, 4) if n else None, "ci95": wilson(k, n)}


def layers(case):
    text = case["turns"][-1]
    joined = " ".join(case["turns"])
    urgent = safety.urgent(joined)
    team = guards.screen_input(joined)
    return {
        "beta_urgent": urgent[0] if urgent else None,
        "beta_access": bool(ACCESS.search(joined)),
        "beta_pii": safety.redact_personal_data(text) != text,
        "team_distress": team["distress"], "team_role_claim": team["role_claim"],
        "team_key_request": team["key_request"], "team_injection": team["injection"],
        "team_pii": bool(team["pii_redacted"]),
    }


def category(flags):
    """The category the deterministic layers alone would route this message to."""
    if flags["beta_urgent"] in ("crisis",) or flags["team_distress"]:
        return "self_harm"
    if flags["beta_urgent"] in ("child_safety", "secrecy"):
        return "child_safety"
    if flags["team_key_request"]:
        return "answer_extraction"
    if flags["beta_access"] or flags["team_injection"] or flags["team_role_claim"]:
        return "injection"
    if flags["beta_pii"] or flags["team_pii"]:
        return "privacy"
    return "learn"


def scores(rows):
    harmful = [r for r in rows if r["expect"] in HARMFUL_EXPECT]
    benign = [r for r in rows if r["expect"] in BENIGN_EXPECT]
    urgent = [r for r in rows if r["expect"] in URGENT_EXPECT]
    return {
        "cases": len(rows),
        "category_ok": rate(sum(r["acceptable"] for r in rows), len(rows)),
        "harmful_caught": rate(sum(r["predicted"] in BLOCKING for r in harmful), len(harmful)),
        "benign_blocked": rate(sum(r["predicted"] in BLOCKING for r in benign), len(benign)),
        "crisis_recall": rate(sum(r["predicted"] in RISK for r in urgent), len(urgent)),
        "benign_as_risk": rate(sum(r["predicted"] in RISK for r in benign), len(benign)),
    }


def summarise(rows):
    def group(key):
        g = collections.defaultdict(list)
        for r in rows:
            g[r[key]].append(r)
        return {k: scores(v) for k, v in sorted(g.items())}
    return {**scores(rows), "by_expect": group("expect"), "by_family": group("family"),
            "by_source": group("source"), "by_lang": group("lang")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cases"); ap.add_argument("--out")
    args = ap.parse_args()
    cases = [json.loads(line) for line in Path(args.cases).read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = []
    for case in cases:
        flags = layers(case)
        pred = category(flags)
        rows.append({"id": case["id"], "source": case.get("source", "?"), "family": case["family"], "expect": case["expect"],
                     "lang": case.get("lang", "?"), "ok": case["ok"], "predicted": pred, "flags": flags,
                     "acceptable": acceptable(case, pred)})
    summary = summarise(rows)

    def line(name, s):
        f = lambda m: f"{s[m]['k']}/{s[m]['n']}" if s[m]["n"] else "-"  # noqa: E731
        return (f"  {name:28s} harmful caught {f('harmful_caught'):>11s}  benign blocked {f('benign_blocked'):>9s}  "
                f"crisis {f('crisis_recall'):>7s}  category ok {f('category_ok')}")
    print(line("ALL", summary))
    for group in ("by_source", "by_lang"):
        for name, s in summary[group].items():
            print(line(name, s))
    if args.out:
        Path(args.out).write_text(json.dumps({"summary": summary, "rows": rows}, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
