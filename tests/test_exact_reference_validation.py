"""Published-maths checker: independent implementation, catalogue coverage and adversarial keys."""
import ast,copy
from pathlib import Path
import pytest
from tutor_validation import exact_reference as reference
from tutor.question_catalog import graph_items,allowed
from tutor import mathcore

ITEMS=[item for item in graph_items() if allowed(item,"practice")]
@pytest.mark.parametrize("item",ITEMS,ids=lambda i:i["question_id"])
def test_every_public_practice_key_and_a_wrong_key_are_checked(item):
    answer=mathcore.compute_key(item["problem"])["key"]
    assert reference.validate(item["problem"],answer)["status"]=="verified"
    bad=copy.deepcopy(answer)
    if bad["kind"]=="scalar":bad["value"]="("+bad["value"]+")+1"
    elif bad["values"]:bad["values"][0]="("+bad["values"][0]+")+1"
    else:bad["values"]=["123"]
    assert reference.validate(item["problem"],bad)["status"]=="failed"

def problem(task,givens):
    return {"task_type":task,"givens":givens,"number_domain":"real","answer_precision":"exact"}
@pytest.mark.parametrize("givens,values",[
    ({"a":2,"b":4,"c":-6},["-3","1"]),
    ({"a":3,"b":-18,"c":27},["3"]),
    ({"a":1,"b":5,"c":9},[]),
    ({"a":1,"b":0,"c":-2},["-sqrt(2)","sqrt(2)"]),
    ({"a":2,"b":3,"c":-1},["(-3-sqrt(17))/4","(-3+sqrt(17))/4"]),
])
def test_distinct_repeated_nonreal_and_irrational_roots(givens,values):
    p=problem("quadratic_solve",givens)
    assert reference.validate(p,{"kind":"finite_set","values":values})["status"]=="verified"
    if len(values)==2:
        assert reference.validate(p,{"kind":"finite_set","values":values[:1]})["status"]=="failed"
def test_negative_progression_and_nonintegral_count():
    assert reference.validate(problem("ap_count",{"a":10,"d":-3,"last":-2}),{"kind":"finite_set","values":["5"],"unit":"terms"})["status"]=="verified"
    assert reference.validate(problem("ap_count",{"a":2,"d":4,"last":12}),{"kind":"finite_set","values":[],"unit":"terms"})["status"]=="verified"
def test_units_and_shapes_cannot_pass_on_numeric_coincidence():
    p=problem("ap_term",{"a":7,"d":0,"n":5})
    assert reference.validate(p,{"kind":"scalar","value":"7","unit":"radians"})["status"]=="failed"
    q=problem("ap_count",{"a":2,"d":2,"last":6})
    assert reference.validate(q,{"kind":"finite_set","values":"3","unit":"terms"})["status"]=="failed"
    assert reference.validate(q,None)["status"]=="failed"
def test_untrusted_expression_is_never_executed(tmp_path):
    sentinel=tmp_path/"must_not_exist"
    with pytest.raises(ValueError):reference.parse("__import__('pathlib').Path("+repr(str(sentinel))+").touch()")
    assert not sentinel.exists()
def test_expression_growth_and_unbounded_iteration_fail_closed():
    expression="2"
    for _ in range(25):expression="("+expression+")**2"
    with pytest.raises(ValueError):reference.parse(expression)
    assert reference.validate(problem("ap_sum",{"a":1,"d":1,"n":10001}),{"kind":"scalar","value":"50015001"})["status"]=="failed"
def test_checker_does_not_import_the_runtime_or_its_solver():
    tree=ast.parse(Path(reference.__file__).read_text(encoding="utf-8"))
    imports=[n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
    assert not any(name.startswith(("tutor","socratic_data","sympy","numpy")) for name in imports)



@pytest.mark.parametrize("task,givens,answer", [
    ("ap_term", {"a":3,"d":-2,"n":4}, {"kind":"scalar","value":"-3"}),
    ("ap_sum", {"a":3,"d":-2,"n":4}, {"kind":"scalar","value":"0"}),
    ("ap_first", {"term":-1,"d":-2,"n":5}, {"kind":"scalar","value":"7"}),
    ("ap_difference", {"m":5,"n":2,"term_m":-3,"term_n":6}, {"kind":"scalar","value":"-3"}),
    ("ap_count", {"a":2,"d":2,"last":8}, {"kind":"finite_set","values":["4"],"unit":"terms"}),
    ("ap_mean", {"left":-3,"right":8}, {"kind":"scalar","value":"5/2"}),
    ("ap_ledger_term", {"n":5,"prefix_sum":"29","previous_sum":"17"}, {"kind":"scalar","value":"12"}),
    ("trig_triangle_ratio", {"opposite":3,"adjacent":4,"hypotenuse":5,"reference":"C","ratio":"tan"}, {"kind":"scalar","value":"4/3"}),
])
def test_known_answers_without_using_the_runtime_solver(task,givens,answer):
    assert reference.validate(problem(task,givens),answer)["status"]=="verified"

@pytest.mark.parametrize("prefix", [0.5, True, "1"*201, "1e10000", "1e9999999999999", "1/0"])
def test_ledger_input_requires_bounded_exact_data(prefix):
    p=problem("ap_ledger_term",{"n":2,"prefix_sum":prefix,"previous_sum":"0"})
    assert reference.validate(p,{"kind":"scalar","value":"1/2"})["status"]=="failed"
