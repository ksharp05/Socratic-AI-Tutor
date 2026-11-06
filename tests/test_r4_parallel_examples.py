"""R4 parallel examples: public-family coverage, proof tampering and tool permissions."""
import copy
import pytest
from tutor import mathcore,parallel_examples
from socratic_data import math_kernel as mk
from tutor.question_catalog import graph_items,allowed
from tutor.toolbus import CallContext,ToolCallError
from tutor.app import TutorApp

ITEMS=[i for i in graph_items() if allowed(i,'practice')]

@pytest.mark.parametrize('item',ITEMS,ids=lambda i:i['question_id'])
def test_each_connected_item_gets_a_case_preserving_example_or_required_safe_fallback(item):
    key=mathcore.compute_key(item['problem']);assert key['verified']
    result=parallel_examples.generate(item,key['key'])
    task=item['problem']['task_type'];answer=key['key']
    # Explicit mathematical impossibilities: preserving these cases shares the active answer.
    conflict=(task=='quadratic_solve' and (not answer['values'] or any(mk.equivalent(v,'0') for v in answer['values'])))
    conflict=conflict or (task=='ap_count' and (not answer['values'] or any(mk.equivalent(v,'1') for v in answer['values'])))
    conflict=conflict or (answer['kind']=='scalar' and mk.equivalent(answer['value'],'0'))
    if conflict:
        assert not result['available'] and result['reason']=='preserved_case_conflicts_with_active_item_guard'
        return
    assert result['available'] and result['verified'],(item['question_id'],result)
    assert result['version']=='parallel-example-v3' and result['boundary_regime_preserved'] is True
    e=result['example'];assert e['problem']['task_type']==item['problem']['task_type']
    assert set(e['problem']['givens'])==set(item['problem']['givens'])
    assert parallel_examples.verify(e,item['problem'])
    assert not mathcore.grade(e['answer'],key['key'])['correct']
    if key['key']['kind']==e['answer']['kind']=='finite_set':assert not any(mk.equivalent(a,b) for a in key['key']['values'] for b in e['answer']['values'])
    assert not mathcore.leak_check(e['presentation'],key['key'])['leak']
    assert e['presentation'].count('?')==1 and result['teacher_review_status']=='not_reviewed'

@pytest.mark.parametrize('corruption',['result','operation','answer','presentation','givens'])
def test_step_or_presentation_tampering_is_not_verified(corruption):
    item=next(i for i in ITEMS if i['problem']['task_type']=='ap_term');key=mathcore.compute_key(item['problem'])['key']
    e=copy.deepcopy(parallel_examples.generate(item,key)['example'])
    if corruption=='result':e['worked_steps'][0]['result']='999'
    if corruption=='operation':e['worked_steps'][0]['operation']='add'
    if corruption=='answer':e['answer']['value']='999'
    if corruption=='presentation':e['presentation']+=' The original answer is 999.'
    if corruption=='givens':e['problem']['givens']['a']+=1
    assert not parallel_examples.verify(e)


def test_mcp_service_requires_code_owned_scope_and_never_returns_active_key(tmp_path):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'t.db'),checkpoint_name=str(tmp_path/'c.db'))
    item=next(i for i in ITEMS if i['problem']['task_type']=='ap_term')
    try:
        args={'question_ref':item['question_id']}
        for ctx in [CallContext('ordinary',node='tutor'),CallContext('quiz',node='quiz_answer'),CallContext('wrong',node='after_last_hint',parallel_example_for='another-question')]:
            with pytest.raises(ToolCallError,match='FORBIDDEN'):app.bus.call(ctx,'tutor','math-tools','generate_parallel_example',args)
        context=CallContext('parallel',node='after_last_hint',parallel_example_for=item['question_id'])
        result=app.bus.call(context,'tutor','math-tools','generate_parallel_example',args)
        assert result['available'] and 'active_key' not in result and 'key' not in result
        assert result['source_question_ref']==item['question_id']
        with pytest.raises(ToolCallError):app.bus.call(context,'grader','math-tools','generate_parallel_example',args)
    finally:app.close()


def test_unverified_original_key_fails_closed():
    item=next(i for i in ITEMS if i['problem']['task_type']=='ap_term')
    assert parallel_examples.generate(item,{'kind':'scalar','value':'999999999'})['available'] is False


def test_mcp_rejects_quiz_item_even_with_a_controller_scope(tmp_path):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'t.db'),checkpoint_name=str(tmp_path/'c.db'))
    q=next(i['question_id'] for i in graph_items() if allowed(i,'quiz') and not allowed(i,'practice'))
    try:
        context=CallContext('scoped',node='after_last_hint',parallel_example_for=q)
        with pytest.raises(ToolCallError,match='FORBIDDEN'):
            app.bus.call(context,'tutor','math-tools','generate_parallel_example',{'question_ref':q})
    finally:app.close()
