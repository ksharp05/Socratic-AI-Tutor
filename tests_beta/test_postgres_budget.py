"""Shared serverless budgets: real synthetic Postgres, no provider network."""
import copy,json,os,uuid
from pathlib import Path
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
import pytest
from socrates_beta.postgres_budget import PostgresBudget
from tutor_eval.provider_budget import BudgetExceeded,CappedClient

def grant(**updates):
    value={"status":"approved","allocation_id":"synthetic-"+uuid.uuid4().hex,"phase_ceiling_usd":10,
       "reserved_usd":.5,"previous_accounted_usd":.14413205,"max_calls":3,
       "destination":"https://openrouter.ai/api/v1","model":"openai/gpt-4.1-mini",
       "approval_quote":"Synthetic test only, not provider authorization.","prior_provider_attempts":1218,
       "funding_receipt_sha256":"a"*64}
    value.update(updates)
    value["provider_policy"]={"max_calls":value["max_calls"],"max_usd":value["reserved_usd"],"prior_calls":1218,
       "input_price":3,"output_price":12,"approval_receipt_sha256":"a"*64,"approved_total_limit":1218+value["max_calls"]}
    return value

@pytest.fixture
def funded():
    dsn=os.environ.get("BETA_TEST_POSTGRES_DSN")
    if not dsn:pytest.skip("Requires loopback synthetic Postgres")
    p=urlsplit(dsn);assert p.hostname in ("127.0.0.1","localhost") and p.path=="/socrates_test"
    from socrates_beta.postgres import PostgresRepository
    repo=PostgresRepository(dsn,migrate=True)
    g=grant()
    budget=PostgresBudget.provision(repo,g)
    try:yield repo,g,budget
    finally:budget.set_paused()

def test_concurrent_cap_is_global_and_survives_instances(funded):
    repo,g,budget=funded
    def reserve(i):
        try:return PostgresBudget(repo,g).reserve([("user","Synthetic "+str(i))],240)
        except BudgetExceeded:return None
    with ThreadPoolExecutor(max_workers=8) as pool:ids=[i for i in pool.map(reserve,range(15)) if i]
    assert len(ids)==3 and len(set(ids))==3
    restored=PostgresBudget(repo,g)
    assert restored.snapshot()["provider_attempts"]==3
    assert restored.snapshot()["prior_plus_attempts"]==1221
    assert all(a["status"]=="reserved" for a in restored.export()["attempts"])
    with pytest.raises(BudgetExceeded):restored.reserve([("user","another")],240)
    assert restored.snapshot()["refused"]==13

def test_no_reset_changed_grant_pause_replay_and_usage(funded):
    repo,g,budget=funded
    messages=[("user","Synthetic fixed request")]
    call=budget.reserve(messages,240)
    with pytest.raises(BudgetExceeded):budget.reserve(messages,240)
    with pytest.raises(ValueError):PostgresBudget.provision(repo,g)
    changed={**g,"approval_quote":"Changed"}
    with pytest.raises(ValueError):PostgresBudget(repo,changed)
    budget.finish(call,error=TimeoutError())
    row=budget.export()["attempts"][0]
    assert row["accounted_usd"]==row["reserved_usd"] and row["billed_usd"] is None
    budget.set_paused()
    with pytest.raises(BudgetExceeded):budget.reserve([("user","not sent")],240)
    budget.set_paused(False)
    assert budget.snapshot()["provider_attempts"]==1
    call2=budget.reserve([("user","Another synthetic request")],240)
    response=SimpleNamespace(usage_metadata={"input_tokens":10,"output_tokens":5},response_metadata={"token_usage":{"cost":.0001}})
    budget.finish(call2,reply=response)
    assert budget.snapshot()["provider_reported_usd"]==.0001
    assert "Synthetic fixed request" not in json.dumps(budget.export())

def test_usd_cap_refuses_before_client_is_invoked(funded):
    repo,g,budget=funded
    budget.set_paused()
    small=grant(reserved_usd=.001)
    lease=PostgresBudget.provision(repo,small)
    calls=[]
    class Provider:
        def invoke(self,*args,**kwargs):calls.append(1)
    try:
        with pytest.raises(BudgetExceeded):CappedClient(Provider(),lease).invoke([("user","Never sent")])
        assert calls==[] and lease.snapshot()["provider_attempts"]==0
    finally:lease.set_paused()

def test_live_factory_requires_consent_and_uses_preprovisioned_lease(funded,tmp_path):
    from fastapi.testclient import TestClient
    from socrates_beta.vercel_app import vercel_app
    repo,g,budget=funded
    calls=[]
    class FakeLanguage:
        def __init__(self,root,lease):assert lease.snapshot()["provider_attempts"]==0
        def generate(self,*args):calls.append(1);raise RuntimeError("Synthetic offline fallback")
        def health(self):return {"mode":"live","remaining":3}
    origin="https://socratic-tutor-beta.vercel.app"
    env={"TUTOR_PUBLIC_ORIGIN":origin,"TUTOR_BROWSER_SECRET":"ab"*32,"TUTOR_BETA_LIVE":"1",
         "TUTOR_DEPLOYMENT_BUDGET_JSON":json.dumps(g)}
    app=vercel_app(env=env,repository=repo,data=tmp_path,language_factory=FakeLanguage)
    headers={"Origin":origin,"X-Socrates-Request":"1"}
    with TestClient(app,base_url=origin) as client:
        assert client.get("/beta/api/bootstrap").json()["model_consent_required"]
        sid=client.post("/beta/api/sessions",headers=headers,json={"grade":10,"subject":"Mathematics"}).json()["id"]
        body={"session_id":sid,"text":"Can you tell me about trigonometry","request_id":"synthetic-consent-check"}
        assert client.post("/beta/api/chat",headers=headers,json=body).status_code==403
        assert not calls
        assert client.post("/beta/api/preferences",headers=headers,json={"grade":10,"subject":"Mathematics","model_consent":True}).status_code==200
        response=client.post("/beta/api/chat",headers=headers,json=body).json()
        assert response["citations"] and response["move"]!="missing_evidence"
        assert len(calls)==1

def test_global_grant_policy_must_match():
    from socrates_beta.postgres_budget import policy_for
    value=grant()
    assert policy_for(value)["prior_calls"]==1218
    value["provider_policy"]["max_usd"]=1
    with pytest.raises(ValueError):policy_for(value)
