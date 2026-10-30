"""Copy the POC slice out of the frozen dataset (v0.10.0). The frozen build is only read, never changed.

Tutor-visible content goes to content/poc/. Evaluation fixtures go to eval/poc/ and come only from the
development partition: no held-out cases, held-out students or held-out queries are ever copied.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .config import CONTENT_DIR, EVAL_DIR, SETTINGS

PRACTICE_FIELDS = ("question_id", "prompt", "problem", "answer_contract", "hint_stages", "difficulty",
                   "chapter", "family_id", "supporting_passage_ids")


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write(path: Path, data) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def committed_counts() -> dict:
    """Counts for the slice already committed in content/poc/ and eval/poc/."""
    return {"concepts": len(load("concepts")), "cards": len(load("cards")),
            "misconceptions": len(load("misconceptions")), "practice_items": len(load("practice")),
            "dev_students": len(json.loads((EVAL_DIR / "students.json").read_text(encoding="utf-8"))),
            "dev_quiz_pairs": len(json.loads((EVAL_DIR / "quiz_pairs.json").read_text(encoding="utf-8")))}


def build() -> dict:
    """Recopy the slice from the frozen build if it is present; otherwise keep the committed slice."""
    build_dir = SETTINGS.dataset_build
    if not build_dir.exists():
        return {"source": "committed content/poc and eval/poc", **committed_counts()}
    poc = SETTINGS.poc
    concepts_wanted = set(poc["concepts"])
    manifest: dict[str, str] = {}

    concepts = [c for c in _jsonl(build_dir / "metadata/concepts.jsonl") if c["concept_id"] in concepts_wanted]
    for c in concepts:  # keep the prerequisite graph closed over the slice
        c["prerequisites"] = [p for p in c["prerequisites"] if p in concepts_wanted]
    manifest["content/poc/concepts.json"] = _write(CONTENT_DIR / "concepts.json", concepts)

    cards = [c for c in _jsonl(build_dir / "development_preview/corpus.jsonl") if c["concept_id"] in concepts_wanted]
    manifest["content/poc/cards.json"] = _write(CONTENT_DIR / "cards.json", cards)

    misconceptions = [m for m in _jsonl(build_dir / "metadata/misconceptions.jsonl") if m["concept_id"] in concepts_wanted]
    manifest["content/poc/misconceptions.json"] = _write(CONTENT_DIR / "misconceptions.json", misconceptions)

    practice = sorted((q for q in _jsonl(build_dir / "development_preview/practice_questions.jsonl")
                       if q["problem"]["task_type"] == poc["practice_task_type"]), key=lambda q: q["question_id"])
    practice = [{k: q[k] for k in PRACTICE_FIELDS} for q in practice[: poc["practice_items"]]]
    manifest["content/poc/practice.json"] = _write(CONTENT_DIR / "practice.json", practice)

    # Evaluation fixtures: development partition only.
    students = [s for s in _jsonl(build_dir / "private/simulated_students.jsonl") if s["student_id"] in poc["dev_students"]]
    assert students and all(s["partition"] == "development" for s in students), "POC may only use development students"
    manifest["eval/poc/students.json"] = _write(EVAL_DIR / "students.json", students)

    cases = {c["question_id"]: c for c in _jsonl(build_dir / "private/cases.jsonl")}
    pairs = [p for p in _jsonl(build_dir / "private/quiz_pairs.jsonl")
             if p["evaluation_partition"] == "development" and p["task_type"] == poc["practice_task_type"]]
    quiz = [{"pair_id": p["pair_id"],
             "pre": {k: cases[p["pre_id"]][k] for k in ("question_id", "prompt", "problem", "answer_contract")},
             "post": {k: cases[p["post_id"]][k] for k in ("question_id", "prompt", "problem", "answer_contract")}}
            for p in pairs]
    manifest["eval/poc/quiz_pairs.json"] = _write(EVAL_DIR / "quiz_pairs.json", quiz)

    _write(CONTENT_DIR / "MANIFEST.json", {"dataset_version": SETTINGS.raw["dataset"]["version"],
                                           "source_build": SETTINGS.raw["dataset"]["build"],
                                           "files_sha256": manifest,
                                           "note": "POC slice. Teaching content is an unapproved development preview."})
    return {"source": str(SETTINGS.raw["dataset"]["build"]), "concepts": len(concepts), "cards": len(cards),
            "misconceptions": len(misconceptions), "practice_items": len(practice), "dev_students": len(students),
            "dev_quiz_pairs": len(quiz)}


def load(name: str):
    return json.loads((CONTENT_DIR / f"{name}.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    print(build())
