"""Portable, read-only index setup and integrated service readiness."""
import json
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from ncert_pipeline.build import SCHEMA, insert_passage
from ncert_pipeline.catalogue import sha256
from socrates_beta.container_entrypoint import prepare_index
from tutor.app import TutorApp
from tutor_api.main import create_app


@pytest.fixture
def synthetic_index(tmp_path):
    index=tmp_path/'synthetic.sqlite'
    with sqlite3.connect(index) as conn:
        conn.executescript(SCHEMA)
        insert_passage(conn,{'id':'synthetic:math','source_id':'synthetic:source','book':'jemh1',
            'subject':'Mathematics','title':'Synthetic','page':1,'unit_file_index':4,'kind':'fixture',
            'text':'A synthetic passage about quadratic equations.', 'source_sha256':'a'*64,
            'source_url':'https://example.org/synthetic','human_review_status':'pending'},[10])
    return index


def test_prepared_index_registration_is_hash_checked_idempotent_and_preserves_active(tmp_path,synthetic_index):
    data=tmp_path/'data';digest=sha256(synthetic_index)
    with pytest.raises(ValueError,match='SHA-256'):
        prepare_index(synthetic_index,data,'synthetic','b'*64)
    assert not data.exists()
    first=prepare_index(synthetic_index,data,'synthetic',digest)
    assert first['passages']==1 and first['reused'] is False
    registry=data/'registry.json';before=registry.read_bytes()
    second=prepare_index(synthetic_index,data,'synthetic',digest)
    assert second['reused'] is True and registry.read_bytes()==before
    with pytest.raises(ValueError,match='different dataset'):
        prepare_index(synthetic_index,data,'another-id',digest)
    assert registry.read_bytes()==before
    with sqlite3.connect(synthetic_index) as conn:
        conn.execute("UPDATE passages SET title='Changed synthetic passage'")
    with pytest.raises(ValueError,match='SHA-256'):
        prepare_index(synthetic_index,data,'synthetic',digest)
    assert registry.read_bytes()==before


def test_container_entrypoint_registers_before_launch_and_forces_no_other_action(monkeypatch,tmp_path):
    from socrates_beta import container_entrypoint
    observed={}
    def prepare(index,data,identifier,digest):
        observed['args']=(index,data,identifier,digest)
        return {'id':identifier,'passages':1,'reused':False}
    def execute(application,**kwargs):observed['exec']=(application,kwargs)
    monkeypatch.setattr(container_entrypoint,'prepare_index',prepare)
    import uvicorn
    monkeypatch.setattr(uvicorn,'run',execute)
    config=tmp_path/'config.json';config.write_text(json.dumps({'data_directory':str(tmp_path/'data')}),encoding='utf-8')
    monkeypatch.setenv('TUTOR_BETA_CONFIG',str(config))
    monkeypatch.delenv('TUTOR_BIND_HOST',raising=False);monkeypatch.delenv('TUTOR_BIND_PORT',raising=False)
    monkeypatch.setenv('TUTOR_CONTAINER_INDEX','/sources/knowledge.sqlite')
    monkeypatch.setenv('TUTOR_INDEX_SHA256','a'*64)
    monkeypatch.setenv('TUTOR_DATASET_ID','synthetic')
    container_entrypoint.main()
    assert observed['args']==(Path('/sources/knowledge.sqlite'),tmp_path/'data','synthetic','a'*64)
    assert observed['exec']==('tutor_api.main:app',{'host':'0.0.0.0','port':8000})


def test_readiness_requires_beta_only_when_configured(tmp_path,monkeypatch):
    monkeypatch.delenv('TUTOR_BETA_CONFIG',raising=False)
    tutor=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        monkeypatch.delenv('TUTOR_REQUIRE_BETA',raising=False)
        with TestClient(create_app(tutor=tutor,tokens='a:student:A'),base_url='http://localhost') as client:
            ready=client.get('/health/ready')
            assert ready.status_code==200 and ready.json()['components']=={'graph':'ready','beta':'not_configured'}
            original=tutor.cards
            try:
                tutor.cards={key:value for key,value in original.items() if value.get('chapter')=='quadratic_equations'}
                assert client.get('/health/ready').status_code==503
            finally:tutor.cards=original
        monkeypatch.setenv('TUTOR_REQUIRE_BETA','1')
        with TestClient(create_app(tutor=tutor,tokens='a:student:A'),base_url='http://localhost') as client:
            ready=client.get('/health/ready')
            assert ready.status_code==503 and ready.json()['components']['beta']=='unavailable'
    finally:tutor.close()


def test_mounted_readiness_detects_tampered_index(tmp_path,synthetic_index,monkeypatch):
    root=Path(__file__).resolve().parents[1]
    data=tmp_path/'data';prepare_index(synthetic_index,data,'synthetic',sha256(synthetic_index))
    config=tmp_path/'beta.json';config.write_text(json.dumps({'app_root':str(root),'data_directory':str(data)}),encoding='utf-8')
    monkeypatch.setenv('TUTOR_BETA_CONFIG',str(config));monkeypatch.setenv('TUTOR_BETA_WORKSPACE',str(root))
    monkeypatch.setenv('TUTOR_REQUIRE_BETA','1');monkeypatch.delenv('TUTOR_BETA_LIVE',raising=False)
    tutor=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        with TestClient(create_app(tutor=tutor,tokens='a:student:A'),base_url='http://localhost') as client:
            response=client.get('/health/ready')
            assert response.status_code==200 and response.json()['components']=={'graph':'ready','beta':'ready'}
            assert client.get('/beta/').status_code==200
            with sqlite3.connect(synthetic_index) as conn:
                conn.execute("UPDATE passages SET title='Changed synthetic passage'")
            response=client.get('/health/ready')
            assert response.status_code==503 and response.json()['components']['beta']=='unavailable'
            assert str(tmp_path) not in response.text
    finally:tutor.close()


def test_integrated_compose_overlay_declares_readonly_index_and_offline_model():
    yaml=pytest.importorskip('yaml')
    root=Path(__file__).resolve().parents[1]
    overlay=yaml.safe_load((root/'docker-compose.integrated.yml').read_text(encoding='utf-8'))
    api=overlay['services']['api'];env=api['environment']
    assert env['TUTOR_LLM']=='stub' and env['TUTOR_BETA_LIVE']=='0' and env['TUTOR_REQUIRE_BETA']=='1'
    assert env['TUTOR_CONTAINER_INDEX']=='/sources/knowledge.sqlite'
    assert api['volumes'][0]['read_only'] is True
    assert 'TUTOR_INDEX_PATH:?' in api['volumes'][0]['source']
    assert 'TUTOR_INDEX_SHA256:?' in env['TUTOR_INDEX_SHA256']
    assert '/health/ready' in api['healthcheck']['test'][-1]


def test_container_build_excludes_private_workspace_and_local_config():
    root=Path(__file__).resolve().parents[1]
    patterns=set((root/'.dockerignore').read_text(encoding='utf-8').splitlines())
    assert {'Directions/','heldout_private/','.workspace_migration/','config/beta/local.json',
            'eval/','socratic_tutor_dataset*','.env'} <= patterns


def test_entrypoint_localhost_smoke_from_prepared_index(tmp_path,synthetic_index):
    import os, socket, subprocess, sys, time, urllib.error, urllib.request
    root=Path(__file__).resolve().parents[1]
    data=tmp_path/'data';config=tmp_path/'beta.json'
    config.write_text(json.dumps({'app_root':str(root),'data_directory':str(data)}),encoding='utf-8')
    runtime=tmp_path/'runtime';runtime.mkdir()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env=os.environ.copy()
    env.update({'TUTOR_CONTAINER_INDEX':str(synthetic_index),'TUTOR_INDEX_SHA256':sha256(synthetic_index),
                'TUTOR_DATASET_ID':'synthetic','TUTOR_BETA_CONFIG':str(config),'TUTOR_BETA_WORKSPACE':str(root),
                'SOCRATES_SOURCE_WORKSPACE':str(root),'TUTOR_REQUIRE_BETA':'1','TUTOR_BETA_LIVE':'0',
                'TUTOR_LLM':'stub','TUTOR_VAR_DIR':str(runtime),'TUTOR_API_SEED':'1',
                'TUTOR_API_TOKENS':'synthetic-student:student:L-S,synthetic-teacher:teacher:T-S',
                'TUTOR_BIND_HOST':'127.0.0.1','TUTOR_BIND_PORT':str(port),
                'PYTHONPATH':str(root/'src')+os.pathsep+str(root/'socratic_tutor_dataset_v2'/'src')})
    proc=subprocess.Popen([sys.executable,'-m','socrates_beta.container_entrypoint'],cwd=Path.cwd(),env=env,
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    try:
        base=f'http://127.0.0.1:{port}'
        for _ in range(100):
            if proc.poll() is not None:
                raise AssertionError('Synthetic server exited during startup: '+proc.stdout.read())
            try:
                with urllib.request.urlopen(base+'/health/ready',timeout=1) as response:
                    if json.load(response)['status']=='ready':break
            except (OSError,urllib.error.URLError):pass
            time.sleep(.1)
        else:raise AssertionError('Synthetic server did not become ready')
        with urllib.request.urlopen(base+'/beta/',timeout=2) as response:assert response.status==200
        def post(path,token,payload):
            request=urllib.request.Request(base+path,data=json.dumps(payload).encode(),method='POST',
                    headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
            with urllib.request.urlopen(request,timeout=10) as response:return json.load(response)
        proposal=post('/teacher/proposals','synthetic-teacher',{'concept_id':'qe04','mode':'practice'})
        assert post('/teacher/proposals/'+proposal['set_id']+'/approve','synthetic-teacher',{})['status']=='published'
        response=post('/chat','synthetic-student',{'text':'practice','chapter':'quadratic_equations'})
        assert response['active_item'] and response['route']=='set_question'
    finally:
        proc.terminate()
        try:proc.wait(timeout=10)
        except subprocess.TimeoutExpired:proc.kill();proc.wait(timeout=5)
        if proc.stdout:proc.stdout.close()


def test_index_search_understands_spelled_out_trigonometric_ratios(tmp_path):
    from socrates_beta.knowledge import DatasetRegistry
    from socrates_beta.ports import Scope
    index=tmp_path/'trig.sqlite'
    with sqlite3.connect(index) as conn:
        conn.executescript(SCHEMA)
        insert_passage(conn,{'id':'synthetic:trig','source_id':'synthetic:source','book':'jemh1',
            'subject':'Mathematics','title':'Ratios','page':1,'unit_file_index':8,'kind':'fixture',
            'text':'For angle A, sin(A) is opposite over hypotenuse, cos(A) is adjacent over hypotenuse, and tan(A) is opposite over adjacent.',
            'source_sha256':'a'*64,'source_url':'https://example.org/synthetic','human_review_status':'pending'},[10])
    registry=DatasetRegistry(tmp_path/'data');registry.register('synthetic-trig',index,title='Synthetic',activate=True)
    for query in ('sine cosine','tangent','tan'):
        results=registry.knowledge().search(query,Scope(10,'Mathematics','jemh1',8))
        assert [item['id'] for item in results]==['synthetic:trig']


def test_container_build_has_portable_math_and_beta_inputs():
    root=Path(__file__).resolve().parents[1]
    for rel in ('README.md','Dockerfile','docker-compose.yml','config/beta/container.json',
                'src/socratic_data/math_kernel.py','src/socratic_data/tasks.py',
                'src/socrates_beta/container_entrypoint.py'):
        assert (root/rel).is_file(),rel
