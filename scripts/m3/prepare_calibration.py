"""Make a versioned, agreement-compatible packet with explicit existing-fixture top-ups. No model calls."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

CODE=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(CODE/'src'))


def prepare(packet, out):
    if out.exists():
        raise ValueError('Existing calibration/rating artifacts are preserved')
    with (packet/'rater_a.csv').open(encoding='utf-8-sig',newline='') as f:
        source=list(csv.DictReader(f))
    rating_fields=['leak_label_none_partial_full','targets_label_yes_no_uncertain','citation_faithfulness_supported_unsupported_insufficient_na',
                   'teaching_quality_1_to_5','reason','rater','rated_at']
    for name in ['rater_a.csv','rater_b.csv']:
        with (packet/name).open(encoding='utf-8-sig',newline='') as f:
            if any(row.get(k) for row in csv.DictReader(f) for k in rating_fields):
                raise ValueError('Human labels already exist; preserve them and create an explicit migration')
    records=[]
    for row in source:
        records.append({'item_id':row['turn_id'],'record_origin':'recorded_development_tutor_turn',
            'problem':row['problem'],'reference_answer':row['reference_answer_evaluator_only'],
            'prior_conversation':row['prior_conversation'],'session_references_evaluator_only':row['session_references_evaluator_only'],
            'seeded_misconceptions':row['target_misconceptions_evaluator_only'],'student':row['student'],'tutor':row['tutor'],
            'citation_sources':row['citation_sources']})
    mapping=json.loads((packet/'mapping_private.json').read_text(encoding='utf-8'))
    strata=Counter(row['level'] for row in mapping)
    fixtures=[json.loads(l) for l in (CODE/'eval/fixtures/leak_examples.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    partial=[x for x in fixtures if x['label']=='partial']
    practice={q['question_id']:q for q in (json.loads(l) for l in (CODE/'content/dataset-v0.10.0/practice_questions.jsonl').read_text(encoding='utf-8').splitlines() if l.strip())}
    from tutor.mathcore import compute_key
    from tutor_eval.simulator import render
    for i,item in enumerate(partial,1):
        key=compute_key(practice[item['question_id']]['problem'])
        if not key['verified']:raise ValueError('Calibration reference did not verify')
        tid=f'CAL-{i:03d}'
        records.append({'item_id':tid,'record_origin':'existing_AI_drafted_calibration_fixture_not_a_model_result',
            'problem':item['prompt'],'reference_answer':render(key['key']), 'prior_conversation':'[]',
            'session_references_evaluator_only':'[]','seeded_misconceptions':'[]',
            'student':item.get('student_said',''),'tutor':item['tutor_reply'],'citation_sources':'[]'})
        mapping.append({'turn_id':tid,'level':'partial','origin_fixture_id':item['example_id'],
                        'origin_status':item['status'],'not_a_recorded_model_result':True})
        strata['partial']+=1
    fields=['item_id','record_origin','problem','reference_answer','prior_conversation','session_references_evaluator_only',
            'seeded_misconceptions','student','tutor','citation_sources','leak','targets_seeded','mistake_identification',
            'revealing_of_the_answer','providing_guidance','actionability','citation_faithfulness',
            'teaching_quality_1_to_5','rater','rated_at','notes']
    out.mkdir(parents=True)
    for name in ['rater_a.csv','rater_b.csv']:
        with (out/name).open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(records)
    (out/'mapping_private.json').write_text(json.dumps(mapping,indent=2)+'\n',encoding='utf-8')
    manifest={'recorded_tutor_turns':len(source),'existing_calibration_fixtures_added':len(partial),'total_rating_items':len(records),
              'proposed_sampling_classes_not_human_ground_truth':dict(strata),
              'at_least_five_proposed_items_per_leak_class':all(strata[k]>=5 for k in ['none','partial','full']),
              'human_labels':0,'human_raters_assigned':False,'judge_calibrated':False,
              'fixtures_excluded_from_experiment_metrics':True,'source_packet_preserved':str(packet),
              'fixture_source_sha256':hashlib.sha256((CODE/'eval/fixtures/leak_examples.jsonl').read_bytes()).hexdigest(),
              'files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}}
    (out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (out/'README.md').write_text("Assign two independent human raters and give each their own CSV, opened as UTF-8. All rating fields are blank. Keep mapping_private.json and proposed code/fixture labels hidden until rating. Context/reference/target columns are evaluator-only and must never enter tutor prompts. There are 60 recorded development turns plus three existing AI-drafted calibration fixtures; those three are not model outcomes and are excluded from experiment results. Proposed strata include at least five of each leak class, but actual class counts and agreement must be established by human labels. Use leak=none/partial/full and targets_seeded=yes/no/uncertain (use blank for fixture items without a target). Other rubric fields follow eval/README.md and the supplied references. Label citation_faithfulness as supported/unsupported/insufficient_context/not_applicable. Add rater, date and a reason. For rater agreement use python -m tutor_eval.agreement score --raters <rater_a.csv> <rater_b.csv> --label leak, and repeat with --label targets_seeded. Comparing a judge additionally needs the private mapping from blinded IDs to actual session#turn IDs; do not claim calibration from the proposed sampling labels. Existing packet versions and any human edits are preserved.\n",encoding='utf-8')
    return manifest


def main():
    p=argparse.ArgumentParser();p.add_argument('--packet',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.packet,a.out),indent=2))


if __name__=='__main__':main()
