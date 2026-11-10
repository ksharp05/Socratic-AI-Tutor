"""R4 regression tests for the distress check (finding 8 in Docs/m3/PR7_9_TEST_FINDINGS.md).

"I'm hopeless at trigonometry" is about schoolwork and must not trigger the helpline handoff;
real distress must still be caught. Offline: no model or API key needed.
"""
import pytest

from tutor.guards import screen_input


@pytest.mark.parametrize("text", [
    "I'm hopeless at trigonometry",
    "I am hopeless at trig, can you help?",
    "I'm hopeless in maths",
    "I'm hopeless with fractions",
    "This quadratic is killing me, can you give me a hint?",
    "A die is thrown twice. What is the probability?",
])
def test_schoolwork_wording_is_not_distress(text):
    assert not screen_input(text)["distress"], text


@pytest.mark.parametrize("text", [
    "I feel hopeless",
    "Everything is hopeless",
    "I'm hopeless",
    "I feel hopeless at school",
    "I want to die",
    "I don't want to live anymore",
    "mar jana hai",
    "There is no reason to live",
])
def test_real_distress_is_still_caught(text):
    assert screen_input(text)["distress"], text
