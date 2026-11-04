"""Behaviour and spending contracts for the isolated M3/M4 development study."""
import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from tutor import store
from tutor.seed import seed_learner
from tutor_eval import arms, harness, metrics
from tutor_eval.provider_budget import ProviderBudget, CappedClient, BudgetExceeded


def test_durable_budget_refuses_concurrent_overrun_and_counts_errors(tmp_path):
    path = tmp_path / 'budget.json'
    budget = ProviderBudget(path, max_calls=2, max_usd=.1, prior_calls=98)
    class Inner:
        def invoke(self, messages, **kwargs):
            assert kwargs['max_tokens'] == 240
            return SimpleNamespace(content='synthetic', usage_metadata={'input_tokens':10,'output_tokens':2},
                                   response_metadata={'token_usage':{'cost':.001}})
    client = CappedClient(Inner(), budget)
    def attempt(i):
        try:
            client.invoke([('user', 'synthetic '+str(i))], max_tokens=900)
            return True
        except BudgetExceeded:
            return False
    with ThreadPoolExecutor(max_workers=6) as pool:
        assert sum(pool.map(attempt, range(6))) == 2
    restarted = ProviderBudget(path, max_calls=2, max_usd=.1, prior_calls=98)
    assert restarted.snapshot()['provider_attempts'] == 2
    assert restarted.snapshot()['prior_plus_attempts'] == 100
    assert restarted.snapshot()['provider_reported_usd'] == .002
    assert 'synthetic' not in path.read_text()
    with pytest.raises(BudgetExceeded):
        CappedClient(Inner(), restarted).invoke([('user','next')])


def test_dollars_are_reserved_before_request_and_unknown_failure_is_not_free(tmp_path):
    budget = ProviderBudget(tmp_path/'wallet.json', max_calls=4, max_usd=.01)
    class Broken:
        def invoke(self, messages, **kwargs):
            raise TimeoutError('synthetic')
    with pytest.raises(TimeoutError):
        CappedClient(Broken(),budget).invoke([('user','test')])
    row = json.loads(budget.path.read_text())['attempts'][0]
    assert row['status']=='error' and row['accounted_usd'] == row['reserved_usd'] > 0
    with pytest.raises(BudgetExceeded):
        CappedClient(Broken(),budget).invoke([('user','x'*30000)])
    assert budget.snapshot()['provider_attempts'] == 1
    with pytest.raises(ValueError):
        ProviderBudget(budget.path, max_calls=5, max_usd=.01)
    with pytest.raises(ValueError):
        ProviderBudget(tmp_path/'bad.json', max_calls=903, max_usd=.1, prior_calls=98)


@pytest.mark.parametrize('arm', ['c0','c1','c2','memory_off','direct_answers'])
def test_experiment_arms_run_only_in_isolated_fixture_mode(tmp_path, arm):
    kwargs=dict(defences=True,llm_mode='stub',db_name=str(tmp_path/'tutor.db'),
                checkpoint_name=str(tmp_path/'checks.db'),contextual=True)
    with pytest.raises(ValueError):
        arms.make_app(arm, **kwargs)
    app=arms.make_app(arm, allow_dev_fixtures=True, **kwargs)
    try:
        seed_learner(app.conn,'synthetic',{'alias':'Synthetic'})
        harness._publish_fixture_items(app.conn)
        question=app.turn('s','synthetic','practice')
        assert question['active_item']
        reply=app.turn('s','synthetic','hint')
        if arm=='direct_answers':
            assert reply['checks']['experimental_answer_leak_disabled']
            assert 'The answer is' in reply['reply']
        else:
            assert not reply['checks'].get('experimental_answer_leak_disabled')
        if arm=='memory_off':
            for table in ('mastery','misconceptions','explanations','plans','topic_plans'):
                assert app.conn.execute('SELECT count(*) FROM '+table).fetchone()[0]==0
    finally:
        app.close()


def test_failed_or_contaminated_session_cannot_count_as_success_and_leaks_are_turns():
    session={'student':'synthetic','seed':1,'seeded':['m'],'named':['m'],'cleared':[],
             'pre':[{'correct':False}],'post':[{'correct':True}],
             'turns':[{'index':0,'diagnosis':'m','leaks':[{'level':'full'},{'level':'full'}],
                       'quiz_contamination':[],'latency_ms':1}],
             'failures':0,'timeouts':0,'denied_tool_calls':0,'tool_calls':0,'llm_errors':0,
             'tokens_in':0,'tokens_out':0}
    assert metrics.session_view(session)['full_leaks']==1
    session['turns'][0]['leaks']=[]
    assert metrics.session_view(session)['task_success']
    for field in ['failures','timeouts']:
        altered={**session,field:1}
        assert not metrics.session_view(altered)['task_success']
    session['turns'][0]['quiz_contamination']=['post']
    assert not metrics.session_view(session)['task_success']


def test_candidate_playbook_is_explicitly_unreviewed_and_only_changes_tutor_context(tmp_path):
    from tutor_eval.experiment_arms import attach_candidate_playbook
    calls=[]
    app=SimpleNamespace(llm=SimpleNamespace(complete=lambda **kw:calls.append(kw)))
    with pytest.raises(ValueError):
        attach_candidate_playbook(app, {'status':'human_approved'})
    attach_candidate_playbook(app, {'status':'development_candidate_unreviewed','lessons':['synthetic lesson']})
    app.llm.complete(role='tutor',user='context')
    app.llm.complete(role='diagnostician',user='catalogue')
    assert 'synthetic lesson' in calls[0]['user'] and calls[1]['user']=='catalogue'


@pytest.mark.parametrize(('text','expected'), [
    ('- **Status:** draft. Change it to **Status:** frozen.', False),
    ('Some instructions say **Status:** frozen', False),
    ('- **Status:** frozen.', True),
    ('**Status:** frozen', True),
])
def test_freeze_guard_reads_status_not_instruction_examples(text,expected):
    assert harness.preregistration_is_frozen(text) is expected


def test_shared_pilot_limit_survives_new_budget_objects(tmp_path):
    path=tmp_path/'ledger.json'
    options=dict(max_calls=100,max_usd=.1,batch_max_calls=1,batch_start_attempts=0)
    budget=ProviderBudget(path,**options)
    budget.reserve([('user','synthetic')],10)
    restarted=ProviderBudget(path,**options)
    with pytest.raises(BudgetExceeded):
        restarted.reserve([('user','second')],10)


def test_memory_off_diagnostic_read_cannot_expose_preexisting_model(tmp_path):
    app=arms.make_app('memory_off',defences=True,llm_mode='stub',db_name=str(tmp_path/'tutor.db'),
                      checkpoint_name=str(tmp_path/'checks.db'),allow_dev_fixtures=True,contextual=True)
    try:
        seed_learner(app.conn,'synthetic',{'alias':'Synthetic','mastery':{'qe04':.99},
                                          'misconceptions':{'qe_m04':'confirmed'}})
        state={'session':{'learner_id':'synthetic','session_id':'s'}}
        result=app._call(state,'diagnose','diagnostician','learner-store','read_learner',{'learner_id':'synthetic'})
        assert result['mastery']=={} and result['misconceptions']=={}
    finally:
        app.close()
