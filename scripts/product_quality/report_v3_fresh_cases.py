"""Reproduce fresh v3 aggregate reports from frozen evidence; no network calls."""
from __future__ import annotations
import argparse,hashlib,json,os
from collections import Counter
from pathlib import Path
CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()
ROOT=SOURCE/'Directions/product_quality/v3';DEST=CODE/'Docs/product_quality/v3'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):return [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(items):
    pos=[r for r in items if r['proposed_expected'] is not None];neg=[r for r in items if r['proposed_expected'] is None]
    return {'cases':len(items),'incorrect_claim_targets':len(pos),'target_hits':sum(r['observed_diagnosis']==r['proposed_expected'] for r in pos),'no_error_targets':len(neg),'false_labels':sum(r['observed_diagnosis'] is not None for r in neg),'wrong_type_labels':sum(r['observed_diagnosis'] is not None and r['observed_diagnosis']!=r['proposed_expected'] for r in pos)}
def build():
    protocol=read(ROOT/'FRESH_CASE_PROTOCOL.json');snapshot=read(ROOT/'REPORT_INPUTS_SNAPSHOT.json')
    cases=rows(ROOT/'case_round_02/cases.jsonl');ri=read(ROOT/'blind_label_review_reconciled_01/INDEX.json')
    assert sha(ROOT/'case_round_02/cases.jsonl')==protocol['case_sha256']
    assert sha(ROOT/'blind_label_review_reconciled_01/reviews.jsonl')==ri['reviews_sha256']
    cmap={r['id']:r for r in cases};reviews={r['case_id']:r for r in rows(ROOT/'blind_label_review_reconciled_01/reviews.jsonl')}
    assert len(cmap)==len(reviews)==360 and cmap.keys()==reviews.keys()
    agreed=set();disagreed=[];uncertain=[]
    for cid,case in cmap.items():
        r=reviews[cid]
        if r['validation_errors'] or r['decision']=='ambiguous':uncertain.append(cid);continue
        label=r['misconception_id'] if r['decision']=='incorrect_claim' else None
        if label==case['expected_misconception']:agreed.add(cid)
        else:disagreed.append(cid)
    variants={}
    for version in ['before','merged']:
        folder=ROOT/'fresh_case_replay'/version;index=read(folder/'INDEX.json');result=rows(folder/'results.jsonl')
        assert index['status']=='completed' and len(result)==360 and index['results_sha256']==sha(folder/'results.jsonl')
        assert {r['id'] for r in result}==cmap.keys()
        variants[version]={'source_commit':protocol['baseline_commit' if version=='before' else 'candidate_commit'],'all_proposed_labels':metrics(result),'ai_agreement_subset':metrics([r for r in result if r['id'] in agreed]),'partitions':{p:metrics([r for r in result if r['partition']==p]) for p in ['development','challenge','confirmation']},'by_type':{mid:metrics([r for r in result if r['catalogue_type']==mid]) for mid in sorted({r['catalogue_type'] for r in result})},'guard_rejections':sum(not(r['checks'].get('ok') or r['checks'].get('skipped')) for r in result),'unexpected_mastery_rows':sum(r['mastery_rows'] for r in result),'citation_snapshots':sum(len(r['citations']) for r in result),'citation_errors':sum(len(r['citation_errors']) for r in result),'model_calls':sum(r['model_calls'] for r in result),'results_sha256':index['results_sha256']}
    for path,expected in snapshot['frozen_original_wallets'].items():assert sha(SOURCE/path)==expected,'Historical wallet changed'
    phase=snapshot['phase']
    for a in phase['batch_allocations']:
        assert a['status'].startswith('completed')
        if 'ledger_sha256' in a:assert sha(SOURCE/a['wallet'])==a['ledger_sha256']
    report={'scope':'AI-authored one-turn public development evidence, offline only; no human, learning or final-evaluation claim','protocol_sha256':sha(ROOT/'FRESH_CASE_PROTOCOL.json'),'cases':360,'catalogue_types':30,'partitions':dict(Counter(c['partition'] for c in cases)),'actual_human_reviews':0,'label_review':{'author_model':'openai/gpt-6-luna','reviewer_model':'google/gemini-3.1-flash-lite','responses':360,'invalid_evidence':ri['validation_errors'],'ambiguous':ri['ambiguous'],'generator_reviewer_agreements':len(agreed),'disagreements':len(disagreed),'excluded_uncertain':len(uncertain),'reviews_sha256':ri['reviews_sha256'],'initial_review_failure':'One non-verbatim evidence quote; original outputs preserved, continuation sent only unreviewed groups','duplicate_provider_requests':0},'variants':variants,'budget_snapshot':{'total_provider_attempts':snapshot['total_provider_attempts'],'known_continuation_usd':snapshot['known_continuation_usd'],'phase_provider_reported_usd':phase['actual_spend_usd'],'phase_accounted_usd':phase['accounted_phase_usd'],'phase_ceiling_usd':10,'remaining_accounted_ceiling_usd':10-phase['accounted_phase_usd'],'unknown_cost_limits':snapshot['unknown_cost_limits']},'remaining_gates':['Human case, source and teaching review','R3 diagnosis quality and specialist/tool-selection acceptance','R3 integration of prepared R2/R4 services','Independent final authors and raters','Final scope, preregistration and freeze','Independent installation and release acceptance','Deployment deferred']}
    text='# Fresh v3 development results\n\n6 November 2026. Two frozen builds each completed 360 fresh one-turn synthetic cases in stub mode: 720 sessions, zero tutor-provider calls. Baseline '+protocol['baseline_commit'][:7]+'; merged R3 candidate '+protocol['candidate_commit'][:7]+'. No diagnosis changes were authored from these cases.\n\n'
    text+='| Build | Hits / proposed incorrect claims | False labels / proposed no-error messages | Checked citations | Guard rejections / unexpected mastery |\n| --- | --- | --- | --- | --- |\n'
    for name,v in variants.items():
        m=v['all_proposed_labels'];text+=f"| {name} | {m['target_hits']}/{m['incorrect_claim_targets']} | {m['false_labels']}/{m['no_error_targets']} | {v['citation_snapshots']} ({v['citation_errors']} errors) | {v['guard_rejections']} / {v['unexpected_mastery_rows']} |\n"
    text+='\nLoading 30/30 catalogue types has not produced broad diagnosis accuracy. The merged build adds three target hits and three false labels on proposed labels. This does not establish product quality or learning. R3 owns diagnosis changes. Citation identity/hash/chapter checks do not establish semantic faithfulness.\n\n'
    text+=f"GPT-6-Luna authored the cases; Gemini reviewed shuffled opaque IDs and messages with the public chapter catalogue, without target labels, generator rationales or tutor outputs. There are {len(agreed)} label agreements, {len(disagreed)} disagreements and {len(uncertain)} uncertain/unusable rows ({ri['validation_errors']} invalid quote, {ri['ambiguous']} ambiguous). The first review job stopped at the invalid quote; the continuation sent only untouched groups. No received request was repeated.\n\n"
    text+='| Build | Hits / AI-agreed incorrect claims | False labels / AI-agreed no-error messages |\n| --- | --- | --- |\n'
    for name,v in variants.items():
        m=v['ai_agreement_subset'];text+=f"| {name} | {m['target_hits']}/{m['incorrect_claim_targets']} | {m['false_labels']}/{m['no_error_targets']} |\n"
    text+='\nTwo-model agreement is a development screen, not ground truth. This subset excludes disputed cases and may be easier; full proposed-label results remain visible. Human reviews remain zero. No learning, C2 advantage, independent-final or teaching-approval claim is supported.\n\n'
    text+=f"Product-phase provider-reported spend: USD {phase['actual_spend_usd']:.7f}; accounted spend: USD {phase['accounted_phase_usd']:.7f}, including the conservative reservation for an earlier failed request with unknown actual billing. Total historical/current provider attempts: {snapshot['total_provider_attempts']}. The USD 10 ceiling remains enforced. All five original wallets are byte-identical; unused caps were released and no paid job remains scheduled.\n\n"
    text+='Reproduce without network calls: scripts/product_quality/report_v3_fresh_cases.py --check. Raw cases, responses, databases and wallets stay under ignored Directions; only aggregate reports and source are published. See [DATA_SUFFICIENCY.md](DATA_SUFFICIENCY.md) and [TOOLS_HANDOFF.md](TOOLS_HANDOFF.md).\n'
    audit="""# Fresh-data sufficiency and remaining gates\n\nThe 360 messages cover 30 public types in three chapters: 12/type, with four proposed incorrect claims and eight correct/question/correction/insufficient-evidence controls. The 120/120/120 partitions were fixed before testing; both builds were archived before inspection or tuning. No cases were used to change R3 diagnosis code.\n\nThis is enough to expose a broad current detection gap and false-label risks. It is **not enough for final release or learning claims**:\n\n- Only four proposed positive paraphrases/type; type-level rates are unstable. Label disagreement, ambiguity and invalid quoted evidence remain explicit.\n- One generated batch/type creates correlation. Scenario partitions differ deliberately; they are not random exchangeable held-out samples. Explicit Hinglish slots occur only in development, so cross-partition results cannot establish multilingual generalization.\n- A separate AI family reviewed blinded messages, but two-model agreement cannot replace teacher labels or independent raters.\n- Fresh-state, single-turn stub sessions do not test live conversational quality, long-term learning, realistic learner behavior or deployment. No new C1/C2 comparison was run; existing matched results and limits remain unchanged.\n- Citation checks establish identity, hashes and chapter matching only. Meaning, age-appropriate teaching and safety need human review. CI security smokes are not comprehensive; unsupported original E2 channels remain unsupported.\n\nNext: R3/R2 triage private failures and label disagreements against the public catalogue; actual teachers review case truth, false-positive controls and worked examples; independently author and lock final cases before candidate freeze; preregister metrics and sample size for the intended scope; run fresh matched C1/C2 and supported-channel safety checks after runtime/content acceptance. Do not spend the budget repeating weak studies or count disputed labels as successes.\n\nOriginal frozen studies, data, blank teacher packets and reports remain intact. R1 and R5 being one person does not create two independent raters. Formal M3/M4 acceptance remains open.\n"""
    return {'RESULTS.json':json.dumps(report,indent=2)+'\n','RESULTS.md':text,'DATA_SUFFICIENCY.md':audit}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for name,value in build().items():
        p=DEST/name
        if args.check:assert p.read_text(encoding='utf-8')==value,f'Report changed: {name}'
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value,encoding='utf-8')
    print(json.dumps({'status':'verified' if args.check else 'written'}))
if __name__=='__main__':main()
