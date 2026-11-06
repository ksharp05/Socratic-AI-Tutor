"""Reproduce R4 review and task-pool audit aggregates from frozen evidence, offline."""
from __future__ import annotations
import argparse,hashlib,json,os,statistics
from collections import Counter
from pathlib import Path
CODE=Path(__file__).resolve().parents[2];SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()
ROOT=SOURCE/'Directions/product_quality/v3';DEST=CODE/'Docs/product_quality/v3'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def round_summary(number):
    root=ROOT/f'r4_review_{number:02d}';protocol=read(root/'PROTOCOL.json');index=read(root/'attempt_01/INDEX.json')
    assert index['status']=='completed' and len(index['cases'])==30
    assert index['protocol_sha256']==sha(root/'PROTOCOL.json')
    assert sha(root/'cases.json')==protocol['cases_sha256'] and sha(root/'mapping_private.json')==protocol['mapping_sha256']
    mapping=read(root/'mapping_private.json');actual={};controls=[];invalid_quotes=0
    for receipt in index['cases']:
        path=root/'attempt_01'/receipt['id']/'review.json';assert sha(path)==receipt['review_sha256'] and sha(path.with_name('raw.txt'))==receipt['raw_sha256']
        row=read(path);assert not row['schema_errors']
        invalid_quotes+=sum(bool(i['validation_errors']) for i in row['issues'])
        if mapping[receipt['id']]['control']:controls.append(row)
        else:actual[receipt['id']]=row
    mechanical=read(root/'MECHANICAL_CHECKS.json')
    assert mechanical['originals_verified']==18 and mechanical['altered_controls_rejected']==12
    summary={'originals':18,'controls':12,'original_math_labels':dict(Counter(r['math_status'] for r in actual.values())),'mean_clarity':statistics.mean(r['clarity_score'] for r in actual.values()),'method_match_labels':dict(Counter(r['method_match'] for r in actual.values())),'controls_flagged_incorrect':sum(r['math_status']=='incorrect' for r in controls),'controls_missed':sum(r['math_status']=='correct' for r in controls),'unbound_issue_quotes':invalid_quotes,'mechanical_originals_verified':18,'mechanical_controls_rejected':12,'provider_calls':index['budget']['provider_attempts'],'provider_reported_usd':index['budget']['provider_reported_usd'],'example_code_sha256':protocol['example_code_sha256'],'protocol_sha256':sha(root/'PROTOCOL.json')}
    return summary,actual
def build():
    before,a=round_summary(1);after,b=round_summary(2);assert a.keys()==b.keys()
    paired={'improved':sum(b[k]['clarity_score']>a[k]['clarity_score'] for k in a),'unchanged':sum(b[k]['clarity_score']==a[k]['clarity_score'] for k in a),'lower':sum(b[k]['clarity_score']<a[k]['clarity_score'] for k in a)}
    cost=read(ROOT/'r4_review_02/COST_SNAPSHOT.json');phase=cost['phase']
    for entry in phase['batch_allocations']:
        assert entry['status'].startswith('completed')
        if 'ledger_sha256' in entry:assert sha(SOURCE/entry['wallet'])==entry['ledger_sha256']
    audit=read(ROOT/'r4_math_audit_03/RESULTS.json');assert audit['status']=='completed' and audit['cases']==900 and audit['source_sha256']==after['example_code_sha256']
    report={'scope':'Paired AI development feedback on the same examples, not held-out evidence or teacher acceptance','before':before,'after':after,'paired_clarity':paired,'machine_audit':{'same_seeded_inputs':900,'valid_examples_verified':892,'invalid_inputs_rejected':8,'independent_oracle':'Fraction formulas, AP summation, polynomial substitution and Vieta'},'human_reviews':0,'runtime_integration':'R3 owner still needs to connect the tools; API/UI overview is read-only','budget_snapshot':{'total_provider_attempts':cost['total_provider_attempts'],'new_calls':60,'new_reported_usd':before['provider_reported_usd']+after['provider_reported_usd'],'phase_provider_reported_usd':phase['actual_spend_usd'],'phase_accounted_usd':phase['accounted_phase_usd'],'remaining_accounted_ceiling_usd':10-phase['accounted_phase_usd']},'review_limit':'AI misses known incorrect controls and emits unbound/contradictory issues. It cannot grade numeric answers, override verification or grant publication/teacher approval.'}
    md='# R4 worked-example improvement\n\nThe v2 renderer explains each calculation, completes zero-product equations and ends with a task-specific transfer question. Checked steps bind the displayed text; existing role/scope/quiz/answer guards remain enforced. Natural sentences replace mixed notation such as division by the word two. Versioned example IDs prevent reuse under an older renderer.\n\n'
    md+='| Check | Before | After |\n| --- | --- | --- |\n'
    md+=f"| AI mean clarity, same 18 examples (1-5) | {before['mean_clarity']:.3f} | {after['mean_clarity']:.3f} |\n| Known wrong controls flagged by AI | {before['controls_flagged_incorrect']}/12 | {after['controls_flagged_incorrect']}/12 |\n| Originals verified by code | 18/18 | 18/18 |\n| Altered controls rejected by code | 12/12 | 12/12 |\n"
    md+=f"\nPaired AI clarity: {paired['improved']} higher, {paired['unchanged']} unchanged, {paired['lower']} lower, with the same public prompts and example numbers. Each round has one unbound issue quote. The reviewer misses four controls before and five after, and some issue labels contradict their explanations. Its clarity preference is development feedback, not a reliable mathematical or teaching gate. Raw errors are preserved. Human reviews remain zero.\n\n"
    md+='All 331 public practice items retain verified, different-answer examples passing the production active-item guard. The same 900 seeded inputs were replayed: 892 valid examples pass a separate oracle; eight invalid inputs are rejected. Repeated regression inputs are not independent learner observations. Boundary regimes are still not guaranteed to match; teacher review and R3 integration remain open.\n\nThe overview now shows learners only their own revisit counts by chapter. Teachers can inspect the earliest 100 item references without internal hashes. Counts include every eligible current-version row; deletion removes them. Reading cannot publish, grade or start a question. R3 still needs to persist session revisit marks and recheck publication before resuming an item.\n\n'
    md+=f"Both capped review batches completed once: 60 calls / USD {report['budget_snapshot']['new_reported_usd']:.8f}, with every cost reported. Phase reported spend: USD {phase['actual_spend_usd']:.8f}; accounted: USD {phase['accounted_phase_usd']:.8f}, including the preserved unknown-cost reservation. The USD 10 ceiling holds; wallets are closed. Only public/synthetic material was sent.\n\nReproduce offline: scripts/product_quality/report_r4_iteration.py --check. Raw evidence and blank v2 teacher forms stay under ignored Directions. Earlier reports retain their original sources/cost snapshots.\n"
    folder=ROOT/'baseline_task_pool_audit_02';pool=read(folder/'INDEX.json');protocol=read(folder/'PROTOCOL.json');pair=read(folder/'PAIR_CHECK.json')
    assert pool['status']=='completed' and pool['core_source_unchanged'] and pair['exact_legacy_trajectory_matches']==48
    assert sha(Path(pool['run'])/'manifest.json')==pool['manifest_sha256']
    pool_report={'scope':'Evaluation-only C2 task-pool ablation; product defaults and diagnosis unchanged','protocol_sha256':sha(folder/'PROTOCOL.json'),'full_current_pool':331,'limited_prior_pool':131,'sessions':48,'provider_calls':0,'restricted_pool':{k:pool[k] for k in ['diagnosis_recall','diagnosis_precision','success_proxy','synthetic_mean_gain','practice']},'full_pool_baseline':{'diagnosis_recall':.083,'diagnosis_precision':.4,'success_proxy':4,'synthetic_mean_gain':.083,'unchecked_practice':18},'exact_prior_trajectory_matches':48,'interpretation':'Changing only the evaluation process AP task pool restores prior metrics and all 48 prior trajectories. The full-pool baseline changed curriculum/task support, so it does not isolate diagnosis-code deterioration. Expanded-scope diagnosis and human learning remain unvalidated.','source_note':protocol['note'],'first_preflight_failure':'Git LF versus working-tree CRLF stopped preflight before sessions; normalized text check corrected, original error preserved.'}
    pool_md="""# Why the fixed baseline changed

The cached paired audit finds 15 changed trajectories per arm, all first diverging at AP practice selection on turn index 1. Nine sessions per arm lose a diagnosis hit; no earlier learner-message or route divergence appears.

A predeclared evaluation-only C2 ablation keeps qualified core runtime, diagnosis, simulator, data/config and seeds unchanged, and restricts AP selection to its earlier two families. It changes only that worker process and restores the setting. The product keeps all 331 practice items.

| Scope | Pool | Recall | Precision | Success proxy | Synthetic gain | Unchecked practice |
| --- | --- | --- | --- | --- | --- | --- |
| Expanded baseline | 331 | 0.083 | 0.4 | 4/48 | 0.083 | 18 |
| Earlier task scope, same diagnosis | 131 | 0.208 | 0.625 | 4/48 | 0.167 | 0 |

All 48 restricted-scope trajectories match the prior v2 C2 baseline, excluding identifiers/timing. Task-pool selection drives these observed differences on this simulator. This does not validate newly connected families or establish learning; the separate fresh-message diagnosis gap remains.

Keep both scopes visible. R5/R2 should review and extend simulator/task support from public mathematical rules before expanded-scope efficacy comparisons. Do not silently narrow the product or relabel unsupported attempts as successes. The same 16 cards/three seeds are repeated, not 48 independent new learners. This audit uses zero provider calls and preserves earlier reports.

The first preflight stopped before any session because Git LF and Windows CRLF bytes differed. Newline-normalized text comparison corrected that check; the original error is preserved. No product code changed to obtain this result. Private evidence: Directions/product_quality/v3/baseline_task_pool_audit_02.
"""
    return {'R4_REVIEW.json':json.dumps(report,indent=2)+'\n','R4_REVIEW.md':md,'TASK_POOL_AUDIT.json':json.dumps(pool_report,indent=2)+'\n','TASK_POOL_AUDIT.md':pool_md}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for name,value in build().items():
        p=DEST/name
        if args.check:assert p.read_text(encoding='utf-8')==value,name
        else:p.write_text(value,encoding='utf-8')
    print(json.dumps({'status':'verified' if args.check else 'written'}))
if __name__=='__main__':main()
