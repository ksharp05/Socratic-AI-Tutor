"""Bounded exact mathematics and typed answer comparison.

No eval, Python execution, symbolic string sympify, implicit domain extension,
or approximate equality is used for student-facing exact answers.
"""
from __future__ import annotations
import ast
import re
from fractions import Fraction
from typing import Any
import sympy as sp


class MathInputError(ValueError):
    pass


class UndefinedMath(MathInputError):
    pass


class UnsupportedMath(MathInputError):
    """The expression is outside the admitted parser/resource contract."""


class UnverifiedMath(MathInputError):
    """Exact equivalence has not been decided; this is not a wrong answer."""


def exact(text: Any, bindings: dict[str, sp.Expr] | None = None) -> sp.Expr:
    if isinstance(text, bool) or not isinstance(text, (str, int)):
        raise MathInputError("Expected a string or integer, not a bool/float/object")
    source = str(text).strip().replace("^", "**")
    if not source or len(source) > 512:
        raise UnsupportedMath("Expression length limit exceeded")
    try:
        tree = ast.parse(source, mode="eval")
    except (SyntaxError, ValueError) as error:
        raise MathInputError("Invalid mathematical syntax") from error
    if sum(1 for _ in ast.walk(tree)) > 120:
        raise UnsupportedMath("Expression node limit exceeded")
    # Bound symbolic work as well as size: simplifying a power of a sum of many radicals or trig values can take
    # minutes (e.g. (sqrt(2)+sqrt(3)+sqrt(5)+sqrt(7))**512, security review AS-01, 10 Nov 2026).
    if sum(1 for n in ast.walk(tree) if isinstance(n, ast.Call)) > 6:
        raise UnsupportedMath("Function call limit exceeded")
    if bindings and "pi" in bindings:
        raise MathInputError("The constant pi cannot be rebound")
    values = {"pi": sp.pi, **{k:sp.sympify(v) for k,v in (bindings or {}).items() if isinstance(v,(sp.Basic,int)) and not isinstance(v,bool)}}
    if bindings and len(values)!=len(bindings)+1:
        raise MathInputError("Bindings must be trusted symbolic expressions or integers")
    functions = {"sqrt": sp.sqrt, "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                 "sec": sp.sec, "csc": sp.csc, "cosec": sp.csc, "cot": sp.cot,
                 "abs": sp.Abs}

    def bounded(value):
        if value.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
            raise UndefinedMath("The original expression is undefined")
        if value.is_real is False:
            raise MathInputError("Only real-valued expressions are supported")
        if isinstance(value, sp.Rational) and max(abs(int(value.p)).bit_length(), int(value.q).bit_length()) > 512:
            raise UnsupportedMath("Exact arithmetic size limit exceeded")
        return value

    def visit(node, depth=0):
        if depth > 20:
            raise UnsupportedMath("Expression depth limit exceeded")
        if isinstance(node, ast.Expression):
            return visit(node.body, depth+1)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise MathInputError("Only numeric constants are supported")
            token = ast.get_source_segment(source, node).replace("_", "")
            if len(token) > 160:
                raise UnsupportedMath("Numeric literal length limit exceeded")
            exponent = re.search(r"[eE]([+-]?\d+)$", token)
            if exponent and abs(int(exponent.group(1))) > 512:
                raise UnsupportedMath("Scientific exponent limit exceeded")
            try:
                return bounded(sp.Rational(token))
            except MathInputError:
                raise
            except (TypeError, ValueError) as error:
                raise MathInputError("Invalid exact numeric literal") from error
        if isinstance(node, ast.Name):
            if node.id not in values:
                raise UnsupportedMath("Unbound symbol")
            return bounded(values[node.id])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand, depth+1)
            return bounded(-value if isinstance(node.op, ast.USub) else value)
        if isinstance(node, ast.BinOp):
            left, right = visit(node.left, depth+1), visit(node.right, depth+1)
            if isinstance(node.op, ast.Add): return bounded(left+right)
            if isinstance(node.op, ast.Sub): return bounded(left-right)
            if isinstance(node.op, ast.Mult): return bounded(left*right)
            if isinstance(node.op, ast.Div):
                if right.is_zero is True:
                    raise UndefinedMath("Division by zero in the original expression")
                return bounded(left/right)
            if isinstance(node.op, ast.Pow):
                if right.is_Rational and right.q==2 and abs(right.p)<=32:
                    if left.is_negative is True:raise MathInputError('A half-integer power leaves the real domain')
                    if left.is_nonnegative is not True:raise UnverifiedMath('Cannot establish the real domain of this half-integer power')
                    if left.is_zero and right<0:raise UndefinedMath('Zero to a negative power is undefined')
                    return bounded(sp.sqrt(left)**int(right.p))
                if right.is_Integer is not True or abs(right)>512:
                    raise UnsupportedMath("Only bounded integer and half-integer powers are supported")
                if abs(right)>12 and left.is_Rational is not True:
                    raise UnsupportedMath("Powers above 12 are supported only for rational bases")
                if left.is_zero is True and right<=0:
                    raise UndefinedMath("Zero to a nonpositive power is not an admitted answer")
                return bounded(left**right)
            raise UnsupportedMath("Unsupported mathematical operator")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in functions:
            if len(node.args)!=1 or node.keywords:
                raise MathInputError("Function requires one positional argument")
            argument = visit(node.args[0], depth+1)
            if node.func.id=="sqrt" and argument.is_negative is True:
                raise MathInputError("Square root leaves the declared real domain")
            return bounded(functions[node.func.id](argument))
        raise UnsupportedMath("Unsupported mathematical syntax")

    return visit(tree)


def canonical(value: sp.Expr | int) -> str:
    if isinstance(value,bool):raise MathInputError("A boolean is not a scalar")
    if isinstance(value,Fraction):value=sp.Rational(value.numerator,value.denominator)
    value = sp.radsimp(sp.simplify(sp.sympify(value))) if isinstance(value, (sp.Basic, int)) else exact(value)
    if value.free_symbols or value.has(sp.zoo, sp.nan, sp.oo, -sp.oo) or value.is_real is False:
        raise MathInputError("Expected an exact finite real number")
    return sp.sstr(value)


def equivalent(first: str | int, second: str | int) -> bool:
    difference=sp.simplify(exact(first)-exact(second))
    if difference==0:return True
    if difference.is_zero is False:return False
    raise UnverifiedMath("Exact equivalence is undecided; request adjudication or a supported equivalent form")


def normalized_unit(unit):
    aliases={"km/h":"km/h", "kmph":"km/h", "kilometres per hour":"km/h", "kilometers per hour":"km/h",
             "cm":"cm", "centimetres":"cm", "centimeters":"cm", "m":"m", "metres":"m", "meters":"m",
             "units":"units", "unit":"units", "terms":"terms", "term":"terms", "degrees":"degrees", "degree":"degrees"}
    if unit is None:return None
    if not isinstance(unit,str):raise MathInputError("Unit must be text or null")
    if len(unit)>64:raise UnsupportedMath('Unit text length limit exceeded')
    clean=unit.strip().lower()
    if clean not in aliases:raise MathInputError("Unrecognised unit")
    return aliases[clean]


def validate_answer(answer):
    if not isinstance(answer,dict):raise MathInputError("Answer must be a typed object")
    kind=answer.get("kind")
    allowed={"scalar":{"kind","value","unit"}, "finite_set":{"kind","values","unit"},
             "coefficients":{"kind","values"}, "classification":{"kind","value"},
             "boolean":{"kind","value"}, "defined_value":{"kind","defined","value"}}
    if not isinstance(kind,str) or kind not in allowed or set(answer)-allowed[kind]:raise MathInputError("Unknown answer kind or fields")
    required={"finite_set":{"kind","values"},"coefficients":{"kind","values"},"defined_value":{"kind","defined","value"}}
    if not required.get(kind,{"kind","value"})<=set(answer):raise MathInputError("Missing required answer fields")
    if kind=="scalar":exact(answer.get("value")); normalized_unit(answer.get("unit"))
    elif kind in {"finite_set","coefficients"}:
        values=answer.get("values")
        if not isinstance(values,list) or len(values)>8:raise MathInputError("Answer requires a bounded list")
        if kind=="coefficients" and len(values)!=3:raise MathInputError("Three coefficients are required")
        parsed=[exact(x) for x in values]
        if kind=="finite_set":
            if any(equivalent(str(a),str(b)) for i,a in enumerate(parsed) for b in parsed[i+1:]):
                raise MathInputError("Duplicate roots/values are not canonical")
            normalized_unit(answer.get("unit"))
    elif kind=="boolean":
        if type(answer.get("value")) is not bool:raise MathInputError("A JSON boolean is required")
    elif kind=="classification":
        if not isinstance(answer.get("value"),str) or not re.fullmatch(r"[a-z][a-z_]{0,60}",answer["value"]):
            raise MathInputError("A canonical classification label is required")
    elif kind=="defined_value":
        if type(answer.get("defined")) is not bool:raise MathInputError("Defined must be a JSON boolean")
        if answer["defined"]:exact(answer.get("value"))
        elif answer.get("value") is not None:raise MathInputError("Undefined values must use null, never zero/infinity")
    return answer


def answers_equivalent(first,second):
    validate_answer(first);validate_answer(second)
    if first["kind"]!=second["kind"]:return False
    kind=first["kind"]
    if kind in {"scalar","finite_set"} and normalized_unit(first.get("unit"))!=normalized_unit(second.get("unit")):return False
    if kind=="scalar":return equivalent(first["value"],second["value"])
    if kind=="finite_set":
        return len(first["values"])==len(second["values"]) and all(any(equivalent(a,b) for b in second["values"]) for a in first["values"])
    if kind=="coefficients":return all(equivalent(a,b) for a,b in zip(first["values"],second["values"]))
    if kind in {"boolean","classification"}:return first["value"]==second["value"]
    if kind=="defined_value":return first["defined"]==second["defined"] and (not first["defined"] or equivalent(first["value"],second["value"]))
    return False


def grade_mathematics(response,expected):
    """Grade only the typed mathematical component, never free-text reasoning."""
    validate_answer(expected)
    try:
        correct=answers_equivalent(response,expected)
    except (UnsupportedMath,UnverifiedMath) as error:
        return {"correct":None,"status":"unverified","scorable":False,"reason":str(error),"reasoning_evaluated":False}
    except MathInputError as error:
        return {"correct":False,"status":"invalid_response","scorable":False,"reason":str(error),"reasoning_evaluated":False}
    return {"correct":bool(correct),"status":"correct" if correct else "incorrect","scorable":True,"reason":"exact_match" if correct else "mathematical_answer_or_unit_mismatch","reasoning_evaluated":False}


def summarize_grades(results):
    """Report abstentions and invalid inputs without silently dropping or failing them."""
    counts=dict.fromkeys(["correct","incorrect","invalid_response","unverified"],0)
    for result in results:
        if not isinstance(result,dict):raise MathInputError('Grading result must be a typed object')
        status=result.get("status")
        if not isinstance(status,str) or status not in counts:raise MathInputError("Unknown grading status")
        expected_correct=True if status=="correct" else None if status=="unverified" else False
        if result.get("correct") is not expected_correct or result.get("scorable") is not (status in {"correct","incorrect"}):
            raise MathInputError("Inconsistent grading result")
        counts[status]+=1
    total=sum(counts.values());scored=counts["correct"]+counts["incorrect"]
    return {"attempts":total,"status_counts":counts,"scored_attempts":scored,
            "coverage":scored/total if total else None,
            "conditional_accuracy":counts["correct"]/scored if scored else None,
            "conservative_correct_fraction":counts["correct"]/total if total else None,
            "final_accuracy":counts["correct"]/total if total and scored==total else None,
            "requires_adjudication":scored!=total}


def scalar(value,unit=None):
    result={"kind":"scalar","value":canonical(value)}
    if unit is not None:result["unit"]=normalized_unit(unit)
    return result


def finite_set(values,unit=None):
    strings=[]
    for value in values:
        text=canonical(value)
        if not any(equivalent(text,existing) for existing in strings):strings.append(text)
    result={"kind":"finite_set","values":sorted(strings)}
    if unit is not None:result["unit"]=normalized_unit(unit)
    return result
