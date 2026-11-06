"""Versioned source notes do not mutate the frozen pack or learner history."""
import hashlib,json,uuid
from pathlib import Path
import pytest
from socrates_beta.public_index import prepare_public_index
from socrates_beta.reference_notes import SupplementedRegistry
from socrates_beta.repository import Repository
from socrates_beta.dialogue import DialogueService
from socrates_beta.ports import Scope
CODE=Path(__file__).resolve().parents[1]
@pytest.fixture
def notes(tmp_path):
    base=prepare_public_index(CODE,tmp_path/"index")
    reg=SupplementedRegistry(base,CODE)
    return reg,Repository(tmp_path/"learner.sqlite")

@pytest.mark.parametrize("concept",["qe01","qe03","tr01","tr02","tr03","ap01","ap02","ap03"])
def test_note_identity_and_historical_source_are_both_preserved(notes,concept):
    reg,repo=notes;k=reg.knowledge()
    original=k.base.passage("normalized:"+concept)
    assert k.passage(original["id"])==original
    note=k.passage("beta-reference-v1:"+concept)
    assert note["id"]!=original["id"] and note["source_sha256"]==reg.digest
    assert note["human_review_status"]=="pending" and note["approved"]==0
    assert note["source_url"].startswith("https://openstax.org/books/")
    assert note["page"]==0 and note["kind"]=="reference_note"
    assert k.base.dataset_id==k.dataset_id

def test_retrieved_notes_are_scoped_and_use_the_correct_degree(notes):
    reg,_=notes;k=reg.knowledge()
    original_sha=hashlib.sha256(k.base.path.read_bytes()).hexdigest()
    hits=k.search("quadratic equations",Scope(10,"Mathematics"))
    assert any(p["id"]=="beta-reference-v1:qe01" and "highest nonzero power two" in p["text"] for p in hits)
    assert all(p["unit_file_index"]==4 for p in hits)
    assert k.search("trigonometry",Scope(10,"Mathematics",unit=5))==[]
    assert k.search("trigonometry",Scope(9,"Mathematics"))==[]
    assert hashlib.sha256(k.base.path.read_bytes()).hexdigest()==original_sha
    assert reg.public()["reference_notes"]["count"]==8

@pytest.mark.parametrize("reply,error",[
 ("A quadratic equation is a polynomial with a nonzero squared coefficient after collecting terms. Which coefficient is nonzero?","missing_quadratic_qualifier"),
 ("The graph curves like a U rather than a straight line. What shape is the graph?","unsupported_graph_fact"),
])
def test_unsupported_definition_or_graph_fact_is_not_published(notes,reply,error):
    reg,repo=notes
    class Language:
        def generate(self,system,context):
            return json.dumps({"reply":reply,"citations":[p["id"] for p in context["excerpts"][:1]]})
    owner=uuid.uuid4().hex;s=repo.create_session(owner,reg.public()["active"],{"grade":10,"subject":"Mathematics"},"Synthetic")
    result=DialogueService(repo,reg,Language()).turn(owner,s["id"],"What is a quadratic equation?",uuid.uuid4().hex)
    assert result["provider_status"]=="provider_failed_source_fallback"
    assert result["validation_error"]==error
    assert "highest" in result["reply"]
    assert result["reference_bundle"].startswith("teaching-notes-v1:")

def test_precise_definition_passes_and_supplement_can_be_saved_as_a_card(notes):
    reg,repo=notes
    class Language:
        def generate(self,system,context):
            return json.dumps({"reply":"A quadratic equation has highest nonzero power two after collecting terms. Which highest power defines a quadratic?",
                               "citations":["beta-reference-v1:qe01"]})
    owner=uuid.uuid4().hex;s=repo.create_session(owner,reg.public()["active"],{"grade":10,"subject":"Mathematics"},"Synthetic")
    result=DialogueService(repo,reg,Language()).turn(owner,s["id"],"What is a quadratic equation?",uuid.uuid4().hex)
    assert result["provider_status"]=="live_accepted"
    assert repo.observations(owner)[0]["node"]=="qe01"
    p=reg.knowledge().passage(result["citations"][0]["id"])
    card=repo.add_card(owner,s["dataset"],p)
    assert card["source"]["source_sha256"]==reg.digest
    assert card["source"]["page"]==0
    assert "highest nonzero power two" in card["back"]
