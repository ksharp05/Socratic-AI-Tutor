"""Typed problems, deterministic prompts, and two answer derivation routes.

The primary route uses closed forms/exact arithmetic. The oracle independently
uses the primitive givens with symbolic solving, enumeration or trig functions.
"""
from __future__ import annotations
from fractions import Fraction
import math
import random
import sympy as sp
from .math_kernel import exact, canonical, equivalent, scalar, finite_set, UndefinedMath, MathInputError
from . import assessment_tasks


TASK_CONCEPTS = {
    "quadratic_solve": ["qe03","qe04","qe05"],
    "quadratic_coefficients": ["qe01","qe02"],
    "quadratic_degree": ["qe01"],
    "quadratic_classify": ["qe02","qe06"],
    "quadratic_parameter_repeated": ["qe02","qe06"],
    "quadratic_rectangle": ["qe07","qe08"],
    "quadratic_speed": ["qe07","qe08"],
    "quadratic_under_specified_rectangle": ["qe07","qe08"],
    "quadratic_check_claim": ["qe03","qe04","qe05"],
    "ap_term": ["ap02","ap03","ap04"],
    "ap_sum": ["ap03","ap06"],
    "ap_membership": ["ap02","ap05"],
    "ap_difference": ["ap04","ap07"],
    "ap_first": ["ap03","ap07"],
    "ap_count": ["ap04","ap05"],
    "ap_inverse_sum": ["ap05","ap06","ap08"],
    "ap_recognition": ["ap01","ap02"],
    "ap_mean": ["ap02","ap07"],
    "ap_ledger_term": ["ap03","ap06","ap08"],
    "trig_triangle_ratio": ["tr01","tr02","tr03"],
    "trig_standard_value": ["tr05","tr06","tr07"],
    "trig_from_ratio": ["tr02","tr03","tr08"],
    "trig_scaled_triangle": ["tr02","tr04"],
    "trig_identity_value": ["tr03","tr06","tr08"],
    "trig_identity_truth": ["tr08","tr09"],
    "trig_square_value": ["tr05","tr07"],
    "trig_domain": ["tr06","tr08","tr09"],
}
TASK_CONCEPTS.update(assessment_tasks.CONCEPTS)
RATIOS = ("sin","cos","tan","sec","csc","cot")
SYMBOLS={"x":sp.Symbol("x",real=True),"theta":sp.Symbol("theta",real=True)}
TRIG_FUNCTIONS={"sin":sp.sin,"cos":sp.cos,"tan":sp.tan,"sec":sp.sec,"csc":sp.csc,"cot":sp.cot}
IDENTITY_VALUES={
    "sine_cosine":"sin(theta)**2+cos(theta)**2",
    "secant_tangent":"sec(theta)**2-tan(theta)**2",
    "cosecant_cotangent":"csc(theta)**2-cot(theta)**2",
}
IDENTITY_CLAIMS={
    "pythagorean":("sin(theta)**2+cos(theta)**2","1"),
    "secant":("sec(theta)**2-tan(theta)**2","1"),
    "cosecant":("csc(theta)**2-cot(theta)**2","1"),
    "quotient":("sin(theta)/cos(theta)","tan(theta)"),
    "reciprocal":("1/sin(theta)","csc(theta)"),
    "false_sum":("sin(theta)+cos(theta)","1"),
    "false_square_expansion":("(sin(theta)+cos(theta))**2","sin(theta)**2+cos(theta)**2"),
    "false_reverse_tangent":("tan(theta)","cos(theta)/sin(theta)"),
    "false_difference":("sin(theta)**2-cos(theta)**2","1"),
    "false_product":("sin(theta)*cos(theta)","1"),
}
DOMAIN_EXPRESSIONS={
    "cancel_sine":"sin(theta)/sin(theta)",
    "cancel_cosine":"cos(theta)/cos(theta)",
    "cancel_tangent":"tan(theta)/tan(theta)",
    "cancel_cotangent":"cot(theta)/cot(theta)",
    "reciprocal_cosine":"1/cos(theta)",
    "reciprocal_sine":"1/sin(theta)",
    "pythagorean":"sin(theta)**2+cos(theta)**2",
}


def ratio_from_sides(name,o,a,h):
    pairs={"sin":(o,h),"cos":(a,h),"tan":(o,a),"sec":(h,a),"csc":(h,o),"cot":(a,o)}
    numerator,denominator=pairs[name]
    if denominator==0:return None
    return sp.Rational(numerator,denominator)


def standard_ratio(name,degrees):
    # Exact special-triangle coordinates, independent of the trig-function oracle.
    sides={0:(sp.Integer(0),sp.Integer(1),sp.Integer(1)),
           30:(sp.Integer(1),sp.sqrt(3),sp.Integer(2)),
           45:(sp.Integer(1),sp.Integer(1),sp.sqrt(2)),
           60:(sp.sqrt(3),sp.Integer(1),sp.Integer(2)),
           90:(sp.Integer(1),sp.Integer(0),sp.Integer(1))}
    o,a,h=sides[degrees]
    pairs={"sin":(o,h),"cos":(a,h),"tan":(o,a),"sec":(h,a),"csc":(h,o),"cot":(a,o)}
    num,den=pairs[name]
    return None if den==0 else sp.simplify(num/den)


def polynomial_coefficients(g):
    return (g["p"]*g["r"]+g["t"],g["p"]*g["s"]+g["q"]*g["r"],g["q"]*g["s"])


def polynomial_expression(g):
    return f"({g['p']}*x+({g['q']}))*({g['r']}*x+({g['s']}))+({g['t']})*x**2"


def real_quadratic_roots(a,b,c):
    if a==0:raise MathInputError("Quadratic leading coefficient must be nonzero")
    discriminant=b*b-4*a*c
    if discriminant<0:return []
    return [sp.Rational(-b,2*a)+sp.sqrt(discriminant)/(2*a),sp.Rational(-b,2*a)-sp.sqrt(discriminant)/(2*a)]


def problem(task_type,givens):
    if task_type not in TASK_CONCEPTS:raise MathInputError("Unknown task type")
    p={"task_type":task_type,"givens":givens,"number_domain":"real","answer_precision":"exact",
       "concept_ids":TASK_CONCEPTS[task_type],"class":10,"language":"en"}
    validate_problem(p)
    return p


def validate_problem(p):
    from .specifications import structural_validate
    structural_validate(p,TASK_CONCEPTS)
    task=p["task_type"];g=p["givens"]
    if task not in TASK_CONCEPTS or not isinstance(g,dict):raise MathInputError("Invalid typed problem")
    if p.get("number_domain")!="real" or p.get("answer_precision")!="exact":raise MathInputError("Unsupported domain/precision")
    for value in g.values():
        if isinstance(value,bool) or not isinstance(value,(int,str,list)):raise MathInputError("Givens require exact primitives")
        if isinstance(value,int) and abs(value)>10**12:raise MathInputError("Given integer exceeds declared resource limit")
    if task in {"quadratic_solve","quadratic_classify","quadratic_check_claim"} and g["a"]==0:raise MathInputError("Nonzero a is required")
    if task.startswith("ap_") and "n" in g and (type(g["n"]) is not int or g["n"]<1):raise MathInputError("Term positions must be positive integers")
    if task=="ap_difference" and (g["m"]<1 or g["m"]==g["n"]):raise MathInputError("Distinct positive term positions required")
    if task=="ap_recognition" and (len(g["terms"])<3 or any(type(x) is not int for x in g["terms"])):raise MathInputError("At least three integer observations required")
    if task=="ap_count" and g["d"]==0:raise MathInputError("A finite terminal-count question requires nonzero d")
    if task=="ap_ledger_term" and g["n"]<2:raise MathInputError("A previous positive prefix count is required")
    if task=="trig_identity_value" and g["identity_id"] not in IDENTITY_VALUES:raise MathInputError("Unknown identity")
    if task=="trig_identity_truth" and g["identity_id"] not in IDENTITY_CLAIMS:raise MathInputError("Unknown identity claim")
    if task=="trig_domain" and (g["expression_id"] not in DOMAIN_EXPRESSIONS or g["angle_degrees"] not in {0,30,45,60,90}):raise MathInputError("Unsupported original domain expression/angle")
    if task in {"trig_triangle_ratio","trig_scaled_triangle"}:
        if min(g["opposite"],g["adjacent"],g["hypotenuse"])<=0 or g["opposite"]**2+g["adjacent"]**2!=g["hypotenuse"]**2:raise MathInputError("A valid positive right triangle is required")
        if g["ratio"] not in RATIOS or g["reference"] not in {"A","C"}:raise MathInputError("Invalid ratio/reference angle")
        if task=="trig_scaled_triangle" and g["scale"]<=0:raise MathInputError("A positive scale factor is required")
    if task in {"trig_standard_value","trig_square_value"}:
        if g["angle_degrees"] not in {0,30,45,60,90} or g["ratio"] not in RATIOS:raise MathInputError("Unsupported standard angle/ratio")
        if task=="trig_square_value" and standard_ratio(g["ratio"],g["angle_degrees"]) is None:raise MathInputError("Squared-ratio value must be defined")
    if task=="trig_from_ratio":
        value=exact(g["given_value"])
        if g["given_ratio"] not in {"sin","cos","tan"} or g["target_ratio"] not in RATIOS or value<=0:raise MathInputError("Invalid acute ratio givens")
        if g["given_ratio"] in {"sin","cos"} and value>=1:raise MathInputError("Acute sine/cosine must lie strictly between zero and one")
    if task=="quadratic_rectangle" and (g["area"]<=0):raise MathInputError("Positive area is required")
    if task=="quadratic_under_specified_rectangle" and g['area']<=0:raise MathInputError('Positive area is required')
    if task=="quadratic_speed" and any(exact(g[name])<=0 for name in ["distance","reduction","delay"]):raise MathInputError("Positive distance, reduction and delay required")
    if task in assessment_tasks.CONCEPTS:assessment_tasks.validate(task,g)
    return p


def primary_answer(p):
    validate_problem(p);task=p["task_type"];g=p["givens"]
    if task in assessment_tasks.CONCEPTS:return assessment_tasks.primary(p)
    if task=="quadratic_solve":return finite_set(real_quadratic_roots(g["a"],g["b"],g["c"]))
    if task=="quadratic_coefficients":return {"kind":"coefficients","values":[canonical(x) for x in polynomial_coefficients(g)]}
    if task=="quadratic_degree":
        a,b,c=polynomial_coefficients(g)
        return {"kind":"classification","value":"quadratic" if a else "linear" if b else "constant_nonzero" if c else "zero_polynomial"}
    if task=="quadratic_classify":
        d=g["b"]**2-4*g["a"]*g["c"]
        return {"kind":"classification","value":"two_distinct_real" if d>0 else "repeated_real" if d==0 else "no_real"}
    if task=="quadratic_parameter_repeated":
        return finite_set([] if g["c"]<0 else [sp.sqrt(g["c"]),-sp.sqrt(g["c"])])
    if task=="quadratic_rectangle":return scalar((-g["gap"]+sp.sqrt(g["gap"]**2+4*g["area"]))/2,"units")
    if task=="quadratic_under_specified_rectangle":
        # Two different positive first sides meet the one supplied constraint.
        pairs=[(sp.Integer(1),sp.Integer(g['area'])),(sp.Integer(2),sp.Rational(g['area'],2))]
        if not all(a*b==g['area'] and a>0 and b>0 for a,b in pairs) or pairs[0][0]==pairs[1][0]:raise MathInputError('Invalid ambiguity witnesses')
        return {'kind':'classification','value':'additional_independent_constraint_required'}
    if task=="quadratic_speed":
        reduction,distance,delay=(exact(g[k]) for k in ["reduction","distance","delay"])
        return scalar((reduction+sp.sqrt(reduction**2+4*reduction*distance/delay))/2,"km/h")
    if task=="quadratic_check_claim":
        actual=finite_set(real_quadratic_roots(g["a"],g["b"],g["c"]))["values"]
        claimed=g["claimed_roots"]
        distinct=all(not equivalent(a,b) for i,a in enumerate(claimed) for b in claimed[i+1:])
        correct=distinct and len(actual)==len(claimed) and all(any(equivalent(a,b) for b in claimed) for a in actual)
        return {"kind":"boolean","value":bool(correct)}
    if task=="ap_term":return scalar(g["a"]+(g["n"]-1)*g["d"])
    if task=="ap_sum":return scalar(sp.Rational(g["n"]*(2*g["a"]+(g["n"]-1)*g["d"]),2))
    if task=="ap_membership":
        count=None if g["d"]==0 else 1+Fraction(g["value"]-g["a"],g["d"])
        ok=g["value"]==g["a"] if count is None else count.denominator==1 and count>=1
        return {"kind":"boolean","value":bool(ok)}
    if task=="ap_difference":return scalar(Fraction(g["term_n"]-g["term_m"],g["n"]-g["m"]))
    if task=="ap_first":return scalar(g["term"]-(g["n"]-1)*g["d"])
    if task=="ap_count":
        n=1+Fraction(g["last"]-g["a"],g["d"])
        return finite_set([sp.Rational(n.numerator,n.denominator)] if n>=1 and n.denominator==1 else [],"terms")
    if task=="ap_inverse_sum":
        a,d,total=g["a"],g["d"],exact(g["total"])
        if d==0:
            if a==0:return {"kind":"classification","value":"infinitely_many_positive_counts"} if total==0 else finite_set([],"terms")
            n=total/a
            return finite_set([n] if n.is_Integer and n>0 else [],"terms")
        roots=real_quadratic_roots(d,2*a-d,-2*total)
        return finite_set([n for n in roots if n.is_Integer and n>0],"terms")
    if task=="ap_recognition":
        differences=[b-a for a,b in zip(g["terms"],g["terms"][1:])]
        return {"kind":"boolean","value":len(set(differences))==1}
    if task=="ap_mean":return scalar(Fraction(g["left"]+g["right"],2))
    if task=="ap_ledger_term":return scalar(exact(g["prefix_sum"])-exact(g["previous_sum"]))
    if task in {"trig_triangle_ratio","trig_scaled_triangle"}:
        o,a,h=g["opposite"],g["adjacent"],g["hypotenuse"]
        if g["reference"]=="C":o,a=a,o
        return scalar(ratio_from_sides(g["ratio"],o,a,h))
    if task=="trig_standard_value":
        value=standard_ratio(g["ratio"],g["angle_degrees"])
        return {"kind":"defined_value","defined":value is not None,"value":canonical(g.get("coefficient",1)*value) if value is not None else None}
    if task=="trig_from_ratio":
        value=exact(g["given_value"])
        if g["given_ratio"]=="sin":s,c=value,sp.sqrt(1-value**2)
        elif g["given_ratio"]=="cos":s,c=sp.sqrt(1-value**2),value
        else:c=1/sp.sqrt(1+value**2);s=value*c
        values={"sin":s,"cos":c,"tan":s/c,"sec":1/c,"csc":1/s,"cot":c/s}
        return scalar(values[g["target_ratio"]])
    if task=="trig_identity_value":return scalar(g["factor"])
    if task=="trig_identity_truth":return {"kind":"boolean","value":not g["identity_id"].startswith("false_")}
    if task=="trig_square_value":return scalar(g["factor"]*standard_ratio(g["ratio"],g["angle_degrees"])**2)
    if task=="trig_domain":
        key=g["expression_id"];angle=g["angle_degrees"]
        if key.startswith("cancel_"):
            name={"cancel_sine":"sin","cancel_cosine":"cos","cancel_tangent":"tan","cancel_cotangent":"cot"}[key]
            denominator=standard_ratio(name,angle)
            value=None if denominator is None or denominator==0 else sp.Integer(1)
        elif key=="reciprocal_cosine":
            d=standard_ratio("cos",angle);value=None if d==0 else 1/d
        elif key=="reciprocal_sine":
            d=standard_ratio("sin",angle);value=None if d==0 else 1/d
        else:value=sp.Integer(1)
        return {"kind":"defined_value","defined":value is not None,"value":canonical(g.get("coefficient",1)*value) if value is not None else None}
    raise MathInputError("Unimplemented primary route")


def oracle_answer(p):
    """Derive solely from primitive givens; do not call the primary calculator."""
    validate_problem(p);task=p["task_type"];g=p["givens"]
    if task in assessment_tasks.CONCEPTS:return assessment_tasks.oracle(p)
    x=sp.Symbol("x",real=True);n=sp.Symbol("n",integer=True)
    if task in {"quadratic_solve","quadratic_check_claim"}:
        solutions=sp.solveset(g["a"]*x**2+g["b"]*x+g["c"],x,domain=sp.S.Reals)
        roots=[] if solutions is sp.S.EmptySet else list(solutions)
        if task=="quadratic_solve":return finite_set(roots)
        # FiniteSet equality alone is structural: nested radicals can encode
        # the same real algebraic root with a different expression tree.
        claimed=[sp.simplify(sp.sqrtdenest(exact(v))) for v in g["claimed_roots"]]
        ok=len(claimed)==len(set(claimed)) and sp.FiniteSet(*claimed)==sp.FiniteSet(*roots)
        return {"kind":"boolean","value":bool(ok)}
    if task in {"quadratic_coefficients","quadratic_degree"}:
        polynomial=sp.Poly(exact(polynomial_expression(g),{"x":x}),x)
        if task=="quadratic_coefficients":return {"kind":"coefficients","values":[canonical(polynomial.nth(k)) for k in [2,1,0]]}
        degree=polynomial.degree()
        return {"kind":"classification","value":"zero_polynomial" if polynomial.is_zero else "quadratic" if degree==2 else "linear" if degree==1 else "constant_nonzero"}
    if task=="quadratic_classify":
        roots=sp.solveset(g["a"]*x*x+g["b"]*x+g["c"],x,domain=sp.S.Reals)
        count=0 if roots is sp.S.EmptySet else len(roots)
        return {"kind":"classification","value":{0:"no_real",1:"repeated_real",2:"two_distinct_real"}[count]}
    if task=="quadratic_parameter_repeated":
        k=sp.Symbol("k",real=True)
        repeated=sp.resultant(x*x+2*k*x+g["c"],2*x+2*k,x)
        roots=sp.solveset(repeated,k,domain=sp.S.Reals)
        return finite_set([] if roots is sp.S.EmptySet else list(roots))
    if task=="quadratic_rectangle":
        roots=sp.solveset(x*(x+g["gap"])-g["area"],x,domain=sp.S.Reals)
        accepted=[r for r in roots if r>0 and r+g["gap"]>0]
        if len(accepted)!=1:raise MathInputError("Rectangle does not have one admissible width")
        return scalar(accepted[0],"units")
    if task=="quadratic_under_specified_rectangle":
        x=sp.Symbol('x',positive=True)
        y=sp.Symbol('y',real=True)
        parameterized=sp.solveset(x*y-g['area'],y,domain=sp.S.Reals)
        formula=next(iter(parameterized))
        values=[sp.sqrt(g['area']),2*sp.sqrt(g['area'])]
        witnesses=[(value,sp.simplify(formula.subs(x,value))) for value in values]
        if not all(a>0 and b>0 and a*b==g['area'] for a,b in witnesses) or values[0]==values[1]:raise MathInputError('CAS could not establish nonuniqueness')
        return {'kind':'classification','value':'additional_independent_constraint_required'}
    if task=="quadratic_speed":
        distance,reduction,delay=(exact(g[k]) for k in ["distance","reduction","delay"])
        roots=sp.solveset(distance/(x-reduction)-distance/x-delay,x,domain=sp.S.Reals)
        accepted=[r for r in roots if r>reduction]
        if len(accepted)!=1:raise MathInputError("Speed does not have one admissible answer")
        return scalar(accepted[0],"km/h")
    if task in {"ap_term","ap_sum"}:
        if g["n"]<=1000:
            terms=[];current=g["a"]
            for _ in range(g["n"]):terms.append(current);current+=g["d"]
            value=terms[-1] if task=="ap_term" else sum(terms)
        else:
            j=sp.Symbol("j",integer=True)
            value=sp.summation(g["a"]+j*g["d"],(j,0,g["n"]-1)) if task=="ap_sum" else g["a"]+sp.summation(g["d"],(j,1,g["n"]-1))
        return scalar(value)
    if task in {"ap_membership","ap_count"}:
        target=g["value"] if task=="ap_membership" else g["last"]
        solutions=sp.solveset(g["a"]+(n-1)*g["d"]-target,n,domain=sp.S.Integers)
        if solutions is sp.S.Integers:ok=True;positive=[]
        elif solutions is sp.S.EmptySet:ok=False;positive=[]
        else:positive=[v for v in solutions if v>=1];ok=bool(positive)
        return {"kind":"boolean","value":ok} if task=="ap_membership" else finite_set(positive,"terms")
    if task=="ap_difference":
        a,d=sp.symbols("a d",real=True)
        result=sp.solve([a+(g["m"]-1)*d-g["term_m"],a+(g["n"]-1)*d-g["term_n"]],(a,d),dict=True)
        return scalar(result[0][d])
    if task=="ap_first":
        a=sp.Symbol("a",real=True)
        result=sp.solveset(a+(g["n"]-1)*g["d"]-g["term"],a,domain=sp.S.Reals)
        return scalar(next(iter(result)))
    if task=="ap_inverse_sum":
        j=sp.Symbol("j",integer=True)
        accumulated=sp.summation(g["a"]+j*g["d"],(j,0,n-1))
        solutions=sp.solveset(accumulated-exact(g["total"]),n,domain=sp.S.Integers)
        if solutions is sp.S.Integers:return {"kind":"classification","value":"infinitely_many_positive_counts"}
        return finite_set([] if solutions is sp.S.EmptySet else [v for v in solutions if v>=1],"terms")
    if task=="ap_recognition":
        first,second=g["terms"][:2]
        result=all(value==first+index*(second-first) for index,value in enumerate(g["terms"]))
        return {"kind":"boolean","value":result}
    if task=="ap_mean":
        b=sp.Symbol("b",real=True)
        return scalar(sp.solve(sp.Eq(b-g["left"],g["right"]-b),b)[0])
    if task=="ap_ledger_term":
        final=sp.Symbol("final",real=True)
        return scalar(sp.solve(sp.Eq(exact(g["previous_sum"])+final,exact(g["prefix_sum"])),final)[0])
    if task in {"trig_triangle_ratio","trig_scaled_triangle"}:
        multiplier=g["scale"] if task=="trig_scaled_triangle" else 1
        vertical=sp.Integer(g["opposite"]*multiplier);horizontal=sp.Integer(g["adjacent"]*multiplier)
        angle=sp.atan(vertical/horizontal)
        if g["reference"]=="C":angle=sp.pi/2-angle
        return scalar(sp.trigsimp(TRIG_FUNCTIONS[g["ratio"]](angle)))
    if task in {"trig_standard_value","trig_square_value"}:
        value=TRIG_FUNCTIONS[g["ratio"]](sp.Integer(g["angle_degrees"])*sp.pi/180)
        undefined=value.has(sp.zoo,sp.nan,sp.oo,-sp.oo)
        if task=="trig_standard_value":return {"kind":"defined_value","defined":not undefined,"value":None if undefined else canonical(g.get("coefficient",1)*value)}
        return scalar(g["factor"]*value**2)
    if task=="trig_from_ratio":
        value=exact(g["given_value"])
        inverse={"sin":sp.asin,"cos":sp.acos,"tan":sp.atan}
        angle=inverse[g["given_ratio"]](value)
        return scalar(sp.trigsimp(TRIG_FUNCTIONS[g["target_ratio"]](angle)))
    if task=="trig_identity_value":
        theta=sp.Symbol("theta",real=True)
        expression=exact(IDENTITY_VALUES[g["identity_id"]],{"theta":theta})
        simplified=sp.trigsimp(g["factor"]*expression)
        if simplified.free_symbols:raise MathInputError("Oracle did not establish constant identity")
        return scalar(simplified)
    if task=="trig_identity_truth":
        theta=sp.Symbol("theta",real=True)
        left,right=IDENTITY_CLAIMS[g["identity_id"]]
        difference=sp.trigsimp(exact(left,{"theta":theta})-exact(right,{"theta":theta}))
        if sp.simplify(difference)==0:return {"kind":"boolean","value":True}
        for degrees in [30,45,60]:
            angle=sp.Integer(degrees)*sp.pi/180
            a,b=exact(left,{"theta":angle}),exact(right,{"theta":angle})
            if sp.simplify(a-b)!=0:return {"kind":"boolean","value":False}
        raise MathInputError("No finite in-domain counterexample established")
    if task=="trig_domain":
        try:
            value=exact(DOMAIN_EXPRESSIONS[g["expression_id"]],{"theta":sp.Integer(g["angle_degrees"])*sp.pi/180})
            return {"kind":"defined_value","defined":True,"value":canonical(g.get("coefficient",1)*value)}
        except UndefinedMath:return {"kind":"defined_value","defined":False,"value":None}
    raise MathInputError("Unimplemented oracle route")


def render_prompt(p):
    validate_problem(p);task=p["task_type"];g=p["givens"]
    if task in assessment_tasks.CONCEPTS:return assessment_tasks.prompt(p)
    polynomial=f"({g.get('a')})*x^2+({g.get('b')})*x+({g.get('c')})"
    if task=="quadratic_solve":return f"Find every distinct real root of {polynomial}=0. Give exact values; do not repeat a repeated root."
    if task=="quadratic_coefficients":return f"Expand {polynomial_expression(g).replace('**','^')} and state the signed coefficients of x^2, x and the constant, including zeros."
    if task=="quadratic_degree":return f"After collecting like terms in {polynomial_expression(g).replace('**','^')}, classify it as quadratic, linear, constant_nonzero or zero_polynomial."
    if task=="quadratic_classify":return f"Classify the real roots of {polynomial}=0 as two_distinct_real, repeated_real or no_real, using a checked discriminant."
    if task=="quadratic_parameter_repeated":return f"Find every real k for which x^2+2*k*x+({g['c']})=0 has a repeated real root."
    if task=="quadratic_rectangle":return f"A rectangle has area {g['area']} square units and length equal to its width plus ({g['gap']}) units. Find its positive width, checking that both dimensions are positive."
    if task=="quadratic_under_specified_rectangle":return f"A rectangle has positive side lengths x and y and area {g['area']} square units. Neither side is designated as the longer one. No perimeter, ratio or other dimension is supplied. Can x be determined uniquely? If further information is needed, classify that explicitly and justify it with distinct admissible dimensions."
    if task=="quadratic_speed":return f"A vehicle travels {g['distance']} km at a constant speed. Reducing its speed by {g['reduction']} km/h increases travel time by {g['delay']} hours. Find the original speed in km/h; it must exceed the reduction."
    if task=="quadratic_check_claim":return f"For {polynomial}=0, a learner claims the complete list of distinct real roots is {g['claimed_roots']}. Is that claim correct, including completeness and absence of duplicates?"
    if task=="ap_term":return f"An AP starts at {g['a']} with common difference {g['d']}. Find term {g['n']}, using one-based positions."
    if task=="ap_sum":return f"Find the sum of the first {g['n']} terms of an AP with first term {g['a']} and common difference {g['d']}."
    if task=="ap_membership":return f"Does the value {g['value']} occur at any positive integer position in the AP with first term {g['a']} and common difference {g['d']}?"
    if task=="ap_difference":return f"An AP has term {g['m']} equal to {g['term_m']} and term {g['n']} equal to {g['term_n']}. Find its signed common difference."
    if task=="ap_first":return f"An AP has common difference {g['d']} and term {g['n']} equal to {g['term']}. Find its first term."
    if task=="ap_count":return f"A finite AP begins at {g['a']}, has common difference {g['d']} and last term {g['last']}. Give all possible positive integer term counts; use an empty set if no such finite AP exists."
    if task=="ap_inverse_sum":return f"An AP begins at {g['a']} with difference {g['d']}. Its first n terms sum to {g['total']}. Find all positive integer n; if every positive count works, classify that explicitly."
    if task=="ap_recognition":return f"Are {g['terms']} consecutive terms of one AP? Check every observed term."
    if task=="ap_mean":return f"Insert one value between {g['left']} and {g['right']} so that the three values form an AP."
    if task=="ap_ledger_term":return f"An AP ledger reports S_{g['n']-1}={g['previous_sum']} and S_{g['n']}={g['prefix_sum']}. Find the term at position {g['n']}; distinguish an individual term from a cumulative sum."
    if task in {"trig_triangle_ratio","trig_scaled_triangle"}:
        text=f"A right triangle has hypotenuse {g['hypotenuse']}, opposite side {g['opposite']} and adjacent side {g['adjacent']} relative to acute angle A. C is its other acute angle. "
        if task=="trig_scaled_triangle":text+=f"Every side is multiplied by {g['scale']}. "
        return text+f"Find {g['ratio']}({g['reference']}) exactly."
    if task in {'trig_standard_value','trig_domain'} and 'coefficient' in g:
        inner=f"{g['ratio']}({g['angle_degrees']} degrees)" if task=='trig_standard_value' else DOMAIN_EXPRESSIONS[g['expression_id']].replace('**','^')
        return f"Evaluate the ORIGINAL expression ({g['coefficient']})*({inner}) at theta={g['angle_degrees']} degrees. Check the original ratio and denominators before multiplication, even for a zero coefficient; report an exact value or undefined."
    if task=="trig_standard_value":return f"Evaluate {g['ratio']}({g['angle_degrees']} degrees) exactly if defined. If undefined, state that explicitly instead of returning zero or infinity."
    if task=="trig_from_ratio":return f"For an acute angle A, {g['given_ratio']}(A)={g['given_value']}. Find {g['target_ratio']}(A) exactly, using the positive acute-angle values."
    if task=="trig_identity_value":return f"For any acute theta, simplify {g['factor']}*({IDENTITY_VALUES[g['identity_id']].replace('**','^')}). Explain the identity and retain its original domain."
    if task=="trig_identity_truth":
        left,right=IDENTITY_CLAIMS[g["identity_id"]]
        return f"Does ({left.replace('**','^')})=({right.replace('**','^')}) hold for every acute theta? A true verdict needs valid identity reasoning; a false verdict needs a finite counterexample inside the acute domain."
    if task=="trig_square_value":return f"Evaluate {g['factor']}*({g['ratio']}({g['angle_degrees']} degrees))^2 exactly. The square applies to the ratio value, not the angle."
    if task=="trig_domain":return f"Evaluate the ORIGINAL expression {DOMAIN_EXPRESSIONS[g['expression_id']].replace('**','^')} at theta={g['angle_degrees']} degrees. Is it defined? If so, give its exact value. Do not cancel away original domain restrictions."
    raise MathInputError("Unimplemented prompt renderer")


def generate_problem(task,index,rng):
    """Diverse primitive cases, including signed/zero/boundary parameters."""
    if task in assessment_tasks.CONCEPTS:return problem(task,assessment_tasks.generate(task,index,rng))
    if task in {"quadratic_solve","quadratic_classify","quadratic_check_claim"}:
        a=rng.choice([-5,-3,-2,-1,1,2,3,5])
        mode=index%5
        if mode==0:b=0;c=0
        elif mode==1:r=rng.randint(-15,15);b=-2*a*r;c=a*r*r
        elif mode==2:b=2*rng.randint(-12,12)*a;c=(b*b//(4*a))+a*rng.randint(1,8)
        elif mode==3:b=rng.randint(-25,25);c=rng.randint(-50,50)
        else:r,s=rng.sample(range(-18,19),2);b=-a*(r+s);c=a*r*s
        g={"a":a,"b":b,"c":c}
        if task=="quadratic_check_claim":
            roots=finite_set(real_quadratic_roots(a,b,c))["values"]
            claimed=list(roots)
            if index%3==0:claimed=claimed+["999"]
            elif index%3==1:claimed=claimed[:-1] if claimed else ["0"]
            g["claimed_roots"]=claimed
        return problem(task,g)
    if task in {"quadratic_coefficients","quadratic_degree"}:
        p,q,r,s=(rng.randint(-9,9) for _ in range(4));t=-p*r if index%3==0 else rng.randint(-10,10)
        if task=="quadratic_degree":
            if index%4==0:q=s=0;t=-p*r
            elif index%4==1:p=1;q=rng.randint(1,12);r=-1;s=q;t=1
            elif index%4==2:p=1;r=0;s=rng.choice([-5,-2,2,7]);t=0
            elif p*r+t==0:t+=1
        return problem(task,{"p":p,"q":q,"r":r,"s":s,"t":t})
    if task=="quadratic_parameter_repeated":return problem(task,{"c":rng.randint(-20,150)})
    if task=="quadratic_under_specified_rectangle":return problem(task,{'area':rng.randint(1,1200)})
    if task=="quadratic_rectangle":
        width=rng.randint(3,35);gap=rng.randint(-width+1,15)
        return problem(task,{"area":rng.randint(5,800) if index%4==0 else width*(width+gap),"gap":gap})
    if task=="quadratic_speed":
        reduction=rng.randint(1,12);speed=reduction+rng.randint(5,65);delay=rng.randint(1,4)
        if index%4==0:return problem(task,{"distance":str(rng.randint(20,700)),"reduction":str(reduction),"delay":str(Fraction(delay,2))})
        return problem(task,{"distance":str(Fraction(delay*speed*(speed-reduction),reduction)),"reduction":str(reduction),"delay":str(delay)})
    if task.startswith("ap_"):
        a=rng.randint(-25,40);d=rng.randint(-8,10);n=rng.randint(1,35)
        if task in {"ap_term","ap_sum"}:g={"a":a,"d":d,"n":n}
        elif task=="ap_membership":g={"a":a,"d":d,"value":a+(n-1)*d+(0 if index%2==0 else 1)}
        elif task=="ap_difference":
            m=rng.choice([v for v in range(1,36) if v!=n]);g={"m":m,"n":n,"term_m":a+(m-1)*d,"term_n":a+(n-1)*d+(1 if index%4==0 else 0)}
        elif task=="ap_first":g={"d":d,"n":n,"term":a+(n-1)*d}
        elif task=="ap_count":
            d=d or 1;g={"a":a,"d":d,"last":a+(n-1)*d+(1 if index%4==0 else 0)}
        elif task=="ap_inverse_sum":
            if index%9==0:g={"a":0,"d":0,"total":"0"}
            elif index%9==1:g={"a":0,"d":0,"total":"1"}
            elif index%9==2:g={"a":5,"d":-1,"total":"5"}
            elif index%9==3:g={"a":1,"d":1,"total":"501501"}
            else:g={"a":a,"d":d,"total":str(Fraction(n*(2*a+(n-1)*d),2))}
        elif task=="ap_recognition":
            terms=[a+j*d for j in range(4)]
            if index%2:terms[2]+=rng.choice([-3,-1,1,4])
            g={"terms":terms}
        elif task=="ap_mean":g={"left":a,"right":a+2*d+(1 if index%3==0 else 0)}
        elif task=="ap_ledger_term":
            n=max(2,n);g={"n":n,"previous_sum":str(Fraction((n-1)*(2*a+(n-2)*d),2)),"prefix_sum":str(Fraction(n*(2*a+(n-1)*d),2))}
        else:raise MathInputError("Unknown AP task")
        return problem(task,g)
    if task in {"trig_triangle_ratio","trig_scaled_triangle","trig_from_ratio"}:
        m=rng.randint(2,14);n=rng.randint(1,m-1)
        o,adj,h=m*m-n*n,2*m*n,m*m+n*n
        divisor=math.gcd(o,math.gcd(adj,h));o//=divisor;adj//=divisor;h//=divisor
        if task=="trig_from_ratio":
            given=rng.choice(["sin","cos","tan"]);target=rng.choice([r for r in RATIOS if r!=given])
            if index%3==0:
                denominator=rng.randint(3,15);numerator=rng.randint(1,denominator-1)
                return problem(task,{"given_ratio":given,"given_value":str(Fraction(numerator,denominator)),"target_ratio":target})
            return problem(task,{"given_ratio":given,"given_value":canonical(ratio_from_sides(given,o,adj,h)),"target_ratio":target})
        g={"opposite":o,"adjacent":adj,"hypotenuse":h,"ratio":rng.choice(RATIOS),"reference":rng.choice(["A","C"])}
        if task=="trig_scaled_triangle":g["scale"]=rng.randint(2,12)
        return problem(task,g)
    if task=="trig_standard_value":return problem(task,{"ratio":RATIOS[index%6],"angle_degrees":[0,30,45,60,90][(index//6)%5]})
    if task=="trig_square_value":return problem(task,{"ratio":rng.choice(RATIOS),"angle_degrees":rng.choice([30,45,60]),"factor":rng.randint(-8,12) or 1})
    if task=="trig_identity_value":return problem(task,{"identity_id":list(IDENTITY_VALUES)[index%3],"factor":rng.randint(-20,20) or 1})
    if task=="trig_identity_truth":return problem(task,{"identity_id":list(IDENTITY_CLAIMS)[index%10]})
    if task=="trig_domain":return problem(task,{"expression_id":list(DOMAIN_EXPRESSIONS)[index%7],"angle_degrees":[0,30,45,60,90][(index//7)%5]})
    raise MathInputError("Unimplemented problem generator")
