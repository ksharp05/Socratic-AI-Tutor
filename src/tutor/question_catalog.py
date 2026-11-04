"""Public practice and explicitly scoped development-check question sources."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from .config import ROOT
from .setup_content import load

PUBLIC_FIELDS = ('question_id','prompt','problem','answer_contract','hint_stages','difficulty','chapter','family_id','supporting_passage_ids')
MODES = frozenset({'practice','quiz','diagnostic'})
# Only scalar families supported by the connected graph's parser and checker.
CONNECTED_PRACTICE_FAMILIES = {
    'arithmetic_progressions': frozenset({'ap_term', 'ap_sum'}),
    'trigonometry': frozenset({'trig_triangle_ratio'}),
}


def allowed(item: dict, mode: str) -> bool:
    policy = item.get('mode_policy')
    if not isinstance(policy, dict) or policy.get('tutor_visible') is not True:
        return False
    modes = policy.get('allowed_modes')
    return (isinstance(modes,list) and all(isinstance(m,str) and m in MODES for m in modes)
            and mode in modes)


def graph_items(poc_loader=load) -> list[dict]:
    """Return matched quadratic POC items, supported public practice and separate dev checks.

    No private/evaluation material is read. Missing or mismatched public content
    is not silently promoted; existing approvals are rechecked against this pool.
    """
    path=ROOT/'content/dataset-v0.10.0/practice_questions.jsonl'
    with path.open(encoding='utf-8-sig') as f:
        public={item['question_id']:item for item in (json.loads(line) for line in f if line.strip())}
    result=[];seen=set()
    for raw in poc_loader('practice'):
        original=public.get(raw['question_id'])
        if not original or any(raw.get(k)!=original.get(k) for k in PUBLIC_FIELDS):
            continue
        item=copy.deepcopy(raw);item['mode_policy']=copy.deepcopy(original.get('mode_policy'))
        item['review_status']=original.get('review_status');item['authorship']=original.get('authorship')
        if allowed(item,'practice'):
            result.append(item);seen.add(item['question_id'])
    for original in public.values():
        chapter = original.get('chapter')
        problem = original.get('problem') or {}
        if (problem.get('task_type') not in CONNECTED_PRACTICE_FAMILIES.get(chapter, ())
                or (original.get('answer_contract') or {}).get('allowed_kinds') != ['scalar']
                or not allowed(original, 'practice')):
            continue
        qid = original['question_id']
        if qid in seen:
            raise ValueError('Duplicate practice question ID')
        item = copy.deepcopy(original)
        item.setdefault('review_status', None)
        item.setdefault('authorship', None)
        result.append(item)
        seen.add(qid)
    for item in json.loads((ROOT/'content/milestone2_dev/quiz_items.json').read_text(encoding='utf-8-sig')):
        qid=item.get('question_id')
        if not isinstance(qid,str) or qid in seen or qid in public:
            raise ValueError('Invalid or duplicate development-check question ID')
        if not allowed(item,'quiz') or allowed(item,'practice'):
            raise ValueError('Development check must be quiz-authorized and excluded from practice')
        result.append(item);seen.add(qid)
    return result
