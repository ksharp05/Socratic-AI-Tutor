"""Development integration: mounted beta and teacher API share a server, not authority or state."""
import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient
from ncert_pipeline.build import SCHEMA, insert_passage
from socrates_beta.knowledge import DatasetRegistry

ROOT = Path(__file__).resolve().parents[1]


def test_beta_mount_does_not_grant_teacher_authority(app, tmp_path, monkeypatch):
    from tutor_api.main import create_app

    index = tmp_path / 'fixture.sqlite'
    with sqlite3.connect(index) as conn:
        conn.executescript(SCHEMA)
        insert_passage(conn, {
            'id': 'fixture:math', 'source_id': 'fixture:page', 'book': 'fixture',
            'subject': 'Mathematics', 'title': 'Quadratics', 'page': 1, 'unit_file_index': 4,
            'kind': 'fixture', 'text': 'A quadratic equation has degree two.',
            'source_sha256': 'a' * 64, 'source_url': 'https://example.org/fixture',
            'human_review_status': 'pending',
        }, [10])
    data = tmp_path / 'data'
    DatasetRegistry(data).register('synthetic-fixture', index, title='Synthetic', activate=True)
    config = tmp_path / 'beta.json'
    config.write_text(json.dumps({'app_root': str(ROOT), 'data_directory': str(data)}), encoding='utf-8')
    monkeypatch.setenv('TUTOR_BETA_CONFIG', str(config))
    monkeypatch.setenv('TUTOR_BETA_WORKSPACE', str(ROOT))
    monkeypatch.delenv('TUTOR_BETA_LIVE', raising=False)

    api = create_app(tutor=app, tokens='tok-a:student:L-A,tok-t:teacher:T-001')
    with TestClient(api, base_url='http://localhost') as client:
        beta = client.get('/beta/api/health')
        assert beta.status_code == 200
        assert beta.json()['dataset'] == 'synthetic-fixture'
        assert beta.json()['language']['mode'] == 'offline'
        assert client.get('/health').json()['status'] == 'ok'
        # The beta's anonymous browser cookie and a student token never confer teacher access.
        assert client.get('/teacher/proposals').status_code == 401
        assert client.get('/teacher/proposals', headers={'Authorization': 'Bearer tok-a'}).status_code == 403
        assert client.get('/teacher/proposals', headers={'Authorization': 'Bearer tok-t'}).status_code == 200
