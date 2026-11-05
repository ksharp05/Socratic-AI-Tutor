"""Fresh stub-only C1/C2 reproducibility qualification; never reruns old experiments."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()
os.environ.update(SOCRATES_SOURCE_WORKSPACE=str(SOURCE),TUTOR_LLM='stub',TUTOR_BETA_CONFIG='',TUTOR_BETA_LIVE='0',TUTOR_REQUIRE_BETA='0')
sys.path.insert(0,str(CODE/'src'));sys.path.insert(0,str(CODE/'scripts/m3'))
from tutor_eval import harness
from report_v3 import trajectory

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    assert subprocess.check_output(['git','-C',str(CODE),'branch','--show-current'],text=True).strip()=='Beta'
    assert not subprocess.check_output(['git','-C',str(CODE),'status','--porcelain'],text=True).strip()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',choices=['v1','v2'],default='v1')
    args=parser.parse_args()
    root=SOURCE/f'Directions/product_quality/{args.version}/c1_c2_baseline'
    if root.exists():raise RuntimeError('Inspect existing evidence; no silent repeat')
    root.mkdir();index={'status':'running','purpose':'Current public-rule candidate stub qualification, no live E1 result','jobs':{},'replays':{},'provider_requests':0}
    save(root/'INDEX.json',index)
    evidence={}
    for stage in ['smoke','offline']:
        for arm in ['c1','c2']:
            config=CODE/f'eval/configs/pq_v1_{stage}_{arm}.toml'
            folder=harness.run(config,out_dir=root/stage/arm);m=load(folder/'manifest.json')
            sessions=[json.loads(line) for line in (folder/'sessions.jsonl').read_text(encoding='utf-8').splitlines()]
            assert all(s['llm_calls']==0 for s in sessions) and m['provider_budget'] is None
            assert m['gate']['status']=='pass' and not m['git']['uncommitted_changes']
            assert m['summary']['failures']==m['summary']['timeouts']==m['summary']['policy']['llm_errors']==0
            key=stage+'_'+arm;evidence[key]=sessions
            index['jobs'][key]={'run':str(folder),'run_id':m['run_id'],'git':m['git'],'config_sha256':sha(config),
                'manifest_sha256':sha(folder/'manifest.json'),'summary':m['summary']}
            save(root/'INDEX.json',index);print(json.dumps({'job':key,'sessions':len(sessions),'gate':'pass','provider_calls':0}),flush=True)
    for arm in ['c1','c2']:
        full={(s['student'],s['seed']):s for s in evidence['offline_'+arm]}
        short=evidence['smoke_'+arm]
        matched=sum(trajectory(s)==trajectory(full[(s['student'],s['seed'])]) for s in short)
        assert matched==len(short)==3 and len(full)==48
        index['replays'][arm]={'matched':matched,'scheduled':3,'excluded':'identifiers and timing only'}
    index['status']='completed';save(root/'INDEX.json',index)
    print(json.dumps({'baseline_sessions':96,'smoke_sessions':6,'matched_smoke_full':6,'provider_calls':0},indent=2))

if __name__=='__main__':main()
