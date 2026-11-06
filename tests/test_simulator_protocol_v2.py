"""Canonical-format coverage does not imply conversational or learning validity."""
import ast
import copy
from pathlib import Path
import pytest
from tutor_eval import protocol_v2 as v2, simulator
from tutor import mathcore
from tutor.question_catalog import graph_items,allowed
from tutor.app import TutorApp
from tutor.seed import seed_learner

ITEMS=[i for i in graph_items() if allowed(i,"practice")]


@pytest.mark.parametrize("item",ITEMS,ids=lambda i:i["question_id"])
def test_every_public_family_supports_exact_canonical_roundtrip(item):
    problem=item["problem"];key=mathcore.compute_key(problem)["key"]
    assert v2.support(problem)["supported"]
    assert v2.support(problem)["trajectory_coverage"] is False
    text=v2.render(key);parsed=mathcore.parse_answer(text,key)
    assert parsed["ok"] and mathcore.grade(parsed["typed"],key)["correct"]


def test_count_phrase_is_versioned_and_does_not_change_selected_answer():
    answer={"kind":"finite_set","values":[],"unit":"terms"};original=copy.deepcopy(answer)
    assert simulator.render(answer)=="there is no such term"
    assert v2.render(answer)=="no valid term count"
    assert answer==original
    assert v2.render({"kind":"finite_set","values":["0"],"unit":"terms"})=="0 terms"
    assert v2.render({"kind":"finite_set","values":[]})=="no real roots"


def test_student_adapter_preserves_all_random_choices_and_typed_answers():
    item=next(i for i in ITEMS if i["problem"]["task_type"]=="ap_count")
    card={"student_id":"synthetic-protocol","hidden_card":{"true_mastery_by_concept":{},"seeded_misconception_ids":[]}}
    old,new=simulator.Student(card,{},17),v2.StudentV2(card,{},17)
    for index in range(30):
        a=old.answer(item["problem"],str(index));b=new.answer(item["problem"],str(index))
        assert a["typed"]==b["typed"] and a["rule"]==b["rule"]
        assert old.rng.getstate()==new.rng.getstate()
        assert b["text"]==v2.render(a["typed"])


def test_canonical_empty_count_reaches_actual_grading(tmp_path):
    item=next(i for i in ITEMS if i["problem"]["task_type"]=="ap_count" and not mathcore.compute_key(i["problem"])["key"]["values"])
    app=TutorApp(llm_mode="stub",db_name=str(tmp_path/"t.db"),checkpoint_name=str(tmp_path/"c.db"))
    seed_learner(app.conn,"synthetic-protocol",{"alias":"Synthetic protocol fixture; no human review"})
    try:
        proposal=app.propose_set(item["problem"]["concept_ids"][0])
        app.decide(proposal["set_id"],"edit","automated-test-no-human",question_ids=[item["question_id"]])
        app.decide(proposal["set_id"],"approve","automated-test-no-human")
        first=app.turn("protocol","synthetic-protocol","practice",chapter="arithmetic_progressions")
        assert first["active_item"]==item["question_id"]
        key=mathcore.compute_key(item["problem"])["key"]
        result=app.turn("protocol","synthetic-protocol",v2.render(key),chapter="arithmetic_progressions")
        assert result["route"]=="grade" and "Correct:" in result["reply"]
        assert app.conn.execute("SELECT count(*) FROM applied_quizzes").fetchone()[0]==0
    finally:
        app.close()


def test_unknown_tasks_are_reported_and_formatting_does_not_correct_wrong_values():
    assert not v2.support({"task_type":"unknown"})["supported"]
    assert not v2.support({"task_type":"ap_term","givens":{}})["supported"]
    assert v2.render({"kind":"scalar","value":"999"})=="999"
    with pytest.raises(ValueError):v2.render({"kind":"finite_set","values":"3","unit":"terms"})


def test_simulator_adapter_does_not_import_runtime_solver_or_routes():
    tree=ast.parse(Path(v2.__file__).read_text(encoding="utf-8"))
    imports=[n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert not any(name=="tutor" or name.startswith("tutor.") for name in imports)
