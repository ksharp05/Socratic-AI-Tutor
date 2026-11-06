"""Boundary cases are a safety contract, not a promise of an example for every item."""
import copy
import pytest

from socratic_data import tasks, math_kernel as mk
from tutor import mathcore, parallel_examples as pe, parallel_regimes as regimes
from tutor_validation import exact_reference as reference


CASES = [
    ("distinct-positive", "quadratic_solve", {"a":1,"b":-5,"c":6}, {"discriminant_class":1,"rational_roots":True,"unit_leading_magnitude":True}, True),
    ("repeated-positive-one", "quadratic_solve", {"a":1,"b":-2,"c":1}, {"discriminant_class":0,"root_sign_pattern":"positive"}, True),
    ("repeated-negative-nonmonic", "quadratic_solve", {"a":-2,"b":-12,"c":-18}, {"discriminant_class":0,"leading_sign":-1,"unit_leading_magnitude":False}, True),
    ("irrational-mixed", "quadratic_solve", {"a":1,"b":0,"c":-2}, {"rational_roots":False,"linear_term_zero":True,"root_sign_pattern":"mixed"}, True),
    ("irrational-positive", "quadratic_solve", {"a":1,"b":-4,"c":2}, {"rational_roots":False,"root_sign_pattern":"both_positive"}, True),
    ("no-real", "quadratic_solve", {"a":1,"b":2,"c":5}, {"discriminant_class":-1}, False),
    ("zero-root", "quadratic_solve", {"a":1,"b":-4,"c":0}, {"zero_root":True}, False),
    ("only-zero-root", "quadratic_solve", {"a":3,"b":0,"c":0}, {"zero_root":True}, False),
    ("decreasing-crosses-zero", "ap_term", {"a":12,"d":-4,"n":6}, {"direction":-1,"initial_sign":1,"last_sign":-1}, True),
    ("constant-positive", "ap_term", {"a":7,"d":0,"n":8}, {"direction":0,"last_sign":1}, True),
    ("first-position", "ap_term", {"a":7,"d":-3,"n":1}, {"first_position":True}, True),
    ("zero-term", "ap_term", {"a":12,"d":-4,"n":4}, {"last_sign":0}, False),
    ("negative-sum", "ap_sum", {"a":-3,"d":-2,"n":5}, {"direction":-1,"sum_sign":-1}, True),
    ("zero-sum", "ap_sum", {"a":-5,"d":2,"n":6}, {"sum_sign":0}, False),
    ("recover-negative-first", "ap_first", {"d":3,"n":6,"term":8}, {"initial_sign":-1,"last_sign":1}, True),
    ("recover-zero-first", "ap_first", {"d":4,"n":3,"term":8}, {"initial_sign":0}, False),
    ("fractional-difference", "ap_difference", {"m":2,"n":4,"term_m":5,"term_n":8}, {"integral_difference":False,"index_order":1}, True),
    ("reversed-positions", "ap_difference", {"m":5,"n":2,"term_m":2,"term_n":11}, {"direction":-1,"index_order":-1}, True),
    ("zero-difference", "ap_difference", {"m":2,"n":5,"term_m":8,"term_n":8}, {"direction":0}, False),
    ("count-to-zero", "ap_count", {"a":-12,"d":3,"last":0}, {"last_sign":0,"positive_integral_count":True}, True),
    ("decreasing-count", "ap_count", {"a":10,"d":-3,"last":-2}, {"direction":-1,"last_sign":-1}, True),
    ("invalid-count", "ap_count", {"a":2,"d":4,"last":12}, {"positive_integral_count":False}, False),
    ("one-term-count", "ap_count", {"a":7,"d":3,"last":7}, {"first_position":True}, False),
    ("negative-half-mean", "ap_mean", {"left":-8,"right":3}, {"integral_mean":False,"mean_sign":-1}, True),
    ("descending-half-mean", "ap_mean", {"left":8,"right":-3}, {"endpoint_order":-1,"mean_sign":1}, True),
    ("zero-mean", "ap_mean", {"left":-5,"right":5}, {"mean_sign":0}, False),
    ("ledger-crosses-zero", "ap_ledger_term", {"n":2,"previous_sum":"-3/2","prefix_sum":"5/2"}, {"earlier_sum_sign":-1,"later_sum_sign":1,"first_prefix":True}, True),
    ("ledger-decreases", "ap_ledger_term", {"n":7,"previous_sum":"5","prefix_sum":"-7"}, {"increment_sign":-1,"first_prefix":False}, True),
    ("zero-ledger-increment", "ap_ledger_term", {"n":4,"previous_sum":"3","prefix_sum":"3"}, {"increment_sign":0}, False),
] + [
    (f"triangle-{ratio}-{angle}", "trig_triangle_ratio",
     {"opposite":3,"adjacent":4,"hypotenuse":5,"ratio":ratio,"reference":angle},
     {"ratio":ratio,"reference":angle,"leg_order":-1}, True)
    for ratio in ("sin","cos","tan","csc","sec","cot") for angle in ("A","C")
]


@pytest.mark.parametrize("name,task,givens,expected,available", CASES, ids=[c[0] for c in CASES])
def test_named_mathematical_cases_and_safe_fallbacks(name, task, givens, expected, available):
    problem = tasks.problem(task, givens)
    original = copy.deepcopy(problem)
    item = {"question_id": "synthetic:"+name, "problem": problem}
    key = mathcore.compute_key(problem)["key"]
    result = pe.generate(item, key)
    assert problem == original
    assert {k:regimes.signature(problem)[k] for k in expected} == expected
    assert result["available"] is available, result
    if available:
        example = result["example"]
        assert {k:regimes.signature(example["problem"])[k] for k in expected} == expected
        assert pe.verify(example, problem)
        assert reference.validate(example["problem"],example["answer"])["status"] == "verified"
        assert not mk.answers_equivalent(key,example["answer"])
        assert not mathcore.leak_check(example["presentation"],key)["leak"]
        assert result["case_policy_version"] == regimes.VERSION
        assert result["exact_oracle_version"] == reference.VERSION
        if task == "quadratic_solve":
            assert len(example["answer"]["values"]) == len(key["values"])
            assert all(not mk.equivalent(a,b) for a in key["values"] for b in example["answer"]["values"])
    else:
        assert result["reason"] == "preserved_case_conflicts_with_active_item_guard"
        assert "example" not in result and "answer" not in result


def test_irrational_formula_and_repeated_factor_proofs_reject_tampering():
    for givens in ({"a":2,"b":3,"c":-1}, {"a":3,"b":-18,"c":27}):
        problem=tasks.problem("quadratic_solve",givens)
        result=pe.generate({"question_id":"synthetic:proof","problem":problem}, mathcore.compute_key(problem)["key"])
        assert result["available"]
        example=copy.deepcopy(result["example"])
        example["worked_steps"][-1]["roots"]=["999"]
        assert not pe.verify(example,problem)


def test_case_binding_rejects_a_correct_example_for_a_different_case():
    source=tasks.problem("quadratic_solve",{"a":1,"b":-5,"c":6})
    other=tasks.problem("quadratic_solve",{"a":1,"b":-8,"c":16})
    key=mathcore.compute_key(other)["key"]
    example={"problem":other,"answer":key,**pe.worked(other,key)}
    assert pe.verify(example)
    assert not pe.verify(example,source)


def test_separate_reference_checker_is_an_enforced_gate(monkeypatch):
    problem=tasks.problem("ap_term",{"a":7,"d":3,"n":5})
    item={"question_id":"synthetic:oracle","problem":problem};key=mathcore.compute_key(problem)["key"]
    example=pe.generate(item,key)["example"]
    monkeypatch.setattr(reference,"validate",lambda *args:{"status":"failed"})
    assert not pe.verify(example,problem)
    assert pe.generate(item,key)["reason"] == "unverified_active_problem"


def test_candidate_search_is_bounded_when_every_answer_conflicts(monkeypatch):
    problem=tasks.problem("ap_term",{"a":7,"d":3,"n":5});calls=[]
    def same(source,index):
        calls.append(index)
        return copy.deepcopy(source)
    monkeypatch.setattr(regimes,"candidate",same)
    result=pe.generate({"question_id":"synthetic:bounded","problem":problem},mathcore.compute_key(problem)["key"])
    assert not result["available"] and len(calls)==64


@pytest.mark.parametrize("item,key",[(None,None), ({},{}), ({"problem":{"task_type":"ap_count","givens":{"a":2,"d":0,"last":3}}},{})])
def test_malformed_originals_fail_closed(item,key):
    assert pe.generate(item,key)["available"] is False
