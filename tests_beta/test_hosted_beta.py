"""Hosted beta acceptance uses public content, synthetic browser profiles and fake providers only."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from tutor.question_catalog import graph_items,allowed
from tutor_eval.protocol_v2 import render
from tutor_eval.provider_budget import CappedClient,BudgetExceeded
from socrates_beta.transport import BrowserTransport
from socrates_beta.public_index import prepare_public_index
from socrates_beta.hosted import hosted_app
from socrates_beta.maths import CheckedMaths
from socrates_beta.deployment_budget import DeploymentBudget,HostedLanguage

CODE=Path(__file__).resolve().parents[1]
ORIGIN="https://socrates.example.test"
HEADERS={"X-Socrates-Request":"1","Origin":ORIGIN}
ITEMS=[i for i in graph_items() if allowed(i,"practice")]


@pytest.fixture(scope="module")
def checked():
    return CheckedMaths(CODE)


def grant(**updates):
    value={"status":"approved","allocation_id":"synthetic-test-allocation","phase_ceiling_usd":10,
           "reserved_usd":0.50,"previous_accounted_usd":0.14413205,"max_calls":3,
           "destination":"https://openrouter.ai/api/v1","model":"openai/gpt-4.1-mini",
           "approval_quote":"Synthetic isolated test grant; never a real provider authorization."}
    return {**value,**updates}


@pytest.mark.parametrize("origin",["http://site.example","https://evil.example/path","https://name:secret@site.example","https://*.example","https://site.example?x=1","https://SITE.example","https://site..example","https://site.example:0"])
def test_public_origin_is_strict(origin):
    with pytest.raises(ValueError):BrowserTransport.configured(origin)


def test_canonical_origin_has_no_untrusted_forwarded_header_input():
    config=BrowserTransport.configured(ORIGIN)
    assert config.secure_cookie and "socrates.example.test" in config.hosts
    assert BrowserTransport.configured("https://socrates.example.test:443/").origin==ORIGIN
    assert BrowserTransport.configured().origin is None


@pytest.mark.parametrize("item",ITEMS,ids=lambda i:i["question_id"])
def test_native_browser_math_roundtrip_for_every_public_practice_item(checked,item):
    key=checked.key(item["question_id"])
    result=checked.grade(item["question_id"],render(key))
    assert result["scorable"] and result["correct"]


def test_public_index_is_portable_reused_and_never_marked_human_approved(tmp_path):
    reg=prepare_public_index(CODE,tmp_path)
    original=reg.entries();again=prepare_public_index(CODE,tmp_path)
    assert again.entries()==original
    assert not (tmp_path/"book_pipeline").exists()
    assert reg.knowledge().catalogue()[0]["grade"]==10
    with reg.knowledge().connect() as conn:
        assert conn.execute("SELECT count(*) FROM passages").fetchone()[0]==25
        assert conn.execute("SELECT count(*) FROM passages WHERE approved!=0 OR human_review_status!='pending'").fetchone()[0]==0


def test_changed_index_is_rejected_without_rebuilding(tmp_path):
    import sqlite3
    reg=prepare_public_index(CODE,tmp_path);entry=reg.entries()["datasets"][reg.entries()["active"]]
    with sqlite3.connect(entry["path"]) as conn:conn.execute("UPDATE passages SET text='changed' WHERE id=(SELECT id FROM passages LIMIT 1)")
    with pytest.raises(ValueError,match="changed"):prepare_public_index(CODE,tmp_path)


def test_transport_owner_restart_quiz_isolation_and_delete(tmp_path):
    app=hosted_app(data=tmp_path,origin=ORIGIN,live=False)
    with TestClient(app,base_url=ORIGIN) as client:
        bootstrap=client.get("/beta/api/bootstrap")
        assert bootstrap.status_code==200,bootstrap.text
        assert "Secure" in bootstrap.headers["set-cookie"] and "HttpOnly" in bootstrap.headers["set-cookie"]
        assert bootstrap.json()["assessment_policy"]=="reference_checked_beta"
        assert bootstrap.json()["graph_journey"] is False
        assert client.get("/beta/api/health").json()["maths_practice_items"]==len(ITEMS)
        assert client.get("/beta/api/bootstrap",headers={"Host":"evil.example"}).status_code==400
        assert client.post("/beta/api/preferences",headers={**HEADERS,"Origin":"https://evil.example","X-Forwarded-Host":"socrates.example.test"},json={"grade":10,"subject":"Mathematics"}).status_code==403
        assert client.post("/beta/api/preferences",headers=HEADERS,json={"grade":10,"subject":"Mathematics"}).status_code==200
        session=client.post("/beta/api/sessions",headers=HEADERS,json={"grade":10,"subject":"Mathematics"}).json()
        empty=next(i for i in ITEMS if i["problem"]["task_type"]=="ap_count" and not CheckedMaths(CODE).key(i["question_id"])["values"])
        assessment=client.post("/beta/api/practice",headers=HEADERS,json={"session_id":session["id"],"question_id":empty["question_id"]}).json()
        done=client.post(f"/beta/api/practice/{assessment['id']}/submit",headers=HEADERS,json={"answer":"no valid term count","request_id":"synthetic-count-1"})
        assert done.status_code==200 and done.json()["status"]=="correct",done.text
        assert client.get("/beta/api/dashboard").json()["correct_answers"]==1
        cookies=dict(client.cookies)
    with TestClient(hosted_app(data=tmp_path,origin=ORIGIN,live=False),base_url=ORIGIN) as restarted:
        restarted.cookies.update(cookies)
        assert restarted.get("/beta/api/dashboard").json()["correct_answers"]==1
        assert len(restarted.get("/beta/api/sessions").json())==1
        with TestClient(app,base_url=ORIGIN) as other:
            assert other.get("/beta/api/sessions/"+session["id"]).status_code==404
        assert restarted.post("/beta/api/forget",headers=HEADERS,json={}).status_code==200
        assert restarted.get("/beta/api/sessions").json()==[]


def test_bad_cookie_does_not_break_public_app(tmp_path):
    with TestClient(hosted_app(data=tmp_path,origin=ORIGIN,live=False),base_url=ORIGIN) as client:
        client.cookies.set("socrates_beta_profile","z"*32+"."+"0"*64)
        response=client.get("/beta/api/bootstrap")
        assert response.status_code==200 and "set-cookie" in response.headers


def test_serving_never_creates_or_resets_provider_allowance(tmp_path):
    with pytest.raises(ValueError,match="not provisioned"):DeploymentBudget(tmp_path,grant())
    budget=DeploymentBudget.provision(tmp_path,grant())
    budget.reserve([("user","synthetic one")],100)
    reopened=DeploymentBudget(tmp_path,grant())
    assert reopened.snapshot()["provider_attempts"]==1
    with pytest.raises(FileExistsError):DeploymentBudget.provision(tmp_path,grant())
    with pytest.raises(ValueError,match="changed"):DeploymentBudget(tmp_path,grant(approval_quote="changed"))
    budget.path.unlink()
    with pytest.raises(ValueError,match="not provisioned"):DeploymentBudget(tmp_path,grant())


def test_concurrent_instances_share_the_hard_request_cap(tmp_path):
    budget=DeploymentBudget.provision(tmp_path,grant(max_calls=1))
    def reserve(index):
        try:return DeploymentBudget(tmp_path,grant(max_calls=1)).reserve([("user",f"synthetic {index}")],100)
        except BudgetExceeded:return None
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(reserve,range(4)))
    assert sum(v is not None for v in results)==1
    assert budget.snapshot()["provider_attempts"]==1


def test_uncertain_request_and_exact_replay_cannot_call_provider_twice(tmp_path):
    budget=DeploymentBudget.provision(tmp_path,grant());calls=[]
    class Fake:
        def invoke(self,*args,**kwargs):
            calls.append(kwargs)
            raise TimeoutError("synthetic lost acknowledgement")
    client=CappedClient(Fake(),budget,cap=240)
    with pytest.raises(TimeoutError):client.invoke([("user","synthetic replay")])
    with pytest.raises(BudgetExceeded):client.invoke([("user","synthetic replay")])
    assert len(calls)==1 and budget.snapshot()["accounted_usd"]>0
    assert "synthetic replay" not in budget.path.read_text()


def test_dollar_limit_and_operator_pause_refuse_before_sending(tmp_path):
    budget=DeploymentBudget.provision(tmp_path,grant(reserved_usd=0.001))
    with pytest.raises(BudgetExceeded):budget.reserve([("user","synthetic")],240)
    assert budget.snapshot()["provider_attempts"]==0
    paused=DeploymentBudget.provision(tmp_path,grant(allocation_id="synthetic-paused-allocation"))
    paused.pause_file.touch()
    with pytest.raises(BudgetExceeded):paused.reserve([("user","synthetic")],100)
    assert paused.snapshot()["provider_attempts"]==0


@pytest.mark.parametrize("updates",[{"max_calls":True},{"reserved_usd":float("nan")},{"previous_accounted_usd":9.9},{"status":"pending"},{"model":"another/model"},{"destination":"https://example.org"}])
def test_uncovered_or_malformed_allocation_cannot_initialize(tmp_path,updates):
    with pytest.raises(ValueError):DeploymentBudget.provision(tmp_path,grant(**updates))


def test_live_consent_and_paid_acknowledgement_replay_are_separate(tmp_path,monkeypatch):
    receipt=grant();DeploymentBudget.provision(tmp_path,receipt)
    monkeypatch.setenv("TUTOR_DEPLOYMENT_BUDGET_JSON",json.dumps(receipt))
    fake=SimpleNamespace(calls=0)
    class Language:
        def health(self):return {"mode":"live","model":"fake-no-network"}
        def generate(self,system,context):
            fake.calls+=1
            return json.dumps({"reply":"After collecting terms, a quadratic has a nonzero squared-term coefficient. Which coefficient must stay nonzero?",
                               "citations":[context["excerpts"][0]["id"]]})
    app=hosted_app(data=tmp_path,origin=ORIGIN,live=True,language_factory=lambda *args:Language())
    with TestClient(app,base_url=ORIGIN) as client:
        session=client.post("/beta/api/sessions",headers=HEADERS,json={"grade":10,"subject":"Mathematics"}).json()
        body={"session_id":session["id"],"text":"Explain a quadratic equation","request_id":"synthetic-chat-1"}
        assert client.post("/beta/api/chat",headers=HEADERS,json=body).status_code==403
        assert fake.calls==0
        urgent={**body,"text":"I want to hurt myself","request_id":"synthetic-urgent-1"}
        assert client.post("/beta/api/chat",headers=HEADERS,json=urgent).json()["move"]=="human_help"
        assert fake.calls==0
        assert client.post("/beta/api/preferences",headers=HEADERS,json={"grade":10,"subject":"Mathematics","model_consent":True}).status_code==200
        first=client.post("/beta/api/chat",headers=HEADERS,json=body)
        assert first.status_code==200 and fake.calls==1,first.text
        assert client.post("/beta/api/chat",headers=HEADERS,json=body).json()==first.json() and fake.calls==1

def test_beta_publication_is_bound_to_registered_scope_and_versions(tmp_path,checked):
    from socrates_beta.reference_policy import ReferenceCheckedAssessmentService
    from socrates_beta.repository import Repository
    from socrates_beta.ports import Scope
    policy=ReferenceCheckedAssessmentService(Repository(tmp_path/"state.sqlite"),checked)
    eligible=policy._eligible(Scope(10,"Mathematics"),None,"practice")
    assert {i["question_id"] for i in eligible}=={i["question_id"] for i in ITEMS}
    item=eligible[0];qid=item["question_id"]
    original=copy.deepcopy(checked.items[qid])
    try:
        checked.items[qid]["prompt"]+=" Unreviewed change."
        assert qid not in {i["question_id"] for i in policy._eligible(Scope(10,"Mathematics"),None,"practice")}
    finally:
        checked.items[qid]=original

def test_real_sdk_is_constructed_with_single_attempt_and_no_request(tmp_path,monkeypatch):
    # Synthetic key; client construction does not invoke any provider.
    monkeypatch.setenv("LLM_API_KEY","synthetic-not-a-live-provider-key")
    monkeypatch.setenv("TUTOR_LLM","auto")
    monkeypatch.setenv("LLM_MODEL","openai/gpt-4.1-mini")
    monkeypatch.setenv("LLM_BASE_URL","https://openrouter.ai/api/v1")
    budget=DeploymentBudget.provision(tmp_path,grant())
    language=HostedLanguage(CODE,budget)
    inner=language.delegate.chat.inner
    assert inner.max_retries==inner.root_client.max_retries==0
    assert inner.max_tokens==240 and language.delegate.chat.cap==240
    assert language.health()["calls"]==0
