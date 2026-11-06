"""Explicit mathematical case invariants for parallel practice; no learner state."""
from __future__ import annotations

import copy
from fractions import Fraction as F
from math import isqrt

VERSION = "parallel-cases-v1"


def sign(value):
    return (value > 0) - (value < 0)


def signature(problem):
    """Cases, not full assessment equivalence. Inputs must be validated first."""
    task, g = problem["task_type"], problem["givens"]
    if task == "quadratic_solve":
        a, b, c = g["a"], g["b"], g["c"]
        discriminant = b*b - 4*a*c
        product, total = F(c, a), F(-b, a)
        roots = ("nonreal" if discriminant < 0 else
                 "zero" if discriminant == 0 and not b else
                 "positive" if discriminant == 0 and total > 0 else
                 "negative" if discriminant == 0 else
                 "mixed" if product < 0 else
                 "zero_positive" if not product and total > 0 else
                 "zero_negative" if not product else
                 "both_positive" if total > 0 else "both_negative")
        return {"discriminant_class": sign(discriminant),
                "rational_roots": discriminant >= 0 and isqrt(discriminant)**2 == discriminant,
                "leading_sign": sign(a), "unit_leading_magnitude": abs(a) == 1,
                "linear_term_zero": b == 0, "zero_root": c == 0,
                "root_sign_pattern": roots}
    if task in ("ap_term", "ap_sum", "ap_first"):
        first = F(g["a"]) if "a" in g else F(g["term"]) - (g["n"]-1)*F(g["d"])
        last = first + (g["n"]-1)*F(g["d"])
        case = {"direction": sign(F(g["d"])), "initial_sign": sign(first),
                "first_position": g["n"] == 1, "last_sign": sign(last)}
        if task == "ap_sum":
            case["sum_sign"] = sign(first + last)
        return case
    if task == "ap_count":
        count = 1 + F(g["last"]-g["a"], g["d"])
        return {"direction": sign(g["d"]), "initial_sign": sign(g["a"]),
                "last_sign": sign(g["last"]),
                "positive_integral_count": count >= 1 and count.denominator == 1,
                "first_position": count == 1}
    if task == "ap_difference":
        gap = g["n"]-g["m"]
        difference = F(g["term_n"]-g["term_m"], gap)
        return {"direction": sign(difference),
                "integral_difference": difference.denominator == 1,
                "index_order": sign(gap), "adjacent_positions": abs(gap) == 1,
                "includes_first_position": min(g["m"], g["n"]) == 1,
                "known_m_sign": sign(g["term_m"]), "known_n_sign": sign(g["term_n"])}
    if task == "ap_mean":
        return {"endpoint_order": sign(g["right"]-g["left"]),
                "left_sign": sign(g["left"]), "right_sign": sign(g["right"]),
                "mean_sign": sign(g["left"]+g["right"]),
                "integral_mean": (g["left"]+g["right"]) % 2 == 0}
    if task == "ap_ledger_term":
        return {"increment_sign": sign(F(g["prefix_sum"])-F(g["previous_sum"])),
                "earlier_sum_sign": sign(F(g["previous_sum"])),
                "later_sum_sign": sign(F(g["prefix_sum"])),
                "first_prefix": g["n"] == 2}
    if task == "trig_triangle_ratio":
        return {"ratio": g["ratio"], "reference": g["reference"],
                "leg_order": sign(g["opposite"]-g["adjacent"])}
    raise ValueError("Unsupported parallel task")


def invariant_answer_conflict(problem):
    """Cases whose invariant answer cannot be changed safely."""
    task, g = problem["task_type"], problem["givens"]
    case = signature(problem)
    if task == "quadratic_solve":
        return case["discriminant_class"] < 0 or case["zero_root"]
    if task == "ap_count":
        return not case["positive_integral_count"] or case["first_position"]
    if task == "ap_difference":
        return case["direction"] == 0
    if task == "ap_first":
        return case["initial_sign"] == 0
    if task == "ap_term":
        return case["last_sign"] == 0
    if task == "ap_sum":
        return case["sum_sign"] == 0
    if task == "ap_mean":
        return case["mean_sign"] == 0
    if task == "ap_ledger_term":
        return case["increment_sign"] == 0
    return False


def candidate(source, index):
    """Positive scaling preserves signs/cases; counts and ratios need new shapes."""
    task, g = source["task_type"], source["givens"]
    k = 2 + index % 31
    problem = copy.deepcopy(source)
    if task == "quadratic_solve":
        h = 1 if abs(g["a"]) == 1 else 2 + index % 7
        values = {"a": h*g["a"], "b": h*k*g["b"], "c": h*k*k*g["c"]}
    elif task in ("ap_term", "ap_sum", "ap_first"):
        position = 1 if g["n"] == 1 else 3 + index % 13
        first_scale = k if g["n"] == 1 else k*(position-1)
        difference_scale = k if g["n"] == 1 else k*(g["n"]-1)
        if task == "ap_first":
            values = {"d": difference_scale*g["d"], "n": position,
                      "term": first_scale*g["term"]}
        else:
            values = {"a": first_scale*g["a"], "d": difference_scale*g["d"], "n": position}
    elif task == "ap_count":
        old_count = 1 + F(g["last"]-g["a"], g["d"])
        if old_count.denominator != 1 or old_count <= 1:
            raise ValueError("Count case cannot supply a distinct safe answer")
        position = 3 + index % 13
        first = k*(position-1)*g["a"]
        difference = k*(int(old_count)-1)*g["d"]
        values = {"a": first, "d": difference, "last": first+(position-1)*difference}
    elif task == "ap_difference":
        difference = F(g["term_n"]-g["term_m"], g["n"]-g["m"])
        k = 1 + difference.denominator*k
        gap_scale = 1 if abs(g["n"]-g["m"]) == 1 else 2 + index % 11
        low = 1 if min(g["m"], g["n"]) == 1 else 3 + index % 17
        high = low + abs(g["n"]-g["m"])*gap_scale
        m, n = (low, high) if g["n"] > g["m"] else (high, low)
        values = {"m": m, "n": n,
                  "term_m": k*gap_scale*g["term_m"], "term_n": k*gap_scale*g["term_n"]}
    elif task == "ap_mean":
        k = 2*k + 1
        values = {"left": k*g["left"], "right": k*g["right"]}
    elif task == "ap_ledger_term":
        values = {"n": g["n"], "previous_sum": str(k*F(g["previous_sum"])),
                  "prefix_sum": str(k*F(g["prefix_sum"]))}
    elif task == "trig_triangle_ratio":
        opposite, adjacent, hypotenuse = [(5,12,13), (7,24,25), (8,15,17),
                                           (20,21,29), (9,40,41)][index % 5]
        if sign(opposite-adjacent) != sign(g["opposite"]-g["adjacent"]):
            opposite, adjacent = adjacent, opposite
        values = {"opposite": opposite*k, "adjacent": adjacent*k, "hypotenuse": hypotenuse*k,
                  "ratio": g["ratio"], "reference": g["reference"]}
    else:
        raise ValueError("Unsupported parallel task")
    problem["givens"] = values
    return problem
