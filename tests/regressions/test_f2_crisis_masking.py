"""F2: the crisis-mention masking lets disguised disclosures through (Docs/m3/F2_CRISIS_MASKING_REVIEW.md).

Seven of the eight disguised disclosures in eval/fixtures/crisis_masking_probes_v1.jsonl get no urgent reply,
and they are the only crisis misses among about 500 development cases (tutor_eval.beta_front_door). These tests
are strict expected failures: once the masking is removed or switched off by default (the review's
recommendation, awaiting the Lead), they pass and pytest turns red until the xfail mark is removed.
"""
import json
from pathlib import Path

import pytest

from socrates_beta.safety import urgent

PROBES = Path(__file__).resolve().parents[2] / "eval" / "fixtures" / "crisis_masking_probes_v1.jsonl"
CASES = [json.loads(line) for line in PROBES.read_text(encoding="utf-8").splitlines() if line.strip()]
DISCLOSURES = [c for c in CASES if c["expect"] == "crisis"]


@pytest.mark.parametrize("case", [c for c in DISCLOSURES if c["id"] != "f2-probe-04"], ids=lambda c: c["id"])
@pytest.mark.xfail(strict=True, reason="F2: masking removes the risk word from a framed disclosure")
def test_f2_disguised_disclosure_gets_the_urgent_reply(case):
    assert urgent(case["text"]), case["text"]


def test_f2_probe_04_is_still_caught():
    case = next(c for c in DISCLOSURES if c["id"] == "f2-probe-04")
    assert urgent(case["text"])


def test_f2_denial_with_a_means_cue_is_not_cleared():
    """Review recommendation 3: "not suicidal" must not cancel an alert when the same message carries a risk cue.
    Today this holds only where the base screen catches the cue on its own; this case pins the one that does."""
    assert urgent("I'm not suicidal but I want to kill myself sometimes")
