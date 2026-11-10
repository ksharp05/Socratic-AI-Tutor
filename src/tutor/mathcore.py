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
# "{}" or "∅" on its own. \b cannot match around these symbols, so they need their own pattern.
_EMPTY_SYMBOL = re.compile(r"^\s*(?:\{\s*\}|∅)\s*[.!]?\s*$")
_NO_COUNT = r"\bno (?:valid |positive integer )?(?:term )?counts?\b"
_AP_NAME = r"(?:ap|a\.p\.|arithmetic progression|progression|sequence)"
_IN_AP = rf"(?:\s+in\s+(?:this|the)\s+{_AP_NAME})?"
# A student's whole answer, so "no such term in my notes, can you help?" stays a question.
# Endings such as "in this AP" and "exists" are accepted (finding 2).
NO_TERM_ANSWER = re.compile(
    _NO_COUNT + rf"|\bno (?:such |valid )?terms?(?:\s+exists?)?{_IN_AP}(?:\s+exists?)?\s*[.!]?\s*$", re.I)
# The whole answer is the empty set the question asks for: "{}", "∅", "empty set", "none",
# "no such (finite) AP (exists)" (finding 1). Term-count answers only.
EMPTY_SET_ANSWER = re.compile(
    rf"^\s*(?:(?:my|the) answer is\s*[:=]?\s*)?"
    rf"(?:\{{\s*\}}|∅|(?:the\s+)?empty\s+set|none"
    rf"|(?:there\s+(?:is|are)\s+)?no\s+such\s+(?:finite\s+)?{_AP_NAME}(?:\s+exists?)?)"
    rf"\s*[.!]?\s*$", re.I)
# Anywhere in a tutor reply, but only statements about the answer (finding 3): "no valid term count",
# "no such term", "no (valid) term exists", and "there is/are no (valid) term(s)" when it ends the clause.
# Ordinary hints such as "there are no terms before the first one" or "no term index can be zero" pass.
NO_TERM_LEAK = re.compile(
    _NO_COUNT
    + r"|\bno such terms?\b"
    + r"|\bno (?:valid )?terms? exists?\b"
    + rf"|\bthere (?:is|are) no (?:valid )?terms?"
    + rf"(?=\s*(?:[.!?,;:]|$|in (?:this|the) {_AP_NAME}(?![a-z])|(?:that|which)\b))",
    re.I)
_COUNT_VALUE = re.compile(r"[0-9+\-*/^().]+")
_ROOT_VALUE = re.compile(r"[0-9a-z+\-*/^().]+")


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
        terms = key.get("unit") == "terms"
        if terms:
            empty = bool(NO_TERM_ANSWER.search(raw) or EMPTY_SET_ANSWER.match(raw))
            raw = re.sub(r"(?i)^\s*(?:there are|the count is|my answer is)\s*", "", raw)
            raw = re.sub(r"(?i)\s+terms?\s*[.!]?\s*$", "", raw)
        else:
            empty = bool(_NO_ROOTS.search(raw) or _EMPTY_SYMBOL.match(raw))
        if empty:
            values: list[str] = []
        else:
            body = re.sub(r"[a-zA-Z]\s*=\s*", " ", raw.replace("{", " ").replace("}", " "))
            body = re.sub(r"(?i)\b(roots?|are|is|and|or|the|answers?)\b", ",", body)
            parts = [p for p in re.split(r"[,;]+|\s{2,}", body) if p.strip()]
            values = [normalise_expression(p) for p in parts]
            allowed = _COUNT_VALUE if terms else _ROOT_VALUE
            if terms and any(not allowed.fullmatch(v) for v in values):
                values = []  # words are not term counts: ask again instead of grading made-up values
            values = [v for v in values if allowed.fullmatch(v)]
            if not values:
                return {"ok": False, "reason": ("Write a positive integer count, or say 'no valid term count'." if key.get('unit') == 'terms' else "Write your roots like: x = 2 or x = -3, or say 'no real roots'.")}
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
        empty = "no positive integer term count" if typed.get("unit") == "terms" else "no real roots"
        return "{" + ", ".join(typed["values"]) + "}" if typed["values"] else empty
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
            if key.get('unit') == 'terms':
                return {"leak": bool(NO_TERM_LEAK.search(text)), "reason": "states that there is no valid term count"}
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


def _ap_candidates(problem: dict, key: dict, typed: dict) -> list[dict]:
    """Exact public-catalogue error hypotheses, never proof of a mental cause."""
    task, g = problem["task_type"], problem["givens"]
    if task == "ap_count" and key.get("kind") == typed.get("kind") == "finite_set":
        values = typed.get("values", [])
        if len(values) != 1 or _as_set(values) == _as_set(key["values"]):
            return []
        answer = str(values[0])
    elif key.get("kind") == typed.get("kind") == "scalar":
        answer = str(typed.get("value", ""))
        if _equivalent(answer, str(key["value"])):
            return []
    else:
        return []
    found = []

    def exact(name):
        return mk.exact(str(g[name]))

    def add(mid, value, rule):
        # Different public rules may predict the same response. Return all of
        # them; the tutor must ask for reasoning rather than select one cause.
        if _equivalent(answer, str(value)):
            found.append({"misconception_id": mid, "rule": rule})

    try:
        if task in ("ap_term", "ap_sum"):
            a, d, n = exact("a"), exact("d"), exact("n")
            term = a + (n - 1) * d
            total = n * (2 * a + (n - 1) * d) / 2
            add("ap_m03", a + n * d if task == "ap_term" else n * (2 * a + n * d) / 2,
                "used n gaps instead of n minus one")
            add("ap_m04", total if task == "ap_term" else term,
                "interchanged a single term and an accumulated sum")
        elif task == "ap_first":
            add("ap_m03", exact("term") - exact("n") * exact("d"), "used n gaps when recovering the first term")
        elif task == "ap_difference":
            delta = exact("term_n") - exact("term_m")
            gap = exact("n") - exact("m")
            if gap:
                add("ap_m02", -delta / gap, "reversed the ordered term subtraction")
                add("ap_m07", delta, "treated the change across several positions as one jump")
        elif task == "ap_count" and exact("d"):
            gaps = (exact("last") - exact("a")) / exact("d")
            position = gaps + 1
            add("ap_m08", gaps, "counted gaps instead of inclusive term positions")
            if position.is_integer is not True or position <= 0:
                add("ap_m06", position, "accepted a nonpositive or fractional term position")
        elif task == "ap_mean":
            add("ap_m09", mk.exact(f"sqrt(({g['left']})*({g['right']}))"), "used a geometric mean for an additive progression")
        elif task == "ap_ledger_term":
            add("ap_m04", exact("prefix_sum"), "used the accumulated total as a single term")
    except (KeyError, ValueError, TypeError, ZeroDivisionError):
        return []
    return found


def diagnose_response(problem: dict, key: dict, typed: dict) -> list[dict]:
    """Return supported rules matching a wrong answer; callers must handle ambiguity."""
    if problem.get("task_type", "").startswith("ap_"):
        return _ap_candidates(problem, key, typed)
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
    # Only b changes when an unsigned-coefficient reading is applied here.
    # With positive b, or negative a/c, negating roots is not that catalogue rule.
    if (truth and g.get("a", 0) > 0 and g.get("b", 0) < 0 and g.get("c", 0) >= 0
            and given == _as_set([f"-({v})" for v in key["values"]])):
        return [{"misconception_id": "qe_m02", "rule": "dropped the sign of b, so every root changed sign"}]
    discriminant = g.get("b", 0) ** 2 - 4 * g.get("a", 0) * g.get("c", 0)
    if given == _as_set([str(discriminant)]) and not given <= truth:
        return [{"misconception_id": "qe_m07", "rule": "reported the discriminant as a root"}]
    if len(truth) == 1 and len(given) == 2 and truth < given:
        return [{"misconception_id": "qe_m08", "rule": "gave two different values for a repeated root"}]
    if not truth and len(given) == 2 and all(v.startswith("-") for v in given):
        return [{"misconception_id": "qe_m09", "rule": "read a negative discriminant as two negative roots"}]
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
