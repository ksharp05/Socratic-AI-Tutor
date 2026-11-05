"""Candidate post-quiz copying policy; not selected by the frozen harness.

A numeric match is not sufficient to associate a tutor reply with an unseen quiz item.
Only a full answer match with explicit problem context can enable simulated copying.
Unattributed matches remain unreviewed rather than becoming passed disclosure cases.
"""
from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from collections import Counter
import sqlite3
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


def context_sources(reply: str, post: dict, *, student_message: str = '', active_item: dict | None = None,
                    previously_exposed: bool = False) -> list[str]:
    sources = ['earlier_explicit_problem_exposure'] if previously_exposed else []
    if _contains_prompt(reply, post.get('prompt', '')) or _contains_prompt(student_message, post.get('prompt', '')):
        sources.append('exact_post_prompt_in_dialogue')
    if active_item and same_problem(active_item.get('problem') or {}, post.get('problem') or {}):
        prompt = active_item.get('prompt', '')
        if _contains_prompt(reply, prompt) or _contains_prompt(student_message, prompt):
            sources.append('exposed_registered_problem_with_identical_givens')
    return sources


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
    sources = context_sources(reply, post, student_message=student_message, active_item=active_item,
                              previously_exposed=previously_exposed)
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


# A context-local observer preserves the frozen transition function and isolates parallel sessions.
_CURRENT = ContextVar('post_copy_measurement', default=None)
LEGACY_POLICY = 'legacy_v2_numeric_match'


def current_measurement():
    return _CURRENT.get()


class Measurement:
    def __init__(self, app, post_items, practice):
        from . import simulator
        self.post_items = {p['question_id']: {**p, 'answer': p.get('answer') or simulator.correct_answer(p['problem'])}
                           for p in post_items}
        if not post_items or len(self.post_items) != len(post_items):
            raise ValueError('Context-bound scoring requires distinct post-quiz items')
        self.practice = practice
        self.exposed = set()
        self.eligible = set()
        self.audit = []
        self.model_observations = []
        self.event = None
        self.turns = 0
        self.filtered = None
        self.app = _ObservedApp(app, self)

    def begin_turn(self, message, result, model_observation=None):
        self.model_observations.append({'turn_index': self.turns, 'route': result.get('route'),
            **(model_observation or {'trace_observed': False, 'model_calls': None, 'model_errors': None, 'model_nodes': []})})
        reply = result.get('reply', '')
        active_item = self.practice.get(result.get('active_item'))
        self.event = {'reply': reply, 'student_message': message, 'active_item': active_item,
                      'previously_exposed': set(self.exposed), 'turn_index': self.turns}
        self.turns += 1
        for qid, post in self.post_items.items():
            if context_sources(reply, post, student_message=message, active_item=active_item):
                self.exposed.add(qid)

    def observe(self, post, produced):
        if self.event is None or post['question_id'] not in self.post_items:
            raise RuntimeError('Post-copy observer is missing its current turn')
        event = self.event
        result = classify(event['reply'], self.post_items[post['question_id']],
            student_message=event['student_message'], active_item=event['active_item'],
            previously_exposed=post['question_id'] in event['previously_exposed'], produced=produced)
        # Never grant copying from a match excluded by the frozen produced-answer rules.
        if result['legacy_level'] == leakcheck.FULL:
            self.audit.append({**result, 'turn_index': event['turn_index']})
            if result['copy_eligible']:
                self.eligible.add(post['question_id'])

    def before_quiz(self, student, items):
        if {p['question_id'] for p in items} != set(self.post_items):
            return  # pre quiz and registered-practice telling are unchanged
        before = student.told & set(self.post_items)
        removed = before - self.eligible
        student.told.difference_update(removed)
        self.filtered = {'post_ids_previously_told': sorted(before), 'removed_ineligible_post_ids': sorted(removed),
                         'post_ids_allowed_to_copy': sorted(before & self.eligible)}

    def summary(self):
        if self.filtered is None:
            raise RuntimeError('The post quiz did not pass through the context-bound filter')
        return {'policy': POLICY, 'status': 'development_candidate_not_human_calibrated',
                'legacy_full_match_witnesses': len(self.audit),
                'decision_counts': dict(Counter(row['decision'] for row in self.audit)),
                'explicitly_exposed_post_ids': sorted(self.exposed), **self.filtered,
                'semantic_disclosure': 'unreviewed', 'human_labels': 0, 'audit': self.audit,
                'turn_model_observations': self.model_observations}


class _ObservedApp:
    def __init__(self, app, measurement):
        self._app, self._measurement = app, measurement

    def __getattr__(self, name):
        return getattr(self._app, name)

    def _last_trace(self):
        conn = getattr(self._app, 'conn', None)
        if conn is None:
            return None
        try:
            return conn.execute('SELECT COALESCE(MAX(id),0) FROM trace_events').fetchone()[0]
        except (AttributeError, sqlite3.Error):
            return None

    def _model_calls(self, session_id, after):
        if after is None:
            return None
        rows = self._app.conn.execute("SELECT node,outcome FROM trace_events WHERE session_id=? AND id>? AND kind='llm'",
                                      (session_id, after)).fetchall()
        return {'trace_observed': True, 'model_calls': len(rows),
                'model_errors': sum(row[1] == 'error' for row in rows), 'model_nodes': [row[0] for row in rows]}

    def turn(self, session_id, learner_id, message, **kwargs):
        trace_start = self._last_trace()
        try:
            result = self._app.turn(session_id, learner_id, message, **kwargs)
        except Exception:
            self._measurement.begin_turn(message, {'reply': '', 'active_item': None}, self._model_calls(session_id, trace_start))
            raise
        self._measurement.begin_turn(message, result, self._model_calls(session_id, trace_start))
        return result


@contextmanager
def session_scope(app, post_items, practice):
    measurement = Measurement(app, post_items, practice)
    token = _CURRENT.set(measurement)
    try:
        yield measurement
    finally:
        _CURRENT.reset(token)
