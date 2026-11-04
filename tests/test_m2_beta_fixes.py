"""Regression checks for the 5 November Beta handoff defects; no provider calls."""
import asyncio

import pytest
from fastmcp import Client

from tutor import learner
from tutor.mcp_servers import textbook_kb
from tutor.retrieval.hybrid import HybridRetriever
from tutor.retrieval.textnorm import normalise_ratio_names, tokenize


@pytest.mark.parametrize('backend', ['poc_cards', 'hybrid'])
@pytest.mark.parametrize(('spelled', 'short', 'expected'), [
    ('SINE COSINE TANGENT', 'sin cos tan', 'ratios'),
    ('secant cosecant cotangent', 'sec csc cot', 'reciprocals'),
    ('sec cosec cot', 'sec csc cot', 'reciprocals'),
])
def test_ratio_names_find_formula_cards_in_both_backends(monkeypatch, backend, spelled, short, expected):
    cards = [dict(passage_id=pid, concept_id=pid, title=pid, text=text,
                  chapter='trigonometry', **{'class': 10}) for pid, text in [
        ('ratios', 'sin = opposite/hypotenuse; cos = adjacent/hypotenuse; tan = opposite/adjacent'),
        ('reciprocals', 'sec = 1/cos; csc = 1/sin; cot = 1/tan'),
    ]]
    monkeypatch.setattr(textbook_kb, 'topic_cards', lambda: cards)
    if backend == 'hybrid':
        from tutor.retrieval import hybrid
        monkeypatch.setattr(hybrid, 'build_retriever', lambda cfg, root: (HybridRetriever(cards, []), []))
    server = textbook_kb.build({'mode': backend})
    async def search():
        async with Client(server) as client:
            async def ids(query, chapter='trigonometry'):
                result = await client.call_tool('search', {'query': query, 'chapter': chapter, 'k': 2})
                return [r['passage_id'] for r in result.structured_content['results']]
            named, abbreviated = await ids(spelled), await ids(short)
            assert named == abbreviated and expected in named
            assert await ids(spelled, 'quadratic_equations') == []
    asyncio.run(search())


def test_ratio_normalisation_preserves_other_words_and_agrees_with_hybrid_tokens():
    assert normalise_ratio_names('cosinewave tangentline hyperbolic') == 'cosinewave tangentline hyperbolic'
    assert tokenize('cosecant squared') == tokenize('cosec squared') == tokenize('csc squared')


def result(cid, correct=True, qid='synthetic-quiz', scorable=True):
    return {'concept_ids': [cid], 'correct': correct, 'question_id': qid, 'scorable': scorable}


@pytest.mark.parametrize(('chapter', 'passed', 'next_concept'), [
    ('arithmetic_progressions', ['ap01', 'ap02', 'ap03'], 'ap04'),
    ('trigonometry', ['tr01', 'tr02', 'tr03'], 'tr04'),
])
def test_perfect_topic_quiz_advances_without_inventing_mastery(chapter, passed, next_concept):
    snapshot = {'mastery': {cid: .9 for cid in passed}}
    plan = learner.make_topic_plan(snapshot, chapter, [result(cid) for cid in passed])
    assert plan['steps'][0]['concept_id'] == next_concept
    assert not set(passed) & {step['concept_id'] for step in plan['steps']}
    assert plan['mastered'] == []  # .9 remains below the configured .95 threshold.
    assert plan['quiz_passed'] == sorted(passed)
    assert snapshot == {'mastery': {cid: .9 for cid in passed}}


@pytest.mark.parametrize(('chapter', 'missed'), [('arithmetic_progressions', 'ap03'), ('trigonometry', 'tr02')])
def test_topic_mistake_is_reviewed_even_if_snapshot_mastery_is_high(chapter, missed):
    plan = learner.make_topic_plan({'mastery': {missed: .99}}, chapter, [result(missed, False)])
    first = plan['steps'][0]
    assert first['concept_id'] == missed and first['action'] == 'review'
    assert '1 of 1' in first['why'] and first['evidence_question_ids'] == ['synthetic-quiz']
    assert missed not in plan['quiz_passed']


def test_quadratic_quiz_prioritises_the_missed_concept_and_names_its_prerequisite():
    plan = learner.make_plan({'mastery': {}}, quiz_results=[result('qe04', False)])
    first = plan['steps'][0]
    assert first['concept_id'] == 'qe04' and first['action'] == 'review_prerequisite'
    assert first['evidence_question_ids'] == ['synthetic-quiz']
    assert 'incorrect' in first['why'] and 'qe02' in first['why']


def test_perfect_quadratic_quiz_leaves_assessed_concepts_for_a_new_step():
    ids = ['qe01', 'qe02', 'qe03', 'qe04']
    plan = learner.make_plan({'mastery': {cid: .9 for cid in ids}}, quiz_results=[result(cid) for cid in ids])
    assert plan['steps'][0]['concept_id'] == 'qe05'
    assert plan['mastered'] == [] and plan['quiz_passed'] == ids


def test_unscorable_or_other_chapter_results_do_not_change_quadratic_plan():
    snapshot = {'mastery': {}}
    baseline = learner.make_plan(snapshot)
    assert learner.make_plan(snapshot, quiz_results=[result('qe04', False, scorable=False), result('ap03')]) == baseline


def test_perfect_ap_quiz_prefers_a_ready_successor_to_an_unassessed_foundation():
    passed = ['ap02', 'ap03', 'ap04', 'ap06']
    snapshot = {'mastery': {cid: .9 for cid in passed}}
    plan = learner.make_topic_plan(snapshot, 'arithmetic_progressions', [result(cid) for cid in passed])
    assert plan['steps'][0]['concept_id'] == 'ap05'
    assert 'ap01' not in [step['concept_id'] for step in plan['steps'][:2]]


def test_completed_plan_is_not_described_as_a_missing_plan():
    from tutor.conversation import plan_summary
    text = plan_summary({'steps': [], 'mastered': ['ap01'], 'version': 2})
    assert 'no new steps' in text and 'teacher' in text
    assert "don't have a study plan yet" in plan_summary(None)
