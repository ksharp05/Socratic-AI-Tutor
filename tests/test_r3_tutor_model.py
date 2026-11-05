"""Tutor turns reach the model, with templates as the fallback. A fake replaces the model, so nothing leaves the machine."""
import json

def _fake_model(app, monkeypatch, reply):
    calls = []

    def complete(*, session_id, node, role, system, user, max_tokens=None):
        calls.append({"node": node, "user": user})
        return reply

    monkeypatch.setattr(app.llm, "enabled", True)
    monkeypatch.setattr(app.llm, "complete", complete)
    return calls


def test_a_general_question_reaches_the_model_with_the_students_words(app, monkeypatch):
    calls = _fake_model(app, monkeypatch, "What does that value measure?")
    result = app.turn("s-model-general", "L-A", "What does the discriminant tell us?")
    assert result["route"] == "tutor"
    assert [call["node"] for call in calls] == ["tutor"]
    assert "What does the discriminant tell us?" in calls[0]["user"]
    assert result["reply"].startswith("What does that value measure?")
    assert "[" in result["reply"]  # code adds the citation when the model leaves it out


def test_a_general_question_keeps_its_template_when_the_model_fails(app, monkeypatch):
    calls = _fake_model(app, monkeypatch, None)
    result = app.turn("s-model-down", "L-A", "What does the discriminant tell us?")
    assert len(calls) == 1
    assert result["reply"].startswith("Let's think it through.")


def _verdict(question):
    return json.dumps({"misconception_id": "qe_m04", "confidence": 0.9, "evidence": "divided", "question": question})


def test_the_model_writes_the_diagnosis_probe(app, monkeypatch):
    _fake_model(app, monkeypatch, _verdict("What must be true about x before you divide by it?"))
    result = app.turn("s-model-probe", "L-B", "I divided both sides by x and lost a root")
    assert result["route"] == "diagnose"
    assert "What must be true about x before you divide by it?" in result["reply"]


def test_a_probe_with_a_new_number_falls_back_to_the_catalogue(app, monkeypatch):
    _fake_model(app, monkeypatch, _verdict("Have you tried x = 0?"))
    result = app.turn("s-model-probe-leak", "L-B", "I divided both sides by x and lost a root")
    assert result["route"] == "diagnose"
    assert "x = 0" not in result["reply"]
    assert app.misconceptions["qe_m04"]["diagnostic_probe"] in result["reply"]
