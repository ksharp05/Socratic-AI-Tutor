"""Stress: saved revisit marks across restarts, chapters, answers and learner deletion.

Usage: python stress_revisit.py <tree root> <out.json>   (TUTOR_LLM=stub, offline)
"""
import json
import os
import sys
import tempfile
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

L = "synthetic"
PRACTICE = [i for i in graph_items() if allowed(i, "practice")]
AP = [i for i in PRACTICE if i["problem"]["task_type"] == "ap_term"][:4]
TRIG = [i for i in PRACTICE if i["problem"]["task_type"] == "trig_triangle_ratio"][:1]
BY_ID = {i["question_id"]: i for i in PRACTICE}


class World:
    def __init__(self, tmp):
        self.tmp = tmp
        self.app = None

    def open(self):
        if self.app:
            self.app.close()
        self.app = TutorApp(llm_mode="stub", db_name=os.path.join(self.tmp, "t.db"),
                            checkpoint_name=os.path.join(self.tmp, "c.db"))
        return self.app

    def publish(self, items):
        by_concept = {}
        for i in items:
            by_concept.setdefault(i["problem"]["concept_ids"][0], []).append(i["question_id"])
        for concept, ids in by_concept.items():
            p = self.app.propose_set(concept)
            self.app.decide(p["set_id"], "edit", L, question_ids=ids)
            self.app.decide(p["set_id"], "approve", L)

    def active(self, session):
        values = self.app.graph.get_state({"configurable": {"thread_id": session}}).values
        return (values.get("active_item") or {}).get("question_id")

    def practice(self, session, chapter):
        r = self.app.turn(session, L, "practice", chapter=chapter)
        return self.active(session), r["reply"]

    def last_hint(self, session):
        for _ in range(3):
            self.app.turn(session, L, "hint")
        self.app.turn(session, L, "99991")
        return self.app.turn(session, L, "99992")["reply"]

    def answer_correctly(self, session):
        item = BY_ID[self.active(session)]
        key = mathcore.compute_key(item["problem"])["key"]
        text = ", ".join(key["values"]) if key["kind"] == "finite_set" else str(key["value"])
        return self.app.turn(session, L, text)["reply"]

    def saved(self):
        ctx = CallContext("read", learner_id=L)
        snap = self.app.bus.call(ctx, "study_planner", "learner-store", "read_learner", {"learner_id": L})
        return [r["question_ref"] for r in snap.get("revisit_items", [])]


def scenario(name, fn, results):
    with tempfile.TemporaryDirectory() as tmp:
        w = World(tmp)
        w.open()
        seed_learner(w.app.conn, L, {"alias": "Synthetic"})
        try:
            results[name] = fn(w)
        except Exception:
            results[name] = {"crash": traceback.format_exc()[-1200:]}
        finally:
            if w.app:
                w.app.close()


def restart_brings_mark_back(w):
    """Solve the first question, give up on the second; after a restart the second must come first."""
    w.publish(AP[:3])
    chapter = AP[0]["chapter"]
    solved, _ = w.practice("s1", chapter)
    w.answer_correctly("s1")
    marked, _ = w.practice("s1", chapter)
    w.last_hint("s1")
    saved_after = w.saved()
    w.open()  # process restart on the same database
    served, reply = w.practice("s2", chapter)
    return {"solved_first": solved, "marked": marked, "saved_after_hint": saved_after, "served_after_restart": served,
            "mark_came_back_first": served == marked, "reply": reply[:160]}


def many_distinct_marks(w):
    """Session n solves n questions then gives up on the next, so three different questions get marked."""
    w.publish(AP)
    chapter = AP[0]["chapter"]
    marked = []
    for n in range(3):
        for _ in range(n):
            w.practice(f"d{n}", chapter)
            w.answer_correctly(f"d{n}")
        served, _ = w.practice(f"d{n}", chapter)
        w.last_hint(f"d{n}")
        marked.append(served)
    w.open()
    order = []
    for _ in range(4):
        served, _ = w.practice("final", chapter)
        order.append(served)
        w.answer_correctly("final")
    return {"marked": marked, "saved_before_final": None, "final_order": order,
            "marked_served_first": set(order[:3]) == set(marked), "saved_after_final": w.saved()}


def other_chapter_ignores_mark(w):
    w.publish(AP[:2] + TRIG)
    first, _ = w.practice("s1", AP[0]["chapter"])
    w.last_hint("s1")
    w.open()
    served, _ = w.practice("s2", TRIG[0]["chapter"])
    return {"marked": first, "served_in_trig": served, "ok": served == TRIG[0]["question_id"]}


def wrong_keeps_then_right_clears(w):
    w.publish(AP[:2])
    chapter = AP[0]["chapter"]
    first, _ = w.practice("s1", chapter)
    w.last_hint("s1")
    w.open()
    served, _ = w.practice("s2", chapter)
    w.app.turn("s2", L, "99993")
    kept = first in w.saved()
    reply = w.answer_correctly("s2")
    cleared = first not in w.saved()
    w.open()
    next_served, _ = w.practice("s3", chapter)
    return {"served_first": served == first, "kept_after_wrong": kept, "correct_reply": reply[:80],
            "cleared_after_correct": cleared, "s3_served": next_served, "s3_not_the_cleared_one": next_served != first}


def many_marks_order(w):
    w.publish(AP)
    chapter = AP[0]["chapter"]
    marked = []
    for n in range(3):  # three sessions, each gives up on the first question it is served
        served, _ = w.practice(f"m{n}", chapter)
        w.last_hint(f"m{n}")
        marked.append(served)
    w.open()
    order = []
    for n in range(4):
        served, _ = w.practice("final", chapter)
        order.append(served)
        w.answer_correctly("final")
    return {"marked_sessions": marked, "distinct_marked": len(set(marked)), "saved": w.saved(),
            "final_session_order": order, "saved_first": set(order[:len(set(marked))]) == set(marked)}


def deleted_learner(w):
    w.publish(AP[:2])
    chapter = AP[0]["chapter"]
    w.practice("s1", chapter)
    w.last_hint("s1")
    out = {"saved_before": w.saved()}
    try:
        out["forget"] = str(w.app.forget_learner(L, "teacher"))[:200]
    except Exception as exc:
        out["forget"] = f"{type(exc).__name__}: {exc}"[:200]
    for label, session in (("same_session_turn", "s1"), ("new_session_practice", "s9")):
        try:
            text = "99994" if label == "same_session_turn" else "practice"
            r = w.app.turn(session, L, text, chapter=chapter) if text == "practice" else w.app.turn(session, L, text)
            out[label] = r["reply"][:160]
        except Exception as exc:
            out[label] = f"{type(exc).__name__}: {str(exc)[:160]}"
    return out


def deleted_learner_mid_hints(w):
    """Deletion lands while a question is active; the next wrong answer reaches the last hint."""
    w.publish(AP[:2])
    w.practice("s1", AP[0]["chapter"])
    for _ in range(3):
        w.app.turn("s1", L, "hint")
    w.app.turn("s1", L, "99991")
    try:
        w.app.forget_learner(L, "teacher")
    except Exception as exc:
        return {"forget": f"{type(exc).__name__}: {exc}"[:200]}
    try:
        return {"after_last_hint_reply": w.app.turn("s1", L, "99992")["reply"][:200]}
    except Exception as exc:
        return {"after_last_hint_error": f"{type(exc).__name__}: {str(exc)[:200]}"}


def main():
    results = {}
    for name, fn in [("restart_brings_mark_back", restart_brings_mark_back),
                     ("other_chapter_ignores_mark", other_chapter_ignores_mark),
                     ("wrong_keeps_then_right_clears", wrong_keeps_then_right_clears),
                     ("many_marks_order", many_marks_order),
                     ("many_distinct_marks", many_distinct_marks),
                     ("deleted_learner", deleted_learner),
                     ("deleted_learner_mid_hints", deleted_learner_mid_hints)]:
        scenario(name, fn, results)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, ensure_ascii=False)
    print(json.dumps(results, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
