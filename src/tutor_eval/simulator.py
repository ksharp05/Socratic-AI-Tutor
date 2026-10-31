"""Simulated student (R5), written independently of the tutor: it answers with the dataset kernel and its own
buggy rules, never with tutor code. Its parameters and transition rules are pre-registered in
eval/PREREGISTRATION.md; change them only before the freeze.

- Answering: an active misconception with a rule for the problem gives that rule's wrong answer. Otherwise
  the student is right with probability m(1 - SLIP) + (1 - m)GUESS, where m is mastery of the problem's concepts.
- Rule 1 (clearing): at the end of a session a misconception clears with probability P_CLEAR, but only if the
  tutor named it and targeted it.
- Rule 2 (mastery): each concept of an item answered correctly with at most one hint gains LEARN * (1 - m).
- Rule 3 (telling): when the tutor gives an item's answer away, the student copies it for that item only.
"""
from __future__ import annotations

import random
import statistics
from fractions import Fraction

import sympy as sp

from socratic_data import math_kernel as mk
from socratic_data import tasks as kt

SLIP, GUESS, LEARN, P_CLEAR = 0.10, 0.05, 0.15, 0.7
CLASSES = ["two_distinct_real", "repeated_real", "no_real"]


def correct_answer(problem: dict) -> dict:
    return kt.primary_answer(problem)


# ------------------------------------------------------------------ buggy rules, one per misconception
def _roots(g):
    return kt.real_quadratic_roots(g["a"], g["b"], g["c"])


def _sides(g):
    o, a, h = g["opposite"], g["adjacent"], g["hypotenuse"]
    return (a, o, h) if g["reference"] == "C" else (o, a, h)


def _classify(d):
    return {"kind": "classification", "value": "two_distinct_real" if d > 0 else "repeated_real" if d == 0 else "no_real"}


def _qe_m02(t, g):  # a coefficient is always the unsigned number
    if t == "quadratic_coefficients":
        return {"kind": "coefficients", "values": [mk.canonical(abs(x)) for x in kt.polynomial_coefficients(g)]}
    if t == "quadratic_classify":
        return _classify(g["b"] ** 2 - 4 * abs(g["a"]) * abs(g["c"]))


def _qe_m04(t, g):  # only one factor is checked, or dividing by x is "safe": a root is lost
    if t == "quadratic_solve" and len(r := _roots(g)) == 2:
        return mk.finite_set([x for x in r if x != 0] if 0 in r else r[:1])


def _qe_m05(t, g):  # a square root gives only the positive value
    if t == "quadratic_solve" and len(r := _roots(g)) == 2 and (pos := [x for x in r if x >= 0]) and len(pos) < 2:
        return mk.finite_set(pos)


def _qe_m06(t, g):  # ± is one operation: only the + branch
    if t == "quadratic_solve" and len(r := _roots(g)) == 2:
        return mk.finite_set([max(r)])


def _qe_m08(t, g):  # a repeated root means two different values
    if t == "quadratic_classify" and g["b"] ** 2 - 4 * g["a"] * g["c"] == 0:
        return _classify(1)


def _qe_m09(t, g):  # a negative discriminant means two negative real roots
    if t == "quadratic_classify" and g["b"] ** 2 - 4 * g["a"] * g["c"] < 0:
        return _classify(1)


def _qe_m10(t, g):  # every algebraic root is accepted in a word problem
    if t == "quadratic_rectangle":
        return mk.scalar((-g["gap"] - sp.sqrt(g["gap"] ** 2 + 4 * g["area"])) / 2, "units")


def _ap_m01(t, g):  # a constant ratio makes an AP
    if t == "ap_recognition" and 0 not in (terms := g["terms"]) and len({Fraction(b, a) for a, b in zip(terms, terms[1:])}) == 1:
        return {"kind": "boolean", "value": True}


def _ap_m02(t, g):  # d is earlier term minus later term
    if t == "ap_term" and g["d"]:
        return mk.scalar(g["a"] - (g["n"] - 1) * g["d"])


def _ap_m03(t, g):  # the nth term is a + n*d
    if t == "ap_term":
        return mk.scalar(g["a"] + g["n"] * g["d"])
    if t == "ap_sum":
        return mk.scalar(sp.Rational(g["n"] * (2 * g["a"] + g["n"] * g["d"]), 2))


def _ap_m04(t, g):  # the nth term and the sum of n terms are the same quantity
    if t == "ap_sum":
        return mk.scalar(g["a"] + (g["n"] - 1) * g["d"])
    if t == "ap_ledger_term":
        return mk.scalar(mk.exact(g["prefix_sum"]))


def _ap_m05(t, g):  # an AP must increase
    if t == "ap_recognition" and len(diffs := {b - a for a, b in zip(g["terms"], g["terms"][1:])}) == 1 and diffs.pop() < 0:
        return {"kind": "boolean", "value": False}
    if t == "ap_term" and g["d"] < 0:
        return mk.scalar(g["a"] + (g["n"] - 1) * abs(g["d"]))


def _ap_m06(t, g):  # any real n is a term position
    if t == "ap_count" and g["d"] and (n := 1 + Fraction(g["last"] - g["a"], g["d"])).denominator != 1 and n >= 1:
        return mk.finite_set([sp.Rational(n.numerator, n.denominator)], "terms")


def _ap_m07(t, g):  # the difference of two terms is d, whatever the index gap
    if t == "ap_difference" and abs(g["n"] - g["m"]) != 1:
        return mk.scalar(g["term_n"] - g["term_m"])


def _ap_m08(t, g):  # the number of terms equals the number of gaps
    if t == "ap_count" and g["d"] and (n := Fraction(g["last"] - g["a"], g["d"])).denominator == 1 and n >= 1:
        return mk.finite_set([sp.Integer(n.numerator)], "terms")


def _ap_m10(t, g):  # a familiar-looking pattern is an AP
    if t == "ap_recognition":
        return {"kind": "boolean", "value": True}


def _tr_m01(t, g):  # opposite and adjacent keep their names whichever angle is the reference
    if t in ("trig_triangle_ratio", "trig_scaled_triangle") and g["reference"] == "C":
        return mk.scalar(kt.ratio_from_sides(g["ratio"], g["opposite"], g["adjacent"], g["hypotenuse"]))


def _tr_m02(t, g):  # sine is adjacent over hypotenuse
    if t in ("trig_triangle_ratio", "trig_scaled_triangle") and g["ratio"] == "sin":
        o, a, h = _sides(g)
        return mk.scalar(sp.Rational(a, h))


def _tr_m03(t, g):  # cosine is the reciprocal of sine
    if t in ("trig_triangle_ratio", "trig_scaled_triangle") and g["ratio"] == "cos":
        o, a, h = _sides(g)
        return mk.scalar(sp.Rational(h, o)) if o else None


def _tr_m04(t, g):  # tangent is cosine over sine
    if t in ("trig_triangle_ratio", "trig_scaled_triangle") and g["ratio"] == "tan":
        o, a, h = _sides(g)
        return mk.scalar(sp.Rational(a, o)) if o else None


def _tr_m07(t, g):  # an undefined ratio has value zero
    if t in ("trig_standard_value", "trig_domain"):
        return {"kind": "defined_value", "defined": True, "value": "0"}


def _tr_m08(t, g):  # a larger similar triangle has a larger sine
    if t == "trig_scaled_triangle" and g.get("scale", 1) > 1:
        o, a, h = _sides(g)
        value = kt.ratio_from_sides(g["ratio"], o, a, h)
        return mk.scalar(value * g["scale"]) if value is not None else None


def _tr_m10(t, g):  # one matching substitution proves an identity
    if t == "trig_identity_truth":
        return {"kind": "boolean", "value": True}


def _qe_m01(t, g):  # any equation that shows x squared is quadratic
    if t == "quadratic_degree":
        return {"kind": "classification", "value": "quadratic"}
    if t == "quadratic_coefficients" and kt.polynomial_coefficients(g)[0] == 0:  # misses that the x² terms cancel
        a, b, c = kt.polynomial_coefficients(g)
        return {"kind": "coefficients", "values": [mk.canonical(g["p"] * g["r"]), mk.canonical(b), mk.canonical(c)]}


def _qe_m03(t, g):  # the quadratic formula still applies when a = 0, so it is still "quadratic"
    if t == "quadratic_degree" and kt.polynomial_coefficients(g)[0] == 0:
        return {"kind": "classification", "value": "quadratic"}


def _qe_m07(t, g):  # the discriminant is a root: one value, so a "repeated" root
    if t == "quadratic_classify" and g["b"] ** 2 - 4 * g["a"] * g["c"] != 0:
        return {"kind": "classification", "value": "repeated_real"}


def _ap_m09(t, g):  # the middle of three AP terms is their geometric mean
    if t == "ap_mean" and g["left"] * g["right"] >= 0:
        return mk.scalar(sp.sqrt(g["left"] * g["right"]))


def _tr_m05(t, g):  # sin²θ read as the sine of θ², so the square is dropped
    if t == "trig_square_value" and (value := kt.standard_ratio(g["ratio"], g["angle_degrees"])) is not None:
        return mk.scalar(g["factor"] * value)


def _tr_m06(t, g):  # the angle is taken as radians, as software would
    if t == "trig_standard_value":
        value = float(sp.N(getattr(sp, g["ratio"])(g["angle_degrees"]) * g.get("coefficient", 1)))
        return {"kind": "defined_value", "defined": True, "value": mk.canonical(sp.Rational(str(round(value, 4))))}


def _tr_m09(t, g):  # squaring a sum gives only the sum of the squares
    if t == "trig_identity_truth" and g["identity_id"] == "false_square_expansion":
        return {"kind": "boolean", "value": True}


RULES = {"qe_m01": _qe_m01, "qe_m03": _qe_m03, "qe_m07": _qe_m07, "ap_m09": _ap_m09, "tr_m05": _tr_m05,
         "tr_m06": _tr_m06, "tr_m09": _tr_m09, "qe_m02": _qe_m02, "qe_m04": _qe_m04, "qe_m05": _qe_m05, "qe_m06": _qe_m06, "qe_m08": _qe_m08,
         "qe_m09": _qe_m09, "qe_m10": _qe_m10, "ap_m01": _ap_m01, "ap_m02": _ap_m02, "ap_m03": _ap_m03,
         "ap_m04": _ap_m04, "ap_m05": _ap_m05, "ap_m06": _ap_m06, "ap_m07": _ap_m07, "ap_m08": _ap_m08,
         "ap_m10": _ap_m10, "tr_m01": _tr_m01, "tr_m02": _tr_m02, "tr_m03": _tr_m03, "tr_m04": _tr_m04,
         "tr_m07": _tr_m07, "tr_m08": _tr_m08, "tr_m10": _tr_m10}
# Every misconception has a rule. Where a rule doesn't apply to a problem on its own concept, the student gives a
# generic wrong answer there instead (logged as "<id>:generic").


def generic_wrong(answer: dict) -> dict:
    """A plausible wrong answer of the same kind, for slips and for misconceptions without a rule."""
    kind = answer["kind"]
    if kind == "scalar":
        return {**answer, "value": mk.canonical(mk.exact(answer["value"]) + 1)}
    if kind == "finite_set":
        values = answer["values"]
        new = values[:-1] if len(values) > 1 else [mk.canonical(mk.exact(values[0]) + 1)] if values else ["0"]
        return {**answer, "values": new}
    if kind == "boolean":
        return {"kind": "boolean", "value": not answer["value"]}
    if kind == "classification":
        options = [c for c in CLASSES if c != answer["value"]]
        return {"kind": "classification", "value": options[0]}
    if kind == "coefficients":
        a, b, c = answer["values"]
        return {"kind": "coefficients", "values": [a, mk.canonical(-mk.exact(b)) if mk.exact(b) else "1", c]}
    if kind == "defined_value":
        return {"kind": "defined_value", "defined": True, "value": "0"} if not answer["defined"] else \
               {"kind": "defined_value", "defined": False, "value": None}
    raise ValueError(f"unknown answer kind {kind}")


def render(answer: dict) -> str:
    """The answer as a student would type it."""
    kind = answer["kind"]
    if kind == "finite_set":
        values = [v.replace("*", "") for v in answer["values"]]
        if answer.get("unit") == "terms":  # a count of terms, not roots
            return " or ".join(values) if values else "there is no such term"
        return "no real roots" if not values else " or ".join(f"x = {v}" for v in values)
    if kind == "scalar":
        return answer["value"].replace("*", "")
    if kind == "boolean":
        return "yes" if answer["value"] else "no"
    if kind == "classification":
        return answer["value"].replace("_", " ")
    if kind == "coefficients":
        return ", ".join(f"{n} = {v}" for n, v in zip("abc", answer["values"]))
    return "undefined" if not answer["defined"] else answer["value"]


def is_correct(given: dict, expected: dict) -> bool | None:
    """Graded by the dataset kernel. None means the answer could not be scored."""
    graded = mk.grade_mathematics(given, expected)
    return graded["correct"] if graded["scorable"] else None


class Student:
    """One simulated student, built from a card. The tutor never sees the card."""

    def __init__(self, card: dict, catalogue: dict, seed: int):
        hidden = card["hidden_card"]
        self.id = card["student_id"]
        self.rng = random.Random(f"{card['student_id']}:{seed}")
        self.mastery = dict(hidden["true_mastery_by_concept"])
        self.active = list(hidden["seeded_misconception_ids"])
        self.seeded = list(self.active)
        self.persona = hidden.get("persona", {})
        self.catalogue = catalogue
        self.told: set[str] = set()  # items whose answer the tutor gave away (rule 3)

    def answer(self, problem: dict, question_id: str | None = None) -> dict:
        """{"typed", "text", "rule"}: rule names why the answer is what it is."""
        right = correct_answer(problem)
        if question_id and question_id in self.told:
            return {"typed": right, "text": render(right), "rule": "copied_from_tutor"}
        for m in self.active:
            rule = RULES.get(m)
            buggy = rule(problem["task_type"], problem["givens"]) if rule else None
            if buggy is not None and not mk.answers_equivalent(buggy, right):
                return {"typed": buggy, "text": render(buggy), "rule": m}
            if buggy is None and self.catalogue.get(m, {}).get("concept_id") in problem["concept_ids"]:
                # the rule doesn't fit this task type, but the item is on the misconception's concept
                wrong = generic_wrong(right)
                return {"typed": wrong, "text": render(wrong), "rule": f"{m}:generic"}
        m = statistics.fmean([self.mastery.get(c, 0.5) for c in problem["concept_ids"]] or [0.5])
        if self.rng.random() < m * (1 - SLIP) + (1 - m) * GUESS:
            return {"typed": right, "text": render(right), "rule": "mastery"}
        wrong = generic_wrong(right)
        return {"typed": wrong, "text": render(wrong), "rule": "slip"}

    def learn(self, concept_ids: list[str]) -> None:  # rule 2
        for c in concept_ids:
            m = self.mastery.get(c, 0.5)
            self.mastery[c] = m + LEARN * (1 - m)

    def end_session(self, named: set[str], targeted: set[str]) -> list[str]:  # rule 1
        cleared = [m for m in self.active if m in named and m in targeted and self.rng.random() < P_CLEAR]
        self.active = [m for m in self.active if m not in cleared]
        return cleared

    # -------------------------------------------------------------- what the student says
    def opener(self, problem_prompt: str, answer: dict) -> str:
        return f"For this one: {problem_prompt} I got {answer['text']}. Is that right?"

    def belief(self) -> str:
        rule = next((self.catalogue[m]["incorrect_rule"] for m in self.active if m in self.catalogue), None)
        if not rule:
            return "I'm not sure. Can you give me a hint?"
        return f"I thought {rule[0].lower()}{rule[1:]}"


def expression_rate(card: dict, catalogue: dict, problems: list[dict], runs: int = 20) -> dict:
    """Validation (before any tutoring): how often each seeded misconception shows up on the problems it applies to."""
    shown: dict[str, list[bool]] = {m: [] for m in card["hidden_card"]["seeded_misconception_ids"]}
    for run in range(runs):
        student = Student(card, catalogue, seed=run)
        for problem in problems:
            result = student.answer(problem)
            for m in shown:
                if result["rule"] in (m, f"{m}:generic"):
                    shown[m].append(True)
    return {m: len(v) / runs for m, v in shown.items()}
