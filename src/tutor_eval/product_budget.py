"""Phase-wide capped product experiments; original fairness wallets stay unchanged."""
from __future__ import annotations
import hashlib,json,os,re,uuid
from pathlib import Path
from filelock import FileLock
from .provider_budget import ProviderBudget,CappedClient,BudgetExceeded


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
    path=Path(path);temp=path.with_name(path.name+'.tmp-'+uuid.uuid4().hex)
    temp.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(temp,path)

class ProductPhase:
    def __init__(self,source,iteration='v3'):
        if iteration not in ('v3','v4'):raise ValueError('Unknown product iteration')
        self.source=Path(source).resolve();self.root=self.source/'Directions/product_quality'/iteration
        self.phase_path=self.source/'Directions/product_quality/v1/PHASE_AUTHORIZATION.json'
        self.authorization=self.root/'ITERATION_AUTHORIZATION.json'
        auth=read(self.authorization)
        if auth.get('status')!='approved' or auth.get('destination')!='https://openrouter.ai/api/v1' or auth.get('phase_ceiling_usd')!=10:
            raise ValueError('Explicit product phase/destination authorization missing')
        # Opt-in only: one local batch may run while a hosted lease stays open. The hosted cap
        # still counts toward the ceiling and is never released or spent locally.
        self.beside_hosted=auth.get('allow_local_batch_beside_hosted_lease') is True
        self.lock=FileLock(str(self.phase_path)+'.allocation.lock',timeout=15)

    def _check(self,phase):
        if phase.get('status')!='approved' or phase.get('max_phase_usd')!=10:raise ValueError('Phase is not approved')
        if sum(b['max_usd'] for b in phase['batch_allocations'])>10+1e-10:raise BudgetExceeded('Phase allocations exceed USD 10')
        for entry in phase['batch_allocations']:
            if entry['status'].startswith('completed') and 'ledger_sha256' in entry:
                if sha(self.source/entry['wallet'])!=entry['ledger_sha256']:raise ValueError('Closed wallet was changed')

    def allocate(self,slug,purpose,*,max_usd=.9,max_calls=500):
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,70}',slug):raise ValueError('Invalid batch identifier')
        if not 0<max_usd<=1 or type(max_calls) is not int or max_calls<1:raise ValueError('Invalid bounded allocation')
        with self.lock:
            phase=read(self.phase_path);self._check(phase)
            hosted=lambda b:self.beside_hosted and bool(b.get('remote_allocation'))
            if any(not b['status'].startswith('completed') and not hosted(b) for b in phase['batch_allocations']):raise ValueError('Close the previous batch before another allocation')
            if sum(b['max_usd'] for b in phase['batch_allocations'])+max_usd>10+1e-10:raise BudgetExceeded('New allocation exceeds the phase ceiling')
            folder=self.root/'batches'/slug
            if folder.exists():raise ValueError('Existing batch; never reset or silently repeat it')
            auth=read(self.authorization)
            # Chain from the last local wallet: a hosted mirror keeps changing while its lease is open.
            chain=[b for b in phase['batch_allocations'] if not hosted(b)]
            previous=self.source/(chain[-1]['wallet'] if chain else auth['previous_provider_ledger'])
            previous_data=read(previous)
            if any(a['status']=='reserved' for a in previous_data['attempts']):raise ValueError('Prior request is still in flight')
            prior=previous_data['policy']['prior_calls']+len(previous_data['attempts'])
            folder.mkdir(parents=True)
            receipt={'status':'approved','approved_by':auth['approved_by'],'approval_quote':auth['approval_quote'],'prior_provider_attempts':prior,'additional_requests':max_calls,'max_additional_usd':max_usd,'previous_ledger_path':str(previous),'previous_ledger_sha256':sha(previous),'phase_authorization_sha256':sha(self.authorization),'destination':auth['destination'],'payload_scope':auth['payload_scope'],'purpose':purpose,'request_limit_basis':'internal bounded count under user-authorized USD 10 phase'}
            save(folder/'APPROVAL.json',receipt)
            wallet=ProviderBudget(folder/'provider_budget.json',max_calls=max_calls,max_usd=max_usd,prior_calls=prior,input_price=3,output_price=12,approval_receipt=folder/'APPROVAL.json')
            phase['batch_allocations'].append({'batch':slug,'purpose':purpose,'approval':str((folder/'APPROVAL.json').relative_to(self.source)).replace('\\','/'),'max_calls':max_calls,'max_usd':max_usd,'original_allocated_cap_usd':max_usd,'wallet':str(wallet.path.relative_to(self.source)).replace('\\','/'),'status':'running'})
            phase['unallocated_cap_usd']=10-sum(b['max_usd'] for b in phase['batch_allocations']);save(self.phase_path,phase)
            return PhaseWallet(self,slug,wallet)

    def open(self,slug):
        with self.lock:
            phase=read(self.phase_path);self._check(phase)
            entry=next(b for b in phase['batch_allocations'] if b['batch']==slug)
            if entry['status']!='running':raise ValueError('Closed batch cannot be reopened')
            path=self.source/entry['wallet'];policy=read(path)['policy']
            wallet=ProviderBudget(path,max_calls=policy['max_calls'],max_usd=policy['max_usd'],prior_calls=policy['prior_calls'],input_price=3,output_price=12,approval_receipt=self.source/entry['approval'])
            return PhaseWallet(self,slug,wallet)

    def close(self,budget,*,status='completed'):
        with self.lock:
            phase=read(self.phase_path);self._check(phase)
            entry=next(b for b in phase['batch_allocations'] if b['batch']==budget.slug)
            if entry['status']!='running':raise ValueError('Batch already closed')
            if entry.get('remote_allocation'):
                raise ValueError('Hosted allocation must be paused and reconciled with dedicated remote-close tooling; generic cap release is forbidden')
            data=read(budget.path)
            if any(a['status']=='reserved' for a in data['attempts']):raise ValueError('In-flight requests prevent closing')
            snap=budget.snapshot();accounted=snap['accounted_usd']
            if accounted>entry['max_usd']+1e-10:raise BudgetExceeded('Unexpected provider cost: stop phase')
            entry.update(status=status,max_usd=accounted,requests_used=snap['provider_attempts'],accounted_usd=accounted,provider_reported_usd=snap['provider_reported_usd'],ledger_sha256=sha(budget.path),cap_released_on_completion=True,requests_remaining_authorized=0,no_additional_batch_requests_scheduled=True)
            phase['actual_spend_usd']=sum(b.get('provider_reported_usd',0) for b in phase['batch_allocations'])
            phase['accounted_phase_usd']=sum(b.get('accounted_usd',b.get('provider_reported_usd',0)) for b in phase['batch_allocations'])
            phase['unallocated_cap_usd']=10-sum(b['max_usd'] for b in phase['batch_allocations']);self._check(phase);save(self.phase_path,phase)
            save(budget.path.parent/'CLOSED.json',{'status':status,'snapshot':snap,'phase_accounted_usd':phase['accounted_phase_usd'],'ledger_sha256':entry['ledger_sha256']})
            return snap

class PhaseWallet:
    def __init__(self,phase,slug,wallet):self.phase,self.slug,self.wallet,self.path=phase,slug,wallet,wallet.path
    def reserve(self,messages,max_tokens):
        with self.phase.lock:
            phase=read(self.phase.phase_path);self.phase._check(phase)
            entry=next(b for b in phase['batch_allocations'] if b['batch']==self.slug)
            if entry.get('remote_allocation'):raise BudgetExceeded('Hosted allocation cannot also spend through a local wallet')
            if entry['status']!='running' or entry['max_usd']!=self.wallet.policy['max_usd']:raise BudgetExceeded('Batch is not open')
            return self.wallet.reserve(messages,max_tokens)
    def finish(self,*args,**kwargs):return self.wallet.finish(*args,**kwargs)
    def snapshot(self):return self.wallet.snapshot()


def attach_product_budget(llm,budget,*,cap=300,timeout=30):
    auth=read(budget.phase.authorization)
    if not llm.enabled or llm.model not in auth['models']:raise ValueError('Unapproved product model or disabled provider')
    if not 1<=cap<=3000:raise ValueError('Output cap outside approved development envelope')
    from tutor.config import SETTINGS
    if llm.model not in SETTINGS.llm['course_models']:raise ValueError('Product model is outside the course allowlist')
    from tutor.llm import base_url
    if base_url().rstrip('/')!=auth['destination']:raise ValueError('Provider destination mismatch')
    inner=llm._chat();root=getattr(inner,'root_client',None)
    if root is None or getattr(getattr(inner,'client',None),'_client',None) is not root:raise ValueError('Cannot verify provider retries')
    inner.max_retries=root.max_retries=0;inner.request_timeout=root.timeout=timeout;inner.max_tokens=cap
    wrapped=CappedClient(inner,budget,cap=cap);llm._chat=lambda *args,**kwargs:wrapped
    return wrapped
