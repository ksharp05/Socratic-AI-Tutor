"""One-shot fresh public-case replay against separately frozen source archives, offline only."""
from __future__ import annotations
import argparse,hashlib,json,os,sys
from pathlib import Path
CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()
ROOT=SOURCE/'Directions/product_quality/v3'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(temporary,path)
def profile(app):
    return {str(p.relative_to(app)).replace('\\','/'):sha(p) for name in ['src','content','config'] for p in sorted((app/name).rglob('*')) if p.is_file() and p.suffix in ('.py','.json','.jsonl','.toml')}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--version',required=True,choices=['before','merged']);args=parser.parse_args()
    app_source=ROOT/('before_source' if args.version=='before' else 'merged_source')
    output=ROOT/'fresh_case_replay'/args.version
    if output.exists():raise RuntimeError('Replay exists; preserve rather than repeat')
    protocol=read(ROOT/'FRESH_CASE_PROTOCOL.json');cases_path=ROOT/'case_round_02/cases.jsonl'
    assert sha(cases_path)==protocol['case_sha256']
    cases=[json.loads(line) for line in cases_path.read_text().splitlines() if line.strip()]
    assert len(cases)==len({c['id'] for c in cases})==360
    os.environ.update(TUTOR_LLM='stub',TUTOR_MODEL_DIAGNOSIS='0',TUTOR_BETA_CONFIG='',TUTOR_BETA_LIVE='0',TUTOR_REQUIRE_BETA='0',SOCRATES_SOURCE_WORKSPACE=str(SOURCE))
    sys.path.insert(0,str(app_source/'src'))
    from tutor import store
    from tutor.seed import seed_learner
    from tutor.topic_sources import cards
    from v02_integration.runtime import ContextualPreviewTutor
    assert Path(sys.modules['tutor'].__file__).resolve().is_relative_to(app_source.resolve())
    source_profile=profile(app_source)
    output.mkdir(parents=True)
    state={'status':'running','version':args.version,'protocol_sha256':sha(ROOT/'FRESH_CASE_PROTOCOL.json'),'cases_sha256':sha(cases_path),'runner_sha256':sha(Path(__file__)),'source_profile':source_profile,'completed':0,'actual_human_reviews':0,'model_calls':0,'errors':[],'scope':'One-turn synthetic offline development evidence; no student-learning or live-model claim'}
    save(output/'INDEX.json',state)
    app=ContextualPreviewTutor(llm_mode='stub',defences=True,db_name=str(output/'tutor.db'),checkpoint_name=str(output/'checkpoint.db'))
    references={r['passage_id']:r for r in cards()}
    try:
        for index,case in enumerate(cases):
            sid='fresh-'+case['id'];lid='fresh-learner-'+case['id']
            seed_learner(app.conn,lid,{'alias':'Synthetic one-turn public development learner'})
            # Only the message and public chapter enter the tutor, never the label, slot or rationale.
            out=app.turn(sid,lid,case['message'],chapter=case['chapter'])
            diagnosis=(out.get('diagnosis') or {}).get('misconception_id')
            citations=app.history(sid)[-1].get('citations',[]);citation_errors=[]
            for ref in citations:
                body={k:v for k,v in ref.items() if k!='reference_sha256'}
                if ref.get('reference_sha256')!=hashlib.sha256(store.dumps(body).encode()).hexdigest():citation_errors.append('snapshot_hash')
                source=references.get(ref.get('passage_id'))
                if not source or source.get('text')!=ref.get('text') or ref.get('chapter')!=case['chapter']:citation_errors.append('source_or_chapter')
            calls=app.conn.execute("SELECT count(*) FROM trace_events WHERE session_id=? AND kind='llm'",(sid,)).fetchone()[0]
            assert calls==0,'Offline runner must never invoke a provider'
            mastery=app.conn.execute('SELECT count(*) FROM mastery WHERE learner_id=?',(lid,)).fetchone()[0]
            row={'id':case['id'],'partition':case['partition'],'chapter':case['chapter'],'catalogue_type':case['catalogue_type'],'slot':case['slot'],'proposed_expected':case['expected_misconception'],'observed_diagnosis':diagnosis,'route':out.get('route'),'reply':out['reply'],'checks':out.get('checks'),'citations':citations,'citation_errors':citation_errors,'mastery_rows':mastery,'model_calls':calls}
            with (output/'results.jsonl').open('a',encoding='utf-8') as file:file.write(json.dumps(row)+'\n')
            state['completed']=index+1
            if (index+1)%30==0:save(output/'INDEX.json',state);print(json.dumps({'version':args.version,'completed':index+1}),flush=True)
        assert profile(app_source)==source_profile,'Source changed during replay'
        state.update(status='completed',results_sha256=sha(output/'results.jsonl'));save(output/'INDEX.json',state)
        print(json.dumps({'version':args.version,'status':'completed','cases':state['completed'],'model_calls':0}),flush=True)
    except BaseException as exc:
        state.update(status='failed',error_type=type(exc).__name__);save(output/'INDEX.json',state);raise
    finally:app.close()
if __name__=='__main__':main()
