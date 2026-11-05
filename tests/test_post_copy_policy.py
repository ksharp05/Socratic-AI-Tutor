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
