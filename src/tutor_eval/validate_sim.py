"""Simulator validation (R5), on development cards only, before the pre-registration freezes.

    python -m tutor_eval.validate_sim                      # reads eval/dev/ once the freeze has written it
    python -m tutor_eval.validate_sim --build <.../builds/v0.10.0>   # or the development records of the build, in memory

Checks, per card and seeded misconception (thresholds from eval/PREREGISTRATION.md):
1. Expression: before any tutoring, the misconception shows on at least 80% of its assigned quiz items it applies to.
2. No-help control: without tutoring it never clears, and still shows on the post-quiz.
3. Contrast: it clears at about P_CLEAR only when named and targeted; never when only named, or only targeted.
4. No card leak: the student's messages never contain card fields (misconception IDs, mastery numbers, persona).
Writes var/runs/sim_validation-<time>/report.md and returns non-zero if any check fails.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from tutor.config import ROOT, VAR_DIR
from tutor_eval import simulator

RUNS, EXPRESSION_MIN = 50, 0.8


def load_dev(build: Path | None) -> tuple[list[dict], dict, dict]:
    """Development cards, quiz pairs with their items, and assignments."""
    if build:
        from tutor_eval.freeze import plan_freeze
        files = {k: [json.loads(line) for line in v] for k, v in plan_freeze(build, 0)["dev_files"].items()}
    else:
        d = ROOT / "eval" / "dev"
        if not d.exists():
            raise SystemExit("eval/dev/ does not exist yet. Run the freeze, or pass --build to read the build in memory.")
        files = {p.name: [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
                 for p in d.glob("*.jsonl")}
    items = {i["question_id"]: i for i in files["quiz_items.jsonl"]}
    pairs = {p["pair_id"]: (items[p["pre_id"]], items[p["post_id"]]) for p in files["quiz_pairs.jsonl"]}
    assigned = {a["student_id"]: a["pair_ids"] for a in files["student_quiz_assignments.jsonl"]}
    return files["simulated_students.jsonl"], pairs, assigned


def validate(cards: list[dict], pairs: dict, assigned: dict, catalogue: dict) -> list[dict]:
    rows = []
    for card in cards:
        mine = [pairs[p] for p in assigned.get(card["student_id"], pairs) if p in pairs]
        seeded = card["hidden_card"]["seeded_misconception_ids"]
        for position, m in enumerate(seeded):
            # an item counts for m only if no misconception listed before it claims the item (the student shows one)
            claims = lambda problem: _applies(m, problem, catalogue) and not any(
                _applies(e, problem, catalogue) for e in seeded[:position])
            shown, applicable, persisted, post_applicable, leaks = 0, 0, 0, 0, []
            for run in range(RUNS):
                student = simulator.Student(card, catalogue, seed=run)
                for pre, _ in mine:
                    rule = student.answer(pre["problem"])["rule"]
                    if claims(pre["problem"]) and rule in (m, f"{m}:generic"):
                        shown += 1
                    applicable += claims(pre["problem"])
                student.end_session(named=set(), targeted=set())  # no help
                for _, post in mine:
                    if claims(post["problem"]):
                        post_applicable += 1
                        persisted += student.answer(post["problem"])["rule"] in (m, f"{m}:generic")
                said = student.belief() + " " + student.opener(mine[0][0]["prompt"], student.answer(mine[0][0]["problem"])) if mine else student.belief()
                leaks += [f for f in _card_fields(card) if f in said]
            clear_both = sum(m in simulator.Student(card, catalogue, s).end_session({m}, {m}) for s in range(200)) / 200
            clear_named = sum(m in simulator.Student(card, catalogue, s).end_session({m}, set()) for s in range(200)) / 200
            clear_targeted = sum(m in simulator.Student(card, catalogue, s).end_session(set(), {m}) for s in range(200)) / 200
            expression = shown / applicable if applicable else None
            rows.append({
                "student": card["student_id"], "misconception": m, "applicable_items": applicable // RUNS,
                "expression": expression, "persistence": persisted / post_applicable if post_applicable else None,
                "clear_named_and_targeted": clear_both, "clear_named_only": clear_named, "clear_targeted_only": clear_targeted,
                "card_leaks": sorted(set(leaks)),
                "ok": (expression is None or expression >= EXPRESSION_MIN)
                      and (not post_applicable or persisted == post_applicable)
                      and clear_named == clear_targeted == 0 and abs(clear_both - simulator.P_CLEAR) < 0.1 and not leaks,
            })
    return rows


def _applies(m: str, problem: dict, catalogue: dict) -> bool:
    rule = simulator.RULES.get(m)
    buggy = rule(problem["task_type"], problem["givens"]) if rule else None
    if buggy is not None:  # the rule fits this task: it shows only if it changes the answer
        return not simulator.mk.answers_equivalent(buggy, simulator.correct_answer(problem))
    return catalogue.get(m, {}).get("concept_id") in problem["concept_ids"]


def _card_fields(card: dict) -> list[str]:
    hidden = card["hidden_card"]
    fields = list(hidden["seeded_misconception_ids"]) + [str(v) for v in hidden.get("persona", {}).values() if isinstance(v, str)]
    return [f for f in fields if len(f) > 3]


def report(rows: list[dict]) -> str:
    failed = [r for r in rows if not r["ok"]]
    untested = [r for r in rows if r["expression"] is None]
    lines = ["# Simulator validation (development cards)", "",
             f"{len(rows)} card × misconception pairs; {len(failed)} failed; {len(untested)} with no assigned quiz item the misconception applies to.",
             f"Thresholds: expression ≥ {EXPRESSION_MIN}; no clearing without help; clearing ≈ {simulator.P_CLEAR} only when named and targeted; no card text in messages.", "",
             "| Student | Misconception | Items it applies to | Expression | Persists without help | Clears: both / named / targeted | Card leaks | OK |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        f = lambda x: "–" if x is None else f"{x:.2f}"
        lines.append(f"| {r['student']} | {r['misconception']} | {r['applicable_items']} | {f(r['expression'])} | {f(r['persistence'])} | "
                     f"{f(r['clear_named_and_targeted'])} / {f(r['clear_named_only'])} / {f(r['clear_targeted_only'])} | "
                     f"{', '.join(r['card_leaks']) or '–'} | {'yes' if r['ok'] else '**no**'} |")
    if untested:
        lines += ["", "**Not measurable by quiz:** the student's assigned pairs contain no item these misconceptions apply to, "
                  "so pre/post scores can't show them. Diagnosis can still be measured in the session."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m tutor_eval.validate_sim", description=__doc__.split("\n\n")[0])
    ap.add_argument("--build", type=Path, help="read development records from the build in memory instead of eval/dev/")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    catalogue = {m["misconception_id"]: m for m in (json.loads(line) for line in
                 (ROOT / "content/dataset-v0.10.0/misconceptions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
    rows = validate(*load_dev(args.build), catalogue)
    out = VAR_DIR / "runs" / f"sim_validation-{time.strftime('%Y%m%d-%H%M%S')}"
    out.mkdir(parents=True, exist_ok=True)
    text = report(rows)
    (out / "report.md").write_text(text, encoding="utf-8")
    (out / "results.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(text + f"\nSaved to {out}")
    if any(not r["ok"] for r in rows):
        raise SystemExit("Simulator validation failed; fix the rules before the pre-registration freezes.")


if __name__ == "__main__":
    main()
