"""Publication must use the current, teacher-approved, unchanged payload."""
import json
import pytest
from tutor.app import TutorApp
from tutor import store
from tutor.toolbus import CallContext


def published_items(app):
    return app.bus.call(CallContext(session_id='synthetic-check'), 'question_setter',
                        'question-bank', 'list_published', {})['items']


def test_edit_hides_previously_published_version_until_reapproval(tmp_path):
    app = TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        proposal = app.propose_set('qe04')
        sid = proposal['set_id']
        approved = app.decide(sid, 'approve', 'synthetic-teacher')
        assert approved['status'] == 'published'
        items = [x['question_id'] for x in app.proposal(sid)['payload']['items']]
        assert any(x['set_id'] == sid for x in published_items(app))
        assert app.decide(sid, 'edit', 'synthetic-teacher', question_ids=items[:-1])['status'] == 'pending'
        assert not any(x['set_id'] == sid for x in published_items(app))
        assert app.try_publish(sid, approved['token'], 'synthetic-teacher')['published'] is False
        assert app.decide(sid, 'approve', 'synthetic-teacher')['status'] == 'published'
        assert any(x['set_id'] == sid for x in published_items(app))
    finally:
        app.close()


def test_unapproved_rows_are_not_visible_to_the_normal_tutor(tmp_path):
    app = TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        from tutor.setup_content import load
        item = load('practice')[0]
        payload = {'set_id':'synthetic-unapproved','concept_id':'qe04','revision':1,'items':[item]}
        app.conn.execute('INSERT INTO published VALUES (?,?,?,?,?,?)',
                         ('synthetic-unapproved',store.dumps(payload),'not-a-hash','none','eval_fixture_unapproved',store.now()))
        assert not any(x['set_id'] == 'synthetic-unapproved' for x in published_items(app))
    finally:
        app.close()


def test_tampered_payload_cannot_be_published_using_an_old_valid_token(tmp_path):
    app = TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        proposal = app.propose_set('qe04')
        sid = proposal['set_id']
        approved = app.decide(sid, 'approve', 'synthetic-teacher')
        payload = app.proposal(sid)['payload']
        payload['items'][0]['prompt'] += ' [tampered]'
        # Simulate a corrupted stored payload while retaining the old signed digest.
        app.conn.execute('UPDATE proposals SET payload_json=? WHERE set_id=?', (store.dumps(payload), sid))
        assert app.try_publish(sid, approved['token'], 'synthetic-teacher')['published'] is False
        assert not any(x['set_id'] == sid for x in published_items(app))
    finally:
        app.close()


def test_only_explicit_development_mode_can_serve_synthetic_fixtures(tmp_path):
    db, ck1, ck2 = tmp_path/'shared.db', tmp_path/'normal-checkpoints.db', tmp_path/'dev-checkpoints.db'
    normal = TutorApp(llm_mode='stub', db_name=str(db), checkpoint_name=str(ck1))
    dev = TutorApp(llm_mode='stub', db_name=str(db), checkpoint_name=str(ck2), allow_dev_fixtures=True)
    try:
        from tutor.setup_content import load
        item = load('practice')[0]
        payload = {'set_id':'fixture','concept_id':'qe04','revision':1,'items':[item]}
        normal.conn.execute('INSERT INTO published VALUES (?,?,?,?,?,?)',
                            ('fixture',store.dumps(payload),'fixture','none','eval_fixture_unapproved',store.now()))
        assert not any(x['set_id'] == 'fixture' for x in published_items(normal))
        assert any(x['set_id'] == 'fixture' for x in published_items(dev))
    finally:
        dev.close()
        normal.close()


def test_rejected_proposal_cannot_be_republished_with_prior_token(tmp_path):
    app = TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        sid = app.propose_set('qe04')['set_id']
        approved = app.decide(sid, 'approve', 'synthetic-teacher')
        app.bus.call(CallContext(session_id='teacher'), 'approval_gate', 'question-bank',
                     'reject_proposal', {'set_id':sid,'reason':'synthetic rejection'})
        assert app.try_publish(sid, approved['token'], 'synthetic-teacher')['published'] is False
        assert not any(x['set_id'] == sid for x in published_items(app))
    finally:
        app.close()


def test_concurrent_publish_cannot_leave_an_edited_set_visible(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from threading import Event
    import pytest
    from tutor.mcp_servers import question_bank

    monkeypatch.setenv('APPROVAL_SECRET', 'synthetic-test-secret')
    db = tmp_path/'shared.db'
    first = TutorApp(llm_mode='stub', db_name=str(db), checkpoint_name=str(tmp_path/'a-checkpoints.db'))
    second = TutorApp(llm_mode='stub', db_name=str(db), checkpoint_name=str(tmp_path/'b-checkpoints.db'))
    release = Event()
    try:
        sid = first.propose_set('qe04')['set_id']
        approved = first.decide(sid, 'approve', 'synthetic-teacher')
        items = [x['question_id'] for x in first.proposal(sid)['payload']['items']]
        verified = Event()
        edit_started = Event()
        original = question_bank.approval_token_valid
        def controlled_validation(token, digest, teacher):
            verdict = original(token, digest, teacher)
            verified.set()
            if not release.wait(10):
                raise RuntimeError('test did not release publication')
            return verdict
        monkeypatch.setattr(question_bank, 'approval_token_valid', controlled_validation)
        def publish():
            return first.try_publish(sid, approved['token'], 'synthetic-teacher')
        def edit():
            edit_started.set()
            return second.bus.call(CallContext(session_id='teacher'), 'approval_gate', 'question-bank',
                                   'update_proposal', {'set_id':sid,'question_ids':items[:-1],'thread_id':'synthetic-edit'})
        with ThreadPoolExecutor(max_workers=2) as pool:
            publish_future = pool.submit(publish)
            assert verified.wait(10)
            edit_future = pool.submit(edit)
            assert edit_started.wait(10)
            with pytest.raises(TimeoutError):
                edit_future.result(timeout=0.3)
            release.set()
            assert publish_future.result(timeout=10)['published'] is True
            edit_future.result(timeout=10)
        assert second.proposal(sid)['status'] == 'pending'
        assert not any(x['set_id'] == sid for x in published_items(second))
        assert second.try_publish(sid, approved['token'], 'synthetic-teacher')['published'] is False
    finally:
        release.set()
        second.close()
        first.close()


@pytest.mark.parametrize('arm', ['c1', 'c2'])
@pytest.mark.parametrize('defences', [True, False])
def test_edit_revokes_an_active_practice_question(tmp_path, arm, defences):
    from tutor_eval.arms import make_app
    from tutor.seed import seed_learner

    app = make_app(arm, defences=defences, llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        seed_learner(app.conn, 'learner', {'alias':'synthetic'})
        proposal = app.propose_set('qe04')
        sid = proposal['set_id']
        assert app.decide(sid, 'approve', 'synthetic-teacher')['status'] == 'published'
        started = app.turn('practice-session', 'learner', 'practice')
        assert started['active_item']
        ids = [i['question_id'] for i in app.proposal(sid)['payload']['items']]
        app.decide(sid, 'edit', 'synthetic-teacher', question_ids=ids[:-1])
        next_turn = app.turn('practice-session', 'learner', 'hint')
        assert next_turn['route'] == 'question_revoked'
        assert next_turn['active_item'] is None
        assert 'no longer available' in next_turn['reply'].lower()
    finally:
        app.close()


@pytest.mark.parametrize('arm', ['c1', 'c2'])
@pytest.mark.parametrize('defences', [True, False])
def test_edit_cancels_an_active_quiz_without_scoring_it(tmp_path, arm, defences):
    from tutor_eval.arms import make_app
    from tutor.seed import seed_learner

    app = make_app(arm, defences=defences, llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        seed_learner(app.conn, 'learner', {'alias':'synthetic'})
        proposal = app.propose_set('qe04', mode='quiz')
        sid = proposal['set_id']
        assert app.decide(sid, 'approve', 'synthetic-teacher')['status'] == 'published'
        started = app.turn('quiz-session', 'learner', 'start a quiz', mode='quiz')
        assert started['route'] == 'quiz_start'
        ids = [i['question_id'] for i in app.proposal(sid)['payload']['items']]
        app.decide(sid, 'edit', 'synthetic-teacher', question_ids=ids[:-1])
        next_turn = app.turn('quiz-session', 'learner', 'x = 1', mode='quiz')
        assert next_turn['route'] == 'question_revoked'
        state = app.graph.get_state({'configurable':{'thread_id':'quiz-session'}}).values
        assert state['quiz'] is None and not state.get('grade')
    finally:
        app.close()


@pytest.mark.parametrize('arm', ['c1', 'c2'])
def test_publication_check_failure_revokes_active_question(tmp_path, monkeypatch, arm):
    from tutor_eval.arms import make_app
    from tutor.seed import seed_learner

    app = make_app(arm, defences=False, llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        seed_learner(app.conn, 'learner', {'alias': 'synthetic'})
        proposal = app.propose_set('qe04')
        assert app.decide(proposal['set_id'], 'approve', 'synthetic-teacher')['status'] == 'published'
        assert app.turn('session', 'learner', 'practice')['active_item']
        original = app._call
        def unavailable(state, agent, principal, server, method, args):
            if server == 'question-bank' and method == 'list_published':
                raise RuntimeError('synthetic outage')
            return original(state, agent, principal, server, method, args)
        monkeypatch.setattr(app, '_call', unavailable)
        response = app.turn('session', 'learner', 'x = 1')
        assert response['route'] == 'question_revoked'
        assert response['active_item'] is None
        assert not response.get('grade')
    finally:
        app.close()


@pytest.mark.parametrize('arm', ['c1', 'c2'])
@pytest.mark.parametrize('same_app', [True, False])
def test_teacher_edit_waits_for_active_learner_turn(tmp_path, monkeypatch, arm, same_app):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from threading import Event
    from tutor_eval.arms import make_app
    from tutor.seed import seed_learner

    db = tmp_path / 'shared.db'
    learner = make_app(arm, defences=True, llm_mode='stub', db_name=str(db),
                       checkpoint_name=str(tmp_path / 'learner-checkpoints.db'))
    teacher = learner if same_app else TutorApp(llm_mode='stub', db_name=str(db), checkpoint_name=str(tmp_path / 'teacher-checkpoints.db'))
    release = Event()
    try:
        seed_learner(learner.conn, 'learner', {'alias': 'synthetic'})
        sid = learner.propose_set('qe04')['set_id']
        assert learner.decide(sid, 'approve', 'synthetic-teacher')['status'] == 'published'
        assert learner.turn('session', 'learner', 'practice')['active_item']
        ids = [i['question_id'] for i in learner.proposal(sid)['payload']['items']]
        checked, editing = Event(), Event()
        original = learner._call
        def pause_after_check(state, node, role, server, tool, args):
            result = original(state, node, role, server, tool, args)
            if node == 'input_guard' and server == 'question-bank' and tool == 'list_published':
                checked.set()
                if not release.wait(10):
                    raise RuntimeError('test did not release turn')
            return result
        monkeypatch.setattr(learner, '_call', pause_after_check)
        def do_edit():
            editing.set()
            return teacher.bus.call(CallContext(session_id='teacher'), 'approval_gate', 'question-bank',
                                    'update_proposal', {'set_id': sid, 'question_ids': ids[:-1], 'thread_id': 'edit'})
        with ThreadPoolExecutor(max_workers=2) as pool:
            turn = pool.submit(learner.turn, 'session', 'learner', 'x = 1')
            assert checked.wait(10)
            edit = pool.submit(do_edit)
            assert editing.wait(10)
            with pytest.raises(TimeoutError):
                edit.result(timeout=0.4)
            release.set()
            assert turn.result(timeout=10)['route'] == 'grade'
            edit.result(timeout=10)
        assert learner.turn('session', 'learner', 'hint')['route'] == 'question_revoked'
    finally:
        release.set()
        if teacher is not learner:
            teacher.close()
        learner.close()


@pytest.mark.parametrize('arm', ['c1', 'c2'])
def test_resume_does_not_grade_a_set_edited_during_interruption(tmp_path, arm):
    from tutor import guards
    from tutor_eval.arms import make_app
    from tutor.seed import seed_learner

    app = make_app(arm, defences=True, llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        seed_learner(app.conn, 'learner', {'alias':'synthetic'})
        sid = app.propose_set('qe04')['set_id']
        assert app.decide(sid, 'approve', 'synthetic-teacher')['status'] == 'published'
        assert app.turn('session', 'learner', 'practice')['active_item']
        screen = guards.screen_input('x = 1')
        config = {'configurable': {'thread_id':'session'}}
        stop_after = 'load_learner' if arm == 'c1' else 'planner'
        app.graph.invoke({'incoming': screen['text'], 'screen': screen,
                          'session': {'session_id':'session', 'learner_id':'learner', 'mode':'practice'}},
                         config, interrupt_after=[stop_after])
        assert app.graph.get_state(config).next
        ids = [i['question_id'] for i in app.proposal(sid)['payload']['items']]
        app.decide(sid, 'edit', 'synthetic-teacher', question_ids=ids[:-1])
        result = app.resume('session')
        assert 'no longer available' in result['reply'].lower()
        state = app.graph.get_state(config)
        assert not state.next
        assert state.values.get('active_item') is None and state.values.get('quiz') is None
        assert not state.values.get('grade')
    finally:
        app.close()



def test_teacher_edit_respects_publication_lock_held_by_another_process(tmp_path):
    import subprocess
    import sys
    import time
    from concurrent.futures import ThreadPoolExecutor, TimeoutError

    app = TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    child = None
    release = tmp_path / 'release'
    try:
        sid = app.propose_set('qe04')['set_id']
        assert app.decide(sid, 'approve', 'synthetic-teacher')['status'] == 'published'
        ids = [i['question_id'] for i in app.proposal(sid)['payload']['items']]
        ready = tmp_path / 'ready'
        script = (
            'import pathlib,sys,time\n'
            'from filelock import FileLock\n'
            'lock,ready,release=map(pathlib.Path,sys.argv[1:])\n'
            'with FileLock(lock,timeout=5,preserve_lock_file=True,fallback_to_soft=False):\n'
            ' ready.write_text("ready")\n'
            ' deadline=time.monotonic()+15\n'
            ' while not release.exists() and time.monotonic()<deadline: time.sleep(.02)\n'
            ' if not release.exists(): raise RuntimeError("test release timed out")\n'
        )
        child = subprocess.Popen([sys.executable, '-c', script, str(app.bus.publication_lock.lock_file),
                                  str(ready), str(release)])
        deadline = time.monotonic() + 10
        while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
            time.sleep(.02)
        assert ready.exists(), 'child process did not acquire the lock'
        def edit():
            return app.bus.call(CallContext(session_id='teacher'), 'approval_gate', 'question-bank',
                                'update_proposal', {'set_id':sid, 'question_ids':ids[:-1], 'thread_id':'edit'})
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(edit)
            try:
                with pytest.raises(TimeoutError):
                    future.result(timeout=.4)
            finally:
                release.touch()
            assert future.result(timeout=10)['set_id'] == sid
        assert child.wait(timeout=10) == 0
    finally:
        release.touch()
        if child and child.poll() is None:
            child.terminate()
            child.wait(timeout=10)
        app.close()


def test_resume_rechecks_a_correct_grade_after_active_item_was_cleared(tmp_path):
    from tutor import guards
    from tutor.seed import seed_learner
    from tutor_eval.simulator import render

    app = TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        seed_learner(app.conn, 'learner', {'alias':'synthetic'})
        sid = app.propose_set('qe04')['set_id']
        assert app.decide(sid, 'approve', 'synthetic-teacher')['status'] == 'published'
        question = app.turn('session', 'learner', 'practice')['active_item']
        key = json.loads(app.conn.execute('SELECT key_json FROM keys WHERE question_ref=?', (question,)).fetchone()[0])
        screen = guards.screen_input(render(key))
        config = {'configurable': {'thread_id':'session'}}
        app.graph.invoke({'incoming':screen['text'], 'screen':screen,
                          'session': {'session_id':'session', 'learner_id':'learner', 'mode':'practice'}},
                         config, interrupt_after=['grade'])
        state = app.graph.get_state(config)
        assert state.next and state.values['grade']['correct'] and state.values['active_item'] is None
        ids = [i['question_id'] for i in app.proposal(sid)['payload']['items']]
        app.decide(sid, 'edit', 'synthetic-teacher', question_ids=ids[:-1])
        result = app.resume('session')
        assert result['revoked'] is True and 'no longer available' in result['reply'].lower()
        assert not app.graph.get_state(config).next
        assert app.graph.get_state(config).values['grade'] is None
    finally:
        app.close()
