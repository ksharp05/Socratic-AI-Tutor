"""A student can say a term-count question has no answer in natural words, not only 'no valid term count'."""
import pytest

from tutor import mathcore
from tutor.app import TutorApp
from tutor.question_catalog import allowed, graph_items
from tutor.seed import seed_learner

COUNTS = [i for i in graph_items() if i["problem"]["task_type"] == "ap_count" and allowed(i, "practice")]
KEYS = {i["question_id"]: mathcore.compute_key(i["problem"])["key"] for i in COUNTS}
EMPTY = next(i for i in COUNTS if not KEYS[i["question_id"]]["values"])
FULL = next(i for i in COUNTS if KEYS[i["question_id"]]["values"])
EMPTY_KEY, FULL_KEY = KEYS[EMPTY["question_id"]], KEYS[FULL["question_id"]]
LEARNER = "synthetic"
SAYS_NONE = ["there is no such term", "There is no such term.", "no such term", "no such term exists",
             "there are no such terms", "no term", "I think there is no such term", "no valid term count"]
NOT_ANSWERS = ["is there no such term?", "no such term in my notes, can you help?"]


@pytest.mark.parametrize("text", SAYS_NONE)
def test_the_phrase_is_right_when_the_question_has_no_answer(text):
    parsed = mathcore.parse_answer(text, EMPTY_KEY)
    assert parsed["typed"]["values"] == []
    assert mathcore.grade(parsed["typed"], EMPTY_KEY)["correct"]


@pytest.mark.parametrize("text", SAYS_NONE)
def test_the_phrase_is_wrong_when_the_question_has_an_answer(text):
    parsed = mathcore.parse_answer(text, FULL_KEY)
    assert not mathcore.grade(parsed["typed"], FULL_KEY)["correct"]


@pytest.mark.parametrize("text", NOT_ANSWERS)
def test_a_question_about_the_phrase_is_not_an_answer(text):
    assert not mathcore.NO_TERM_ANSWER.search(text)


def test_a_tutor_reply_with_the_phrase_counts_as_a_leak():
    assert mathcore.leak_check("Look closely: there is no such term, so check it.", EMPTY_KEY)["leak"]


@pytest.fixture
def tutor(tmp_path):
    app = TutorApp(llm_mode="stub", db_name=str(tmp_path / "tutor.db"), checkpoint_name=str(tmp_path / "checkpoint.db"))
    seed_learner(app.conn, LEARNER, {"alias": "Synthetic"})
    proposal = app.propose_set(EMPTY["problem"]["concept_ids"][0])
    app.decide(proposal["set_id"], "edit", LEARNER, question_ids=[EMPTY["question_id"]])
    app.decide(proposal["set_id"], "approve", LEARNER)
    tutor_session = "s"
    app.turn(tutor_session, LEARNER, "practice", chapter=EMPTY["chapter"])
    yield app
    app.close()


def test_the_phrase_reaches_the_grader_in_a_real_turn(tutor):
    result = tutor.turn("s", LEARNER, "there is no such term")
    assert result["route"] == "grade"
    assert result["reply"].startswith("Correct")


def test_a_question_about_the_phrase_is_not_graded(tutor):
    assert tutor.turn("s", LEARNER, "is there no such term?")["route"] != "grade"
