"""R4 regression tests for term-count answers and the narrowed leak check.

Findings 1-3 in Docs/m3/PR7_9_TEST_FINDINGS.md. Offline: no dataset build, model or API key needed.
"""
import pytest

from tutor.mathcore import leak_check, parse_answer

EMPTY_TERMS = {"kind": "finite_set", "values": [], "unit": "terms"}
COUNT_TERMS = {"kind": "finite_set", "values": ["12"], "unit": "terms"}
EMPTY_ROOTS = {"kind": "finite_set", "values": []}
ROOTS = {"kind": "finite_set", "values": ["2", "-3"]}


# Finding 1 and 2: the answer the question asks for must parse as the empty set.
@pytest.mark.parametrize("text", [
    "{}", "{ }", "∅", "empty set", "Empty set.", "the empty set", "none", "None.",
    "no such AP", "there is no such AP", "No such finite AP exists.", "My answer is the empty set",
    "there is no such term", "No such term exists.", "there are no terms", "no valid term count",
    "There is no such term in this AP.", "No such term exists in the AP",
])
def test_empty_answers_parse_as_empty_set(text):
    result = parse_answer(text, EMPTY_TERMS)
    assert result["ok"], text
    assert result["typed"]["values"] == [], text


# Finding 1: other words get the count-specific message instead of becoming made-up values.
@pytest.mark.parametrize("text", [
    "no", "zero", "does not exist", "not possible", "maybe",
    "no such term in my notes, can you help?",
])
def test_other_words_are_rejected_not_turned_into_values(text):
    result = parse_answer(text, EMPTY_TERMS)
    assert not result["ok"], text
    assert "count" in result["reason"]


@pytest.mark.parametrize("text", ["12", "there are 12 terms", "n = 12", "12 terms."])
def test_numeric_counts_still_parse(text):
    result = parse_answer(text, COUNT_TERMS)
    assert result["ok"], text
    assert result["typed"]["values"] == ["12"], text


@pytest.mark.parametrize("text", ["{}", "∅", "no real roots", "none"])
def test_root_sets_accept_empty_notation(text):
    result = parse_answer(text, EMPTY_ROOTS)
    assert result["ok"], text
    assert result["typed"]["values"] == [], text


def test_roots_still_parse():
    result = parse_answer("x = 2 or x = -3", ROOTS)
    assert result["ok"]
    assert sorted(result["typed"]["values"]) == ["-3", "2"]


# Finding 3: ordinary hints on empty-answer items are not leaks; statements of the answer still are.
@pytest.mark.parametrize("line", [
    "There are no terms before the first one.",
    "Remember that no term index can be zero or negative.",
    "Check whether n comes out as a positive whole number.",
])
def test_ordinary_hints_are_not_leaks(line):
    assert not leak_check(line, EMPTY_TERMS)["leak"], line


@pytest.mark.parametrize("line", [
    "There is no such term in this AP.",
    "No such term exists.",
    "So there are no valid terms.",
    "The answer is that there is no valid term count.",
    "there are no terms",
    "There is no term in this AP that fits.",
])
def test_answer_statements_are_still_leaks(line):
    assert leak_check(line, EMPTY_TERMS)["leak"], line
