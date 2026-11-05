"""Build a reviewable v3 engineering checkpoint from saved offline evidence; no model calls."""
from __future__ import annotations
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()
sys.path.insert(0,str(CODE/'src'));sys.path.insert(0,str(CODE/'scripts/m3'))
from analyse import citation_audit,security_bounds


def load(path):return json.loads(path.read_text(encoding='utf-8'))
def rows(path):return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def trajectory(s):
    fields=['student','chapter','seed','seeded','named','targeted','cleared','pre','post','practice_summary']
    turns=['index','student','tutor','route','problem','diagnosis','active_item','leaks','quiz_contamination','post_question_exposure','graded_attempt','error']
    return {**{k:s[k] for k in fields},'turns':[{k:t.get(k) for k in turns} for t in s['turns']]}


def main():
    root=SOURCE/'Directions/m3_runs/v3';out=CODE/'Docs/m3/v3';out.mkdir(parents=True,exist_ok=True)
    smoke=load(root/'smoke/INDEX.json');offline=load(root/'offline/INDEX.json')
    conditions=[];receipts=[];replays={};source_commits=set();total_citations=0
    for arm in ['c0','c1','c2','memory_off','direct_answers','e3_after']:
        job=offline['jobs'][arm];assert job['status']=='completed'
        d=Path(job['run']);m=load(d/'manifest.json');sessions=rows(d/'sessions.jsonl');summary=m['summary']
        source_commits.add(m['git']['commit']);assert m['git']['uncommitted_changes'] is False
        assert m['gate']['status']=='pass' and summary['failures']==summary['timeouts']==summary['policy']['llm_errors']==0
        assert all(s['llm_calls']==0 for s in sessions)
        measure=[s['post_copy_measurement'] for s in sessions];decisions=Counter(k for s in measure for a in s['audit'] for k in [a['decision']])
        cites=citation_audit(sessions);total_citations+=cites.get('snapshots',0)
        assert all(cites.get(field,0)==cites.get('snapshots',0) for field in ['valid_snapshot_hash','same_chapter','registered_source_text_match'])
        conditions.append({'condition':arm,'sessions':len(sessions),'success_proxy':summary['task_success'],'mean_quiz_gain':summary['quiz']['mean_gain'],
            'diagnosis_recall':summary['diagnosis']['recall'],'full_leak_turns':summary['leaks']['full_turns'],
            'legacy_post_match_witnesses':sum(s['legacy_full_match_witnesses'] for s in measure),
            'post_copies_removed':sum(len(s['removed_ineligible_post_ids']) for s in measure),
            'post_copies_retained':sum(len(s['post_ids_allowed_to_copy']) for s in measure),
            'post_match_decisions':dict(decisions),'citations':cites,'provider_requests':0})
        by_key={(s['student'],s['seed']):s for s in sessions}
        smoke_dir=Path(smoke['jobs'][arm]['run']);sm=load(smoke_dir/'manifest.json');short=rows(smoke_dir/'sessions.jsonl')
        assert sm['git']['commit']==m['git']['commit'] and sm['git']['uncommitted_changes'] is False
        matched=sum(trajectory(s)==trajectory(by_key[(s['student'],s['seed'])]) for s in short)
        assert matched==len(short)==3
        replays[arm]={'matched':matched,'scheduled':len(short),'excluded':['run/session identifiers','timing','tool-log timing and per-call trace identifiers']}
        for stage,folder,manifest in [('offline',d,m),('smoke',smoke_dir,sm)]:
            receipts.append({'stage':stage,'condition':arm,'run_id':manifest['run_id'],'manifest_sha256':sha(folder/'manifest.json'),'config_sha256':manifest['config']['sha256'],'git':manifest['git']})
    security={}
    for key in ['e2_on','e2_off']:
        d=Path(offline['jobs'][key]['run']);m=load(d/'manifest.json');assert m['summary']['errors']==0 and m['git']['uncommitted_changes'] is False
        security[key]={'run_id':m['run_id'],'summary':m['summary'],'bounds':security_bounds(rows(d/'security.jsonl'))}
        receipts.append({'stage':'offline','condition':key,'run_id':m['run_id'],'manifest_sha256':sha(d/'manifest.json'),'git':m['git']})
    assert len(source_commits)==1
    code_commit=next(iter(source_commits))
    sources=subprocess.check_output(['git','-C',str(CODE),'ls-files','src/tutor','src/tutor_eval','src/tutor_api','src/v02_integration','src/socratic_data','config/app.toml'],text=True).splitlines()
    configs=[str(p.relative_to(CODE)).replace('\\','/') for p in (CODE/'eval/configs').glob('m3_v3_*.toml')]
    sources.extend(load(Path(offline['jobs']['c2']['run'])/'manifest.json')['fixture_input_sha256'])
    sources.append('eval/fixtures/m3_candidate_playbook.json')
    scripts=['scripts/m3/run_v3_pilot.py','scripts/m3/validate_v3.py','scripts/m3/audit_copy_policy.py']
    profile={name:sha(CODE/name) for name in sorted(set(sources+configs+scripts)) if (CODE/name).is_file()}
    data={str(p.relative_to(SOURCE)).replace('\\','/'):sha(p) for p in (SOURCE/'Directions/m3_data/development-v1').glob('*.json') if p.name in ['students.json','pairs.json','assignments.json']}
    tests=(SOURCE/'Directions/git_delivery/v3_full_regression.log').read_text(encoding='utf-8');passed=re.search(r'(\d+) passed in ([\d.]+)s',tests);assert passed and int(passed.group(1))==554
    audit=load(out/'COPY_POLICY_AUDIT.json');coverage=load(root/'COVERAGE_CEILING_DRAFT.json');assert audit['baseline_reproductions']==224
    wallets=[SOURCE/'Directions/m3_runs/provider_budget.json',SOURCE/'Directions/m3_runs/provider_budget_extension_e3.json']
    assert sha(wallets[0])=='2b0e529b378dfc7c68be4375a89a859b9c3c173dbc23f543a602c2c0cdd8b9de'
    assert sha(wallets[1])=='72130f49d2ef764a9bcb6df769fa3387629f5e22f684fd6437cd5444205cc430'
    assert not (root/'provider_budget_pilot.json').exists()
    ci=[]
    for log_name in ['v3_ci_c1.log','v3_ci_eval.log','v3_ci_security.log']:
        log=(SOURCE/'Directions/git_delivery'/log_name).read_text(encoding='utf-8')
        folder=Path(re.search(r'Run folder: (.+)',log).group(1).strip())
        manifest=load(folder/'manifest.json')
        assert manifest['git']['commit']==code_commit and manifest['git']['uncommitted_changes'] is False
        ci.append({'log':log_name,'run_id':manifest['run_id'],'manifest_sha256':sha(folder/'manifest.json'),'cli_gate_exit':0})
    checkpoint={'status':'offline_validated_candidate_human_review_pending','validated_runtime_commit':code_commit,
        'local_branch':'Beta','proposed_tag':'beta-m3-behaviour-v3-candidate','source_config_sha256':profile,'development_data_sha256':data,
        'local_CI_equivalent':ci,'remote_Beta_CI':'not_run_local_only',
        'full_regression':{'passed':554,'seconds':float(passed.group(2)),'log':'Directions/git_delivery/v3_full_regression.log'},
        'smoke_sessions':18,'offline_tutoring_sessions':224,'offline_security_cases':160,'provider_calls_added':0,
        'reproducibility':replays,'conditions':conditions,'security':security,'run_receipts':receipts,
        'copy_policy_audit':audit,'data_coverage':coverage,'new_pilot_approval':'pending','human_reviews':0,
        'final_preregistration':'draft','formal_M3_M4_accepted':False,'new_model_behavior_live_validation':'not_run',
        'model_role_architecture':'Existing shared heuristic controllers/graph; full specialist-agent acceptance remains R3 work',
        'report_script_sha256':sha(Path(__file__))}
    (out/'ENGINEERING_CHECKPOINT.json').write_text(json.dumps(checkpoint,indent=2)+'\n',encoding='utf-8')
    (out/'DATA_COVERAGE.json').write_text(json.dumps(coverage,indent=2)+'\n',encoding='utf-8')
    lines=['# Version 3: engineering checkpoint and next gates','',
        f"The integrated local Beta candidate on `{code_commit[:7]}` passes **554 regressions**, all six three-chapter smoke configurations (18 sessions), the full **224-session offline tutoring matrix** and **160 offline security cases**, with zero execution failures. No provider calls were added. These are stub qualification results, not new live E1-E4 results.",'',
        '## Reproducibility and scoring repair','',
        'All 18 smoke trajectories match their corresponding full-run trajectories, including 6/6 C1/C2 sessions. Identifiers/timing/tool-log timing are excluded. The original frozen transition function is unchanged; all 224 saved live simulator baselines still reproduce. The repair is opt-in and keeps legacy flags visible while filtering post copying through explicit question context.','',
        'The cached audit attributes 161 of 177 old full-match witnesses to the exact application-owned answer-format instruction; 16 are unattributed answer matches and remain semantically unreviewed. All 86 old post-copy triggers are removed in these recorded trajectories. Positive controls retain genuine context-linked disclosure, and echo/context-isolation/privacy regressions pass. This development evidence is not human calibration.','',
        '| Offline condition | Sessions | Success proxy | Mean synthetic quiz change | Full leak turns | Removed post copies | Retained post copies |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in conditions:lines.append(f"| {r['condition']} | {r['sessions']} | {r['success_proxy']} | {r['mean_quiz_gain']:.3f} | {r['full_leak_turns']} | {r['post_copies_removed']} | {r['post_copies_retained']} |")
    lines+=['',f'All {total_citations} offline citation snapshots pass mechanical hash/chapter/source checks. Semantic faithfulness is unreviewed. Telling is an intentional isolated answer-disclosure condition; primary post-answer match flags remain conservative for success qualification.','',
        '## Data adequacy: a capability ceiling to resolve','',
        'The 16 development source cards contain 17 seeded types and 24 card/type associations. Runtime diagnosis loads 9 types and supports only 12/24 associations. Its optimistic development micro-recall ceiling from catalogue coverage alone is **50%** (type-macro ceiling 9/17, 52.9%); seven cards have no loaded seeded diagnosis. These are structural upper bounds, not measured accuracy. More repeats cannot fix the missing runtime IDs.','',
        'R3 and R2 should review the public catalogue, distinguishing evidence and supported task families, complete or explicitly scope the runtime adapters, and keep diagnosis design separate from simulator rules. Existing broad practice/textbook holdings are not equivalent to connected runtime coverage. Independent final-content authorship/new hidden attacks and human relevance/faithfulness labels remain required.','',
        '## The next executable step','',
        'A six-session C1/C2 development pilot is prepared: three existing cards (one per chapter), seed 1, eight turns, fixed gpt-4.1-mini, template voice, no judge. New per-turn telemetry checks actual model calls on tutor-route turns rather than a positive session total. The runner defaults to preflight; execution refuses a pending receipt. Proposed separate cap: **80 requests / USD 0.05**. The prior E3 allowance is purpose-specific and is not reused. Both existing wallets remain byte-identical.','',
        'Pilot success verifies those model-call paths; it does not prove independently designed multi-agent specialists, fix the catalogue ceiling, calibrate human labels or qualify final learning effects. The historical dev_live.toml uses an uncapped LLM voice without the current durable wallet contract and must not be used as a substitute.','',
        '## Final acceptance remains external','',
        'R2 must decide the final preregistration/scoring policy and scope. The teacher/Lead must make actual lesson and question-set decisions. Two independent people must label the existing 63-item packet and the focused 40-item copying packet (30 real contexts + 10 explicitly marked AI controls); no labels/approvals are generated. R3 still owns specialist-agent acceptance and catalogue-based diagnosis review; R4 owns missing defence-layer/semantic evidence. R6 needs an independent clean-machine attestation and actual failed-CI demonstration if the checklist is retained.','',
        'Beta remains local until requested. A draft PR can provide remote CI and team review once publishing is authorized. The old v2 live reports remain attached to their original tags and are not evidence for this changed behaviour. Exact run IDs, source/config/data hashes, coverage bounds and honest gate statuses are in ENGINEERING_CHECKPOINT.json.']
    (out/'STATUS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for name in ['ENGINEERING_CHECKPOINT.json','DATA_COVERAGE.json','STATUS.md']:
        target=SOURCE/'Docs/m3/v3'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(out/name,target)
    print(json.dumps({'checkpoint':str(out/'STATUS.md'),'runtime_commit':code_commit,'tests':554,'smoke':18,'offline_tutoring':224,'security':160,'replays':sum(r['matched'] for r in replays.values()),'offline_citations':total_citations,'provider_calls':0},indent=2))


if __name__=='__main__':main()
