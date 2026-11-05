"""Reconstruct saved v2 engineering evidence offline; never runs a model or experiment."""
from __future__ import annotations
import argparse,ast,hashlib,json,os,re,shutil,subprocess
from collections import Counter
from pathlib import Path
CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()
ROOT=SOURCE/'Directions/product_quality/v2'
OUT=CODE/'Docs/product_quality/v2'

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [json.loads(line) for line in p.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
def git(*args):return subprocess.check_output(['git','-C',str(CODE),*args])
def profile_snapshot(index,folder):
    for name,expected in index['source_sha256'].items():assert sha(folder/name)==expected,name

def citation(ref,chapter):
    body={k:v for k,v in ref.items() if k!='reference_sha256'}
    encoded=json.dumps(body,ensure_ascii=False,sort_keys=True)
    assert ref['reference_sha256']==hashlib.sha256(encoded.encode()).hexdigest()
    assert ref['chapter']==chapter

def panel(version):
    folder=ROOT/'offline'/version;index=load(folder/'INDEX.json')
    assert index['status']=='completed' and len(index['cases'])==32
    assert index['protocol_sha256']==sha(CODE/'eval/fixtures/product_quality_v2_panel.json')
    assert index['runner_sha256']==sha(CODE/'scripts/product_quality/run_v2_panel.py')
    snapshot=ROOT/('before_source' if version=='before' else 'after_source')
    profile_snapshot(index,snapshot)
    categories={};cites=0;turns=0
    spec={c['id']:c for c in load(CODE/'eval/fixtures/product_quality_v2_panel.json')['cases']}
    for case in index['cases']:
        case_root=folder/case['id']
        assert sha(case_root/'turns.jsonl')==case['turns_sha256'] and sha(case_root/'trace.json')==case['trace_sha256']
        transcript=rows(case_root/'turns.jsonl');assert len(transcript)==case['turns']
        assert [t['student'] for t in transcript]==spec[case['id']]['messages']
        assert case['model_calls']==0 and case['functional_checks_pass']==(not case['failures'])
        for turn in transcript:
            assert turn['model_calls']==0
            for ref in turn['citations']:citation(ref,spec[case['id']]['chapter']);cites+=1
        group=categories.setdefault(case['category'],{'cases':0,'passed':0});group['cases']+=1;group['passed']+=case['functional_checks_pass']
        turns+=len(transcript)
    assert cites==sum(c['citation_snapshots'] for c in index['cases'])
    return {'cases':32,'turns':turns,'passed':sum(c['functional_checks_pass'] for c in index['cases']),'citation_snapshots_verified':cites,'provider_requests':0,'categories':categories,'index_sha256':sha(folder/'INDEX.json')}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    lock=load(ROOT/'SOURCE_LOCK.json');assert lock['protocol_sha256']==load(ROOT/'PANEL_LOCK.json')['sha256']
    for name,expected in lock['profile'].items():assert sha(ROOT/'after_source'/name)==sha(CODE/name)==expected,name
    before,after=panel('before'),panel('after')
    assert before['passed']==10 and after['passed']==32 and before['turns']==after['turns']==42
    log=SOURCE/'Directions/git_delivery/product_quality_v2_final_regression.log';text=log.read_text(encoding='utf-8')
    match=re.search(r'(\d+) passed in ([\d.]+)s',text);assert match and int(match[1])==815 and sha(log)==lock['full_regression_log_sha256']
    ci={}
    for kind in ['c1','eval','security']:
        p=SOURCE/f'Directions/git_delivery/v2_final_ci_{kind}.log';run=Path(re.search(r'Run folder: (.+)',p.read_text(encoding='utf-8'))[1].strip());m=load(run/'manifest.json')
        assert m['git']=={'commit':lock['git'],'uncommitted_changes':False}
        if kind!='security':assert m['gate']['status']=='pass'
        else:assert m['summary']['errors']==0 and m['summary']['attack_success_rate']==0 and m['summary']['false_block_rate']==0
        ci[kind]={'run':str(run),'manifest_sha256':sha(run/'manifest.json'),'gate':'pass'}
    base=load(ROOT/'c1_c2_baseline/INDEX.json');assert base['status']=='completed'
    baseline={};base_cites=0
    for name,job in base['jobs'].items():
        run=Path(job['run']);assert sha(run/'manifest.json')==job['manifest_sha256']
        m=load(run/'manifest.json');assert m['git']=={'commit':lock['git'],'uncommitted_changes':False}
        sessions=rows(run/'sessions.jsonl');assert all(s['llm_calls']==0 for s in sessions)
        for session in sessions:
            for turn in session['turns']:
                for ref in turn['citations']:citation(ref,session['chapter']);base_cites+=1
        if name.startswith('offline_'):
            s=m['summary'];baseline[name[-2:]]={'sessions':len(sessions),'diagnosis_recall':s['diagnosis']['recall'],'diagnosis_precision':s['diagnosis']['precision'],'success_proxy':s['task_success'],'synthetic_mean_gain':s['quiz']['mean_gain'],'failures':s['failures'],'full_detected_leaks':s['leaks']['full_turns'],'sessions_sha256':sha(run/'sessions.jsonl')}
    assert all(v['matched']==v['scheduled']==3 for v in base['replays'].values())
    sec=load(ROOT/'security/INDEX.json');assert sec['status']=='completed'
    for job in sec['jobs'].values():assert sha(Path(job['run'])/'manifest.json')==job['manifest_sha256'] and job['operations']['model_requests_logged']==0
    prior={'Directions/m3_runs/provider_budget.json':'2b0e529b378dfc7c68be4375a89a859b9c3c173dbc23f543a602c2c0cdd8b9de','Directions/m3_runs/provider_budget_extension_e3.json':'72130f49d2ef764a9bcb6df769fa3387629f5e22f684fd6437cd5444205cc430','Directions/m3_runs/v3/provider_budget_pilot.json':'ca964e400d1424eabc96e3a3531b2ed075606b84356cc7630503e24957461a70','Directions/product_quality/v1/provider_budget.json':'67ab16bc91a476ac5bf16b4c4f4e3e8a120328fa897e8b3dcd75e57b2724c721'}
    for name,expected in prior.items():assert sha(SOURCE/name)==expected,name
    approval=load(ROOT/'BATCH_APPROVAL.json');assert approval['status']=='pending_transmission_approval'
    assert not (ROOT/'provider_budget.json').exists() and not (ROOT/'live').exists()
    phase=load(SOURCE/'Directions/product_quality/v1/PHASE_AUTHORIZATION.json');allocated=sum(b['max_usd'] for b in phase['batch_allocations']);assert allocated==.5 and phase['max_phase_usd']==10
    frozen=git('ls-tree','-r','--name-only','466bcaa','--','Docs/m4','Docs/m3/v3','Docs/product_quality/v1').decode().splitlines()
    for name in frozen:assert git('show','466bcaa:'+name).replace(b'\r\n',b'\n')==(CODE/name).read_bytes().replace(b'\r\n',b'\n'),name
    def transition(blob):return ast.dump(next(n for n in ast.parse(blob).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='run_session'),include_attributes=False)
    assert transition(git('show','12d541e:src/tutor_eval/harness.py').decode())==transition((CODE/'src/tutor_eval/harness.py').read_text(encoding='utf-8'))
    browser=load(ROOT/'ui_browser/BROWSER_RECEIPT.json');assert browser['status']=='passed' and all(v==0 for v in browser['database_counts'].values()) and browser['servers_stopped']
    for name,expected in browser['screenshots'].items():assert sha(ROOT/'ui_browser'/name)==expected
    raw=load(CODE/'content/product_quality/v2/concept_help.json');assert len(raw['cards'])==7 and len(raw['explanations'])==12 and raw['human_reviews']==0
    paired=rows(OUT/'PAIRED_REVIEW.jsonl');source_reviews=rows(OUT/'SOURCE_REVIEW.jsonl')
    assert len(paired)==32 and len(source_reviews)==12
    human=sum(bool(r.get('reviewer')) for r in paired+source_reviews)
    report={'status':'offline_candidate_qualified_live_transmission_approval_pending','date_Asia_Kolkata':'2026-11-06','source_git':lock['git'],'previous_source_git':'466bcaad466d93d3ca7f0a4a6a21dd5fc87a213a','publication':'Keep Beta local; no push or PR','improvements':['Direct short source-backed explanations for twelve concept requests','Maths intent survives frustration/support requests and whitespace wrapping','Explicit correction acknowledgements are information turns, without model or mastery claims','Smaller practice support asks for givens without advancing the hint','Owned quiz/interrupted-session state restores and locks conflicting actions; unfinished quiz can be left without scoring'],
        'validation':{'full_regressions':815,'full_seconds':float(match[2]),'new_tests_since_v1':163,'new_formatting_regressions':122,'local_CI':ci,'offline_before':before,'offline_after':after,'baseline_sessions':96,'baseline_smokes':6,'matching_smokes':6,'baseline_citations_verified':base_cites,'baseline':baseline,'security':{k:v['summary'] for k,v in sec['jobs'].items()},'browser':browser},
        'failures_preserved':{'initial_definition_formatting':{'passed':37,'scheduled':48,'failed':11},'initial_guard_formatting':{'matched':4,'scheduled':12,'missed':8},'test_launch_missing_source_env':{'passed':781,'fixture_errors':34,'cause':'SOCRATES_SOURCE_WORKSPACE omitted; fixed launch, no product-code change','log_sha256':sha(SOURCE/'Directions/git_delivery/product_quality_v2_regression_missing_source_env.log')},'pre_hardening_offline_index_sha256':sha(ROOT/'offline/after-attempt-1-pre-format-hardening/INDEX.json')},
        'data':load(ROOT/'DATA_SCOPE.json'),'reference_cards':7,'explicit_concepts':12,'human_reviews':human,'independent_final_evaluation':False,'formal_M3_M4_accepted':False,
        'budget':{'new_provider_requests':0,'new_spend_usd':0,'total_provider_attempts':1061,'known_continuation_usd_excluding_original_98_unknown':.2862964,'phase_ceiling_usd':10,'phase_actual_usd':.0023244,'allocated_caps_usd':allocated,'unallocated_cap_usd':10-allocated,'prepared_live_cap_requests':200,'prepared_live_cap_usd':.4,'live_status':'Automatic approval review rejected destination/payload authorization; user reply pending','wallet_created':False,'prior_wallet_hashes_unchanged':prior},
        'preservation':{'historical_documents_unchanged':len(frozen),'legacy_run_session_AST_identical':True,'source_files_archived':len(lock['profile']),'old_pilot_and_E1_E4_not_repeated':True},
        'limits':['Developer-authored public panel, including cases targeted by implementation; 32 shared journeys, not 64 independent observations.','Offline templates only for v2: no new live-model result or latency/cost estimate.','Formatting variants and seed repeats are not independent learners or efficacy samples.','C1/C2 stub results are identical; diagnosis recall remains 0.208. No architecture or learning advantage.','27/80 security cases per condition remain unsupported; overlay checks are not on-disk index poisoning or exhaustive safety.','Seven source paraphrases and twelve explanations remain unapproved by an actual teacher.','Independent raters/final content, final preregistration, specialist architecture review, another person installation and remote CI failure evidence remain open.'],
        'provenance':{'source_lock_sha256':sha(ROOT/'SOURCE_LOCK.json'),'protocol_sha256':sha(CODE/'eval/fixtures/product_quality_v2_panel.json'),'reporter_sha256':sha(Path(__file__)),'prior_reports':'Preserved; do not regenerate v1 report against changed phase allocation.'}}
    if args.check:
        assert load(OUT/'RESULTS.json')==report,'Saved report differs; inspect changed evidence before regeneration'
        print(json.dumps({'verified':True,'tests':815,'panel':'10/32 -> 32/32 offline','new_provider_requests':0,'historical_documents_unchanged':len(frozen)}));return
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    target=SOURCE/'Docs/product_quality/v2';target.mkdir(parents=True,exist_ok=True);shutil.copy2(OUT/'RESULTS.json',target/'RESULTS.json')
    print(json.dumps({'report':str(OUT/'RESULTS.json'),'tests':815,'baseline_citations':base_cites,'new_provider_requests':0}))

if __name__=='__main__':main()
