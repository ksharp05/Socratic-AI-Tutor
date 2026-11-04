"""Numerical error patterns remain provisional, especially when ambiguous."""
import pytest
from socratic_data.tasks import problem
from tutor import mathcore
from tutor.app import TutorApp
from tutor_eval.single_agent import SingleAgentTutor
from tutor.seed import seed_learner


@pytest.mark.parametrize(('ratio','reference','value','expected'),[
    ('cos','C','4/5',{'tr_m01'}),
    ('sin','A','4/5',{'tr_m02'}),
    ('tan','A','4/3',{'tr_m04'}),
    ('sin','C','3/5',{'tr_m01','tr_m02'}),
    ('tan','C','3/4',{'tr_m01','tr_m04'}),
    ('cos','C','3/5',set()),
    ('cos','C','17/19',set()),
])
def test_exact_ratio_candidates_and_ambiguity(ratio,reference,value,expected):
    p=problem('trig_triangle_ratio',{'opposite':3,'adjacent':4,'hypotenuse':5,'ratio':ratio,'reference':reference})
    key=mathcore.compute_key(p)['key']
    candidates=mathcore.diagnose_response(p,key,{'kind':'scalar','value':value})
    assert {c['misconception_id'] for c in candidates}==expected


@pytest.mark.parametrize('cls',[TutorApp,SingleAgentTutor])
def test_checked_trig_hypotheses_stay_suspected_and_do_not_replace_quadratic_plan(tmp_path,cls):
    app=cls(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    seed_learner(app.conn,'synthetic',{'alias':'Synthetic'})
    try:
        qe=app.turn('quadratic','synthetic','hello')['plan']
        proposal=app.propose_set('tr01');app.decide(proposal['set_id'],'edit','synthetic',question_ids=['q_4d0ac7929daa3f76c87d'])
        app.decide(proposal['set_id'],'approve','synthetic')
        app.turn('trig','synthetic','practice',chapter='trigonometry')
        for _ in range(2):
            response=app.turn('trig','synthetic','4/5',chapter='trigonometry')
            assert response['diagnosis']['misconception_id']=='tr_m01'
            assert 'What changes when the reference angle changes?' in response['reply']
            assert '3/5' not in response['reply']
        assert app.conn.execute("SELECT status FROM misconceptions WHERE learner_id='synthetic' AND misconception_id='tr_m01'").fetchone()[0]=='suspected'
        import json
        assert json.loads(app.conn.execute("SELECT plan_json FROM plans WHERE learner_id='synthetic'").fetchone()[0])==qe
        app.turn('trig','synthetic','hint',chapter='trigonometry')
        assert app.conn.execute("SELECT status FROM misconceptions WHERE misconception_id='tr_m01'").fetchone()[0]=='suspected'
        app.turn('trig','synthetic','3/5',chapter='trigonometry')
        app.turn('trig','synthetic','practice',chapter='trigonometry')
        app.turn('trig','synthetic','3/5',chapter='trigonometry')
        assert app.conn.execute("SELECT status FROM misconceptions WHERE misconception_id='tr_m01'").fetchone()[0]=='suspected'
    finally:app.close()


def test_ambiguous_ratio_requests_reasoning_without_recording_a_cause(tmp_path):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    seed_learner(app.conn,'synthetic',{'alias':'Synthetic'})
    try:
        proposal=app.propose_set('tr01');app.decide(proposal['set_id'],'edit','synthetic',question_ids=['q_d0599115712cee20789a'])
        app.decide(proposal['set_id'],'approve','synthetic')
        app.turn('trig','synthetic','practice',chapter='trigonometry')
        response=app.turn('trig','synthetic','17/145',chapter='trigonometry')
        assert response['diagnosis'] is None and 'more than one step' in response['reply']
        assert app.conn.execute('SELECT count(*) FROM misconceptions').fetchone()[0]==0
    finally:app.close()


def test_every_public_triangle_correct_answer_has_no_error_hypothesis():
    from tutor.question_catalog import graph_items, allowed
    items=[q for q in graph_items() if q['problem']['task_type']=='trig_triangle_ratio' and allowed(q,'practice')]
    assert len(items)==40
    for item in items:
        key=mathcore.compute_key(item['problem'])['key']
        assert mathcore.diagnose_response(item['problem'],key,key)==[]
