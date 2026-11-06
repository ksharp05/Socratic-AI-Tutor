"""Verify the merged-source C1/C2 stub regression baseline without rerunning it."""
from __future__ import annotations
import argparse,hashlib,json,os,sys
from pathlib import Path
CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()
ROOT=SOURCE/'Directions/product_quality/v3'
sys.path.insert(0,str(CODE/'src'));sys.path.insert(0,str(CODE/'scripts/m3'))
from tutor.topic_sources import cards
from report_v3 import trajectory
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):return [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
    index=read(ROOT/'c1_c2_baseline/INDEX.json');assert index['status']=='completed'
    refs={r['passage_id']:r for r in cards()};evidence={};arms={};citations=0
    for name,job in index['jobs'].items():
        run=Path(job['run']);assert sha(run/'manifest.json')==job['manifest_sha256']
        m=read(run/'manifest.json');assert m['git']=={'commit':'3e27ab49146085a48b12189d8863220c1eaafbf6','uncommitted_changes':False}
        sessions=rows(run/'sessions.jsonl');evidence[name]=sessions
        assert all(s['llm_calls']==0 for s in sessions) and m['provider_budget'] is None
        assert m['gate']['status']=='pass' and m['summary']['failures']==m['summary']['timeouts']==0
        for session in sessions:
            for turn in session['turns']:
                for ref in turn['citations']:
                    body={k:v for k,v in ref.items() if k!='reference_sha256'}
                    assert ref['reference_sha256']==hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
                    assert ref['chapter']==session['chapter'] and refs[ref['passage_id']]['text']==ref['text']
                    citations+=1
        if name.startswith('offline_'):
            s=m['summary'];arms[name[-2:]]={'sessions':len(sessions),'unique_cards':len({r['student'] for r in sessions}),'seeds':sorted({r['seed'] for r in sessions}),'diagnosis_recall':s['diagnosis']['recall'],'diagnosis_precision':s['diagnosis']['precision'],'success_proxy':s['task_success'],'synthetic_mean_gain':s['quiz']['mean_gain'],'unchecked_practice':s['checked_practice']['not_checked'],'grading_disagreements':s['checked_practice']['grading_disagreements'],'failures':s['failures'],'timeouts':s['timeouts'],'full_detected_leaks':s['leaks']['full_turns'],'sessions_sha256':sha(run/'sessions.jsonl'),'manifest_sha256':job['manifest_sha256']}
    for arm in ['c1','c2']:
        full={(s['student'],s['seed']):s for s in evidence['offline_'+arm]}
        assert len(full)==48
        assert all(trajectory(s)==trajectory(full[(s['student'],s['seed'])]) for s in evidence['smoke_'+arm])
    a={(s['student'],s['seed']):s for s in evidence['offline_c1']};b={(s['student'],s['seed']):s for s in evidence['offline_c2']}
    paired=sum(trajectory(a[k])==trajectory(b[k]) for k in a)
    report={'source_commit':'3e27ab49146085a48b12189d8863220c1eaafbf6','scope':'Deterministic regression replay after changed runtime/content; repeated cards/seeds, not additional independent data or a final E1 study','baseline_sessions':96,'smoke_sessions':6,'smoke_full_matches':6,'paired_c1_c2_identical_trajectories':paired,'provider_requests':0,'citations_verified':citations,'arms':arms,'earlier_v2_baseline':{'source':'779e788','recall':.208,'precision':.625,'synthetic_mean_gain':.167,'note':'Preserved historical evidence. The current replay is worse on this simulator; cause is not isolated. Runtime/content changes may affect simulator support. No human-learning or causal attribution.'},'human_reviews':0,'independent_final_evaluation':False,'protocol_metadata_correction':'The preparatory prose incorrectly said 24 cards/two seeds; executable frozen configs and actual manifests are 16 cards/three seeds per arm.'}
    text='# Current C1/C2 regression baseline\n\nSource 3e27ab4: 96 offline sessions plus six matching smokes, using the same 16 synthetic development cards and seeds 1/2/3 per arm. These repeats qualify reproducibility after source changes; they are not new independent learner observations. All four jobs pass their execution gates, with zero provider calls.\n\n'
    text+='| Arm | Sessions | Diagnosis recall | Precision | Success proxy | Mean synthetic quiz gain |\n| --- | --- | --- | --- | --- | --- |\n'
    for arm,v in arms.items():text+=f"| {arm} | {v['sessions']} | {v['diagnosis_recall']} | {v['diagnosis_precision']} | {v['success_proxy']}/48 | {v['synthetic_mean_gain']} |\n"
    text+=f"\nAll {paired}/48 paired C1/C2 trajectories are identical; no architecture advantage is observed. All six smoke trajectories match their full runs. {citations} reference snapshots pass identity/hash/chapter checks; semantic source faithfulness remains unreviewed. Each arm has 18 unchecked practice attempts and zero grading disagreements, errors, timeouts or measured full leaks.\n\n"
    text+='The earlier v2 baseline had recall 0.208, precision 0.625 and mean synthetic gain 0.167; the current values are worse. This is a measured regression on the fixed simulator, with no isolated cause or human-learning interpretation. R3/R2 must triage runtime/content and simulator-support changes before a new live efficacy comparison. Do not relabel this as an improvement or inherit old results onto new code.\n\n'
    text+='The preparation note mistakenly described 24 cards/two seeds. The frozen executable configs and manifests actually use 16 cards/three seeds. The original note is retained and the correction is explicit; no run was repeated to fix prose.\n\n'
    text+='Reproduce the aggregate audit offline: scripts/product_quality/report_v3_baseline.py --check. All raw trajectories and manifests remain private under Directions/product_quality/v3/c1_c2_baseline. Human/independent-final reviews remain open.\n'
    return {'BASELINE.json':json.dumps(report,indent=2)+'\n','BASELINE.md':text}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for name,value in build().items():
        p=CODE/'Docs/product_quality/v3'/name
        if args.check:assert p.read_text(encoding='utf-8')==value
        else:p.write_text(value,encoding='utf-8')
    print(json.dumps({'status':'verified' if args.check else 'written'}))
if __name__=='__main__':main()
