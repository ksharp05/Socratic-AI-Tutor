"""Mounted beta must serve only the exact teacher-approved question versions."""
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from ncert_pipeline.build import SCHEMA, insert_passage
from socrates_beta.knowledge import DatasetRegistry
from tutor.app import TutorApp
from tutor_api.main import create_app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def mounted(tmp_path, monkeypatch):
    index = tmp_path / 'fixture.sqlite'
    with sqlite3.connect(index) as conn:
        conn.executescript(SCHEMA)
        insert_passage(conn, {'id':'fixture:math', 'source_id':'fixture:page', 'book':'fixture',
            'subject':'Mathematics', 'title':'Quadratics', 'page':1, 'unit_file_index':4,
            'kind':'fixture', 'text':'A quadratic equation has degree two.',
            'source_sha256':'a'*64, 'source_url':'https://example.org/fixture',
            'human_review_status':'pending'}, [10])
    data = tmp_path / 'data'
    DatasetRegistry(data).register('synthetic-fixture', index, title='Synthetic', activate=True)
    config = tmp_path / 'beta.json'
    config.write_text(json.dumps({'app_root':str(tmp_path/'unused-standalone-checkout'), 'data_directory':str(data)}), encoding='utf-8')
    monkeypatch.setenv('TUTOR_BETA_CONFIG', str(config))
    monkeypatch.setenv('TUTOR_BETA_WORKSPACE', str(ROOT))
    monkeypatch.delenv('TUTOR_BETA_LIVE', raising=False)
    app = TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'), checkpoint_name=str(tmp_path/'checkpoint.db'))
    try:
        api = create_app(tutor=app, tokens='teacher-token:teacher:T-001,student-token:student:L-A')
        with TestClient(api, base_url='http://localhost') as client:
            yield client, app
    finally:
        app.close()


def session(client):
    response = client.post('/beta/api/sessions', headers={'X-Socrates-Request':'1'},
                           json={'grade':10,'subject':'Mathematics','book':'fixture','unit':4})
    assert response.status_code == 200, response.text
    return response.json()['id']


def approve(client):
    teacher = {'Authorization':'Bearer teacher-token'}
    proposal = client.post('/teacher/proposals', headers=teacher, json={'concept_id':'qe04'})
    assert proposal.status_code == 200
    body = proposal.json(); sid = body['set_id']
    approved = client.post(f'/teacher/proposals/{sid}/approve', headers=teacher)
    assert approved.status_code == 200 and approved.json()['status'] == 'published'
    return sid, [i['question_id'] for i in body['proposal']['payload']['items']]


def test_mounted_practice_requires_a_current_teacher_approved_set(mounted):
    client, _ = mounted
    learner = {'X-Socrates-Request':'1'}
    sid = session(client)
    response = client.post('/beta/api/practice', headers=learner, json={'session_id':sid, 'mode':'practice'})
    assert response.status_code == 400 and 'approved' in response.json()['detail'].lower()
    _, ids = approve(client)
    response = client.post('/beta/api/practice', headers=learner, json={'session_id':sid, 'mode':'practice'})
    assert response.status_code == 200, response.text
    assert response.json()['item']['id'] in ids


def test_teacher_edit_revokes_active_mounted_practice_before_grading(mounted, tmp_path):
    client, _ = mounted
    learner = {'X-Socrates-Request':'1'}
    sid = session(client)
    set_id, ids = approve(client)
    start = client.post('/beta/api/practice', headers=learner, json={'session_id':sid,'mode':'practice'}).json()
    aid = start['id']
    response = client.post(f'/teacher/proposals/{set_id}/edit', headers={'Authorization':'Bearer teacher-token'},
                           json={'question_ids':ids[:-1]})
    assert response.status_code == 200 and response.json()['status'] == 'pending'
    response = client.post(f'/beta/api/practice/{aid}/submit', headers=learner,
                           json={'answer':'x = 1','request_id':'submit-0001'})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['status'] == 'question_revoked'
    assert result['assessment']['complete'] and result['assessment']['item'] is None
    assert 'summary' not in result['assessment']
    assert client.get(f'/beta/api/sessions/{sid}').json()['assessment'] is None
    with sqlite3.connect(tmp_path/'data/beta.sqlite') as db:
        assert db.execute("SELECT COUNT(*) FROM observations WHERE kind='checked_answer'").fetchone()[0] == 0


def test_revoked_answer_retry_cannot_replay_a_stale_question(mounted):
    client, _ = mounted
    learner = {'X-Socrates-Request':'1'}
    sid = session(client)
    set_id, ids = approve(client)
    start = client.post('/beta/api/practice', headers=learner, json={'session_id':sid,'mode':'practice'}).json()
    aid = start['id']
    payload = {'answer':'x = 1','request_id':'retry-00001'}
    first = client.post(f'/beta/api/practice/{aid}/submit', headers=learner, json=payload)
    assert first.status_code == 200 and first.json()['status'] == 'incorrect'
    client.post(f'/teacher/proposals/{set_id}/edit', headers={'Authorization':'Bearer teacher-token'},
                json={'question_ids':ids[:-1]})
    replay = client.post(f'/beta/api/practice/{aid}/submit', headers=learner, json=payload)
    assert replay.status_code == 200 and replay.json()['status'] == 'question_revoked'
    assert replay.json()['assessment']['item'] is None


def test_mounted_quiz_is_cancelled_without_grading_after_an_edit(mounted, tmp_path):
    client, _ = mounted
    learner = {'X-Socrates-Request':'1'}
    sid = session(client)
    set_id, ids = approve(client)
    start = client.post('/beta/api/practice', headers=learner, json={'session_id':sid,'mode':'quiz'}).json()
    assert start['total'] >= 2
    aid = start['id']
    first = client.post(f'/beta/api/practice/{aid}/submit', headers=learner,
                        json={'answer':'x = 1','request_id':'quiz-00001'})
    assert first.status_code == 200 and first.json()['status'] == 'recorded'
    with sqlite3.connect(tmp_path/'data/beta.sqlite') as db:
        count = db.execute("SELECT COUNT(*) FROM observations WHERE kind='checked_answer'").fetchone()[0]
    client.post(f'/teacher/proposals/{set_id}/edit', headers={'Authorization':'Bearer teacher-token'},
                json={'question_ids':ids[:-1]})
    result = client.post(f'/beta/api/practice/{aid}/submit', headers=learner,
                         json={'answer':'x = 1','request_id':'quiz-00002'}).json()
    assert result['status'] == 'question_revoked' and result['assessment']['item'] is None
    assert 'summary' not in result['assessment']
    with sqlite3.connect(tmp_path/'data/beta.sqlite') as db:
        assert db.execute("SELECT COUNT(*) FROM observations WHERE kind='checked_answer'").fetchone()[0] == count


def test_mounted_practice_fails_closed_if_approval_service_is_unavailable(mounted, monkeypatch):
    client, app = mounted
    sid = session(client)
    approve(client)
    original = app.bus.call
    def fail(ctx, role, server, tool, args):
        if server == 'question-bank' and tool == 'list_published':
            raise RuntimeError('synthetic outage')
        return original(ctx, role, server, tool, args)
    monkeypatch.setattr(app.bus, 'call', fail)
    response = client.post('/beta/api/practice', headers={'X-Socrates-Request':'1'},
                           json={'session_id':sid,'mode':'practice'})
    assert response.status_code == 503
    assert 'unavailable' in response.json()['detail'].lower()


def test_mounted_beta_refuses_public_items_that_differ_from_approved_payload(mounted):
    client, _ = mounted
    sid = session(client)
    _, ids = approve(client)
    beta = next(route.app for route in client.app.routes if getattr(route, 'name', None) == 'socrates-beta')
    for qid in ids:
        beta.state.services['maths'].items[qid]['prompt'] += ' [different payload]'
    response = client.post('/beta/api/practice', headers={'X-Socrates-Request':'1'},
                           json={'session_id':sid,'mode':'practice'})
    assert response.status_code == 400 and 'approved' in response.json()['detail'].lower()


def test_teacher_edit_waits_for_inflight_mounted_grading(mounted, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from threading import Event

    client, _ = mounted
    learner = {'X-Socrates-Request':'1'}
    sid = session(client)
    set_id, ids = approve(client)
    start = client.post('/beta/api/practice', headers=learner, json={'session_id':sid,'mode':'practice'}).json()
    beta = next(route.app for route in client.app.routes if getattr(route, 'name', None) == 'socrates-beta')
    maths = beta.state.services['maths']
    original = maths.grade
    entered, release, editing = Event(), Event(), Event()
    def pause_grade(qid, text):
        entered.set()
        if not release.wait(10): raise RuntimeError('test did not release grading')
        return original(qid, text)
    monkeypatch.setattr(maths, 'grade', pause_grade)
    def submit():
        return client.post(f"/beta/api/practice/{start['id']}/submit", headers=learner,
                           json={'answer':'x = 1','request_id':'concurrent-0001'})
    def edit():
        editing.set()
        return client.post(f'/teacher/proposals/{set_id}/edit', headers={'Authorization':'Bearer teacher-token'},
                           json={'question_ids':ids[:-1]})
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            attempt = pool.submit(submit)
            assert entered.wait(10)
            update = pool.submit(edit)
            assert editing.wait(10)
            try:
                with pytest.raises(TimeoutError): update.result(timeout=.4)
            finally:
                release.set()
            assert attempt.result(timeout=10).status_code == 200
            assert update.result(timeout=10).json()['status'] == 'pending'
        response = client.post(f"/beta/api/practice/{start['id']}/hint", headers=learner, json={})
        assert response.status_code == 200 and response.json()['status'] == 'question_revoked'
    finally:
        release.set()


def test_mounted_health_reports_approval_policy(mounted):
    client, _ = mounted
    assert client.get('/beta/api/health').json()['assessment_policy'] == 'teacher_published'
    assert client.get('/beta/api/bootstrap').json()['assessment_policy'] == 'teacher_published'


def test_tutor_close_releases_database_connections_and_tool_thread(tmp_path):
    import sqlite3
    from tutor.app import TutorApp

    app = TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoint.db'))
    app.close()
    with pytest.raises(sqlite3.ProgrammingError): app.conn.execute('SELECT 1')
    with pytest.raises(sqlite3.ProgrammingError): app.checkpointer.conn.execute('SELECT 1')
    assert not app.bus._thread.is_alive()
    app.close()  # Closing twice is safe.


def test_unavailable_tutor_provider_is_reported_without_exposing_details(mounted):
    client, _ = mounted
    sid = session(client)
    beta = next(route.app for route in client.app.routes if getattr(route, 'name', None) == 'socrates-beta')
    def unavailable(): raise RuntimeError('internal provider detail')
    beta.state.services['assessment'].tutor_provider = unavailable
    response = client.post('/beta/api/practice', headers={'X-Socrates-Request':'1'},
                           json={'session_id':sid,'mode':'practice'})
    assert response.status_code == 503
    assert 'unavailable' in response.json()['detail'].lower()
    assert 'internal provider detail' not in response.text
