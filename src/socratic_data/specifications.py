"""Closed schemas: unknown fields, bool-as-int and incomplete givens fail."""
from .math_kernel import MathInputError, exact
from .assessment_tasks import FIELDS as ASSESSMENT_FIELDS

FIELDS={
 "quadratic_solve":{"a":"int","b":"int","c":"int"},
 "quadratic_classify":{"a":"int","b":"int","c":"int"},
 "quadratic_check_claim":{"a":"int","b":"int","c":"int","claimed_roots":"expressions"},
 "quadratic_coefficients":dict.fromkeys(["p","q","r","s","t"],"int"),
 "quadratic_degree":dict.fromkeys(["p","q","r","s","t"],"int"),
 "quadratic_parameter_repeated":{"c":"int"},
 "quadratic_rectangle":{"area":"int","gap":"int"},
 "quadratic_under_specified_rectangle":{"area":"int"},
 "quadratic_speed":dict.fromkeys(["distance","reduction","delay"],"exact"),
 "ap_term":{"a":"int","d":"int","n":"position"},
 "ap_sum":{"a":"int","d":"int","n":"position"},
 "ap_membership":{"a":"int","d":"int","value":"int"},
 "ap_difference":{"m":"position","n":"position","term_m":"int","term_n":"int"},
 "ap_first":{"d":"int","n":"position","term":"int"},
 "ap_count":{"a":"int","d":"int","last":"int"},
 "ap_inverse_sum":{"a":"int","d":"int","total":"exact"},
 "ap_recognition":{"terms":"integers"},
 "ap_mean":{"left":"int","right":"int"},
 "ap_ledger_term":{"n":"position","previous_sum":"exact","prefix_sum":"exact"},
 "trig_triangle_ratio":{"opposite":"int","adjacent":"int","hypotenuse":"int","reference":"text","ratio":"text"},
 "trig_scaled_triangle":{"opposite":"int","adjacent":"int","hypotenuse":"int","reference":"text","ratio":"text","scale":"int"},
 "trig_standard_value":{"ratio":"text","angle_degrees":"int"},
 "trig_from_ratio":{"given_ratio":"text","given_value":"exact","target_ratio":"text"},
 "trig_identity_value":{"identity_id":"text","factor":"int"},
 "trig_identity_truth":{"identity_id":"text"},
 "trig_square_value":{"ratio":"text","angle_degrees":"int","factor":"int"},
 "trig_domain":{"expression_id":"text","angle_degrees":"int"},
}
FIELDS.update(ASSESSMENT_FIELDS)
OPTIONAL_FIELDS={task:{'coefficient':'int'} for task in ['trig_standard_value','trig_domain']}


def structural_validate(p,concepts):
    if not isinstance(p,dict) or set(p)!={"task_type","givens","number_domain","answer_precision","concept_ids","class","language"}:
        raise MathInputError("Incomplete/unknown problem fields")
    task=p["task_type"]
    if not isinstance(task,str) or task not in FIELDS:raise MathInputError("Unknown task")
    if type(p["class"]) is not int or p["class"]!=10 or p["language"]!="en" or p["concept_ids"]!=concepts[task]:
        raise MathInputError("Curriculum metadata mismatch")
    g=p["givens"]
    optional=OPTIONAL_FIELDS.get(task,{})
    if not isinstance(g,dict) or not set(FIELDS[task])<=set(g) or not set(g)<=set(FIELDS[task])|set(optional):raise MathInputError("Incomplete/unknown givens")
    admitted={**FIELDS[task],**{k:v for k,v in optional.items() if k in g}}
    for name,kind in admitted.items():
        value=g[name]
        if kind in {"int","position"}:
            if type(value) is not int or abs(value)>10**12 or (kind=="position" and not 1<=value<=10**7):
                raise MathInputError("Integer/domain/resource limit violated")
        elif kind=="exact":
            if not isinstance(value,str):raise MathInputError("Exact given must be a string")
            v=exact(value)
            if v.free_symbols or abs(v)>10**12:raise MathInputError("Exact given exceeds domain/resource limit")
        elif kind=="text":
            if not isinstance(value,str) or len(value)>64:raise MathInputError("Invalid enum text")
        elif kind in {"integers","expressions"}:
            if not isinstance(value,list) or len(value)>8:raise MathInputError("Invalid bounded primitive list")
            for item in value:
                if kind=="integers" and (type(item) is not int or abs(item)>10**12):raise MathInputError("Invalid integer observation")
                if kind=="expressions":exact(item)


def problem_schema(concepts):
    primitives={"int":{"type":"integer","minimum":-10**12,"maximum":10**12},
                "position":{"type":"integer","minimum":1,"maximum":10**7},
                "text":{"type":"string","maxLength":64},"exact":{"type":"string","maxLength":512},
                "integers":{"type":"array","minItems":3,"maxItems":8,"items":{"type":"integer"}},
                "expressions":{"type":"array","maxItems":8,"items":{"type":["string","integer"]}}}
    variants=[]
    for task,fields in FIELDS.items():
        properties={"task_type":{"const":task},"givens":{"type":"object","additionalProperties":False,"required":list(fields),"properties":{n:primitives[t] for n,t in {**fields,**OPTIONAL_FIELDS.get(task,{})}.items()}},
                    "number_domain":{"const":"real"},"answer_precision":{"const":"exact"},"concept_ids":{"const":concepts[task]},"class":{"const":10},"language":{"const":"en"}}
        variants.append({"type":"object","additionalProperties":False,"required":list(properties),"properties":properties})
    return {"$schema":"https://json-schema.org/draft/2020-12/schema","oneOf":variants}


def answer_schema():
    """Structural schema; exact parser and domain/unit checks remain mandatory."""
    number={'type':['string','integer'],'maxLength':512}
    unit={'type':['string','null'],'maxLength':64}
    variants=[]
    def add(kind,properties,required):
        variants.append({'type':'object','additionalProperties':False,'properties':{'kind':{'const':kind},**properties},'required':['kind',*required]})
    add('scalar',{'value':number,'unit':unit},['value'])
    add('finite_set',{'values':{'type':'array','maxItems':8,'items':number},'unit':unit},['values'])
    add('coefficients',{'values':{'type':'array','minItems':3,'maxItems':3,'items':number}},['values'])
    add('classification',{'value':{'type':'string','pattern':'^[a-z][a-z_]{0,60}$'}},['value'])
    add('boolean',{'value':{'type':'boolean'}},['value'])
    for defined in [False,True]:
        add('defined_value',{'defined':{'const':defined},'value':number if defined else {'type':'null'}},['defined','value'])
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:socratic:typed-answer:1',
            'description':'Structural validation only; semantic exact arithmetic, units and distinctness require the grader.', 'oneOf':variants}


def grade_result_schema():
    variants=[]
    for status,correct,scorable in [('correct',True,True),('incorrect',False,True),('invalid_response',False,False),('unverified',None,False)]:
        fields={'status':{'const':status},'correct':{'const':correct},'scorable':{'const':scorable},
                'reason':{'type':'string','maxLength':512},'reasoning_evaluated':{'const':False}}
        variants.append({'type':'object','additionalProperties':False,'required':list(fields),'properties':fields})
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:socratic:grade-result:2','oneOf':variants}
