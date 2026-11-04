"""Bounded English side-label checks for registered right-triangle practice."""
import re
from fractions import Fraction


def check_labels(problem: dict, response: str) -> dict:
    if problem.get('task_type') != 'trig_triangle_ratio':
        return {'status':'unsupported'}
    if not isinstance(response,str) or len(response)>1000:
        return {'status':'clarify'}
    if re.search(r"\b(?:not|isn't|aren't|cannot|can't|don't|doesn't|either|or|false|wrong|incorrect|cm|mm|km|metres?|meters?)\b|[\^*]",response,re.I):
        return {'status':'clarify'}
    angle_pattern=r"\b(?:reference(?:\s+angle)?|angle|using|i\s+used)\s*(?:is|=|:)?\s*([A-Z])\b"
    angles=set(re.findall(angle_pattern,response,re.I))
    remainder=re.sub(angle_pattern,' ',response,flags=re.I)
    angles={a.upper() for a in angles}
    labels={}
    for name in ('opposite','adjacent','hypotenuse'):
        pattern=r'\b'+name+r"(?:\s+side)?\s*(?:is|=|:)?\s*([+-]?\d{1,5}(?:\s*/\s*\d{1,5})?)(?![\d/^*+\-]|\.\d)"
        raw=re.findall(pattern,response,re.I)
        remainder=re.sub(pattern,' ',remainder,flags=re.I)
        try:
            values={Fraction(x.replace(' ','')) for x in raw}
        except (ValueError,ZeroDivisionError):
            return {'status':'clarify'}
        if len(values)!=1 or next(iter(values))<=0:
            return {'status':'clarify'}
        labels[name]=next(iter(values))
    remainder=re.sub(r"\b(?:i think|i used|the|and|my)\b",' ',remainder,flags=re.I)
    if len(angles)!=1 or re.search(r"[^\s,;:.!?]",remainder):
        return {'status':'clarify'}
    givens=problem.get('givens') or {}
    if next(iter(angles)) != givens.get('reference'):
        return {'status':'reference_mismatch'}
    expected={name:givens[name] for name in labels}
    if givens['reference']=='C':
        expected['opposite'],expected['adjacent']=expected['adjacent'],expected['opposite']
    return {'status':'labels_correct' if all(labels[k]==expected[k] for k in labels) else 'labels_mismatch'}


def check_ratio_definition(problem: dict, response: str) -> dict:
    """Check an ordered pair of side names without evaluating their lengths."""
    if problem.get('task_type') != 'trig_triangle_ratio':
        return {'status':'unsupported'}
    if not isinstance(response,str) or len(response)>1000 or re.search(r"\b(?:not|isn't|aren't|cannot|can't|don't|doesn't|either|or|false|wrong|incorrect)\b",response,re.I):
        return {'status':'clarify'}
    pairs=re.findall(r'\b(opposite|adjacent|hypotenuse)(?:\s+side)?\s*(?:/|over|divided\s+by)\s*(?:the\s+)?(opposite|adjacent|hypotenuse)\b',response,re.I)
    if len(pairs)!=1:
        return {'status':'clarify'}
    aliases={'sin':'sin','sine':'sin','cos':'cos','cosine':'cos','tan':'tan','tangent':'tan','sec':'sec','secant':'sec','csc':'csc','cosecant':'csc','cosec':'csc','cot':'cot','cotangent':'cot'}
    named={aliases[x.lower()] for x in re.findall(r'\b(sin|sine|cos|cosine|tan|tangent|sec|secant|csc|cosec|cosecant|cot|cotangent)\b',response,re.I)}
    ratio=problem['givens'].get('ratio')
    if named and named!={ratio}:
        return {'status':'definition_mismatch'}
    definitions={'sin':('opposite','hypotenuse'),'cos':('adjacent','hypotenuse'),'tan':('opposite','adjacent'),
                 'sec':('hypotenuse','adjacent'),'csc':('hypotenuse','opposite'),'cot':('adjacent','opposite')}
    return {'status':'definition_correct' if tuple(x.lower() for x in pairs[0])==definitions.get(ratio) else 'definition_mismatch'}
