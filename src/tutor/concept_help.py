"""Small source-backed explanations for explicit concept questions, not homework solving."""
from __future__ import annotations
import copy,json,re
from functools import lru_cache
from .config import ROOT

@lru_cache(maxsize=1)
def _load():
    data=json.loads((ROOT/'content/product_quality/v2/concept_help.json').read_text(encoding='utf-8'))
    refs={c['passage_id']:c for c in data['cards']}
    if len(refs)!=len(data['cards']):raise ValueError('Duplicate concept reference')
    for entry in data['explanations']:
        if entry['definition'] not in refs[entry['passage_id']]['text']:raise ValueError('Explanation lacks its stated source')
    return data

def cards():
    return copy.deepcopy(_load()['cards'])

def by_id(identifier):
    return copy.deepcopy(next((e for e in _load()['explanations'] if e['id']==identifier),None))

def match(text,chapter):
    if any(c.isnumeric() for c in text) or re.search(r'[=^]|\bsqrt\b|\b(?:calculate|solve|answer key|final answer)\b',text,re.I):return None
    if not re.search(r'\b(?:what|which side|define|explain|meaning|difference between)\b',text,re.I):return None
    return copy.deepcopy(next((e for e in _load()['explanations'] if e['chapter']==chapter and any(re.search(cue,text,re.I) for cue in e['cues'])),None))
