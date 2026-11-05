"""Maths in plain, tested code: keys, grading, answer parsing, leak checks and buggy-rule diagnosis.

Keys come from the frozen dataset's own kernel (two independent routes must agree), vendored unchanged in
src/socratic_data/. This module runs only inside the math-tools server; answer keys never leave it.
"""
from __future__ import annotations

import re

from socratic_data import math_kernel as mk
from socratic_data.tasks import oracle_answer, primary_answer

_UNICODE = {"−": "-", "–": "-", "×": "*", "·": "*", "÷": "/", "²": "^2", "³": "^3", "√": "sqrt", "π": "pi"}
_NO_ROOTS = re.compile(r"\b(no (real )?(roots?|solutions?)|none|empty|∅)\b", re.I)


def compute_key(problem: dict) -> dict:
    """Return the typed key and whether two calculation routes agree."""
    key = primary_answer(problem)
    return {"key": key, "verified": bool(mk.answers_equivalent(key, oracle_answer(problem)))}


def normalise_expression(text: str) -> str:
    for src, dst in _UNICODE.items():
        text = text.replace(src, dst)
    text = re.sub(r"\\sqrt\{([^}]*)\}", r"sqrt(\1)", text)
    text = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)", text)
    text = re.sub(r"sqrt\s*(\d+)", r"sqrt(\1)", text)            # √3 -> sqrt(3)
    text = re.sub(r"(\d)\s*(sqrt|pi|\()", r"\1*\2", text)          # 2sqrt(3) -> 2*sqrt(3)
    text = re.sub(r"\)\s*(\d|sqrt|\()", r")*\1", text)
    return text.replace(" ", "")


def parse_answer(text: str, key: dict) -> dict:
    """Turn free text into the typed answer shape of `key`. Rules only; never judges correctness."""
    kind = key["kind"]
    raw = text.strip()
    if kind == "finite_set":
        if _NO_ROOTS.search(raw):
            values: list[str] = []
        else:
            body = re.sub(r"[a-zA-Z]\s*=\s*", " ", raw.replace("{", " ").replace("}", " "))
            body = re.sub(r"(?i)\b(roots?|are|is|and|or|the|answers?)\b", ",", body)
            parts = [p for p in re.split(r"[,;]+|\s{2,}", body) if p.strip()]
            values = [normalise_expression(p) for p in parts]
            values = [v for v in values if re.fullmatch(r"[0-9a-z+\-*/^().]+", v)]
            if not values:
                return {"ok": False, "reason": "Write your roots like: x = 2 or x = -3, or say 'no real roots'."}
        typed = {"kind": "finite_set", "values": values}
    elif kind == "scalar":
        # Recognise a few explicit English lead-ins without guessing at free-form reasoning.
        raw = re.sub(r"^\s*(?:(?:my|the) answer is|i think (?:the answer is|it(?:'s| is))|it(?:'s| is))\s*[:=]?\s*",
                     "", raw, flags=re.I)
        m = re.search(r"=?\s*([-+0-9a-z*/^().√ ]+)$", raw)
        typed = {"kind": "scalar", "value": normalise_expression(m.group(1) if m else raw)}
    else:
        return {"ok": False, "reason": f"Answers of kind '{kind}' are not supported in the POC yet."}
    for extra in ("unit",):
        if extra in key:
            typed[extra] = key[extra]
    return {"ok": True, "typed": typed, "display": _display(typed)}


def _display(typed: dict) -> str:
    if typed["kind"] == "finite_set":
        return "{" + ", ".join(typed["values"]) + "}" if typed["values"] else "no real roots"
    return str(typed.get("value"))


def grade(typed: dict, key: dict) -> dict:
    return mk.grade_mathematics(typed, key)


def _equivalent(a: str, b: str) -> bool:
    try:
        return bool(mk.equivalent(a, b))
    except Exception:  # unverified / unsupported expressions never count as a match
        return False


_NUMBER_LIKE = re.compile(r"[-+]?\s*\(?\s*(?:\d+(?:\.\d+)?(?:\s*/\s*\d+)?|sqrt\(\d+\))(?:\s*[-+*/]\s*(?:\d+|sqrt\(\d+\)))*\)?")


def leak_check(text: str, key: dict) -> dict:
    """A reply leaks when it states every value of the key (or 'no real roots' for an empty key)."""
    norm = normalise_expression(text.lower()).replace("−", "-")
    if key["kind"] == "finite_set":
        values = key["values"]
        if not values:
            return {"leak": bool(_NO_ROOTS.search(text)), "reason": "states that there are no real roots"}
        candidates = {c.strip() for c in _NUMBER_LIKE.findall(norm) if c.strip()}
        hits = [v for v in values if any(_equivalent(c, v) for c in candidates)]
        return {"leak": len(hits) == len(values), "reason": f"mentions {len(hits)} of {len(values)} key values"}
    if key["kind"] == "scalar":
        candidates = {c.strip() for c in _NUMBER_LIKE.findall(norm) if c.strip()}
        return {"leak": any(_equivalent(c, str(key["value"])) for c in candidates), "reason": "mentions the value"}
    return {"leak": False, "reason": "kind not checked"}


# ---- Diagnostician's buggy rules (written separately from the simulator's rules in tutor_eval) ----

def _as_set(values: list[str]) -> set[str]:
    out = set()
    for v in values:
        try:
            out.add(mk.canonical(mk.exact(v)))
        except Exception:
            out.add(v)
    return out


def diagnose_response(problem: dict, key: dict, typed: dict) -> list[dict]:
    """Return supported rules matching a wrong answer; callers must handle ambiguity."""
    if problem.get("task_type") == "trig_triangle_ratio" and typed.get("kind") == "scalar" and key.get("kind") == "scalar":
        if _equivalent(str(typed.get("value", "")), str(key["value"])):
            return []
        g = problem["givens"]
        o, a, h = g["opposite"], g["adjacent"], g["hypotenuse"]
        if any(type(v) is not int or v <= 0 for v in (o,a,h)) or o*o+a*a != h*h or g.get("reference") not in ("A", "C"):
            return []
        original = {"sin":(o,h), "cos":(a,h), "tan":(o,a), "csc":(h,o), "sec":(h,a), "cot":(a,o)}
        if g["reference"] == "C":
            o,a = a,o
        candidates = []
        if g["reference"] == "C" and g.get("ratio") in original:
            candidates.append(("tr_m01", original[g["ratio"]], "kept the side labels for the other acute angle"))
        if g.get("ratio") == "sin":
            candidates.append(("tr_m02", (a,h), "used adjacent over hypotenuse for sine"))
        if g.get("ratio") == "tan":
            candidates.append(("tr_m04", (a,o), "used adjacent over opposite for tangent"))
        return [{"misconception_id":mid, "rule":rule} for mid,(numerator,denominator),rule in candidates
                if _equivalent(str(typed.get("value", "")), f"{numerator}/{denominator}")]
    if problem["task_type"] != "quadratic_solve" or typed.get("kind") != "finite_set":
        return []
    truth, given = _as_set(key["values"]), _as_set(typed["values"])
    g = problem["givens"]
    if truth and g.get("b") and given == _as_set([f"-({v})" for v in key["values"]]):
        return [{"misconception_id": "qe_m02", "rule": "dropped the sign of b, so every root changed sign"}]
    if given == truth or not given or not given < truth:
        return []
    found = []
    if g.get("b") == 0 and len(truth) == 2 and all(not v.startswith("-") for v in given):
        found.append({"misconception_id": "qe_m05", "rule": "kept only the positive square root"})
    if g.get("c") == 0 and "0" in truth and "0" not in given:
        found.append({"misconception_id": "qe_m04", "rule": "lost the root x = 0 by dividing by x"})
    elif len(given) == 1:
        found.append({"misconception_id": "qe_m04", "rule": "checked only one factor"})
    return found
