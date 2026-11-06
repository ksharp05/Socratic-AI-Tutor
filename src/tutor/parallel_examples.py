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
VERSION='parallel-example-v1'

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


def worked(problem,key):
    task,g=problem['task_type'],problem['givens'];steps=[];lines=[]
    def step(op,a,b,result,label=None):
        data=arithmetic(op,a,b,result);steps.append(data)
        symbols={'add':'+','subtract':'-','multiply':'*','divide':'/'}
        right='one' if label=='one' else 'two' if label=='two' else str(b)
        lines.append(f"{a} {symbols[op]} {right} = {result}.")
    if task=='quadratic_solve':
        values=sorted((f(v) for v in key['values']));r,s=values
        prompt=f"Solve x*x - {r+s}*x = {-r*s}."
        lines=[f"Move the constant to form x*x - {r+s}*x + {r*s}.",f"Factor: (x - {r})*(x - {s}).",'A zero product has a zero factor.',f"Example solutions: x = {r} or x = {s}."]
        steps=[{'operation':'factor_roots','roots':[str(r),str(s)]}]
    elif task=='ap_term':
        prompt=f"An AP starts at {g['a']} with difference {g['d']}. Find term {g['n']}."
        jumps=g['n']-1;change=jumps*g['d'];step('subtract',g['n'],1,jumps,'one');step('multiply',jumps,g['d'],change);step('add',g['a'],change,g['a']+change)
    elif task=='ap_sum':
        prompt=f"An AP starts at {g['a']} with difference {g['d']}. Add its first {g['n']} terms."
        jumps=g['n']-1;last=g['a']+jumps*g['d'];pair=g['a']+last;product=g['n']*pair
        step('subtract',g['n'],1,jumps,'one');step('multiply',jumps,g['d'],jumps*g['d']);step('add',g['a'],jumps*g['d'],last);step('add',g['a'],last,pair);step('multiply',g['n'],pair,product);step('divide',product,2,Fraction(product,2),'two')
    elif task=='ap_first':
        prompt=f"Term {g['n']} of an AP is {g['term']}, with difference {g['d']}. Find its first term."
        jumps=g['n']-1;change=jumps*g['d'];step('subtract',g['n'],1,jumps,'one');step('multiply',jumps,g['d'],change);step('subtract',g['term'],change,g['term']-change)
    elif task=='ap_difference':
        prompt=f"An AP has term {g['m']} = {g['term_m']} and term {g['n']} = {g['term_n']}. Find its difference."
        gap=g['n']-g['m'];change=g['term_n']-g['term_m'];step('subtract',g['n'],g['m'],gap);step('subtract',g['term_n'],g['term_m'],change);step('divide',change,gap,Fraction(change,gap))
    elif task=='ap_count':
        prompt=f"An AP starts at {g['a']}, changes by {g['d']}, and ends at {g['last']}. Count its terms."
        change=g['last']-g['a'];gap=Fraction(change,g['d']);step('subtract',g['last'],g['a'],change);step('divide',change,g['d'],gap);step('add',gap,1,gap+1,'one')
    elif task=='ap_mean':
        prompt=f"Insert an arithmetic mean between {g['left']} and {g['right']}."
        change=g['right']-g['left'];half=Fraction(change,2);step('subtract',g['right'],g['left'],change);step('divide',change,2,half,'two');step('add',g['left'],half,f(g['left'])+half)
    elif task=='ap_ledger_term':
        prompt=f"Prefix totals are S_{g['n']-1} = {g['previous_sum']} and S_{g['n']} = {g['prefix_sum']}. Find term {g['n']}."
        lines.append('The later total includes one extra term.');step('subtract',g['prefix_sum'],g['previous_sum'],f(g['prefix_sum'])-f(g['previous_sum']))
    else:
        o,a,h=g['opposite'],g['adjacent'],g['hypotenuse']
        if g['reference']=='C':o,a=a,o
        numerators={'sin':(o,h,'opposite / hypotenuse'),'cos':(a,h,'adjacent / hypotenuse'),'tan':(o,a,'opposite / adjacent'),'csc':(h,o,'hypotenuse / opposite'),'sec':(h,a,'hypotenuse / adjacent'),'cot':(a,o,'adjacent / opposite')}
        num,den,meaning=numerators[g['ratio']]
        prompt=f"Relative to angle {g['reference']}, opposite = {o}, adjacent = {a}, hypotenuse = {h}. Find {g['ratio']} of that angle."
        lines.append(f"Use {meaning}.");step('divide',num,den,Fraction(num,den))
    presentation='Parallel example (different numbers): '+prompt+'\n'+'\n'.join(lines)+'\nWhich matching step can you apply to your item?'
    return {'question':prompt,'worked_steps':steps,'presentation':presentation}


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
        return {'available':True,'verified':True,'version':VERSION,'source_question_ref':item['question_id'],'active_problem_sha256':digest(original),'example_id':'parallel:'+digest(problem)[:24],'example':example,'example_sha256':digest(example),'not_the_active_solution':True,'teacher_review_status':'not_reviewed','scope':'generated parallel practice example, never an assessment item','structure_preserved':['task_type','givens_schema','answer_kind'],'boundary_regime_preserved':False}
    return {'available':False,'reason':'no_distinct_verified_example_passed_active_item_guard'}
