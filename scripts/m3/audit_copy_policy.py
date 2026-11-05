"""Audit the candidate copying repair on saved development trajectories; no model/provider calls."""
from __future__ import annotations
import ast
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys

CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()
sys.path.insert(0,str(CODE/'src'));sys.path.insert(0,str(CODE/'scripts/m3'))
from tutor import store
from tutor_eval import harness, simulator, post_copy_policy as policy
from post_copy_sensitivity import RecordedApp, replay, semantic, gain


def load(path):return json.loads(path.read_text(encoding='utf-8'))
def rows(path):return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def review_packet(witnesses,posts,out):
    if out.exists():raise ValueError('Existing review data is preserved; use a new packet version')
    unique={}
    for w in witnesses:
        key=hashlib.sha256(json.dumps([w['history'],w['student'],w['tutor'],w['post']['question_id']],sort_keys=True).encode()).hexdigest()
        unique.setdefault(key,w)
    candidates=list(unique.values());random.Random(0).shuffle(candidates)
    chosen=[]
    for decision in ['match_only_in_owned_format','unattributed_full_answer_match']:
        chosen.extend([w for w in candidates if w['decision']==decision][:15])
    chosen.extend([w for w in candidates if w not in chosen][:max(0,30-len(chosen))])
    controls=[]
    for chapter in ['quadratic_equations','arithmetic_progressions','trigonometry']:
        quota=2 if chapter!='trigonometry' else 1
        for post in posts[chapter]:
            kind=post['answer']['kind']
            if kind not in ('scalar','finite_set'):continue
            if kind=='scalar':answer='The value is '+post['answer']['value']+'.'
            elif post['answer']['values']:answer='The roots are '+' and '.join(post['answer']['values'])+'.'
            else:continue
            positive=post['prompt']+' '+answer
            negative=post['prompt']+' Which relationship would you check next?'
            if not policy.classify(positive,post)['copy_eligible'] or policy.classify(negative,post)['copy_eligible']:continue
            for text,proposed in [(positive,'context_linked_full_match'),(negative,'no_context_linked_full_answer')]:
                controls.append({'history':[],'student':'Please help with this question.','tutor':text,'post':post,
                    'decision':proposed,'record_type':'AI_authored_development_calibration_reply','run_id':None,'session':None,'turn_index':None})
            quota-=1
            if not quota:break
        if quota:raise ValueError('Insufficient suitable development controls for '+chapter)
    records=[{**w,'record_type':'recorded_development_turn'} for w in chosen]+controls
    random.Random(1).shuffle(records);out.mkdir(parents=True)
    fields=['item_id','record_type','prior_conversation','student','tutor','post_question_evaluator_only',
        'post_answer_evaluator_only','question_context_yes_no_uncertain','answer_disclosure_none_partial_full_uncertain',
        'copy_justified_yes_no_uncertain','rater','notes']
    prepared=[];mapping=[]
    for i,w in enumerate(records,1):
        item=f'COPY-CONTEXT-{i:03d}'
        prepared.append({'item_id':item,'record_type':w['record_type'],'prior_conversation':json.dumps(w['history'],ensure_ascii=False),
            'student':w['student'],'tutor':w['tutor'],'post_question_evaluator_only':w['post']['prompt'],
            'post_answer_evaluator_only':json.dumps(w['post']['answer'],ensure_ascii=False)})
        mapping.append({'item_id':item,**{k:w.get(k) for k in ['decision','run_id','session','turn_index']},'post_question_id':w['post']['question_id']})
    for name in ['rater_a.csv','rater_b.csv']:
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(prepared)
    (out/'mapping_private.json').write_text(json.dumps(mapping,indent=2)+'\n',encoding='utf-8')
    manifest={'real_unique_contexts_available':len(unique),'recorded_turns_sampled':len(chosen),'AI_authored_controls':len(controls),
        'items':len(records),'human_labels':0,'human_raters_assigned':False,'not_independent_final_data':True,
        'sampling_classes_are_not_ground_truth':True,'files_sha256':{name:sha(out/name) for name in ['rater_a.csv','rater_b.csv']}}
    (out/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (out/'README.md').write_text('Two independent people should use separate CSVs. All labels are blank. Keep mapping_private.json hidden until ratings are complete. Judge question-context linkage, actual answer disclosure and whether simulated copying is justified; use uncertain rather than guessing. The ten synthetic reply controls are explicitly marked and excluded from study metrics. These proposed classes are not human gold labels. This is focused review of the copying rule, not a replacement for the existing leak/targets judge calibration or independent final assessment.\n',encoding='utf-8')
    return manifest


def main():
    old_root=SOURCE/'Directions/m3_runs/v2/live';out_root=SOURCE/'Directions/m3_runs/v3';out_root.mkdir(parents=True,exist_ok=True)
    wallet_paths=[SOURCE/'Directions/m3_runs/provider_budget.json',SOURCE/'Directions/m3_runs/provider_budget_extension_e3.json']
    wallets_before={str(p):sha(p) for p in wallet_paths}
    frozen=subprocess.check_output(['git','-C',str(CODE),'show','12d541e:src/tutor_eval/harness.py'],text=True)
    current=(CODE/'src/tutor_eval/harness.py').read_text(encoding='utf-8')
    function=lambda text:next(ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='run_session')
    assert function(frozen)==function(current),'Frozen transition function changed'
    data=SOURCE/'Directions/m3_data/development-v1'
    cards={c['student_id']:c for c in load(data/'students.json')};pairs={p['pair_id']:p for p in load(data/'pairs.json')}
    assigned={a['student_id']:a['pair_ids'] for a in load(data/'assignments.json')}
    catalogue={m['misconception_id']:m for m in rows(CODE/'content/dataset-v0.10.0/misconceptions.jsonl')}
    conn=store.connect(Path(':memory:'))
    try:practice={p['question_id']:p for p in harness._publish_fixture_items(conn)}
    finally:conn.close()
    summaries=[];private_rows=[];witnesses=[];posts_by_chapter={chapter:[] for chapter in ['quadratic_equations','arithmetic_progressions','trigonometry']};input_hashes=[]
    index=load(old_root/'INDEX.json')
    for arm,job in index['jobs'].items():
        if arm.startswith('e2_') or job.get('status')!='completed':continue
        directory=Path(job['run']);manifest=load(directory/'manifest.json');decisions=Counter();count=removed=allowed=0;original_gains=[];repaired_gains=[]
        for recorded in rows(directory/'sessions.jsonl'):
            chosen=[pairs[pid] for pid in assigned[recorded['student']]];post_items=[p['post'] for p in chosen]
            assert not {p['question_id'] for p in post_items}&(set(practice)|{p['pre']['question_id'] for p in chosen})
            posts_by_chapter[recorded['chapter']].extend(p for p in post_items if p not in posts_by_chapter[recorded['chapter']])
            args=(recorded,cards[recorded['student']],chosen,catalogue,practice,manifest['run_id'])
            baseline=replay(*args);assert semantic(baseline)==semantic(recorded),recorded['session']
            app=RecordedApp(recorded)
            try:
                with policy.session_scope(app,post_items,practice) as measurement:
                    repaired=harness.run_session(measurement.app,args[1],chosen,{'run':{'max_turns':len(recorded['turns']),'turn_timeout_s':120}},recorded['seed'],manifest['run_id'],catalogue,practice,simulator.Voice('template'))
                audit=measurement.summary()
            finally:app.conn.close()
            assert semantic(baseline)['turns']==semantic(repaired)['turns']
            assert len(audit['audit'])==sum(len(t['quiz_contamination']) for t in recorded['turns'])
            original_gains.append(gain(recorded));repaired_gains.append(gain(repaired));count+=1
            decisions.update(audit['decision_counts']);removed+=len(audit['removed_ineligible_post_ids']);allowed+=len(audit['post_ids_allowed_to_copy'])
            post_lookup={p['question_id']:p for p in post_items}
            for entry in audit['audit']:
                i=entry['turn_index'];t=recorded['turns'][i]
                witnesses.append({**entry,'condition':arm,'run_id':manifest['run_id'],'session':recorded['session'],
                    'history':[{'student':turn['student'],'tutor':turn['tutor']} for turn in recorded['turns'][:i]],
                    'student':t['student'],'tutor':t['tutor'],'post':post_lookup[entry['question_id']]})
            private_rows.append({'condition':arm,'session':recorded['session'],'student':recorded['student'],'seed':recorded['seed'],
                'original_gain':gain(recorded),'repaired_gain':gain(repaired),'measurement':audit})
        summaries.append({'condition':arm,'sessions':count,'decision_counts':dict(decisions),'removed_post_copies':removed,'retained_post_copies':allowed,
            'original_mean_gain':sum(original_gains)/count,'candidate_mean_gain':sum(repaired_gains)/count})
        input_hashes.append({'run_id':manifest['run_id'],'manifest_sha256':sha(directory/'manifest.json'),'sessions_sha256':sha(directory/'sessions.jsonl')})
        print('AUDITED',arm,count,'sessions',dict(decisions),flush=True)
    packet=review_packet(witnesses,posts_by_chapter,out_root/'review_packets/post-copy-context-v1')
    assert {str(p):sha(p) for p in wallet_paths}==wallets_before
    result={'policy':policy.POLICY,'scope':'post_hoc_development_candidate_validation_not_human_calibrated',
        'baseline_reproductions':len(private_rows),'identical_recorded_dialogue_trajectories':len(private_rows),
        'legacy_full_match_witnesses':len(witnesses),'conditions':summaries,'review_packet':packet,'inputs':input_hashes,
        'provider_calls':0,'ledger_hashes_unchanged':wallets_before,'run_session_AST_unchanged':True,
        'policy_sha256':sha(CODE/'src/tutor_eval/post_copy_policy.py'),'script_sha256':sha(Path(__file__)),
        'unattributed_matches_remain_semantically_unreviewed':True,'original_primary_outcomes_unchanged':True}
    (out_root/'COPY_POLICY_AUDIT_PRIVATE.json').write_text(json.dumps({**result,'sessions':private_rows},indent=2)+'\n',encoding='utf-8')
    public=CODE/'Docs/m3/v3';public.mkdir(parents=True,exist_ok=True)
    (public/'COPY_POLICY_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    lines=['# Context-bound copying repair: development validation','',
        f"All {len(private_rows)} recorded simulator baselines reproduce with the legacy policy, and all dialogue trajectories remain identical under the candidate repair. This is cached-output analysis, not a fresh live tutor experiment. The frozen transition function is unchanged. No provider calls were made.",'',
        '| Recorded condition | Sessions | Owned-format matches | Unattributed full matches | Context-linked full matches | Removed post copies | Retained copies | Original/candidate mean quiz change |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in summaries:
        d=r['decision_counts'];lines.append(f"| {r['condition']} | {r['sessions']} | {d.get('match_only_in_owned_format',0)} | {d.get('unattributed_full_answer_match',0)} | {d.get('context_linked_full_match',0)} | {r['removed_post_copies']} | {r['retained_post_copies']} | {r['original_mean_gain']:.3f}/{r['candidate_mean_gain']:.3f} |")
    lines+=['','The policy removes only the exact application-owned formatting suffix attached to a registered question. Copying requires an explicit post-question or identical registered-problem exposure plus a full answer match that survives student-echo exclusion. Numeric matches without question context remain unreviewed; they are not counted as semantic passes. Registered-practice telling is unaffected. Legacy contamination flags remain in session evidence and qualified-success checks stay conservative.','',
        f"A separate non-overwriting review packet contains {packet['recorded_turns_sampled']} unique recorded contexts plus {packet['AI_authored_controls']} explicitly marked AI-authored calibration replies. All labels are blank; no reviewer is assigned. These controls are excluded from study metrics and do not establish independent final data or human calibration.",'',
        'Positive/negative functional controls verify that actual context-linked disclosures can still enable copying, unrelated values cannot, student echoes do not become new copying evidence, private quiz references do not enter application inputs, and concurrent scopes remain isolated. The candidate is opt-in and needs human/protocol review before final qualification. It does not remove the simulator/kernel assumptions or establish human learning.']
    (public/'COPY_POLICY_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for name in ['COPY_POLICY_AUDIT.json','COPY_POLICY_AUDIT.md']:
        target=SOURCE/'Docs/m3/v3'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(public/name,target)
    print(json.dumps({'baseline_reproductions':len(private_rows),'witnesses':len(witnesses),'packet':packet,'provider_calls':0},indent=2))


if __name__=='__main__':main()
