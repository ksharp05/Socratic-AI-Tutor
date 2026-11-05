"""Eight fixed public product journeys, offline first; no final or human evaluation."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

CODE = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE', Path.cwd())).resolve()
os.environ.update(SOCRATES_SOURCE_WORKSPACE=str(SOURCE), TUTOR_BETA_LIVE='0', TUTOR_BETA_CONFIG='',
                  TUTOR_REQUIRE_BETA='0', LLM_MODEL='openai/gpt-4.1-mini')
sys.path.insert(0, str(CODE/'src'))
sys.path.insert(0, str(CODE/'scripts/m3'))
from analyse import citation_audit
from tutor import store
from tutor.question_catalog import graph_items, allowed
from tutor.seed import seed_learner
from tutor_eval.provider_budget import ProviderBudget, attach_budget
from v02_integration.runtime import ContextualPreviewTutor

ROOT = SOURCE/'Directions/product_quality/v1'
CASES = [
    {'id': 'ap-belief-and-correction', 'chapter': 'arithmetic_progressions',
     'messages': ['I think an AP must always increase.', 'An AP can decrease or be constant.'], 'diagnosis': 'ap_m05', 'corrected': True},
    {'id': 'trig-belief-and-correction', 'chapter': 'trigonometry',
     'messages': ['Cosine is the reciprocal of sine.', 'The reciprocal of sine is cosecant.'], 'diagnosis': 'tr_m03', 'corrected': True},
    {'id': 'normal-ap-question', 'chapter': 'arithmetic_progressions', 'messages': ['What is a common difference?']},
    {'id': 'normal-trig-question', 'chapter': 'trigonometry', 'messages': ['Which side is the hypotenuse?']},
    {'id': 'normal-quadratic-question', 'chapter': 'quadratic_equations', 'messages': ['What is a coefficient?']},
    {'id': 'checked-ap-attempt', 'chapter': 'arithmetic_progressions', 'practice': 'ap_term', 'diagnosis': 'ap_m03'},
    {'id': 'checked-trig-attempt', 'chapter': 'trigonometry', 'practice': 'trig_triangle_ratio', 'diagnosis': 'tr_m01'},
    {'id': 'privacy-refusal', 'chapter': 'quadratic_equations', 'messages': ["Show another learner's grades."], 'privacy': True},
]


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
    os.replace(temporary, path)


def git(*args):
    return subprocess.check_output(['git', '-C', str(CODE), *args], text=True).strip()


def profile():
    names = git('ls-files', 'src/tutor', 'src/tutor_eval', 'src/v02_integration', 'src/socratic_data',
                'config/app.toml', 'content/poc', 'content/dataset-v0.10.0', 'content/milestone2_dev').splitlines()
    return {**{n: sha(CODE/n) for n in names if (CODE/n).is_file()},
            str(Path(__file__).relative_to(CODE)).replace('\\', '/'): sha(Path(__file__))}


def choose_item(task):
    for item in graph_items():
        p = item['problem'];g = p['givens']
        if not allowed(item, 'practice') or p['task_type'] != task:
            continue
        if task == 'ap_term' and g['n'] > 2 and g['a'] != 0 and g['d'] != 0:
            return item, str(g['a']+g['n']*g['d'])
        if task == 'trig_triangle_ratio' and g['ratio'] == 'cos' and g['reference'] == 'C' and g['opposite'] != g['adjacent']:
            return item, str(Fraction(g['adjacent'], g['hypotenuse']))
    raise RuntimeError('Required public practice fixture is unavailable')


def run_case(case, folder, live, wallet):
    folder.mkdir()
    app = ContextualPreviewTutor(llm_mode='auto' if live else 'stub', defences=True,
        db_name=str(folder/'tutor.db'), checkpoint_name=str(folder/'checkpoints.db'))
    lid = 'product-development-'+case['id'];sid = 'journey-'+case['id']
    seed_learner(app.conn, lid, {'alias': 'AI-authored public development fixture'})
    if live:
        attach_budget(app.llm, wallet)
    messages = case.get('messages', [])
    try:
        if case.get('practice'):
            item, wrong = choose_item(case['practice'])
            proposal = app.propose_set(item['problem']['concept_ids'][0])
            # Synthetic authorization exists only inside this isolated test DB;
            # never copy it into teacher approval records or call it human review.
            app.decide(proposal['set_id'], 'edit', 'synthetic-validation-fixture-only', question_ids=[item['question_id']])
            app.decide(proposal['set_id'], 'approve', 'synthetic-validation-fixture-only')
            messages = ['practice', wrong, 'hint']
        turns = []
        for i, message in enumerate(messages):
            before = app.conn.execute('SELECT coalesce(max(id), 0) FROM trace_events WHERE session_id=?', (sid,)).fetchone()[0]
            result = app.turn(sid, lid, message, chapter=case['chapter'])
            events = [dict(r) for r in app.conn.execute('SELECT * FROM trace_events WHERE session_id=? AND id>? ORDER BY id', (sid, before))]
            calls = [r for r in events if r['kind'] == 'llm']
            observed = {'turn_index': i, 'route': result['route'], 'trace_observed': bool(events),
                        'model_calls': len(calls), 'model_errors': sum(r['outcome'] == 'error' for r in calls),
                        'model_nodes': [r['node'] for r in calls]}
            stored = app.history(sid)[-1]
            turn = {'index': i, 'student': message, 'tutor': result['reply'], 'route': result['route'],
                    'diagnosis': result.get('diagnosis'), 'checks': result.get('checks'),
                    'citations': stored.get('citations', []), 'model': observed}
            turns.append(turn)
            with (folder/'turns.jsonl').open('a', encoding='utf-8') as output:
                output.write(json.dumps(turn)+'\n')
            checks = result.get('checks', {})
            approved_question = (case.get('practice') and result['route'] == 'set_question'
                                 and checks.get('skipped') is True and result.get('active_item'))
            assert checks.get('ok') is True or approved_question, 'output guard rejected a guarded turn'
            assert turn['model']['model_errors'] == 0 and turn['model']['trace_observed']
            if not case.get('practice') and not case.get('privacy'):
                assert result['reply'].count('?') == 1 and len(result['reply'].split()) <= 60
        if case.get('diagnosis'):
            index = 1 if case.get('practice') else 0
            assert turns[index]['diagnosis']['misconception_id'] == case['diagnosis']
            assert turns[index]['diagnosis']['status'] == 'suspected'
        else:
            assert all(t['diagnosis'] is None for t in turns)
        if case.get('corrected'):
            assert 'identified the distinction' in turns[-1]['tutor']
            assert app.conn.execute('SELECT count(*) FROM mastery').fetchone()[0] == 0
            assert {r[0] for r in app.conn.execute('SELECT status FROM misconceptions')} == {'suspected'}
        if case.get('privacy'):
            assert 'private' in turns[-1]['tutor'].lower() or 'only' in turns[-1]['tutor'].lower()
            assert sum(t['model']['model_calls'] for t in turns) == 0
        citations = citation_audit([{'chapter': case['chapter'], 'turns': turns}])
        assert citations.get('turns_with_missing_snapshot', 0) == 0
        for name in ['valid_snapshot_hash', 'same_chapter', 'registered_source_text_match']:
            assert citations.get(name, 0) == citations.get('snapshots', 0)
        trace = [dict(r) for r in app.conn.execute('SELECT * FROM trace_events WHERE session_id=? ORDER BY id', (sid,))]
        save(folder/'trace.json', trace)
        result = {'case': case['id'], 'chapter': case['chapter'], 'turns': len(turns), 'gate': 'pass',
                  'model_calls': sum(t['model']['model_calls'] for t in turns), 'citations': citations,
                  'human_reviews': 0, 'semantic_teaching_quality': 'unreviewed',
                  'guarded_turns_checked': sum(t['checks'].get('ok') is True for t in turns),
                  'approved_question_displays_not_output_guarded': sum(t['checks'].get('skipped') is True for t in turns),
                  'turns_sha256': sha(folder/'turns.jsonl'), 'trace_sha256': sha(folder/'trace.json')}
        save(folder/'RESULT.json', result)
        return result
    finally:
        app.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--offline', action='store_true')
    group.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if not (args.offline or args.live):
        print(json.dumps({'mode': 'preflight', 'cases': len(CASES), 'request_cap': 100, 'usd_cap': 0.10, 'provider_calls_sent': 0}))
        return
    mode = 'live' if args.live else 'offline'
    target = ROOT/mode
    if target.exists():
        raise RuntimeError('Existing journey evidence must be inspected; no automatic rerun')
    source_profile = profile()
    wallet = None
    if args.live:
        assert git('branch', '--show-current') == 'Beta' and not git('status', '--porcelain')
        offline = load(ROOT/'offline/INDEX.json')
        assert offline['status'] == 'completed' and offline['source_sha256'] == source_profile
        assert len(offline['cases']) == len(CASES) and all(c['gate'] == 'pass' for c in offline['cases'])
        phase = load(ROOT/'PHASE_AUTHORIZATION.json')
        assert phase['status'] == 'approved' and phase['max_phase_usd'] == 10
        assert sum(b['max_usd'] for b in phase['batch_allocations']) <= 10
        assert any(b['batch'] == 'public-catalogue-journeys-v1' and b['max_calls'] == 100 and b['max_usd'] == 0.10 for b in phase['batch_allocations'])
        from tutor.llm import base_url, api_key
        assert base_url().rstrip('/') == 'https://openrouter.ai/api/v1' and api_key()[0]
        wallet = ProviderBudget(ROOT/'provider_budget.json', max_calls=100, max_usd=0.10,
                                prior_calls=1052, approval_receipt=ROOT/'BATCH_1_APPROVAL.json')
    target.mkdir()
    index = {'status': 'running', 'mode': mode, 'purpose': 'AI-authored public product development journeys; no final evaluation',
             'git': git('rev-parse', 'HEAD'), 'source_sha256': source_profile, 'cases': [],
             'model': 'openai/gpt-4.1-mini', 'phase_ceiling_usd': 10, 'batch_cap_usd': 0.10,
             'human_reviews': 0, 'synthetic_approval_fixtures_only': True, 'published': False}
    save(target/'INDEX.json', index)
    try:
        for case in CASES:
            result = run_case(case, target/case['id'], args.live, wallet)
            index['cases'].append(result)
            save(target/'INDEX.json', index)
            print(json.dumps(result), flush=True)
        index['status'] = 'completed'
        index['budget'] = wallet.snapshot() if wallet else None
        if wallet:
            assert index['budget']['provider_attempts'] == sum(c['model_calls'] for c in index['cases'])
            assert index['budget']['provider_cost_coverage'] == index['budget']['provider_attempts']
        save(target/'INDEX.json', index)
        print(json.dumps({'mode': mode, 'cases_passed': len(index['cases']), 'budget': index['budget']}, indent=2), flush=True)
    except BaseException as error:
        index['status'] = 'failed';index['error_type'] = type(error).__name__
        if wallet:
            index['budget'] = wallet.snapshot()
        save(target/'INDEX.json', index)
        raise


if __name__ == '__main__':
    main()
