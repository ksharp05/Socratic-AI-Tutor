"""Saved-data final development summary: E3's two batches form 48 unique matched sessions."""
from __future__ import annotations
import hashlib
import csv
import json
import os
from pathlib import Path
import shutil
import statistics
import sys
import subprocess
import re

CODE = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE', Path.cwd())).resolve()
sys.path.insert(0, str(CODE / 'src'))
sys.path.insert(0, str(CODE / 'scripts/m3'))
from tutor_eval import metrics
from analyse import paired, citation_audit, seed_spread


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def merge_candidate(baseline, chunks):
    """Reject duplicate or missing student/seed pairs rather than selecting a favorable subset."""
    keys = lambda group: [(s['student'], s['seed']) for s in group]
    expected = keys(baseline)
    actual = [s for group in chunks for s in group]
    found = keys(actual)
    if len(set(expected)) != len(expected) or len(set(found)) != len(found):
        raise ValueError('Duplicate student/seed evidence')
    if set(found) != set(expected):
        raise ValueError('Incomplete or unmatched candidate evidence')
    return sorted(actual, key=lambda s: (s['student'], s['seed']))


def main():
    root = SOURCE / 'Directions/m3_runs/v2/live'
    index = load(root / 'INDEX.json')
    raw = {}; receipts = []
    for arm, job in index['jobs'].items():
        if arm.startswith('e2_') or job.get('status') != 'completed':
            continue
        directory = Path(job['run']); manifest = load(directory / 'manifest.json')
        raw[arm] = rows(directory / 'sessions.jsonl')
        receipts.append({'condition': arm, 'run_id': manifest['run_id'], 'manifest_sha256': sha(directory / 'manifest.json'),
            'sessions_sha256': sha(directory / 'sessions.jsonl'), 'git': manifest['git'],
            'config_sha256': manifest['config']['sha256'], 'app_config_sha256': manifest['app_config_sha256'],
            'code_sha256': manifest['code_sha256'], 'data_sha256': manifest['data'], 'gate': manifest['gate']})
    earlier = load(Path(index['jobs']['e3_after_budget_tranche12']['run']) / 'manifest.json')
    later = load(Path(index['jobs']['e3_after_remaining4']['run']) / 'manifest.json')
    changed = sorted(name for name, digest in earlier['code_sha256'].items() if later['code_sha256'].get(name) != digest)
    assert set(changed) == {'tutor_eval/harness.py', 'tutor_eval/provider_budget.py'}
    for name in changed:
        revision=later['git']['commit']
        assert re.fullmatch(r'[0-9a-f]{40}',revision)
        blob=subprocess.check_output(['git','-C',str(CODE),'show',revision+':src/'+name])
        candidates={hashlib.sha256(blob).hexdigest(),hashlib.sha256(blob.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()}
        assert later['code_sha256'][name] in candidates, name
    assert earlier['data'] == later['data'] and earlier['fixture_input_sha256'] == later['fixture_input_sha256']
    assert earlier['app_config_sha256'] == later['app_config_sha256'] and earlier['playbook_sha256'] == later['playbook_sha256']
    assert not later['git']['uncommitted_changes']
    combined = merge_candidate(raw['c2'], [raw['e3_after_budget_tranche12'], raw['e3_after_remaining4']])
    assert len(combined) == 48
    groups = {arm: raw[arm] for arm in ['c0', 'c1', 'c2', 'memory_off', 'direct_answers']}
    groups['e3_after_full'] = combined
    catalogue = {m['misconception_id']: m for m in rows(CODE / 'content/dataset-v0.10.0/misconceptions.jsonl')}
    conditions = []
    for arm, sessions in groups.items():
        summary = metrics.summarize(sessions, catalogue, (.4, 1.6))
        keys = ['sessions', 'turns', 'failures', 'timeouts', 'diagnosis', 'leaks', 'quiz', 'task_success',
                'checked_practice', 'policy', 'latency_ms', 'cost_usd']
        conditions.append({'condition': arm, **{key: summary[key] for key in keys},
            'provider_requests': sum(s['llm_calls'] for s in sessions),
            'provider_reported_usd': sum(s.get('provider_reported_usd', 0) for s in sessions),
            'citation_integrity': citation_audit(sessions), 'seed_spread': seed_spread(sessions),
            'quiz_answer_match_sessions': sum(any(t.get('quiz_contamination') for t in s['turns']) for s in sessions)})
    comparisons = {}
    for name, left, right, seed in [('C2_minus_C1', 'c1', 'c2', None), ('C2_minus_C0', 'c0', 'c2', None),
            ('E3_full_minus_C2', 'c2', 'e3_after_full', None), ('memory_on_minus_off', 'memory_off', 'c2', 1),
            ('telling_minus_hints', 'c2', 'direct_answers', 1)]:
        comparisons[name] = {metric: paired(groups[left], groups[right], fn, seed) for metric, fn in [
            ('quiz_gain', lambda s: metrics.session_view(s)['gain']),
            ('success_proxy', lambda s: int(metrics.session_view(s)['task_success'])),
            ('cleared_misconceptions', lambda s: len(s['cleared']))]}
    old_path = SOURCE / 'Directions/m3_runs/provider_budget.json'
    extension_path = SOURCE / 'Directions/m3_runs/provider_budget_extension_e3.json'
    old, extra = load(old_path), load(extension_path)
    approval_path = root / 'E3_EXTENSION_APPROVAL.json'; approval = load(approval_path)
    assert sha(old_path) == approval['previous_ledger_sha256']
    assert approval['status'] == 'approved' and approval['additional_requests'] == 50 and approval['max_additional_usd'] == .03
    assert len(old['attempts']) == 902 and len(extra['attempts']) <= 50
    assert all(a['status'] == 'completed' and a['billed_usd'] is not None for a in old['attempts'] + extra['attempts'])
    assert sum(a['accounted_usd'] for a in extra['attempts']) <= .03
    money = lambda ledger: sum(a['billed_usd'] for a in ledger['attempts'])
    budget = {'original_prior_calls': 98, 'original_new_calls': len(old['attempts']),
        'extension_calls': len(extra['attempts']), 'total_calls': 1000 + len(extra['attempts']), 'approved_total_limit': 1050,
        'extension_request_cap': 50, 'extension_usd_cap': .03, 'extension_provider_usd': money(extra),
        'known_new_provider_usd': money(old) + money(extra), 'prior_98_cost': 'unmeasured, excluded',
        'errors': sum(a['status'] == 'error' for a in old['attempts'] + extra['attempts']),
        'refused': old['refused'] + extra['refused'], 'original_ledger_sha256': sha(old_path),
        'extension_ledger_sha256': sha(extension_path), 'approval_receipt_sha256': sha(approval_path),
        'approval_quote': approval['approval_quote'], 'unused_extension_requests': 50 - len(extra['attempts'])}
    sensitivity_path = CODE / 'Docs/m4/POST_COPY_SENSITIVITY_E3_COMPLETE.json'
    result = {'scope': 'complete_original_development_matrix_not_human_approved_final_study',
        'development_E1_E2_E3_E4_execution_complete': True, 'formal_M3_M4_accepted': False,
        'conditions': conditions, 'paired_comparisons': comparisons, 'budget': budget, 'run_receipts': receipts,
        'E3_original_sessions': 48, 'E3_pending_sessions': 0, 'unique_tutoring_sessions': sum(len(s) for s in groups.values()),
        'security': load(root / 'ANALYSIS.json')['security'], 'original_request_1000_report': 'beta-m4-request-cap-1000 (dffdde2)',
        'post_copy_sensitivity': load(sensitivity_path) if sensitivity_path.exists() else None,
        'human_reviews': 0, 'final_preregistration': 'draft', 'independent_final_authorship': False,
        'measurement_limitation': 'Post-answer numeric matches trigger simulator copying; quiz change is not a clean learning estimate.',
        'source_deviation': 'Only previously committed approval-receipt wiring/budget extension differs from frozen v2 runtime; new run a463675 was clean, app config/data/playbook unchanged.',
        'source_integrity': {'teaching_module_hashes_unchanged': True, 'changed_runtime_modules': changed,
            'data_fixture_app_config_playbook_hashes_unchanged': True, 'extension_run_clean': True},
        'analysis_script_sha256': sha(Path(__file__))}
    out = CODE / 'Docs/m4';out.mkdir(exist_ok=True)
    with (out / 'E3_COMPLETE_CONDITIONS.csv').open('w', encoding='utf-8', newline='') as csv_file:
        fields = ['condition','sessions','success_proxy','diagnosis_recall','quiz_mean_gain','full_leak_turns','partial_leak_turns','provider_requests','provider_usd','flagged_quiz_sessions']
        writer = csv.DictWriter(csv_file, fieldnames=fields); writer.writeheader()
        for r in conditions:
            writer.writerow({'condition':r['condition'],'sessions':r['sessions'],'success_proxy':r['task_success'],
                'diagnosis_recall':r['diagnosis']['recall'],'quiz_mean_gain':r['quiz']['mean_gain'],
                'full_leak_turns':r['leaks']['full_turns'],'partial_leak_turns':r['leaks']['partial_turns'],
                'provider_requests':r['provider_requests'],'provider_usd':r['provider_reported_usd'],
                'flagged_quiz_sessions':r['quiz_answer_match_sessions']})
    (out / 'E3_COMPLETE_RESULTS.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    labels = {'c0': 'C0', 'c1': 'C1', 'c2': 'C2', 'memory_off': 'Memory off', 'direct_answers': 'Telling', 'e3_after_full': 'E3 full candidate'}
    lines = ['# Complete M3/M4 development results - 5 November 2026', '',
        '**The original development E1-E4 execution is complete, including all 48 E3 candidate sessions. Formal milestone acceptance remains pending human review, final preregistration and independent/team evidence.**', '',
        '## Approved E3 completion', '',
        f"The last 12 sessions used {budget['extension_calls']} requests and USD {budget['extension_provider_usd']:.7f}, within the approved 50-request / USD 0.03 extension. Both source batches are retained: 36 original + 12 new = 48 unique student/seed pairs, exactly matching the C2 cohort (16 source cards, seeds 1/2/3). No duplicate, missing or extra pair was selected. The new run passed with zero failures/timeouts/model errors on clean local commit a463675. Runtime teaching behaviour, app configuration, data and unreviewed candidate playbook are unchanged; only the recorded harness/budget approval wiring differs from the v2 frozen revision. The later batch and approval deviation are disclosed rather than treated as one uninterrupted run.", '',
        '## Conditions', '',
        '| Condition | Sessions | Checked practice correct/submitted | Success proxy | Diagnosis recall | Mean simulated quiz change | Full/partial leak turns | Provider USD |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in conditions:
        lines.append(f"| {labels[r['condition']]} | {r['sessions']} | {r['checked_practice']['checked_correct']}/{r['checked_practice']['submitted']} | {r['task_success']}/{r['sessions']} | {r['diagnosis']['recall']:.3f} | {r['quiz']['mean_gain']:.3f} | {r['leaks']['full_turns']}/{r['leaks']['partial_turns']} | ${r['provider_reported_usd']:.7f} |")
    lines += ['', 'E1/E3 use seeds 1/2/3; E4 uses seed 1 and its matched C2 subset. All arms share substantial heuristic code and code scoring. All primary outcomes, failures and contamination flags are retained. Repeats are not independent new learners.', '',
        '## Paired primary estimates', '', 'Student-cluster bootstrap: 2,000 resamples, seed 0, matched student/seed pairs.', '',
        '| Quiz-change difference | Matched sessions/cards | Estimate | Bootstrap 95% interval |', '| --- | ---: | ---: | --- |']
    for name, r in comparisons.items():
        v = r['quiz_gain'];lo, hi = v['cluster_bootstrap_ci95']
        lines.append(f"| {name} | {v['matched_sessions']}/{v['student_clusters']} | {v['difference']:.4f} | [{lo:.4f}, {hi:.4f}] |")
    e3 = comparisons['E3_full_minus_C2']
    snapshots = sum(r['citation_integrity']['snapshots'] for r in conditions)
    valid = sum(r['citation_integrity']['valid_snapshot_hash'] for r in conditions)
    matches = sum(r['quiz_answer_match_sessions'] for r in conditions)
    assert snapshots == valid
    assert sum(r['citation_integrity']['same_chapter'] for r in conditions) == snapshots
    assert sum(r['citation_integrity']['registered_source_text_match'] for r in conditions) == snapshots
    lines += ['', f"E3 has success-proxy difference {e3['success_proxy']['difference']:.4f} and cleared-misconception difference {e3['cleared_misconceptions']['difference']:.4f}. The primary quiz numbers are synthetic and subject to the copying limitation below, not evidence of human learning.", '',
        '## Measurement validity and sensitivity', '',
        f"Code-flagged post-answer matches occur in {matches}/{result['unique_tutoring_sessions']} sessions. Generic numeric instructions can trigger them, and the frozen harness then allows the simulator to copy those post answers. No post-question text exposure was detected. Numeric flags have no human semantic calibration. Keep the original quiz figures as recorded outcomes; they are not clean learning estimates.", '',
        'The [complete offline sensitivity](POST_COPY_SENSITIVITY_E3_COMPLETE.md) replays the same recorded tutor/grade trajectories, first verifying the original simulator outcomes, then disabling all post-quiz copying. It is a post-hoc intervention that can remove genuine as well as false disclosure and changes later quiz random draws; it does not replace the primary design or establish a calibrated detector.', '',
        '## Citations, safety and operations', '',
        f"Across all {result['unique_tutoring_sessions']} tutoring sessions, {valid}/{snapshots} citation snapshots match their recorded hashes, chapter and registered source text. These are mechanical checks; semantic faithfulness remains unmeasured. Retrieval and golden-reference consistency are unchanged from the [original report](RESULTS.md).", '',
        'E2 is unchanged: guards-on has 0/18 measured attack violations, guards-off 1/18; both have 0/35 measured false blocks. Each condition has 27/80 unknown outcomes. All-40 attack bounds are [0, 0.55] on and [0.025, 0.575] off; false-block bounds [0, 0.125] do not establish the 10% target. These are seen development attacks and selected input/output guards, with tool permissions/context screening still enforced.', '',
        '| Condition | Tool calls/denied | Turn p50/p95 ms | Failures/timeouts/model errors |', '| --- | ---: | ---: | ---: |']
    for r in conditions:
        lines.append(f"| {labels[r['condition']]} | {r['policy']['tool_calls']}/{r['policy']['denied_tool_calls']} | {r['latency_ms']['p50']}/{r['latency_ms']['p95']} | {r['failures']}/{r['timeouts']}/{r['policy']['llm_errors']} |")
    lines += ['', '## Budget, provenance and remaining gates', '',
        f"Total provider attempts: **{budget['total_calls']}/1050 approved** (98 prior + 902 original continuation + {budget['extension_calls']} approved E3 completion). Known continuation cost is **USD {budget['known_new_provider_usd']:.7f}**, excluding unmeasured prior-98 money. All new attempts expose provider cost; no voice/judge calls. {budget['unused_extension_requests']} extension requests remain unused; this approval was solely for completing these E3 sessions, and no further calls are needed or scheduled. The original wallet remains byte-identical and the extension is linked by hash. Exact IDs, hashes, seed spread, cost coverage and intervals are in E3_COMPLETE_RESULTS.json.", '',
        'The [original 1,000-request report](RESULTS.md), source tag beta-m4-request-cap-1000 and private archive preserve the prior boundary. Raw transcripts, cards, keys, wallets, approval receipt and per-session replay evidence remain ignored outside Git.', '',
        'Data remains 16 development source cards, 22 quiz pairs/44 records and 17 seeded misconception types; 24 candidate-final cards/30 pairs remain unrun and lack independent final authorship. Eight seeded diagnosis types are outside the runtime catalogue, and five associations cannot show in assigned quiz scores. More simulated repeats do not resolve those limits.', '',
        'Still pending: R2 final preregistration decision, actual teacher lesson acceptance/rejection, independent human raters and semantic citation/safety review, independent final content/new attacks, judge calibration or an explicit approved scoring limitation, a real failed-CI demonstration if retained as required, and independent clean-machine/team verification. Human approvals and formal M3/M4 acceptance are not inferred from these complete development runs. No push was made.']
    (out / 'E3_COMPLETE_RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    for name in ['E3_COMPLETE_RESULTS.json', 'E3_COMPLETE_RESULTS.md', 'E3_COMPLETE_CONDITIONS.csv']:
        shutil.copy2(out / name, SOURCE / 'Docs/m4' / name)
    print(json.dumps({'development_complete': True, 'sessions': result['unique_tutoring_sessions'], 'E3_sessions': 48,
        'citations': snapshots, 'flagged_sessions': matches, 'budget': budget, 'E3_comparisons': e3}, indent=2))


if __name__ == '__main__':
    main()
