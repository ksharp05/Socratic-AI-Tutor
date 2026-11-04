"""Synthetic same-server graph journey through the browser's authenticated API."""
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from ncert_pipeline.build import SCHEMA, insert_passage
from socrates_beta.knowledge import DatasetRegistry
from tutor.app import TutorApp
from tutor.seed import seed_learner
from tutor_api.main import create_app

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def connected(tmp_path,monkeypatch):
    index=tmp_path/'fixture.sqlite'
    with sqlite3.connect(index) as conn:
        conn.executescript(SCHEMA)
        insert_passage(conn,{'id':'fixture:math','source_id':'fixture:page','book':'jemh1',
            'subject':'Mathematics','title':'Quadratics','page':1,'unit_file_index':4,
            'kind':'fixture','text':'A quadratic equation has degree two.',
            'source_sha256':'a'*64,'source_url':'https://example.org/fixture',
            'human_review_status':'pending'},[10])
        conn.execute('CREATE TABLE concepts(id TEXT PRIMARY KEY,title TEXT,description TEXT,prerequisites TEXT,unit INTEGER,passage_ids TEXT)')
        conn.execute('INSERT INTO concepts VALUES (?,?,?,?,?,?)',('qe04','Factoring','Synthetic concept','[]',4,'["fixture:math"]'))
    data=tmp_path/'data'; DatasetRegistry(data).register('synthetic',index,title='Synthetic',activate=True)
    config=tmp_path/'beta.json';config.write_text(json.dumps({'app_root':str(ROOT),'data_directory':str(data)}),encoding='utf-8')
    monkeypatch.setenv('TUTOR_BETA_CONFIG',str(config));monkeypatch.setenv('TUTOR_BETA_WORKSPACE',str(ROOT))
    monkeypatch.delenv('TUTOR_BETA_LIVE',raising=False)
    tutor=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    seed_learner(tutor.conn,'L-A',{'alias':'Synthetic A'});seed_learner(tutor.conn,'L-B',{'alias':'Synthetic B'})
    try:
        api=create_app(tutor=tutor,tokens='a:student:L-A,b:student:L-B,t:teacher:T-1')
        with TestClient(api,base_url='http://localhost') as client:yield client,tutor
    finally:tutor.close()


def test_same_server_connected_quiz_updates_only_authenticated_learner(connected):
    client,_=connected
    a={'Authorization':'Bearer a'};b={'Authorization':'Bearer b'};teacher={'Authorization':'Bearer t'}
    assert client.get('/beta/api/bootstrap').json()['graph_journey'] is True
    assert client.get('/beta/').status_code==200
    assert client.get('/me',headers=a).json()=={'role':'student','id':'L-A'}
    assert client.get('/me',headers=teacher).json()['role']=='teacher'
    assert client.get('/chat/active',headers=teacher).status_code==403
    assert client.get('/chat/active').status_code==401
    assert client.post('/chat',json={'text':'hello'}).status_code==401
    assert client.get('/learners/L-B',headers=a).status_code==403
    assert client.post('/teacher/proposals',headers=a,json={'concept_id':'qe04'}).status_code==403
    proposal=client.post('/teacher/proposals',headers=teacher,json={'concept_id':'qe04'}).json()
    assert client.post('/teacher/proposals/'+proposal['set_id']+'/approve',headers=teacher).json()['status']=='published'
    sid='web-synthetic-learner-a'
    first=client.post('/chat',headers=a,json={'session_id':sid,'text':'hello','mode':'practice'}).json()
    other=client.post('/chat',headers=b,json={'session_id':'web-synthetic-learner-b','text':'hello','mode':'practice'}).json()
    assert first['quiz_active'] is False and other['quiz_active'] is False
    old_version=first['plan']['version'];other_plan=other['plan']
    started=client.post('/chat',headers=a,json={'session_id':sid,'text':'start a quiz','mode':'quiz'}).json()
    assert started['route']=='quiz_start' and started['quiz_active'] is True
    invalid=client.post('/chat',headers=a,json={'session_id':sid,'text':'banana','mode':'quiz'}).json()
    assert invalid['quiz_active'] is True and 'could not read' in invalid['reply'].lower()
    assert client.get('/chat/'+sid+'/history',headers=b).status_code==403
    for _ in range(3):
        final=client.post('/chat',headers=a,json={'session_id':sid,'text':'no real roots','mode':'quiz'}).json()
    assert final['quiz_active'] is False and final['plan']['version']>old_version
    assert final['plan']['replan_reason'].startswith('after quiz:')
    history=client.get('/chat/'+sid+'/history',headers=a).json()
    assert history['quiz_active'] is False and history['interrupted'] is False
    assert client.get('/learners/L-B',headers=b).json()['plan']==other_plan
    assert client.get('/chat/'+sid+'/history').status_code==401


def test_same_server_edit_revokes_connected_quiz(connected):
    client,_=connected;a={'Authorization':'Bearer a'};teacher={'Authorization':'Bearer t'}
    proposal=client.post('/teacher/proposals',headers=teacher,json={'concept_id':'qe04'}).json()
    set_id=proposal['set_id'];items=proposal['proposal']['payload']['items']
    assert client.post('/teacher/proposals/'+set_id+'/approve',headers=teacher).json()['status']=='published'
    sid='web-synthetic-revocation'
    quiz=client.post('/chat',headers=a,json={'session_id':sid,'text':'start a quiz','mode':'quiz'}).json()
    assert quiz['quiz_active'] is True
    edited=client.post('/teacher/proposals/'+set_id+'/edit',headers=teacher,json={'question_ids':[i['question_id'] for i in items[:-1]]})
    assert edited.status_code==200 and edited.json()['status']=='pending'
    reply=client.post('/chat',headers=a,json={'session_id':sid,'text':'no real roots','mode':'quiz'}).json()
    assert reply['route']=='question_revoked' and reply['quiz_active'] is False
    assert 'no longer available' in reply['reply']


def test_connected_quiz_cannot_be_bypassed_by_another_graph_session(connected):
    client,_=connected;a={'Authorization':'Bearer a'};b={'Authorization':'Bearer b'};teacher={'Authorization':'Bearer t'}
    proposal=client.post('/teacher/proposals',headers=teacher,json={'concept_id':'qe04'}).json()
    assert client.post('/teacher/proposals/'+proposal['set_id']+'/approve',headers=teacher).json()['status']=='published'
    first=client.post('/chat',headers=a,json={'session_id':'quiz-a','text':'start a quiz','mode':'quiz'}).json()
    assert first['quiz_active'] is True
    other=client.post('/chat',headers=a,json={'session_id':'practice-a','text':'practice','mode':'practice'})
    assert other.status_code==409
    assert client.post('/chat',headers=b,json={'session_id':'practice-b','text':'practice','mode':'practice'}).status_code==200
    for _ in range(3):
        client.post('/chat',headers=a,json={'session_id':'quiz-a','text':'no real roots','mode':'quiz'})
    assert client.post('/chat',headers=a,json={'session_id':'practice-a','text':'practice','mode':'practice'}).status_code==200


def test_active_quiz_can_be_recovered_and_left_without_a_score(connected):
    client,tutor=connected;a={'Authorization':'Bearer a'};b={'Authorization':'Bearer b'};teacher={'Authorization':'Bearer t'}
    proposal=client.post('/teacher/proposals',headers=teacher,json={'concept_id':'qe04'}).json()
    client.post('/teacher/proposals/'+proposal['set_id']+'/approve',headers=teacher)
    sid='quiz-recover-leave'
    client.post('/chat',headers=a,json={'session_id':sid,'text':'start a quiz','mode':'quiz'})
    active=client.get('/chat/active',headers=a).json()
    assert active=={'session_id':sid,'quiz_active':True,'interrupted':False}
    assert client.get('/chat/active',headers=b).json()['session_id'] is None
    assert client.post('/chat/leave',headers=b,json={'session_id':sid}).status_code==403
    urgent=client.post('/chat',headers=a,json={'session_id':'different','text':'I want to die','mode':'practice'}).json()
    assert urgent['route']=='handoff' and urgent['persistence']=='not_saved_urgent'
    assert client.get('/chat/active',headers=a).json()['session_id']==sid
    result=client.post('/chat/leave',headers=a,json={'session_id':sid}).json()
    assert result['ended'] is True and 'No score' in result['reply']
    assert tutor.conn.execute('SELECT COUNT(*) FROM applied_quizzes').fetchone()[0]==0
    assert tutor.conn.execute('SELECT COUNT(*) FROM mastery').fetchone()[0]==0
    assert client.get('/chat/active',headers=a).json()['session_id'] is None
    assert client.post('/chat',headers=a,json={'session_id':'fresh','text':'practice'}).status_code==200


def test_quiz_reservation_survives_another_api_instance(connected,tmp_path):
    client,_=connected;a={'Authorization':'Bearer a'};teacher={'Authorization':'Bearer t'}
    proposal=client.post('/teacher/proposals',headers=teacher,json={'concept_id':'qe04'}).json()
    client.post('/teacher/proposals/'+proposal['set_id']+'/approve',headers=teacher)
    client.post('/chat',headers=a,json={'session_id':'quiz-persisted','text':'start a quiz','mode':'quiz'})
    other=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        with TestClient(create_app(tutor=other,tokens='a:student:L-A,b:student:L-B,t:teacher:T-1'),base_url='http://localhost') as second:
            assert second.get('/chat/active',headers=a).json()['session_id']=='quiz-persisted'
            assert second.post('/chat',headers=a,json={'session_id':'another','text':'practice'}).status_code==409
            assert second.post('/chat/leave',headers=a,json={'session_id':'quiz-persisted'}).json()['ended'] is True
        assert client.get('/chat/active',headers=a).json()['session_id'] is None
    finally:other.close()


def test_interrupted_quiz_requires_recovery_before_another_turn(connected,monkeypatch):
    client,tutor=connected;a={'Authorization':'Bearer a'};teacher={'Authorization':'Bearer t'}
    proposal=client.post('/teacher/proposals',headers=teacher,json={'concept_id':'qe04'}).json()
    client.post('/teacher/proposals/'+proposal['set_id']+'/approve',headers=teacher)
    sid='quiz-interrupted-api'
    client.post('/chat',headers=a,json={'session_id':sid,'text':'start a quiz','mode':'quiz'})
    for _ in range(2):client.post('/chat',headers=a,json={'session_id':sid,'text':'no real roots','mode':'quiz'})
    original=tutor._call;crashed=False
    def fail_after_apply(state,node,role,server,tool,args):
        nonlocal crashed
        result=original(state,node,role,server,tool,args)
        if not crashed and node=='update_memory' and tool=='apply_quiz':
            crashed=True;raise RuntimeError('synthetic crash after quiz transaction')
        return result
    monkeypatch.setattr(tutor,'_call',fail_after_apply)
    with pytest.raises(RuntimeError,match='synthetic crash'):
        client.post('/chat',headers=a,json={'session_id':sid,'text':'no real roots','mode':'quiz'})
    assert client.get('/chat/active',headers=a).json()['interrupted'] is True
    assert client.post('/chat',headers=a,json={'session_id':sid,'text':'no real roots','mode':'quiz'}).status_code==409
    assert client.post('/chat/leave',headers=a,json={'session_id':sid}).status_code==409
    events=tutor.conn.execute('SELECT COUNT(*) FROM learner_events').fetchone()[0]
    recovered=client.post('/chat/resume',headers=a,json={'session_id':sid}).json()
    assert recovered['resumed'] is True
    assert tutor.conn.execute('SELECT COUNT(*) FROM learner_events').fetchone()[0]==events
    assert client.get('/chat/active',headers=a).json()['session_id'] is None


def test_concurrent_quiz_starts_on_separate_connections_admit_only_one(connected,tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    client,_=connected;a={'Authorization':'Bearer a'};teacher={'Authorization':'Bearer t'}
    proposal=client.post('/teacher/proposals',headers=teacher,json={'concept_id':'qe04'}).json()
    client.post('/teacher/proposals/'+proposal['set_id']+'/approve',headers=teacher)
    second_tutor=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        second_api=create_app(tutor=second_tutor,tokens='a:student:L-A,b:student:L-B,t:teacher:T-1')
        with TestClient(second_api,base_url='http://localhost') as second:
            barrier=Barrier(2)
            def start(pair):
                selected,sid=pair;barrier.wait(timeout=5)
                return selected.post('/chat',headers=a,json={'session_id':sid,'text':'start a quiz','mode':'quiz'}).status_code
            with ThreadPoolExecutor(max_workers=2) as pool:
                statuses=list(pool.map(start,[(client,'race-one'),(second,'race-two')]))
            assert sorted(statuses)==[200,409]
            active=client.get('/chat/active',headers=a).json()
            assert active['session_id'] in {'race-one','race-two'} and active['quiz_active'] is True
    finally:second_tutor.close()


def test_failed_turn_before_checkpoint_does_not_orphan_reservation(connected,monkeypatch):
    client,tutor=connected;a={'Authorization':'Bearer a'}
    original=tutor.turn
    def fail_before_graph(*args,**kwargs):raise RuntimeError('synthetic early failure')
    monkeypatch.setattr(tutor,'turn',fail_before_graph)
    with pytest.raises(RuntimeError,match='synthetic early failure'):
        client.post('/chat',headers=a,json={'session_id':'failed-early','text':'hello'})
    assert client.get('/chat/active',headers=a).json()['session_id'] is None
    monkeypatch.setattr(tutor,'turn',original)
    assert client.post('/chat',headers=a,json={'session_id':'later-session','text':'hello'}).status_code==200
