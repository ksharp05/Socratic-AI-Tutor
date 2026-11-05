"""Run only the twelve explicitly approved remaining E3 sessions, with durable deduplication."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tomllib

CODE = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE', Path.cwd())).resolve()
sys.path.insert(0, str(CODE / 'src'))
os.environ.update(TUTOR_LLM='auto', TUTOR_BETA_LIVE='0', TUTOR_BETA_CONFIG='', TUTOR_REQUIRE_BETA='0', LLM_MODEL='openai/gpt-4.1-mini')
from filelock import FileLock
from tutor_eval import harness
from tutor_eval.provider_budget import ProviderBudget


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def preflight(root, index, config):
    cfg = tomllib.loads(config.read_text(encoding='utf-8'))
    plan = load(root / 'E3_BUDGET_TRANCHE.json')
    before = Path(index['jobs']['c2']['run'])
    tranche = Path(index['jobs']['e3_after_budget_tranche12']['run'])
    base_rows, done_rows = rows(before / 'sessions.jsonl'), rows(tranche / 'sessions.jsonl')
    keys = lambda sessions: {(s['student'], s['seed']) for s in sessions}
    pending = {(student, seed) for student in cfg['data']['only_students'] for seed in cfg['run']['seeds']}
    assert len(base_rows) == 48 and len(done_rows) == 36 and len(pending) == 12
    assert pending == keys(base_rows) - keys(done_rows) and not pending & keys(done_rows)
    assert set(cfg['data']['only_students']) == set(plan['pending_original_cards'])
    original = tomllib.loads((CODE / 'eval/configs/m3_live_e3_after.toml').read_text(encoding='utf-8'))
    for key in ['arm', 'contextual', 'defences', 'llm', 'voice', 'seeds', 'max_turns', 'turn_timeout_s', 'playbook']:
        assert cfg['run'][key] == original['run'][key], key
    allowed = {'src/tutor_eval/harness.py', 'src/tutor_eval/provider_budget.py'}
    names = subprocess.check_output(['git', '-C', str(CODE), 'ls-tree', '-r', '--name-only', '12d541e',
        'src/tutor', 'src/tutor_eval', 'src/v02_integration', 'src/tutor_api/traces.py'], text=True).splitlines()
    for name in names:
        ref = 'dffdde2' if name in allowed else '12d541e'
        committed = subprocess.check_output(['git', '-C', str(CODE), 'show', ref + ':' + name])
        assert (CODE / name).read_bytes().replace(b'\r\n', b'\n') == committed.replace(b'\r\n', b'\n'), name
    manifest = load(tranche / 'manifest.json')
    for name, digest in manifest['data'].items():
        path = Path(name)
        assert sha(path if path.is_absolute() else CODE / path) == digest, name
    for name, digest in manifest['fixture_input_sha256'].items():
        assert sha(CODE / name) == digest, name
    assert sha(CODE / cfg['run']['playbook']) == manifest['playbook_sha256']
    assert subprocess.check_output(['git', '-C', str(CODE), 'branch', '--show-current'], text=True).strip() == 'Beta'
    assert not subprocess.check_output(['git', '-C', str(CODE), 'status', '--porcelain'], text=True).strip()
    # No request is made by constructing the approved chained wallet.
    wallet = ProviderBudget(SOURCE / 'Directions/m3_runs/provider_budget_extension_e3.json',
        max_calls=50, max_usd=.03, prior_calls=1000,
        approval_receipt=root / 'E3_EXTENSION_APPROVAL.json')
    return cfg, pending, wallet


def main():
    root = SOURCE / 'Directions/m3_runs/v2/live'
    config = CODE / 'eval/configs/m3_live_e3_remaining4.toml'
    folder = root / 'e3_after_remaining4'
    key = 'e3_after_remaining4'
    with FileLock(str(SOURCE / 'Directions/m3_runs/matrix.lock'), timeout=1):
        index_path = root / 'INDEX.json'
        index = load(index_path)
        cfg, pending, wallet = preflight(root, index, config)
        if key in index['jobs'] or (folder.exists() and any(folder.iterdir())) or wallet.snapshot()['provider_attempts']:
            raise RuntimeError('Existing remaining-E3 evidence must be inspected; no automatic retry or duplication')
        from tutor.llm import api_key
        if not api_key()[0]:
            raise RuntimeError('Provider not configured; refusing a silently offline replacement')
        index['jobs'][key] = {'status': 'running', 'started': time.time(), 'config_sha256': sha(config),
            'planned_sessions': 12, 'approval_receipt_sha256': sha(root / 'E3_EXTENSION_APPROVAL.json')}
        save(index_path, index)
        print('Approved E3 completion: 12 sessions, expected 36 attempts, hard 50 attempts / USD 0.03.', flush=True)
        run = harness.run(config, out_dir=folder)
        manifest = load(run / 'manifest.json')
        actual = rows(run / 'sessions.jsonl')
        actual_keys = [(s['student'], s['seed']) for s in actual]
        assert len(actual_keys) == len(set(actual_keys)) == 12 and set(actual_keys) == pending
        assert 0 < wallet.snapshot()['provider_attempts'] <= 50
        assert wallet.snapshot()['accounted_usd'] <= .03
        index['jobs'][key] = {'status': 'completed', 'run': str(run), 'config_sha256': sha(config),
            'gate': manifest['gate'], 'approval_receipt_sha256': sha(root / 'E3_EXTENSION_APPROVAL.json'),
            'provider_budget': wallet.snapshot()}
        save(index_path, index)
        print(json.dumps({'run': str(run), 'sessions': len(actual), 'gate': manifest['gate'], 'budget': wallet.snapshot()}, indent=2), flush=True)


if __name__ == '__main__':
    main()
