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
    return result
