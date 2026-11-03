"""Portable prepared-index startup tests. Fixtures contain no textbook or held-out data."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys

from ncert_pipeline.build import SCHEMA, insert_passage

CODE_ROOT = Path(__file__).resolve().parents[1]


def prepared_index(path):
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        passage = {
            'id': 'fixture:quadratic', 'source_id': 'fixture:page', 'book': 'fixture',
            'subject': 'Mathematics', 'title': 'Quadratic structure', 'page': 1,
            'unit_file_index': 4, 'kind': 'fixture',
            'text': 'A quadratic expression has a squared term with a nonzero coefficient.',
            'source_sha256': 'a' * 64, 'source_url': 'https://example.org/fixture',
            'human_review_status': 'pending',
        }
        insert_passage(conn, passage, [10])
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cli(workspace, config, *args):
    env = dict(os.environ, SOCRATES_SOURCE_WORKSPACE=str(workspace), PYTHONPATH=str(CODE_ROOT / 'src'))
    return subprocess.run([sys.executable, '-m', 'socrates_beta', '--config', str(config), *args],
                          cwd=CODE_ROOT, env=env, capture_output=True, text=True, timeout=30)


def test_fresh_workspace_registers_and_loads_a_pinned_index(tmp_path):
    workspace = tmp_path / 'clean-workspace'
    workspace.mkdir()
    index = tmp_path / 'authorized-prepared.sqlite'
    digest = prepared_index(index)
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({'app_root': str(CODE_ROOT), 'data_directory': 'Directions/beta_data'}))

    registered = run_cli(workspace, config, 'register-index', '--file', str(index), '--id',
                         'fixture-v1', '--title', 'Synthetic fixture', '--activate', '--expected-sha256', digest)
    assert registered.returncode == 0, registered.stderr
    assert json.loads(registered.stdout)['sha256'] == digest
    assert not (workspace / 'Directions/book_pipeline/v0_1').exists()

    listed = run_cli(workspace, config, 'datasets')
    assert listed.returncode == 0, listed.stderr
    data = json.loads(listed.stdout)
    assert data['active'] == 'fixture-v1'
    assert data['datasets'][0]['passages'] == 1

    # A changed index must fail before the command can report a usable dataset.
    with sqlite3.connect(index) as conn:
        conn.execute("UPDATE passages SET text = 'modified' WHERE id = 'fixture:quadratic'")
    changed = run_cli(workspace, config, 'datasets')
    assert changed.returncode != 0
    assert 'changed after registration' in changed.stderr


def test_wrong_expected_hash_cannot_register_an_index(tmp_path):
    workspace = tmp_path / 'clean-workspace'
    workspace.mkdir()
    index = tmp_path / 'fixture.sqlite'
    prepared_index(index)
    config = tmp_path / 'config.json'
    config.write_text(json.dumps({'app_root': str(CODE_ROOT), 'data_directory': 'Directions/beta_data'}))
    result = run_cli(workspace, config, 'register-index', '--file', str(index), '--id', 'fixture-v1',
                     '--title', 'Synthetic fixture', '--activate', '--expected-sha256', '0' * 64)
    assert result.returncode != 0
    assert 'does not match' in result.stderr
    registry = json.loads((workspace / 'Directions/beta_data/registry.json').read_text())
    assert registry['active'] is None
    assert registry['datasets'] == {}
