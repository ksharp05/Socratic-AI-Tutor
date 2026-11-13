"""The beta's safety front door must not get worse on any development case (R5, 14 Nov 2026).

See tests/regressions/README.md. Offline: no model, no key, no corpus.
"""
import json

import pytest

from socrates_beta.dialogue import DialogueService
from tutor_eval import beta_front_door as fd


@pytest.fixture(scope="module")
def results():
    return fd.run()


def test_no_case_regresses_against_the_baseline(results):
    cases, _ = results
    baseline = json.loads(fd.BASELINE.read_text(encoding="utf-8"))
    regressions, _ = fd.compare(cases, baseline)
    assert not regressions, "\n".join(f"{r['id']} ({r['metric']}, {r['lang']}): {r['routes']}" for r in regressions)


def test_every_scored_case_is_in_the_baseline(results):
    """A new fixture case must be added to the baseline in the same pull request, so its first result is reviewed."""
    cases, _ = results
    baseline = json.loads(fd.BASELINE.read_text(encoding="utf-8"))["cases"]
    missing = [r["id"] for r in cases if r["metric"] and r["id"] not in baseline]
    assert not missing, f"Run `python -m tutor_eval.beta_front_door --write-baseline`; missing: {missing[:10]}"


def test_no_unexpected_urgent_replies(results):
    _, summary = results
    assert summary["unexpected_urgent"] == 0


def test_gate_routes_match_the_real_dialogue_service(results):
    """The gate copies DialogueService.turn's screening order. The urgent and support branches run before any
    database or model work, so the real service can answer them with no repository: check that both agree."""
    service = DialogueService(repo=None, registry=None)
    cases, _ = results
    by_id = fd.load_cases_by_id()
    checked = 0
    for r in cases:
        for text, gate_route in zip(by_id[r["id"]]["turns"], r["routes"]):
            # Messages caught only after redaction take the database path; the gate test above covers them.
            if not (fd.urgent(text) or fd.emotional_support_reply(text)):
                continue
            if gate_route in fd.URGENT_KINDS or gate_route == "support":
                reply = service.turn("owner", "session", text, "request")
                expected = "emotional_support" if gate_route == "support" else "human_help"
                assert reply["move"] == expected, (r["id"], text)
                if gate_route != "support":
                    assert reply["safety_kind"] == gate_route, (r["id"], text)
                checked += 1
    assert checked > 50
