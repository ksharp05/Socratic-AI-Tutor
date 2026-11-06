"""Opt-in public-practice protocol v2. Legacy simulator and studies stay unchanged.

Only message formatting changes. Typed answers, randomness, misconception rules,
learning and clearing probabilities remain those of the legacy Student.
"""
from __future__ import annotations

from tutor_validation import exact_reference as reference
from socratic_data import tasks
from . import simulator as legacy

VERSION = "public-practice-protocol-v2"
SUPPORTED = frozenset({
    "quadratic_solve", "ap_term", "ap_sum", "ap_first", "ap_difference",
    "ap_count", "ap_mean", "ap_ledger_term", "trig_triangle_ratio",
})


def render(answer):
    """Preserve the chosen answer; distinguish a term count from a root set."""
    if answer.get("kind") == "finite_set" and answer.get("unit") == "terms":
        values = answer["values"]
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            raise ValueError("Term-count values must be an exact expression list")
        return " or ".join(values) + " terms" if values else "no valid term count"
    return legacy.render(answer)


def support(problem):
    """Mathematical support, not misconception, language or trajectory coverage."""
    if not isinstance(problem, dict) or problem.get("task_type") not in SUPPORTED:
        return {"supported": False, "reason": "outside_declared_task_scope", "protocol": VERSION}
    try:
        answer = tasks.primary_answer(problem)
        verified = reference.validate(problem, answer)["status"] == "verified"
        return {"supported": verified, "reason": "exact_reference_verified" if verified else "not_reference_verified",
                "protocol": VERSION, "scope": "exact answers and canonical messages only",
                "trajectory_coverage": False, "human_learning_validation": False}
    except (ValueError, KeyError, TypeError, ZeroDivisionError, OverflowError):
        return {"supported": False, "reason": "invalid_or_unverified_problem", "protocol": VERSION}


class StudentV2(legacy.Student):
    """Explicit opt-in adapter; the frozen harness still selects legacy.Student."""
    def answer(self, problem, question_id=None):
        result = super().answer(problem, question_id)
        return {**result, "text": render(result["typed"]), "protocol_version": VERSION}
