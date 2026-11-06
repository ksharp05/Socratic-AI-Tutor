"""Deterministic, verified TP-A2 examples for connected public practice families.

No assessment files, simulator rules, models or active-item answer disclosures.
R3 owns when this service is called and how the verified presentation is shown.
"""
from __future__ import annotations
import copy,hashlib,json
from fractions import Fraction
from . import mathcore
from socratic_data import math_kernel as mk

SUPPORTED=frozenset({'quadratic_solve','ap_term','ap_sum','ap_first','ap_difference','ap_count','ap_mean','ap_ledger_term','trig_triangle_ratio'})
VERSION='parallel-example-v2'

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def f(value):return Fraction(str(value))
def arithmetic(operation,left,right,result):return {'operation':operation,'left':str(left),'right':str(right),'result':str(result)}
def calculate(step):
    a,b=f(step['left']),f(step['right'])
    return {'add':lambda:a+b,'subtract':lambda:a-b,'multiply':lambda:a*b,'divide':lambda:a/b}[step['operation']]()

def candidate(source,index):
    task=source['task_type'];a=11+index%71;d=5+index%17;n=4+index%5
    problem=copy.deepcopy(source)
    if task=='quadratic_solve':
        r,s=3+index%13,23+index%17;g={'a':1,'b':-(r+s),'c':r*s}
    elif task in ('ap_term','ap_sum'):g={'a':a,'d':d,'n':n}
    elif task=='ap_first':g={'d':d,'n':n,'term':a+(n-1)*d}
    elif task=='ap_difference':
        m=3+index%4;position=m+n;g={'m':m,'n':position,'term_m':a+(m-1)*d,'term_n':a+(position-1)*d}
    elif task=='ap_count':g={'a':a,'d':d,'last':a+(n-1)*d}
    elif task=='ap_mean':g={'left':a,'right':a+2*d}
    elif task=='ap_ledger_term':g={'n':n,'previous_sum':str(Fraction((n-1)*(2*a+(n-2)*d),2)),'prefix_sum':str(Fraction(n*(2*a+(n-1)*d),2))}
    else:
        o,adj,h=[(5,12,13),(7,24,25),(8,15,17),(20,21,29),(9,40,41)][index%5]
        scale=1+index//5%5;g={'opposite':o*scale,'adjacent':adj*scale,'hypotenuse':h*scale,'ratio':source['givens']['ratio'],'reference':source['givens']['reference']}
    problem['givens']=g;return problem


def worked(problem: dict, key: dict) -> dict:
    """Bind each checked operation to a short explanation of its purpose."""
    task, g = problem["task_type"], problem["givens"]
    steps, lines = [], []

    def step(operation, left, right, result, explanation):
        steps.append(arithmetic(operation, left, right, result))
        lines.append(explanation)

    if task == "quadratic_solve":
        r, s = sorted(f(value) for value in key["values"])
        prompt = f"Solve x*x - {r+s}*x = {-r*s}."
        lines = [
            f"Put all terms on the left: x*x - {r+s}*x + {r*s} = zero.",
            f"Factor the left side: (x - {r})*(x - {s}) = zero.",
            "A product is zero only if at least one factor is zero.",
            f"The example solutions are x = {r} or x = {s}.",
        ]
        steps = [{"operation": "factor_roots", "roots": [str(r), str(s)]}]
        transfer = "Which factors could make a zero product in your question?"
    elif task == "ap_term":
        prompt = f"An AP starts at {g['a']} with difference {g['d']}. Find term {g['n']}."
        jumps = g["n"] - 1
        change = jumps * g["d"]
        step("subtract", g["n"], 1, jumps,
             f"From the first term to position {g['n']}, there are {jumps} equal jumps.")
        step("multiply", jumps, g["d"], change,
             f"Find the total change: {jumps} * {g['d']} = {change}.")
        step("add", g["a"], change, g["a"] + change,
             f"Add that change to the first term: {g['a']} + {change} = {g['a'] + change}.")
        transfer = "How many equal jumps lead to the term in your question?"
    elif task == "ap_sum":
        prompt = f"An AP starts at {g['a']} with difference {g['d']}. Add its first {g['n']} terms."
        jumps = g["n"] - 1
        change = jumps * g["d"]
        last = g["a"] + change
        pair = g["a"] + last
        product = g["n"] * pair
        step("subtract", g["n"], 1, jumps,
             f"To reach the last term at position {g['n']}, take {jumps} equal jumps.")
        step("multiply", jumps, g["d"], change,
             f"Find the change to the last term: {jumps} * {g['d']} = {change}.")
        step("add", g["a"], change, last,
             f"The last term is {g['a']} + {change} = {last}.")
        step("add", g["a"], last, pair,
             f"Pair the first and last terms: {g['a']} + {last} = {pair}.")
        step("multiply", g["n"], pair, product,
             f"Multiply this pair total by the term count: {g['n']} * {pair} = {product}.")
        step("divide", product, 2, Fraction(product, 2),
             f"This counts every term twice, so halve the total. The example sum is {Fraction(product, 2)}.")
        transfer = "Which first and last terms would you pair in your question?"
    elif task == "ap_first":
        prompt = f"Term {g['n']} of an AP is {g['term']}, with difference {g['d']}. Find its first term."
        jumps = g["n"] - 1
        change = jumps * g["d"]
        first = g["term"] - change
        step("subtract", g["n"], 1, jumps,
             f"The known term is {jumps} equal jumps after the first term.")
        step("multiply", jumps, g["d"], change,
             f"Find the total change across those jumps: {jumps} * {g['d']} = {change}.")
        step("subtract", g["term"], change, first,
             f"Undo that change to recover the first term: {g['term']} - {change} = {first}.")
        transfer = "What total change should you subtract from your known term?"
    elif task == "ap_difference":
        prompt = f"An AP has term {g['m']} = {g['term_m']} and term {g['n']} = {g['term_n']}. Find its difference."
        gap = g["n"] - g["m"]
        change = g["term_n"] - g["term_m"]
        difference = Fraction(change, gap)
        step("subtract", g["n"], g["m"], gap,
             f"Count the equal jumps between the positions: {g['n']} - {g['m']} = {gap}.")
        step("subtract", g["term_n"], g["term_m"], change,
             f"Find the change in term values: {g['term_n']} - {g['term_m']} = {change}.")
        step("divide", change, gap, difference,
             f"Divide by the jump count to find the change per jump: {change} / {gap} = {difference}.")
        transfer = "How many equal jumps separate the known terms in your question?"
    elif task == "ap_count":
        prompt = f"An AP starts at {g['a']}, changes by {g['d']}, and ends at {g['last']}. Count its terms."
        change = g["last"] - g["a"]
        jumps = Fraction(change, g["d"])
        count = jumps + 1
        step("subtract", g["last"], g["a"], change,
             f"Find the total change: {g['last']} - {g['a']} = {change}.")
        step("divide", change, g["d"], jumps,
             f"Count the equal jumps: {change} / {g['d']} = {jumps}.")
        step("add", jumps, 1, count,
             f"Include the starting term as well as the jumps. The example contains {count} terms.")
        transfer = "How many equal jumps fit between your first and last terms?"
    elif task == "ap_mean":
        prompt = f"Insert an arithmetic mean between {g['left']} and {g['right']}."
        change = g["right"] - g["left"]
        half = Fraction(change, 2)
        mean = f(g["left"]) + half
        lines.append("The arithmetic mean sits halfway between the given numbers.")
        step("subtract", g["right"], g["left"], change,
             f"Find the gap between them: {g['right']} - {g['left']} = {change}.")
        step("divide", change, 2, half, f"Half of that gap is {half}.")
        step("add", g["left"], half, mean,
             f"Move halfway from the first number: {g['left']} + {half} = {mean}.")
        transfer = "What is half the gap between your given numbers?"
    elif task == "ap_ledger_term":
        prompt = f"Prefix totals are S_{g['n']-1} = {g['previous_sum']} and S_{g['n']} = {g['prefix_sum']}. Find term {g['n']}."
        value = f(g["prefix_sum"]) - f(g["previous_sum"])
        lines.append("A prefix total adds all terms up to its position; it is not an individual term.")
        lines.append("The later total contains the earlier total plus the next term.")
        step("subtract", g["prefix_sum"], g["previous_sum"], value,
             f"Subtract the earlier total to leave only that next term: {g['prefix_sum']} - {g['previous_sum']} = {value}.")
        transfer = "Which earlier total should you subtract from the later total?"
    else:
        opposite, adjacent, hypotenuse = g["opposite"], g["adjacent"], g["hypotenuse"]
        if g["reference"] == "C":
            opposite, adjacent = adjacent, opposite
        ratios = {
            "sin": (opposite, hypotenuse, "opposite / hypotenuse"),
            "cos": (adjacent, hypotenuse, "adjacent / hypotenuse"),
            "tan": (opposite, adjacent, "opposite / adjacent"),
            "csc": (hypotenuse, opposite, "hypotenuse / opposite"),
            "sec": (hypotenuse, adjacent, "hypotenuse / adjacent"),
            "cot": (adjacent, opposite, "adjacent / opposite"),
        }
        numerator, denominator, meaning = ratios[g["ratio"]]
        prompt = f"Relative to angle {g['reference']}, opposite = {opposite}, adjacent = {adjacent}, hypotenuse = {hypotenuse}. Find {g['ratio']} of that angle."
        lines.append(f"For {g['ratio']} of this angle, use {meaning}.")
        step("divide", numerator, denominator, Fraction(numerator, denominator),
             f"Substitute the matching sides: {numerator} / {denominator} = {Fraction(numerator, denominator)}.")
        transfer = "Which two sides form that ratio in your question?"
    presentation = "Parallel example (different numbers): " + prompt + "\n" + "\n".join(lines) + "\n" + transfer
    return {"question": prompt, "worked_steps": steps, "presentation": presentation}


def verify(example):
    try:
        problem,key=example['problem'],example['answer'];task=problem['task_type']
        if task not in SUPPORTED:return False
        check=mathcore.compute_key(problem)
        if not check['verified'] or not mk.answers_equivalent(key,check['key']):return False
        if worked(problem,key)!={k:example[k] for k in ('question','worked_steps','presentation')}:return False
        for step in example['worked_steps']:
            if step['operation']=='factor_roots':
                roots=[f(v) for v in step['roots']];g=problem['givens']
                if len(roots)!=2 or sum(roots)!=Fraction(-g['b'],g['a']) or roots[0]*roots[1]!=Fraction(g['c'],g['a']):return False
            elif calculate(step)!=f(step['result']):return False
        last=example['worked_steps'][-1]
        if task!='quadratic_solve':
            output={'kind':'finite_set','values':[last['result']],'unit':'terms'} if task=='ap_count' else {'kind':'scalar','value':last['result']}
            if not mk.answers_equivalent(output,key):return False
        return True
    except (KeyError,TypeError,ValueError,ZeroDivisionError,OverflowError):return False


def generate(item,active_key):
    original=item['problem'];task=original.get('task_type')
    if task not in SUPPORTED:return {'available':False,'reason':'unsupported_task_family'}
    checked=mathcore.compute_key(original)
    if not checked['verified'] or not mk.answers_equivalent(active_key,checked['key']):return {'available':False,'reason':'unverified_active_problem'}
    start=int(digest(original)[:8],16)%997
    for attempt in range(64):
        problem=candidate(original,start+attempt);result=mathcore.compute_key(problem)
        if not result['verified'] or mk.answers_equivalent(active_key,result['key']):continue
        if active_key.get('kind')==result['key'].get('kind')=='finite_set' and any(mk.equivalent(a,b) for a in active_key['values'] for b in result['key']['values']):continue
        example={'problem':problem,'answer':result['key'],**worked(problem,result['key'])}
        if not verify(example) or mathcore.leak_check(example['presentation'],active_key)['leak']:continue
        return {'available':True,'verified':True,'version':VERSION,'source_question_ref':item['question_id'],'active_problem_sha256':digest(original),'example_id':'parallel:'+digest({'version':VERSION,'problem':problem})[:24],'example':example,'example_sha256':digest(example),'not_the_active_solution':True,'teacher_review_status':'not_reviewed','scope':'generated parallel practice example, never an assessment item','structure_preserved':['task_type','givens_schema','answer_kind'],'boundary_regime_preserved':False}
    return {'available':False,'reason':'no_distinct_verified_example_passed_active_item_guard'}
