"""Integrated signature walkthrough through the real API. Default: synthetic model, no network.

Teacher publication, a streamed cited hint, a code-graded wrong attempt, a correct
attempt, the teacher trace, student trace denial and edit revocation all use the
actual API with the contextual hint adapter selected.

--live sends the active synthetic problem, recent synthetic turns, the allowed
teaching move and the one-sentence normalized:qe04 card to the configured
provider. It makes at most two provider requests (hint and wrong-attempt
feedback), with retries disabled. Use --live only after that transfer and call
budget are approved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import uuid
from unittest.mock import patch

CODE_ROOT=Path(__file__).resolve().parents[2]
SOURCE_ROOT=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',CODE_ROOT)).resolve()
QID='m2_signature_qe_factor_zero'
CALL_BUDGET=2


class BudgetedClient:
    """Counts generation requests and refuses any beyond the approved budget before sending."""
    def __init__(self,inner,budget=CALL_BUDGET):
        self.inner=inner;self.budget=budget;self.calls=0;self.refused=0;self.sent=[]
    def invoke(self,messages,**kwargs):
        if self.calls>=self.budget:
            self.refused+=1
            raise RuntimeError('Approved provider-call budget exhausted; no request was sent')
        self.calls+=1
        self.sent.append({'messages':[list(m) for m in messages],'options':kwargs})
        return self.inner.invoke(messages,**kwargs)


class SyntheticClient:
    def invoke(self,messages,**kwargs):
        assert kwargs == {'max_tokens':240}
        return SimpleNamespace(content='What factor is shared by both terms without dividing by it [normalized:qe04]?',
                               usage_metadata={'input_tokens':1,'output_tokens':1})


def live_preflight(llm,settings):
    """Stop before any request unless a course model and a verifiable single-attempt client are configured."""
    if not llm.enabled:
        raise RuntimeError('No configured live provider; no call was made')
    if llm.model not in settings['course_models']:
        raise RuntimeError(f'{llm.model} is not a course model; no call was made')
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from quadratic_probe import configure_single_attempt
    client=llm._chat()
    configure_single_attempt(client)
    return client


def read_sse(response):
    events=[];event=None
    for line in response.iter_lines():
        if line.startswith('event: '):
            event=line[7:]
        elif line.startswith('data: '):
            events.append((event,json.loads(line[6:])))
    return events


def check(condition,step):
    if not condition:
        raise RuntimeError(f'Walkthrough check failed: {step}')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true',help='Make at most two approved provider requests')
    args=parser.parse_args(argv)
    run=SOURCE_ROOT/'Directions/git_delivery'/('signature-walkthrough-'+uuid.uuid4().hex[:12])
    run.mkdir(parents=True,exist_ok=False)
    os.environ.update(TUTOR_LLM='auto' if args.live else 'stub',TUTOR_CONTEXTUAL_HINTS='1',TUTOR_API_SEED='0',
                      TUTOR_VAR_DIR=str(run/'state'),TUTOR_BETA_CONFIG='',TUTOR_REQUIRE_BETA='0')
    sys.path.insert(0,str(CODE_ROOT/'src'))
    from fastapi.testclient import TestClient
    from tutor.config import SETTINGS
    from tutor.seed import seed_learner
    from tutor_api.main import create_app
    from v02_integration.runtime import ContextualPreviewTutor
    captured=[]
    init=ContextualPreviewTutor.__init__
    def capture(self,**kwargs):
        init(self,**kwargs);captured.append(self)
    student={'Authorization':'Bearer synthetic-student'}
    teacher={'Authorization':'Bearer synthetic-teacher'}
    session='synthetic-signature-walkthrough'
    budgeted=None;observed={};failure=None
    try:
        with patch.object(ContextualPreviewTutor,'__init__',capture):
            with TestClient(create_app(tokens='synthetic-student:student:synthetic-demo,synthetic-teacher:teacher:synthetic-demo-teacher')) as client:
                tutor=captured[0];seed_learner(tutor.conn,'synthetic-demo',{'alias':'Synthetic demonstration'})
                if args.live:
                    budgeted=BudgetedClient(live_preflight(tutor.llm,SETTINGS.llm))
                else:
                    tutor.llm.enabled=True;tutor.llm.model='SYNTHETIC_MODEL_NOT_A_PROVIDER_CALL'
                    budgeted=BudgetedClient(SyntheticClient())
                tutor.llm._chat=lambda *args:budgeted
                observed['model']=tutor.llm.model
                def request(method,path,headers=student,**kwargs):
                    response=client.request(method,path,headers=headers,**kwargs)
                    if response.status_code!=200:
                        raise RuntimeError(f'Unexpected status {response.status_code} at {path}')
                    return response.json()
                def turn(text):
                    return request('POST','/chat',json={'session_id':session,'text':text})
                def graded():
                    return tutor.graph.get_state({'configurable':{'thread_id':session}}).values
                try:
                    observed['health']=request('GET','/health')
                    sid=request('POST','/teacher/proposals',teacher,json={'concept_id':'qe04','mode':'practice'})['set_id']
                    request('POST',f'/teacher/proposals/{sid}/edit',teacher,json={'question_ids':[QID]})
                    request('POST',f'/teacher/proposals/{sid}/approve',teacher)
                    question=turn('practice');observed['question_id']=question['active_item']
                    check(question['active_item']==QID and budgeted.calls==0,'published signature question selected without a model call')
                    with client.stream('POST','/chat/stream',headers=student,json={'session_id':session,'text':'hint'}) as response:
                        check(response.status_code==200,'streamed hint request accepted')
                        stream=read_sse(response)
                    hint=stream[-1][1]
                    observed['hint']={'reply':hint['reply'],'checks':hint.get('checks'),'model_requests_so_far':budgeted.calls,
                                      'citations':[{'passage_id':c['passage_id'],'reference_sha256':c['reference_sha256']} for c in hint['citations']]}
                    observed['sse']={'event_counts':{name:sum(1 for event,_ in stream if event==name) for name in dict.fromkeys(e for e,_ in stream)},
                                     'token_text_equals_reply':''.join(d['text'] for e,d in stream if e=='token')==hint['reply'],
                                     'delivery':'chunked after the complete turn; not model-token streaming'}
                    check(stream[-1][0]=='done' and observed['sse']['token_text_equals_reply'],'stream ends with the complete reply')
                    wrong=turn('x = 5');state=graded()
                    observed['wrong_attempt']={'route':wrong['route'],'reply':wrong['reply'],'checks':wrong.get('checks'),
                                               'scorable':state['grade']['scorable'],'correct':state['grade']['correct'],
                                               'suspected_misconception':(state.get('diagnosis') or {}).get('misconception_id'),
                                               'model_requests_so_far':budgeted.calls}
                    check(state['grade']['scorable'] and not state['grade']['correct'],'wrong attempt is code-graded incorrect')
                    correct=turn('x = 0 or x = 5');state=graded()
                    observed['correct_attempt']={'accepted':bool(state['grade']['correct']),'active_item':correct['active_item'],
                                                 'model_requests_so_far':budgeted.calls}
                    check(state['grade']['correct'] and correct['active_item'] is None,'correct attempt is accepted without a model call')
                    observed['teacher_trace']=request('GET',f'/teacher/sessions/{session}/trace',teacher)
                    observed['student_trace_status']=client.get(f'/teacher/sessions/{session}/trace',headers=student).status_code
                    check(observed['student_trace_status']==403,'student cannot read the teacher trace')
                    turn('practice')
                    request('POST',f'/teacher/proposals/{sid}/edit',teacher,json={'question_ids':[QID]})
                    observed['revoked_route']=turn('hint')['route']
                    check(observed['revoked_route']=='question_revoked','teacher edit revokes the active question')
                    if not args.live:
                        check(budgeted.calls==2,'exactly two contextual generations in the scripted flow')
                finally:
                    observed['generation_events']=[dict(row) for row in tutor.conn.execute(
                        "SELECT kind,name,outcome,latency_ms,detail FROM trace_events WHERE session_id=? AND kind IN ('llm','v02_generation') ORDER BY id",
                        (session,))]
    except Exception as exc:
        failure=f'{type(exc).__name__}: {exc}'[:300]
    try:
        commit=subprocess.run(['git','-C',str(CODE_ROOT),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
        dirty=bool(subprocess.run(['git','-C',str(CODE_ROOT),'status','--porcelain'],check=True,capture_output=True,text=True).stdout.strip())
    except subprocess.CalledProcessError:
        commit=None;dirty=None
    files=('src/tutor/llm.py','src/tutor/app.py','src/tutor_api/main.py','src/tutor_api/traces.py','src/v02_integration/runtime.py',
           'src/tutor/question_catalog.py','content/milestone2_dev/practice_items.json','scripts/m2/signature_live_walkthrough.py')
    requests=budgeted.calls if budgeted else 0
    evidence={'artifact_type':'signature_api_walkthrough','mode':'live' if args.live else 'synthetic_model',
              'completed':failure is None,'failure':failure,
              'provider_calls':requests if args.live else 0,'synthetic_client_invocations':0 if args.live else requests,
              'call_budget':CALL_BUDGET,'refused_over_budget':budgeted.refused if budgeted else 0,
              'human_review':False,'independent_evaluation':False,
              'git':{'commit':commit,'uncommitted_changes':dirty},
              'code_data_sha256':{name:hashlib.sha256((CODE_ROOT/name).read_bytes()).hexdigest() for name in files},
              **observed,
              'limitations':['Synthetic learner, teacher and publication; not educator-reviewed content.',
                             'One scripted session; no learning, teaching-quality or comprehensive leak-prevention claim.',
                             'In-process API client; not a browser, Docker or second-machine run.']}
    (run/'evidence.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    # Exact generation requests, kept only in the ignored run folder for audit.
    (run/'sent_messages.json').write_text(json.dumps(budgeted.sent if budgeted else [],indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'evidence':str(run/'evidence.json'),'mode':evidence['mode'],'completed':evidence['completed'],
                      'failure':failure,'model':observed.get('model'),'provider_calls':evidence['provider_calls'],
                      'synthetic_client_invocations':evidence['synthetic_client_invocations'],
                      'hint':observed.get('hint',{}).get('reply'),'wrong_attempt_reply':observed.get('wrong_attempt',{}).get('reply'),
                      'git':evidence['git']},indent=2,ensure_ascii=False))
    if failure:
        raise SystemExit('Walkthrough incomplete; inspect the labelled local evidence')


if __name__=='__main__':
    main()
