"""One test per MCP tool, through the ToolBus (so the permission hooks are exercised too)."""
import pytest

from tutor.toolbus import CallContext, ToolCallError
from tutor.setup_content import load

ITEM = load("practice")[0]["question_id"]


def call(app, role, server, tool, args, learner_id=None):
    return app.bus.call(CallContext(session_id="test-tools", learner_id=learner_id), role, server, tool, args)


def test_textbook_search_returns_cited_passages(app):
    out = call(app, "tutor", "textbook-kb", "search", {"query": "both factors zero product"})
    assert out["results"] and out["results"][0]["passage_id"].startswith("normalized:")


def test_textbook_get_section_and_not_found(app):
    assert call(app, "tutor", "textbook-kb", "get_section", {"passage_id": "normalized:qe04"})["concept_id"] == "qe04"
    with pytest.raises(ToolCallError, match="NOT_FOUND"):
        call(app, "tutor", "textbook-kb", "get_section", {"passage_id": "normalized:zz99"})


def test_math_solve_hides_key(app):
    out = call(app, "question_setter", "math-tools", "solve", {"question_ref": ITEM})
    assert out["verified"] is True and "key" not in out and "values" not in out


def test_math_parse_answer(app):
    out = call(app, "grader", "math-tools", "parse_answer", {"question_ref": ITEM, "text": "x = 2 or x = -3"})
    assert out["ok"] and out["display"] == "{2, -3}"


def test_math_check_equivalence_wrong_and_unreadable(app):
    assert call(app, "grader", "math-tools", "check_equivalence",
                {"question_ref": ITEM, "response": "x = 12345"})["status"] == "incorrect"
    assert call(app, "grader", "math-tools", "check_equivalence",
                {"question_ref": ITEM, "response": "banana"})["scorable"] is False


def test_math_diagnose_response_finds_lost_root():
    from tutor import mathcore
    problem = {"task_type": "quadratic_solve", "givens": {"a": 1, "b": -5, "c": 0}, "concept_ids": ["qe03", "qe04", "qe05"],
               "answer_precision": "exact", "class": 10, "language": "en", "number_domain": "real"}
    key = mathcore.compute_key(problem)["key"]
    typed = mathcore.parse_answer("x = 5", key)["typed"]
    assert mathcore.diagnose_response(problem, key, typed)[0]["misconception_id"] == "qe_m04"
    sym = {**problem, "givens": {"a": 1, "b": 0, "c": -9}}
    key2 = mathcore.compute_key(sym)["key"]
    assert mathcore.diagnose_response(sym, key2, mathcore.parse_answer("3", key2)["typed"])[0]["misconception_id"] == "qe_m05"


def test_math_diagnose_response_tool(app):
    out = call(app, "diagnostician", "math-tools", "diagnose_response", {"question_ref": ITEM, "response": "x = 1"})
    assert "candidates" in out


def test_math_leak_check():
    from tutor import mathcore
    key = {"kind": "finite_set", "values": ["-3", "3"]}
    assert mathcore.leak_check("So the roots are 3 and -3.", key)["leak"] is True
    assert mathcore.leak_check("Is x = 3 the only value that works?", key)["leak"] is False


def test_learner_read_and_update_mastery_bounds(app):
    assert "mastery" in call(app, "study_planner", "learner-store", "read_learner", {"learner_id": "L-A"}, "L-A")
    with pytest.raises(ToolCallError, match="INVALID_INPUT"):
        call(app, "study_planner", "learner-store", "update_mastery",
             {"learner_id": "L-A", "concept_id": "qe04", "p_mastery": 1.5, "evidence_ref": "t"}, "L-A")


def test_learner_record_misconception_rejects_unknown(app):
    with pytest.raises(ToolCallError, match="INVALID_INPUT"):
        call(app, "study_planner", "learner-store", "record_misconception",
             {"learner_id": "L-A", "misconception_id": "xx_m99", "status": "suspected", "evidence_ref": "t"}, "L-A")


def test_learner_record_explanation_and_save_plan(app):
    assert call(app, "study_planner", "learner-store", "record_explanation",
                {"learner_id": "L-A", "misconception_id": "qe_m04", "style": "analogy", "success": True}, "L-A")["ok"]
    assert call(app, "study_planner", "learner-store", "save_plan",
                {"learner_id": "L-A", "plan": {"version": 9, "steps": []}}, "L-A")["ok"]


def test_question_bank_list_candidates_and_propose_never_publishes(app):
    ids = call(app, "question_setter", "question-bank", "candidate_items", {"concept_id": "qe04"})["question_ids"]
    out = call(app, "question_setter", "question-bank", "propose_set",
               {"set_id": "set-unit", "concept_id": "qe04", "question_ids": ids[:2], "rationale": "t", "thread_id": "t"})
    published = call(app, "question_setter", "question-bank", "list_published", {})["items"]
    assert out["payload_sha256"] and not any(i["set_id"] == "set-unit" for i in published)


def test_question_bank_get_update_reject(app):
    before = call(app, "approval_gate", "question-bank", "get_proposal", {"set_id": "set-unit"})
    ids = [i["question_id"] for i in before["payload"]["items"]][:1]
    after = call(app, "approval_gate", "question-bank", "update_proposal",
                 {"set_id": "set-unit", "question_ids": ids, "thread_id": "t"})
    assert after["payload_sha256"] != before["payload_sha256"]
    assert call(app, "approval_gate", "question-bank", "reject_proposal", {"set_id": "set-unit", "reason": "t"})["rejected"]


def test_question_bank_publish_needs_matching_token(app):
    with pytest.raises(ToolCallError, match="FORBIDDEN"):
        call(app, "approval_gate", "question-bank", "publish_approved_set",
             {"set_id": "set-unit", "approval_token": "0" * 64, "teacher_id": "T-001"})


def test_hooks_block_wrong_role_and_other_learner(app):
    with pytest.raises(ToolCallError, match="FORBIDDEN"):
        call(app, "tutor", "question-bank", "publish_approved_set", {"set_id": "x", "approval_token": "y", "teacher_id": "z"})
    with pytest.raises(ToolCallError, match="own learner"):
        call(app, "study_planner", "learner-store", "read_learner", {"learner_id": "L-B"}, learner_id="L-A")
