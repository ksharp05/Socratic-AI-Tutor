"""Create a bounded, contextual human-rating packet. Refuses to overwrite any existing packet."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import random

SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()


def create(index_path, out, catalogue_path, limit=60):
    if out.exists():
        raise ValueError('Existing human-review packet is preserved; choose a new versioned output directory')
    catalogue={m['misconception_id']:m for m in (json.loads(l) for l in catalogue_path.read_text(encoding='utf-8').splitlines() if l.strip())}
    index=json.loads(index_path.read_text(encoding='utf-8'));candidates=[]
    data=SOURCE/'Directions/m3_data/development-v1'
    assigned={a['student_id']:a['pair_ids'] for a in json.loads((data/'assignments.json').read_text(encoding='utf-8'))}
    pairs={p['pair_id']:p for p in json.loads((data/'pairs.json').read_text(encoding='utf-8'))}
    for arm,job in index['jobs'].items():
        if arm.startswith('e2_') or job.get('status')!='completed':continue
        run=Path(job['run']);run_id=json.loads((run/'manifest.json').read_text(encoding='utf-8'))['run_id']
        for line in (run/'sessions.jsonl').read_text(encoding='utf-8').splitlines():
            session=json.loads(line)
            targets=[{'misconception_id':mid,'incorrect_rule':catalogue[mid]['incorrect_rule'],
                      'correct_reasoning':catalogue[mid].get('correct_reasoning')} for mid in session['seeded'] if mid in catalogue]
            for i,turn in enumerate(session['turns']):
                if not turn.get('problem'):continue
                levels={l['level'] for l in turn['leaks']};level='full' if 'full' in levels else 'partial' if 'partial' in levels else 'none'
                history=[{'student':t['student'],'tutor':t['tutor']} for t in session['turns'][:i]]
                references=[{'role':'conversation_problem','prompt':t['problem']['prompt'],'answer':t['problem']['answer']}
                            for t in session['turns'][:i+1] if t.get('problem')]
                references += [{'role':'assigned_post_quiz','prompt':pairs[pid]['post']['prompt'],
                                'answer':pairs[pid]['post'].get('answer')} for pid in assigned.get(session['student'],[])]
                record={'problem':turn['problem']['prompt'],'reference_answer_evaluator_only':turn['problem']['answer'],
                        'prior_conversation':json.dumps(history,ensure_ascii=False),
                        'session_references_evaluator_only':json.dumps(references,ensure_ascii=False),'student':turn['student'],'tutor':turn['tutor'],
                        'target_misconceptions_evaluator_only':json.dumps(targets,ensure_ascii=False),
                        'citation_sources':json.dumps(turn.get('citations',[]),ensure_ascii=False)}
                candidates.append({'level':level,'record':record,'arm':arm,'run_id':run_id,
                                   'session':session['session'],'turn_index':turn['index']})
    rng=random.Random(0);rng.shuffle(candidates);selected=[]
    for level in ['none','partial','full']:
        selected += [c for c in candidates if c['level']==level][:limit//3]
    selected += [c for c in candidates if c not in selected][:max(0,limit-len(selected))]
    rng.shuffle(selected);out.mkdir(parents=True)
    records=[];mapping=[]
    for i,c in enumerate(selected,1):
        tid=f'REVIEW-{i:03d}';records.append({'turn_id':tid,**c['record']})
        mapping.append({'turn_id':tid,**{k:c[k] for k in ['arm','run_id','session','turn_index','level']}})
    fields=['turn_id','problem','reference_answer_evaluator_only','prior_conversation','session_references_evaluator_only','student','tutor',
            'target_misconceptions_evaluator_only','citation_sources','leak_label_none_partial_full',
            'targets_label_yes_no_uncertain','citation_faithfulness_supported_unsupported_insufficient_na',
            'teaching_quality_1_to_5','reason','rater','rated_at']
    for name in ['rater_a.csv','rater_b.csv']:
        with (out/name).open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(records)
    (out/'mapping_private.json').write_text(json.dumps(mapping,indent=2)+'\n',encoding='utf-8')
    counts=dict(Counter(c['level'] for c in selected))
    manifest={'source_index':str(index_path),'source_index_sha256':hashlib.sha256(index_path.read_bytes()).hexdigest(),
              'turns':len(records),'sampling_code_labels_not_human_truth':counts,
              'class_count_gate_met_by_sampling_labels_only':all(counts.get(k,0)>=5 for k in ['none','partial','full']),
              'human_labels_at_creation':0,'blinded_arm_names':True,'independent_raters_assigned':False,
              'evaluator_only_reference_fields_never_tutor_prompt':True,
              'files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}}
    (out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (out/'README.md').write_text("Two separately assigned human raters should label their own CSV without viewing mapping_private.json or each other's labels. Every rating starts blank. Context includes the complete prior conversation (at most seven exchanges), source snapshots, evaluator-only target rule, conversation reference answers and assigned post-quiz references. Assess the current turn using the relevant reference and what the student already produced; do not infer a leak merely from a coincidentally shared number. These reference fields must never enter tutor prompts. Rate leaks as none/partial/full, whether the turn targets any listed misconception as yes/no/uncertain, source faithfulness as supported/unsupported/insufficient_context/not_applicable, and teaching quality 1 (incorrect or harmful) to 5 (accurate, focused, appropriately scaffolded). Add a reason, rater and date. Code labels only stratify the sample; they are not human ground truth. If any class has fewer than five samples, add an explicitly separate development calibration top-up before judging agreement. No teacher approval, human agreement or judge calibration has been inferred. Existing packet versions are preserved.\n",encoding='utf-8')
    return manifest


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--index',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(create(args.index,args.out,SOURCE/'content/dataset-v0.10.0/misconceptions.jsonl'),indent=2))


if __name__=='__main__':main()
