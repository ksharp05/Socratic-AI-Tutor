"""Single-value answers written with thousands separators are graded on their value.

Found on 11 Nov by the public test set (GSM8K and MATH answers): "70,000" was read as "000" and marked incorrect.
Indian students also write lakh grouping ("1,00,000"). A comma-separated list is not joined into one number.
"""
import pytest

from tutor import mathcore

KEY = lambda v: {"kind": "scalar", "value": v}  # noqa: E731


def grade(text, value):
    parsed = mathcore.parse_answer(text, KEY(value))
    assert parsed["ok"], parsed
    return mathcore.grade(parsed["typed"], KEY(value))["status"]


@pytest.mark.parametrize("text,value", [
    ("70,000", "70000"),
    ("1,275", "1275"),
    ("The answer is 1,275", "1275"),
    ("x = 57,500", "57500"),
    ("1,00,000", "100000"),          # Indian lakh grouping
    ("12,34,567", "1234567"),
    ("-1,000", "-1000"),
    ("1,000,000", "1000000"),
])
def test_grouped_numbers_are_read_as_one_value(text, value):
    assert grade(text, value) == "correct"


@pytest.mark.parametrize("text,value", [
    ("70,001", "70000"),
    ("1,00,001", "100000"),
])
def test_grouped_numbers_still_fail_when_wrong(text, value):
    assert grade(text, value) == "incorrect"


@pytest.mark.parametrize("text", ["2,3", "1,5", "10,20"])
def test_lists_are_not_joined_into_one_number(text):
    parsed = mathcore.parse_answer(text, KEY("23"))
    if parsed["ok"]:
        assert mathcore.grade(parsed["typed"], KEY("23"))["status"] != "correct"
        assert mathcore.grade(parsed["typed"], KEY("1020"))["status"] != "correct" if text == "10,20" else True


def test_root_lists_are_unchanged():
    key = {"kind": "finite_set", "values": ["2", "3"]}
    parsed = mathcore.parse_answer("x = 2, 3", key)
    assert parsed["ok"] and mathcore.grade(parsed["typed"], key)["status"] == "correct"
