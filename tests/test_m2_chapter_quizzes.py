"""Chapter quiz approvals, exact scoring, plan isolation and replay safety."""
import json
from fractions import Fraction
import pytest
from fastapi.testclient import TestClient
from tutor.app import TutorApp
from tutor.seed import seed_learner
from tutor.toolbus import CallContext, ToolCallError
from tutor_api.main import create_app


def test_new_quiz_pack_exact_arithmetic_and_policy():
    from tutor.config import ROOT
    from tutor.mathcore import compute_key
    from tutor.question_catalog import allowed
    questions=json.loads((ROOT/'content/milestone2_dev/chapter_quiz_items.json').read_text(encoding='utf-8-sig'))
    assert len(questions)==6 and len({q['question_id'] for q in questions})==6
    public=[json.loads(line) for line in (ROOT/'content/dataset-v0.10.0/practice_questions.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    assert not {q['question_id'] for q in questions} & {q['question_id'] for q in public}
    assert not {(q['problem']['task_type'],json.dumps(q['problem']['givens'],sort_keys=True)) for q in questions} & {(q['problem']['task_type'],json.dumps(q['problem']['givens'],sort_keys=True)) for q in public}
    expected=[Fraction(-17),Fraction(34),Fraction(48),Fraction(8,17),Fraction(7,25),Fraction(9,40)]
    for item,value in zip(questions,expected):
        assert item['review_status']=='pending_human_review' and 'key' not in item
        assert allowed(item,'quiz') and not allowed(item,'practice')
        key=compute_key(item['problem'])
        assert key['verified'] and Fraction(key['key']['value'])==value


@pytest.mark.parametrize(('chapter','concept','correct_answers'),[
    ('arithmetic_progressions','ap03',['-17','34','48']),
    ('trigonometry','tr01',['8/17','7/25','9/40']),
])
def test_connected_quiz_replans_only_its_chapter_and_learner(tmp_path,monkeypatch,chapter,concept,correct_answers):
    monkeypatch.delenv('TUTOR_BETA_CONFIG',raising=False)
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    seed_learner(app.conn,'A',{'alias':'A'});seed_learner(app.conn,'B',{'alias':'B'})
    try:
        with TestClient(create_app(tutor=app,tokens='a:student:A,b:student:B,t:teacher:T'),base_url='http://localhost') as client:
            teacher={'Authorization':'Bearer t'}
            def turn(user,sid,text,mode='quiz'):
                r=client.post('/chat',headers={'Authorization':'Bearer '+user},json={'session_id':sid,'chapter':chapter,'mode':mode,'text':text})
                assert r.status_code==200,r.text
                return r.json()
            assert turn('a','pending','start a quiz')['quiz_active'] is False
            proposal=client.post('/teacher/proposals',headers=teacher,json={'concept_id':concept,'mode':'quiz'})
            assert proposal.status_code==200,proposal.text
            payload=proposal.json()['proposal']['payload'];assert len(payload['items'])==3
            assert all(q['chapter']==chapter and q['mode_policy']['allowed_modes']==['quiz','diagnostic'] for q in payload['items'])
            assert turn('a','unapproved','start a quiz')['quiz_active'] is False
            approved=client.post('/teacher/proposals/'+proposal.json()['set_id']+'/approve',headers=teacher)
            assert approved.status_code==200 and approved.json()['status']=='published'
            # The quadratic plan is a separate pre-existing record.
            quadratic=app.turn('quadratic','A','hello')['plan']
            begun=turn('a','quiz-a','start a quiz');assert begun['quiz_active'] is True
            quiz_id=app.graph.get_state({'configurable':{'thread_id':'quiz-a'}}).values['quiz']['quiz_id']
            unreadable=turn('a','quiz-a','I do not know')
            assert unreadable['quiz_active'] and 'not been scored' in unreadable['reply']
            turn('a','quiz-a','999')
            turn('a','quiz-a',correct_answers[1])
            result=turn('a','quiz-a',correct_answers[2])
            assert result['quiz_active'] is False and result['plan']['chapter']==chapter
            assert result['plan']['replan_reason']=='after quiz: scored 2/3'
            assert result['plan']['steps'][0]['action']=='review'
            assert payload['items'][0]['question_id'] in result['plan']['steps'][0]['evidence_question_ids']
            assert app.conn.execute('SELECT count(*) FROM applied_quizzes WHERE quiz_id=?',(quiz_id,)).fetchone()[0]==1
            profile=client.get('/learners/A',headers={'Authorization':'Bearer a'}).json()
            assert profile['plan']==quadratic and profile['topic_plans'][chapter]==result['plan']
            before=client.get('/learners/B',headers={'Authorization':'Bearer b'}).json()
            assert chapter not in before['topic_plans']
            assert turn('b','quiz-b','start a quiz')['quiz_active'] is True
            for answer in correct_answers:other=turn('b','quiz-b',answer)
            assert other['plan']['replan_reason']=='after quiz: scored 3/3'
            assert all(step['action']=='practise' for step in other['plan']['steps'])
            assessed = {cid for item in payload['items'] for cid in item['problem']['concept_ids']}
            assert other['plan']['steps'] and all(step['concept_id'] not in assessed for step in other['plan']['steps'])
            assert set(other['plan']['quiz_passed']) == assessed
            assert client.get('/learners/A',headers={'Authorization':'Bearer a'}).json()['topic_plans'][chapter]==result['plan']
            assert client.get('/learners/A',headers={'Authorization':'Bearer b'}).status_code==403
    finally:app.close()


def test_topic_quiz_application_rollback_replay_and_chapter_binding(tmp_path,monkeypatch):
    from tutor import learner
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    seed_learner(app.conn,'A',{'alias':'A'})
    context=CallContext(session_id='atomic',learner_id='A')
    results=[{'question_id':'synthetic-q','correct':False,'scorable':True,'concept_ids':['ap03'],'kind':'scalar'}]
    args={'learner_id':'A','quiz_id':'c'*32,'results':results,'chapter':'arithmetic_progressions'}
    try:
        with pytest.raises(ToolCallError):
            app.bus.call(context,'study_planner','learner-store','apply_quiz',{**args,'results':[{**results[0],'scorable':False}]})
        original=learner.make_topic_plan
        def fail(*a,**k):raise RuntimeError('synthetic plan failure')
        monkeypatch.setattr(learner,'make_topic_plan',fail)
        with pytest.raises(ToolCallError):app.bus.call(context,'study_planner','learner-store','apply_quiz',args)
        for table in ('mastery','learner_events','applied_quizzes','topic_plans'):
            assert app.conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==0
        monkeypatch.setattr(learner,'make_topic_plan',original)
        assert app.bus.call(context,'study_planner','learner-store','apply_quiz',args)['applied']
        before=app.conn.execute('SELECT plan_json FROM topic_plans').fetchone()[0]
        assert not app.bus.call(context,'study_planner','learner-store','apply_quiz',args)['applied']
        assert app.conn.execute('SELECT plan_json FROM topic_plans').fetchone()[0]==before
        with pytest.raises(ToolCallError):
            app.bus.call(context,'study_planner','learner-store','apply_quiz',{**args,'chapter':'trigonometry'})
        with pytest.raises(ToolCallError):
            app.bus.call(context,'study_planner','learner-store','apply_quiz',{**args,'chapter':'quadratic_equations'})
    finally:app.close()


def test_interrupted_topic_quiz_replay_does_not_overwrite_newer_plan(tmp_path,monkeypatch):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    seed_learner(app.conn,'A',{'alias':'A'})
    try:
        proposal=app.propose_set('ap03',mode='quiz');app.decide(proposal['set_id'],'approve','synthetic')
        kwargs={'mode':'quiz','chapter':'arithmetic_progressions'}
        app.turn('interrupted','A','start a quiz',**kwargs)
        app.turn('interrupted','A','-17',**kwargs);app.turn('interrupted','A','34',**kwargs)
        original=app._call;failed=False
        def crash_after_commit(state,node,role,server,tool,args):
            nonlocal failed
            out=original(state,node,role,server,tool,args)
            if not failed and node=='update_memory' and tool=='apply_quiz':
                failed=True
                raise RuntimeError('synthetic interruption after commit')
            return out
        monkeypatch.setattr(app,'_call',crash_after_commit)
        with pytest.raises(RuntimeError):app.turn('interrupted','A','48',**kwargs)
        app.turn('newer','A','start a quiz',**kwargs)
        for answer in ('0','0','0'):latest=app.turn('newer','A',answer,**kwargs)
        assert latest['plan']['version']==2
        before=app.conn.execute('SELECT plan_json FROM topic_plans').fetchone()[0]
        events=app.conn.execute('SELECT count(*) FROM learner_events').fetchone()[0]
        assert app.resume('interrupted')
        assert app.conn.execute('SELECT plan_json FROM topic_plans').fetchone()[0]==before
        assert app.conn.execute('SELECT count(*) FROM learner_events').fetchone()[0]==events
    finally:app.close()


def test_existing_store_upgrade_preserves_quadratic_plan(tmp_path):
    import sqlite3
    from tutor import store
    path=tmp_path/'legacy.db'
    old=sqlite3.connect(path)
    old.execute('CREATE TABLE plans (learner_id TEXT PRIMARY KEY, plan_json TEXT, version INTEGER, updated_at REAL)')
    old.execute('INSERT INTO plans VALUES (?,?,?,?)',('synthetic', '{"version":7}',7,1.0))
    old.commit();old.close()
    upgraded=store.connect(path)
    try:
        assert upgraded.execute('SELECT plan_json FROM plans WHERE learner_id=?',('synthetic',)).fetchone()[0]=='{"version":7}'
        assert upgraded.execute('SELECT count(*) FROM topic_plans').fetchone()[0]==0
    finally:upgraded.close()


def test_beta_math_adapter_loads_new_quiz_items_without_practice_permission():
    from tutor.config import ROOT
    from socrates_beta.maths import CheckedMaths
    from tutor.question_catalog import allowed
    maths=CheckedMaths(ROOT)
    for qid in ('m2_demo_quiz_ap_01','m2_demo_quiz_tr_01'):
        item=maths.items[qid]
        assert allowed(item,'quiz') and not allowed(item,'practice')
        assert maths.key(qid)['kind']=='scalar'
