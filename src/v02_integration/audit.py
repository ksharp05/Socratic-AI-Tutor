"""Reproducible source-preserving audit; never a pedagogy approval or runtime export."""
import argparse,csv,hashlib,json,re,time,math
from collections import Counter,defaultdict
from pathlib import Path
from jsonschema import Draft202012Validator
from .math_audit import check_reference

COLLECTIONS={
 'problems':'dev/problem_variants.jsonl','dialogues':'dev/dialogues_synthetic.jsonl',
 'tutor_contexts':'dev/tutor_turn_contexts_unreviewed.jsonl','messages':'dev/contextual_learner_messages.jsonl',
 'preferences':'critic_only/response_preference_pairs.jsonl','security':'dev/security_attack_control_pairs.jsonl',
 'references':'review/reference_answers_dev_only.jsonl','retrieval':'review/retrieval_candidates_unlabelled.jsonl',
 'glossary':'review/glossary_unreviewed.jsonl','seed_misconceptions':'parent_seed_v0_1/dev/misconceptions.jsonl',
 'quarantine':'quarantine/T08_curriculum_unconfirmed_dialogues.jsonl'}
TRAJECTORIES={'self_repair','persistent_error','frustrated_rephrase','ambiguous_input'}
RUBRIC=['math_correctness','misconception_diagnosis','actionable_scaffolding','clarity_and_tone','answer_protection','context_fidelity']

def digest(value):return hashlib.sha256((json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()).hexdigest()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def tree_digest(files):return hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def require(condition,message):
 if not condition:raise ValueError(message)
def write_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def pairs(items):
 out={}
 for k,v in items:
  require(k not in out,'Duplicate JSON key');out[k]=v
 return out

def load_json(text):
 def constant(value):raise ValueError('Nonfinite JSON constant')
 def finite(value):
  number=float(value);require(math.isfinite(number),'Nonfinite JSON number');return number
 return json.loads(text,object_pairs_hook=pairs,parse_constant=constant,parse_float=finite)
def read_rows(path):
 require(path.stat().st_size<=32*1024*1024,'Input collection exceeds audit bound')
 with path.open(encoding='utf-8-sig') as f:return [load_json(line) for line in f if line.strip()]
def read_csv(path):
 with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def csv_view(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  if not rows:return
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader()
  for row in rows:
   writer.writerow({k:"'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v for k,v in row.items()})

def infer_schema(values):
 types=defaultdict(list)
 for v in values:
  kind='null' if v is None else 'boolean' if type(v) is bool else 'integer' if type(v) is int else 'number' if type(v) is float else 'object' if isinstance(v,dict) else 'array' if isinstance(v,list) else 'string'
  types[kind].append(v)
 variants=[]
 for kind,items in sorted(types.items()):
  result={'type':kind}
  if kind=='object':
   keys=set().union(*(set(v) for v in items));required=set.intersection(*(set(v) for v in items))
   result.update(additionalProperties=False,required=sorted(required),properties={k:infer_schema([v[k] for v in items if k in v]) for k in sorted(keys)})
  elif kind=='array':
   children=[x for v in items for x in v];result['items']=infer_schema(children) if children else {}
  variants.append(result)
 return variants[0] if len(variants)==1 else {'anyOf':variants}

def text_profile(texts):
 exact=Counter(' '.join(t.lower().split()) for t in texts)
 numeric=Counter(re.sub(r'\d+(?:[./]\d+)?','<n>',' '.join(t.lower().split())) for t in texts)
 return {'records':len(texts),'unique_exact_texts':len(exact),'unique_number_normalized_patterns':len(numeric),
  'top_repeated_text_hashes':[{'text_sha256':digest(t),'count':n,'words':len(t.split())} for t,n in exact.most_common(12)],
  'note':'number normalization is a dependence heuristic, not a count of semantic teaching situations'}

def priority_queue(dialogues,problems):
 selected=[]
 for mid in sorted({d['misconception_id'] for d in dialogues}):
  candidates=[d for d in dialogues if d['misconception_id']==mid]
  first=min(d['problem_id'] for d in candidates)
  for trajectory in sorted(TRAJECTORIES):
   d=next(d for d in candidates if d['problem_id']==first and d['trajectory']==trajectory)
   row={'dialogue_id':d['id'],'problem_id':first,'misconception_id':mid,'chapter':d['chapter'],'trajectory':trajectory,
     'variant_family':d['variant_family'],'source_path':COLLECTIONS['dialogues'],'source_content_sha256':digest(d),
     'student_error_text':d['messages'][0]['text'],'first_candidate_move':d['messages'][1]['move'],
     'candidate_response_sha256':digest(d['messages'][1]['text']),'machine_risk':'synthetic_template_dependence;triage_only',
     'status':'pending_human_review','subject_reviewer_id':'','pedagogy_reviewer_id':'','review_date':'',
     **{k:'' for k in RUBRIC},'policy_version':'','decision':'','revision_sha256':'','comments':''}
   selected.append(row)
 require(len(selected)==116,'Priority queue must cover 29 active misconceptions and four paths')
 return selected

def audit(source,output):
 start=time.perf_counter();source=source.resolve();output=output.resolve()
 require(source!=output and source not in output.parents,'Audit output must be separate from input snapshot')
 before={p.relative_to(source).as_posix():sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
 manifest=load_json((source/'MANIFEST.json').read_text(encoding='utf-8'))
 expected={v['path']:v for v in manifest['files']}
 require(len(expected)==len(manifest['files']),'Duplicate manifest paths')
 for name,entry in expected.items():
  target=(source/name).resolve();require(source in target.parents,'Unsafe manifest path')
  require(name in before and before[name]==entry['sha256'] and target.stat().st_size==entry['bytes'],'Manifest content mismatch: '+name)
 require(set(before)==set(expected)|{'MANIFEST.json'},'Unmanifested input file')
 data={k:read_rows(source/name) for k,name in COLLECTIONS.items()}
 for kind,rows in data.items():
  id_key='problem_id' if kind=='references' else 'id'
  require(len({r[id_key] for r in rows})==len(rows),'Duplicate IDs in '+kind)
  schema={'$schema':'https://json-schema.org/draft/2020-12/schema',**infer_schema(rows)}
  validator=Draft202012Validator(schema)
  for row in rows:validator.validate(row)
  write_json(output/'schemas'/f'{kind}.schema.json',schema)
 P={r['id']:r for r in data['problems']};D={r['id']:r for r in data['dialogues']};R={r['problem_id']:r for r in data['references']}
 require(set(P)==set(R),'Missing/extra private reference join')
 seed_ids={r['id'] for r in data['seed_misconceptions']}
 for name in ['problems','dialogues','messages','preferences','security']:
  for row in data[name]:
   require(row['split']=='development_only' and row['review_status']=='unreviewed' and row['reviewer_id'] is None,'Fabricated promotion in '+name)
   require(row['misconception_id'] in seed_ids and row['misconception_id']!='T08' and row['curriculum_scope']=='in_scope','Scope/seed join mismatch')
 family_issues=[]
 for name in ['dialogues','messages','preferences','security','references','tutor_contexts']:
  for row in data[name]:
   pid=row['context']['problem_id'] if name=='messages' else row['problem_id']
   require(pid in P,'Missing problem join in '+name)
   require(row['misconception_id']==P[pid]['misconception_id'],'Misconception join mismatch in '+name)
   if row['variant_family']!=P[pid]['variant_family']:family_issues.append({'collection':name,'record_id':row.get('id') or pid,'problem_id':pid,'declared_family':row['variant_family'],'problem_family':P[pid]['variant_family']})
   if 'chapter' in row:require(row['chapter']==P[pid]['chapter'],'Chapter join mismatch')
 for row in data['messages']:require(row['context']['active_problem']==P[row['context']['problem_id']]['problem_text'],'Message active context mismatch')
 for row in data['preferences']:require(row['dialogue_id'] in D and row['problem_id']==D[row['dialogue_id']]['problem_id'],'Preference join mismatch')
 for row in data['tutor_contexts']:
  d=D[row['dialogue_id']];n=len(row['context']);expected_context=[{'role':t['role'],'content':t['text']} for t in d['messages'][:n]]
  require(n<len(d['messages']) and row['context']==expected_context and d['messages'][n]['role']=='tutor' and row['candidate_tutor_response']==d['messages'][n]['text'] and row['candidate_teaching_move']==d['messages'][n]['move'],'Derived tutor context drift')
 require(Counter(r['dialogue_id'] for r in data['tutor_contexts'])==Counter({k:6 for k in D}),'Derived contexts incomplete')
 active={p['misconception_id'] for p in P.values()}
 paths=Counter(d['trajectory'] for d in D.values())
 require(set(paths)==TRAJECTORIES and all(n==len(P) for n in paths.values()),'Trajectory coverage drift')
 math=[]
 for pid,p in P.items():
  try:math.append(check_reference(p,R[pid]))
  except Exception as exc:math.append({'problem_id':pid,'status':'unverified','issue_code':type(exc).__name__,'math_type':R[pid]['math_check']['type']})
 write_json(output/'evidence/independent_math.json',math)
 write_json(output/'evidence/family_join_issues.json',family_issues)
 math_counts=dict(Counter(r['status'] for r in math))
 tutor=[t['text'] for d in D.values() for t in d['messages'] if t['role']=='tutor']
 student=[t['text'] for d in D.values() for t in d['messages'] if t['role']=='student']
 outliers=[];exact_hits=[];short=0
 for d in D.values():
  key=R[d['problem_id']]['expected_answer']
  if len(key)<4:short+=1
  for t in d['messages']:
   if t['role']!='tutor':continue
   codes=[]
   if t['text'].count('?')!=1:codes.append('question_count_not_one')
   if not t['text'].rstrip().endswith('?'):codes.append('does_not_end_in_question')
   if len(t['text'].split())>60:codes.append('over_60_words')
   if len(key)>=4 and key in t['text']:codes.append('literal_long_reference_match');exact_hits.append({'dialogue_id':d['id'],'turn':t['turn']})
   if codes:outliers.append({'dialogue_id':d['id'],'turn':t['turn'],'issue_codes':codes,'status':'machine_triage_not_human_verdict'})
 counts={k:len(v) for k,v in data.items()};counts['dialogue_turns']=sum(len(d['messages']) for d in D.values())
 intent_counts=Counter(r['primary_intent'] for r in data['messages'])
 old_catalog=read_csv(source/'review/intent_catalogue.csv')
 discrepancies=[{'intent':r['intent'],'reported_count':int(r['count']),'observed_count':intent_counts[r['intent']]} for r in old_catalog if int(r['count'])!=intent_counts[r['intent']]]
 corrected=[{'intent':intent,'observed_count':n,'observed_routes':';'.join(sorted({r['expected_route'] for r in data['messages'] if r['primary_intent']==intent})),
   'status':'recomputed_inventory_only_unreviewed_labels','source_sha256':before[COLLECTIONS['messages']]} for intent,n in sorted(intent_counts.items())]
 csv_view(output/'corrected/intent_catalogue_v0_2_audit.csv',corrected)
 queue=priority_queue(list(D.values()),P);csv_view(output/'03_REVIEW_QUEUE.csv',queue)
 write_json(output/'evidence/dialogue_outliers.json',outliers)
 sample=read_csv(source/'review/messages_annotation_sample.csv');M={r['id']:r for r in data['messages']};blinded=[];routing=[]
 for row in sample:
  m=M[row['id']];opaque='annotation_'+digest({'id':m['id'],'context':m['context'],'text':m['raw_student_text']})[:20]
  blinded.append({'annotation_task_id':opaque,'context':json.dumps(m['context'],ensure_ascii=False),'learner_message':m['raw_student_text'],'primary_intent':'','route':'','ambiguity':'','human_help_needed':'','confidence':'','comments':''})
  routing.append({'annotation_task_id':opaque,'source_id':m['id'],'source_sha256':digest(m)})
 csv_view(output/'review_views/rater_A.csv',blinded);csv_view(output/'review_views/rater_B.csv',blinded)
 restricted=source.parent/'_integration_work'/tree_digest(before)[:16]/'restricted';restricted.mkdir(parents=True,exist_ok=True)
 write_json(restricted/'annotation_routing.json',routing)
 # Empty approved projection is deliberate: no approvals exist in the supplied snapshot.
 write_json(output/'approved_export_manifest.json',{'records':0,'approved_examples':[],'human_approvals':0,'source_snapshot_sha256':tree_digest(before),'runtime_ingestion_allowed':False})
 profiles={'problem_texts':text_profile([p['problem_text'] for p in P.values()]),'tutor_turns':text_profile(tutor),'student_turns':text_profile(student),
  'contextual_messages':text_profile([r['raw_student_text'] for r in data['messages']]),
  'security_attack_texts':text_profile([r['attack_text'] for r in data['security']]),'security_control_texts':text_profile([r['matched_control_text'] for r in data['security']])}
 metrics={'source_root':str(source),'snapshot_sha256':tree_digest(before),'manifest_sha256':before['MANIFEST.json'],'manifest_files_verified':len(expected),
  'family_join_issue_count':len(family_issues),'family_join_issue_counts':dict(Counter(r['collection'] for r in family_issues)),
  'data_admission_status':'needs_metadata_repair' if family_issues else 'mechanically_checked_unreviewed',
  'counts':counts,'active_misconception_ids':sorted(active),'missing_seed_ids':sorted(seed_ids-active),'chapter_dialogues':dict(Counter(d['chapter'] for d in D.values())),
  'trajectories':dict(paths),'intent_counts':dict(sorted(intent_counts.items())),'intent_catalogue_discrepancies':discrepancies,
  'message_paraphrase_families':len({r['paraphrase_family'] for r in data['messages']}),'message_style_counts':dict(Counter(r.get('style') for r in data['messages'])),
  'teaching_moves':dict(Counter(t.get('move') for d in D.values() for t in d['messages'] if t['role']=='tutor')),
  'student_states':dict(Counter(t.get('state') for d in D.values() for t in d['messages'] if t['role']=='student')),
  'text_profiles':profiles,'independent_public_prompt_math':math_counts,'literal_long_answer_matches':len(exact_hits),
  'dialogues_omitted_by_supplied_short_key_check':short,'turn_outlier_flags':len(outliers),'priority_review_items':len(queue),'blinded_annotation_items_per_rater':len(blinded),
  'quarantine_separate':all(r['misconception_id']=='T08' for r in data['quarantine']),
  'retrieval_unlabelled':sum(r['gold_passage_ids'] is None and r['is_gold_label'] is False for r in data['retrieval']),
  'source_unchanged':before=={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()},
  'human_approvals':0,'independently_authored_final_cases':0,'runtime_exports':0,'pedagogy_verified':False,
  'audit_seconds':round(time.perf_counter()-start,3),'source_lineage':'tutor contexts depend on dialogues; parent seed is history, not additional independent data'}
 require(metrics['source_unchanged'],'Original source changed during audit')
 write_json(output/'coverage_metrics.json',metrics)
 file_index=[]
 for kind,name in COLLECTIONS.items():
  first=data[kind][0]
  access='restricted_verifier_only' if kind=='references' else 'critic_only' if kind=='preferences' else 'quarantine_only' if kind=='quarantine' else 'engineering_review_only'
  file_index.append({'collection':kind,'source_path':str(source/name),'records':len(data[kind]),'source_sha256':before[name],
    'schema_path':f'schemas/{kind}.schema.json','keys':sorted(first),'example_id':first.get('id') or first.get('problem_id'),
    'access_class':access,'runtime_allowed':False})
 write_json(output/'file_index.json',file_index)
 return metrics

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 result=audit(args.source,args.output)
 print(json.dumps({k:result[k] for k in ['counts','independent_public_prompt_math','family_join_issue_count','data_admission_status','priority_review_items','source_unchanged','human_approvals','runtime_exports']},indent=2))
if __name__=='__main__':main()
