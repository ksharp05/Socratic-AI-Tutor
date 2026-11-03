"""Independent reference checks derived from displayed public problem statements.

Keys stay inside this verifier; reports contain only IDs, statuses and issue codes.
This is bounded prompt verification, not certification of teaching quality.
"""
import re
from fractions import Fraction
import sympy as sp

X=sp.Symbol('x',real=True)

def norm(text):return text.replace('\u2212','-').replace('\u00b2','**2').replace('\u03b8','theta').replace('\u00b0',' degrees')

def expression(text):
    source=norm(text).strip()
    if len(source)>256 or not re.fullmatch(r'[0-9x+*/().\-\s]+',source):raise ValueError('Unsupported displayed expression')
    source=re.sub(r'(\d)(?=[x(])',r'\1*',source)
    source=re.sub(r'x(?=\()',r'x*',source)
    source=re.sub(r'\)(?=[x(\d])',r')*',source)
    # The character allowlist above prohibits names, calls and attributes other than x.
    from socratic_data.math_kernel import exact
    return exact(source,{'x':X})

def equation(text):
    lhs,rhs=text.split('=');return sp.expand(expression(lhs)-expression(rhs))

def number(text):return sp.Rational(norm(text).strip())

def check_reference(problem,reference):
    p=norm(problem['problem_text']);answer=norm(reference['expected_answer']);kind=reference['math_check']['type']
    nums=[int(n) for n in re.findall(r'(?<![\w*])-?\d+',p)]
    notes=[];passed=False
    if kind in {'root_factors','zero_product','double_root','square_roots'}:
        eq=equation(p.removeprefix('Solve ').removesuffix('.'))
        roots=sp.solveset(eq,X,domain=sp.S.Reals)
        proposed={sp.Integer(n) for n in re.findall(r'x\s*=\s*(-?\d+)',answer)}
        passed=isinstance(roots,sp.FiniteSet) and proposed==set(roots)
    elif kind=='coefficients':
        eq=equation(p.removeprefix('Identify a, b and c in ').removesuffix('.'))
        poly=sp.Poly(eq,X);got=[int(re.search(r'\b'+n+r'\s*=\s*(-?\d+)',answer).group(1)) for n in 'abc']
        passed=got==poly.all_coeffs()
    elif kind=='discriminant':
        eq=equation(p.removeprefix('Classify the real roots of ').split(' using')[0]);d=sp.discriminant(eq,X)
        stated=int(re.search(r'D\s*=\s*(-?\d+)',answer).group(1))
        passed=d==stated and d<0 and 'No real roots' in answer
    elif kind=='standard_form':
        eq=equation(p.removeprefix('Write ').split(' in standard')[0]);got=equation(answer)
        passed=sp.expand(eq-got)==0 and sp.Poly(got,X).degree()==2
    elif kind=='diff_squares':
        original=expression(p.removeprefix('Factor ').removesuffix('.'));got=expression(answer)
        passed=sp.expand(original-got)==0 and sp.Poly(original,X).degree()==2
    elif kind=='rectangle':
        k,area=map(int,re.search(r'length \(x \+ (\d+)\) cm and area (\d+) cm',p).groups())
        passed=sp.expand(equation(answer)-(X*(X+k)-area))==0
    elif kind in {'ap_nth','ap_zero'}:
        if 'first term' in p:
            a,d,n=nums
        else:a,d,n=nums[0],nums[1]-nums[0],nums[-1]
        # Recurrence, not the generator's closed form.
        value=a
        for _ in range(n-1):value+=d
        passed=number(answer)==value and n>0
    elif kind=='ap_difference':passed=number(answer)==nums[1]-nums[0]==nums[2]-nums[1]
    elif kind=='ap_sum':
        n,a,b,c=nums;d=b-a
        passed=number(answer)==sum(a+i*d for i in range(n)) and c-b==d and n>0
    elif kind=='ap_find_n':
        a,d,target=nums;n=sp.Rational(target-a,d)+1
        passed=n.is_Integer is True and n>0 and int(re.fullmatch(r'Term (\d+)',answer).group(1))==n
    elif kind=='ap_real_world':
        first,first_index,d,n=nums;value=first
        for _ in range(n-first_index):value+=d
        passed=int(re.fullmatch(r'(\d+) seats',answer).group(1))==value and first_index==1
    elif kind=='not_ap':
        deltas=[b-a for a,b in zip(nums,nums[1:])]
        passed=len(set(deltas))>1 and answer.startswith('No;')
    elif kind=='trig_ratio':
        opp,adj,hyp=nums;fn=re.search(r'Find (sin|cos|tan) theta',p).group(1)
        angle=sp.atan(sp.Rational(opp,adj))
        value={'sin':sp.sin,'cos':sp.cos,'tan':sp.tan}[fn](angle)
        passed=min(opp,adj,hyp)>0 and opp**2+adj**2==hyp**2 and sp.simplify(value-number(answer))==0
    elif kind=='trig_identity':
        opp,hyp=nums;adj=sp.sqrt(hyp**2-opp**2)
        passed=0<opp<hyp and sp.simplify(adj/hyp-number(answer))==0
    elif kind=='special_angle':
        match=re.search(r'\b(sin|tan)(?= |\()',p)
        fn=match.group(1) if match else 'tan' if 'tangent' in p else None
        if fn is None:raise ValueError('Unrecognized displayed angle request')
        angle=nums[0]
        value={'sin':sp.sin,'tan':sp.tan}[fn](angle*sp.pi/180)
        passed=sp.simplify(value-number(answer))==0
    elif kind=='cot':
        opp,adj=nums
        passed=opp>0 and adj>0 and number(answer)==sp.Rational(adj,opp)
    elif kind=='hypotenuse':
        a,b,c=sorted(nums)
        passed=a>0 and a*a+b*b==c*c and int(re.fullmatch(r'(\d+) cm',answer).group(1))==c
    else:raise ValueError('Unimplemented public prompt family')
    return {'problem_id':problem['id'],'status':'pass' if passed else 'fail','method':'displayed_givens_exact_symbolic_or_recurrence','math_type':kind}
