"""Post-hoc simulator sensitivity on saved tutoring trajectories; never calls a tutor/model.

First reproduce every recorded semantic outcome with the unchanged run_session function.
Then suppress only post-quiz copying and replay the same recorded tutor/grade trajectory.
This is exploratory sensitivity, not a new experimental condition or a corrected live run.
"""
from __future__ import annotations
import ast
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

CODE = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE', Path.cwd())).resolve()
sys.path.insert(0, str(CODE / 'src'))
from tutor import store
from tutor_eval import harness, simulator
sys.path.insert(0, str(CODE / 'scripts/m3'))
from analyse import paired


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RecordedApp:
    """No model or tutor exists in this adapter. Reject any change in student input."""
    def __init__(self, session):
        self.session = session
        self.cursor = 0
        self.current = None
        self.conn = store.connect(Path(':memory:'))
        self.graph = SimpleNamespace(get_state=self.get_state)

    def turn(self, session_id, learner_id, message, *, chapter):
        turn = self.session['turns'][self.cursor]
        if message != turn['student'] or chapter != self.session['chapter']:
            raise AssertionError('Recorded trajectory diverged at turn ' + str(self.cursor))
        self.cursor += 1
        self.current = turn
        return {'reply': turn['tutor'], 'route': turn['route'], 'active_item': turn['active_item'],
                'diagnosis': {'misconception_id': turn['diagnosis']} if turn['diagnosis'] else {},
                'tools': turn.get('tools', []), 'citations': turn.get('citations', []),
                'checks': turn.get('checks', {})}

    def get_state(self, config):
        recorded = self.current.get('graded_attempt')
        grade = None
        if recorded and recorded['tutor_status'] != 'not_checked':
            grade = {'question_id': recorded['question_id'], 'status': recorded['tutor_status'],
                     'correct': recorded['tutor_correct'], 'scorable': recorded['tutor_correct'] is not None}
        return SimpleNamespace(values={'grade': grade} if grade else {})


def semantic(session):
    fields = ['student', 'chapter', 'seed', 'session', 'seeded', 'practice_summary', 'named', 'targeted',
              'cleared', 'pre', 'post', 'failures']
    turn_fields = ['index', 'student', 'tutor', 'route', 'problem', 'diagnosis', 'active_item', 'leaks',
                   'quiz_contamination', 'post_question_exposure', 'graded_attempt', 'error']
    return {**{key: session[key] for key in fields},
            'turns': [{key: turn.get(key) for key in turn_fields} for turn in session['turns']]}


def replay(recorded, card, pairs, catalogue, practice, run_id, *, suppress_post_copy=False):
    app = RecordedApp(recorded)
    post_ids = {pair['post']['question_id'] for pair in pairs}
    original_quiz = harness._quiz

    def quiz_without_post_copy(student, items):
        if {item['question_id'] for item in items} == post_ids:
            student.told.difference_update(post_ids)
        return original_quiz(student, items)

    context = patch.object(harness, '_quiz', quiz_without_post_copy) if suppress_post_copy else nullcontext()
    try:
        with context:
            result = harness.run_session(app, card, pairs,
                {'run': {'max_turns': len(recorded['turns']), 'turn_timeout_s': 120}},
                recorded['seed'], run_id, catalogue, practice, simulator.Voice('template'))
        assert app.cursor == len(recorded['turns'])
        return result
    finally:
        app.conn.close()


def gain(session):
    return sum(bool(q['correct']) for q in session['post']) - sum(bool(q['correct']) for q in session['pre'])


def main():
    root = SOURCE / 'Directions/m3_runs/v2'
    wallet = SOURCE / 'Directions/m3_runs/provider_budget.json'
    before = sha(wallet)
    # Prove this analysis uses the actual frozen transition function, not a rewritten approximation.
    frozen = subprocess.check_output(['git', '-C', str(CODE), 'show', '12d541e:src/tutor_eval/harness.py'], text=True)
    current = (CODE / 'src/tutor_eval/harness.py').read_text(encoding='utf-8')
    function = lambda text: next(ast.dump(n, include_attributes=False) for n in ast.parse(text).body
                                  if isinstance(n, ast.FunctionDef) and n.name == 'run_session')
    assert function(frozen) == function(current)
    data = SOURCE / 'Directions/m3_data/development-v1'
    cards = {c['student_id']: c for c in load(data / 'students.json')}
    pairs = {p['pair_id']: p for p in load(data / 'pairs.json')}
    assigned = {a['student_id']: a['pair_ids'] for a in load(data / 'assignments.json')}
    catalogue = {m['misconception_id']: m for m in rows(CODE / 'content/dataset-v0.10.0/misconceptions.jsonl')}
    connection = store.connect(Path(':memory:'))
    try:
        practice = {q['question_id']: q for q in harness._publish_fixture_items(connection)}
    finally:
        connection.close()
    results = []; aggregate = []; manifests = []
    index = load(root / 'live/INDEX.json')
    for arm, job in index['jobs'].items():
        if arm.startswith('e2_') or job.get('status') != 'completed':
            continue
        directory = Path(job['run']); manifest = load(directory / 'manifest.json')
        recorded_rows = rows(directory / 'sessions.jsonl'); arm_rows = []
        for recorded in recorded_rows:
            chosen = [pairs[p] for p in assigned[recorded['student']]]
            pre_ids = {p['pre']['question_id'] for p in chosen}
            post_ids = {p['post']['question_id'] for p in chosen}
            assert not post_ids & (pre_ids | set(practice)), 'Post copy may affect the tutoring trajectory'
            args = (recorded, cards[recorded['student']], chosen, catalogue, practice, manifest['run_id'])
            baseline = replay(*args)
            if semantic(baseline) != semantic(recorded):
                raise AssertionError('Frozen baseline replay mismatch: ' + recorded['session'])
            sensitivity = replay(*args, suppress_post_copy=True)
            assert semantic(baseline)['turns'] == semantic(sensitivity)['turns']
            row = {'condition': arm, 'session': recorded['session'], 'student': recorded['student'],
                   'seed': recorded['seed'], 'baseline_reproduced': True,
                   'original_gain': gain(recorded), 'without_post_copy_gain': gain(sensitivity),
                   'copied_post_items_original': sum(q['rule'] == 'copied_from_tutor' for q in recorded['post']),
                   'copied_post_items_sensitivity': sum(q['rule'] == 'copied_from_tutor' for q in sensitivity['post'])}
            assert row['copied_post_items_sensitivity'] == 0
            arm_rows.append(row); results.append(row)
        aggregate.append({'condition': arm, 'sessions': len(arm_rows),
            'original_mean_gain': statistics.fmean(r['original_gain'] for r in arm_rows),
            'without_post_copy_mean_gain': statistics.fmean(r['without_post_copy_gain'] for r in arm_rows),
            'changed_session_scores': sum(r['original_gain'] != r['without_post_copy_gain'] for r in arm_rows),
            'original_copied_post_items': sum(r['copied_post_items_original'] for r in arm_rows)})
        manifests.append({'run_id': manifest['run_id'], 'manifest_sha256': sha(directory / 'manifest.json'),
                          'sessions_sha256': sha(directory / 'sessions.jsonl')})
        print('Reproduced and replayed', arm, len(arm_rows), flush=True)
    assert sha(wallet) == before
    groups = {arm: [r for r in results if r['condition'] == arm] for arm in index['jobs'] if not arm.startswith('e2_')}
    comparisons = {}
    for label, left, right, seed in [('C2_minus_C1', 'c1', 'c2', None), ('C2_minus_C0', 'c0', 'c2', None),
            ('E3_tranche_minus_matched_C2', 'c2', 'e3_after_budget_tranche12', None),
            ('memory_on_minus_off', 'memory_off', 'c2', 1), ('telling_minus_hints', 'c2', 'direct_answers', 1)]:
        comparisons[label] = paired(groups[left], groups[right], lambda row: row['without_post_copy_gain'], seed)
    private = {'method': 'post_hoc_fixed_trajectory_disable_all_post_quiz_copying',
        'baseline_reproductions': len(results), 'provider_calls': 0, 'original_ledger_sha256': before,
        'original_run_session_AST_matches_frozen_commit': True, 'original_outcomes_unchanged': True,
        'script_sha256': sha(Path(__file__)), 'conditions': aggregate, 'paired_quiz_gain_sensitivity': comparisons,
        'inputs': manifests, 'sessions': results}
    (root / 'validation/POST_COPY_SENSITIVITY.json').write_text(json.dumps(private, indent=2) + '\n', encoding='utf-8')
    public = {k: v for k, v in private.items() if k != 'sessions'}
    out = CODE / 'Docs/m4/POST_COPY_SENSITIVITY.json'
    out.write_text(json.dumps(public, indent=2) + '\n', encoding='utf-8')
    lines = ['# Post-quiz copying sensitivity - exploratory offline replay', '',
        f"The simulator replay matched all {len(results)} recorded student-message sequences, diagnoses/clearing, practice summaries and pre/post quiz answers while consuming the recorded tutor replies and grades. It uses the frozen run_session transition function. This does not verify that a live tutor would regenerate those replies. Timing/tool traces are excluded, and no tutor or model is invoked.", '',
        'A second replay holds every recorded tutoring message and grade fixed, but clears the post-quiz told set immediately before the post quiz. No post-quiz ID is a pre-quiz or registered-practice ID, so this intervention leaves the tutoring trajectory unchanged. The simulator uses its ordinary mastery/misconception/guessing rules for the post quiz instead of copying.', '',
        '| Condition | Sessions | Original mean quiz change | Without post copying | Changed session scores | Original copied post items |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in aggregate:
        lines.append(f"| {r['condition']} | {r['sessions']} | {r['original_mean_gain']:.3f} | {r['without_post_copy_mean_gain']:.3f} | {r['changed_session_scores']} | {r['original_copied_post_items']} |")
    lines += ['', 'Paired differences below use the same student-cluster bootstrap as the original analysis: 2,000 resamples, seed 0, matched student/seed pairs. They quantify this post-hoc sensitivity only.', '',
        '| Without-post-copy contrast | Matched sessions / cards | Difference | Bootstrap 95% interval |',
        '| --- | ---: | ---: | --- |']
    for label, row in comparisons.items():
        lo, hi = row['cluster_bootstrap_ci95']
        lines.append(f"| {label} | {row['matched_sessions']}/{row['student_clusters']} | {row['difference']:.4f} | [{lo:.4f}, {hi:.4f}] |")
    lines += ['', 'This is a post-hoc sensitivity, not a preregistered comparison, a rerun of the tutor, a human learning estimate or a replacement for the original primary results. Disabling all post copying can remove genuine as well as false disclosure; it is not a calibrated detector. Skipped copying branches normally skip random draws, so later quiz-item draws can also change. Shared simulator/kernel assumptions remain. Validate a revised contextual disclosure rule separately before a fresh qualified study.', '',
        'Original transcripts, manifests, labels, study results and provider ledger are unchanged. Exact input hashes and aggregate results are in POST_COPY_SENSITIVITY.json; per-session audit records remain private.']
    report = CODE / 'Docs/m4/POST_COPY_SENSITIVITY.md'
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    for p in [out, report]: shutil.copy2(p, SOURCE / 'Docs/m4' / p.name)
    print(json.dumps({'baseline_reproductions': len(results), 'conditions': aggregate, 'provider_calls': 0}, indent=2))


if __name__ == '__main__':
    main()
