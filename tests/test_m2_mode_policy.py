"""Question-use policy is enforced at selection and when resuming checks."""
import json
from pathlib import Path

from tutor.app import TutorApp
from tutor.seed import seed_learner
from tutor.toolbus import CallContext
from socrates_beta.maths import AssessmentService,CheckedMaths
from socrates_beta.repository import Repository

ROOT=Path(__file__).resolve().parents[1]


def test_graph_quiz_requires_approved_quiz_mode_questions(tmp_path):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        seed_learner(app.conn,'L-A',{'alias':'Synthetic'})
        practice=app.propose_set('qe04');app.decide(practice['set_id'],'approve','synthetic-teacher')
        response=app.turn('synthetic-policy','L-A','start a quiz',mode='quiz')
        assert "no teacher-approved quiz" in response['reply'].lower()
        assert not app.graph.get_state({'configurable':{'thread_id':'synthetic-policy'}}).values.get('quiz')
        proposal=app.propose_set('qe04',mode='quiz');app.decide(proposal['set_id'],'approve','synthetic-teacher')
        payload=app.proposal(proposal['set_id'])['payload']
        assert all('quiz' in item['mode_policy']['allowed_modes'] and 'practice' not in item['mode_policy']['allowed_modes'] for item in payload['items'])
        response=app.turn('synthetic-policy','L-A','start a quiz',mode='quiz')
        quiz=app.graph.get_state({'configurable':{'thread_id':'synthetic-policy'}}).values['quiz']
        allowed={item['question_id'] for item in payload['items']}
        assert {item['question_id'] for item in quiz['items']}<=allowed
        visible=app.bus.call(CallContext(session_id='synthetic-check'),'question_setter','question-bank','list_published',{'mode':'practice'})['items']
        assert all('practice' in item['mode_policy']['allowed_modes'] for item in visible)
    finally:app.close()


def test_standalone_quiz_and_diagnostic_only_use_permitted_items(tmp_path):
    repo=Repository(tmp_path/'beta.sqlite');maths=CheckedMaths(ROOT)
    for i,mode in enumerate(('quiz','diagnostic')):
        session=repo.create_session(f'synthetic-owner-{i}','synthetic-dataset',
            {'grade':10,'subject':'Mathematics','book':None,'unit':None},'Synthetic')
        check=AssessmentService(repo,maths).start(session,mode)
        assert mode in maths.items[check['item']['id']]['mode_policy']['allowed_modes']
        assert check['item']['id'].startswith('m2_demo_quiz_')


def test_standalone_old_practice_only_quiz_is_cancelled_before_grading(tmp_path):
    repo=Repository(tmp_path/'beta.sqlite');maths=CheckedMaths(ROOT);service=AssessmentService(repo,maths)
    session=repo.create_session('synthetic-owner','synthetic-dataset',
        {'grade':10,'subject':'Mathematics','book':None,'unit':None},'Synthetic')
    practice=service.start(session,'practice')
    with repo.connect() as conn:conn.execute("UPDATE assessments SET mode='quiz' WHERE id=?",(practice['id'],))
    outcome=service.submit('synthetic-owner',practice['id'],'x = 3','synthetic-request')
    assert outcome['status']=='question_revoked' and outcome['assessment']['item'] is None
    assert 'summary' not in outcome['assessment'] and repo.observations('synthetic-owner')==[]


def test_old_unbound_teacher_approval_is_not_visible(tmp_path):
    from tutor import store
    from tutor.mcp_servers.question_bank import payload_hash
    from tutor.setup_content import load
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        item=load('practice')[0]
        payload={'set_id':'legacy','concept_id':'qe04','revision':1,'items':[item]}
        digest=payload_hash(payload);raw=store.dumps(payload);now=store.now()
        app.conn.execute('INSERT INTO proposals VALUES (?,?,?,?,?,?,?,?,?)',('legacy','qe04',raw,digest,'published',1,'legacy-thread','legacy',now))
        app.conn.execute('INSERT INTO published VALUES (?,?,?,?,?,?)',('legacy',raw,digest,'synthetic-teacher','teacher_approved',now))
        visible=app.bus.call(CallContext(session_id='synthetic-check'),'question_setter','question-bank','list_published',{})['items']
        assert not any(item['set_id']=='legacy' for item in visible)
    finally:app.close()


def test_quiz_only_items_are_not_served_as_practice(tmp_path):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        seed_learner(app.conn,'L-A',{'alias':'Synthetic'})
        quiz=app.propose_set('qe04',mode='quiz');app.decide(quiz['set_id'],'approve','synthetic-teacher')
        reply=app.turn('quiz-only-practice','L-A','practice')
        assert reply['active_item'] is None and 'no teacher-approved practice' in reply['reply'].lower()
    finally:app.close()


def test_legacy_graph_quiz_with_practice_only_item_is_revoked(tmp_path):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        seed_learner(app.conn,'L-A',{'alias':'Synthetic'})
        proposal=app.propose_set('qe04');app.decide(proposal['set_id'],'approve','synthetic-teacher')
        item=app.proposal(proposal['set_id'])['payload']['items'][0]
        app.turn('legacy-quiz','L-A','hello')
        config={'configurable':{'thread_id':'legacy-quiz'}}
        quiz={'quiz_id':'d'*32,'items':[{'question_id':item['question_id'],'prompt':item['prompt'],
              'concept_ids':item['problem']['concept_ids'],'set_id':proposal['set_id'],
              'set_payload_sha256':proposal['payload_sha256'],'kind':item['answer_contract']['allowed_kinds'][0]}],
              'index':0,'results':[]}
        app.graph.update_state(config,{'quiz':quiz},as_node='respond')
        result=app.turn('legacy-quiz','L-A','no real roots',mode='quiz')
        assert result['route']=='question_revoked'
        assert app.graph.get_state(config).values['quiz'] is None
        assert app.conn.execute('SELECT COUNT(*) FROM applied_quizzes').fetchone()[0]==0
    finally:app.close()


def test_teacher_approval_binds_the_mode_policy(tmp_path):
    from tutor import store
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        proposal=app.propose_set('qe04',mode='quiz');approved=app.decide(proposal['set_id'],'approve','synthetic-teacher')
        payload=app.proposal(proposal['set_id'])['payload']
        payload['items'][0]['mode_policy']['allowed_modes'].append('practice')
        app.conn.execute('UPDATE proposals SET payload_json=? WHERE set_id=?',(store.dumps(payload),proposal['set_id']))
        assert app.try_publish(proposal['set_id'],approved['token'],'synthetic-teacher')['published'] is False
        visible=app.bus.call(CallContext(session_id='synthetic-check'),'question_setter','question-bank','list_published',{})['items']
        assert not any(item['set_id']==proposal['set_id'] for item in visible)
    finally:app.close()


def test_synthetic_quiz_questions_agree_with_independent_symbolic_solver():
    import sympy as sp
    from tutor.mathcore import compute_key
    items=json.loads((ROOT/'content/milestone2_dev/quiz_items.json').read_text(encoding='utf-8-sig'))
    assert len(items)==6 and len({item['question_id'] for item in items})==6
    x=sp.symbols('x')
    for item in items:
        assert 'key' not in item and item['review_status']=='pending_human_review'
        a,b,c=(item['problem']['givens'][name] for name in ('a','b','c'))
        result=compute_key(item['problem']);assert result['verified'] is True
        actual={sp.simplify(sp.sympify(value)) for value in result['key']['values']}
        expected=set(sp.solveset(a*x*x+b*x+c,x,domain=sp.S.Reals))
        assert actual==expected,item['question_id']


def test_teacher_approval_binds_review_and_source_metadata(tmp_path):
    import copy
    from tutor import store
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        for field,value in [('review_status','human_reviewed'),('chapter','other_chapter'),
                            ('supporting_passage_ids',['synthetic:changed'])]:
            proposal=app.propose_set('qe04',mode='quiz');approved=app.decide(proposal['set_id'],'approve','synthetic-teacher')
            payload=copy.deepcopy(app.proposal(proposal['set_id'])['payload'])
            payload['items'][0][field]=value
            app.conn.execute('UPDATE proposals SET payload_json=? WHERE set_id=?',(store.dumps(payload),proposal['set_id']))
            assert app.try_publish(proposal['set_id'],approved['token'],'synthetic-teacher')['published'] is False
            visible=app.bus.call(CallContext(session_id='synthetic-check'),'question_setter','question-bank','list_published',{})['items']
            assert not any(item['set_id']==proposal['set_id'] for item in visible)
    finally:app.close()
