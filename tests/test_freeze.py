"""The held-out freeze, on a small synthetic build. The real build is never needed or touched."""
import hashlib
import json
from collections import Counter

import pytest

from tutor_eval import freeze

GOLDEN = {"development": 4, "heldout": 6}


def _write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def make_build(root):
    """Two development families and three held-out ones, six cases each, three concepts per family."""
    cases, contracts, routing, tasks = [], [], [], []
    for split, families in (("development", ["fa", "fb"]), ("candidate_heldout", ["fc", "fd", "fe"])):
        for fam in families:
            for i in range(6):
                qid = f"{split[:3]}_{fam}_{i}"
                cases.append({"question_id": qid, "split": split, "family_id": fam, "problem": {"concept_ids": [f"{fam}_c{i % 3}"]}})
                row = {"evaluation_task_id": f"t_{qid}", "partition": split, "source_question_id": qid}
                contracts.append(row)
                routing.append(row)
                tasks.append({"evaluation_task_id": f"t_{qid}", "question": "q"})
    pairs = []
    for i, part in enumerate(["development", "development", "candidate_final"]):
        for side in ("pre", "post"):
            cases.append({"question_id": f"quiz_{side}_{i}", "split": "practice", "family_id": "fq", "problem": {"concept_ids": ["fq_c0"]}})
        pairs.append({"pair_id": f"pair_{i}", "evaluation_partition": part, "pre_id": f"quiz_pre_{i}", "post_id": f"quiz_post_{i}"})
    students = [{"student_id": f"s{i}", "partition": p} for i, p in enumerate(["development", "candidate_final", "candidate_final"])]
    p = root / "private"
    _write(p / "cases.jsonl", cases)
    _write(p / "benchmark_contracts.jsonl", contracts)
    _write(p / "benchmark_query_routing.jsonl", routing)
    _write(p / "benchmark_inputs" / "tasks.jsonl", tasks)
    _write(p / "quiz_pairs.jsonl", pairs)
    _write(p / "simulated_students.jsonl", students)
    _write(p / "student_quiz_assignments.jsonl", students)
    _write(p / "retrieval_judgments.jsonl", [{"query_id": "rq0", "partition": "development"}, {"query_id": "rq1", "partition": "candidate_heldout"}])
    _write(p / "retrieval_inputs" / "queries.jsonl", [{"retrieval_task_id": "rt0"}, {"retrieval_task_id": "rt1"}])
    _write(p / "retrieval_query_routing.jsonl", [{"retrieval_task_id": "rt0", "source_query_id": "rq0"},
                                                 {"retrieval_task_id": "rt1", "source_query_id": "rq1"}])
    _write(p / "attacks.jsonl", [{"case_id": "atk0"}])
    _write(p / "clean_controls.jsonl", [{"case_id": "ctl0", "paired_attack_id": "atk0"}])
    files = {f.relative_to(root).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob("*.jsonl")}
    manifest = root / "metadata" / "files.sha256.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps(files), encoding="utf-8")
    return hashlib.sha256(manifest.read_bytes()).hexdigest()


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(freeze, "GOLDEN", GOLDEN)
    build, repo, private = tmp_path / "build", tmp_path / "repo", tmp_path / "private"
    payload = make_build(build)
    repo.mkdir()
    args = ["--build", str(build), "--seed", "7", "--private-out", str(private), "--expect-payload", payload, "--repo", str(repo)]
    return build, repo, private, args


def test_golden_sets_spread_over_families_and_concepts(setup):
    build = setup[0]
    held = [c for c in freeze.Table(build / "private" / "cases.jsonl").rows if c["split"] == "candidate_heldout"]
    picked = freeze.stratified(held, 6, freeze.random.Random(1))
    assert Counter(c["family_id"] for c in picked) == {"fc": 2, "fd": 2, "fe": 2}
    for fam in ("fc", "fd", "fe"):  # two picks per family land on two different concepts
        assert len({c["problem"]["concept_ids"][0] for c in picked if c["family_id"] == fam}) == 2


def test_same_seed_same_selection(setup):
    build = setup[0]
    first, again = freeze.plan_freeze(build, 7, GOLDEN), freeze.plan_freeze(build, 7, GOLDEN)
    assert first["selection"] == again["selection"] and first["golden_dev_ids"] == again["golden_dev_ids"]


def test_freeze_writes_dev_split_and_hashes_only(setup, capsys):
    build, repo, private, args = setup
    log = repo / "EXPERIMENT_LOG.md"
    freeze.main(args + ["--log", str(log)])
    dev = [json.loads(line) for line in (repo / "eval" / "dev" / "benchmark_cases.jsonl").read_text().splitlines()]
    assert len(dev) == 12 and {c["split"] for c in dev} == {"development"}
    items = {json.loads(line)["question_id"] for line in (repo / "eval" / "dev" / "quiz_items.jsonl").read_text().splitlines()}
    assert items == {"quiz_pre_0", "quiz_post_0", "quiz_pre_1", "quiz_post_1"}
    manifest = (repo / "eval" / "HELDOUT_MANIFEST.json").read_text()
    for held_id in ("can_fc_0", "quiz_pre_2", "s1", "rq1", "atk0"):  # no held-out ID reaches a committed file
        assert held_id not in manifest
    selection = json.loads((private / "heldout_selection.json").read_text())
    assert len(selection["golden_case_ids"]) == 6 and len(selection["reserve_case_ids"]) == 12
    assert json.loads(manifest)["private_selection_sha256"] == hashlib.sha256((private / "heldout_selection.json").read_bytes()).hexdigest()
    assert "held-out freeze" in log.read_text(encoding="utf-8")


def test_dry_run_writes_nothing(setup):
    build, repo, private, args = setup
    freeze.main(args + ["--dry-run"])
    assert not (repo / "eval").exists() and not private.exists()


def test_freeze_happens_once(setup):
    args = setup[3]
    freeze.main(args)
    with pytest.raises(SystemExit, match="already recorded"):
        freeze.main(args)


def test_refuses_private_output_inside_repo(setup):
    build, repo, private, args = setup
    args[args.index("--private-out") + 1] = str(repo / "eval" / "private")
    with pytest.raises(SystemExit, match="inside the repository"):
        freeze.main(args)


def test_refuses_a_changed_build(setup):
    build, args = setup[0], setup[3]
    with (build / "private" / "attacks.jsonl").open("a") as fh:
        fh.write('{"case_id": "atk1"}\n')
    with pytest.raises(SystemExit, match="does not match"):
        freeze.main(args)
