"""Stress: natural 'there is no such term' phrasings on term-count items.

Checks three paths for each phrase: the parser (mathcore), the team tutor's router and grader
(TutorApp turn), and the live beta's practice grader (socrates_beta CheckedMaths).
Also measures the new leak pattern on ordinary tutor wording while an empty-answer item is active.

Usage: python stress_phrases.py <tree root> <out.json>   (TUTOR_LLM=stub, offline)
"""
import json
import os
import sys
import tempfile

ROOT = sys.argv[1]
OUT = sys.argv[2]
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("TUTOR_LLM", "stub")

from tutor import mathcore  # noqa: E402
from tutor.app import TutorApp  # noqa: E402
from tutor.question_catalog import allowed, graph_items  # noqa: E402
from tutor.seed import seed_learner  # noqa: E402
from socrates_beta.maths import CheckedMaths  # noqa: E402

ANSWERS = [
    "there is no such term", "There is no such term.", "no such term", "No such term exists.",
    "There is no such term in this AP.", "No such term exists in the AP", "No, there is no such term.",
    "no such AP", "No such finite AP exists.", "no such AP exists", "there is no such AP",
    "empty set", "the empty set", "{}", "∅", "none", "None.", "no answer", "not possible",
    "it is not possible", "no valid term count", "there are no terms", "no positive integer count",
    "no such count", "it doesn't exist", "does not exist", "60 is not a term of this AP",
    "0", "zero", "no",
]
QUESTIONS = [
    "is there no such term?", "what if there is no such term?", "does no such term mean the empty set?",
    "no such term in my notes, can you help?", "what does empty set mean here?", "can the answer be none?",
]
# Ordinary tutor wording that does not give the answer away, for the leak-pattern check.
TUTOR_LINES = [
    "Check whether no term can be negative.", "There are no terms before the first one.",
    "Count the terms from the first to the last.", "Is 60 one of the terms of this AP?",
    "No term is skipped when you count the gaps.", "Remember that no term index can be zero or negative.",
    "What position would the last term occupy?",
]

COUNT = [i for i in graph_items() if allowed(i, "practice") and i["problem"]["task_type"] == "ap_count"]
KEYS = {i["question_id"]: mathcore.compute_key(i["problem"])["key"] for i in COUNT}
EMPTY = next(i for i in COUNT if not KEYS[i["question_id"]]["values"])
FULL = next(i for i in COUNT if KEYS[i["question_id"]]["values"])


def parse(text, item):
    key = KEYS[item["question_id"]]
    parsed = mathcore.parse_answer(text, key)
    if not parsed.get("ok"):
        return "unparsed"
    return "correct" if mathcore.grade(parsed["typed"], key)["correct"] else "wrong"


def beta(maths, text, item):
    result = maths.grade(item["question_id"], text)
    if result.get("status") == "invalid_response":
        return "invalid"
    return "correct" if result.get("correct") else "wrong"


def tutor_turn(text, item):
    with tempfile.TemporaryDirectory() as tmp:
        app = TutorApp(llm_mode="stub", db_name=os.path.join(tmp, "t.db"), checkpoint_name=os.path.join(tmp, "c.db"))
        try:
            seed_learner(app.conn, "L", {"alias": "S"})
            proposal = app.propose_set(item["problem"]["concept_ids"][0])
            app.decide(proposal["set_id"], "edit", "L", question_ids=[item["question_id"]])
            app.decide(proposal["set_id"], "approve", "L")
            app.turn("s", "L", "practice", chapter=item["chapter"])
            r = app.turn("s", "L", text)
            reply = r["reply"]
            verdict = ("correct" if reply.startswith("Correct") else "wrong" if reply.startswith("Not quite")
                       else "fallback" if "Let's slow down" in reply else "not_graded")
            return {"route": r.get("route"), "verdict": verdict, "reply": reply[:140]}
        finally:
            app.close()


def main():
    maths = CheckedMaths(ROOT)
    rows = []
    for text in ANSWERS + QUESTIONS:
        row = {"text": text, "is_question": text in QUESTIONS}
        for label, item in (("empty", EMPTY), ("full", FULL)):
            row[f"{label}_parser"] = parse(text, item)
            row[f"{label}_beta"] = beta(maths, text, item)
            row[f"{label}_tutor"] = tutor_turn(text, item)
        rows.append(row)
    leak = {line: mathcore.leak_check(line, KEYS[EMPTY["question_id"]])["leak"] for line in TUTOR_LINES}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"empty_item": EMPTY["question_id"], "full_item": FULL["question_id"], "rows": rows,
                   "leak_on_ordinary_tutor_lines": leak}, fh, indent=1, ensure_ascii=False)
    print("done", OUT)


if __name__ == "__main__":
    main()
