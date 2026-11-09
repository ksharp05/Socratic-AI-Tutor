"""No-network proofs that a local v4 batch can run beside an open hosted lease without touching its cap."""
from types import SimpleNamespace
import pytest
from tutor_eval.product_budget import ProductPhase,read,save,BudgetExceeded

AUTH={'status':'approved','approved_by':'synthetic unit fixture','approval_quote':'unit-test-only authorization',
      'destination':'https://openrouter.ai/api/v1','phase_ceiling_usd':10,'models':{},'payload_scope':['synthetic']}


def finish(wallet,cost):
    call=wallet.reserve([('user','synthetic')],100)
    wallet.finish(call,reply=SimpleNamespace(usage_metadata={'input_tokens':5,'output_tokens':5},response_metadata={'token_usage':{'cost':cost}}))


@pytest.fixture
def world(tmp_path,monkeypatch):
    """A closed local batch, then an open hosted lease allocated through v3, as on the real ledger."""
    monkeypatch.setenv('SOCRATES_SOURCE_WORKSPACE',str(tmp_path))
    v3=tmp_path/'Directions/product_quality/v3';v3.mkdir(parents=True)
    previous=v3/'previous.json';save(previous,{'policy':{'prior_calls':0},'attempts':[],'refused':0})
    save(v3/'ITERATION_AUTHORIZATION.json',{**AUTH,'previous_provider_ledger':str(previous.relative_to(tmp_path))})
    (tmp_path/'Directions/product_quality/v1').mkdir()
    save(tmp_path/'Directions/product_quality/v1/PHASE_AUTHORIZATION.json',{'status':'approved','max_phase_usd':10,'batch_allocations':[]})
    old=ProductPhase(tmp_path)
    local=old.allocate('local-one','synthetic local',max_usd=.5,max_calls=5);finish(local,.001);finish(local,.001);old.close(local)
    hosted=old.allocate('hosted-one','synthetic hosted lease',max_usd=.5,max_calls=5)
    state=read(old.phase_path);state['batch_allocations'][-1]['remote_allocation']='hosted-one';save(old.phase_path,state)
    v4=tmp_path/'Directions/product_quality/v4';v4.mkdir()
    save(v4/'ITERATION_AUTHORIZATION.json',{**AUTH,'allow_local_batch_beside_hosted_lease':True,
                                            'previous_provider_ledger':str(previous.relative_to(tmp_path))})
    return SimpleNamespace(root=tmp_path,old=old,hosted=hosted,v4=v4)


def test_default_iteration_still_refuses_beside_hosted(world):
    with pytest.raises(ValueError,match='Close the previous batch'):world.old.allocate('v3-new','must stay refused')


def test_v4_without_opt_in_refuses_beside_hosted(world):
    auth=read(world.v4/'ITERATION_AUTHORIZATION.json');del auth['allow_local_batch_beside_hosted_lease']
    save(world.v4/'ITERATION_AUTHORIZATION.json',auth)
    with pytest.raises(ValueError,match='Close the previous batch'):ProductPhase(world.root,iteration='v4').allocate('v4-new','synthetic')


def test_v4_opt_in_allows_one_local_batch_and_keeps_hosted_cap(world):
    phase=ProductPhase(world.root,iteration='v4')
    wallet=phase.allocate('v4-new','synthetic',max_usd=1,max_calls=5)
    state=read(phase.phase_path)
    hosted=next(b for b in state['batch_allocations'] if b['batch']=='hosted-one')
    assert hosted['status']=='running' and hosted['max_usd']==.5
    assert abs(state['unallocated_cap_usd']-(10-.001*2-.5-1))<1e-9
    assert wallet.path.parent==world.v4/'batches/v4-new'
    with pytest.raises(ValueError,match='Close the previous batch'):phase.allocate('v4-second','synthetic')


def test_v4_chains_from_last_local_wallet_not_the_hosted_mirror(world):
    phase=ProductPhase(world.root,iteration='v4')
    wallet=phase.allocate('v4-new','synthetic',max_usd=.5,max_calls=5)
    assert wallet.snapshot()['prior_calls']==2
    # A hosted sync rewrites its mirror; the local batch must still reopen and close normally.
    mirror=world.root/read(phase.phase_path)['batch_allocations'][1]['wallet'];data=read(mirror)
    data['attempts'].append({'id':'synthetic','status':'completed','accounted_usd':.0001,'billed_usd':.0001});save(mirror,data)
    reopened=phase.open('v4-new');finish(reopened,.002)
    assert phase.close(reopened)['provider_attempts']==1


def test_v4_counts_hosted_cap_against_the_ceiling(world):
    state=read(world.old.phase_path)
    state['batch_allocations'].insert(0,{'batch':'sealed','status':'completed','max_usd':8.9})
    save(world.old.phase_path,state)
    with pytest.raises(BudgetExceeded):ProductPhase(world.root,iteration='v4').allocate('too-much','synthetic',max_usd=.7)


def test_hosted_lease_still_cannot_spend_locally_or_be_closed(world):
    ProductPhase(world.root,iteration='v4').allocate('v4-new','synthetic',max_usd=.5,max_calls=5)
    with pytest.raises(BudgetExceeded,match='local wallet'):world.hosted.reserve([('user','must not send')],100)
    with pytest.raises(ValueError,match='remote-close'):world.old.close(world.hosted)


def test_unknown_iteration_is_rejected(world):
    with pytest.raises(ValueError,match='Unknown product iteration'):ProductPhase(world.root,iteration='v9')
