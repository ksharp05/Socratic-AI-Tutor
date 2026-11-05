"""Source-backed development cards for the three assessed chapters."""
from __future__ import annotations
import json
from .config import ROOT
from .setup_content import load

CHAPTERS = {'quadratic_equations': 'Quadratic Equations',
            'arithmetic_progressions': 'Arithmetic Progressions',
            'trigonometry': 'Introduction to Trigonometry'}


def cards():
    # Keep the existing quadratic POC behavior; add only public AP/trig cards.
    result=list(load('cards'));seen={item['passage_id'] for item in result}
    with (ROOT/'content/dataset-v0.10.0/corpus.jsonl').open(encoding='utf-8-sig') as f:
        for line in f:
            if not line.strip():continue
            item=json.loads(line)
            if item.get('chapter') in ('arithmetic_progressions','trigonometry'):
                if item['passage_id'] in seen:raise ValueError('Duplicate source card ID')
                seen.add(item['passage_id']);result.append(item)
    from .concept_help import cards as concept_cards
    for item in concept_cards():
        if item['passage_id'] in seen:raise ValueError('Duplicate supplemental source card ID')
        seen.add(item['passage_id']);result.append(item)
    return result


def concepts():
    """Retain the quadratic graph and register public AP/trigonometry concepts for observations."""
    result = list(load('concepts'))
    seen = {item['concept_id'] for item in result}
    with (ROOT / 'content/dataset-v0.10.0/concepts.jsonl').open(encoding='utf-8-sig') as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get('chapter') in ('arithmetic_progressions', 'trigonometry'):
                if item['concept_id'] in seen:
                    raise ValueError('Duplicate concept ID')
                seen.add(item['concept_id'])
                result.append(item)
    return result


def misconceptions():
    """Register public AP/trigonometry hypotheses without inferring teaching approval.

    A catalogue entry supplies vocabulary and a probe, not proof of a learner's
    misconception. Numerical adapters and statement evidence remain separately
    checked, and all catalogue review/author fields are preserved.
    """
    result = list(load('misconceptions'))
    seen = {item['misconception_id'] for item in result}
    known_concepts = {item['concept_id'] for item in concepts()}
    with (ROOT / 'content/dataset-v0.10.0/misconceptions.jsonl').open(encoding='utf-8-sig') as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get('chapter') not in ('arithmetic_progressions', 'trigonometry'):
                continue
            if item['misconception_id'] in seen:
                raise ValueError('Duplicate misconception ID')
            if item['concept_id'] not in known_concepts:
                raise ValueError('Misconception references an unavailable concept')
            seen.add(item['misconception_id'])
            result.append(item)
    return result
