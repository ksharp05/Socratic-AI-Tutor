"""Measured development run through the real API, with real model calls and isolated state."""
from __future__ import annotations
import concurrent.futures,datetime,hashlib,json,statistics,sys,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from fastapi.testclient import TestClient
from socrates_beta.api import create_app
from socrates_beta.bootstrap import bootstrap
from socrates_beta.repository import Repository

HEADERS={'X-Socrates-Request':'1'}
LABELS={'math_concepts':'Maths concepts','science_concepts':'Science concepts','other_subjects':'Other subjects',
        'natural_english':'Conversational English','checked_practice':'Code-checked practice','known_limits':'Known limitations'}


def main():
    case_file=ROOT/'Docs/beta/DEVELOPMENT_CASES.json';raw=case_file.read_bytes();case_doc=json.loads(raw)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out=ROOT/'Directions/beta_data/evaluation_runs'/stamp;out.mkdir(parents=True)
    (out/'FROZEN_CASES.json').write_bytes(raw)
    settings=json.loads((ROOT/'config/beta/local.json').read_text(encoding='utf-8-sig'));settings['data_directory']=str(out);settings['max_live_calls']=60;settings['audit_directory']=str(out/'provider_responses')
    registry=bootstrap(ROOT,Path(settings['app_root']));repo=Repository(out/'observations.sqlite')
    snapshot={}
    for file in (ROOT/'src/socrates_beta').rglob('*'):
        if file.is_file() and file.suffix in ('.py','.js','.css','.html'):
            snapshot[str(file.relative_to(ROOT))]=hashlib.sha256(file.read_bytes()).hexdigest()
            saved=out/'runtime_snapshot'/file.relative_to(ROOT/'src/socrates_beta');saved.parent.mkdir(parents=True,exist_ok=True);saved.write_bytes(file.read_bytes())
    app=create_app(settings,live=True,registry=registry,repository=repo,testing=True)
    language=app.state.services['language'];results=[]
    def run_case(case):
        started=time.monotonic();row={k:case[k] for k in ('id','group','kind','grade','subject','question')}
        row.update(completed=False,appropriate_abstention=False,turns=[],failure=None)
        try:
            with TestClient(app) as client:
                r=client.post('/api/sessions',json={'grade':case['grade'],'subject':case['subject'],'title':case['question'][:120]},headers=HEADERS)
                if r.status_code!=200:
                    row.update(failure='scope_unavailable',http_status=r.status_code,appropriate_abstention=case['kind']=='limit',finding=case.get('reason','Scope unavailable in admitted dataset.'))
                    return row
                sid=r.json()['id']
                if case['kind']=='checked_math':
                    a=client.post('/api/practice',json={'session_id':sid,'mode':'practice','question_id':case['question_id']},headers=HEADERS)
                    if a.status_code!=200:raise ValueError('practice_start_failed')
                    response=client.post('/api/practice/'+a.json()['id']+'/submit',json={'answer':case['answer'],'request_id':uuid.uuid4().hex},headers=HEADERS)
                    row['assessment_response']=response.json();row['question_id']=case['question_id']
                    row['completed']=response.status_code==200 and response.json().get('status')=='correct'
                    row['finding']='Independent arithmetic from the public givens matched the code checker; the language model did not grade this answer.' if row['completed'] else 'The independent arithmetic answer did not complete the checker path.'
                else:
                    for text in case.get('messages',[case['question']]):
                        response=client.post('/api/chat',json={'session_id':sid,'text':text,'request_id':uuid.uuid4().hex},headers=HEADERS)
                        if response.status_code!=200:raise ValueError('chat_http_'+str(response.status_code))
                        row['turns'].append(response.json())
                    ids=[c['source_id'] for t in row['turns'] for c in t['citations']]
                    if case['kind']=='limit':
                        row['appropriate_abstention']=all(t['move'] in ('unsupported_input','missing_evidence') and t['provider_status']=='not_called' for t in row['turns'])
                        row['finding']=case['reason']
                    else:
                        row['source_match']=any(s in ids for s in case['expected_sources'])
                        row['all_live_accepted']=all(t['provider_status']=='live_accepted' for t in row['turns'])
                        row['completed']=row['source_match'] and row['all_live_accepted']
                        row['finding']=('Live replies passed reply/citation checks and cited an expected textbook source; factual and teaching-quality review remain pending.' if row['completed'] else
                          'A fallback or unexpected source prevented this task from meeting the declared completion criteria.')
                        if not row['completed']:row['failure']='fallback' if not row['all_live_accepted'] else 'expected_source_not_cited'
        except Exception as exc:
            row['failure']=type(exc).__name__+':'+str(exc)[:80];row['finding']='The task failed to complete; the failure is retained in the denominator.'
        finally:
            row['latency_ms']=round((time.monotonic()-started)*1000)
        return row
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(run_case,c):c for c in case_doc['cases']}
        for future in concurrent.futures.as_completed(futures):
            row=future.result();results.append(row)
            print(f"{row['id']} {row['group']}: {'completed' if row['completed'] else row.get('failure') or 'unsupported/clarified'} ({row.get('latency_ms',0)} ms)",flush=True)
            (out/'partial_results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
    results.sort(key=lambda r:r['id'])
    groups=[]
    for key,label in LABELS.items():
        values=[r for r in results if r['group']==key];completed=sum(r['completed'] for r in values)
        groups.append({'id':key,'label':label,'total':len(values),'completed':completed,'completion_rate':completed/len(values),
                       'appropriate_abstentions':sum(r['appropriate_abstention'] for r in values),
                       'median_latency_ms':statistics.median(r['latency_ms'] for r in values)})
    prefer={'S01':0,'M01':1,'C02':2,'M03':3,'S07':4,'H03':5,'C01':6,'P01':7}
    best=sorted([r for r in results if r['completed']],key=lambda r:(prefer.get(r['id'],20),r['latency_ms']))[:8]
    worst=sorted([r for r in results if not r['completed']],key=lambda r:(r['kind']=='limit',r['id']))[:8]
    summary={'available':True,'run_date':datetime.datetime.now(datetime.timezone.utc).isoformat(),'run_id':stamp,
      'development_only':True,'independent_evaluation':False,'human_review':False,'total_cases':len(results),
      'case_file_sha256':hashlib.sha256(raw).hexdigest(),'dataset_id':registry.entries()['active'],
      'dataset_sha256':registry.entries()['datasets'][registry.entries()['active']]['sha256'],
      'live_calls':language.calls,'groups':groups,'cases':results,'best_questions':best,'worst_questions':worst,
      'measurement_note':'Completion means expected-source plus reply-contract checks, or independently calculated maths checked by code. It is not factual accuracy or learning effectiveness.',
      'runtime_sha256':snapshot,'format_repairs':sum(bool(t.get('format_repaired')) for r in results for t in r.get('turns',[])),
      'monetary_cost':None,'provider_receipts':language.receipts}
    (out/'COMPLETE_RESULTS.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    # Keep source excerpts/prompts and internal receipts local; publish only the question/outcome report.
    public={k:v for k,v in summary.items() if k!='provider_receipts'}
    (ROOT/'Docs/beta/EVALUATION_RESULTS.json').write_text(json.dumps(public,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'run_id':stamp,'cases':len(results),'live_calls':language.calls,'completed':sum(r['completed'] for r in results),'groups':groups},indent=2),flush=True)

if __name__=='__main__':main()
