"""The evaluation's own answer-leak check (teaching policy TP-L1/TP-L2), separate from R4's guard.

It measures leaks; it never blocks anything. Values are compared with the dataset kernel, so "3*sqrt(3)",
"3√3" and "3 sqrt(3)" all count as the same number. Numbers that already appear in the question, or that
the student produced, are not leaks (TP-L "not a leak").
"""
from __future__ import annotations

import re

from socratic_data import math_kernel as mk

FULL, PARTIAL, NONE = "full", "partial", "none"

_COMPOUND = re.compile(r"[-+−]?\s*\d+(?:\.\d+)?\s*[-+−±]\s*\d*(?:\.\d+)?\s*(?:√|sqrt)\s*\(?\s*\d+\s*\)?")
_SQRT = re.compile(r"[-+−]?\s*\d*(?:\.\d+)?\s*\*?\s*(?:√|sqrt)\s*\(?\s*\d+\s*\)?(?:\s*/\s*\d+)?")
_NUMBER = re.compile(r"(?<![\w.])[-−]?\d+(?:\.\d+)?(?:\s*/\s*\d+)?(?!\.?\d)(?![A-Za-z_])")
_EXAMPLE = re.compile(r"(?:\blike|\be\.g\.|\bfor example|\bsuch as|\bformat)\s*:?\s*'[^']*'(?:\s*\((?:or\s+)?'[^']*'\))?", re.I)
_ASSERTS = re.compile(r"(?:=|\b(?:is|are|equals?|gives?|be)\b)\s*$", re.I)  # "x = 5", "the root is 5"
_EMPTY = re.compile(r"\bno\s+(?:real\s+)?(?:roots?|solutions?|values?|such\s+terms?|terms?)\b|\bnot?\s+(?:have|has)\s+(?:any\s+)?real\s+roots?\b", re.I)
_UNDEFINED = re.compile(r"\b(?:undefined|not\s+defined|does\s+not\s+exist|doesn't\s+exist)\b", re.I)
_VERDICT = re.compile(r"\b(?:(?:claim|statement|identity|it|this|that)\s+(?:is|isn't|is\s+not)\s+(?:true|false|correct|incorrect|valid|invalid|right|wrong)"
                      r"|(?:is|isn't|is\s+not)\s+an?\s+(?:ap|arithmetic\s+progression))\b", re.I)
_CLASS_WORDS = {
    "two_distinct_real": ["two distinct real", "two different real", "two unequal real"],
    "repeated_real": ["repeated real", "equal roots", "repeated root", "two equal real", "coincident roots", "equal (repeated)",
                      "real and equal", "equal real roots"],
    "no_real": ["no real roots", "no real solution", "not real", "imaginary roots", "complex roots"],
}


def _value(text: str):
    clean = text.replace("−", "-").replace("√", "sqrt").replace(" ", "")
    clean = re.sub(r"sqrt\(?(\d+)\)?", r"sqrt(\1)", clean)
    clean = re.sub(r"(\d)sqrt", r"\1*sqrt", clean)
    clean = clean.replace("±", "+")
    try:
        return mk.canonical(mk.exact(clean))
    except Exception:  # anything the kernel can't read exactly is simply not a candidate
        return None


def _candidates(text: str) -> list[tuple[str, bool]]:
    """(value, asserted) for every exact value in the text, in order. Asserted means it follows "=", "is",
    "are"…, or continues an asserted list ("are 2, -3 and 1")."""
    hits = []
    for pattern in (_COMPOUND, _SQRT, _NUMBER):
        for m in pattern.finditer(text):
            if not any(s <= m.start() < e for s, e, _ in hits) and (value := _value(m.group(0))) is not None:
                hits.append((m.start(), m.end(), value))
    found, previous_asserted, previous_end = [], False, 0
    for start, end, value in sorted(hits):
        before = text[max(0, start - 20):start]
        listed = previous_asserted and re.fullmatch(r"\s*(?:,|and|or|,\s*and)\s*", text[previous_end:start], re.I)
        asserted = bool(_ASSERTS.search(before) or listed)
        found.append((value, asserted))
        previous_asserted, previous_end = asserted, end
    return found


def numbers_in(text: str) -> list[str]:
    """Exact values written in the text: plain numbers, fractions, surds and a ± b√c forms."""
    return [v for v, _ in _candidates(text)]


def _same(a: str, b: str) -> bool:
    try:
        return mk.equivalent(a, b)
    except Exception:
        return False


def check(text: str, expected: dict, *, prompt: str = "", produced: list[dict] | None = None) -> dict:
    """Leak level of one tutor turn against the expected typed answer of the problem being worked on.

    A value the student already gave is never a leak. A value that also appears in the question counts only
    when the tutor asserts it ("x = 18", "the root is 18"), since a bare mention may just quote a given.
    """
    kind = expected["kind"]
    text = _EXAMPLE.sub(" ", text)  # "Answer like 'x = 2 or x = -3'" shows a format, not an answer
    produced_values = [str(x) for a in (produced or []) for x in (a.get("values") or [a.get("value")]) if x is not None]
    echoes = [v for v in (_value(p) for p in produced_values) if v]
    said_empty = any(a.get("kind") == "finite_set" and not a.get("values") for a in (produced or []))
    givens = numbers_in(prompt)
    said = [(v, asserted) for v, asserted in _candidates(text) if not any(_same(v, e) for e in echoes)]

    def mentioned(values: list[str]) -> list[str]:
        return [v for v in values if not any(_same(v, e) for e in echoes) and any(
            _same(v, s) and (asserted or not any(_same(v, g) for g in givens)) for s, asserted in said)]

    def result(level: str, reason: str = "", heuristic: bool = False) -> dict:
        return {"level": level, "reason": reason, "kind": kind, "heuristic": heuristic}

    if kind == "finite_set":
        values = expected["values"]
        if not values:  # repeating a student's own "no real roots" is an echo
            return result(FULL, "states there are no solutions") if _EMPTY.search(text) and not said_empty else result(NONE)
        hit = mentioned(values)
        if len(hit) == len(values):
            return result(FULL, f"states all {len(values)} value(s)")
        return result(PARTIAL, f"states {len(hit)} of {len(values)} values") if hit else result(NONE)
    if kind in ("scalar", "coefficients"):
        values = [expected["value"]] if kind == "scalar" else expected["values"]
        hit = mentioned(values)
        if hit and len(hit) == len(values):
            return result(FULL, "states the value" if kind == "scalar" else "states the coefficients")
        return result(PARTIAL, "states some coefficients") if hit else result(NONE)
    if kind == "defined_value":
        if not expected["defined"]:
            return result(FULL, "says it is undefined") if _UNDEFINED.search(text) else result(NONE)
        return result(FULL, "states the value") if mentioned([expected["value"]]) else result(NONE)
    if kind == "boolean":  # revealing a verdict counts whether or not it is the right one (MRBench)
        return result(FULL, "gives a true/false verdict", True) if _VERDICT.search(text) else result(NONE, "", True)
    if kind == "classification":
        words = _CLASS_WORDS.get(expected["value"], [expected["value"].replace("_", " ")])
        return result(FULL, "names the class", True) if any(w in text.lower() for w in words) else result(NONE, "", True)
    return result(NONE, f"kind {kind} is not checked", True)
