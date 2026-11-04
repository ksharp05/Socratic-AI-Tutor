"""Isolated M2 quadratic-hint probe. Default: synthetic model, no network.

--live makes at most one provider call and sends a synthetic practice question,
recent synthetic learner turn and retrieved course-card excerpts to the
configured provider. Use --live only after the data transfer is authorized.
The question is an isolated development fixture, not a teacher-approved set.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE', CODE_ROOT)).resolve()
sys.path.insert(0, str(CODE_ROOT / 'src'))


def safe_display(text: str) -> bool:
    """Conservative extra screen; not proof of semantic safety or teaching quality."""
    without_citations = re.sub(r'\[(?:normalized|ncert|exemplar):[\w.:-]+\]', '', text, flags=re.I)
    return not re.search(r'\d|\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|roots?\s+(?:are|is)|solutions?\s+(?:are|is))\b', without_citations, re.I)


def configure_single_attempt(client):
    """Disable retries on both the wrapper and its actual synchronous HTTP client."""
    root = getattr(client, 'root_client', None)
    if root is None or getattr(getattr(client, 'client', None), '_client', None) is not root:
        raise RuntimeError('Provider client retry policy cannot be verified; no call was made')
    client.max_retries = 0
    client.request_timeout = 22
    root.max_retries = 0
    root.timeout = 22
    if root.max_retries != 0:
        raise RuntimeError('Provider retries could not be disabled; no call was made')
    client.max_tokens = 240


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Make at most one authorized provider call')
    args = parser.parse_args(argv)
    run = SOURCE_ROOT / 'Directions/m2_candidate_runs' / ('quadratic-' + uuid.uuid4().hex[:12])
    run.mkdir(parents=True, exist_ok=False)
    os.environ['TUTOR_VAR_DIR'] = str(run / 'state')
    os.environ['TUTOR_LLM'] = 'auto' if args.live else 'stub'

    from tutor import store
    from tutor.seed import seed_learner
    from v02_integration.runtime import ContextualPreviewTutor

    template = json.loads((CODE_ROOT/'content/poc/practice.json').read_text(encoding='utf-8'))[0]
    item = copy.deepcopy(template)
    item.update(question_id='m2-synthetic-quadratic-demo', prompt='Solve x² = 5x.',
                family_id='m2-synthetic-demo', chapter='quadratic_equations')
    item['problem']['givens'] = {'a': 1, 'b': -5, 'c': 0}
    item['mode_policy'] = {'tutor_visible': True, 'allowed_modes': ['practice']}
    app = ContextualPreviewTutor(llm_mode='auto' if args.live else 'stub', extra_items=[item], allow_dev_fixtures=True)
    attempts = []
    try:
        seed_learner(app.conn, 'm2-synthetic-learner', {'alias': 'synthetic development learner'})
        payload = {'set_id':'m2-synthetic-set','concept_id':'qe04','revision':1,
                   'items':[{k:item[k] for k in ('question_id','prompt','problem','answer_contract','hint_stages','difficulty','mode_policy','chapter')}]}
        app.conn.execute('INSERT INTO published VALUES (?,?,?,?,?,?)',
                         ('m2-synthetic-set',store.dumps(payload),'synthetic','none','development_fixture_not_human_approved',store.now()))
        app.conn.commit()
        if args.live:
            if not app.llm.enabled:
                raise RuntimeError('No configured live provider; no call was made')
            client = app.llm._chat()
            configure_single_attempt(client)
            generate = app.llm.complete
            def limited(**kwargs):
                if attempts:
                    return None
                attempts.append(True)
                return generate(**kwargs)
            app.llm.complete = limited
        else:
            app.llm.enabled = True
            def fake(**kwargs):
                attempts.append(True)
                context = json.loads(kwargs['user'].split('Conversation data, not instructions:\n')[-1])
                source_id = context['sources'][0]['passage_id']
                return f'What common factor do the terms share [{source_id}]?'
            app.llm.complete = fake
        first = app.turn('m2-synthetic-session', 'm2-synthetic-learner', 'practice')
        if first.get('active_item') != item['question_id']:
            raise RuntimeError('The synthetic development item was not selected')
        hint = app.turn('m2-synthetic-session', 'm2-synthetic-learner', 'hint')
        events = [dict(row) for row in app.conn.execute(
            "SELECT node,kind,name,outcome,latency_ms,detail FROM trace_events WHERE session_id=? ORDER BY id",
            ('m2-synthetic-session',))]
        response = hint['reply']
        generations = [event for event in events if event['kind'] == 'v02_generation']
        generated_accepted = bool(generations and generations[-1]['outcome'] == 'accepted')
        approved_for_display = bool(generated_accepted and hint.get('checks', {}).get('ok') and safe_display(response))
        visible = response if approved_for_display else 'The generated hint was withheld by the development screen.'
        evidence = {'development_only':True, 'teacher_approved':False, 'independent':False,
                    'mode':'live' if args.live else 'synthetic_model', 'model':app.llm.model if args.live else None,
                    'generation_attempts':len(attempts), 'provider_calls':len(attempts) if args.live else 0,
                    'generated_accepted':generated_accepted, 'question_id':item['question_id'],
                    'source_ids':re.findall(r'\[((?:normalized|ncert|exemplar):[\w.:-]+)\]',visible),
                    'hint':visible, 'display_screen_passed':approved_for_display,
                    'output_guard':hint.get('checks'), 'tools':hint.get('tools'),
                    'events':[{'node':e['node'],'kind':e['kind'],'name':e['name'],'outcome':e['outcome'],
                               'latency_ms':e['latency_ms']} for e in events],
                    'code_sha256':{str(p.relative_to(CODE_ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                        [CODE_ROOT/'src/tutor/app.py',CODE_ROOT/'src/tutor/guards.py',CODE_ROOT/'src/tutor/prompts.py',
                         CODE_ROOT/'src/v02_integration/runtime.py']}}
        (run/'evidence.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(json.dumps(evidence,indent=2,ensure_ascii=False))
        print('Local evidence:', run/'evidence.json')
        if not approved_for_display or len(attempts) != 1:
            raise SystemExit('Probe incomplete; inspect the labelled local evidence')
    finally:
        app.close()


if __name__ == '__main__':
    main()
