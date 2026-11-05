"""Verify saved product-quality evidence; no provider calls or new experiment runs."""
from __future__ import annotations
from collections import Counter
import hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()
ROOT=SOURCE/'Directions/product_quality/v1'
sys.path.insert(0,str(CODE/'src'))

def load(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    offline,live=load(ROOT/'offline/INDEX.json'),load(ROOT/'live/INDEX.json')
    assert offline['status']==live['status']=='completed' and len(offline['cases'])==len(live['cases'])==8
    assert offline['source_sha256']==live['source_sha256'] and offline['git']==live['git']
    snapshot=ROOT/'source_snapshot';snapshot.mkdir(exist_ok=True)
    for name,expected in live['source_sha256'].items():
        archived=snapshot/name
        if not archived.exists():
            assert sha(CODE/name)==expected,name
            archived.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(CODE/name,archived)
        assert sha(archived)==expected,name
        blob=subprocess.check_output(['git','-C',str(CODE),'show',live['git']+':'+name])
        assert blob.replace(b'\r\n',b'\n')==archived.read_bytes().replace(b'\r\n',b'\n'),name
    prior={
        'Directions/m3_runs/provider_budget.json':'2b0e529b378dfc7c68be4375a89a859b9c3c173dbc23f543a602c2c0cdd8b9de',
        'Directions/m3_runs/provider_budget_extension_e3.json':'72130f49d2ef764a9bcb6df769fa3387629f5e22f684fd6437cd5444205cc430',
        'Directions/m3_runs/v3/provider_budget_pilot.json':'ca964e400d1424eabc96e3a3531b2ed075606b84356cc7630503e24957461a70'}
    for name,expected in prior.items():assert sha(SOURCE/name)==expected,name
    wallet_path=ROOT/'provider_budget.json';wallet=load(wallet_path);attempts=wallet['attempts']
    assert len(attempts)==9 and wallet['refused']==0
    assert all(a['status']=='completed' and a['billed_usd'] is not None for a in attempts)
    cost=sum(a['billed_usd'] for a in attempts)
    assert abs(cost-0.0023244)<1e-12 and abs(cost-sum(a['accounted_usd'] for a in attempts))<1e-12
    assert wallet['policy']['max_calls']==100 and wallet['policy']['max_usd']==0.10
    assert wallet['policy']['approval_receipt_sha256']==sha(ROOT/'BATCH_1_APPROVAL.json')
    trace_costs=[];generations=[];route_calls=Counter();turns=0
    for case in live['cases']:
        folder=ROOT/'live'/case['case']
        assert sha(folder/'turns.jsonl')==case['turns_sha256'] and sha(folder/'trace.json')==case['trace_sha256']
        assert case['gate']=='pass';turns+=case['turns']
        for row in load(folder/'trace.json'):
            detail=json.loads(row['detail']) if isinstance(row.get('detail'),str) else row.get('detail',{})
            if row['kind']=='llm':
                assert row['outcome']=='ok' and detail.get('cost_usd') is not None
                trace_costs.append(detail['cost_usd'])
            if row['kind']=='v02_generation':generations.append(row['outcome'])
        for line in (folder/'turns.jsonl').read_text(encoding='utf-8').splitlines():
            turn=json.loads(line);route_calls[(turn['route'],bool(turn['model']['model_calls']))]+=1
    assert turns==14 and len(trace_costs)==9 and abs(sum(trace_costs)-cost)<1e-12
    assert generations==['accepted']*4
    match=re.search(r'(\d+) passed in ([\d.]+)s',(SOURCE/'Directions/git_delivery/product_quality_full_regression_v1.log').read_text(encoding='utf-8'))
    assert match and int(match[1])==647
    ci=[]
    for name in ['product_quality_ci_c1_v1.log','product_quality_ci_eval_v1.log','product_quality_ci_security_v1.log']:
        log=SOURCE/'Directions/git_delivery'/name
        folder=Path(re.search(r'Run folder: (.+)',log.read_text(encoding='utf-8')).group(1).strip());manifest=load(folder/'manifest.json')
        assert manifest['git']=={'commit':live['git'],'uncommitted_changes':False}
        ci.append({'log':name,'run_id':manifest['run_id'],'manifest_sha256':sha(folder/'manifest.json'),'exit':0})
    public=[json.loads(line) for line in (snapshot/'content/dataset-v0.10.0/practice_questions.jsonl').read_text(encoding='utf-8-sig').splitlines()]
    snapshots=sum(c['citations'].get('snapshots',0) for c in live['cases'])
    phase=load(ROOT/'PHASE_AUTHORIZATION.json');allocated=sum(b['max_usd'] for b in phase['batch_allocations'])
    assert phase['status']=='approved' and phase['max_phase_usd']==10 and allocated<=10
    report={'status':'local_candidate_validated_human_and_final_gates_open','reported_date_Asia_Kolkata':'2026-11-06',
        'runtime_change_commit':'8716bcf','validated_source_commit':live['git'],'published':False,
        'validation':{'full_regression_passed':647,'seconds':float(match[2]),'new_public_regressions':93,
            'offline_journeys_passed':8,'live_journeys_passed':8,'live_turns':14,'model_calls':9,
            'buffered_practice_generations_accepted':4,'buffered_practice_fallbacks':0,
            'citation_snapshots_mechanically_verified':snapshots,'guarded_turns_checked':12,
            'approved_question_displays_without_output_guard':2,'local_CI':ci,'source_files_archived':len(live['source_sha256'])},
        'public_source_scope':{'public_practice_items':len(public),'public_practice_by_chapter':dict(Counter(i['chapter'] for i in public)),
            'loaded_catalogue_types':len(load(snapshot/'content/poc/misconceptions.json'))+sum(json.loads(line)['chapter'] in ('arithmetic_progressions','trigonometry') for line in (snapshot/'content/dataset-v0.10.0/misconceptions.jsonl').read_text(encoding='utf-8-sig').splitlines()),'previous_loaded_types':9,'public_statement_examples_checked':20,
            'checked_AP_error_adapter_task_families':['ap_term','ap_sum','ap_first','ap_difference','ap_count','ap_mean','ap_ledger_term'],
            'connected_AP_practice_families':['ap_term','ap_sum'],
            'interpretation':'Catalogue/public-example coverage is not measured diagnosis accuracy. Five AP adapters remain unit-tested but outside connected practice.'},
        'live_cases':live['cases'],'route_model_coverage':[{'route':k[0],'model_called':k[1],'turns':v} for k,v in route_calls.items()],
        'known_route_limit':'Two deterministic self-correction acknowledgements still use tutor route without a model call; full R3/per-route acceptance is open.',
        'budget':{'phase_ceiling_usd':10,'batch_cap_usd':0.10,'batch_cap_requests':100,'requests_used':9,'provider_reported_usd':cost,
            'provider_cost_coverage':9,'errors':0,'refused':0,'in_flight':0,'allocated_phase_cap_usd':allocated,'unallocated_phase_cap_usd':10-allocated,
            'prior_attempts':1052,'total_provider_attempts':1061,'known_continuation_usd_excluding_original_98_unknown':0.283972+cost,
            'ledger_sha256':sha(wallet_path),'approval_sha256':sha(ROOT/'BATCH_1_APPROVAL.json'),'old_wallets_unchanged':prior,
            'unused_batch_allowance':'All eight cases complete; no automatic repeats or repurposing.'},
        'provenance':{'author':'AI candidate under user authorization; actual R3/R2 review pending','human_reviews':0,'independent_final_content':False,
            'new_E1_E4_results':False,'teaching_semantics':'AI qualitative inspection only; human review pending',
            'synthetic_approvals':'Isolated validation DB fixtures only, not real teacher approval.'},
        'limitations':['Small public developer-authored cases, no human learning or held-out efficacy.',
            'Conservative statement patterns do not cover every paraphrase or reasoning chain.',
            'Full specialist architecture, wider UI acceptance, actual raters, independent installation/safety review and final preregistration remain open.'],
        'source_sha256':live['source_sha256'],'offline_index_sha256':sha(ROOT/'offline/INDEX.json'),
        'live_index_sha256':sha(ROOT/'live/INDEX.json'),'report_script_sha256':sha(Path(__file__))}
    out=CODE/'Docs/product_quality/v1';out.mkdir(parents=True,exist_ok=True)
    (out/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    text=f"""# Product-quality candidate - 6 November 2026

The local Beta candidate adds chapter-scoped AP/trigonometry diagnosis from the public catalogue, exact AP error hypotheses, conservative handling of ambiguous answers, and acknowledgement when a learner states the correct distinction. Generic coefficient/square-root questions no longer automatically diagnose an error. Text evidence stays suspected; the model cannot change the observed cause or invent its evidence quote. Non-quadratic follow-up uses the relevant catalogue instead of a quadratic factor story.

**647 regressions passed**, including 93 new public-source cases. All three exact local CI gates and all eight offline/live journeys passed. The live batch used **9 requests / USD {cost:.7f}**, with all costs exposed and no errors/refusals. Four buffered practice replies were accepted without fallback. All {snapshots} citation snapshots match mechanically; semantic faithfulness is unreviewed. Twelve replies were output-guarded; two approved-question displays follow the existing skip policy.

The user authorized a USD 10 ceiling for this phase. Only USD 0.10 was allocated; USD 9.90 remains unallocated. All eight cases are complete. Total recorded provider usage is 1,061 requests and known continuation cost USD {0.283972+cost:.7f}, excluding the original 98 requests whose money is unknown. Original, E3 and v3-pilot wallets are unchanged. Beta remains local as explicitly requested.

## What the recorded journeys show

- AP: a claim that progressions must increase triggers a relevant probe; a stated correction moves on without awarding mastery.
- Trigonometry: confusing cosine with the reciprocal of sine triggers a conceptual probe; identifying cosecant moves on without a false mastery claim.
- Ordinary chapter questions do not acquire an error label.
- Checked AP off-by-one and triangle-reference errors get targeted questions/hints with actual model calls.
- A request for another learner's grades is declined without a model call.

Catalogue availability rises from 9 to 26 provisional types, preserving source review metadata. All 20 public AP/trig wrong-work examples and separate correct-statement/paraphrase controls are tested. This is coverage of public examples, not diagnosis accuracy. There are {len(public)} public practice items; AP term/sum and the existing triangle-ratio families remain the connected non-quadratic practice pool. Other exact AP adapters are unit-tested and await separate integration/review.

## Limits and next work

This is an AI-authored candidate; actual R3/R2 review remains pending. The eight journeys are public development fixtures with synthetic authorization confined to isolated test databases. No real teacher approval, human labels, independently authored final data or new E1-E4 effectiveness result is claimed. The v2 paid studies and v3 pilot remain attached to their original source/tag snapshots.

Two deterministic acknowledgement turns still carry the tutor route without model calls. Full specialist/per-route acceptance remains open; later routing cleanup can classify these as information actions. Broader paraphrases, UI acceptance, human teaching/citation review, independent installation/security evidence and final preregistration still need work before M3/M4 acceptance.

Runtime changes are at `8716bcf`; exact local CI and live evidence use clean `{live['git'][:7]}`. All 87 captured source/config/data files are preserved privately with exact hashes. `RESULTS.json` has the receipts and limits; `scripts/product_quality/report_results.py` verifies saved evidence offline. Never rerun completed live jobs merely to regenerate reporting.
"""
    current_path=out/'CURRENT_CHECKPOINT.json'
    if current_path.exists():
        current=load(current_path)
        update=("The learner interface now exposes all three chapters, pins the chapter per conversation, keeps references with each reply, and restores saved replies after lost acknowledgements without automatic replay. "
                f"The final connected-app/UI suite passes {current['latest_complete_Main_suite_after_UI']['passed']} tests, including five new learner UI regressions; the earlier four-suite runtime check passed 647. "
                "Assistant-operated browser checks at 1280/390 pixels used isolated stub data, showed no horizontal overflow, and added no provider calls. Temporary servers were stopped.\n\n"
                "Fresh current-candidate C1/C2 stub qualification has 96 sessions plus six matching smokes. Both arms have development recall 0.208, precision 0.625, success proxy 4/48 and synthetic mean gain 0.167; all 240 citation snapshots match mechanically. "
                "The older stub recall was 0.083. These are descriptive development results from only 16 shared cards with three seed repeats; they do not establish independent generalization, a C2 advantage or human learning. See CURRENT_CHECKPOINT.json.\n\n")
        text=text.replace('The local Beta candidate',update+'The local Beta candidate',1)
    (out/'README.md').write_text(text,encoding='utf-8')
    for name in ['README.md','RESULTS.json']:
        p=SOURCE/'Docs/product_quality/v1'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(out/name,p)
    print(json.dumps({'report':str(out/'README.md'),'tests':647,'live_cases':8,'requests':9,'provider_usd':cost,
        'citation_snapshots':snapshots,'public_practice_items':len(public),'provider_calls_added':0},indent=2))

if __name__=='__main__':main()
