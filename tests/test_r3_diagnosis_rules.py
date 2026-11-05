"""Diagnosis rules, written from the misconception catalogue."""
import json
import re
from pathlib import Path

import pytest

from tutor import mathcore
from tutor.app import MIS_KEYWORDS

CATALOGUE = Path(__file__).resolve().parents[1] / "content" / "dataset-v0.10.0" / "misconceptions.jsonl"
ROWS = {row["misconception_id"]: row for row in map(json.loads, CATALOGUE.read_text(encoding="utf-8").splitlines())}


def _candidates(a, b, c, answer):
    problem = {"task_type": "quadratic_solve", "givens": {"a": a, "b": b, "c": c}}
    return [found["misconception_id"] for found in mathcore.diagnose_response(problem, _key(a, b, c), answer)]


def _key(a, b, c):
    roots = {(1, -7, 10): ["2", "5"], (1, -8, 0): ["0", "8"]}
    return {"kind": "finite_set", "values": roots[(a, b, c)]}


def _set(*values):
    return {"kind": "finite_set", "values": list(values)}


@pytest.mark.parametrize("mid", sorted(MIS_KEYWORDS))
def test_each_catalogue_example_matches_its_keywords(mid):
    assert any(re.search(pattern, ROWS[mid]["example_wrong_work"], re.I) for pattern in MIS_KEYWORDS[mid])


def test_dropping_the_sign_of_b_names_qe_m02():
    assert _candidates(1, -7, 10, _set("-2", "-5")) == ["qe_m02"]


def test_losing_zero_names_qe_m04():
    assert _candidates(1, -8, 0, _set("8")) == ["qe_m04"]


def test_one_root_of_a_factorable_equation_names_qe_m04():
    assert _candidates(1, -7, 10, _set("5")) == ["qe_m04"]


def test_an_unrelated_wrong_answer_names_nothing():
    assert _candidates(1, -7, 10, _set("3")) == []
