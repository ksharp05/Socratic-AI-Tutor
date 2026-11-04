"""The integrated signature walkthrough defaults to a synthetic model and bounds any live run."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_walkthrough():
    spec = importlib.util.spec_from_file_location('m2_walkthrough', ROOT/'scripts/m2/signature_live_walkthrough.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_walkthrough_is_synthetic_and_completes_the_api_flow(tmp_path):
    env = dict(os.environ, SOCRATES_SOURCE_WORKSPACE=str(tmp_path), PYTHONPATH=str(ROOT/'src'), TUTOR_LLM='stub')
    result = subprocess.run([sys.executable, str(ROOT/'scripts/m2/signature_live_walkthrough.py')], cwd=ROOT,
                            env=env, text=True, capture_output=True, timeout=120)
    assert result.returncode == 0, result.stderr
    runs = list((tmp_path/'Directions/git_delivery').glob('signature-walkthrough-*'))
    assert len(runs) == 1
    evidence = json.loads((runs[0]/'evidence.json').read_text(encoding='utf-8'))
    assert evidence['completed'] and evidence['mode'] == 'synthetic_model'
    assert evidence['provider_calls'] == 0 and evidence['synthetic_client_invocations'] == 2
    assert evidence['hint']['citations'][0]['passage_id'] == 'normalized:qe04'
    assert evidence['sse']['token_text_equals_reply'] and evidence['sse']['event_counts']['done'] == 1
    assert not evidence['wrong_attempt']['correct'] and evidence['correct_attempt']['accepted']
    assert evidence['student_trace_status'] == 403 and evidence['revoked_route'] == 'question_revoked'
    assert evidence['human_review'] is False and evidence['independent_evaluation'] is False
    sent = json.loads((runs[0]/'sent_messages.json').read_text(encoding='utf-8'))
    assert len(sent) == 2 and all(request['options'] == {'max_tokens': 240} for request in sent)
    assert 'synthetic-demo' not in json.dumps(sent)


def test_budget_refuses_extra_requests_before_sending():
    module = load_walkthrough()
    inner = SimpleNamespace(calls=0)
    def invoke(messages, **kwargs):
        inner.calls += 1
        return 'reply'
    inner.invoke = invoke
    client = module.BudgetedClient(inner, budget=2)
    client.invoke([('user', 'a')]); client.invoke([('user', 'b')])
    with pytest.raises(RuntimeError, match='no request was sent'):
        client.invoke([('user', 'c')])
    assert inner.calls == 2 and client.calls == 2 and client.refused == 1


def test_live_preflight_stops_before_creating_a_client():
    module = load_walkthrough()
    def no_client(*args):
        raise AssertionError('a client must not be created')
    settings = {'course_models': ['openai/gpt-4.1-mini']}
    with pytest.raises(RuntimeError, match='No configured live provider'):
        module.live_preflight(SimpleNamespace(enabled=False, model='openai/gpt-4.1-mini', _chat=no_client), settings)
    with pytest.raises(RuntimeError, match='not a course model'):
        module.live_preflight(SimpleNamespace(enabled=True, model='openai/gpt-4.1', _chat=no_client), settings)
