"""Offline signature API demonstration. Always uses a synthetic model; no live option.

Creates isolated synthetic learner/teacher state under ignored Directions and
records the real publication, hint, grading, trace and revocation API workflow.
"""
from __future__ import annotations

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


def main():
    run=SOURCE_ROOT/'Directions/git_delivery'/('signature-api-'+uuid.uuid4().hex[:12])
    run.mkdir(parents=True,exist_ok=False)
    os.environ.update(TUTOR_LLM='stub',TUTOR_CONTEXTUAL_HINTS='1',TUTOR_API_SEED='0',
                      TUTOR_VAR_DIR=str(run/'state'),TUTOR_BETA_CONFIG='',TUTOR_REQUIRE_BETA='0')
    sys.path.insert(0,str(CODE_ROOT/'src'))
    from fastapi.testclient import TestClient
    from tutor.seed import seed_learner
    from tutor_api.main import create_app
    from v02_integration.runtime import ContextualPreviewTutor
    captured=[];calls=[]
    init=ContextualPreviewTutor.__init__
    def capture(self,**kwargs):
        init(self,**kwargs);captured.append(self)
    def invoke(messages,**kwargs):
        assert kwargs == {'max_tokens':240}
        calls.append(True)
        return SimpleNamespace(content='What factor is shared by both terms without dividing by it [normalized:qe04]?',
                               usage_metadata={'input_tokens':1,'output_tokens':1})
    student={'Authorization':'Bearer synthetic-student'}
    teacher={'Authorization':'Bearer synthetic-teacher'}
    with patch.object(ContextualPreviewTutor,'__init__',capture):
        with TestClient(create_app(tokens='synthetic-student:student:synthetic-demo,synthetic-teacher:teacher:synthetic-demo-teacher')) as client:
            tutor=captured[0];seed_learner(tutor.conn,'synthetic-demo',{'alias':'Synthetic demonstration'})
            tutor.llm.enabled=True;tutor.llm.model='SYNTHETIC_MODEL_NOT_A_PROVIDER_CALL'
            tutor.llm._chat=lambda *args:SimpleNamespace(invoke=invoke)
            def request(method,path,headers=student,**kwargs):
                response=client.request(method,path,headers=headers,**kwargs)
                if response.status_code!=200:
                    raise RuntimeError(f'Unexpected status {response.status_code} at {path}')
                return response.json()
            sid=request('POST','/teacher/proposals',teacher,json={'concept_id':'qe04','mode':'practice'})['set_id']
            request('POST',f'/teacher/proposals/{sid}/edit',teacher,json={'question_ids':['m2_signature_qe_factor_zero']})
            request('POST',f'/teacher/proposals/{sid}/approve',teacher)
            def turn(text):
                return request('POST','/chat',json={'session_id':'synthetic-signature','text':text})
            question=turn('practice')
            assert question['active_item']=='m2_signature_qe_factor_zero' and not calls
            hint=turn('hint')
            assert hint['checks']['ok'] and len(calls)==1
            assert hint['citations'][0]['passage_id']=='normalized:qe04'
            wrong=turn('x = 5')
            state=tutor.graph.get_state({'configurable':{'thread_id':'synthetic-signature'}}).values
            assert state['grade']['scorable'] and not state['grade']['correct'] and len(calls)==2
            wrong_verdict={'route':wrong['route'],'scorable':True,'correct':False,
                           'suspected_misconception':(state.get('diagnosis') or {}).get('misconception_id')}
            correct=turn('x = 0 or x = 5')
            state=tutor.graph.get_state({'configurable':{'thread_id':'synthetic-signature'}}).values
            assert state['grade']['correct'] and correct['active_item'] is None and len(calls)==2
            trace=request('GET','/teacher/sessions/synthetic-signature/trace',teacher)
            assert any(e['kind']=='llm' for e in trace['events'])
            denied=client.get('/teacher/sessions/synthetic-signature/trace',headers=student).status_code
            assert denied==403
            turn('practice')
            request('POST',f'/teacher/proposals/{sid}/edit',teacher,json={'question_ids':['m2_signature_qe_factor_zero']})
            revoked=turn('hint');assert revoked['route']=='question_revoked' and len(calls)==2
    try:
        commit=subprocess.run(['git','-C',str(CODE_ROOT),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
        dirty=bool(subprocess.run(['git','-C',str(CODE_ROOT),'status','--porcelain'],check=True,capture_output=True,text=True).stdout.strip())
    except subprocess.CalledProcessError:
        commit=None;dirty=None
    files=('src/tutor/llm.py','src/tutor/app.py','src/tutor_api/main.py','src/tutor_api/traces.py','src/v02_integration/runtime.py',
           'src/tutor/question_catalog.py','content/milestone2_dev/practice_items.json','scripts/m2/signature_api_smoke.py')
    evidence={'artifact_type':'synthetic_signature_api_development_smoke','live_provider_calls':0,
              'synthetic_client_invocations':len(calls),'human_review':False,'independent_evaluation':False,
              'git':{'commit':commit,'uncommitted_changes':dirty},
              'code_data_sha256':{name:hashlib.sha256((CODE_ROOT/name).read_bytes()).hexdigest() for name in files},
              'question_id':question['active_item'],'hint':hint['reply'],
              'hint_citations':[{'passage_id':c['passage_id'],'reference_sha256':c['reference_sha256']} for c in hint['citations']],
              'wrong_attempt':wrong_verdict,'correct_attempt_accepted':True,'revoked_route':revoked['route'],
              'student_trace_status':denied,'teacher_trace':trace,
              'limitations':['Synthetic model and teacher; not a live or educator-reviewed demonstration.',
                             'No learning, comprehensive leak-prevention, independent evaluation or Docker claim.']}
    (run/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'evidence':str(run/'evidence.json'),'live_provider_calls':0,'synthetic_client_invocations':len(calls),'git':evidence['git']}))


if __name__=='__main__':
    main()
