"""Graph quiz updates must be applied once, including after interruption."""
import pytest
from tutor.app import TutorApp
from tutor.seed import seed_learner


def setup_app(tmp_path):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    seed_learner(app.conn,'learner',{'alias':'synthetic'})
    proposal=app.propose_set('qe04',mode='quiz')
    assert app.decide(proposal['set_id'],'approve','synthetic-teacher')['status']=='published'
    return app


def test_completed_quiz_does_not_reapply_on_later_turns(tmp_path):
    app=setup_app(tmp_path)
    try:
        session='quiz-once'
        started=app.turn(session,'learner','start a quiz',mode='quiz')
        assert started['route']=='quiz_start'
        for _ in range(3):result=app.turn(session,'learner','no real roots',mode='quiz')
        assert result['plan']['replan_reason'].startswith('after quiz:')
        before={r['concept_id']:r['p'] for r in app.conn.execute('SELECT concept_id,p FROM mastery WHERE learner_id=?',('learner',))}
        version=result['plan']['version']
        later=app.turn(session,'learner','hello',mode='practice')
        after={r['concept_id']:r['p'] for r in app.conn.execute('SELECT concept_id,p FROM mastery WHERE learner_id=?',('learner',))}
        assert later['plan']['version']==version
        assert after==before
    finally:app.close()


def test_interruption_after_quiz_plan_save_does_not_apply_results_twice(tmp_path,monkeypatch):
    import json

    app=setup_app(tmp_path)
    try:
        session='quiz-interrupt'
        assert app.turn(session,'learner','start a quiz',mode='quiz')['route']=='quiz_start'
        for _ in range(2):app.turn(session,'learner','no real roots',mode='quiz')
        original=app._call;interrupted=False
        def crash_after_save(state,node,role,server,tool,args):
            nonlocal interrupted
            result=original(state,node,role,server,tool,args)
            if node=='update_memory' and server=='learner-store' and tool=='apply_quiz' and not interrupted:
                interrupted=True
                raise RuntimeError('synthetic interruption after plan save')
            return result
        monkeypatch.setattr(app,'_call',crash_after_save)
        with pytest.raises(RuntimeError,match='synthetic interruption'):
            app.turn(session,'learner','no real roots',mode='quiz')
        before={r['concept_id']:r['p'] for r in app.conn.execute('SELECT concept_id,p FROM mastery WHERE learner_id=?',('learner',))}
        target=next(iter(before))
        from tutor.toolbus import CallContext
        app.bus.call(CallContext(session_id='other-session',learner_id='learner'),'study_planner','learner-store',
                     'update_mastery',{'learner_id':'learner','concept_id':target,'p_mastery':0.987,'evidence_ref':'synthetic later observation'})
        before[target]=0.987
        plan_before=json.loads(app.conn.execute('SELECT plan_json FROM plans WHERE learner_id=?',('learner',)).fetchone()[0])
        plan_before.update(version=99,replan_reason='synthetic later plan')
        app.bus.call(CallContext(session_id='other-session',learner_id='learner'),'study_planner','learner-store',
                     'save_plan',{'learner_id':'learner','plan':plan_before})
        events_before=app.conn.execute('SELECT COUNT(*) FROM learner_events WHERE learner_id=?',('learner',)).fetchone()[0]
        result=app.resume(session)
        assert result and result['reply']
        after={r['concept_id']:r['p'] for r in app.conn.execute('SELECT concept_id,p FROM mastery WHERE learner_id=?',('learner',))}
        plan_after=json.loads(app.conn.execute('SELECT plan_json FROM plans WHERE learner_id=?',('learner',)).fetchone()[0])
        events_after=app.conn.execute('SELECT COUNT(*) FROM learner_events WHERE learner_id=?',('learner',)).fetchone()[0]
        assert after==before and plan_after==plan_before
        assert events_after==events_before
    finally:app.close()


def test_atomic_quiz_application_rolls_back_on_midway_failure(tmp_path,monkeypatch):
    from tutor import store
    from tutor.toolbus import CallContext,ToolCallError

    app=setup_app(tmp_path)
    try:
        context=CallContext(session_id='atomic',learner_id='learner')
        results=[{'question_id':'synthetic-q','correct':True,'scorable':True,
                  'concept_ids':['qe01','qe02'],'kind':'finite_set'}]
        original=store._resolve_stuck_concept_locked
        def fail_on_second(conn,learner_id,concept_id):
            if concept_id=='qe02':raise RuntimeError('synthetic midway failure')
            return original(conn,learner_id,concept_id)
        monkeypatch.setattr(store,'_resolve_stuck_concept_locked',fail_on_second)
        with pytest.raises(ToolCallError):
            app.bus.call(context,'study_planner','learner-store','apply_quiz',
                         {'learner_id':'learner','quiz_id':'a'*32,'results':results})
        assert app.conn.execute('SELECT COUNT(*) FROM mastery WHERE learner_id=?',('learner',)).fetchone()[0]==0
        assert app.conn.execute('SELECT COUNT(*) FROM learner_events WHERE learner_id=?',('learner',)).fetchone()[0]==0
        assert app.conn.execute('SELECT COUNT(*) FROM applied_quizzes').fetchone()[0]==0
        monkeypatch.setattr(store,'_resolve_stuck_concept_locked',original)
        first=app.bus.call(context,'study_planner','learner-store','apply_quiz',
                           {'learner_id':'learner','quiz_id':'a'*32,'results':results})
        count=app.conn.execute('SELECT COUNT(*) FROM learner_events WHERE learner_id=?',('learner',)).fetchone()[0]
        again=app.bus.call(context,'study_planner','learner-store','apply_quiz',
                           {'learner_id':'learner','quiz_id':'a'*32,'results':results})
        assert first['applied'] is True and again['applied'] is False
        assert app.conn.execute('SELECT COUNT(*) FROM learner_events WHERE learner_id=?',('learner',)).fetchone()[0]==count
        changed=[{**results[0],'correct':False}]
        with pytest.raises(ToolCallError,match='FORBIDDEN'):
            app.bus.call(context,'study_planner','learner-store','apply_quiz',
                         {'learner_id':'learner','quiz_id':'a'*32,'results':changed})
    finally:app.close()


def test_quiz_application_is_once_across_two_database_connections(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from tutor.toolbus import CallContext

    first=setup_app(tmp_path)
    second=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'other-checkpoint.db'))
    try:
        results=[{'question_id':'synthetic-q','correct':False,'scorable':True,
                  'concept_ids':['qe01'],'kind':'finite_set'}]
        barrier=Barrier(2)
        def apply(app):
            barrier.wait(timeout=5)
            return app.bus.call(CallContext(session_id='concurrent',learner_id='learner'),
                'study_planner','learner-store','apply_quiz',
                {'learner_id':'learner','quiz_id':'b'*32,'results':results})
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(apply,[first,second]))
        assert sorted(o['applied'] for o in outcomes)==[False,True]
        assert first.conn.execute('SELECT COUNT(*) FROM applied_quizzes').fetchone()[0]==1
        assert first.conn.execute("SELECT COUNT(*) FROM learner_events WHERE learner_id=? AND kind='mastery'",('learner',)).fetchone()[0]==1
        assert first.conn.execute("SELECT COUNT(*) FROM learner_events WHERE learner_id=? AND kind='plan'",('learner',)).fetchone()[0]==1
    finally:
        second.close();first.close()


def test_quiz_application_respects_role_and_learner_boundaries(tmp_path):
    from tutor.toolbus import CallContext,ToolCallError

    app=setup_app(tmp_path)
    try:
        results=[{'question_id':'synthetic-q','correct':False,'scorable':True,
                  'concept_ids':['qe01'],'kind':'finite_set'}]
        args={'learner_id':'learner','quiz_id':'c'*32,'results':results}
        with pytest.raises(ToolCallError,match='FORBIDDEN'):
            app.bus.call(CallContext(session_id='wrong-role',learner_id='learner'),
                         'tutor','learner-store','apply_quiz',args)
        with pytest.raises(ToolCallError,match='FORBIDDEN'):
            app.bus.call(CallContext(session_id='wrong-owner',learner_id='other'),
                         'study_planner','learner-store','apply_quiz',args)
        assert app.conn.execute('SELECT COUNT(*) FROM applied_quizzes').fetchone()[0]==0
    finally:app.close()


def test_finished_legacy_checkpoint_fails_closed_without_false_success(tmp_path):
    import copy
    from tutor import guards

    app=setup_app(tmp_path)
    try:
        session='legacy-finished'
        app.turn(session,'learner','start a quiz',mode='quiz')
        for _ in range(2):app.turn(session,'learner','no real roots',mode='quiz')
        config={'configurable':{'thread_id':session}}
        screen=guards.screen_input('no real roots')
        app.graph.invoke({'incoming':screen['text'],'screen':screen,
                          'session':{'session_id':session,'learner_id':'learner','mode':'quiz'}},
                         config,interrupt_after=['output_guard'])
        snap=app.graph.get_state(config)
        assert snap.next==('update_memory',)
        quiz=copy.deepcopy(snap.values['quiz'])
        quiz.pop('quiz_id')
        app.graph.update_state(config,{'quiz':quiz},as_node='output_guard')
        result=app.resume(session)
        assert 'could not be safely recorded' in result['reply']
        assert "I've updated your study plan" not in result['reply']
        assert app.conn.execute('SELECT COUNT(*) FROM applied_quizzes').fetchone()[0]==0
        assert app.conn.execute('SELECT COUNT(*) FROM mastery').fetchone()[0]==0
    finally:app.close()


def test_unparseable_quiz_answer_does_not_advance_or_change_learner(tmp_path):
    app=setup_app(tmp_path)
    try:
        session='invalid-quiz-answer'
        app.turn(session,'learner','start a quiz',mode='quiz')
        config={'configurable':{'thread_id':session}}
        before=app.graph.get_state(config).values['quiz']
        plan_before=app.conn.execute('SELECT plan_json FROM plans WHERE learner_id=?',('learner',)).fetchone()[0]
        events_before=app.conn.execute('SELECT COUNT(*) FROM learner_events').fetchone()[0]
        result=app.turn(session,'learner','banana',mode='quiz')
        after=app.graph.get_state(config).values['quiz']
        assert result['route']=='quiz_answer'
        assert 'could not read' in result['reply'].lower()
        assert after['index']==before['index'] and after['results']==before['results']
        assert app.conn.execute('SELECT plan_json FROM plans WHERE learner_id=?',('learner',)).fetchone()[0]==plan_before
        assert app.conn.execute('SELECT COUNT(*) FROM learner_events').fetchone()[0]==events_before
        app.turn(session,'learner','no real roots',mode='quiz')
        assert app.graph.get_state(config).values['quiz']['index']==1
    finally:app.close()


def test_unparseable_final_quiz_answer_does_not_complete_or_commit(tmp_path):
    app=setup_app(tmp_path)
    try:
        session='invalid-final-answer'
        app.turn(session,'learner','start a quiz',mode='quiz')
        for _ in range(2):app.turn(session,'learner','no real roots',mode='quiz')
        result=app.turn(session,'learner','banana',mode='quiz')
        quiz=app.graph.get_state({'configurable':{'thread_id':session}}).values['quiz']
        assert 'could not read' in result['reply'].lower()
        assert quiz['index']==2 and len(quiz['results'])==2
        assert app.conn.execute('SELECT COUNT(*) FROM applied_quizzes').fetchone()[0]==0
        assert app.conn.execute('SELECT COUNT(*) FROM mastery').fetchone()[0]==0
        result=app.turn(session,'learner','no real roots',mode='quiz')
        assert 'Quiz finished:' in result['reply']
        assert app.conn.execute('SELECT COUNT(*) FROM applied_quizzes').fetchone()[0]==1
    finally:app.close()
