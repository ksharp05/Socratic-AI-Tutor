"""Copy-on-write family metadata repair; no relabelling, approval or new data."""
import argparse,copy,json
from pathlib import Path
from .audit import read_rows,digest,write_json,require,COLLECTIONS,sha

def repair(source,destination,report):
 source=source.resolve();destination=destination.resolve()
 require(source!=destination and source not in destination.parents,'Repair destination must be outside original source')
 source_hash_before=sha(source/COLLECTIONS['messages'])
 messages=read_rows(source/COLLECTIONS['messages']);problems={r['id']:r for r in read_rows(source/COLLECTIONS['problems'])}
 revised=[];changes=[]
 for row in messages:
  original=copy.deepcopy(row);pid=row['context']['problem_id'];p=problems[pid]
  require(row['context']['active_problem']==p['problem_text'] and row['misconception_id']==p['misconception_id'] and row['chapter']==p['chapter'],'Cannot safely repair conflicting context')
  require(row['split']=='development_only' and row['review_status']=='unreviewed' and row['reviewer_id'] is None,'Repair cannot promote or rewrite reviewed data')
  fixed={**row,'variant_family':p['variant_family']}
  if fixed!=row:changes.append({'id':row['id'],'parent_sha256':digest(original),'old_variant_family':row['variant_family'],'corrected_variant_family':fixed['variant_family'],'revision_sha256':digest(fixed)})
  require({k:v for k,v in original.items() if k!='variant_family'}=={k:v for k,v in fixed.items() if k!='variant_family'},'Repair modified nonmetadata content')
  revised.append(fixed)
 data=''.join(json.dumps(r,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n' for r in revised).encode()
 target=destination/'dev/contextual_learner_messages.jsonl';target.parent.mkdir(parents=True,exist_ok=True)
 require(not target.exists() or target.read_bytes()==data,'Refusing to overwrite a different derived revision')
 target.write_bytes(data)
 receipt={'derivation_version':'v0_2_1_family_metadata_only','source_root':str(source),'derived_root':str(destination),
  'source_messages_sha256':sha(source/COLLECTIONS['messages']),'derived_messages_sha256':sha(target),'records':len(revised),'changed_records':len(changes),
  'permitted_changed_fields':['variant_family'],'all_context_wording_labels_ids_and_statuses_preserved':True,'remaining_family_join_mismatches':0,
  'original_unchanged':source_hash_before==sha(source/COLLECTIONS['messages']),
  'human_approved':False,'split':'development_only','changes':changes}
 write_json(destination/'METADATA_REPAIR_RECEIPT.json',receipt)
 write_json(report,{k:v for k,v in receipt.items() if k!='changes'})
 return receipt

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 result=repair(a.source,a.destination,a.report);print(json.dumps({k:result[k] for k in ['records','changed_records','remaining_family_join_mismatches','human_approved']},indent=2))
if __name__=='__main__':main()
