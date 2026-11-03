"""The quadratic probe defaults to an isolated fake model and never needs credentials."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_default_probe_is_synthetic_and_does_not_call_a_provider(tmp_path):
    env = dict(os.environ, SOCRATES_SOURCE_WORKSPACE=str(tmp_path), PYTHONPATH=str(ROOT/'src'), TUTOR_LLM='stub')
    result = subprocess.run([sys.executable, str(ROOT/'scripts/m2/quadratic_probe.py')], cwd=ROOT,
                            env=env, text=True, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr
    reports = list((tmp_path/'Directions/m2_candidate_runs').glob('*/evidence.json'))
    assert len(reports) == 1
    evidence = json.loads(reports[0].read_text(encoding='utf-8'))
    assert evidence['mode'] == 'synthetic_model' and evidence['provider_calls'] == 0
    assert evidence['generation_attempts'] == 1 and evidence['generated_accepted']
    assert evidence['display_screen_passed'] and evidence['source_ids']
    assert evidence['teacher_approved'] is False and evidence['independent'] is False


def test_probe_disables_underlying_provider_retries_without_network():
    import importlib.util
    from types import SimpleNamespace
    spec = importlib.util.spec_from_file_location('m2_probe', ROOT/'scripts/m2/quadratic_probe.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = SimpleNamespace(max_retries=2, timeout=60)
    client = SimpleNamespace(root_client=root, client=SimpleNamespace(_client=root), max_retries=2,
                             request_timeout=60, max_tokens=None)
    module.configure_single_attempt(client)
    assert client.max_retries == root.max_retries == 0
    assert client.request_timeout == root.timeout == 22 and client.max_tokens == 240
    with __import__('pytest').raises(RuntimeError, match='cannot be verified'):
        module.configure_single_attempt(SimpleNamespace(root_client=None))
