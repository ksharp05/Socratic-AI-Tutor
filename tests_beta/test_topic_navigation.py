"""Regression cases for the reported broad-topic and capability dead ends."""
from pathlib import Path
import uuid
import pytest
from socrates_beta.public_index import prepare_public_index
from socrates_beta.repository import Repository
from socrates_beta.dialogue import DialogueService
from socrates_beta.ports import Scope
CODE=Path(__file__).resolve().parents[1]

@pytest.fixture
def service(tmp_path):
    registry=prepare_public_index(CODE,tmp_path/"index")
    repo=Repository(tmp_path/"progress.sqlite")
    return DialogueService(repo,registry),repo,registry

@pytest.mark.parametrize("message,unit",[
 ("Can you tell me about trigonometry",8),("trigonometry",8),("Teach me trig",8),
 ("Introduction to Trigonometry",8),("Tell me about arithmetic progressions",5),
 ("Can you teach me quadratic equations",4)])
def test_broad_topic_opens_actual_foundational_source(service,message,unit):
    dialogue,repo,registry=service
    owner=uuid.uuid4().hex
    session=repo.create_session(owner,registry.public()["active"],{"grade":10,"subject":"Mathematics"},"Synthetic")
    result=dialogue.turn(owner,session["id"],message,uuid.uuid4().hex)
    assert result["move"]!="missing_evidence"
    assert result["citations"]
    passages=[registry.knowledge().passage(c["id"]) for c in result["citations"]]
    assert all(p["unit_file_index"]==unit for p in passages)
    assert result["citations"][0]["id"] in {"normalized:tr01","normalized:ap01","normalized:qe01"}

def test_exact_screenshot_conversation_and_topic_switch(service):
    dialogue,repo,registry=service
    owner=uuid.uuid4().hex
    session=repo.create_session(owner,registry.public()["active"],{"grade":10,"subject":"Mathematics"},"Synthetic")
    def turn(message):return dialogue.turn(owner,session["id"],message,uuid.uuid4().hex)
    assert turn("Can you tell me about trigonometry")["citations"][0]["id"]=="normalized:tr01"
    topics=turn("what topics can you teach me then?")
    assert topics["move"]=="topic_navigation" and not topics["citations"]
    assert all(label in topics["reply"] for label in ("Trigonometry","Arithmetic Progressions","Quadratic Equations"))
    assert turn("quadratic equations")["citations"][0]["id"]=="normalized:qe01"
    assert turn("trigonometry")["citations"][0]["id"]=="normalized:tr01"

def test_no_new_subject_or_hidden_scope_is_invented(service):
    dialogue,repo,registry=service
    k=registry.knowledge()
    assert k.search("trigonometry",Scope(10,"Mathematics",unit=5))==[]
    assert k.search("trigonometry",Scope(9,"Mathematics"))==[]
    assert k.search("quantum trigonometry on Mars",Scope(10,"Mathematics"))==[]
    owner=uuid.uuid4().hex
    session=repo.create_session(owner,registry.public()["active"],{"grade":10,"subject":"Mathematics"},"Synthetic")
    result=dialogue.turn(owner,session["id"],"Explain photosynthesis",uuid.uuid4().hex)
    assert result["move"]=="missing_evidence"
    assert "Trigonometry" in result["reply"]
    assert not result["citations"]
