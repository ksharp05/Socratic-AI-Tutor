"""Analyse saved development evidence without model calls or changing experimental behaviour."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import re
import statistics
import sys
from collections import Counter, defaultdict

CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',CODE)).resolve()
sys.path.insert(0,str(CODE/'src'))
from tutor import store
from tutor.topic_sources import cards as topic_cards
from tutor_eval import metrics


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def paired(a,b,measure,seed_filter=None):
    left={(s['student'],s['seed']):s for s in a if seed_filter is None or s['seed']==seed_filter}
    right={(s['student'],s['seed']):s for s in b if seed_filter is None or s['seed']==seed_filter}
    keys=sorted(set(left)&set(right));clusters=defaultdict(list)
    for key in keys:
        source=key[0].split('__')[0]
        clusters[source].append(measure(right[key])-measure(left[key]))
    point=statistics.fmean(v for group in clusters.values() for v in group) if clusters else None
    ci=None
    if len(clusters)>=2:
        rng=random.Random(0);ids=sorted(clusters)
        samples=sorted(statistics.fmean(v for sid in rng.choices(ids,k=len(ids)) for v in clusters[sid]) for _ in range(2000))
        ci=[samples[50],samples[1949]]
    return {'matched_sessions':len(keys),'student_clusters':len(clusters),'difference':point,'cluster_bootstrap_ci95':ci,
            'unmatched_left':len(set(left)-set(right)),'unmatched_right':len(set(right)-set(left))}


def citation_audit(sessions):
    registered={c['passage_id']:c for c in topic_cards()}
    counts=Counter()
    for session in sessions:
        for turn in session['turns']:
            counts['turns']+=1
            named=set(re.findall(r'\[((?:normalized|ncert|exemplar):[^]\s]+)\]',turn['tutor']))
            snapshots=turn.get('citations',[])
            if named:counts['turns_with_source_id']+=1
            if snapshots:counts['turns_with_snapshot']+=1
            if named-set(c['passage_id'] for c in snapshots):counts['turns_with_missing_snapshot']+=1
            for snapshot in snapshots:
                counts['snapshots']+=1
                data={k:v for k,v in snapshot.items() if k!='reference_sha256'}
                counts['valid_snapshot_hash']+=snapshot.get('reference_sha256')==hashlib.sha256(store.dumps(data).encode('utf-8')).hexdigest()
                counts['same_chapter']+=snapshot.get('chapter')==session.get('chapter')
                card=registered.get(snapshot['passage_id'])
                counts['registered_source_text_match']+=bool(card and snapshot.get('text')==card['text'])
    return {**dict(counts),'semantic_faithfulness':'unmeasured_requires_human_review'}


def seed_spread(sessions):
    groups=defaultdict(list)
    for s in sessions:groups[s['seed']].append(metrics.session_view(s))
    by_seed={seed:{'sessions':len(group),'success_rate':statistics.fmean(v['task_success'] for v in group),
                   'mean_gain':statistics.fmean(v['gain'] for v in group)} for seed,group in groups.items()}
    output={'per_seed':by_seed}
    for field in ['success_rate','mean_gain']:
        values=[v[field] for v in by_seed.values()]
        output[field]={'mean':statistics.fmean(values) if values else None,
                       'sd':statistics.stdev(values) if len(values)>1 else None,
                       'range':[min(values),max(values)] if values else None}
    return output


def security_bounds(results):
    output={}
    for kind in ['attack','control']:
        selected=[r for r in results if r['kind']==kind]
        known=[r for r in selected if r['supported']]
        positives=sum(bool(r.get('success' if kind=='attack' else 'false_block')) for r in known)
        unknown=len(selected)-len(known)
        output[kind]={'scheduled':len(selected),'measured':len(known),'positive':positives,'unsupported_or_error':unknown,
                      'supported_only_rate':positives/len(known) if known else None,
                      'all_scheduled_rate_bounds':[positives/len(selected),(positives+unknown)/len(selected)] if selected else None}
    return output


def review_packet(all_runs,out):
    if out.exists() and any(out.glob('rater_*.csv')):
        return {'path':str(out),'existing_packet_preserved':True,'human_labels_present':'not_reassessed'}
    candidates=[]
    for arm,(manifest,sessions) in all_runs.items():
        for session in sessions:
            for turn in session['turns']:
                if turn.get('problem'):
                    levels={leak['level'] for leak in turn['leaks']}
                    level='full' if 'full' in levels else 'partial' if 'partial' in levels else 'none'
                    candidates.append((level,arm,manifest['run_id'],session['session'],turn))
    rng=random.Random(0);rng.shuffle(candidates)
    selected=[]
    for level in ['none','partial','full']:
        selected += [item for item in candidates if item[0]==level][:20]
    remaining=[item for item in candidates if item not in selected]
    selected += remaining[:max(0,60-len(selected))]
    rng.shuffle(selected)
    out.mkdir(parents=True,exist_ok=True)
    fields=['turn_id','problem','reference_answer_evaluator_only','student','tutor','leak_label','targets_misconception',
            'citation_faithfulness','teaching_quality_1_to_5','notes']
    prepared=[];mapping=[]
    for i,(level,arm,run,sid,turn) in enumerate(selected,1):
        tid=f'REVIEW-{i:03d}'
        prepared.append(dict(turn_id=tid,problem=turn['problem']['prompt'],reference_answer_evaluator_only=turn['problem']['answer'],
                             student=turn['student'],tutor=turn['tutor']))
        mapping.append({'turn_id':tid,'arm':arm,'run_id':run,'session':sid,'turn_index':turn['index'],'code_leak_label':level})
    for name in ['rater_a.csv','rater_b.csv']:
        with (out/name).open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(prepared)
    (out/'mapping_private.json').write_text(json.dumps(mapping,indent=2)+'\n',encoding='utf-8')
    (out/'README.md').write_text('Two independent raters should label their own CSV. Labels are blank. Leak: none/partial/full; targets: yes/no/uncertain; citation faithfulness: supported/unsupported/insufficient_context/not_applicable; teaching quality 1–5. The reference answer is evaluator-only and must never enter tutor prompts. Keep mapping_private.json hidden until rating. This is development calibration material, not independent final content or human approval.\n',encoding='utf-8')
    return {'turns':len(prepared),'code_label_sample_counts':dict(Counter(item[0] for item in selected)),
            'human_labels_present':0,'path':str(out)}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['smoke','offline','pilot','live'],required=True)
    parser.add_argument('--revision',choices=['v1','v2'],default='v1')
    args=parser.parse_args();root=SOURCE/'Directions/m3_runs'/(('v2/'+args.stage) if args.revision=='v2' else args.stage)
    index=json.loads((root/'INDEX.json').read_text(encoding='utf-8'))
    all_runs={};report={'stage':args.stage,'development_only':True,'independent_evaluation':False,'runs':{},'security':{}}
    for arm,job in index['jobs'].items():
        if job.get('status')!='completed':continue
        run=Path(job['run']);manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
        if arm.startswith('e2_'):
            report['security'][arm]={'run_id':manifest['run_id'],'summary':manifest['summary'],
                'bounds':security_bounds(rows(run/'security.jsonl')),'operations':manifest.get('operations',{}),
                'switch_scope':manifest.get('switch_scope'),'manifest_sha256':hashlib.sha256((run/'manifest.json').read_bytes()).hexdigest()}
            continue
        sessions=rows(run/'sessions.jsonl');all_runs[arm]=(manifest,sessions)
        summary=manifest['summary']
        report['runs'][arm]={'run_id':manifest['run_id'],'sessions':len(sessions),'failures':summary['failures'],
            'timeouts':summary['timeouts'],'task_success_proxy':summary['task_success'],'diagnosis':summary['diagnosis'],
            'quiz':summary['quiz'],'leaks':summary['leaks'],'checked_practice':summary['checked_practice'],
            'cost':summary['cost_usd'],'latency_ms':summary['latency_ms'],'policy':summary['policy'],
            'citations':citation_audit(sessions),'seed_spread':seed_spread(sessions),
            'provider_budget':manifest.get('provider_budget'),'sessions_not_run':manifest['budget']['sessions_not_run'],
            'code_sha256':manifest['code_sha256'],'data_sha256':manifest['data'],
            'manifest_sha256':hashlib.sha256((run/'manifest.json').read_bytes()).hexdigest()}
    comparisons={}
    for label,left,right,seed in [('E1_C2_minus_C1','c1','c2',None),('E1_C2_minus_C0','c0','c2',None),
                                  ('E3_candidate_minus_before','c2','e3_after',None),
                                  ('E3_budget_tranche_minus_matched_before','c2','e3_after_budget_tranche12',None),
                                  ('E4a_memory_on_minus_off','memory_off','c2',1),
                                  ('E4b_telling_minus_hints','c2','direct_answers',1)]:
        if left in all_runs and right in all_runs:
            comparisons[label]={name:paired(all_runs[left][1],all_runs[right][1],measure,seed) for name,measure in
                [('quiz_gain',lambda s:metrics.session_view(s)['gain']),
                 ('success_proxy',lambda s:int(metrics.session_view(s)['task_success'])),
                 ('cleared_misconceptions',lambda s:len(s['cleared']))]}
    report['paired_comparisons']=comparisons
    report['analysis_code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if (root/'E3_BUDGET_TRANCHE.json').exists():
        report['E3_original_design_completion']=json.loads((root/'E3_BUDGET_TRANCHE.json').read_text(encoding='utf-8'))
    report['review_packet']=review_packet(all_runs,root/'review_packet')
    (root/'ANALYSIS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    lines=[f'# {args.stage.capitalize()} development experiment analysis','',
           'Synthetic development evidence; final preregistration, human review and independent evaluation remain pending. Code proxies do not establish real learning or semantic safety.','',
           '| Arm | Sessions | Failures/timeouts | Success proxy | Mean quiz gain | Full/partial leak turns | Estimated USD |',
           '| --- | --- | --- | --- | --- | --- | --- |']
    for arm,item in report['runs'].items():
        lines.append(f"| {arm} | {item['sessions']} | {item['failures']}/{item['timeouts']} | {item['task_success_proxy']} | {item['quiz']['mean_gain']} | {item['leaks']['full_turns']}/{item['leaks']['partial_turns']} | {item['cost']['total']} |")
    lines += ['', 'Run IDs and exact source/data hashes, seed spread, paired cluster-bootstrap intervals, citation integrity, budget and unsupported-security bounds are in ANALYSIS.json beside this report.', '',
              'E3 uses an unreviewed candidate; E4 gains depend on synthetic transition/copying rules. These are exploratory development results. Repeated seeds are not additional independent learners.', '',
              'Two blank-rater development CSVs are in review_packet/. Citation faithfulness, teaching quality, human agreement and judge calibration remain unmeasured.']
    (root/'ANALYSIS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'stage':args.stage,'arms':{k:{key:v[key] for key in ['sessions','failures','timeouts','task_success_proxy']} for k,v in report['runs'].items()},'security':{k:v['summary'] for k,v in report['security'].items()},'saved':str(root/'ANALYSIS.json')},indent=2))


if __name__=='__main__':main()
