"""Synthetic graph deletion, authorization, isolation and interruption recovery."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tutor import store
from tutor.app import TutorApp
from tutor.learner_privacy import LEARNER_TABLES
from tutor.seed import seed_learner
from tutor.toolbus import CallContext, ToolCallError
from tutor_api.main import create_app

TOKENS = 'a:student:synthetic-a,b:student:synthetic-b,t:teacher:synthetic-teacher'
A = {'Authorization': 'Bearer a'}
B = {'Authorization': 'Bearer b'}
T = {'Authorization': 'Bearer t'}


def make_tutor(tmp_path, checkpoint='checkpoints.db'):
    return TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'), checkpoint_name=str(tmp_path/checkpoint))


@pytest.fixture
def tutor(tmp_path):
    app = make_tutor(tmp_path)
    seed_learner(app.conn, 'synthetic-a', {'alias':'Synthetic A','mastery':{'qe04':0.2}})
    seed_learner(app.conn, 'synthetic-b', {'alias':'Synthetic B','mastery':{'qe04':0.7}})
    try:
        yield app
    finally:
        app.close()


def seed_history(app):
    prop = app.propose_set('qe04')
    app.decide(prop['set_id'], 'approve', 'synthetic-teacher')
    app.turn('a-first', 'synthetic-a', 'practice')
    app.turn('a-first', 'synthetic-a', 'I need a hint')
    app.turn('a-second', 'synthetic-a', 'hello')
    app.turn('b-first', 'synthetic-b', 'hello')
    # Simulate history written before the new session index existed.
    app.conn.execute("DELETE FROM learner_session_index WHERE session_id='a-first'")
    for table, values in (
        ('misconceptions', ('synthetic-a','qe_m04','suspected',1,1.0)),
        ('explanations', ('synthetic-a','qe_m04','counterexample',1,0)),
        ('topic_plans', ('synthetic-a','trigonometry','{}',1,1.0)),
        ('applied_quizzes', ('synthetic-quiz','synthetic-a','synthetic-digest',1.0)),
        ('graph_session_leases', ('synthetic-a','a-first')),
    ):
        app.conn.execute(f"INSERT OR REPLACE INTO {table} VALUES ({','.join('?' for _ in values)})",values)
    for i in range(3):
        store.record_stuck_session(app.conn,'synthetic-a','qe04',f'stuck-{i}')
    app.conn.execute("INSERT INTO learner_events (learner_id,kind,payload,ts) VALUES (?,?,?,?)",
                     ('synthetic-a','synthetic','{}',1.0))
    return prop


def learner_rows(app, learner):
    return {table:[tuple(row) for row in app.conn.execute(f'SELECT * FROM {table} WHERE learner_id=?',(learner,))]
            for table in LEARNER_TABLES}


def test_delete_reaches_legacy_checkpoints_all_derived_state_and_own_traces(tutor):
    seed_history(tutor)
    other_rows = learner_rows(tutor,'synthetic-b')
    other_history = tutor.history('b-first')
    shared_tables = ('proposals','published','keys','verified_key_cache')
    shared_before = {table:[tuple(r) for r in tutor.conn.execute(f'SELECT * FROM {table}')] for table in shared_tables}
    with TestClient(create_app(tutor=tutor,tokens=TOKENS)) as client:
        assert client.get('/learners/synthetic-a',headers=A).status_code==200
        assert client.get('/learners/synthetic-b',headers=B).status_code==200
        b_trace = [tuple(r) for r in tutor.conn.execute("SELECT * FROM trace_events WHERE session_id='api' AND json_extract(args,'$.learner_id')='synthetic-b'")]
        result=client.delete('/learners/synthetic-a',headers=T)
        assert result.status_code==200,result.text
        receipt=result.json()
        assert receipt['deleted'] and receipt['checkpoint_threads']==2
        assert receipt['logical_deletion_only'] and not receipt['backups_removed']
        assert not receipt['separate_beta_profile_removed']
        assert all(not rows for rows in learner_rows(tutor,'synthetic-a').values())
        assert learner_rows(tutor,'synthetic-b')==other_rows
        assert tutor.history('b-first')==other_history
        assert tutor.history('a-first')==[]
        for table in ('checkpoints','writes'):
            assert not tutor.checkpointer.conn.execute(f"SELECT 1 FROM {table} WHERE thread_id IN ('a-first','a-second')").fetchone()
        assert not tutor.conn.execute("SELECT 1 FROM trace_events WHERE session_id IN ('a-first','a-second') OR json_extract(args,'$.learner_id')='synthetic-a'").fetchone()
        assert [tuple(r) for r in tutor.conn.execute("SELECT * FROM trace_events WHERE session_id='api' AND json_extract(args,'$.learner_id')='synthetic-b'")]==b_trace
        assert {table:[tuple(r) for r in tutor.conn.execute(f'SELECT * FROM {table}')] for table in shared_tables}==shared_before
        assert tutor.approval.get_state({'configurable':{'thread_id':tutor.conn.execute('SELECT thread_id FROM proposals').fetchone()[0]}}).values
        assert 'a-first' not in tutor._ctx
        marker=tutor.conn.execute("SELECT * FROM learner_deletions WHERE learner_id='synthetic-a'").fetchone()
        assert marker['status']=='complete' and json.loads(marker['session_refs'])==[]
        assert client.delete('/learners/synthetic-a',headers=T).json()==receipt
        assert client.get('/learners',headers=T).json()['learners']==[{'learner_id':'synthetic-b','alias':'Synthetic B'}]
        for path in ('/learners/synthetic-a','/chat/a-first/history','/chat/active'):
            assert client.get(path,headers=A).status_code==410
        for path,body in (('/chat',{'text':'hello'}),('/chat/resume',{'session_id':'a-first'}),('/chat/leave',{'session_id':'a-first'})):
            assert client.post(path,json=body,headers=A).status_code==410
        assert client.post('/chat',json={'text':'hello'},headers=B).status_code==200


@pytest.mark.parametrize('headers',[{},A,B])
def test_delete_requires_real_teacher_role(tutor,headers):
    with TestClient(create_app(tutor=tutor,tokens=TOKENS)) as client:
        result=client.delete('/learners/synthetic-a',headers=headers)
        assert result.status_code==(401 if not headers else 403)
        assert not tutor.conn.execute('SELECT 1 FROM learner_deletions').fetchone()
        assert tutor.conn.execute("SELECT 1 FROM learners WHERE learner_id='synthetic-a'").fetchone()


def test_unknown_delete_does_not_create_tombstone(tutor):
    with TestClient(create_app(tutor=tutor,tokens=TOKENS)) as client:
        assert client.delete('/learners/not-present',headers=T).status_code==404
        assert not tutor.conn.execute('SELECT 1 FROM learner_deletions').fetchone()


def test_partial_checkpoint_deletion_blocks_access_and_recovers_after_restart(tmp_path,tutor,monkeypatch):
    seed_history(tutor)
    real_delete=tutor.checkpointer.delete_thread
    def interrupted(session_id):
        real_delete(session_id)
        raise RuntimeError('synthetic interruption after checkpoint commit')
    monkeypatch.setattr(tutor.checkpointer,'delete_thread',interrupted)
    with TestClient(create_app(tutor=tutor,tokens=TOKENS)) as client:
        result=client.delete('/learners/synthetic-a',headers=T)
        assert result.status_code==503 and 'pending' in result.json()['detail']
        assert client.get('/learners/synthetic-a',headers=A).status_code==410
        assert client.get('/chat/a-first/history',headers=A).status_code==410
        assert client.post('/chat',json={'text':'hello'},headers=A).status_code==410
        assert client.get('/learners',headers=T).json()['learners']==[{'learner_id':'synthetic-b','alias':'Synthetic B'}]
        assert not seed_learner(tutor.conn,'synthetic-a',{'alias':'must not return'})
        request_id=tutor.conn.execute('SELECT request_id FROM learner_deletions').fetchone()[0]
    tutor.close()
    restarted=make_tutor(tmp_path)
    try:
        with TestClient(create_app(tutor=restarted,tokens=TOKENS)) as client:
            assert client.get('/learners/synthetic-a',headers=A).status_code==410
            result=client.delete('/learners/synthetic-a',headers=T)
            assert result.status_code==200,result.text
            assert result.json()['request_id']==request_id
            assert all(not rows for rows in learner_rows(restarted,'synthetic-a').values())
            assert not restarted.conn.execute("SELECT 1 FROM trace_events WHERE session_id LIKE 'a-%'").fetchone()
            assert client.post('/chat',json={'text':'hello'},headers=B).status_code==200
    finally:
        restarted.close()


def test_domain_rollback_keeps_worklist_for_retry(tutor):
    seed_history(tutor)
    tutor.conn.executescript("CREATE TRIGGER fail_synthetic_delete BEFORE DELETE ON mastery BEGIN SELECT RAISE(ABORT,'synthetic failure'); END;")
    with pytest.raises(ToolCallError,match='BUSY'):
        tutor.forget_learner('synthetic-a','synthetic-teacher')
    marker=tutor.conn.execute('SELECT * FROM learner_deletions').fetchone()
    assert marker['status']=='pending' and len(json.loads(marker['session_refs']))==2
    assert tutor.conn.execute("SELECT 1 FROM trace_events WHERE session_id='a-first'").fetchone()
    assert tutor.conn.execute("SELECT 1 FROM learners WHERE learner_id='synthetic-a'").fetchone()
    tutor.conn.execute('DROP TRIGGER fail_synthetic_delete')
    assert tutor.forget_learner('synthetic-a','synthetic-teacher')['deleted']
    assert not tutor.conn.execute("SELECT 1 FROM trace_events WHERE session_id='a-first'").fetchone()


def test_all_registered_checkpoint_files_are_purged(tmp_path,tutor):
    tutor.turn('a-main','synthetic-a','hello')
    other=make_tutor(tmp_path,'other-checkpoints.db')
    try:
        other.turn('a-other','synthetic-a','hello')
        other.turn('b-other','synthetic-b','hello')
        expected=other.history('b-other')
        assert tutor.forget_learner('synthetic-a','synthetic-teacher')['checkpoint_threads']==2
        assert other.history('a-other')==[] and other.history('b-other')==expected
        with pytest.raises(ToolCallError,match='GONE'):
            other.turn('new-a','synthetic-a','hello')
    finally:
        other.close()


def test_registered_pending_writes_without_finished_checkpoint_are_purged(tutor):
    tutor.checkpointer.setup()
    tutor.conn.execute('INSERT INTO learner_session_index VALUES (?,?,?)',('a-pending',tutor.checkpoint_path,'synthetic-a'))
    tutor.checkpointer.put_writes({'configurable':{'thread_id':'a-pending','checkpoint_ns':'','checkpoint_id':'synthetic-checkpoint'}},[('synthetic','private synthetic turn')],'synthetic-task')
    assert tutor.checkpointer.conn.execute("SELECT 1 FROM writes WHERE thread_id='a-pending'").fetchone()
    assert tutor.forget_learner('synthetic-a','synthetic-teacher')['deleted']
    assert not tutor.checkpointer.conn.execute("SELECT 1 FROM writes WHERE thread_id='a-pending'").fetchone()


def test_mixed_legacy_ownership_is_quarantined_without_erasing_other_learner(tutor):
    tutor.turn('legacy-shared','synthetic-a','hello')
    tutor.graph.update_state({'configurable':{'thread_id':'legacy-shared'}},{'session':{'session_id':'legacy-shared','learner_id':'synthetic-b','mode':'practice'}})
    before=list(tutor.checkpointer.list(None))
    with pytest.raises(ToolCallError,match='CONFLICT'):
        tutor.forget_learner('synthetic-a','synthetic-teacher')
    assert len(list(tutor.checkpointer.list(None)))==len(before)
    assert tutor.conn.execute("SELECT 1 FROM learners WHERE learner_id='synthetic-b'").fetchone()
    with pytest.raises(ToolCallError,match='GONE'):
        tutor.turn('a-new','synthetic-a','hello')


def test_index_prevents_cross_store_session_reuse_by_other_learner(tmp_path,tutor):
    tutor.turn('existing-thread','synthetic-a','hello')
    other=make_tutor(tmp_path,'other-checkpoints.db')
    try:
        with pytest.raises(ToolCallError,match='FORBIDDEN'):
            other.turn('existing-thread','synthetic-b','hello')
    finally:
        other.close()


@pytest.mark.parametrize('sid',['api','teacher','qs-reserved'])
def test_reserved_trace_names_cannot_be_student_sessions(tutor,sid):
    with TestClient(create_app(tutor=tutor,tokens=TOKENS)) as client:
        assert client.post('/chat',json={'session_id':sid,'text':'hello'},headers=A).status_code==422


def test_agents_cannot_delete_and_deleted_context_cannot_create_new_traces(tutor):
    assert not any('forget' in tool['name'] for tools in tutor.bus.list_tools().values() for tool in tools)
    with pytest.raises(ToolCallError,match='FORBIDDEN'):
        tutor.bus.call(CallContext(session_id='synthetic-attempt',learner_id='synthetic-a'),'study_planner','learner-store','forget_learner',{'learner_id':'synthetic-a'})
    tutor.forget_learner('synthetic-a','synthetic-teacher')
    count=tutor.conn.execute('SELECT COUNT(*) FROM trace_events').fetchone()[0]
    with pytest.raises(ToolCallError,match='GONE'):
        tutor.bus.call(CallContext(session_id='synthetic-attempt',learner_id='synthetic-a'),'study_planner','learner-store','read_learner',{'learner_id':'synthetic-a'})
    assert tutor.conn.execute('SELECT COUNT(*) FROM trace_events').fetchone()[0]==count
    assert not seed_learner(tutor.conn,'synthetic-a',{'mastery':{'qe04':0.4}})


def test_api_startup_seeding_respects_tombstone(tmp_path,tutor,monkeypatch):
    from tutor import config
    from tutor_api.main import _seed_if_needed
    from tutor_api.auth import parse_tokens
    tutor.forget_learner('synthetic-a','synthetic-teacher')
    monkeypatch.setattr(config,'db_path',lambda name:tmp_path/name)
    _seed_if_needed(parse_tokens(TOKENS))
    assert not tutor.conn.execute("SELECT 1 FROM learners WHERE learner_id='synthetic-a'").fetchone()
    assert tutor.conn.execute("SELECT 1 FROM learners WHERE learner_id='synthetic-b'").fetchone()


def test_delete_waits_for_active_turn_then_removes_its_final_writes(tmp_path,tutor,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from threading import Event
    other=make_tutor(tmp_path,'other-checkpoints.db')
    entered,release=Event(),Event()
    invoke=other.graph.invoke
    def held(*args,**kwargs):
        entered.set()
        assert release.wait(10)
        return invoke(*args,**kwargs)
    monkeypatch.setattr(other.graph,'invoke',held)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            turn=pool.submit(other.turn,'a-in-flight','synthetic-a','hello')
            assert entered.wait(5)
            deletion=pool.submit(tutor.forget_learner,'synthetic-a','synthetic-teacher')
            try:
                with pytest.raises(TimeoutError):
                    deletion.result(timeout=.3)
            finally:
                release.set()
            assert turn.result(timeout=10)['reply']
            assert deletion.result(timeout=10)['deleted']
        assert other.history('a-in-flight')==[]
        assert not tutor.conn.execute("SELECT 1 FROM trace_events WHERE session_id='a-in-flight'").fetchone()
        with pytest.raises(ToolCallError,match='GONE'):
            other.turn('after-delete','synthetic-a','hello')
    finally:
        release.set()
        other.close()


def test_delete_obeys_lock_held_by_another_process(tmp_path,tutor):
    import subprocess
    import sys
    import time
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    ready,release=tmp_path/'ready',tmp_path/'release'
    script='''import pathlib,sys,time
from filelock import FileLock
lock,ready,release=map(pathlib.Path,sys.argv[1:])
with FileLock(lock,timeout=5,preserve_lock_file=True,fallback_to_soft=False):
 ready.write_text('ready')
 deadline=time.monotonic()+15
 while not release.exists() and time.monotonic()<deadline: time.sleep(.02)
 if not release.exists(): raise RuntimeError('synthetic release timeout')
'''
    child=subprocess.Popen([sys.executable,'-c',script,str(tutor.bus.publication_lock.lock_file),str(ready),str(release)])
    try:
        deadline=time.monotonic()+10
        while not ready.exists() and child.poll() is None and time.monotonic()<deadline:
            time.sleep(.02)
        assert ready.exists() and child.poll() is None
        with ThreadPoolExecutor(max_workers=1) as pool:
            deletion=pool.submit(tutor.forget_learner,'synthetic-a','synthetic-teacher')
            try:
                with pytest.raises(TimeoutError):
                    deletion.result(timeout=.3)
            finally:
                release.touch()
            assert deletion.result(timeout=10)['deleted']
        assert child.wait(timeout=10)==0
    finally:
        release.touch()
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)


def test_teacher_deletion_widgets_require_confirmation_and_show_receipt(tutor,monkeypatch):
    import requests
    from urllib.parse import urlsplit
    from streamlit.testing.v1 import AppTest
    with TestClient(create_app(tutor=tutor,tokens=TOKENS)) as client:
        def route_local(method,url,headers=None,timeout=None,**kwargs):
            return client.request(method,urlsplit(url).path,headers=headers,**kwargs)
        monkeypatch.setattr(requests,'request',route_local)
        monkeypatch.setenv('TUTOR_API_URL','http://testserver')
        monkeypatch.setenv('TUTOR_UI_TOKEN','t')
        # Execute the actual page function with the same sign-in and HTTP helper.
        source=(Path(__file__).resolve().parents[1]/'ui/app.py').read_text(encoding='utf-8')
        ui=AppTest.from_string(source.replace('st.navigation(pages).run()','teacher_privacy()')).run(timeout=30)
        assert not ui.exception
        button=lambda:next(b for b in ui.button if b.label=='Delete connected learning record')
        assert button().disabled
        ui.text_input(key='delete_learner_id').set_value('synthetic-a').run()
        ui.text_input(key='delete_confirmation').set_value('synthetic-b').run()
        ui.checkbox[0].check().run()
        assert button().disabled
        ui.text_input(key='delete_confirmation').set_value('synthetic-a').run()
        assert not button().disabled
        button().click().run(timeout=30)
        assert not ui.exception and any('record was deleted' in s.value for s in ui.success)
        receipts=[json.loads(element.value) for element in ui.json]
        assert any(r.get('deleted') and r.get('logical_deletion_only') for r in receipts)
        assert client.get('/learners/synthetic-b',headers=B).status_code==200


def test_invalid_trace_json_cannot_break_deletion(tutor):
    tutor.turn('a-trace','synthetic-a','hello')
    tutor.conn.execute("INSERT INTO trace_events (session_id,args) VALUES (?,?)",('synthetic-unrelated','not-json'))
    assert tutor.forget_learner('synthetic-a','synthetic-teacher')['deleted']
    assert tutor.conn.execute("SELECT 1 FROM trace_events WHERE session_id='synthetic-unrelated'").fetchone()
