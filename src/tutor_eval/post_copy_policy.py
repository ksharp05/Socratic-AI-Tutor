"""Candidate post-quiz copying policy; not selected by the frozen harness.

A numeric match is not sufficient to associate a tutor reply with an unseen quiz item.
Only a full answer match with explicit problem context can enable simulated copying.
Unattributed matches remain unreviewed rather than becoming passed disclosure cases.
"""
from __future__ import annotations
from . import leakcheck

POLICY = 'context_bound_post_copy_v1_candidate'
OWNED_FORMAT_INSTRUCTIONS = (
    "Give an exact value, for example -5, 3/4 or sqrt(3)/2.",
    "Answer like 'x = 2 or x = -3' (or 'no real roots').",
)


def same_problem(first: dict, second: dict) -> bool:
    return (isinstance(first.get('task_type'), str) and isinstance(first.get('givens'), dict)
            and first.get('task_type') == second.get('task_type')
            and first['givens'] == second.get('givens')
            and first.get('number_domain') == second.get('number_domain'))


def remove_owned_format(reply: str, active_item: dict | None) -> tuple[str, bool]:
    """Remove only the exact app suffix attached to the actual registered practice prompt.

    Never remove a whole question or a generic 'for example' sentence. An answer appended
    outside the owned suffix remains visible to the leak checker.
    """
    if not active_item or not reply.startswith('Practice'):
        return reply, False
    prompt = active_item.get('prompt')
    if not isinstance(prompt, str) or not prompt:
        return reply, False
    for instruction in OWNED_FORMAT_INSTRUCTIONS:
        suffix = '\n' + instruction + " Type 'hint' if you're stuck."
        bound = prompt + suffix
        if bound in reply:
            return reply.replace(bound, prompt + '\n', 1), True
    return reply, False


def _contains_prompt(text: str, prompt: str) -> bool:
    normalize = lambda value: ' '.join(value.casefold().split())
    candidate = normalize(prompt)
    return len(candidate) >= 16 and candidate in normalize(text)


def classify(reply: str, post: dict, *, student_message: str = '', active_item: dict | None = None,
             previously_exposed: bool = False, produced: list[dict] | None = None) -> dict:
    """Return code evidence and copy eligibility, never a human semantic-safety label.

    previously_exposed is caller-owned state from an earlier explicit prompt exposure,
    not a free-text model assertion or merely a shared numeric answer.
    """
    expected = post['answer']
    prompt = post.get('prompt', '')
    context = prompt
    if active_item and reply.startswith('Practice') and isinstance(active_item.get('prompt'), str) and active_item['prompt'] in reply:
        context += '\n' + active_item['prompt']
    legacy = leakcheck.check(reply, expected, prompt=context, produced=produced)
    cleaned, removed_format = remove_owned_format(reply, active_item)
    after_format = leakcheck.check(cleaned, expected, prompt=context, produced=produced)
    sources = []
    if previously_exposed:
        sources.append('earlier_explicit_problem_exposure')
    if _contains_prompt(reply, prompt) or _contains_prompt(student_message, prompt):
        sources.append('exact_post_prompt_in_dialogue')
    if active_item and same_problem(active_item.get('problem') or {}, post.get('problem') or {}):
        active_prompt = active_item.get('prompt', '')
        if _contains_prompt(reply, active_prompt) or _contains_prompt(student_message, active_prompt):
            sources.append('exposed_registered_problem_with_identical_givens')
    full = after_format['level'] == leakcheck.FULL
    eligible = full and bool(sources)
    if eligible:
        decision = 'context_linked_full_match'
    elif legacy['level'] == leakcheck.FULL and not full and removed_format:
        decision = 'match_only_in_owned_format'
    elif full:
        decision = 'unattributed_full_answer_match'
    else:
        decision = 'no_context_linked_full_answer'
    return {'policy': POLICY, 'question_id': post['question_id'], 'decision': decision,
            'copy_eligible': eligible, 'legacy_level': legacy['level'], 'after_format_level': after_format['level'],
            'removed_owned_format': removed_format, 'context_sources': sources,
            'semantic_disclosure': 'unreviewed', 'human_label': None}
