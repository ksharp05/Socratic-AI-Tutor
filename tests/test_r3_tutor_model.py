"""Tutor turns reach the model, with templates as the fallback. A fake replaces the model, so nothing leaves the machine."""
import json
import re

from tutor import prompts


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


def _probe(app):
    state = {"focus_misconception": "qe_m04", "messages": [{"content": "I divided both sides by x and lost a root"}],
             "session": {"session_id": "s-probe", "learner_id": "L-A"}, "learner": {"misconceptions": {}}}
    return app._diagnose(state)["draft"]["text"]


def test_the_model_writes_the_diagnosis_probe(app, monkeypatch):
    _fake_model(app, monkeypatch, _verdict("What must be true about x before you divide by it?"))
    assert "What must be true about x before you divide by it?" in _probe(app)


def test_a_probe_with_a_new_number_falls_back_to_the_catalogue(app, monkeypatch):
    _fake_model(app, monkeypatch, _verdict("Have you tried x = 0?"))
    text = _probe(app)
    assert "x = 0" not in text
    assert app.misconceptions["qe_m04"]["diagnostic_probe"] in text


def test_a_long_or_two_question_model_turn_keeps_its_template(app, monkeypatch):
    _fake_model(app, monkeypatch, "Why? And what next?")
    result = app.turn("s-model-shape", "L-A", "What does the discriminant tell us?")
    assert result["reply"].startswith("Let's think it through.")


def test_the_turn_shape_rule_ignores_citations(app):
    assert app._turn_shape_ok("What does that value measure? [normalized:qe04]")
    assert app._turn_shape_ok("What does that value measure [normalized:qe04]?")
    assert not app._turn_shape_ok("That value measures the roots.")
    assert not app._turn_shape_ok("word " * 61 + "?")


def test_a_diagnosed_wrong_attempt_asks_one_question(app, monkeypatch, published_set):
    real_call = app._call

    def call(state, node, role, server, tool, args):
        if tool == "diagnose_response":
            return {"candidates": [{"misconception_id": "qe_m04", "rule": "test"}]}
        return real_call(state, node, role, server, tool, args)

    monkeypatch.setattr(app, "_call", call)
    app.turn("s-one-question", "L-B", "practice")
    result = app.turn("s-one-question", "L-B", "x = 100")
    assert result["route"] == "grade"
    assert result["reply"].startswith("Not quite")
    assert result["reply"].split("(Study plan")[0].count("?") == 1


def test_a_tutor_turn_names_a_policy_style(app, monkeypatch):
    calls = _fake_model(app, monkeypatch, "What does that value measure?")
    app.turn("s-model-style", "L-A", "What does the discriminant tell us?")
    assert "reverse_question" in calls[0]["user"]
    assert "reverse_question" in prompts.STYLES


def test_a_made_up_citation_is_replaced_by_a_real_one(app, monkeypatch):
    _fake_model(app, monkeypatch, "What does that value measure? [passage_id: qe01]")
    result = app.turn("s-model-cite", "L-A", "What does the discriminant tell us?")
    assert "passage_id:" not in result["reply"]
    assert re.search(r"\[(normalized|ncert|exemplar):", result["reply"])


def test_a_probe_with_a_number_word_uses_the_catalogue(app, monkeypatch):
    _fake_model(app, monkeypatch, _verdict("Could the missing root be zero?"))
    assert app.misconceptions['qe_m04']['diagnostic_probe'] in _probe(app)


def test_probe_numeric_variants_fall_back_to_conceptual_questions(app):
    message='I have used these symbols in my working'
    for question in ['Could it be -5?', 'Could it be 3/4?', 'Could it be ½?',
                     'Could it be five?', 'Could it be one half?', 'Could it be ²?']:
        assert app._safe_question(question, message) is None
    assert app._safe_question('What must be true before that cancellation?', message)


def test_citation_cleanup_preserves_math_brackets(app):
    assert app._real_citations('Which values belong to [0, 1]?', []) == 'Which values belong to [0, 1]?'
    assert app._real_citations('What does [x + 1] represent?', []) == 'What does [x + 1] represent?'
    result=app._real_citations('Which values belong to [0, 1]? [passage_id: qe01]',
                               [{'passage_id':'normalized:qe04'}])
    assert '[0, 1]' in result and 'passage_id:' not in result


def test_math_brackets_do_not_replace_the_required_citation(app, monkeypatch):
    _fake_model(app, monkeypatch, 'Which values belong to [0, 1]?')
    state={'learner':{'mastery':{}},'messages':[{'content':'What is an interval?'}],
           'session':{'session_id':'s-interval','learner_id':'L-A'}}
    result=app._model_turn(state,[{'passage_id':'normalized:qe04','text':'A registered source.'}],
                           misconception='none',move='reverse_question')
    assert '[0, 1]' in result and '[normalized:qe04]' in result


def test_bracketed_prose_still_counts_toward_turn_length(app):
    assert not app._turn_shape_ok('What follows from ['+'word '*61+']?')
