"""TP-A3: a question marked for revisit survives into later sessions until the student solves it."""
import pytest

from tutor.app import TutorApp
from tutor.question_catalog import allowed, graph_items
from tutor.seed import seed_learner
from tutor.toolbus import CallContext, ToolCallError

ITEMS = [i for i in graph_items() if i["problem"]["task_type"] == "ap_term" and allowed(i, "practice")][:2]
FIRST, SECOND = (i["question_id"] for i in ITEMS)
CONCEPT = ITEMS[0]["problem"]["concept_ids"][0]
CHAPTER = ITEMS[0]["chapter"]
LEARNER = "synthetic"


def _publish(app, *question_ids):
    proposal = app.propose_set(CONCEPT)
    app.decide(proposal["set_id"], "edit", LEARNER, question_ids=list(question_ids))
    app.decide(proposal["set_id"], "approve", LEARNER)


@pytest.fixture
def tutor(tmp_path):
    app = TutorApp(llm_mode="stub", db_name=str(tmp_path / "tutor.db"), checkpoint_name=str(tmp_path / "checkpoint.db"))
    seed_learner(app.conn, LEARNER, {"alias": "Synthetic"})
    yield app
    app.close()


def _store(app, tool, question_id):
    context = CallContext("setup", learner_id=LEARNER)
    return app.bus.call(context, "study_planner", "learner-store", tool, {"learner_id": LEARNER, "question_ref": question_id})


def _saved(app):
    context = CallContext("read", learner_id=LEARNER)
    snapshot = app.bus.call(context, "study_planner", "learner-store", "read_learner", {"learner_id": LEARNER})
    return [row["question_ref"] for row in snapshot["revisit_items"]]


def _active(app, session):
    return app.graph.get_state({"configurable": {"thread_id": session}}).values["active_item"]["question_id"]


def _reach_last_hint(app, session):
    app.turn(session, LEARNER, "practice", chapter=CHAPTER)
    for _ in range(3):
        app.turn(session, LEARNER, "hint")
    app.turn(session, LEARNER, "99991")
    app.turn(session, LEARNER, "99992")


def _mark_every_answer_correct(app, monkeypatch):
    real_call = app._call

    def call(state, node, role, server, tool, args):
        if tool == "check_equivalence":
            return {"status": "correct", "scorable": True, "correct": True, "reason": None, "parsed": "1"}
        return real_call(state, node, role, server, tool, args)

    monkeypatch.setattr(app, "_call", call)


def test_reaching_the_last_hint_saves_the_mark(tutor):
    _publish(tutor, FIRST)
    _reach_last_hint(tutor, "s1")
    assert _saved(tutor) == [FIRST]


def test_a_later_session_brings_the_saved_question_back_first(tutor):
    _publish(tutor, FIRST, SECOND)
    _store(tutor, "record_revisit", SECOND)
    tutor.turn("s2", LEARNER, "practice", chapter=CHAPTER)
    assert _active(tutor, "s2") == SECOND


def test_the_same_session_moves_on_to_a_new_question_first(tutor):
    _publish(tutor, FIRST, SECOND)
    _reach_last_hint(tutor, "s1")
    marked = _active(tutor, "s1")
    tutor.turn("s1", LEARNER, "practice", chapter=CHAPTER)
    assert _active(tutor, "s1") != marked


def test_a_saved_question_no_longer_published_is_not_served(tutor):
    _publish(tutor, FIRST)
    _store(tutor, "record_revisit", SECOND)
    tutor.turn("s2", LEARNER, "practice", chapter=CHAPTER)
    assert _active(tutor, "s2") == FIRST
    assert _saved(tutor) == [SECOND]


def test_a_wrong_answer_keeps_the_mark(tutor):
    _publish(tutor, FIRST)
    _store(tutor, "record_revisit", FIRST)
    tutor.turn("s2", LEARNER, "practice", chapter=CHAPTER)
    tutor.turn("s2", LEARNER, "99991")
    assert _saved(tutor) == [FIRST]


def test_a_checked_correct_answer_in_a_later_session_clears_the_mark(tutor, monkeypatch):
    _publish(tutor, FIRST)
    _store(tutor, "record_revisit", FIRST)
    tutor.turn("s2", LEARNER, "practice", chapter=CHAPTER)
    _mark_every_answer_correct(tutor, monkeypatch)
    tutor.turn("s2", LEARNER, "1")
    assert _saved(tutor) == []


def test_a_question_the_store_refuses_stays_marked_for_this_session(tutor, monkeypatch):
    _publish(tutor, FIRST)
    real_call = tutor.bus.call

    def call(ctx, role, server, tool, args):
        if tool == "record_revisit":
            raise ToolCallError("INVALID_INPUT", "refused")
        return real_call(ctx, role, server, tool, args)

    monkeypatch.setattr(tutor.bus, "call", call)
    _reach_last_hint(tutor, "s1")
    state = tutor.graph.get_state({"configurable": {"thread_id": "s1"}}).values
    assert state["revisit"] == [FIRST]


def test_the_oldest_saved_question_comes_back_first(tutor):
    _publish(tutor, SECOND, FIRST)
    _store(tutor, "record_revisit", FIRST)
    _store(tutor, "record_revisit", SECOND)
    tutor.turn("s2", LEARNER, "practice", chapter=CHAPTER)
    assert _active(tutor, "s2") == FIRST
