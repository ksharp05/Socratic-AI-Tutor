"""POC evaluation: development cards only. Pre-quiz -> tutoring session -> post-quiz, scored by code.

Every number here is a smoke test of the harness, not a result (see Docs/plan/10-proof-of-concept.md).
"""
from __future__ import annotations

import json
import statistics
import time

from tutor import mathcore, store
from tutor.config import EVAL_DIR, SETTINGS, db_path
from tutor.seed import seed_learner
from tutor.setup_content import load

MAX_TUTOR_TURNS = 6


def _quiz_score(student, items: list[dict]) -> tuple[int, list[dict]]:
    rows = []
    for item in items:
        text = student.answer(item["problem"])
        key = mathcore.compute_key(item["problem"])["key"]
        parsed = mathcore.parse_answer(text, key)
        correct = bool(parsed["ok"] and mathcore.grade(parsed["typed"], key)["correct"])
        rows.append({"question_id": item["question_id"], "answer": text, "correct": correct})
    return sum(r["correct"] for r in rows), rows


def _prepare_eval_db() -> None:
    conn = store.connect(db_path("eval.db"))
    conn.execute("DELETE FROM published")
    payload = {"set_id": "eval-fixture", "concept_id": "qe04", "revision": 1,
               "items": [{k: q[k] for k in ("question_id", "prompt", "problem", "answer_contract", "hint_stages",
                                            "difficulty")} for q in load("practice")]}
    # Evaluation database only: fixture items are clearly labelled and never count as a teacher approval.
    conn.execute("INSERT OR REPLACE INTO published VALUES (?,?,?,?,?,?)",
                 ("eval-fixture", store.dumps(payload), "n/a", "none", "eval_fixture_unapproved", store.now()))
    conn.close()


def run_card(app, card: dict, seed: int, quiz_pairs: list[dict]) -> dict:
    from tutor_eval.simstudent import SimStudent
    student = SimStudent(card, seed)
    lid = f"sim-{card['student_id'][-3:]}-s{seed}"
    seed_learner(app.conn, lid, {"alias": "simulated student"})  # the tutor starts with no knowledge of the card
    session = f"eval-{lid}-{int(time.time())}"
    pre, pre_rows = _quiz_score(student, [p["pre"] for p in quiz_pairs])
    seeded = list(student.active)

    transcript, diagnosed, shown_items, latencies = [], set(), [], []
    script = [student.opener(), student.reply_to_probe(), "practice", None, "hint", None]
    item_problem = None
    for message in script[:MAX_TUTOR_TURNS]:
        if message is None:  # answer the item currently on screen
            if not item_problem:
                continue
            message = student.answer(item_problem)
        started = time.perf_counter()
        result = app.turn(session, lid, message)
        latencies.append((time.perf_counter() - started) * 1000)
        transcript.append({"student": message, "tutor": result["reply"], "route": result["route"]})
        if result.get("diagnosis"):
            diagnosed.add(result["diagnosis"]["misconception_id"])
        if result.get("active_item"):
            item = next(q for q in load("practice") if q["question_id"] == result["active_item"])
            item_problem = item["problem"]
            shown_items.append(item)
        if result["route"] == "grade" and "Correct" in result["reply"] and item_problem:
            student.learn(item_problem["concept_ids"])
    snapshot = app.conn.execute("SELECT misconception_id, status FROM misconceptions WHERE learner_id=?", (lid,)).fetchall()
    addressed = {r["misconception_id"] for r in snapshot if r["status"] in ("addressed", "resolved")}
    cleared = [m for m in seeded if student.maybe_clear(m, m in diagnosed, m in addressed)]
    post, post_rows = _quiz_score(student, [p["post"] for p in quiz_pairs])

    leaks = 0
    for turn in transcript:
        for item in shown_items:
            key = mathcore.compute_key(item["problem"])["key"]
            if mathcore.leak_check(turn["tutor"], key)["leak"] and not turn["tutor"].startswith("Practice"):
                leaks += 1
    tool_calls = app.conn.execute("SELECT COUNT(*) FROM trace_events WHERE session_id=? AND kind='tool'",
                                  (session,)).fetchone()[0]
    return {"student": card["student_id"], "seed": seed, "session": session, "seeded": seeded,
            "diagnosed": sorted(diagnosed), "diagnosis_hit": bool(set(seeded) & diagnosed), "addressed": sorted(addressed),
            "cleared": cleared, "pre": pre, "post": post, "n_quiz": len(quiz_pairs), "gain": post - pre, "leaks": leaks,
            "turns": len(transcript), "tool_calls": tool_calls,
            "latency_ms_median": round(statistics.median(latencies), 1) if latencies else None,
            "transcript": transcript}


def main(seeds: int = 1, defences: bool = True) -> list[dict]:
    from tutor.app import TutorApp
    _prepare_eval_db()
    app = TutorApp(defences=defences, db_name="eval.db", checkpoint_name="eval_checkpoints.db")
    cards = json.loads((EVAL_DIR / "students.json").read_text(encoding="utf-8"))
    pairs = json.loads((EVAL_DIR / "quiz_pairs.json").read_text(encoding="utf-8"))
    assert all(c["partition"] == "development" for c in cards)
    results = []
    try:
        for card in cards:
            for s in range(seeds):
                results.append(run_card(app, card, card["seed"] + s, pairs))
    finally:
        app.close()
    failed = len(app.llm.errors)
    report = _report(results, defences, app.llm.label + (f"; {failed} live calls failed and used templates "
                                                          f"(run `tutor check-llm`)" if failed else ""))
    out = db_path("reports").parent / "reports"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"poc_eval_{time.strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(report, encoding="utf-8")
    (path.with_suffix(".json")).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(report)
    print(f"Report: {path}")
    return results


def _report(results: list[dict], defences: bool, llm: str) -> str:
    lines = ["# POC evaluation (smoke test, not a result)", "",
             f"Config sha256 `{SETTINGS.sha256[:12]}` · defences {'on' if defences else 'off'} · LLM: {llm}",
             "Development cards only. Learning is modelled by the simulator's pre-registered rules (see simstudent.py).",
             "", "| Student | Seed | Seeded | Diagnosed | Hit | Cleared | Pre | Post | Gain | Leaks | Turns | Tool calls | Median turn ms |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['student']} | {r['seed']} | {', '.join(r['seeded'])} | {', '.join(r['diagnosed']) or '-'} | "
                     f"{'yes' if r['diagnosis_hit'] else 'no'} | {', '.join(r['cleared']) or '-'} | {r['pre']}/{r['n_quiz']} | "
                     f"{r['post']}/{r['n_quiz']} | {r['gain']:+d} | {r['leaks']} | {r['turns']} | {r['tool_calls']} | "
                     f"{r['latency_ms_median']} |")
    lines += ["", "## Transcripts", ""]
    for r in results:
        lines.append(f"### {r['student']} (seed {r['seed']}, session `{r['session']}`)")
        for t in r["transcript"]:
            lines.append(f"- **Student:** {t['student']}\n  **Tutor** ({t['route']}): {t['tutor']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
