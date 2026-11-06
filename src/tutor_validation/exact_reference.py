"""Independent exact reference checks: standard library only, no tutor/dataset solver imports."""
from __future__ import annotations
import ast
import re
from dataclasses import dataclass
from fractions import Fraction as F
from math import isqrt

VERSION = "published-maths-oracle-v1"
SOURCES = {
    "quadratic": "https://openstax.org/books/algebra-and-trigonometry-2e/pages/2-5-quadratic-equations",
    "ap": "https://openstax.org/books/algebra-and-trigonometry-2e/pages/13-2-arithmetic-sequences",
    "ap_sum": "https://openstax.org/books/algebra-and-trigonometry-2e/pages/13-4-series-and-their-notations",
    "trig": "https://openstax.org/books/algebra-and-trigonometry-2e/pages/7-2-right-triangle-trigonometry",
}

def rational_sqrt(value):
    value = F(value)
    if value < 0:
        return None
    top, bottom = isqrt(value.numerator), isqrt(value.denominator)
    return F(top, bottom) if top * top == value.numerator and bottom * bottom == value.denominator else None

@dataclass(frozen=True)
class Real:
    p: F
    q: F = F(0)
    d: int = 2
    def __post_init__(self):
        if any(abs(v).bit_length() > 4096 for value in (self.p, self.q) for v in (value.numerator, value.denominator)):
            raise ValueError("Exact expression exceeds resource bound")
    def coerce(self, other):
        if isinstance(other, Real):
            if other.d != self.d: raise ValueError("Different fields")
            return other
        return Real(F(other), F(0), self.d)
    def __add__(self, other):
        other = self.coerce(other)
        return Real(self.p + other.p, self.q + other.q, self.d)
    __radd__ = __add__
    def __neg__(self): return Real(-self.p, -self.q, self.d)
    def __sub__(self, other): return self + -self.coerce(other)
    def __mul__(self, other):
        other = self.coerce(other)
        return Real(self.p * other.p + self.q * other.q * self.d,
                    self.p * other.q + self.q * other.p, self.d)
    __rmul__ = __mul__
    def __truediv__(self, other):
        other = self.coerce(other)
        denominator = other.p * other.p - other.q * other.q * self.d
        if not denominator: raise ValueError("Zero denominator")
        return self * Real(other.p / denominator, -other.q / denominator, self.d)

def parse(text, d=2):
    if not isinstance(text, str) or len(text) > 500: raise ValueError("Invalid expression")
    tree = ast.parse(text, mode="eval")
    if sum(1 for _ in ast.walk(tree)) > 120: raise ValueError("Expression too large")
    def visit(node):
        if isinstance(node, ast.Constant) and type(node.value) is int and abs(node.value) <= 10**24:
            return Real(F(node.value), F(0), d)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add): return left + right
            if isinstance(node.op, ast.Sub): return left - right
            if isinstance(node.op, ast.Mult): return left * right
            if isinstance(node.op, ast.Div): return left / right
            if isinstance(node.op, ast.Pow) and right.q == 0 and right.p == 2: return left * left
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "sqrt" and len(node.args) == 1 and not node.keywords:
            argument = visit(node.args[0])
            if argument.q or argument.p < 0: raise ValueError("Unsupported radical")
            square = rational_sqrt(argument.p)
            if square is not None: return Real(square, F(0), d)
            scale = rational_sqrt(argument.p / d)
            if scale is not None: return Real(F(0), scale, d)
        raise ValueError("Unsupported expression")
    return visit(tree.body)

def integer(givens, name):
    value = givens[name]
    if type(value) is not int or abs(value) > 10**12: raise ValueError("Exact bounded integer required")
    return value

def bounded_fraction(value):
    """Exact bounded data only: do not silently interpret binary floats."""
    if type(value) is int and abs(value) <= 10**24:
        return F(value)
    if not isinstance(value, str) or len(value) > 200 or not re.fullmatch(r"[+-]?[0-9]+(?:/[0-9]+)?", value):
        raise ValueError("Bounded rational string required")
    result = F(value)
    if max(abs(result.numerator).bit_length(), result.denominator.bit_length()) > 512:
        raise ValueError("Rational input exceeds resource bound")
    return result

def scalar_matches(answer, value):
    return answer.get("kind") == "scalar" and answer.get("unit") is None and parse(answer["value"]) == Real(F(value))

def validate(problem, answer):
    """A second publisher supplies mathematical definitions; this is not human teaching review."""
    task = problem.get("task_type", "") if isinstance(problem, dict) else ""
    source = SOURCES["quadratic" if task == "quadratic_solve" else "trig" if task == "trig_triangle_ratio" else "ap_sum" if task == "ap_sum" else "ap"]
    result = {"status": "failed", "oracle": VERSION, "reference": source,
              "human_review": False, "scope": "exact answer check, not pedagogy or learning"}
    try:
        if not isinstance(problem, dict) or not isinstance(answer, dict): raise ValueError("Invalid record")
        g = problem["givens"]
        if problem.get("number_domain") != "real" or problem.get("answer_precision") != "exact":
            raise ValueError("Unsupported domain")
        if task == "quadratic_solve":
            a, b, c = (integer(g, name) for name in ("a", "b", "c"))
            if not a or answer.get("kind") != "finite_set" or answer.get("unit") is not None: raise ValueError("Invalid quadratic answer")
            discriminant = b*b - 4*a*c
            values = answer["values"]
            if not isinstance(values, list) or len(values)>2: raise ValueError("Invalid root set")
            if discriminant < 0:
                valid = not values
            else:
                field = discriminant if rational_sqrt(discriminant) is None else 2
                roots = {parse(value, field) for value in values}
                zero = Real(F(0), F(0), field)
                if discriminant == 0:
                    valid = roots == {Real(F(-b, 2*a), F(0), field)}
                else:
                    valid = (len(roots) == 2 and all(a*r*r + b*r + c == zero for r in roots)
                             and sum(roots, zero) == Real(F(-b, a), F(0), field))
        elif task in ("ap_term", "ap_sum", "ap_first"):
            n = integer(g, "n")
            if not 1 <= n <= 10000: raise ValueError("Position outside independent audit bound")
            difference = integer(g, "d")
            if task == "ap_first":
                value = F(integer(g, "term"))
                for _ in range(n-1): value -= difference
            else:
                term, total = F(integer(g, "a")), F(0)
                for _ in range(n):
                    total += term
                    last = term
                    term += difference
                value = last if task == "ap_term" else total
            valid = scalar_matches(answer, value)
        elif task == "ap_difference":
            m, n = integer(g, "m"), integer(g, "n")
            if min(m, n) < 1 or m == n: raise ValueError("Invalid positions")
            valid = scalar_matches(answer, F(integer(g, "term_n") - integer(g, "term_m"), n-m))
        elif task == "ap_count":
            a, difference, last = (integer(g, name) for name in ("a", "d", "last"))
            if not difference: raise ValueError("Infinite or ambiguous count")
            position = F(last-a, difference) + 1
            expected = {Real(position)} if position.denominator == 1 and position >= 1 else set()
            valid = (answer.get("kind") == "finite_set" and isinstance(answer.get("values"), list) and len(answer["values"])<=1 and answer.get("unit") == "terms"
                     and {parse(v) for v in answer["values"]} == expected)
        elif task == "ap_mean":
            valid = scalar_matches(answer, F(integer(g, "left") + integer(g, "right"), 2))
        elif task == "ap_ledger_term":
            if integer(g, "n") < 2: raise ValueError("Missing earlier positive prefix")
            valid = scalar_matches(answer, bounded_fraction(g["prefix_sum"]) - bounded_fraction(g["previous_sum"]))
        elif task == "trig_triangle_ratio":
            o, adjacent, h = (integer(g, name) for name in ("opposite", "adjacent", "hypotenuse"))
            if min(o, adjacent, h) <= 0 or o*o + adjacent*adjacent != h*h: raise ValueError("Invalid triangle")
            if g["reference"] == "C": o, adjacent = adjacent, o
            elif g["reference"] != "A": raise ValueError("Unknown reference")
            numerator, denominator = {"sin": (o,h), "cos": (adjacent,h), "tan": (o,adjacent),
                                      "csc": (h,o), "sec": (h,adjacent), "cot": (adjacent,o)}[g["ratio"]]
            valid = scalar_matches(answer, F(numerator, denominator))
        else:
            return {**result, "status": "unsupported", "reason": "task_outside_declared_scope"}
        result["status"] = "verified" if valid else "failed"
    except (ValueError, KeyError, TypeError, SyntaxError, OverflowError, ZeroDivisionError):
        result["reason"] = "invalid_or_unverified_answer"
    return result
