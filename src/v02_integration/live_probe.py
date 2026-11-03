"""Bounded live routing probe against the existing team checkout.

Uses only public legacy POC development examples, never expanded raw content or
private evaluations. Emits response hashes and aggregate trace facts, not keys.
"""
import argparse,hashlib,json,os,sys,time,uuid
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--app-root',type=Path,required=True);p.add_argument('--state-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--adapter',choices=['baseline','contextual'],default='baseline');p.add_argument('--active-item',action='store_true');p.add_argument('--include-wrong-attempt',action='store_true');a=p.parse_args()
 if a.include_wrong_attempt and not a.active_item:p.error('--include-wrong-attempt requires --active-item')
 root=a.app_root.resolve();state=a.state_dir.resolve()
 if state==root or root in state.parents:raise ValueError('Probe state must be outside the team checkout')
 if state.exists():raise ValueError('Use a new, isolated probe state directory')
 state.mkdir(parents=True);os.environ['TUTOR_VAR_DIR']=str(state);os.environ['TUTOR_LLM']='auto';sys.path.insert(0,str(root/'src'))
 from tutor import store
 from tutor.seed import seed_learner,DEMO_LEARNERS
 from tutor.config import db_path
 from tutor.app import TutorApp
 conn=store.connect(db_path());
 for lid,spec in DEMO_LEARNERS.items():seed_learner(conn,lid,spec)
 conn.close()
 if a.adapter=='contextual':
  from v02_integration.runtime import ContextualPreviewTutor
  AppClass=ContextualPreviewTutor
 else:AppClass=TutorApp
 app=AppClass(llm_mode='auto');started=time.perf_counter()
 original_chat=app.llm._chat;budget={'actual_invocations':0};provider_receipts=[]
 class BoundedClient:
  def __init__(self,client):self.client=client
  def invoke(self,messages):
   if budget['actual_invocations']>=2:raise RuntimeError('Probe model-call cap reached')
   budget['actual_invocations']+=1
   reply=self.client.invoke(messages)
   provider_receipts.append({'response_id':getattr(reply,'id',None),'content_type':type(reply.content).__name__,'usage':getattr(reply,'usage_metadata',None) or {},
      'reported_model':(getattr(reply,'response_metadata',None) or {}).get('model_name')})
   return reply
 def bounded_chat(model=None):
  client=original_chat(model);client.max_retries=0;client.max_tokens=120;client.request_timeout=20
  return BoundedClient(client)
 app.llm._chat=bounded_chat
 rows=[];problem='I solved x squared = 5x by dividing both sides by x and got x = 5. Why is there another answer?'
 try:
  if not app.llm.enabled:
   result={'status':'blocked_no_api_key','actual_provider_invocations':0,'credential_values_disclosed':False}
  else:
   if a.active_item:
    proposal=app.propose_set('qe04');app.decide(proposal['set_id'],'approve','SYNTHETIC_TEST_ACTOR_NOT_HUMAN_APPROVAL')
    inputs=['practice']+(['x = 12345'] if a.include_wrong_attempt else [])+['hint','start quiz','hint']
   else:inputs=[problem,'I think dividing is fine']
   for index,text in enumerate(inputs):
    before=app.conn.execute("SELECT COUNT(*) FROM trace_events WHERE kind='llm'").fetchone()[0]
    response=app.turn('v02-probe-'+state.name,'L-A',text)
    events=app.conn.execute("SELECT node,role,outcome,detail FROM trace_events WHERE kind='llm' ORDER BY id").fetchall()
    current=events[before:]
    rows.append({'turn':index+1,'route':response['route'],'response_sha256':hashlib.sha256(response['reply'].encode()).hexdigest(),
      'llm_events':[{'node':r['node'],'role':r['role'],'outcome':r['outcome'],
         'tokens_in':json.loads(r['detail'] or '{}').get('tokens_in'),'tokens_out':json.loads(r['detail'] or '{}').get('tokens_out')} for r in current],
      'output_guard_ok':response.get('checks',{}).get('ok'),'no_raw_response_exported':True})
   result={'status':'provider_responses_observed' if provider_receipts else 'no_successful_provider_responses','actual_provider_invocations':budget['actual_invocations'],'successful_provider_responses':len(provider_receipts),'turns':rows,
      'provider_receipts':provider_receipts,'configured_model':app.llm.model,'cost_usd':None,'cost_status':'not_exposed_by_current_trace_adapter',
      'only_public_legacy_development_data':True,'expanded_data_ingested':False,'credentials_disclosed':False,
      'scope':'isolated wrong-feedback/active-hint and deterministic quiz paths' if a.include_wrong_attempt else 'isolated active-item hint and deterministic quiz paths' if a.active_item else 'baseline diagnostic and misconception-tutor paths only; active-item hints and grading still need audit',
      'runtime_production_approval':False,'adapter':a.adapter,'include_wrong_attempt':a.include_wrong_attempt,'isolated_synthetic_teacher_fixture':a.active_item,
      'candidate_source_sha256':hashlib.sha256((Path(__file__).parent/'runtime.py').read_bytes()).hexdigest() if a.adapter=='contextual' else None,
      'generation_events':[{'outcome':r['outcome'],'detail':json.loads(r['detail'])} for r in app.conn.execute("SELECT outcome,detail FROM trace_events WHERE kind='v02_generation' ORDER BY id").fetchall()]}
 except Exception as exc:
  result={'status':'error','error_class':type(exc).__name__,'actual_provider_invocations':budget['actual_invocations'],'turns':rows,'cost_usd':None}
 finally:app.close()
 result['elapsed_seconds']=round(time.perf_counter()-started,3);a.report.parent.mkdir(parents=True,exist_ok=True)
 a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in result.items() if k in ['status','actual_provider_invocations','elapsed_seconds','scope','error_class']}))
if __name__=='__main__':main()
