"""Run the fixed v2 public panel against one frozen version; no automatic repeats."""
from __future__ import annotations
import argparse,hashlib,json,os,re,sys
from fractions import Fraction
from pathlib import Path

CODE=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path.cwd())).resolve()
ROOT=SOURCE/'Directions/product_quality/v2'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--version',choices=['before','after'],required=True)
parser.add_argument('--live',action='store_true')
args=parser.parse_args()
APP=ROOT/'before_source' if args.version=='before' else CODE
os.environ.update(SOCRATES_SOURCE_WORKSPACE=str(SOURCE),TUTOR_LLM='auto' if args.live else 'stub',
                  TUTOR_BETA_CONFIG='',TUTOR_BETA_LIVE='0',TUTOR_REQUIRE_BETA='0',LLM_MODEL='openai/gpt-4.1-mini')
sys.path.insert(0,str(APP/'src'))
from tutor import store
from tutor.question_catalog import graph_items,allowed
from tutor.seed import seed_learner
from tutor.topic_sources import cards as topic_cards
from tutor_eval.provider_budget import ProviderBudget,attach_budget
from v02_integration.runtime import ContextualPreviewTutor


def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8');os.replace(tmp,p)

def source_profile():
    paths=[]
    for name in ['src/tutor','src/tutor_eval','src/tutor_api','src/v02_integration','src/socratic_data','content/poc','content/dataset-v0.10.0','content/milestone2_dev','content/product_quality']:
        folder=APP/name
        if folder.exists():paths.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.jsonl'))
    paths.extend([APP/'config/app.toml',APP/'ui/app.py'])
    return {str(p.relative_to(APP)).replace('\\','/'):sha(p) for p in sorted(paths)}

ALIASES={'factor':['factor','multiplier','number in front','number multiplying'],
         'nonzero':['nonzero','non-zero','not zero','not be zero'],
         'squared':['squared','degree two','degree 2','second degree','x^2'],
         'fixed':['fixed','constant','same'], 'sum':['sum','total']}

def evaluate(case,turns):
    failures=[]
    for expected in case['checks']:
        t=turns[expected['turn']];reply=t['reply'].casefold();diag=t['diagnosis'];i=expected['turn']
        if expected.get('no_diagnosis') and diag is not None:failures.append(f'{i}:unexpected_diagnosis')
        if expected.get('diagnosis') and (diag or {}).get('misconception_id')!=expected['diagnosis']:failures.append(f'{i}:diagnosis_target')
        if expected.get('route') and t['route']!=expected['route']:failures.append(f'{i}:information_route')
        if expected.get('contains') and expected['contains'].casefold() not in reply:failures.append(f'{i}:required_boundary_message')
        if expected.get('citation') and not t['citations']:failures.append(f'{i}:missing_reference')
        if expected.get('no_model') and t['model_calls']:failures.append(f'{i}:unexpected_model_call')
        if expected.get('one_question') and reply.count('?')!=1:failures.append(f'{i}:question_count')
        if expected.get('first_sentence_terms'):
            first=re.split(r'[.!?]',reply)[0]
            missing=[word for word in expected['first_sentence_terms'] if not any(alias in first for alias in ALIASES.get(word,[word]))]
            if missing:failures.append(f'{i}:direct_explanation_terms:'+','.join(missing))
        if expected.get('does_not_advance_hint') and t['hint_before']!=t['hint_after']:failures.append(f'{i}:hint_advanced_without_request')
        if expected.get('different_from_previous') and i and turns[i-1]['reply']==t['reply']:failures.append(f'{i}:unchanged_support')
        if 'quiz_index' in expected and t['quiz_index']!=expected['quiz_index']:failures.append(f'{i}:quiz_was_scored')
    return failures


def setup(app,case):
    if case.get('setup')=='quiz':
        proposal=app.propose_set('qe04',mode='quiz');app.decide(proposal['set_id'],'approve','synthetic-panel-fixture-only')
    elif case.get('setup') in ('ap_practice','trig_practice'):
        task='ap_term' if case['setup']=='ap_practice' else 'trig_triangle_ratio'
        item=next(i for i in graph_items() if allowed(i,'practice') and i['problem']['task_type']==task)
        proposal=app.propose_set(item['problem']['concept_ids'][0]);app.decide(proposal['set_id'],'edit','synthetic-panel-fixture-only',question_ids=[item['question_id']]);app.decide(proposal['set_id'],'approve','synthetic-panel-fixture-only')


def run_case(case,folder,budget):
    folder.mkdir();app=ContextualPreviewTutor(llm_mode='auto' if args.live else 'stub',defences=True,
        db_name=str(folder/'tutor.db'),checkpoint_name=str(folder/'check.db'))
    sid='panel-'+case['id'];lid='panel-learner'
    seed_learner(app.conn,lid,{'alias':'AI-authored public development case'})
    try:
        if budget:attach_budget(app.llm,budget)
        setup(app,case);turns=[];refs_by_id={c['passage_id']:c for c in topic_cards()};cites=0
        for i,message in enumerate(case['messages']):
            previous=app.graph.get_state({'configurable':{'thread_id':sid}}).values or {}
            hint_before=(previous.get('active_item') or {}).get('hint_stage')
            sequence=app.conn.execute('SELECT coalesce(max(id),0) FROM trace_events WHERE session_id=?',(sid,)).fetchone()[0]
            out=app.turn(sid,lid,message,chapter=case['chapter'])
            current=app.graph.get_state({'configurable':{'thread_id':sid}}).values
            trace=[dict(r) for r in app.conn.execute('SELECT * FROM trace_events WHERE session_id=? AND id>? ORDER BY id',(sid,sequence))]
            calls=[r for r in trace if r['kind']=='llm']
            if any(r['outcome']=='error' for r in calls):raise RuntimeError('Provider error: preserve this attempt without retry')
            citations=app.history(sid)[-1].get('citations',[])
            for ref in citations:
                body={k:v for k,v in ref.items() if k!='reference_sha256'}
                assert ref['reference_sha256']==hashlib.sha256(store.dumps(body).encode()).hexdigest()
                assert ref['chapter']==case['chapter'] and refs_by_id[ref['passage_id']]['text']==ref['text']
                cites+=1
            row={'index':i,'student':message,'reply':out['reply'],'route':out['route'],'diagnosis':out.get('diagnosis'),
                'citations':citations,'checks':out.get('checks'),'model_calls':len(calls),'trace_observed':bool(trace),
                'hint_before':hint_before,'hint_after':(current.get('active_item') or {}).get('hint_stage'),
                'quiz_index':(current.get('quiz') or {}).get('index')}
            turns.append(row)
            with (folder/'turns.jsonl').open('a',encoding='utf-8') as output:output.write(json.dumps(row)+'\n')
        failures=evaluate(case,turns)
        for i,t in enumerate(turns):
            if not (t['checks'].get('ok') is True or t['checks'].get('skipped') is True):failures.append(f'{i}:guard_rejected')
        if not case.get('setup') and app.conn.execute('SELECT count(*) FROM mastery').fetchone()[0]:failures.append('mastery_changed_without_checked_work')
        trace=[dict(r) for r in app.conn.execute('SELECT * FROM trace_events WHERE session_id=? ORDER BY id',(sid,))];save(folder/'trace.json',trace)
        result={'id':case['id'],'category':case['category'],'functional_checks_pass':not failures,'failures':failures,
            'turns':len(turns),'model_calls':sum(t['model_calls'] for t in turns),'citation_snapshots':cites,
            'turns_sha256':sha(folder/'turns.jsonl'),'trace_sha256':sha(folder/'trace.json'),'human_review':'pending'}
        save(folder/'RESULT.json',result);return result
    finally:app.close()


def main():
    mode='live' if args.live else 'offline';target=ROOT/mode/args.version
    if target.exists():raise RuntimeError('Existing panel evidence; no automatic repeat')
    protocol=CODE/'eval/fixtures/product_quality_v2_panel.json';assert sha(protocol)==load(ROOT/'PANEL_LOCK.json')['sha256']
    cases=load(protocol)['cases'];profile=source_profile();budget=None
    if args.live:
        saved=load(ROOT/'offline'/args.version/'INDEX.json');assert saved['status']=='completed' and saved['source_sha256']==profile
        phase=load(SOURCE/'Directions/product_quality/v1/PHASE_AUTHORIZATION.json')
        assert phase['status']=='approved' and sum(b['max_usd'] for b in phase['batch_allocations'])<=phase['max_phase_usd']==10
        assert any(b['batch']=='product-v2-matched-panel' and b['max_usd']==0.4 and b['max_calls']==200 for b in phase['batch_allocations'])
        from tutor.llm import api_key,base_url
        assert api_key()[0] and base_url().rstrip('/')=='https://openrouter.ai/api/v1'
        budget=ProviderBudget(ROOT/'provider_budget.json',max_calls=200,max_usd=.4,prior_calls=1061,approval_receipt=ROOT/'BATCH_APPROVAL.json')
    target.mkdir(parents=True)
    result={'status':'running','version':args.version,'mode':mode,'cases':[],'source_sha256':profile,
        'protocol_sha256':sha(protocol),'runner_sha256':sha(Path(__file__)),'actual_human_reviews':0,
        'scope':'Mechanical public-development targets only, not semantic teaching approval or independent final evidence.',
        'budget_start':budget.snapshot() if budget else None}
    save(target/'INDEX.json',result)
    try:
        for case in cases:
            row=run_case(case,target/case['id'],budget);result['cases'].append(row);save(target/'INDEX.json',result)
            print(json.dumps({'version':args.version,**row}),flush=True)
        result['status']='completed';result['budget_end']=budget.snapshot() if budget else None
        if budget:
            assert result['budget_end']['provider_attempts']-result['budget_start']['provider_attempts']==sum(r['model_calls'] for r in result['cases'])
            assert result['budget_end']['refused']==0
        save(target/'INDEX.json',result)
        print(json.dumps({'version':args.version,'mode':mode,'passed':sum(r['functional_checks_pass'] for r in result['cases']),
            'scheduled':len(cases),'model_calls':sum(r['model_calls'] for r in result['cases']),'budget':result['budget_end']},indent=2))
    except BaseException as error:
        result['status']='failed';result['error_type']=type(error).__name__;result['budget_end']=budget.snapshot() if budget else None;save(target/'INDEX.json',result);raise

if __name__=='__main__':main()
