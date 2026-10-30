"""Additional assessment structures, with independent primitive-given routes.

These improve internal assessment coverage. They do not establish independent
authorship or turn shared curriculum knowledge into unseen evaluation evidence.
"""
from fractions import Fraction
import sympy as sp
from .math_kernel import exact,canonical,scalar,UndefinedMath,MathInputError

CONCEPTS={
 'quadratic_reconstruct':['qe01','qe02','qe04'],
 'quadratic_shift_classify':['qe06'],
 'ap_formula_recognition':['ap01'],
 'ap_from_prefix_sums':['ap03','ap04','ap06','ap07','ap08'],
 'trig_similar_missing_side':['tr01','tr02','tr04'],
 'trig_degree_expression':['tr05','tr06','tr07'],
}
FIELDS={
 'quadratic_reconstruct':dict.fromkeys(['leading','root_one','root_two'],'int'),
 'quadratic_shift_classify':dict.fromkeys(['leading','shift','level'],'int'),
 'ap_formula_recognition':dict.fromkeys(['quadratic','linear','constant'],'int'),
 'ap_from_prefix_sums':{'m':'position','k':'position','n':'position','sum_m':'exact','sum_k':'exact'},
 'trig_similar_missing_side':{'leg':'int','hypotenuse':'int','scale':'exact','reference':'text','ratio':'text'},
 'trig_degree_expression':{'left_ratio':'text','right_ratio':'text','left_degrees':'int','right_degrees':'int','operation':'text','factor':'int'},
}
RATIOS=('sin','cos','tan','sec','csc','cot')
OPERATIONS={'add':'+','subtract':'-','multiply':'*','divide':'/'}
ANGLES=[0,30,45,60,90]
EDGE_GIVENS={
 'quadratic_reconstruct':[
  {'leading':-2,'root_one':37,'root_two':37},
  {'leading':1,'root_one':0,'root_two':37},
  {'leading':4,'root_one':-29,'root_two':37},
 ],
 'quadratic_shift_classify':[
  {'leading':-2,'shift':37,'level':-8},
  {'leading':-2,'shift':37,'level':8},
  {'leading':3,'shift':-37,'level':0},
 ],
 'ap_formula_recognition':[
  {'quadratic':0,'linear':0,'constant':9},
  {'quadratic':0,'linear':-3,'constant':7},
  {'quadratic':1,'linear':-3,'constant':2},
 ],
 'ap_from_prefix_sums':[
  {'m':1,'k':3,'n':4,'sum_m':'5','sum_k':'9'},
  {'m':1,'k':2,'n':3,'sum_m':'1/2','sum_k':'2'},
  {'m':5,'k':2,'n':6,'sum_m':'0','sum_k':'0'},
  {'m':2,'k':5,'n':7,'sum_m':'-3','sum_k':'15'},
 ],
 'trig_similar_missing_side':[
  {'leg':3,'hypotenuse':5,'scale':'2/3','reference':angle,'ratio':ratio}
  for angle in ['D','F'] for ratio in RATIOS
 ]+[
  {'leg':1,'hypotenuse':2,'scale':'3/2','reference':'D','ratio':'sin'},
  {'leg':1,'hypotenuse':2,'scale':'2','reference':'F','ratio':'cos'},
 ],
 'trig_degree_expression':[
  {'left_ratio':'tan','left_degrees':90,'right_ratio':'sin','right_degrees':30,'operation':'multiply','factor':0},
  {'left_ratio':'sin','left_degrees':0,'right_ratio':'cos','right_degrees':90,'operation':'divide','factor':1},
  {'left_ratio':'cos','left_degrees':60,'right_ratio':'sin','right_degrees':30,'operation':'subtract','factor':4},
  {'left_ratio':'sin','left_degrees':30,'right_ratio':'cos','right_degrees':60,'operation':'add','factor':2},
  {'left_ratio':'tan','left_degrees':45,'right_ratio':'cot','right_degrees':45,'operation':'multiply','factor':-3},
  {'left_ratio':'cos','left_degrees':0,'right_ratio':'cos','right_degrees':60,'operation':'divide','factor':0},
 ],
}
REQUIRED_BRANCHES={
 'quadratic_reconstruct':{'positive_leading','negative_leading','repeated_roots','distinct_roots','zero_root'},
 'quadratic_shift_classify':{'two_distinct_real','repeated_real','no_real'},
 'ap_formula_recognition':{'constant_ap','nonconstant_ap','not_ap'},
 'ap_from_prefix_sums':{'positive_difference','negative_difference','zero_difference','fractional_parameters','increasing_prefix_counts','decreasing_prefix_counts'},
 'trig_similar_missing_side':{f'{angle}_{ratio}' for angle in ['D','F'] for ratio in RATIOS}|{'integer_missing_leg','irrational_missing_leg','fractional_scale'},
 'trig_degree_expression':set(OPERATIONS)|{'defined_zero','defined_nonzero','undefined_component','zero_divisor','zero_factor_defined','zero_factor_undefined','negative_factor','angle_0','angle_90'},
}


def validate(task,g):
    if task in {'quadratic_reconstruct','quadratic_shift_classify'} and g['leading']==0:raise MathInputError('Nonzero quadratic leading coefficient required')
    if task=='ap_from_prefix_sums':
        if g['m']==g['k']:raise MathInputError('Distinct positive prefix counts are required')
        if not all(exact(g[key]).is_Rational for key in ['sum_m','sum_k']):raise MathInputError('This task supports exact rational prefix totals')
    if task=='trig_similar_missing_side':
        if not 0<g['leg']<g['hypotenuse'] or exact(g['scale'])<=0:raise MathInputError('Positive nondegenerate right triangle and scale required')
        if g['reference'] not in {'D','F'} or g['ratio'] not in RATIOS:raise MathInputError('Invalid corresponding angle or ratio')
    if task=='trig_degree_expression':
        if g['left_ratio'] not in RATIOS or g['right_ratio'] not in RATIOS or g['operation'] not in OPERATIONS:raise MathInputError('Invalid compound trigonometric expression')
        if g['left_degrees'] not in ANGLES or g['right_degrees'] not in ANGLES:raise MathInputError('Standard degree angles required')


def _fraction(text):
    value=exact(text)
    return Fraction(int(value.p),int(value.q))


def recover_ap(g):
    left,right=_fraction(g['sum_m'])/g['m'],_fraction(g['sum_k'])/g['k']
    difference=2*(right-left)/(g['k']-g['m'])
    first=left-Fraction(g['m']-1,2)*difference
    return first,difference


def _special_ratio(name,degrees):
    # Coordinate definitions of the exact special triangles, rather than trig.
    coordinates={0:(sp.Integer(0),sp.Integer(1),sp.Integer(1)),30:(sp.Integer(1),sp.sqrt(3),sp.Integer(2)),
                 45:(sp.Integer(1),sp.Integer(1),sp.sqrt(2)),60:(sp.sqrt(3),sp.Integer(1),sp.Integer(2)),90:(sp.Integer(1),sp.Integer(0),sp.Integer(1))}
    o,a,h=coordinates[degrees]
    numerator,denominator={'sin':(o,h),'cos':(a,h),'tan':(o,a),'sec':(h,a),'csc':(h,o),'cot':(a,o)}[name]
    return None if denominator==0 else sp.simplify(numerator/denominator)


def expression(g,angle_unit='theta'):
    left=f"{g['left_ratio']}({g['left_degrees']}*{angle_unit})"
    right=f"{g['right_ratio']}({g['right_degrees']}*{angle_unit})"
    return f"({g['factor']})*(({left}){OPERATIONS[g['operation']]}({right}))"


def _defined(value):
    return {'kind':'defined_value','defined':value is not None,'value':canonical(value) if value is not None else None}


def primary(p):
    t,g=p['task_type'],p['givens']
    if t=='quadratic_reconstruct':
        a,r,s=g['leading'],g['root_one'],g['root_two']
        return {'kind':'coefficients','values':[canonical(a),canonical(-a*(r+s)),canonical(a*r*s)]}
    if t=='quadratic_shift_classify':
        ratio=Fraction(g['level'],g['leading'])
        return {'kind':'classification','value':'no_real' if ratio<0 else 'repeated_real' if ratio==0 else 'two_distinct_real'}
    if t=='ap_formula_recognition':return {'kind':'boolean','value':g['quadratic']==0}
    if t=='ap_from_prefix_sums':
        a,d=recover_ap(g)
        return scalar(a+(g['n']-1)*d)
    if t=='trig_similar_missing_side':
        o,a,h=sp.sqrt(g['hypotenuse']**2-g['leg']**2),sp.Integer(g['leg']),sp.Integer(g['hypotenuse'])
        if g['reference']=='F':o,a=a,o
        numerator,denominator={'sin':(o,h),'cos':(a,h),'tan':(o,a),'sec':(h,a),'csc':(h,o),'cot':(a,o)}[g['ratio']]
        return scalar(numerator/denominator)
    if t=='trig_degree_expression':
        a,b=_special_ratio(g['left_ratio'],g['left_degrees']),_special_ratio(g['right_ratio'],g['right_degrees'])
        if a is None or b is None or (g['operation']=='divide' and b==0):return _defined(None)
        value={'add':lambda:a+b,'subtract':lambda:a-b,'multiply':lambda:a*b,'divide':lambda:a/b}[g['operation']]()
        return _defined(g['factor']*value)
    raise MathInputError('Unknown assessment task')


def oracle(p):
    t,g=p['task_type'],p['givens']
    x=sp.Symbol('x',real=True)
    if t=='quadratic_reconstruct':
        # Recover unknown signed coefficients from root constraints. Coincident
        # roots require a zero derivative, not two copies of the same equation.
        b,c=sp.symbols('b c',real=True);a=g['leading'];r,s=g['root_one'],g['root_two']
        second=(2*a*r+b) if r==s else a*s*s+b*s+c
        result=sp.linsolve([a*r*r+b*r+c,second],(b,c))
        b_value,c_value=next(iter(result))
        return {'kind':'coefficients','values':[canonical(a),canonical(b_value),canonical(c_value)]}
    if t=='quadratic_shift_classify':
        roots=sp.solveset(g['leading']*(x-g['shift'])**2-g['level'],x,domain=sp.S.Reals)
        count=0 if roots is sp.S.EmptySet else len(roots)
        return {'kind':'classification','value':{0:'no_real',1:'repeated_real',2:'two_distinct_real'}[count]}
    if t=='ap_formula_recognition':
        n=sp.Symbol('n',integer=True);f=g['quadratic']*n*n+g['linear']*n+g['constant']
        second=sp.Poly(sp.expand(f.subs(n,n+2)-2*f.subs(n,n+1)+f),n)
        return {'kind':'boolean','value':bool(second.is_zero)}
    if t=='ap_from_prefix_sums':
        a,d=sp.symbols('a d',real=True);j=sp.Symbol('j',integer=True)
        constraints=[sp.summation(a+j*d,(j,0,g[count]-1))-exact(g[total]) for count,total in [('m','sum_m'),('k','sum_k')]]
        first,delta=next(iter(sp.linsolve(constraints,(a,d))))
        # The final term is reached by n-1 recurrence increments.
        return scalar(first+sp.summation(delta,(j,1,g['n']-1)))
    if t=='trig_similar_missing_side':
        scale=exact(g['scale']);adj=scale*g['leg'];hyp=scale*g['hypotenuse']
        angle=sp.acos(adj/hyp)
        if g['reference']=='F':angle=sp.pi/2-angle
        fn={'sin':sp.sin,'cos':sp.cos,'tan':sp.tan,'sec':sp.sec,'csc':sp.csc,'cot':sp.cot}[g['ratio']]
        return scalar(sp.trigsimp(fn(angle)))
    if t=='trig_degree_expression':
        try:return _defined(exact(expression(g),{'theta':sp.pi/180}))
        except UndefinedMath:return _defined(None)
    raise MathInputError('Unknown assessment oracle')


def prompt(p):
    t,g=p['task_type'],p['givens']
    if t=='quadratic_reconstruct':return f"A polynomial has nonzero leading coefficient {g['leading']} and roots {g['root_one']} and {g['root_two']}, counted with multiplicity. Construct its standard form and give its signed [x^2, x, constant] coefficients. Explain how the collected leading coefficient confirms its degree."
    if t=='quadratic_shift_classify':return f"For {g['leading']}*(x-({g['shift']}))^2={g['level']}, expand to check the signed discriminant, then classify the real roots as two_distinct_real, repeated_real or no_real."
    if t=='ap_formula_recognition':return f"For every positive integer n, a sequence is defined by a_n=({g['quadratic']})*n^2+({g['linear']})*n+({g['constant']}). Is it an AP? Justify using a difference formula valid for all n, or give a conflicting pair of differences."
    if t=='ap_from_prefix_sums':return f"A ledger's entries form an AP with unknown first entry and signed common difference. Its cumulative numerical totals are S_{g['m']}={g['sum_m']} and S_{g['k']}={g['sum_k']}. Find the individual entry a_{g['n']}. Explain how the two independent prefix constraints determine it; positions are one-based."
    if t=='trig_similar_missing_side':return f"Triangle ABC is right-angled at B, with AB={g['leg']} and hypotenuse AC={g['hypotenuse']}; BC is not supplied. Triangle DEF is similar, with D corresponding to A, E to B and F to C, and every side multiplied by {g['scale']}. Find {g['ratio']}({g['reference']}) exactly. Identify sides relative to that angle and show why the common positive scale leaves the ratio unchanged."
    if t=='trig_degree_expression':
        text=f"({g['factor']})*({g['left_ratio']}({g['left_degrees']} degrees) {OPERATIONS[g['operation']]} {g['right_ratio']}({g['right_degrees']} degrees))"
        return f"Evaluate the ORIGINAL expression {text} exactly, or state that it is undefined. Check each ratio and any division before multiplying, including when the outside factor is zero. The angles are in degrees."
    raise MathInputError('Unknown assessment prompt')


def generate(task,index,rng):
    if index<len(EDGE_GIVENS[task]):return dict(EDGE_GIVENS[task][index])
    if task=='quadratic_reconstruct':
        r=rng.randint(-40,40);s=r if index%4==0 else rng.randint(-40,40)
        return {'leading':rng.choice([-5,-2,-1,1,2,4]),'root_one':r,'root_two':s}
    if task=='quadratic_shift_classify':return {'leading':rng.choice([-4,-2,-1,1,3,5]),'shift':rng.randint(-50,50),'level':0 if index%3==0 else rng.randint(-75,75) or 1}
    if task=='ap_formula_recognition':return {'quadratic':0 if index%2==0 else rng.choice([-6,-2,-1,1,3,5]),'linear':0 if index%10==0 else rng.randint(-25,25),'constant':rng.randint(-50,50)}
    if task=='ap_from_prefix_sums':
        m,k=rng.sample(range(1,31),2);a,d=rng.randint(-35,40),rng.randint(-10,10)
        sm,sk=Fraction(m*(2*a+(m-1)*d),2),Fraction(k*(2*a+(k-1)*d),2)
        if index%4==0:sk+=Fraction(1,2)  # Also exercises noninteger recovered a,d.
        return {'m':m,'k':k,'n':rng.randint(1,45),'sum_m':str(sm),'sum_k':str(sk)}
    if task=='trig_similar_missing_side':
        if index%3==0:h=rng.randint(5,35);leg=rng.randint(1,h-1)
        else:
            m=rng.randint(2,12);n=rng.randint(1,m-1);leg,h=m*m-n*n,m*m+n*n
        return {'leg':leg,'hypotenuse':h,'scale':str(Fraction(rng.randint(1,12),rng.randint(1,5))),'reference':['D','F'][(index//6)%2],'ratio':RATIOS[index%6]}
    if task=='trig_degree_expression':
        return {'left_ratio':rng.choice(RATIOS),'right_ratio':rng.choice(RATIOS),'left_degrees':rng.choice(ANGLES),'right_degrees':rng.choice(ANGLES),
                'operation':list(OPERATIONS)[index%4],'factor':rng.randint(-5,8)}
    raise MathInputError('Unknown assessment generator')


def branch_features(p,answer):
    """Observable parameter/answer strata, not a claim of teaching validity."""
    t,g=p['task_type'],p['givens'];features=set()
    if t=='quadratic_reconstruct':
        features.add('positive_leading' if g['leading']>0 else 'negative_leading')
        features.add('repeated_roots' if g['root_one']==g['root_two'] else 'distinct_roots')
        if 0 in [g['root_one'],g['root_two']]:features.add('zero_root')
    elif t=='quadratic_shift_classify':features.add(answer['value'])
    elif t=='ap_formula_recognition':features.add('not_ap' if not answer['value'] else 'constant_ap' if g['linear']==0 else 'nonconstant_ap')
    elif t=='ap_from_prefix_sums':
        a,d=recover_ap(g)
        features.add('positive_difference' if d>0 else 'negative_difference' if d<0 else 'zero_difference')
        features.add('increasing_prefix_counts' if g['m']<g['k'] else 'decreasing_prefix_counts')
        if a.denominator>1 or d.denominator>1:features.add('fractional_parameters')
    elif t=='trig_similar_missing_side':
        features.add(g['reference']+'_'+g['ratio'])
        missing=sp.sqrt(g['hypotenuse']**2-g['leg']**2)
        features.add('integer_missing_leg' if missing.is_Integer else 'irrational_missing_leg')
        if not exact(g['scale']).is_Integer:features.add('fractional_scale')
    elif t=='trig_degree_expression':
        features.add(g['operation'])
        if answer['defined']:features.add('defined_zero' if exact(answer['value'])==0 else 'defined_nonzero')
        left,right=(_special_ratio(g[role+'_ratio'],g[role+'_degrees']) for role in ['left','right'])
        if left is None or right is None:features.add('undefined_component')
        if left is not None and right==0 and g['operation']=='divide':features.add('zero_divisor')
        if g['factor']==0:features.add('zero_factor_defined' if answer['defined'] else 'zero_factor_undefined')
        if g['factor']<0:features.add('negative_factor')
        for angle in [g['left_degrees'],g['right_degrees']]:features.add('angle_'+str(angle))
    return features


def related_polynomial(p):
    """Underlying monic equation for cross-fold leakage checks, where applicable."""
    t,g=p['task_type'],p['givens']
    if t=='quadratic_reconstruct':return [canonical(-(g['root_one']+g['root_two'])),canonical(g['root_one']*g['root_two'])]
    if t=='quadratic_shift_classify':return [canonical(-2*g['shift']),canonical(sp.Integer(g['shift'])**2-sp.Rational(g['level'],g['leading']))]
    return None


def worked_claims(p,answer):
    from .certificates import claim
    t,g=p['task_type'],p['givens'];steps=[];domain={'number_domain':'real','precision':'exact'}
    if t=='quadratic_reconstruct':
        a,b,c=answer['values'];r,s=g['root_one'],g['root_two']
        steps.append(claim('Construct the polynomial from its leading coefficient and root factors.',f"({g['leading']})*(x-({r}))*(x-({s}))",'eq',f'({a})*x**2+({b})*x+({c})',['x']))
        steps.append(claim('The collected leading coefficient is nonzero, so the degree is two.',a,'ne',0))
        for root in set([r,s]):steps.append(claim('Check the root constraints in the reconstructed polynomial.',f'({a})*({root})**2+({b})*({root})+({c})','eq',0))
        if r==s:steps.append(claim('A coincident root also makes the derivative vanish.',f'2*({a})*({r})+({b})','eq',0))
    elif t=='quadratic_shift_classify':
        a,b,c=g['leading'],-2*g['leading']*g['shift'],g['leading']*g['shift']**2-g['level'];d=b*b-4*a*c
        steps.append(claim('Collect the shifted-square equation into standard form.',f"({a})*(x-({g['shift']}))**2-({g['level']})",'eq',f'({a})*x**2+({b})*x+({c})',['x']))
        steps.append(claim('Calculate the discriminant from signed coefficients.',f'({b})**2-4*({a})*({c})','eq',d))
        steps.append(claim('Establish its sign before classifying real roots.',d,'lt' if d<0 else 'eq' if d==0 else 'gt',0))
    elif t=='ap_formula_recognition':
        q,b,c=g['quadratic'],g['linear'],g['constant']
        steps.append(claim('Calculate the difference for a general positive position.',f'({q})*(n+1)**2+({b})*(n+1)+({c})-(({q})*n**2+({b})*n+({c}))','eq',f'({2*q})*n+({q+b})',['n']))
        if q==0:steps.append(claim('The difference is constant for all positions.',f'({2*q})*n+({q+b})','eq',b,['n']))
        else:steps.append(claim('The differences at positions one and two disagree.',3*q+b,'ne',5*q+b))
    elif t=='ap_from_prefix_sums':
        first,delta=recover_ap(g);a,d=canonical(first),canonical(delta)
        steps.append(claim('Distinct positive prefix counts give an invertible two-equation system.',f"{g['m']}*{g['k']}*({g['k']}-{g['m']})/2",'ne',0))
        for count,total in [('m','sum_m'),('k','sum_k')]:
            n=g[count]
            steps.append(claim('Check the recovered AP against an original cumulative constraint.',f'{n}*(2*({a})+({n}-1)*({d}))/2','eq',g[total]))
        steps.append(claim('Recover a single entry using n minus one jumps, rather than returning a cumulative total.',f"({a})+({g['n']}-1)*({d})",'eq',answer['value']))
        domain['index_domain']='positive_integers'
    elif t=='trig_similar_missing_side':
        missing=canonical(sp.sqrt(g['hypotenuse']**2-g['leg']**2));scale=g['scale']
        steps.append(claim('Use Pythagoras to recover the missing original leg.',f"({missing})**2+{g['leg']}**2",'eq',g['hypotenuse']**2))
        steps.append(claim('A similarity scale must be positive.',scale,'gt',0))
        o,a,h=missing,str(g['leg']),str(g['hypotenuse'])
        if g['reference']=='F':o,a=a,o
        num,den={'sin':(o,h),'cos':(a,h),'tan':(o,a),'sec':(h,a),'csc':(h,o),'cot':(a,o)}[g['ratio']]
        steps.append(claim('Corresponding ratios cancel the same scale in numerator and denominator.',f'(({scale})*({num}))/(({scale})*({den}))','eq',f'({num})/({den})'))
        steps.append(claim('Use sides relative to the requested corresponding acute angle.',f'({num})/({den})','eq',answer['value']))
        domain['angle_domain']='acute'
    elif t=='trig_degree_expression':
        for role in ['left','right']:
            value=_special_ratio(g[role+'_ratio'],g[role+'_degrees'])
            steps.append({'description':'Check a component ratio with explicit degree conversion and its endpoint domain.',
                          'claim_type':'original_domain_evaluation','original_expression':g[role+'_ratio']+'(theta)',
                          'angle_degrees':g[role+'_degrees'],'defined':value is not None,'value':None if value is None else canonical(value)})
        steps.append({'description':'Set theta to one degree in radians, then evaluate the whole original compound expression before cancellation or zero multiplication.',
                      'claim_type':'original_domain_evaluation','original_expression':expression(g),'angle_degrees':1,
                      'defined':answer['defined'],'value':answer['value']})
        domain.update({'angle_unit_in_prompt':'degrees','original_domain_retained':True})
    else:raise MathInputError('Unknown assessment certificate')
    return domain,steps
