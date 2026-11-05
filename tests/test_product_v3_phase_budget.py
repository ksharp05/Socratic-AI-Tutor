"""No-network proofs of phase caps, sealed wallets and conservative accounting."""
import hashlib,json
from pathlib import Path
from types import SimpleNamespace
import pytest
from tutor_eval.product_budget import ProductPhase,read,save,BudgetExceeded

@pytest.fixture
def phase(tmp_path,monkeypatch):
    monkeypatch.setenv('SOCRATES_SOURCE_WORKSPACE',str(tmp_path))
    root=tmp_path/'Directions/product_quality/v3';root.mkdir(parents=True)
    previous=root/'previous.json';save(previous,{'policy':{'prior_calls':0},'attempts':[],'refused':0})
    save(root/'ITERATION_AUTHORIZATION.json',{'status':'approved','approved_by':'synthetic unit fixture','approval_quote':'unit-test-only authorization','destination':'https://openrouter.ai/api/v1','phase_ceiling_usd':10,'models':{},'payload_scope':['synthetic'],'previous_provider_ledger':str(previous.relative_to(tmp_path))})
    (tmp_path/'Directions/product_quality/v1').mkdir()
    save(tmp_path/'Directions/product_quality/v1/PHASE_AUTHORIZATION.json',{'status':'approved','max_phase_usd':10,'batch_allocations':[]})
    return ProductPhase(tmp_path)


def finish(wallet,cost):
    call=wallet.reserve([('user','synthetic')],100)
    reply=SimpleNamespace(usage_metadata={'input_tokens':5,'output_tokens':5},response_metadata={'token_usage':{'cost':cost}})
    wallet.finish(call,reply=reply)


def test_closed_cap_returns_to_pool_without_changing_original_wallet_policy(phase):
    w=phase.allocate('batch-one','synthetic test',max_usd=.5,max_calls=5);finish(w,.001)
    phase.close(w)
    entry=read(phase.phase_path)['batch_allocations'][0]
    assert entry['max_usd']==.001 and entry['original_allocated_cap_usd']==.5
    assert read(w.path)['policy']['max_usd']==.5
    with pytest.raises(BudgetExceeded):w.reserve([('user','another')],100)
    with pytest.raises(ValueError):phase.open('batch-one')


def test_second_open_allocation_is_forbidden(phase):
    phase.allocate('batch-one','synthetic test')
    with pytest.raises(ValueError):phase.allocate('batch-two','synthetic test')


def test_phase_cap_stops_allocation_before_new_wallet(phase):
    value=read(phase.phase_path);value['batch_allocations']=[{'batch':'sealed','status':'completed','max_usd':9.95}];save(phase.phase_path,value)
    with pytest.raises(BudgetExceeded):phase.allocate('over-cap','synthetic test',max_usd=.1)
    assert not (phase.root/'batches/over-cap').exists()


def test_completed_wallet_mutation_is_detected(phase):
    w=phase.allocate('batch-one','synthetic test');finish(w,.001);phase.close(w)
    with w.path.open('a') as f:f.write(' ')
    with pytest.raises(ValueError):phase.allocate('batch-two','synthetic test')


def test_inflight_request_prevents_cap_release(phase):
    w=phase.allocate('batch-one','synthetic test');w.reserve([('user','synthetic')],100)
    with pytest.raises(ValueError):phase.close(w)


def test_chain_counts_actual_prior_attempts(phase):
    one=phase.allocate('batch-one','synthetic test');finish(one,.001);phase.close(one)
    two=phase.allocate('batch-two','synthetic test')
    assert two.snapshot()['prior_calls']==1


def test_sealed_batch_cannot_silently_repeat(phase):
    one=phase.allocate('batch-one','synthetic test');phase.close(one)
    with pytest.raises(ValueError):phase.allocate('batch-one','synthetic test')
