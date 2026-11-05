"""Version-3 development validation; offline only, no provider calls or held-out selection."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()
sys.path.insert(0,str(CODE/'src'))
os.environ.update(TUTOR_LLM='stub',TUTOR_BETA_LIVE='0',TUTOR_BETA_CONFIG='',TUTOR_REQUIRE_BETA='0')
from filelock import FileLock
from tutor_eval import harness, security
from tutor_eval.post_copy_policy import POLICY


def load(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(temporary,path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['smoke','offline'],default='smoke')
    parser.add_argument('--security',action='store_true')
    args=parser.parse_args()
    assert subprocess.check_output(['git','-C',str(CODE),'branch','--show-current'],text=True).strip()=='Beta'
    assert not subprocess.check_output(['git','-C',str(CODE),'status','--porcelain'],text=True).strip(),'Commit the candidate source before qualification runs'
    root=SOURCE/'Directions/m3_runs/v3'/args.stage;root.mkdir(parents=True,exist_ok=True)
    with FileLock(str(SOURCE/'Directions/m3_runs/matrix.lock'),timeout=1):
        path=root/'INDEX.json';index=load(path) if path.exists() else {'stage':args.stage,'policy':POLICY,'jobs':{}}
        for arm in ['c0','c1','c2','memory_off','direct_answers','e3_after']:
            config=CODE/f'eval/configs/m3_v3_{args.stage}_{arm}.toml';cfg=tomllib.loads(config.read_text(encoding='utf-8'))
            assert cfg['run']['llm']=='stub' and cfg['run']['voice']=='template' and cfg['run']['post_copy_policy']==POLICY
            folder=root/arm
            if arm in index['jobs'] or (folder.exists() and any(folder.iterdir())):
                raise RuntimeError('Existing evidence must be inspected; validation does not silently repeat or select a run: '+arm)
            index['jobs'][arm]={'status':'running','config_sha256':sha(config)};save(path,index)
            run=harness.run(config,out_dir=folder);manifest=load(run/'manifest.json')
            sessions=[json.loads(line) for line in (run/'sessions.jsonl').read_text(encoding='utf-8').splitlines()]
            assert manifest['post_copy_policy']==POLICY and manifest['provider_budget'] is None
            assert all(s['llm_calls']==0 and s['post_copy_measurement']['policy']==POLICY for s in sessions)
            assert manifest['gate']['status']=='pass',manifest['gate']
            index['jobs'][arm]={'status':'completed','run':str(run),'config_sha256':sha(config),'gate':manifest['gate']};save(path,index)
            print('COMPLETED',arm,len(sessions),'sessions',flush=True)
        if args.security:
            private=SOURCE/'socratic_tutor_dataset_v2/builds/v0.10.0/private'
            files=[CODE/'eval/fixtures/m2_security_development.jsonl',private/'attacks.jsonl',private/'clean_controls.jsonl']
            for enabled in [True,False]:
                key='e2_on' if enabled else 'e2_off';folder=root/key
                if key in index['jobs'] or (folder.exists() and any(folder.iterdir())):raise RuntimeError('Inspect existing security evidence')
                index['jobs'][key]={'status':'running'};save(path,index)
                run=security.run(files,'m3_v3_'+args.stage+'_'+key,enabled,out_dir=folder,llm_mode='stub',contextual=True)
                manifest=load(run/'manifest.json');index['jobs'][key]={'status':'completed','run':str(run),'summary':manifest['summary']};save(path,index)
                print('COMPLETED',key,manifest['summary'],flush=True)
        print('INDEX',path,flush=True)


if __name__=='__main__':main()
