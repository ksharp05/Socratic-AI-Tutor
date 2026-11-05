"""Public AP integration, with independent exact-arithmetic oracles; no private data."""
from fractions import Fraction
import pytest
from tutor import mathcore
from tutor.app import TutorApp
from tutor.seed import seed_learner
from tutor.question_catalog import graph_items,allowed
from fastapi.testclient import TestClient
from tutor_api.main import create_app

NEW={'ap_first','ap_difference','ap_count','ap_mean','ap_ledger_term'}
ITEMS=[i for i in graph_items() if allowed(i,'practice') and i['problem']['task_type'] in NEW]

def oracle(item):
    task=item['problem']['task_type'];g=item['problem']['givens']
    if task=='ap_first':
        v=Fraction(g['term'])
        for _ in range(g['n']-1):v-=g['d']
        return {'kind':'scalar','value':str(v)}
    if task=='ap_difference':return {'kind':'scalar','value':str(Fraction(g['term_n']-g['term_m'],g['n']-g['m']))}
    if task=='ap_count':
        gap=Fraction(g['last']-g['a'],g['d']);n=gap+1
        return {'kind':'finite_set','values':[str(n)] if n.denominator==1 and n>0 else [],'unit':'terms'}
    if task=='ap_mean':return {'kind':'scalar','value':str(Fraction(g['left']+g['right'],2))}
    return {'kind':'scalar','value':str(Fraction(g['prefix_sum'])-Fraction(g['previous_sum']))}

@pytest.mark.parametrize('item',ITEMS,ids=lambda i:i['question_id'])
def test_each_new_public_item_has_an_exact_checked_answer(item):
    expected=oracle(item);key=mathcore.compute_key(item['problem'])
    assert key['verified'] and mathcore.grade(expected,key['key'])['correct']
    assert mathcore.diagnose_response(item['problem'],key['key'],expected)==[]

@pytest.mark.parametrize('task',sorted(NEW))
def test_actual_api_keeps_new_family_gated_checks_attempt_and_revokes(tmp_path,task):
    item=next(i for i in ITEMS if i['problem']['task_type']==task)
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'t.db'),checkpoint_name=str(tmp_path/'c.db'))
    seed_learner(app.conn,'ap-expansion',{'alias':'Synthetic public integration'})
    try:
        with TestClient(create_app(tutor=app,tokens='s:student:ap-expansion')) as client:
            def turn(text):
                response=client.post('/chat',headers={'Authorization':'Bearer s'},json={'session_id':'expanded','chapter':'arithmetic_progressions','text':text})
                assert response.status_code==200,response.text
                return response.json()
            assert turn('practice')['active_item'] is None
            proposal=app.propose_set(item['problem']['concept_ids'][0])
            app.decide(proposal['set_id'],'edit','synthetic-only',question_ids=[item['question_id']])
            assert turn('practice')['active_item'] is None
            app.decide(proposal['set_id'],'approve','synthetic-only')
            first=turn('practice');assert first['active_item']==item['question_id']
            if task=='ap_count':assert 'positive integer count' in first['reply'] and 'roots' not in first['reply']
            hint=turn('hint');assert hint['checks']['ok'] and hint['active_item']==item['question_id']
            answer=oracle(item);text=answer.get('value') or (answer['values'][0] if answer.get('values') else 'no valid term count')
            done=turn(('There are '+text+' terms') if task=='ap_count' and answer['values'] else text)
            assert done['route']=='grade' and done['active_item'] is None and 'Correct:' in done['reply']
            assert app.conn.execute('SELECT count(*) FROM applied_quizzes').fetchone()[0]==0
            assert turn('practice')['active_item']==item['question_id']
            app.decide(proposal['set_id'],'edit','synthetic-only',question_ids=[item['question_id']])
            assert turn(text)['route']=='question_revoked'
    finally:app.close()

@pytest.mark.parametrize('text',['5','There are 5 terms.','The count is 5','n=5'])
def test_count_parser_accepts_numeric_count_language(text):
    key={'kind':'finite_set','values':['5'],'unit':'terms'};parsed=mathcore.parse_answer(text,key)
    assert parsed['ok'] and mathcore.grade(parsed['typed'],key)['correct']

def test_no_valid_count_is_not_root_language():
    key={'kind':'finite_set','values':[],'unit':'terms'}
    assert mathcore.leak_check('There is no valid term count.',key)['leak']
    assert not mathcore.leak_check('Which term positions are possible?',key)['leak']
    parsed=mathcore.parse_answer('no real roots',key)
    assert not parsed['ok'] or not mathcore.grade(parsed['typed'],key)['correct']
