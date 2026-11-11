"""R4 tests for the D-7 safety classifier (offline: a fake model, no key, no network).

Checks the switch, parsing, routing, fallback, fail-closed behaviour, and that the phrase screens answer
distress without a model call. Live behaviour is checked separately by scripts/r4/classifier_live_check.py.
"""
import pytest

from tutor import safety_classifier as sc
from tutor.guards import screen_with_classifier


class FakeLLM:
    def __init__(self, *replies, enabled=True):
        self.replies = list(replies)
        self.enabled = enabled
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return self.replies.pop(0) if self.replies else None


@pytest.fixture
def on(monkeypatch):
    monkeypatch.setenv("TUTOR_SAFETY_CLASSIFIER", "on")
    monkeypatch.delenv("TUTOR_SAFETY_FAIL_MODE", raising=False)


def reply(category, language="en", query=""):
    return '{"category": "%s", "language": "%s", "english_query": "%s"}' % (category, language, query)


def test_off_by_default_makes_no_call(monkeypatch):
    monkeypatch.delenv("TUTOR_SAFETY_CLASSIFIER", raising=False)
    llm = FakeLLM(reply("sexual"))
    result = sc.classify("hello", llm)
    assert result == {"source": "off", "category": None, "route": None, "allowed": True}
    assert llm.calls == []


def test_no_key_makes_no_call(on):
    llm = FakeLLM(reply("sexual"), enabled=False)
    assert sc.classify("hello", llm)["source"] == "off"
    assert llm.calls == []


@pytest.mark.parametrize("category, route, allowed", [
    ("learn", "teach", True), ("profanity_learn", "teach", True),
    ("self_harm", "crisis", False), ("child_safety", "crisis", False),
    ("sexual", "policy", False), ("hate", "policy", False), ("dangerous", "policy", False),
    ("injection", "policy", False), ("answer_extraction", "policy", False), ("off_topic", "policy", False),
])
def test_routes(on, category, route, allowed):
    result = sc.classify("message", FakeLLM(reply(category)))
    assert (result["source"], result["category"], result["route"], result["allowed"]) == ("model", category, route, allowed)


def test_uses_gemma_with_the_tested_prompt(on):
    llm = FakeLLM(reply("learn"))
    sc.classify("what is a discriminant?", llm, history=["hi", "help with quadratics"])
    call = llm.calls[0]
    assert call["model"] == "google/gemma-4-31b-it"
    assert call["system"] == sc.CLASSIFY_V2
    assert "Latest message: <<<what is a discriminant?>>>" in call["user"]
    assert "<<<help with quadratics>>>" in call["user"]


def test_reads_json_inside_fences_and_keeps_language(on):
    result = sc.classify("x", FakeLLM('```json\n' + reply("learn", "hinglish", "What is an AP?") + '\n```'))
    assert (result["language"], result["english_query"]) == ("hinglish", "What is an AP?")


@pytest.mark.parametrize("bad", [None, "", "SAFE", "{not json}", reply("unknown_category")])
def test_falls_back_when_the_first_reply_is_unusable(on, bad):
    llm = FakeLLM(bad, reply("violence"))
    result = sc.classify("x", llm)
    assert (result["source"], result["category"], result["allowed"]) == ("fallback", "violence", False)
    assert llm.calls[1]["model"] == "anthropic/claude-haiku-5.5"


def test_fails_closed_when_both_fail(on):
    result = sc.classify("x", FakeLLM(None, "???"))
    assert (result["source"], result["allowed"]) == ("fail_closed", False)


def test_fail_open_is_a_setting(on, monkeypatch):
    monkeypatch.setenv("TUTOR_SAFETY_FAIL_MODE", "open")
    result = sc.classify("x", FakeLLM(None, None))
    assert (result["source"], result["allowed"]) == ("fail_open", True)


def test_distress_is_answered_by_the_screen_without_a_model_call(on):
    llm = FakeLLM(reply("learn"))
    flags = screen_with_classifier("I want to die", llm)
    assert flags["distress"] and flags["classifier"]["route"] == "crisis"
    assert llm.calls == []


def test_the_model_sees_redacted_text(on):
    llm = FakeLLM(reply("privacy"))
    flags = screen_with_classifier("call me on 9876543210 about AP", llm)
    assert "9876543210" not in llm.calls[0]["user"]
    assert flags["classifier"]["category"] == "privacy"


def test_classifier_off_leaves_screen_input_unchanged(monkeypatch):
    monkeypatch.delenv("TUTOR_SAFETY_CLASSIFIER", raising=False)
    flags = screen_with_classifier("what is the discriminant of x^2 + 1?", FakeLLM())
    assert flags["classifier"]["allowed"] is True and flags["distress"] is False
