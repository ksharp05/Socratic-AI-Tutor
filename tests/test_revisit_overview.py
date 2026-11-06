"""Owned revisit overview: exact totals, no learner content disclosure and real UI rendering."""
from collections import Counter
import hashlib
from pathlib import Path
from urllib.parse import urlsplit
import pytest
from fastapi.testclient import TestClient
from tutor import store
from tutor.app import TutorApp
from tutor.seed import seed_learner
from tutor.question_catalog import graph_items,allowed
from tutor.toolbus import CallContext
from tutor_api.main import create_app

HEADERS={"a":{"Authorization":"Bearer revisit-a"},"b":{"Authorization":"Bearer revisit-b"},"teacher":{"Authorization":"Bearer revisit-t"}}
@pytest.fixture
def environment(tmp_path):
    app=TutorApp(llm_mode="stub",db_name=str(tmp_path/"t.db"),checkpoint_name=str(tmp_path/"c.db"))
    for lid in ["rv-A","rv-B"]:seed_learner(app.conn,lid,{"alias":"Synthetic revisit learner"})
    try:
        with TestClient(create_app(tutor=app,tokens="revisit-a:student:rv-A,revisit-b:student:rv-B,revisit-t:teacher:rv-teacher")) as client:
            yield app,client
    finally:app.close()
def mark(app):
    item=next(i for i in graph_items() if allowed(i,"practice"))
    app.bus.call(CallContext("synthetic-queue",learner_id="rv-A",node="update_memory"),"study_planner","learner-store","record_revisit",{"learner_id":"rv-A","question_ref":item["question_id"]})
    return item
def test_overview_owns_counts_and_limits_details_to_teacher(environment):
    app,client=environment;item=mark(app)
    student=client.get("/learners/rv-A",headers=HEADERS["a"]).json()
    assert student["revisit_summary"]["total"]==1
    assert student["revisit_summary"]["by_chapter"]=={item["chapter"]:1}
    assert "revisit_items" not in student and item["question_id"] not in str(student)
    assert client.get("/learners/rv-A",headers=HEADERS["b"]).status_code==403
    assert client.get("/learners/rv-B",headers=HEADERS["b"]).json()["revisit_summary"]["total"]==0
    teacher=client.get("/learners/rv-A",headers=HEADERS["teacher"]).json()
    assert teacher["revisit_items"][0]["question_ref"]==item["question_id"]
    assert set(teacher["revisit_items"][0])=={"question_ref","chapter","reason","created_at"}
    assert app.conn.execute("SELECT count(*) FROM mastery").fetchone()[0]==0
def test_summary_is_exact_beyond_the_detail_limit_and_ignores_stale_items(environment):
    app,client=environment;items=[i for i in graph_items() if allowed(i,"practice")][:102]
    for index,item in enumerate(items):
        digest=hashlib.sha256(store.dumps(item).encode()).hexdigest() if index<101 else "stale"
        app.conn.execute("INSERT INTO revisit_items VALUES (?,?,?,?,?,?,?,?)",("rv-A",item["question_id"],item["chapter"],digest,"pending","after_last_hint",index,index))
    body=client.get("/learners/rv-A",headers=HEADERS["teacher"]).json()
    assert body["revisit_summary"]=={"total":101,"by_chapter":dict(Counter(i["chapter"] for i in items[:101])),"has_more":True}
    assert len(body["revisit_items"])==100
    assert items[-1]["question_id"] not in {r["question_ref"] for r in body["revisit_items"]}
def test_deletion_removes_the_summary_and_does_not_recreate_data(environment):
    app,client=environment;mark(app)
    assert client.delete("/learners/rv-A",headers=HEADERS["teacher"]).status_code==200
    assert client.get("/learners/rv-A",headers=HEADERS["a"]).status_code==410
    assert app.conn.execute("SELECT count(*) FROM revisit_items WHERE learner_id='rv-A'").fetchone()[0]==0
def test_student_ui_displays_counts_without_question_ids_or_queue_writes(environment,monkeypatch):
    pytest.importorskip("streamlit")
    import requests
    from streamlit.testing.v1 import AppTest
    app,client=environment;item=mark(app)
    before=app.conn.execute("SELECT count(*) FROM learner_events").fetchone()[0]
    def request(method,url,headers=None,timeout=None,**kwargs):
        return client.request(method,urlsplit(url).path,headers=headers,**kwargs)
    monkeypatch.setattr(requests,"request",request)
    monkeypatch.setenv("TUTOR_API_URL","http://synthetic-local-api")
    monkeypatch.setenv("TUTOR_UI_TOKEN","revisit-a")
    app_file=str(Path(__file__).resolve().parents[1]/"ui/app.py")
    # AppTest.switch_page supports file pages; this app uses callable pages.
    # Load the actual app/authentication, then render its actual progress callable.
    ui=AppTest.from_string("import runpy\nnamespace=runpy.run_path("+repr(app_file)+")\nnamespace['student_progress']()").run(timeout=30)
    assert not ui.exception
    assert any(x.value=="To revisit" for x in ui.subheader)
    assert any("1 practice item is marked" in x.value for x in ui.caption)
    assert all("Question" not in frame.value.columns for frame in ui.dataframe)
    assert item["question_id"] not in " ".join(x.value for x in ui.markdown)
    assert app.conn.execute("SELECT count(*) FROM learner_events").fetchone()[0]==before
    assert app.conn.execute("SELECT count(*) FROM mastery").fetchone()[0]==0


def test_teacher_ui_shows_owned_item_details_without_content_hashes(environment,monkeypatch):
    pytest.importorskip("streamlit")
    import requests
    from streamlit.testing.v1 import AppTest
    app,client=environment;item=mark(app)
    def request(method,url,headers=None,timeout=None,**kwargs):
        return client.request(method,urlsplit(url).path,headers=headers,**kwargs)
    monkeypatch.setattr(requests,"request",request)
    monkeypatch.setenv("TUTOR_API_URL","http://synthetic-local-api")
    monkeypatch.setenv("TUTOR_UI_TOKEN","revisit-t")
    app_file=str(Path(__file__).resolve().parents[1]/"ui/app.py")
    ui=AppTest.from_string("import runpy\nnamespace=runpy.run_path("+repr(app_file)+")\nnamespace['teacher_learners']()").run(timeout=30)
    assert not ui.exception
    tables=[frame.value for frame in ui.dataframe if "Question" in frame.value.columns]
    assert len(tables)==1 and tables[0].iloc[0]["Question"]==item["question_id"]
    assert tables[0].iloc[0]["Marked after"]=="After the last hint"
    assert all("content_sha256" not in frame.value.columns for frame in ui.dataframe)
