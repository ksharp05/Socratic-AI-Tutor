"""R3 review (C2): every branch of the "Check my step" feedback, without the private book corpus.

The beta-level step-feedback tests in tests_beta/test_beta.py are all marked local_corpus,
so GitHub CI never ran ratio_hint.py or the follow-up code in triangle_reasoning.py.
These tests use a synthetic right triangle, so CI runs them. See
Docs/m3/R3_C2_STEP_FEEDBACK_REVIEW.md.
"""
import random

import pytest

from socrates_beta.ratio_hint import HINT_TEXT, ratio_hint
from tutor.triangle_reasoning import (
    _RATIO_ROLES,
    ratio_followup_feedback,
    ratio_followup_question,
    ratio_step_feedback,
)

# Right angle at B. At C the opposite side is 144, the adjacent side 17, the hypotenuse 145,
# so sin C = 144/145 (the givens are stored from angle A, as in the registered items).
C_SIN = {'task_type': 'trig_triangle_ratio',
         'givens': {'opposite': 17, 'adjacent': 144, 'hypotenuse': 145, 'reference': 'C', 'ratio': 'sin'}}
A_TAN = {'task_type': 'trig_triangle_ratio',
         'givens': {'opposite': 3, 'adjacent': 4, 'hypotenuse': 5, 'reference': 'A', 'ratio': 'tan'}}


def _key(verdict, detail):
    """The HINT_TEXT key ratio_hint uses for a verdict."""
    if verdict == 'definition_mismatch' and detail != 'reversed_order':
        detail = 'mismatch_' + detail
    elif verdict == 'partial_correct':
        detail = 'partial_' + detail
    return detail.partition(':')[0]


# ---------------------------------------------------------------- the reply table

def test_every_reply_exists_in_all_three_languages():
    keys = {language: set(texts) for language, texts in HINT_TEXT.items()}
    assert set(keys) == {'en', 'hi', 'hinglish'}
    assert keys['en'] == keys['hi'] == keys['hinglish']


def test_no_reply_contains_a_number():
    # Replies are fixed sentences, so they cannot reveal a side length or the final ratio.
    for language, texts in HINT_TEXT.items():
        for key, text in texts.items():
            assert not any(char.isdigit() for char in text), (language, key)


# ---------------------------------------------------------------- first step: ratio_step_feedback

STEP_CASES = [
    # Side labels written before any ratio
    (C_SIN, 'angle C, opposite 144, adjacent 17, hypotenuse 145', ('definition_correct', 'setup_complete')),
    (C_SIN, 'angle C, opposite 144, adjacent 17', ('partial_correct', 'setup_hypotenuse')),
    (C_SIN, 'angle C, opposite 144', ('partial_correct', 'setup_remaining')),
    (C_SIN, 'angle C, opposite 144, adjacent 17, hypotenuse 17', ('definition_mismatch', 'setup_hypotenuse')),
    (C_SIN, 'angle C, opposite 17, adjacent 144, hypotenuse 145', ('definition_mismatch', 'setup_labels')),
    (C_SIN, 'angle A, opposite 144, adjacent 17, hypotenuse 145', ('definition_mismatch', 'setup_angle')),
    (C_SIN, 'opposite 144, adjacent 17', ('clarify', 'reference_angle')),
    (C_SIN, 'angle C, opposite 144 cm, adjacent 17 m', ('clarify', 'conflicting_labels')),
    # An ordered pair of side names
    (C_SIN, 'opposite/hypotenuse', ('definition_correct', 'order')),
    (C_SIN, 'sin c = opposite/hypotenuse', ('definition_correct', 'order')),
    (C_SIN, 'divide the opposite by the hypotenuse', ('definition_correct', 'order')),
    (C_SIN, 'hypotenuse/opposite', ('definition_mismatch', 'reversed_order')),
    (C_SIN, 'opposite/adjacent', ('definition_mismatch', 'denominator')),
    (C_SIN, 'adjacent/hypotenuse', ('definition_mismatch', 'numerator')),
    (C_SIN, 'adjacent/opposite', ('definition_mismatch', 'side_roles')),
    (C_SIN, 'cos c = adjacent/hypotenuse', ('definition_mismatch', 'target_ratio')),
    (C_SIN, 'sin a = opposite/hypotenuse', ('clarify', 'reference_angle')),
    (C_SIN, 'opposite/hypotenuse + 1', ('clarify', 'expression')),
    (C_SIN, 'opposite/opposite', ('clarify', 'side_roles')),
    (A_TAN, 'opposite/adjacent', ('definition_correct', 'order')),
    # One side in one position
    (C_SIN, 'opposite in the numerator', ('partial_correct', 'denominator')),
    (C_SIN, 'hypotenuse in the denominator', ('partial_correct', 'numerator')),
    (C_SIN, 'adjacent in the numerator', ('definition_mismatch', 'numerator')),
    (C_SIN, 'opposite in the denominator', ('definition_mismatch', 'denominator')),
    # Side names, then lengths
    (C_SIN, 'opposite/hypotenuse = 144/145', ('definition_correct', 'substitution')),
    (C_SIN, 'opposite/hypotenuse = 145/144', ('definition_mismatch', 'substitution_order')),
    (C_SIN, 'opposite/hypotenuse = 288/290', ('definition_correct', 'equivalent_fraction')),
    (C_SIN, 'opposite/hypotenuse = 17/145', ('definition_mismatch', 'substitution_numerator')),
    (C_SIN, 'opposite/hypotenuse = 144/17', ('definition_mismatch', 'substitution_denominator')),
    (C_SIN, 'opposite/hypotenuse = 5/7', ('definition_mismatch', 'substitution_values')),
    (C_SIN, 'opposite/hypotenuse = 144 cm/145 m', ('clarify', 'substitution_units')),
    (C_SIN, 'opposite/hypotenuse = x', ('clarify', 'substitution_fraction')),
    (C_SIN, 'opposite/hypotenuse = 0/145', ('clarify', 'substitution_fraction')),
    (C_SIN, 'cos c = opposite/hypotenuse = 144/145', ('definition_mismatch', 'target_ratio')),
    (C_SIN, 'opposite 144, hypotenuse 145, so 144/145', ('definition_correct', 'substitution')),
    (C_SIN, 'opposite 17, hypotenuse 145, so 17/145', ('clarify', 'exercise_lengths')),
    (A_TAN, 'tan a = opposite/adjacent = 3/4', ('definition_correct', 'substitution')),
    # The other acute angle: sin C = cos A, tan A = cot C
    (C_SIN, 'sin c = cos a', ('definition_correct', 'complementary_identity')),
    (C_SIN, 'sin c = sin a', ('definition_mismatch', 'complementary_identity')),
    (C_SIN, 'sin c = cos a = adjacent/hypotenuse', ('definition_correct', 'complementary_setup')),
    (C_SIN, 'cos a = adjacent/hypotenuse', ('definition_correct', 'complementary_setup')),
    (C_SIN, 'cos a = hypotenuse/adjacent', ('definition_mismatch', 'complementary_order')),
    (C_SIN, 'cos a = opposite/hypotenuse', ('definition_mismatch', 'complementary_sides')),
    (C_SIN, 'cos a = hypotenuse/adjacent = 145/144', ('definition_mismatch', 'complementary_order')),
    (C_SIN, 'cos a = opposite/hypotenuse = 17/145', ('definition_mismatch', 'complementary_sides')),
    (C_SIN, 'sin c = cos a = 144/145', ('clarify', 'complementary_work')),
    (C_SIN, 'sin c = cos a = something', ('clarify', 'expression')),
    (A_TAN, 'tan a = cot c', ('definition_correct', 'complementary_identity')),
    # Two fractions offered
    (C_SIN, 'should i use opposite/hypotenuse or adjacent/hypotenuse?', ('clarify', 'choose_numerator:hypotenuse')),
    (C_SIN, 'is it opposite/hypotenuse or opposite/adjacent?', ('clarify', 'choose_denominator:opposite')),
    (C_SIN, 'either opposite/hypotenuse or hypotenuse/adjacent', ('clarify', 'choose_fraction')),
    # Vertex labels (right angle at B, so at C: AB opposite, BC adjacent, AC hypotenuse)
    (C_SIN, 'ab/ac', ('definition_correct', 'order')),
    (C_SIN, 'bc/ac', ('definition_mismatch', 'numerator')),
    (C_SIN, 'right angle at a. ab/ac', ('clarify', 'diagram_angle')),
    (C_SIN, 'xy/ac', ('clarify', 'diagram_labels')),
    # Getting started, discouragement and stress
    (C_SIN, "i'm stuck", ('clarify', 'starting_angle')),
    (C_SIN, "i'm terrible at maths", ('clarify', 'discouraged_start')),
    (C_SIN, 'which side is opposite?', ('clarify', 'find_opposite')),
    (C_SIN, "i'm stressed about my exam", ('clarify', 'study_stress')),
    # A corrected step: only the correction counts, unless it hedges or drops an earlier angle or ratio
    (C_SIN, 'opposite/adjacent. correction: opposite/hypotenuse', ('definition_correct', 'order')),
    (C_SIN, 'opposite/adjacent. i meant: maybe opposite/hypotenuse', ('clarify', 'step')),
    (C_SIN, 'sin a = opposite/hypotenuse. correction: opposite/hypotenuse', ('clarify', 'reference_angle')),
    (C_SIN, 'cos c = adjacent/hypotenuse. correction: opposite/hypotenuse', ('clarify', 'target_ratio')),
    # Everything else
    (C_SIN, 'i only have 144 cm so far', ('clarify', 'length_side')),
    (C_SIN, 'i changed the angle but kept calling the same side opposite', ('definition_mismatch', 'relabel_angle')),
    (C_SIN, 'the opposite is the hypotenuse', ('clarify', 'conflicting_labels')),
    (C_SIN, 'tan c = opposite/adjacent', ('definition_mismatch', 'target_ratio')),
    (C_SIN, 'sin and cos', ('clarify', 'target_ratio')),
    (C_SIN, 'which angle?', ('clarify', 'reference_angle')),
    (C_SIN, 'not opposite/hypotenuse', ('clarify', 'step')),
    (C_SIN, 'sin compares the opposite with the hypotenuse', ('partial_correct', 'side_order')),
    (C_SIN, 'sin compares the opposite with the adjacent', ('definition_mismatch', 'side_roles')),
    (C_SIN, 'cos compares the adjacent with the hypotenuse', ('definition_mismatch', 'target_ratio')),
    (C_SIN, 'should i use the opposite side for sin?', ('partial_correct', 'other_side')),
    (C_SIN, 'should i use the adjacent side for sin?', ('definition_mismatch', 'side_roles')),
    (C_SIN, 'which side goes on top?', ('clarify', 'side_position')),
    (C_SIN, 'opposite', ('clarify', 'side_roles')),
    (C_SIN, 'opposite and hypotenuse instead', ('clarify', 'side_roles')),
    (C_SIN, 'opposite/hypotenuse =', ('clarify', 'substitution_fraction')),
    (C_SIN, 'hmm', ('clarify', 'step')),
    (C_SIN, '', ('clarify', 'step')),
    # Over 1,000 characters the step is not read at all, even when it holds a correct pair.
    (C_SIN, 'opposite/hypotenuse' + ' ' * 990, ('clarify', 'step')),
    (C_SIN, ('opposite/hypotenuse' + ' ' * 990)[:999], ('definition_correct', 'order')),
]


@pytest.mark.parametrize(('problem', 'text', 'verdict'), STEP_CASES, ids=[case[1][:50] for case in STEP_CASES])
def test_step_feedback_branch(problem, text, verdict):
    assert ratio_step_feedback(problem, text) == verdict
    # Every verdict has a reply in all three languages.
    assert _key(*verdict) in HINT_TEXT['en']


@pytest.mark.parametrize(('text', 'status'), [
    ('opposite/hypotenuse', 'definition_correct'),
    ('hypotenuse/opposite', 'definition_mismatch'),
    ('17/145', 'clarify'),
    ('opposite in the numerator', 'clarify'),
])
def test_graph_definition_check_reads_names_only(text, status):
    # The R3 graph's math-tools check_ratio_definition uses check_values=False: it never looks at lengths.
    from tutor.triangle_reasoning import check_ratio_definition
    assert check_ratio_definition(C_SIN, text) == {'status': status}


def test_unsupported_items_get_no_step_feedback():
    assert ratio_step_feedback({'task_type': 'quadratic'}, 'opposite/hypotenuse') == ('unsupported', 'exercise')
    assert ratio_step_feedback({'task_type': 'trig_triangle_ratio', 'givens': {}}, 'x') == ('unsupported', 'exercise')
    assert ratio_hint({'task_type': 'quadratic'}, 'opposite/hypotenuse') is None


# ---------------------------------------------------------------- short answers: ratio_followup_feedback

FOLLOWUP_CASES = [
    ('order', '144/145', ('definition_correct', 'substitution')),
    ('order', '145/144', ('definition_mismatch', 'substitution_order')),
    ('order', 'hello', None),
    ('mismatch_substitution_order', '144', ('partial_correct', 'substitution_numerator')),
    ('mismatch_substitution_order', '17', ('definition_mismatch', 'substitution_order')),
    ('mismatch_substitution_numerator', '144', ('definition_correct', 'substitution')),
    ('mismatch_substitution_denominator', '145', ('definition_correct', 'substitution')),
    ('mismatch_substitution_denominator', '144', ('definition_mismatch', 'substitution_denominator')),
    ('reference_angle', 'c', ('partial_correct', 'reference_angle')),
    ('reference_angle', 'angle a', ('definition_mismatch', 'setup_angle')),
    ('reference_angle', 'no idea', None),
    ('target_ratio', 'sin', ('partial_correct', 'target_ratio')),
    ('target_ratio', 'cos', ('definition_mismatch', 'target_ratio')),
    ('side_position', 'top', ('clarify', 'numerator')),
    ('side_position', 'neeche', ('clarify', 'denominator')),
    ('side_position', 'maybe', None),
    ('partial_setup_opposite:cm', '144 cm', ('definition_correct', 'setup_complete')),
    ('partial_setup_opposite:cm', '144 m', ('clarify', 'setup_opposite')),
    ('partial_setup_hypotenuse', '145', ('definition_correct', 'setup_complete')),
    ('partial_setup_adjacent', '144', ('clarify', 'setup_adjacent')),
    ('mismatch_side_roles', 'opposite and hypotenuse', ('partial_correct', 'side_order')),
    ('mismatch_side_roles', 'adjacent and hypotenuse', ('definition_mismatch', 'side_roles')),
    ('mismatch_side_roles', 'opposite (a) and hypotenuse', ('clarify', 'reference_angle')),
    ('mismatch_side_roles', 'ab and xy', ('clarify', 'diagram_labels')),
    ('mismatch_side_roles', 'xy and zz', None),
    ('partial_target_ratio', 'opposite', ('partial_correct', 'other_side')),
    ('partial_target_ratio', 'adjacent', ('definition_mismatch', 'side_roles')),
    ('length_side', 'opposite', ('clarify', 'length_other_side:opposite')),
    ('length_side', 'adjacent', ('clarify', 'length_ratio_sides')),
    ('length_side', 'xy', None),
    ('partial_other_side:opposite', 'hypotenuse', ('partial_correct', 'side_order')),
    ('partial_other_side:opposite', 'opposite', ('clarify', 'other_side')),
    ('choose_numerator:hypotenuse', 'opposite', ('definition_correct', 'order')),
    ('choose_numerator:hypotenuse', 'adjacent', ('definition_mismatch', 'numerator')),
    ('choose_numerator:hypotenuse', 'hypotenuse', ('clarify', 'choose_numerator:hypotenuse')),
    ('choose_denominator:opposite', 'hypotenuse', ('definition_correct', 'order')),
    ('mismatch_complementary_order', 'adjacent', ('definition_correct', 'complementary_setup')),
    ('mismatch_complementary_order', 'hypotenuse', ('clarify', 'retry_complementary_order')),
    # Vertex labels are read at the other acute angle (A) for this question.
    ('mismatch_complementary_order', 'ab', ('definition_correct', 'complementary_setup')),
    ('mismatch_complementary_order', 'bc', ('clarify', 'retry_complementary_order')),
    ('find_opposite', 'side xy', ('clarify', 'diagram_labels')),
    ('length_side', 'side xy', ('clarify', 'length_side')),
    ('choose_numerator:hypotenuse', 'side xy', ('clarify', 'choose_numerator:hypotenuse')),
    ('partial_numerator', 'opposite', ('definition_correct', 'order')),
    ('partial_numerator', 'adjacent', ('clarify', 'retry_numerator')),
    ('numerator', 'opposite', ('partial_correct', 'denominator')),
    ('denominator', 'hypotenuse', ('partial_correct', 'numerator')),
    ('partial_reference_angle', 'opposite', ('partial_correct', 'denominator')),
    ('find_opposite', 'ab', ('partial_correct', 'opposite_identified')),
    ('find_opposite', 'BC', ('clarify', 'find_opposite')),
    ('find_opposite', 'side AC', ('clarify', 'find_opposite')),
    ('find_opposite', 'xy', None),
    ('not_a_question', 'opposite', None),
]


@pytest.mark.parametrize(('question', 'text', 'verdict'), FOLLOWUP_CASES,
                         ids=[f'{case[0]}-{case[1]}' for case in FOLLOWUP_CASES])
def test_followup_branch(question, text, verdict):
    assert ratio_followup_feedback(C_SIN, text, question) == verdict
    if verdict:
        assert _key(*verdict) in HINT_TEXT['en']


NEXT_QUESTION_CASES = [
    ('starting_angle', '', 'reference_angle'),
    ('study_stress', '', 'reference_angle'),
    ('partial_opposite_identified', '', 'numerator'),
    ('length_other_side:opposite', '', 'partial_other_side:opposite'),
    ('find_opposite', '', 'find_opposite'),
    ('choose_numerator:hypotenuse', '', 'choose_numerator:hypotenuse'),
    ('side_roles', '17/145', 'fraction_side_roles'),
    ('side_roles', 'opposite something', None),
    ('partial_other_side', 'should i use the opposite side for sin?', 'partial_other_side:opposite'),
    ('partial_other_side', 'opposite and adjacent', None),
    ('partial_setup_hypotenuse', 'angle c, opposite 144 cm, adjacent 17 cm', 'partial_setup_hypotenuse:cm'),
    ('partial_setup_hypotenuse', 'angle c, opposite 144, adjacent 17', 'partial_setup_hypotenuse'),
    ('order', '', 'order'),
    ('mismatch_target_ratio', '', 'mismatch_target_ratio'),
    ('not_a_key', '', None),
]


@pytest.mark.parametrize(('key', 'text', 'question'), NEXT_QUESTION_CASES, ids=[case[0] for case in NEXT_QUESTION_CASES])
def test_next_question(key, text, question):
    assert ratio_followup_question(key, text) == question


# ---------------------------------------------------------------- ratio_hint: language and carrying the question

@pytest.mark.parametrize(('text', 'continuation', 'reply', 'next_question'), [
    ('सामने वाली भुजा को कर्ण से भाग', None, HINT_TEXT['hi']['order'], ('order', 'hi')),
    ('maine opposite/hypotenuse likha', None, HINT_TEXT['hinglish']['order'], ('order', 'hinglish')),
    ('opposite/hypotenuse', None, HINT_TEXT['en']['order'], ('order', 'en')),
    # A one-word English answer keeps the language of the earlier turn.
    ('adjacent', ('partial_numerator', 'hi'), HINT_TEXT['hi']['retry_numerator'], ('partial_numerator', 'hi')),
    ('adjacent', ('partial_numerator', 'hinglish'), HINT_TEXT['hinglish']['retry_numerator'],
     ('partial_numerator', 'hinglish')),
    # A retry keeps asking the same question; a correct answer moves on.
    ('opposite', ('partial_numerator', 'en'), HINT_TEXT['en']['order'], ('order', 'en')),
    # An answer the question cannot read falls back to ordinary step feedback.
    ('xy', ('mismatch_side_roles', 'en'), HINT_TEXT['en']['step'], None),
])
def test_ratio_hint_language_and_next_question(text, continuation, reply, next_question):
    assert ratio_hint(C_SIN, text, continuation) == (reply, next_question)


def test_diagram_label_followup_keeps_the_question():
    reply, next_question = ratio_hint(C_SIN, 'ab and xy', ('mismatch_side_roles', 'en'))
    assert reply == HINT_TEXT['en']['diagram_labels'] and next_question == ('mismatch_side_roles', 'en')


# ---------------------------------------------------------------- robustness

def test_random_steps_never_crash_and_always_use_a_known_reply():
    words = ['sin', 'cos', 'tan', 'cot', 'opposite', 'adjacent', 'hypotenuse', 'side', 'over', '/', '=', 'and', 'or',
             'not', 'angle', 'a', 'c', 'b', '(c)', 'ab', 'bc', 'ac', '17', '144', '145', 'cm', 'm', 'correction:',
             'numerator', 'denominator', 'upar', 'neeche', 'कर्ण', 'नहीं', '?', '.', 'which side', 'should i use', 'x']
    problems = [C_SIN, A_TAN, {'task_type': 'trig_triangle_ratio', 'givens': {'ratio': 'cos'}}]
    questions = [None, *sorted(HINT_TEXT['en']), 'partial_other_side:opposite', 'choose_numerator:hypotenuse']
    replies = {text for texts in HINT_TEXT.values() for text in texts.values()}
    rng = random.Random(13)
    for _ in range(3000):
        text = ' '.join(rng.choice(words) for _ in range(rng.randint(1, 8)))
        question = rng.choice(questions)
        out = ratio_hint(rng.choice(problems), text, (question, 'en') if question else None)
        assert out is not None
        reply, next_question = out
        assert reply in replies
        assert next_question is None or (isinstance(next_question[0], str) and next_question[1] in HINT_TEXT)


@pytest.mark.parametrize('text', ['opposite ' * 120, 'sin c = opposite / ' * 50, '( ' * 499, 'ab bc ac ' * 55])
def test_long_steps_return_quickly(text):
    import time
    start = time.perf_counter()
    assert ratio_hint(C_SIN, text[:512]) is not None
    assert time.perf_counter() - start < 0.5


def test_every_ratio_has_side_roles():
    assert set(_RATIO_ROLES) == {'sin', 'cos', 'tan', 'sec', 'csc', 'cot'}


# ---------------------------------------------------------------- found in review (strict xfail: flips to a failure once fixed)

@pytest.mark.xfail(strict=True, reason='R3 review C2-2: a full positional pair is read only when a ratio is named')
def test_positional_pair_without_a_ratio_name_is_understood():
    # Today this asks "Which side did you put on top, and which side underneath?",
    # the question the learner has just answered.
    assert ratio_step_feedback(C_SIN, 'I put opposite on top and hypotenuse on the bottom') == ('definition_correct', 'order')


@pytest.mark.xfail(strict=True, reason='R3 review C2-3: Hinglish without the cue words gets an English reply')
def test_hinglish_step_without_cue_words_gets_a_hinglish_reply():
    reply, _ = ratio_hint(C_SIN, 'opposite ko hypotenuse se divide kiya')
    assert reply == HINT_TEXT['hinglish']['order']
