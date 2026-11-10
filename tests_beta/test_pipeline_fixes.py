"""No-model pipeline fixes from the 10 Nov 2026 deep dive: retrieval floor and vocabulary, topic tracking,
narrower active-problem rule, uncertainty and feedback, honest no-evidence replies. Offline, public index only."""
import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from socrates_beta.api import create_app
from socrates_beta.ports import Scope
from socrates_beta.public_index import prepare_public_index
from socrates_beta.reference_notes import SupplementedRegistry
from socrates_beta.repository import Repository

MAIN = Path(__file__).resolve().parents[1]
SCOPE = Scope(10, "Mathematics", None, None)
H = {"X-Socrates-Request": "1"}


@pytest.fixture(scope="module")
def registry(tmp_path_factory):
    return prepare_public_index(MAIN, tmp_path_factory.mktemp("public") / "index")


@pytest.fixture(scope="module")
def knowledge(registry):
    return SupplementedRegistry(registry, MAIN).knowledge() if not hasattr(registry.knowledge(), "extra_text") else registry.knowledge()


def ids(knowledge, text):
    return [p["id"].split(":")[-1] for p in knowledge.search(text, SCOPE, 3)]


@pytest.mark.parametrize("text", ["girls are naturally bad at maths, right?", "My parents fight a lot at home and I can't focus",
                                  "my maths teacher is a bitch, she gave me zero"])
def test_filler_words_no_longer_retrieve_passages(knowledge, text):
    assert ids(knowledge, text) == []


@pytest.mark.parametrize("text,unit", [("AP ka nth term nikalne ka formula kya hai", "ap"), ("द्विघात समीकरण का विविक्तकर क्या होता है?", "qe"),
                                       ("sir please explain in easy words what is trigonometry", "tr"),
                                       ("what the fuck is a discriminant, my teacher explains like shit", "qe"),
                                       ("what are the roots of a quadratic", "qe")])
def test_questions_reach_their_chapter(knowledge, text, unit):
    found = ids(knowledge, text)
    assert found and found[0].startswith(unit), found


class Language:
    def __init__(self, citations=True):
        self.citations, self.calls = citations, 0

    def health(self):
        return {"mode": "live", "model": "fake"}

    def generate(self, system, context):
        self.calls += 1
        cites = [context["excerpts"][0]["id"]] if self.citations else []
        return json.dumps({"reply": f"What is one detail you notice in step {self.calls}?", "citations": cites})


def chat(language, registry, tmp_path, turns):
    app = create_app({"app_root": str(MAIN), "data_directory": str(tmp_path), "assessment_policy": "reference_checked_beta",
                      "require_live_consent": False}, live=language is not None, language=language, registry=registry,
                      repository=Repository(tmp_path / "obs.sqlite"), browser_secret=b"x" * 32, testing=True)
    out = []
    with TestClient(app) as client:
        sid = client.post("/api/sessions", json={"grade": 10, "subject": "Mathematics", "title": "t"}, headers=H).json()["id"]
        for text in turns:
            out.append(client.post("/api/chat", json={"session_id": sid, "text": text, "request_id": uuid.uuid4().hex}, headers=H).json())
    return out


def test_a_new_question_mid_sentence_changes_topic(registry, tmp_path):
    first, second = chat(Language(), registry, tmp_path, ["What is an arithmetic progression?", "ok now explain what sin theta is"])
    assert all(r.split(":")[-1].startswith("tr") for r in second["retrieval"]["ids"]), second["retrieval"]


def test_dead_focus_does_not_stick(registry, tmp_path):
    turns = chat(Language(), registry, tmp_path, ["you idiot", "ok fine, what is an AP?"])
    assert turns[0]["move"] == "missing_evidence" and turns[1]["move"] != "missing_evidence"


def test_method_question_is_not_an_active_problem(registry, tmp_path):
    (r,) = chat(Language(), registry, tmp_path, ["How do I solve quadratic equations by factorisation?"])
    assert r["move"] != "active_problem_coaching"


def test_uncertainty_and_feedback_change_the_move(registry, tmp_path):
    turns = chat(Language(), registry, tmp_path, ["What is the common difference?", "i still dont get it", "your answers are so long and boring"])
    assert turns[1]["move"] == "break_into_one_step" and turns[2]["move"] == "break_into_one_step"


def test_empty_citations_give_an_honest_reply_not_a_random_sentence(registry, tmp_path):
    (r,) = chat(Language(citations=False), registry, tmp_path, ["What is the common difference of an AP?"])
    assert r["provider_status"] == "live_no_evidence" and r["citations"] == []
    assert "rather not guess" in r["reply"]


def test_missing_evidence_reply_is_warm_and_in_the_learners_language(registry, tmp_path):
    (r,) = chat(None, registry, tmp_path, ["mujhe zero ka matlab samjhao natural numbers mein"])
    assert r["move"] == "missing_evidence" and "guess nahi" in r["reply"]
