"""Run the version-3 live pilot only after its separate explicit budget approval."""
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
os.environ.update(TUTOR_LLM='auto',TUTOR_BETA_LIVE='0',TUTOR_BETA_CONFIG='',TUTOR_REQUIRE_BETA='0',LLM_MODEL='openai/gpt-4.1-mini')
from filelock import FileLock
from tutor_eval import harness
from tutor_eval.provider_budget import ProviderBudget
from tutor_eval.post_copy_policy import POLICY


def load(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):
    temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(temporary,path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-live',action='store_true')
    args=parser.parse_args()
    lock=load(CODE/'Docs/m3/v3/ENGINEERING_CHECKPOINT.json')
    for name,digest in lock['source_config_sha256'].items():
        if sha(CODE/name)!=digest:raise RuntimeError('Source/config changed after the offline checkpoint: '+name)
    for name,digest in lock['development_data_sha256'].items():
        if sha(SOURCE/name)!=digest:raise RuntimeError('Development data changed')
    from tutor.llm import base_url
    if base_url().rstrip('/')!='https://openrouter.ai/api/v1':
        raise ValueError('The approved pilot is scoped to the configured OpenRouter endpoint')
    root=SOURCE/'Directions/m3_runs/v3';receipt=load(root/'PILOT_APPROVAL.json')
    if not args.execute_live:
        print(json.dumps({'mode':'preflight_only','planned_sessions':6,'chapters':3,'arms':['c1','c2'],
            'max_requests':80,'max_usd':.05,'approval':receipt['status'],'provider_requests_sent':0},indent=2))
        return
    if receipt['status']!='approved' or not receipt.get('approved_by') or not receipt.get('approval_quote'):
        raise ValueError('The separate version-3 pilot approval is pending; no provider request sent')
    if subprocess.check_output(['git','-C',str(CODE),'branch','--show-current'],text=True).strip()!='Beta':raise RuntimeError('Use local Beta')
    if subprocess.check_output(['git','-C',str(CODE),'status','--porcelain'],text=True).strip():raise RuntimeError('Commit the reviewed candidate before live execution')
    wallet=ProviderBudget(root/'provider_budget_pilot.json',max_calls=80,max_usd=.05,prior_calls=1036,approval_receipt=root/'PILOT_APPROVAL.json')
    from tutor.llm import api_key
    if not api_key()[0]:raise RuntimeError('Provider unavailable; never substitute an offline run for live validation')
    with FileLock(str(SOURCE/'Directions/m3_runs/matrix.lock'),timeout=1):
        folder=root/'pilot';folder.mkdir(exist_ok=True);index_path=folder/'INDEX.json'
        index=load(index_path) if index_path.exists() else {'purpose':'version3 development pilot, no final qualification','jobs':{}}
        for arm in ['c1','c2']:
            target=folder/arm;config=CODE/f'eval/configs/m3_v3_pilot_{arm}.toml';cfg=tomllib.loads(config.read_text(encoding='utf-8'))
            assert cfg['run']['post_copy_policy']==POLICY and cfg['run']['voice']=='template'
            if arm in index['jobs'] or (target.exists() and any(target.iterdir())):raise RuntimeError('Existing pilot evidence needs inspection; no automatic retry')
            index['jobs'][arm]={'status':'running','config_sha256':sha(config)};save(index_path,index)
            run=harness.run(config,out_dir=target);manifest=load(run/'manifest.json')
            sessions=[json.loads(line) for line in (run/'sessions.jsonl').read_text(encoding='utf-8').splitlines()]
            turns=[row for s in sessions for row in s['post_copy_measurement']['turn_model_observations'] if row['route']=='tutor']
            acceptance={'sessions':len(sessions),'expected_sessions':3,'tutor_route_turns':len(turns),
                'tutor_turns_with_model_call':sum(bool(t['model_calls']) for t in turns),
                'trace_observed_for_all_tutor_turns':all(t['trace_observed'] for t in turns),
                'model_errors':manifest['summary']['policy']['llm_errors'],
                'full_leak_turns':manifest['summary']['leaks']['full_turns'],'gate':manifest['gate']}
            acceptance['pass']=(len(sessions)==3 and bool(turns) and all(t['trace_observed'] and t['model_calls'] for t in turns)
                and acceptance['model_errors']==0 and acceptance['full_leak_turns']==0 and manifest['gate']['status']=='pass')
            index['jobs'][arm]={'status':'completed','run':str(run),'config_sha256':sha(config),'acceptance':acceptance};save(index_path,index)
            print(json.dumps({'arm':arm,'acceptance':acceptance,'budget':wallet.snapshot()},indent=2),flush=True)
            if not acceptance['pass']:raise RuntimeError('Pilot acceptance failed; preserve evidence and investigate without repeating calls')


if __name__=='__main__':main()
