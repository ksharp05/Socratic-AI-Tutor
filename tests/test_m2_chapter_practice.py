"""Teacher-approved AP and trigonometry practice stays chapter-scoped and checked."""
import pytest
from fastapi.testclient import TestClient
from tutor.app import TutorApp
from tutor.seed import seed_learner
from tutor_api.main import create_app


@pytest.mark.parametrize(('chapter','concept','question_id','wrong','correct','prefix'), [
    ('arithmetic_progressions','ap03','q_3ab4d2ba6344efe60125','-105','-110','ap'),
    ('trigonometry','tr01','q_49922f00fe38892497ab','5/13','13/5','tr'),
])
def test_teacher_approved_practice_checks_answers_and_updates_matching_concepts(tmp_path,monkeypatch,chapter,concept,question_id,wrong,correct,prefix):
    monkeypatch.delenv('TUTOR_BETA_CONFIG',raising=False)
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    seed_learner(app.conn,'student',{'alias':'Synthetic'})
    headers={'Authorization':'Bearer student-token'}
    teacher={'Authorization':'Bearer teacher-token'}
    try:
        with TestClient(create_app(tutor=app,tokens='student-token:student:student,teacher-token:teacher:teacher'),base_url='http://localhost') as client:
            def turn(session,text,mode='practice'):
                response=client.post('/chat',headers=headers,json={'session_id':session,'chapter':chapter,'text':text,'mode':mode})
                assert response.status_code==200,response.text
                return response.json()
            assert turn('before','practice')['active_item'] is None
            proposal=client.post('/teacher/proposals',headers=teacher,json={'concept_id':concept,'mode':'practice'})
            assert proposal.status_code==200,proposal.text
            set_id=proposal.json()['set_id']
            edit=client.post(f'/teacher/proposals/{set_id}/edit',headers=teacher,json={'question_ids':[question_id]})
            assert edit.status_code==200,edit.text
            assert turn('pending','practice')['active_item'] is None
            approved=client.post(f'/teacher/proposals/{set_id}/approve',headers=teacher)
            assert approved.status_code==200 and approved.json()['status']=='published',approved.text
            first=turn('exercise','practice')
            assert first['active_item']==question_id and first['plan'] is None
            assert 'exact value' in first['reply'] and 'no real roots' not in first['reply']
            hint=turn('exercise','hint')
            assert hint['citations'] and all(c['passage_id'].startswith('normalized:'+prefix) for c in hint['citations'])
            assert correct not in hint['reply']
            attempt=turn('exercise',wrong)
            assert attempt['route']=='grade' and attempt['active_item']==question_id
            assert correct not in attempt['reply']
            assert app.conn.execute('SELECT count(*) FROM mastery WHERE learner_id=? AND concept_id LIKE ?',('student',prefix+'%')).fetchone()[0]>0
            success=turn('exercise',('My answer is ' if prefix=='ap' else "I think it's " )+correct)
            assert success['route']=='grade' and success['active_item'] is None
            assert 'Correct:' in success['reply'] and "miss a root" not in success['reply']
            assert success['plan'] is None
            quiz=turn('no-quiz','start a quiz','quiz')
            assert quiz['quiz_active'] is False and 'no teacher-approved quiz' in quiz['reply'].lower()
            assert turn('revoked','practice')['active_item']==question_id
            revoked=client.post(f'/teacher/proposals/{set_id}/edit',headers=teacher,json={'question_ids':[question_id]})
            assert revoked.status_code==200 and revoked.json()['status']=='pending'
            outcome=turn('revoked',correct)
            assert outcome['route']=='question_revoked' and outcome['active_item'] is None
            assert 'Correct:' not in outcome['reply']
    finally:
        app.close()


def test_new_public_practice_pool_is_explicitly_scoped():
    from tutor.question_catalog import graph_items,allowed
    extra=[q for q in graph_items() if q['chapter'] in ('arithmetic_progressions','trigonometry') and allowed(q,'practice')]
    assert len(extra)==320
    assert {q['problem']['task_type'] for q in extra}=={'ap_term','ap_sum','ap_first','ap_difference','ap_count','ap_mean','ap_ledger_term','trig_triangle_ratio'}
    assert all(q['answer_contract']['allowed_kinds']==(['finite_set'] if q['problem']['task_type']=='ap_count' else ['scalar']) and allowed(q,'practice') and not allowed(q,'quiz') for q in extra)
    assert all(q['review_status']=='pending_human_review' for q in extra)


def test_public_candidate_answers_against_independent_exact_arithmetic():
    from fractions import Fraction
    from tutor import mathcore
    from tutor.question_catalog import graph_items, allowed
    questions=[q for q in graph_items() if allowed(q,'practice') and q['problem']['task_type'] in {'ap_term','ap_sum','trig_triangle_ratio'}]
    assert len(questions)==120
    for question in questions:
        problem=question['problem'];g=problem['givens'];task=problem['task_type']
        if task=='ap_term':
            expected=Fraction(g['a']+sum(g['d'] for _ in range(g['n']-1)))
        elif task=='ap_sum':
            expected=Fraction(sum(g['a']+i*g['d'] for i in range(g['n'])))
        else:
            assert g['opposite']**2+g['adjacent']**2==g['hypotenuse']**2
            opposite,adjacent=g['opposite'],g['adjacent']
            if g['reference']=='C':opposite,adjacent=adjacent,opposite
            hypotenuse=g['hypotenuse']
            ratios={'sin':(opposite,hypotenuse),'cos':(adjacent,hypotenuse),'tan':(opposite,adjacent),
                    'csc':(hypotenuse,opposite),'sec':(hypotenuse,adjacent),'cot':(adjacent,opposite)}
            expected=Fraction(*ratios[g['ratio']])
        result=mathcore.compute_key(problem)
        assert result['verified'] and Fraction(result['key']['value'])==expected,question['question_id']
        checked=mathcore.grade({'kind':'scalar','value':str(expected)},result['key'])
        assert checked['scorable'] and checked['correct'],question['question_id']
