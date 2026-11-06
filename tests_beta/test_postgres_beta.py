"""Real Postgres acceptance. Only a loopback synthetic database is permitted."""
import os
import uuid
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
import pytest
from fastapi.testclient import TestClient
from socrates_beta.transport import BrowserTransport

ORIGIN="https://socratic-tutor-beta.vercel.app"
HEADERS={"Origin":ORIGIN,"X-Socrates-Request":"1"}

@pytest.fixture
def repo():
    dsn=os.environ.get("BETA_TEST_POSTGRES_DSN")
    if not dsn:pytest.skip("Set a loopback synthetic Postgres test URL")
    parsed=urlsplit(dsn)
    assert parsed.hostname in ("localhost","127.0.0.1") and parsed.path=="/socrates_test"
    from socrates_beta.postgres import PostgresRepository
    return PostgresRepository(dsn,migrate=True)

def test_exact_additional_origins():
    transport=BrowserTransport.configured(ORIGIN,additional_origins=("https://beta-123.vercel.app",))
    assert transport.origins==(ORIGIN,"https://beta-123.vercel.app")
    assert "*.vercel.app" not in transport.hosts
    with pytest.raises(ValueError):BrowserTransport.configured(ORIGIN,additional_origins=("https://*.vercel.app",))
    with pytest.raises(ValueError):BrowserTransport.configured(additional_origins=(ORIGIN,))

def test_postgres_repository_persists_json_and_deduplicates(repo):
    from socrates_beta.postgres import PostgresRepository
    owner=uuid.uuid4().hex
    assert repo.profile(owner)["preferences"]=={}
    repo.preferences(owner,{"grade":10,"subject":"Mathematics","model_consent":False})
    session=repo.create_session(owner,"synthetic-dataset",{"grade":10},"Synthetic acceptance")
    repo.save_turn(session["id"],"test-request-001","Synthetic message",{"citations":[],"text":"Reference"},session["state"])
    other=PostgresRepository(repo._dsn)
    assert other.profile(owner)["preferences"]["grade"]==10
    assert other.prior_turn(session["id"],"test-request-001")["text"]=="Reference"
    assert len(other.history(session["id"]))==1
    assert len(other.sessions(owner))==1
    with pytest.raises(KeyError):other.session(session["id"],uuid.uuid4().hex)
    with pytest.raises(RuntimeError):
        with repo.transaction() as conn:
            repo.observe(owner,session["id"],"synthetic-node","test",{"value":1},conn=conn)
            raise RuntimeError("rollback")
    assert not repo.observations(owner)
    other.forget(owner)
    assert not repo.sessions(owner) and not repo.history(session["id"])

def test_owner_lock_is_cross_instance_reentrant_and_released(repo):
    from socrates_beta.postgres import PostgresRepository
    from socrates_beta.repository import BetaBusy
    owner=uuid.uuid4().hex
    other=PostgresRepository(repo._dsn)
    with repo.owner_guard(owner):
        with repo.owner_guard(owner,timeout=0):pass
        with pytest.raises(BetaBusy):
            with other.owner_guard(owner,timeout=.1):pass
        with other.owner_guard("another-"+owner,timeout=0):pass
    with other.owner_guard(owner,timeout=0):pass
    with pytest.raises(RuntimeError):
        with repo.owner_guard(owner):raise RuntimeError("release")
    with other.owner_guard(owner,timeout=0):pass

def test_postgres_browser_restart_replay_isolation_and_forget(repo,tmp_path):
    from socrates_beta.vercel_app import vercel_app
    from socrates_beta.postgres import PostgresRepository
    from tutor_eval.protocol_v2 import render
    env={"TUTOR_PUBLIC_ORIGIN":ORIGIN,"TUTOR_BROWSER_SECRET":"ab"*32,
         "TUTOR_BETA_LIVE":"0","VERCEL_URL":"beta-exact.vercel.app"}
    app=vercel_app(env=env,data=tmp_path/"first",repository=repo)
    with TestClient(app,base_url=ORIGIN) as client:
        initial=client.get("/beta/api/bootstrap")
        assert initial.status_code==200,initial.text
        # Preserve the actual signed cookie name independently of transport internals.
        cookie_header="; ".join(k+"="+v for k,v in client.cookies.items())
        assert "Secure" in initial.headers["set-cookie"]
        assert "HttpOnly" in initial.headers["set-cookie"]
        assert not list(tmp_path.rglob("browser.secret"))
        assert client.get("/health").json()["saved_progress"]=="postgres_browser_profile"
        assert client.get("/beta/",headers={"Host":"other-project.vercel.app"}).status_code==400
        assert client.post("/beta/api/preferences",headers={**HEADERS,"Origin":"https://evil.example"},json={"grade":10,"subject":"Mathematics"}).status_code==403
        assert client.post("/beta/api/preferences",headers=HEADERS,json={"grade":10,"subject":"Mathematics","goal":"Synthetic goal"}).status_code==200
        session=client.post("/beta/api/sessions",headers=HEADERS,json={"grade":10,"subject":"Mathematics","unit":5}).json()
        sid=session["id"]
        chat=client.post("/beta/api/chat",headers=HEADERS,json={"session_id":sid,"text":"What is an arithmetic progression?","request_id":"synthetic-turn-001"})
        assert chat.status_code==200,chat.text
        citation=chat.json()["citations"][0]["id"]
        card=client.post("/beta/api/cards",headers=HEADERS,json={"session_id":sid,"passage_id":citation}).json()
        assert client.post("/beta/api/cards/"+card["id"]+"/review",headers=HEADERS,json={"rating":"good"}).status_code==200
        check=client.post("/beta/api/practice",headers=HEADERS,json={"session_id":sid}).json()
        aid=check["id"]
        maths=app.routes[-1].app.state.services["maths"]
        answer=render(maths.key(check["item"]["id"]))
    restarted=vercel_app(env=env,data=tmp_path/"second",repository=PostgresRepository(repo._dsn))
    with TestClient(restarted,base_url=ORIGIN,headers={"Cookie":cookie_header}) as client:
        assert client.get("/beta/api/bootstrap").json()["profile"]["goal"]=="Synthetic goal"
        assert len(client.get("/beta/api/sessions").json())==1
        assert len(client.get("/beta/api/sessions/"+sid).json()["turns"])==1
        assert len(client.get("/beta/api/cards").json())==1
        def submit(target):
            with TestClient(target,base_url=ORIGIN,headers={"Cookie":cookie_header}) as duplicate:
                response=duplicate.post("/beta/api/practice/"+aid+"/submit",headers=HEADERS,json={"answer":answer,"request_id":"synthetic-answer-001"})
                assert response.status_code==200,response.text
                return response.json()
        with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(submit,(app,restarted)))
        assert responses[0]==responses[1]
        owner=cookie_header.split("=",1)[1].split(".",1)[0]
        assert len([o for o in repo.observations(owner) if o["kind"]=="checked_answer"])==1
        with TestClient(restarted,base_url=ORIGIN) as stranger:
            assert stranger.get("/beta/api/sessions/"+sid).status_code==404
        assert client.post("/beta/api/forget",headers=HEADERS,json={}).json()["deleted"]
        assert client.get("/beta/api/sessions").json()==[]
        assert client.get("/beta/api/cards").json()==[]
        assert not repo.observations(owner)
        assert repo.history(sid)==[]

@pytest.mark.parametrize("missing",["TUTOR_PUBLIC_ORIGIN","TUTOR_BROWSER_SECRET"])
def test_vercel_configuration_fails_closed(missing,tmp_path):
    from socrates_beta.vercel_app import vercel_app
    env={"TUTOR_PUBLIC_ORIGIN":ORIGIN,"TUTOR_BROWSER_SECRET":"ab"*32}
    del env[missing]
    with pytest.raises(ValueError):vercel_app(env=env,data=tmp_path,repository=object())

def test_live_model_cannot_be_enabled_without_database_wallet(tmp_path):
    from socrates_beta.vercel_app import vercel_app
    with pytest.raises(ValueError,match="budget"):
        vercel_app(env={"TUTOR_PUBLIC_ORIGIN":ORIGIN,"TUTOR_BETA_LIVE":"1"},data=tmp_path,repository=object())
