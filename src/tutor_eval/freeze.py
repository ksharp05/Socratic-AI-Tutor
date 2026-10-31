"""Held-out freeze (R5): verify the dataset build, pick the golden sets, export the development split
and record a SHA-256 for every held-out record.

It reads the frozen build and never writes inside it. A real run writes:
- `eval/dev/` (committed): development records only, as the build's raw JSONL lines, plus MANIFEST.json;
- `eval/HELDOUT_MANIFEST.json` (committed): seed, counts and record hashes. No content and no IDs;
- `<private-out>/heldout_selection.json` (never in git): the held-out IDs the experiments need.

The freeze is a human-only task: R5 picks the seed and runs it once.

    python -m tutor_eval.freeze --build <...>/builds/v0.10.0 --seed <number> --private-out <folder outside the repo> --dry-run
    python -m tutor_eval.freeze --build <...>/builds/v0.10.0 --seed <number> --private-out <folder outside the repo> --log Docs/EXPERIMENT_LOG.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEV, HELDOUT = "development", ("candidate_heldout", "candidate_final")
GOLDEN = {"development": 40, "heldout": 60}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Table:
    """One JSONL file of the build, keeping each record's exact bytes so hashes match the dataset's own."""

    def __init__(self, path: Path):
        self.lines = [ln for ln in path.read_bytes().splitlines(keepends=True) if ln.strip()]
        self.rows = [json.loads(ln) for ln in self.lines]

    def pick(self, keep) -> list[bytes]:
        return [ln for ln, row in zip(self.lines, self.rows) if keep(row)]


def verify_build(build: Path, expected_payload: str) -> None:
    """Every file must match metadata/files.sha256.json, and that file must hash to the recorded payload."""
    manifest = build / "metadata" / "files.sha256.json"
    payload = sha256(manifest.read_bytes())
    if payload != expected_payload:
        raise SystemExit(f"Build payload {payload[:12]}… is not the expected {expected_payload[:12]}…; refusing to freeze.")
    for rel, digest in json.loads(manifest.read_text(encoding="utf-8")).items():
        if sha256((build / rel).read_bytes()) != digest:
            raise SystemExit(f"{rel} does not match its recorded SHA-256; the build has changed. Refusing to freeze.")


def stratified(cases: list[dict], n: int, rng: random.Random) -> list[dict]:
    """n cases spread evenly over task families, each pick favouring the concepts covered least so far."""
    pools = defaultdict(list)
    for case in sorted(cases, key=lambda c: c["question_id"]):
        pools[case["family_id"]].append(case)
    families = sorted(pools)
    for fam in families:
        rng.shuffle(pools[fam])
    quota = {fam: min(len(pools[fam]), n // len(families)) for fam in families}
    covered: Counter = Counter()
    picked: list[dict] = []

    def take(fam: str) -> None:
        best = min(pools[fam], key=lambda c: (min((covered[k] for k in c["problem"]["concept_ids"]), default=0),
                                              sum(covered[k] for k in c["problem"]["concept_ids"])))
        pools[fam].remove(best)
        covered.update(best["problem"]["concept_ids"])
        picked.append(best)

    while any(quota.values()):
        for fam in families:
            if quota[fam]:
                take(fam)
                quota[fam] -= 1
    while len(picked) < n and any(pools.values()):  # remainder, or families too small for their share
        for fam in families:
            if len(picked) < n and pools[fam]:
                take(fam)
    return picked


def plan_freeze(build: Path, seed: int, golden: dict = GOLDEN) -> dict:
    """Everything the freeze would write, computed in memory."""
    p = build / "private"
    cases, contracts, routing, tasks = (Table(p / "cases.jsonl"), Table(p / "benchmark_contracts.jsonl"),
                                        Table(p / "benchmark_query_routing.jsonl"), Table(p / "benchmark_inputs" / "tasks.jsonl"))
    pairs, students, assignments = (Table(p / "quiz_pairs.jsonl"), Table(p / "simulated_students.jsonl"),
                                    Table(p / "student_quiz_assignments.jsonl"))
    judgments, queries, query_routing = (Table(p / "retrieval_judgments.jsonl"), Table(p / "retrieval_inputs" / "queries.jsonl"),
                                         Table(p / "retrieval_query_routing.jsonl"))
    attacks, controls = Table(p / "attacks.jsonl"), Table(p / "clean_controls.jsonl")

    rng = random.Random(f"socratic-tutor-freeze:{seed}")
    dev_cases = [c for c in cases.rows if c["split"] == DEV]
    held_cases = [c for c in cases.rows if c["split"] in HELDOUT]
    golden_dev = stratified(dev_cases, golden["development"], rng)
    golden_held = stratified(held_cases, golden["heldout"], rng)
    golden_held_ids = {c["question_id"] for c in golden_held}
    reserve = {c["question_id"] for c in held_cases} - golden_held_ids

    dev_case_ids = {c["question_id"] for c in dev_cases}
    dev_task_ids = {r["evaluation_task_id"] for r in routing.rows if r["partition"] == DEV}
    dev_pairs = [r for r in pairs.rows if r["evaluation_partition"] == DEV]
    dev_item_ids = {r[k] for r in dev_pairs for k in ("pre_id", "post_id")}
    held_item_ids = {r[k] for r in pairs.rows if r["evaluation_partition"] in HELDOUT for k in ("pre_id", "post_id")}
    dev_query_ids = {r["query_id"] for r in judgments.rows if r["partition"] == DEV}
    dev_retrieval_tasks = {r["retrieval_task_id"] for r in query_routing.rows if r["source_query_id"] in dev_query_ids}
    if dev_item_ids & held_item_ids or dev_case_ids & {c["question_id"] for c in held_cases}:
        raise SystemExit("A record is in both the development and the held-out split; refusing to freeze.")

    dev_files = {
        "benchmark_cases.jsonl": cases.pick(lambda r: r["question_id"] in dev_case_ids),
        "benchmark_contracts.jsonl": contracts.pick(lambda r: r["partition"] == DEV),
        "benchmark_query_routing.jsonl": routing.pick(lambda r: r["partition"] == DEV),
        "benchmark_tasks.jsonl": tasks.pick(lambda r: r["evaluation_task_id"] in dev_task_ids),
        "simulated_students.jsonl": students.pick(lambda r: r["partition"] == DEV),
        "student_quiz_assignments.jsonl": assignments.pick(lambda r: r["partition"] == DEV),
        "quiz_pairs.jsonl": pairs.pick(lambda r: r["evaluation_partition"] == DEV),
        "quiz_items.jsonl": cases.pick(lambda r: r["question_id"] in dev_item_ids),
        "retrieval_judgments.jsonl": judgments.pick(lambda r: r["partition"] == DEV),
        "retrieval_queries.jsonl": queries.pick(lambda r: r["retrieval_task_id"] in dev_retrieval_tasks),
        "retrieval_query_routing.jsonl": query_routing.pick(lambda r: r["source_query_id"] in dev_query_ids),
    }

    held_sets = {  # attacks and controls are frozen here; whether R4 may build against the existing 30 is decided separately
        "golden_cases": cases.pick(lambda r: r["question_id"] in golden_held_ids),
        "reserve_cases": cases.pick(lambda r: r["question_id"] in reserve),
        "simulated_students": students.pick(lambda r: r["partition"] in HELDOUT),
        "quiz_pairs": pairs.pick(lambda r: r["evaluation_partition"] in HELDOUT),
        "quiz_items": cases.pick(lambda r: r["question_id"] in held_item_ids),
        "retrieval_judgments": judgments.pick(lambda r: r["partition"] in HELDOUT),
        "attacks": attacks.lines,
        "clean_controls": controls.lines,
    }
    selection = {
        "golden_case_ids": sorted(golden_held_ids),
        "reserve_case_ids": sorted(reserve),
        "simulated_student_ids": sorted(r["student_id"] for r in students.rows if r["partition"] in HELDOUT),
        "quiz_pair_ids": sorted(r["pair_id"] for r in pairs.rows if r["evaluation_partition"] in HELDOUT),
        "retrieval_query_ids": sorted(r["query_id"] for r in judgments.rows if r["partition"] in HELDOUT),
        "attack_ids": sorted(r["case_id"] for r in attacks.rows),
        "clean_control_ids": sorted(r["case_id"] for r in controls.rows),
    }
    concepts = lambda chosen: len({k for c in chosen for k in c["problem"]["concept_ids"]})
    families = lambda chosen: len({c["family_id"] for c in chosen})
    return {
        "dev_files": dev_files, "held_sets": held_sets, "selection": selection,
        "golden_dev_ids": sorted(c["question_id"] for c in golden_dev),
        "coverage": {
            "golden_development": {"cases": len(golden_dev), "families": f"{families(golden_dev)}/{families(dev_cases)}",
                                   "concepts": f"{concepts(golden_dev)}/{concepts(dev_cases)}"},
            "golden_heldout": {"cases": len(golden_held), "families": f"{families(golden_held)}/{families(held_cases)}",
                               "concepts": f"{concepts(golden_held)}/{concepts(held_cases)}"},
        },
    }


def _inside(path: Path, parent: Path) -> bool:
    return path.resolve().is_relative_to(parent.resolve())


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m tutor_eval.freeze", description=__doc__.split("\n\n")[0])
    ap.add_argument("--build", required=True, type=Path, help="the frozen build folder, e.g. .../builds/v0.10.0")
    ap.add_argument("--seed", required=True, type=int, help="sampling seed, chosen by R5 and recorded in the log")
    ap.add_argument("--private-out", required=True, type=Path, help="folder OUTSIDE the repository for the held-out IDs")
    ap.add_argument("--expect-payload", help="payload SHA-256 to require (default: content/dataset-v0.10.0/MANIFEST.json)")
    ap.add_argument("--repo", type=Path, default=ROOT, help=argparse.SUPPRESS)
    ap.add_argument("--log", type=Path, help="append the freeze entry to this file, e.g. Docs/EXPERIMENT_LOG.md")
    ap.add_argument("--dry-run", action="store_true", help="verify and report coverage; write nothing")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    repo, build = args.repo.resolve(), args.build.resolve()
    expected = args.expect_payload or json.loads(
        (repo / "content" / "dataset-v0.10.0" / "MANIFEST.json").read_text(encoding="utf-8"))["payload_sha256"]
    dev_dir, held_manifest = repo / "eval" / "dev", repo / "eval" / "HELDOUT_MANIFEST.json"
    if _inside(args.private_out, repo):
        raise SystemExit("--private-out is inside the repository; held-out IDs must stay outside git.")
    if any(_inside(p, build) for p in (dev_dir, held_manifest, args.private_out)):
        raise SystemExit("An output would land inside the frozen build; refusing.")
    if not args.dry_run and (held_manifest.exists() or (dev_dir.exists() and any(dev_dir.iterdir()))):
        raise SystemExit("A freeze is already recorded (eval/HELDOUT_MANIFEST.json or eval/dev/). It happens once; "
                         "a change after held-out runs must be logged as a deviation instead.")

    verify_build(build, expected)
    plan = plan_freeze(build, args.seed, GOLDEN)
    print(f"Build verified: payload {expected[:12]}…, every file matches its SHA-256.")
    for name, cov in plan["coverage"].items():
        print(f"  {name}: {cov['cases']} cases, families {cov['families']}, concepts {cov['concepts']}")
    print("  development split: " + ", ".join(f"{k} {len(v)}" for k, v in plan["dev_files"].items()))
    print("  held-out sets: " + ", ".join(f"{k} {len(v)}" for k, v in plan["held_sets"].items()))
    if args.dry_run:
        print("Dry run: nothing written.")
        return

    when = time.strftime("%Y-%m-%d %H:%M %z")
    script_sha = sha256(Path(__file__).read_bytes())
    selection = {"dataset_payload_sha256": expected, "sampling_seed": args.seed, "frozen_at": when, **plan["selection"]}
    selection_bytes = (json.dumps(selection, indent=2) + "\n").encode("utf-8")
    args.private_out.mkdir(parents=True, exist_ok=True)
    (args.private_out / "heldout_selection.json").write_bytes(selection_bytes)

    dev_dir.mkdir(parents=True, exist_ok=True)
    dev_manifest = {"dataset_payload_sha256": expected, "sampling_seed": args.seed, "frozen_at": when,
                    "script_sha256": script_sha, "golden_case_ids": plan["golden_dev_ids"], "files": {}}
    for name, lines in plan["dev_files"].items():
        data = b"".join(lines)
        (dev_dir / name).write_bytes(data)
        dev_manifest["files"][name] = {"records": len(lines), "sha256": sha256(data)}
    (dev_dir / "MANIFEST.json").write_text(json.dumps(dev_manifest, indent=2) + "\n", encoding="utf-8")

    held = {"dataset_payload_sha256": expected, "sampling_seed": args.seed, "frozen_at": when, "script_sha256": script_sha,
            "private_selection_sha256": sha256(selection_bytes),
            "note": "Record hashes are SHA-256 of each record's exact JSONL line in the build, sorted. No content, no IDs.",
            "sets": {}}
    for name, lines in plan["held_sets"].items():
        digests = sorted(sha256(ln) for ln in lines)
        held["sets"][name] = {"records": len(lines), "set_sha256": sha256("\n".join(digests).encode()),
                              "record_sha256": digests}
    held_bytes = (json.dumps(held, indent=2) + "\n").encode("utf-8")
    held_manifest.write_bytes(held_bytes)

    entry = (f"\n### {when[:10]} · freeze-{when[:10]} · held-out freeze\n"
             f"- **Data:** dataset v0.10.0, payload `{expected}`, every file verified.\n"
             f"- **Sampling seed:** {args.seed}. Script `src/tutor_eval/freeze.py`, SHA-256 `{script_sha}`.\n"
             f"- **Held-out:** " + ", ".join(f"{k} {v['records']}" for k, v in held["sets"].items()) + ". "
             f"Manifest `eval/HELDOUT_MANIFEST.json`, SHA-256 `{sha256(held_bytes)}`. The IDs are kept outside git.\n"
             f"- **Development split:** `eval/dev/`, " + ", ".join(f"{k} {v['records']}" for k, v in dev_manifest["files"].items()) + ".\n"
             f"- **Golden coverage:** held-out {plan['coverage']['golden_heldout']['families']} families and "
             f"{plan['coverage']['golden_heldout']['concepts']} concepts; development {plan['coverage']['golden_development']['families']} "
             f"families and {plan['coverage']['golden_development']['concepts']} concepts.\n"
             f"- **Outcome:** frozen. Any later change to these sets is a deviation and is reported.\n")
    if args.log:
        with args.log.open("a", encoding="utf-8") as fh:
            fh.write(entry)
    print(f"Wrote eval/dev/ ({len(plan['dev_files'])} files), eval/HELDOUT_MANIFEST.json, and the held-out IDs to "
          f"{args.private_out / 'heldout_selection.json'}.")
    print(entry if not args.log else f"Appended the freeze entry to {args.log}.")


if __name__ == "__main__":
    main()
