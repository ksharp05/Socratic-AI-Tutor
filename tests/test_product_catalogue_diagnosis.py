"""Development checks from public catalogue examples and independently calculated givens.

These AI-authored regression cases are neither human review nor independent final
assessment. No simulator rules, learner states or held-out files are imported.
"""
import json
from pathlib import Path

import pytest

from tutor import diagnosis_evidence, mathcore, topic_sources
from tutor.app import TutorApp
from tutor.seed import seed_learner
from tutor_eval.single_agent import SingleAgentTutor

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = [json.loads(line) for line in (ROOT / 'content/dataset-v0.10.0/practice_questions.jsonl').read_text(encoding='utf-8-sig').splitlines()]
CATALOGUE = {r['misconception_id']: r for r in map(json.loads, (ROOT / 'content/dataset-v0.10.0/misconceptions.jsonl').read_text(encoding='utf-8-sig').splitlines())}


def problem(task, givens):
    template = next(r['problem'] for r in PUBLIC if r['problem']['task_type'] == task)
    return {**template, 'givens': givens}


@pytest.mark.parametrize(('task', 'givens', 'wrong', 'expected'), [
    ('ap_term', {'a': 5, 'd': 3, 'n': 4}, '17', {'ap_m03'}),
    ('ap_term', {'a': 5, 'd': 3, 'n': 4}, '38', {'ap_m04'}),
    ('ap_sum', {'a': 5, 'd': 3, 'n': 4}, '14', {'ap_m04'}),
    ('ap_sum', {'a': 5, 'd': 3, 'n': 4}, '44', {'ap_m03'}),
    ('ap_first', {'term': 2, 'd': -3, 'n': 5}, '17', {'ap_m03'}),
    ('ap_difference', {'m': 2, 'n': 6, 'term_m': 7, 'term_n': 19}, '-3', {'ap_m02'}),
    ('ap_difference', {'m': 2, 'n': 6, 'term_m': 7, 'term_n': 19}, '12', {'ap_m07'}),
    ('ap_count', {'a': 2, 'd': 3, 'last': 14}, '4', {'ap_m08'}),
    ('ap_count', {'a': 2, 'd': 3, 'last': 12}, '13/3', {'ap_m06'}),
    ('ap_mean', {'left': 2, 'right': 8}, '4', {'ap_m09'}),
    ('ap_ledger_term', {'n': 5, 'prefix_sum': '35', 'previous_sum': '21'}, '35', {'ap_m04'}),
    ('ap_term', {'a': 0, 'd': 4, 'n': 3}, '12', {'ap_m03', 'ap_m04'}),
])
def test_exact_ap_error_patterns_keep_all_possible_causes(task, givens, wrong, expected):
    p = problem(task, givens)
    key = mathcore.compute_key(p)
    assert key['verified']
    typed = {'kind': 'finite_set', 'values': [wrong]} if key['key']['kind'] == 'finite_set' else {'kind': 'scalar', 'value': wrong}
    got = mathcore.diagnose_response(p, key['key'], typed)
    assert {row['misconception_id'] for row in got} == expected


def test_all_public_ap_correct_answers_have_no_error_hypothesis():
    examples = [r['problem'] for r in PUBLIC if r['problem']['task_type'].startswith('ap_')]
    assert len(examples) >= 50
    for p in examples:
        answer = mathcore.compute_key(p)
        assert answer['verified']
        assert mathcore.diagnose_response(p, answer['key'], answer['key']) == []


@pytest.mark.parametrize('wrong', ['17/19', '-191', 'sqrt(19)'])
def test_unrelated_wrong_answer_is_not_diagnosed(wrong):
    p = problem('ap_term', {'a': 5, 'd': 3, 'n': 4})
    assert mathcore.diagnose_response(p, {'kind': 'scalar', 'value': '14'}, {'kind': 'scalar', 'value': wrong}) == []


def test_ap_trig_catalogue_registration_preserves_pending_review_fields():
    rows = {r['misconception_id']: r for r in topic_sources.misconceptions()}
    for mid, row in CATALOGUE.items():
        if row['chapter'] in ('arithmetic_progressions', 'trigonometry'):
            assert rows[mid] == row
            assert row['approved_for_teaching'] is False and row['review_status'] == 'pending_human_review'
    assert len(rows) == len(set(rows))


@pytest.mark.parametrize(('chapter', 'statement', 'expected'), [
    ('arithmetic_progressions', 'I say this is an AP because every term doubles.', 'ap_m01'),
    ('arithmetic_progressions', 'The common difference is the first term minus the second.', 'ap_m02'),
    ('arithmetic_progressions', 'For the nth term I use a+n*d.', 'ap_m03'),
    ('arithmetic_progressions', 'The total is the last deposit only.', 'ap_m04'),
    ('arithmetic_progressions', 'An AP must always increase.', 'ap_m05'),
    ('arithmetic_progressions', 'A fractional term position is valid.', 'ap_m06'),
    ('arithmetic_progressions', 'I ignore the index gap when finding the difference.', 'ap_m07'),
    ('arithmetic_progressions', 'The number of terms is end minus start.', 'ap_m08'),
    ('arithmetic_progressions', 'In an AP the middle value is the geometric mean.', 'ap_m09'),
    ('arithmetic_progressions', 'This familiar pattern must be AP.', 'ap_m10'),
    ('trigonometry', 'The same side is opposite for both acute angles.', 'tr_m01'),
    ('trigonometry', 'Sine is adjacent over hypotenuse.', 'tr_m02'),
    ('trigonometry', 'Cosine is the reciprocal of sine.', 'tr_m03'),
    ('trigonometry', 'Tangent is cosine divided by sine.', 'tr_m04'),
    ('trigonometry', 'sin^2(theta) is sin(theta^2).', 'tr_m05'),
    ('trigonometry', 'I pass degrees unchanged to a radians function.', 'tr_m06'),
    ('trigonometry', 'A denominator zero gives zero.', 'tr_m07'),
    ('trigonometry', 'All sides are doubled and sine is also doubled.', 'tr_m08'),
    ('trigonometry', 'The squared sum has no cross term.', 'tr_m09'),
    ('trigonometry', 'It works at one angle, which proves it for every angle.', 'tr_m10'),
])
def test_explicit_public_claims_offer_the_relevant_probe(chapter, statement, expected):
    assert expected in diagnosis_evidence.candidates(statement, chapter, set(CATALOGUE))


@pytest.mark.parametrize(('chapter', 'statement'), [
    ('arithmetic_progressions', 'What is a common difference?'),
    ('arithmetic_progressions', 'An AP need not always increase.'),
    ('arithmetic_progressions', 'An AP does not always increase.'),
    ('arithmetic_progressions', 'The common difference is the second term minus the first.'),
    ('arithmetic_progressions', 'The nth term is a+(n-1)*d.'),
    ('arithmetic_progressions', 'The number of terms is end minus start plus one.'),
    ('arithmetic_progressions', 'The number of terms is end minus start + 1.'),
    ('arithmetic_progressions', 'An AP can have a constant value or decrease.'),
    ('arithmetic_progressions', 'a_5-a_4 is one jump.'),
    ('arithmetic_progressions', 'I thought an AP must increase, but now I understand decreasing APs.'),
    ('arithmetic_progressions', 'Do not believe an AP must always increase.'),
    ('trigonometry', 'Sine is opposite over hypotenuse.'),
    ('trigonometry', 'Cosine is not the reciprocal of sine.'),
    ('trigonometry', 'Is cosine the reciprocal of sine?'),
    ('trigonometry', 'Opposite and adjacent change with the reference angle.'),
    ('trigonometry', 'Both sides scale together, so sine stays unchanged.'),
])
def test_correct_statements_and_questions_are_not_labelled(chapter, statement):
    assert diagnosis_evidence.candidates(statement, chapter, set(CATALOGUE)) == []


@pytest.mark.parametrize('app_type', [TutorApp, SingleAgentTutor])
@pytest.mark.parametrize(('chapter', 'claim', 'mid'), [
    ('arithmetic_progressions', 'I think an AP must always increase.', 'ap_m05'),
    ('trigonometry', 'Cosine is the reciprocal of sine.', 'tr_m03'),
])
def test_real_chapter_journey_keeps_text_hypothesis_suspected_and_followup_relevant(tmp_path, app_type, chapter, claim, mid):
    app = app_type(llm_mode='stub', db_name=str(tmp_path/'db.sqlite'), checkpoint_name=str(tmp_path/'checks.sqlite'))
    seed_learner(app.conn, 'public-case', {'alias': 'Synthetic regression'})
    try:
        first = app.turn('public-dialogue', 'public-case', claim, chapter=chapter)
        assert first['route'] == 'diagnose'
        assert first['diagnosis']['misconception_id'] == mid
        for _ in range(2):
            follow = app.turn('public-dialogue', 'public-case', 'Please explain that step.', chapter=chapter)
            assert 'factor zero' not in follow['reply'] and 'original equation' not in follow['reply']
            assert follow['reply'].count('?') == 1 and follow['checks']['ok']
        status = app.conn.execute('SELECT status FROM misconceptions WHERE learner_id=? AND misconception_id=?', ('public-case', mid)).fetchone()[0]
        assert status == 'suspected'
        assert app.conn.execute('SELECT count(*) FROM mastery WHERE learner_id=?', ('public-case',)).fetchone()[0] == 0
    finally:
        app.close()


@pytest.mark.parametrize('question', ['What is a coefficient?', 'What is a square root?', 'How do I read plus-minus notation?'])
def test_generic_quadratic_question_does_not_record_an_error(app, question):
    assert app._keyword_candidates(question) == []


def test_ap_count_empty_answer_uses_count_language():
    key = {'kind': 'finite_set', 'values': [], 'unit': 'terms'}
    parsed = mathcore.parse_answer('no valid term count', key)
    assert parsed['ok'] and mathcore.grade(parsed['typed'], key)['correct']
    assert parsed['display'] == 'no positive integer term count'


@pytest.mark.parametrize(('statement', 'expected'), [
    ('a_11-a_4 is one jump.', ['ap_m07']),
    ('a_5-a_4 is one jump.', []),
    ('Positions 3 through 9 contain six terms.', ['ap_m08']),
    ('Positions 3 through 9 contain seven terms.', []),
])
def test_index_evidence_checks_counts_instead_of_memorizing_one_example(statement, expected):
    assert diagnosis_evidence.candidates(statement, 'arithmetic_progressions', set(CATALOGUE)) == expected


@pytest.mark.parametrize(('chapter', 'claim', 'correction'), [
    ('arithmetic_progressions', 'I think an AP must always increase.', 'An AP can decrease or be constant.'),
    ('trigonometry', 'Cosine is the reciprocal of sine.', 'The reciprocal of sine is cosecant.'),
])
def test_explicit_self_correction_exits_the_probe_loop_without_awarding_mastery(tmp_path, chapter, claim, correction):
    app = TutorApp(llm_mode='stub', db_name=str(tmp_path/'db.sqlite'), checkpoint_name=str(tmp_path/'checks.sqlite'))
    seed_learner(app.conn, 'self-correction', {'alias': 'Synthetic regression'})
    try:
        assert app.turn('corrected', 'self-correction', claim, chapter=chapter)['route'] == 'diagnose'
        answer = app.turn('corrected', 'self-correction', correction, chapter=chapter)
        assert answer['diagnosis'] is None
        assert 'identified the distinction' in answer['reply'] and 'practice' in answer['reply']
        assert app.graph.get_state({'configurable': {'thread_id': 'corrected'}}).values['focus_misconception'] is None
        assert app.conn.execute('SELECT count(*) FROM mastery').fetchone()[0] == 0
        assert {r[0] for r in app.conn.execute('SELECT status FROM misconceptions')} == {'suspected'}
    finally:
        app.close()


@pytest.mark.parametrize('app_type', [TutorApp, SingleAgentTutor])
def test_checked_public_ap_attempt_gives_a_specific_probe_and_stays_suspected(tmp_path, app_type):
    from tutor.question_catalog import graph_items, allowed
    item = next(i for i in graph_items() if allowed(i, 'practice') and i['problem']['task_type'] == 'ap_term'
                and i['problem']['givens']['n'] > 2 and i['problem']['givens']['a'] != 0
                and i['problem']['givens']['d'] != 0)
    app = app_type(llm_mode='stub', db_name=str(tmp_path/'db.sqlite'), checkpoint_name=str(tmp_path/'checks.sqlite'))
    seed_learner(app.conn, 'ap-attempt', {'alias': 'Synthetic regression'})
    try:
        proposal = app.propose_set(item['problem']['concept_ids'][0])
        app.decide(proposal['set_id'], 'edit', 'synthetic-fixture-only', question_ids=[item['question_id']])
        app.decide(proposal['set_id'], 'approve', 'synthetic-fixture-only')
        app.turn('ap-attempt', 'ap-attempt', 'practice', chapter='arithmetic_progressions')
        g = item['problem']['givens']
        wrong = str(g['a'] + g['n'] * g['d'])
        for _ in range(2):
            reply = app.turn('ap-attempt', 'ap-attempt', wrong, chapter='arithmetic_progressions')
            assert reply['diagnosis']['misconception_id'] == 'ap_m03'
            assert CATALOGUE['ap_m03']['diagnostic_probe'] in reply['reply']
            assert reply['checks']['ok']
        assert app.conn.execute("SELECT status FROM misconceptions WHERE misconception_id='ap_m03'").fetchone()[0] == 'suspected'
    finally:
        app.close()


@pytest.mark.parametrize('mid', sorted(k for k, r in CATALOGUE.items() if r['chapter'] in ('arithmetic_progressions', 'trigonometry')))
def test_public_catalogue_wrong_work_has_statement_coverage(mid):
    row = CATALOGUE[mid]
    assert mid in diagnosis_evidence.candidates(row['example_wrong_work'], row['chapter'], set(CATALOGUE))


@pytest.mark.parametrize(('verdict_mid', 'quote', 'confidence'), [
    ('ap_m03', 'AP must increase', 0.99),
    ('ap_m05', 'a quote the learner never said', 0.99),
    ('ap_m05', 'AP must increase', 0.2),
    ('ap_m05', 'AP must increase', True),
])
def test_model_cannot_relabel_or_invent_diagnosis_evidence(tmp_path, verdict_mid, quote, confidence):
    app = TutorApp(llm_mode='stub', db_name=str(tmp_path/'db.sqlite'), checkpoint_name=str(tmp_path/'checks.sqlite'))
    seed_learner(app.conn, 'evidence-case', {'alias': 'Synthetic regression'})
    app.llm.enabled = True
    app.llm.complete = lambda **kwargs: json.dumps({'misconception_id': verdict_mid, 'confidence': confidence, 'evidence': quote, 'question': 'Which formula branch should we choose?'})
    try:
        state = {'focus_misconception': 'ap_m05', 'messages': [{'content': 'I think an AP must increase'}],
                 'session': {'session_id': 'evidence-case', 'learner_id': 'evidence-case', 'chapter': 'arithmetic_progressions'},
                 'learner': {'misconceptions': {}}}
        result = app._diagnose(state)
        assert result['diagnosis']['misconception_id'] == 'ap_m05'
        assert result['diagnosis']['status'] == 'suspected'
        assert CATALOGUE['ap_m05']['diagnostic_probe'] in result['draft']['text']
        assert 'LLM quote:' not in ' '.join(result['diagnosis']['evidence'])
    finally:
        app.close()
