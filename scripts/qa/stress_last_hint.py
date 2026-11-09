"""Stress: every public practice item driven to the after-last-hint reply, then answered correctly.

Usage: python stress_last_hint.py <tree root> <out.json>
Offline only: TUTOR_LLM=stub, temporary databases, no provider calls.
"""
import json
import os
import sys
import tempfile
import time
import traceback

ROOT = sys.argv[1]
OUT = sys.argv[2]
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("TUTOR_LLM", "stub")

from tutor import mathcore  # noqa: E402
from tutor.app import TutorApp  # noqa: E402
from tutor.question_catalog import allowed, graph_items  # noqa: E402
from tutor.seed import seed_learner  # noqa: E402
from tutor.toolbus import CallContext  # noqa: E402

LEARNER = "synthetic"
ITEMS = [i for i in graph_items() if allowed(i, "practice")]


def correct_text(item, key):
    if key["kind"] == "finite_set":
        if not key["values"]:
            return "no valid term count" if key.get("unit") == "terms" else "no real roots"
        return ", ".join(key["values"])
    return str(key["value"])


def classify(reply, presentation):
    body = reply.split("(Study plan")[0]
    if presentation and presentation in reply:
        kind = "example"
    elif "Let's slow down" in reply:
        kind = "guard_fallback"
    elif "Type 'practice'" in reply:
        kind = "last_hint"
    else:
        kind = "other"
    return kind, body.count("?")


def pending(app):
    ctx = CallContext("read", learner_id=LEARNER)
    snap = app.bus.call(ctx, "study_planner", "learner-store", "read_learner", {"learner_id": LEARNER})
    return [r["question_ref"] for r in snap.get("revisit_items", [])]


def run_item(item, tmp):
    app = TutorApp(llm_mode="stub", db_name=os.path.join(tmp, "t.db"), checkpoint_name=os.path.join(tmp, "c.db"))
    seen = {"example": None, "leaks": [], "errors": []}
    real = app.bus.call

    def spy(ctx, role, server, tool, args):
        try:
            result = real(ctx, role, server, tool, args)
        except Exception as exc:  # recorded, then re-raised for the app to handle
            seen["errors"].append(f"{tool}:{type(exc).__name__}:{getattr(exc, 'code', '')}")
            raise
        if tool == "generate_parallel_example":
            seen["example"] = result
        if tool == "leak_check" and result.get("leak"):
            seen["leaks"].append(result.get("reason"))
        return result

    app.bus.call = spy
    try:
        seed_learner(app.conn, LEARNER, {"alias": "Synthetic"})
        proposal = app.propose_set(item["problem"]["concept_ids"][0])
        app.decide(proposal["set_id"], "edit", LEARNER, question_ids=[item["question_id"]])
        app.decide(proposal["set_id"], "approve", LEARNER)
        first = app.turn("s", LEARNER, "practice", chapter=item["chapter"])
        served = first.get("active_item")
        guard_fallbacks = 0
        for _ in range(3):
            r = app.turn("s", LEARNER, "hint")
            guard_fallbacks += "Let's slow down" in r["reply"]
        app.turn("s", LEARNER, "99991")
        last = app.turn("s", LEARNER, "99992")
        ex = seen["example"] or {}
        presentation = (ex.get("example") or {}).get("presentation") if ex.get("available") else None
        kind, questions = classify(last["reply"], presentation)
        cite = any(f"[{p}]" in last["reply"] for p in item.get("supporting_passage_ids", []))
        marked_after_hint = item["question_id"] in pending(app)
        key = mathcore.compute_key(item["problem"])["key"]
        answer = app.turn("s", LEARNER, correct_text(item, key))
        return {
            "id": item["question_id"], "family": item["problem"]["task_type"], "served": served == item["question_id"],
            "route": last.get("route"), "kind": kind, "questions": questions, "cites": cite,
            "service_available": bool(ex.get("available")), "service_called": seen["example"] is not None,
            "checks_ok": (last.get("checks") or {}).get("ok"), "leaks": seen["leaks"], "hint_guard_fallbacks": guard_fallbacks,
            "marked_after_hint": marked_after_hint, "correct_reply": answer["reply"][:60],
            "correct_ok": answer["reply"].startswith("Correct"), "marked_after_correct": item["question_id"] in pending(app),
            "errors": seen["errors"], "reply": last["reply"],
        }
    finally:
        app.close()


def main():
    rows, started = [], time.time()
    for item in ITEMS:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                rows.append(run_item(item, tmp))
            except Exception:
                rows.append({"id": item["question_id"], "family": item["problem"]["task_type"],
                             "crash": traceback.format_exc()[-800:]})
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=1)
    print(f"{len(rows)} items in {time.time() - started:.0f}s -> {OUT}")


if __name__ == "__main__":
    main()
