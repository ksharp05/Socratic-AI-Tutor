"""Measurement-policy regressions for known collisions and explicit disclosures, no model calls."""
import pytest
from tutor_eval import post_copy_policy as policy


def item(qid='post', answer='17', *, prompt='Find the sum of the first five terms of this progression.'):
    return {'question_id':qid,'prompt':prompt,'answer':{'kind':'scalar','value':answer},
            'problem':{'task_type':'ap_sum','givens':{'a':1,'d':1,'n':5},'number_domain':'real'}}


def test_unseen_post_answer_match_does_not_enable_copying_or_become_semantic_pass():
    result=policy.classify('The value is 17.',item())
    assert result['legacy_level']=='full'
    assert result['decision']=='unattributed_full_answer_match'
    assert result['copy_eligible'] is False and result['semantic_disclosure']=='unreviewed'
    assert result['human_label'] is None


def test_exact_post_question_and_answer_still_enable_copying():
    post=item();reply=post['prompt']+' The answer is 17.'
    assert policy.classify(reply,post)['copy_eligible'] is True


def test_answer_after_prior_explicit_question_exposure_enables_copying():
    result=policy.classify('The answer is 17.',item(),previously_exposed=True)
    assert result['copy_eligible'] is True


def test_identical_registered_problem_with_different_id_is_context_evidence():
    post=item();active={**post,'question_id':'practice-alias','prompt':'Add the first five terms of this AP.'}
    reply=active['prompt']+' The sum is 17.'
    assert policy.classify(reply,post,active_item=active)['copy_eligible'] is True
    other={**active,'problem':{**active['problem'],'givens':{'a':100,'d':4,'n':8}}}
    assert policy.classify(reply,post,active_item=other)['copy_eligible'] is False


def test_active_problem_registry_alone_is_not_dialogue_exposure():
    post=item();active={**post,'question_id':'practice-alias','prompt':'A different wording for the AP question.'}
    assert not policy.classify('17',post,active_item=active)['copy_eligible']


@pytest.mark.parametrize('answer',['-5','3/4','sqrt(3)/2'])
def test_registered_app_format_numbers_do_not_enable_post_copying(answer):
    post=item(answer=answer);active=item('practice',answer='42',prompt='Find the fourth term of the sequence shown.')
    reply='Practice (medium): '+active['prompt']+'\n'+policy.OWNED_FORMAT_INSTRUCTIONS[0]+" Type 'hint' if you're stuck."
    result=policy.classify(reply,post,active_item=active)
    assert result['removed_owned_format'] and result['legacy_level']=='full'
    assert result['decision']=='match_only_in_owned_format' and not result['copy_eligible']


def test_format_exclusion_does_not_hide_an_appended_real_answer():
    post=item(answer='-5');active={**post,'question_id':'practice-alias'}
    reply='Practice (medium): '+post['prompt']+'\n'+policy.OWNED_FORMAT_INSTRUCTIONS[0]+" Type 'hint' if you're stuck. The answer is -5."
    result=policy.classify(reply,post,active_item=active)
    assert result['removed_owned_format'] and result['copy_eligible']


def test_format_exclusion_never_removes_an_entire_question_with_an_answer_assertion():
    post=item(answer='17');active={**post,'question_id':'practice-alias','prompt':'The answer is 17. Here is the problem.'}
    reply='Practice (medium): '+active['prompt']+'\n'+policy.OWNED_FORMAT_INSTRUCTIONS[0]+" Type 'hint' if you're stuck."
    assert policy.classify(reply,post,active_item=active)['copy_eligible']


def test_missing_registered_prompt_does_not_grant_format_exemption():
    post=item(answer='-5');active=item('unrelated',prompt='This registered prompt was never displayed.')
    reply='Practice: '+policy.OWNED_FORMAT_INSTRUCTIONS[0]+" Type 'hint' if you're stuck."
    result=policy.classify(reply,post,active_item=active)
    assert not result['removed_owned_format'] and not result['copy_eligible']
    assert result['semantic_disclosure']=='unreviewed'


def test_echo_of_student_answer_is_not_new_copying():
    post=item();result=policy.classify(post['prompt']+' The value is 17.',post,produced=[post['answer']])
    assert not result['copy_eligible']


def test_context_bound_session_filters_only_unattributed_post_copying():
    from types import SimpleNamespace
    from tutor_eval import harness
    calls=[]
    class App:
        def turn(self,*args,**kwargs):
            calls.append((args,kwargs))
            return {'reply':'The value is 17.','active_item':None}
    post=item();student=SimpleNamespace(told={'post','registered-practice'})
    with policy.session_scope(App(),[post],{}) as measurement:
        measurement.app.turn('session','learner','Please guide me.',chapter='arithmetic_progressions')
        harness._post_produced(post,{})
        measurement.before_quiz(student,[post])
        assert student.told=={'registered-practice'}
        assert measurement.summary()['decision_counts']=={'unattributed_full_answer_match':1}
        assert measurement.summary()['semantic_disclosure']=='unreviewed'
    assert policy.current_measurement() is None
    assert calls==[(('session','learner','Please guide me.'),{'chapter':'arithmetic_progressions'})]


def test_context_bound_session_retains_real_exposed_post_answer():
    from types import SimpleNamespace
    from tutor_eval import harness
    post=item()
    class App:
        def turn(self,*args,**kwargs):return {'reply':post['prompt']+' The value is 17.','active_item':None}
    student=SimpleNamespace(told={'post'})
    with policy.session_scope(App(),[post],{}) as measurement:
        measurement.app.turn('s','l','Please guide me.')
        harness._post_produced(post,{})
        measurement.before_quiz(student,[post])
        assert student.told=={'post'}
        assert measurement.summary()['post_ids_allowed_to_copy']==['post']


def test_echo_does_not_convert_an_earlier_unattributed_flag_into_copy_eligibility():
    from types import SimpleNamespace
    from tutor_eval import harness
    post=item()
    class App:
        reply='The value is 17.'
        def turn(self,*args,**kwargs):return {'reply':self.reply,'active_item':None}
    app=App();student=SimpleNamespace(told={'post'})
    with policy.session_scope(app,[post],{}) as measurement:
        measurement.app.turn('s','l','Guide me.')
        harness._post_produced(post,{})
        app.reply=post['prompt']+' The value is 17.'
        measurement.app.turn('s','l','I already found 17.')
        harness._post_produced(post,{'post':{'problem':post['problem'],'produced':[post['answer']]}})
        measurement.before_quiz(student,[post])
        assert not student.told


def test_pre_quiz_and_exception_reset_are_isolated():
    from types import SimpleNamespace
    post=item();student=SimpleNamespace(told={'post','practice'})
    class App:
        def turn(self,*args,**kwargs):raise RuntimeError('synthetic failure')
    with pytest.raises(RuntimeError,match='synthetic failure'):
        with policy.session_scope(App(),[post],{}) as measurement:
            measurement.before_quiz(student,[{**post,'question_id':'pre'}])
            assert student.told=={'post','practice'}
            measurement.app.turn('s','l','Hello')
    assert policy.current_measurement() is None


def test_concurrent_measurement_contexts_do_not_share_post_ids():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from types import SimpleNamespace
    from tutor_eval import harness
    barrier=Barrier(2)
    def work(qid):
        post=item(qid=qid)
        class App:
            def turn(self,*args,**kwargs):return {'reply':post['prompt']+' The value is 17.','active_item':None}
        with policy.session_scope(App(),[post],{}) as measurement:
            barrier.wait(timeout=10)
            measurement.app.turn('s','l','Guide me.')
            harness._post_produced(post,{})
            student=SimpleNamespace(told={qid})
            measurement.before_quiz(student,[post])
            assert measurement.summary()['post_ids_allowed_to_copy']==[qid]
        assert policy.current_measurement() is None
        return qid
    with ThreadPoolExecutor(max_workers=2) as workers:
        assert set(workers.map(work,['post-a','post-b']))=={'post-a','post-b'}


def test_unknown_policy_is_rejected_before_data_or_model_initialization(tmp_path):
    from tutor_eval import harness
    config=tmp_path/'invalid.toml';config.write_text('[run]\npost_copy_policy="not-a-policy"\n')
    with pytest.raises(ValueError,match='Unknown post-copy'):harness.run(config)


def test_opt_in_harness_records_policy_and_private_copy_audit(tmp_path,monkeypatch):
    import json
    from tutor.config import ROOT
    from tutor_eval import harness
    monkeypatch.setenv('TUTOR_LLM','stub')
    text=(ROOT/'eval/configs/dev_smoke.toml').read_text(encoding='utf-8')
    text=text.replace('[run]','[run]\npost_copy_policy="'+policy.POLICY+'"',1)
    config=tmp_path/'context-policy.toml';config.write_text(text,encoding='utf-8')
    run=harness.run(config,out_dir=tmp_path/'runs')
    manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    sessions=[json.loads(line) for line in (run/'sessions.jsonl').read_text(encoding='utf-8').splitlines()]
    assert manifest['post_copy_policy']==policy.POLICY and manifest['provider_budget'] is None
    assert 'tutor_eval/post_copy_policy.py' in manifest['code_sha256']
    assert all(s['llm_calls']==0 and s['post_copy_measurement']['human_labels']==0 for s in sessions)
    assert all(s['post_copy_measurement']['semantic_disclosure']=='unreviewed' for s in sessions)


def test_model_calls_are_attributed_to_the_current_turn_and_session():
    from pathlib import Path
    from tutor import store
    post=item()
    class App:
        conn=store.connect(Path(':memory:'))
        def turn(self,session_id,*args,**kwargs):
            store.trace(self.conn,session_id='other-session',node='unrelated',role='tutor',kind='llm',name='fake')
            store.trace(self.conn,session_id=session_id,node='tutor',role='tutor',kind='llm',name='fake')
            return {'reply':'Which step would you check next?','route':'tutor','active_item':None}
    app=App()
    try:
        with policy.session_scope(app,[post],{}) as measurement:
            measurement.app.turn('session','learner','Guide me.')
            measurement.app.turn('session','learner','Continue.')
            observed=measurement.model_observations
            assert [r['model_calls'] for r in observed]==[1,1]
            assert all(r['trace_observed'] and r['model_nodes']==['tutor'] for r in observed)
    finally:app.conn.close()


def test_pending_v3_budget_receipt_cannot_create_an_extension_wallet(tmp_path):
    import json
    from tutor_eval.provider_budget import ProviderBudget
    receipt=tmp_path/'approval.json';receipt.write_text(json.dumps({'status':'pending'}))
    wallet=tmp_path/'pilot.json'
    with pytest.raises(ValueError,match='approval'):
        ProviderBudget(wallet,max_calls=80,max_usd=.05,prior_calls=1036,approval_receipt=receipt)
    assert not wallet.exists()
