"""Resumable development matrix. Default offline. Live needs a fixed shared wallet and explicit cap."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

CODE = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE', CODE)).resolve()
sys.path.insert(0, str(CODE/'src'))


def save(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['smoke','offline','pilot','live'], default='smoke')
    parser.add_argument('--max-calls', type=int, default=0)
    parser.add_argument('--arms', nargs='+', default=['c0','c1','c2','memory_off','direct_answers','e3_after'])
    parser.add_argument('--security', action='store_true')
    args = parser.parse_args()
    if args.stage in ('pilot','live') and args.max_calls != 902:
        raise SystemExit('Live stage requires the predeclared --max-calls 902 shared cap; prior usage is 98')
    os.environ.update(TUTOR_LLM='auto' if args.stage in ('pilot','live') else 'stub', TUTOR_BETA_LIVE='0',
                      TUTOR_BETA_CONFIG='', TUTOR_REQUIRE_BETA='0')
    from tutor_eval import harness, security
    from tutor_eval.provider_budget import ProviderBudget
    from filelock import FileLock
    root = SOURCE/'Directions/m3_runs'/args.stage
    root.mkdir(parents=True,exist_ok=True)
    with FileLock(str(SOURCE/'Directions/m3_runs/matrix.lock'), timeout=1):
        index_path = root/'INDEX.json'
        index = json.loads(index_path.read_text()) if index_path.exists() else {'stage':args.stage,'jobs':{}}
        for arm in args.arms:
            config = CODE/f'eval/configs/m3_{args.stage}_{arm}.toml'
            digest=hashlib.sha256(config.read_bytes()).hexdigest()
            folder=root/arm
            manifests=list(folder.glob('*/manifest.json')) if folder.exists() else []
            completed=[p for p in manifests if json.loads(p.read_text())['config']['sha256']==digest]
            if len(completed)>1:
                raise RuntimeError('Multiple completed runs for one config; inspect rather than select a result')
            if completed:
                prior=json.loads(completed[0].read_text())
                inputs={**{str(CODE/'src'/name):digest for name,digest in prior['code_sha256'].items()},
                        **{str(Path(name) if Path(name).is_absolute() else CODE/name):digest for name,digest in prior['data'].items()},
                        **{str(CODE/name):digest for name,digest in prior['fixture_input_sha256'].items()}}
                if any(hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest for name,digest in inputs.items()):
                    raise RuntimeError('Source changed since completed run; preserve and inspect: '+arm)
                index['jobs'][arm]={'status':'completed','run':str(completed[0].parent),'config_sha256':digest}
                save(index_path,index)
                print('REUSED',arm,completed[0].parent,flush=True)
                continue
            if index['jobs'].get(arm,{}).get('status')=='running' or (folder.exists() and list(folder.iterdir())):
                raise RuntimeError('Interrupted evidence needs inspection before rerun: '+arm)
            index['jobs'][arm]={'status':'running','started':time.time(),'config_sha256':digest}
            save(index_path,index)
            run=harness.run(config,out_dir=folder)
            manifest=json.loads((run/'manifest.json').read_text())
            index['jobs'][arm]={'status':'completed','run':str(run),'config_sha256':digest,'gate':manifest['gate']}
            save(index_path,index)
            print('COMPLETED',arm,manifest['summary']['sessions'],'sessions',manifest['gate'],flush=True)
        if args.security:
            case_files=[CODE/'eval/fixtures/m2_security_development.jsonl']
            # The original 30 seen attacks/controls are development robustness probes here, not new independent attacks.
            private=SOURCE/'socratic_tutor_dataset_v2/builds/v0.10.0/private'
            case_files += [private/'attacks.jsonl',private/'clean_controls.jsonl']
            wallet=ProviderBudget(SOURCE/'Directions/m3_runs/provider_budget.json',max_calls=902,max_usd=1.,prior_calls=98) if args.stage in ('pilot','live') else None
            for enabled in [True,False]:
                key='e2_on' if enabled else 'e2_off'
                folder=root/key
                manifests=list(folder.glob('*/manifest.json')) if folder.exists() else []
                if manifests:
                    if len(manifests)!=1: raise RuntimeError('Inspect duplicate security runs')
                    prior=json.loads(manifests[0].read_text())
                    if any(hashlib.sha256((CODE/'src'/name).read_bytes()).hexdigest()!=digest
                           for name,digest in prior['code_sha256'].items()):
                        raise RuntimeError('Security source changed; preserve and inspect')
                    print('REUSED',key,flush=True)
                    continue
                if index['jobs'].get(key,{}).get('status')=='running' or (folder.exists() and list(folder.iterdir())):
                    raise RuntimeError('Interrupted security evidence needs inspection before rerun')
                index['jobs'][key]={'status':'running','started':time.time()}
                save(index_path,index)
                run=security.run(case_files,'m3_'+args.stage+'_'+key,enabled,out_dir=folder,
                                 llm_mode='auto' if args.stage in ('pilot','live') else 'stub',contextual=True,provider_budget=wallet)
                manifest=json.loads((run/'manifest.json').read_text())
                index['jobs'][key]={'status':'completed','run':str(run),'summary':manifest['summary']}
                save(index_path,index)
                print('COMPLETED',key,manifest['summary'],flush=True)
        print('INDEX',index_path,flush=True)


if __name__=='__main__':
    main()
