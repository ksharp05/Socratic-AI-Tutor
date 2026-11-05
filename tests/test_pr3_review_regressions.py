"""Review-only edge cases that should pass before merging PR3. No model calls."""
from tutor.app import TutorApp
from tutor import mathcore


def test_generated_probe_cannot_introduce_number_words():
    student='I divided both sides by x and lost a root'
    assert TutorApp._safe_question(None,'Could the missing root be zero?',student) is None


def test_citation_cleanup_preserves_mathematical_brackets():
    result=TutorApp._real_citations(TutorApp,'Which values belong to [0, 1]?', [{'passage_id':'normalized:qe04'}])
    assert '[0, 1]' in result


def test_unsigned_coefficient_rule_does_not_trigger_when_b_is_already_positive():
    problem={'task_type':'quadratic_solve','givens':{'a':1,'b':7,'c':10}}
    key={'kind':'finite_set','values':['-2','-5']}
    answer={'kind':'finite_set','values':['2','5']}
    diagnoses=mathcore.diagnose_response(problem,key,answer)
    assert 'qe_m02' not in [d['misconception_id'] for d in diagnoses]
