"""TP-A2: after the last hint the tutor shows R4's checked worked example, word for word."""
import pytest

from tutor.app import TutorApp
from tutor.question_catalog import allowed, graph_items
from tutor.seed import seed_learner
from tutor.toolbus import ToolCallError

ITEM = next(i for i in graph_items() if i["problem"]["task_type"] == "ap_term" and allowed(i, "practice"))
LEARNER = "synthetic"


@pytest.fixture
def tutor(tmp_path):
    app = TutorApp(llm_mode="stub", db_name=str(tmp_path / "tutor.db"), checkpoint_name=str(tmp_path / "checkpoint.db"))
    seed_learner(app.conn, LEARNER, {"alias": "Synthetic"})
    proposal = app.propose_set(ITEM["problem"]["concept_ids"][0])
    app.decide(proposal["set_id"], "edit", LEARNER, question_ids=[ITEM["question_id"]])
    app.decide(proposal["set_id"], "approve", LEARNER)
    yield app
    app.close()


def _reach_last_hint(app, session="s"):
    app.turn(session, LEARNER, "practice", chapter=ITEM["chapter"])
    for _ in range(3):
        app.turn(session, LEARNER, "hint")
    app.turn(session, LEARNER, "99991")
    return app.turn(session, LEARNER, "99992")["reply"]


def test_the_checked_example_is_shown_word_for_word(tutor, monkeypatch):
    seen = []
    real_call = tutor.bus.call

    def call(ctx, role, server, tool, args):
        result = real_call(ctx, role, server, tool, args)
        if tool == "generate_parallel_example":
            seen.append((result, ctx))
        return result

    monkeypatch.setattr(tutor.bus, "call", call)
    reply = _reach_last_hint(tutor)
    result, ctx = seen[-1]
    assert result["example"]["presentation"] in reply
    assert ctx.parallel_example_for is None


def test_the_reply_asks_one_question_and_cites_the_chapter(tutor):
    reply = _reach_last_hint(tutor).split("(Study plan")[0]
    assert reply.count("?") == 1
    assert f"[{ITEM['supporting_passage_ids'][0]}]" in reply


def test_a_refused_call_falls_back_to_the_last_hint(tutor, monkeypatch):
    real_call = tutor.bus.call

    def call(ctx, role, server, tool, args):
        if tool == "generate_parallel_example":
            raise ToolCallError("FORBIDDEN", "refused")
        return real_call(ctx, role, server, tool, args)

    monkeypatch.setattr(tutor.bus, "call", call)
    reply = _reach_last_hint(tutor)
    assert "Parallel example" not in reply
    assert "Type 'practice'" in reply


def test_hints_before_the_trigger_never_show_an_example(tutor):
    tutor.turn("s", LEARNER, "practice", chapter=ITEM["chapter"])
    for _ in range(3):
        assert "Parallel example" not in tutor.turn("s", LEARNER, "hint")["reply"]
