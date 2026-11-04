"""Project saved study evidence into shareable M3/M4 results. Never makes a model request."""
from __future__ import annotations
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',CODE)).resolve()
sys.path.insert(0,str(CODE/'src'))
from tutor_eval import metrics


def load(path):return json.loads(path.read_text(encoding='utf-8'))
def rows(path):return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=SOURCE/'Directions/m3_runs/v2';live=root/'live';analysis=load(live/'ANALYSIS.json');index=load(live/'INDEX.json')
    freeze=load(CODE/'Docs/m3/BEHAVIOUR_FREEZE.json');wallet=load(SOURCE/'Directions/m3_runs/provider_budget.json')
    out=CODE/'Docs/m4';out.mkdir(exist_ok=True);(SOURCE/'Docs/m4').mkdir(exist_ok=True)
    sessions={};manifests={};integrity=[];run_table=[]
    for arm,job in index['jobs'].items():
        if job.get('status')!='completed':continue
        directory=Path(job['run']);manifest=load(directory/'manifest.json');manifests[arm]=manifest
        expected=dict(freeze['code_config_protocol_sha256']);git_covered=[]
        for name,digest in manifest['code_sha256'].items():
            if 'src/'+name not in expected:
                current=(CODE/'src'/name).read_bytes()
                committed=subprocess.check_output(['git','-C',str(CODE),'show','12d541e:src/'+name])
                if current.replace(b'\r\n',b'\n')!=committed.replace(b'\r\n',b'\n'):
                    raise ValueError('Unlisted source differs from the recorded Git revision: '+name)
                expected['src/'+name]=hashlib.sha256(current).hexdigest();git_covered.append(name)
        mismatches=[name for name,digest in manifest['code_sha256'].items() if expected['src/'+name]!=digest]
        if mismatches:raise ValueError('Recorded behaviour differs from the v2 lock: '+str(mismatches))
        integrity.append({'condition':arm,'run_id':manifest['run_id'],'manifest_sha256':sha(directory/'manifest.json'),
                          'behaviour_matches_v2_lock':True,'additional_modules_verified_against_tag':git_covered,'git':manifest['git']})
        if arm.startswith('e2_'):continue
        s=rows(directory/'sessions.jsonl');sessions[arm]=s;summary=manifest['summary']
        shown={t['active_item'] for one in s for t in one['turns'] if t.get('active_item')}
        run_table.append({'condition':arm,'run_id':manifest['run_id'],'sessions':len(s),'turns':summary['turns'],
            'model_requests':sum(one['llm_calls'] for one in s),'success_proxy':summary['task_success'],
            'diagnosis_recall':summary['diagnosis']['recall'],'mean_quiz_gain':summary['quiz']['mean_gain'],
            'full_leak_turns':summary['leaks']['full_turns'],'partial_leak_turns':summary['leaks']['partial_turns'],
            'practice_submitted':summary['checked_practice']['submitted'],'practice_checked_correct':summary['checked_practice']['checked_correct'],
            'unique_registered_practice_shown':len(shown),'unique_prequiz_items':len({q['question_id'] for one in s for q in one['pre']}),
            'unique_postquiz_items':len({q['question_id'] for one in s for q in one['post']}),
            'provider_reported_usd':sum(one.get('provider_reported_usd',0) for one in s),
            'provider_cost_coverage':sum(one.get('provider_cost_coverage',0) for one in s),
            'estimated_usd':summary['cost_usd']['total'],'failures':summary['failures'],'timeouts':summary['timeouts'],
            'llm_errors':summary['policy']['llm_errors'],'latency_ms':summary['latency_ms'],
            'tool_calls':summary['policy']['tool_calls'],'denied_tool_calls':summary['policy']['denied_tool_calls'],
            'quiz_answer_match_witnesses':summary['leaks']['quiz_contamination'],
            'quiz_answer_match_sessions':sum(any(t.get('quiz_contamination') for t in one['turns']) for one in s),
            'post_question_exposures':summary['leaks']['post_question_exposures'],
            'citations':analysis['runs'][arm]['citations'],'seed_spread':analysis['runs'][arm]['seed_spread']})
    selected={s['student'] for s in sessions['e3_after_budget_tranche12']}
    matched_base=[s for s in sessions['c2'] if s['student'] in selected]
    e4_base=[s for s in sessions['c2'] if s['seed']==1]
    cohort_summary=lambda chosen:{'sessions':len(chosen),'mean_gain':statistics.fmean(metrics.session_view(s)['gain'] for s in chosen),
                                 'success_proxy':sum(metrics.session_view(s)['task_success'] for s in chosen)}
    attempts=wallet['attempts'];cost=sum(a['billed_usd'] for a in attempts if a['billed_usd'] is not None)
    assert wallet['policy']['prior_calls']+len(attempts)==1000 and wallet['refused']==0
    assert all(a['status']=='completed' and a['billed_usd'] is not None for a in attempts)
    result={'scope':'synthetic_development_engineering_study_not_final_qualification','behaviour_commit':'12d541ed8dd4716bbcfee2a74bcb4215920a13fc',
        'local_tag':'beta-m3-behaviour-v2','date':'2026-11-05','conditions':run_table,
        'matched_C2_for_E3_tranche':cohort_summary(matched_base),'matched_C2_seed1_for_E4':cohort_summary(e4_base),
        'paired_comparisons':analysis['paired_comparisons'],'security':analysis['security'],
        'data_sufficiency':load(CODE/'Docs/m3/DATA_SUFFICIENCY.json'),'runtime_scope':load(root/'validation/RUNTIME_SCOPE.json'),
        'retrieval':load(root/'validation/RETRIEVAL.json'),'golden_consistency':load(root/'validation/GOLDEN_CONSISTENCY.json'),
        'reproducibility':load(root/'validation/REPRODUCIBILITY.json'),
        'dataset_integrity':load(root/'validation/DATASET_INTEGRITY.json'),
        'post_copy_sensitivity':load(CODE/'Docs/m4/POST_COPY_SENSITIVITY.json') if (CODE/'Docs/m4/POST_COPY_SENSITIVITY.json').exists() else None,
        'budget':{'approved_total_requests':1000,'prior_requests':98,'new_requests':len(attempts),'total_requests':1000,
                  'provider_errors':0,'refused_over_limit':0,'new_provider_reported_usd':cost,
                  'cost_coverage':len(attempts),'prior_98_cost':'not_exposed_unmeasured',
                  'all_time_cost':'unmeasured_prior_98_not_included','ledger_sha256':sha(SOURCE/'Directions/m3_runs/provider_budget.json')},
        'E3_original_design':load(live/'E3_BUDGET_TRANCHE.json'),
        'review_packet':load(live/'review_packet_context_v2/MANIFEST.json'),
        'integrity':integrity,'human_reviews':0,'independent_final_authorship':False,'final_preregistration_status':'draft',
        'judge_calibrated':False,'original_M4_full_design_complete':False,
        'analysis_code_sha256':{'analysis':sha(CODE/'scripts/m3/analyse.py'),'delivery':sha(Path(__file__)),
                               'review_packet':sha(CODE/'scripts/m3/review_packet.py'),'calibration':sha(CODE/'scripts/m3/prepare_calibration.py')}}
    (out/'RESULTS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    with (out/'condition_results.csv').open('w',newline='',encoding='utf-8') as f:
        fields=[k for k in run_table[0] if k not in ['latency_ms','citations','seed_spread']]
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:r[k] for k in fields} for r in run_table)
    labels={'c0':'C0 fixed teaching','c1':'C1 single controller','c2':'C2 graph','memory_off':'Memory off','direct_answers':'Telling','e3_after_budget_tranche12':'E3 candidate tranche'}
    lines=['# M3/M4 development results - 5 November 2026','',
        'Local behaviour checkpoint and measured development results are ready. **Formal M3/M4 acceptance remains open:** the final preregistration is draft, human/independent review is absent, and 12 of the original 48 live E3 candidate sessions remain pending the exhausted request allowance.','',
        '## Engineering checkpoint','',
        '- Frozen teaching behaviour: `12d541e`, local tag `beta-m3-behaviour-v2`, on local `Beta`. All recorded run code hashes match the v2 lock or the exact recorded Git revision; source data and original v1 evidence are preserved.',
        '- 496 offline regression tests passed on that behaviour; six two-card experiment smoke configurations and all three CI evaluation gates passed. C1/C2 smoke/full replays match 4/4 sessions after excluding identifiers/timing. The v2 safety change left all 224 offline core trajectories unchanged.',
        '- All 158 frozen-build files and seven public copies match their recorded hashes; no final-selection freeze was performed.',
        '- Baseline GitHub Actions [passed for 3dd518a](https://github.com/ksharp05/Socratic-AI-Tutor/actions/runs/41908712265). Beta has remained local, so it has no remote CI run.','',
        '## Measured live conditions','',
        'All use gpt-4.1-mini, template student voice, code scoring and at most eight tutor turns. E1 uses 16 development source cards and seeds 1,2,3. E4 uses seed 1. E3 uses a budget-limited, fixed-seed first tranche of 12 cards (four per chapter) and all three seeds; its C2 comparator is the same 36 sessions. The candidate playbook is unreviewed.','',
        '| Condition | Sessions | Checked correct / submitted practice | Success proxy | Diagnosis recall | Mean simulated quiz change | Full / partial leak turns | Provider USD |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for row in run_table:
        lines.append(f"| {labels[row['condition']]} | {row['sessions']} | {row['practice_checked_correct']}/{row['practice_submitted']} | {row['success_proxy']}/{row['sessions']} | {row['diagnosis_recall']:.3f} | {row['mean_quiz_gain']:.3f} | {row['full_leak_turns']}/{row['partial_leak_turns']} | ${row['provider_reported_usd']:.6f} |")
    lines += ['',f"The matched C2 baseline for E3 has mean quiz change {result['matched_C2_for_E3_tranche']['mean_gain']:.3f}; the C2 seed-1 baseline for E4 is {result['matched_C2_seed1_for_E4']['mean_gain']:.3f}. Use these matched subsets rather than the overall C2 mean.",'',
        'The success proxy means a seeded misconception was named, no full leak or contamination occurred, post-quiz score did not decline, and no execution failure/timeout occurred. It is not a count of solved problems. Quiz changes are numbers of correct items under the simulator rules, not measured human learning. Telling intentionally discloses registered practice answers in isolated stores and invokes the simulator copying rule.','',
        '## Paired estimates','',
        'Student-cluster bootstrap, 2,000 resamples, seed 0; repeats from a student stay together. Intervals are empirical development uncertainty, with sparse positive cases and shared code. No p-values are used.','',
        '| Difference in mean simulated correct items | Matched sessions / source cards | Estimate | Bootstrap 95% interval |',
        '| --- | ---: | ---: | --- |']
    for key,label in [('E1_C2_minus_C1','C2 minus C1'),('E1_C2_minus_C0','C2 minus C0'),('E3_budget_tranche_minus_matched_before','E3 candidate minus matched C2'),('E4a_memory_on_minus_off','Memory on minus off'),('E4b_telling_minus_hints','Telling minus hints')]:
        item=analysis['paired_comparisons'][key]['quiz_gain'];ci=item['cluster_bootstrap_ci95']
        lines.append(f"| {label} | {item['matched_sessions']} / {item['student_clusters']} | {item['difference']:.4f} | [{ci[0]:.4f}, {ci[1]:.4f}] |")
    lines += ['', 'C2 did not improve the recorded success proxy over C0/C1. Diagnosis recall is low in all arms. The E3 tranche has no difference in the success proxy or number of cleared misconceptions. Small quiz differences can reflect the synthetic mastery/guessing/clearing rules and wording-sensitive targeting proxy; these results establish no human learning advantage.','',
        '']
    insertion=lines.index('## Paired estimates')
    flag_lines=['## Quiz-answer match and copying limitation','',
        'The frozen checker flags post-quiz answer matches in 83/212 study sessions. Some recorded matches occur in generic numeric instructions, even though no post-question text exposure was detected. This is an uncalibrated code flag, not a human-confirmed answer disclosure. The harness adds every flagged post item to the simulator told set, enabling its answer-copying rule. Consequently the recorded quiz changes in every arm can include copying triggered by numeric overlap; they are not clean estimates of learning. Primary outcomes and all flagged sessions remain included unchanged. A context-sensitive checker and fresh, separately frozen validation are required before interpreting learning effects.','',
        '| Condition | Match witnesses | Flagged sessions | Post-question text exposures |',
        '| --- | ---: | ---: | ---: |']
    for row in run_table:
        flag_lines.append(f"| {labels[row['condition']]} | {row['quiz_answer_match_witnesses']} | {row['quiz_answer_match_sessions']}/{row['sessions']} | {row['post_question_exposures']} |")
    if (out/'POST_COPY_SENSITIVITY.md').exists():
        flag_lines += ['', 'An [offline fixed-trajectory sensitivity](POST_COPY_SENSITIVITY.md) exactly reproduces the recorded simulator outcomes for all 212 sessions using saved tutor replies/grades, then disables only post-quiz copying. C0/C1/C2 each have mean quiz change 0.104 under this intervention; the E3 tranche is 0.056. This post-hoc analysis is reported separately and does not replace primary outcomes or establish learning.']
    lines[insertion:insertion]=flag_lines+['']
    lines += ['## Operations','', '| Condition | Tool calls / denied | Turn p50 / p95 ms | Failures / timeouts / model errors |', '| --- | ---: | ---: | ---: |']
    for row in run_table:
        lines.append(f"| {labels[row['condition']]} | {row['tool_calls']}/{row['denied_tool_calls']} | {row['latency_ms']['p50']}/{row['latency_ms']['p95']} | {row['failures']}/{row['timeouts']}/{row['llm_errors']} |")
    lines += ['', 'Latency is the observed local turn latency for these fixed runs; template voice and no judge requests. It is not a deployment load test.', '', '## Citation snapshots and retrieval', '']
    snapshots=sum(row['citations'].get('snapshots',0) for row in run_table)
    valid=sum(row['citations'].get('valid_snapshot_hash',0) for row in run_table)
    lines += [f'Across the 212 tutoring sessions (excluding the pilot and security overlays), **{valid}/{snapshots} citation snapshots** have valid content hashes; all match their chapter and registered source text. These checks establish mechanical integrity, not semantic faithfulness. The 15 assistant-labelled development retrieval queries score Recall@5 **0.9278**, MRR **0.8356**, support-group@5 **1.0000** through the actual 22-card chapter-pinned backend. Human relevance/faithfulness remains unmeasured. All 160 development golden references match the two-route kernel; this is internal consistency with shared dependencies, not independent factual or tutor-answer accuracy.','',
        '## Safety','',
        '| Selected guards | Measured attack violations | Measured false blocks | Unsupported/semantic unknown | All-40 attack-rate bounds |',
        '| --- | ---: | ---: | ---: | --- |']
    for key,label in [('e2_on','On'),('e2_off','Off')]:
        sec=analysis['security'][key];a,c=sec['bounds']['attack'],sec['bounds']['control'];bounds=a['all_scheduled_rate_bounds']
        lines.append(f"| {label} | {a['positive']}/{a['measured']} | {c['positive']}/{c['measured']} | {sec['summary']['unsupported']}/80 | [{bounds[0]:.3f}, {bounds[1]:.3f}] |")
    lines += ['', 'Both conditions retain tool permissions and publication authority; contextual adapter screening also remains part of the implementation. The ablation switches the existing application input/output guard flag, not every defence layer. Forty attacks and forty controls per condition are previously seen development probes. The six retrieved/tool-result cases are delivered through isolated returned-data overlays; their semantic attack expectations remain unmeasured. False-block bounds over all 40 controls are [0, 0.125], so the 10% target is not established for every scheduled control.','',
        'V1 missed a known urgent-distress phrase. V2 added explicit first-person unsafe/not-safe recognition and passed its positive, mathematical-control and API-boundary regressions. The revealed case passes with guards on and fails with the selected flag off. Original v1 results are retained; this is a known-case regression, not an independent safety test.','',
        '## Cost and allowance','',
        f'Exactly **902 new provider attempts**, all completed without provider errors or over-limit refusals, consumed **${cost:.7f} provider-reported cost**. With the earlier 98 calls, the approved **1,000/1,000** allowance is exhausted. All 902 new costs were exposed by the provider; the prior 98 monetary costs are unmeasured and are not included in this total. The pilot is counted in the allowance/cost but excluded from the condition tables. No voice or judge requests were made. Token-price estimates remain separately available in JSON. Reference prices checked 5 November: [OpenRouter](https://openrouter.ai/openai/gpt-4.1-mini), USD 0.40/M input and 1.60/M output; measured cost is the primary monetary evidence.','',
        '## Data sufficiency and remaining acceptance','',
        'The available bank is sufficient for these bounded engineering runs. It is not sufficient for independent final qualification: 16 development source cards cover 17 seeded misconception types, while eight seeded types lack a runtime diagnosis adapter and five card/misconception associations are not observable in their assigned quiz scores. The connected graph exposes 131 practice items across four task types, 12 quiz items, 22 source concepts/cards and nine diagnosis types; the larger 665-item bank and textbook holdings are broader than the connected runtime. Actual exposure counts and per-seed spread are in `RESULTS.json` and `condition_results.csv`.',
        '', 'There are 24 candidate-final source cards and 30 candidate-final quiz pairs; no candidate-final run or independent authorship is claimed. The original final preregistration remains draft. A separate human-review packet has 60 recorded turns plus three existing AI-drafted calibration fixtures (63 items, proposed leak strata 36 none / 7 partial / 20 full). All human labels are blank. The fixtures are excluded from experimental metrics. Human lesson acceptance/rejection, independent raters and final authors, semantic citation review and judge calibration remain external gates.',
        '', 'The original full E3 design remains incomplete: 36/48 candidate sessions are measured; four cards / 12 sessions remain. Their matched-C2 request estimate is 36. A ready-to-review remaining configuration and a pending-only approval receipt propose up to 50 additional provider attempts, capped at USD 0.03. No extra allowance or human approval has been inferred, and no further call will be sent without an explicit approved receipt linked to the intact original ledger.',
        '', 'Exact run IDs, hashes, per-seed statistics, paired intervals, operations and scope are in [RESULTS.json](RESULTS.json). Raw transcripts, wallets, data exports and rating CSVs remain private under the canonical workspace’s ignored `Directions/m3_runs/v2/`.']
    if (out/'development_results.png').exists():
        at=lines.index('## Citation snapshots and retrieval')
        lines[at:at]=['![Paired score intervals and code-detected disclosure rates](development_results.png)','']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for p in out.iterdir():
        if p.is_file():shutil.copy2(p,SOURCE/'Docs/m4'/p.name)
    print(json.dumps({'report':str(out/'RESULTS.md'),'live_tutoring_sessions_excluding_pilot':sum(r['sessions'] for r in run_table),
                      'citation_snapshots':snapshots,'provider_usd':cost,'all_recorded_behaviour_matches_lock':True},indent=2))


if __name__=='__main__':main()
