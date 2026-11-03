from __future__ import annotations
import json,threading,time,hashlib,os
from pathlib import Path
from .maths import load_team_modules


class TeamLanguage:
    def __init__(self,app_root,max_calls=60,audit_directory=None):
        load_team_modules(app_root)
        from tutor.llm import LLM
        llm=LLM(None)
        if not llm.enabled:raise ValueError('No configured language provider. Configure the team app locally or start offline.')
        self.chat=llm._chat();self.chat.request_timeout=22;self.chat.max_retries=0;self.chat.max_tokens=240
        self.audit_directory=Path(audit_directory).resolve() if audit_directory else None
        if self.audit_directory:
            allowed=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path(__file__).resolve().parents[2])).resolve()/'Directions/beta_data/evaluation_runs'
            if not self.audit_directory.is_relative_to(allowed):raise ValueError('Development response audit must stay inside ignored evaluation runs')
            self.audit_directory.mkdir(parents=True,exist_ok=True)
        self.model=llm.model;self.limit=max(1,min(int(max_calls),120));self.calls=0;self.lock=threading.Lock();self.receipts=[]
    def generate(self,system,context):
        with self.lock:
            if self.calls>=self.limit:raise RuntimeError('provider_budget_exhausted')
            self.calls+=1;number=self.calls
        start=time.monotonic();receipt={'call':number,'model':self.model,'outcome':'error','cost':None,'request_id':context.get('request_id')}
        try:
            response=self.chat.invoke([('system',system),('user',json.dumps(context,ensure_ascii=False))])
            if not isinstance(response.content,str):raise ValueError('Expected text')
            if self.audit_directory:
                record={'call':number,'model':self.model,'request_id':context.get('request_id'),'content':response.content}
                (self.audit_directory/f'response-{number:03}.json').write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')
                receipt['response_sha256']=hashlib.sha256(response.content.encode()).hexdigest()
            receipt.update(outcome='response',usage=getattr(response,'usage_metadata',None))
            return response.content
        finally:
            receipt['latency_ms']=round((time.monotonic()-start)*1000)
            with self.lock:self.receipts.append(receipt)
    def health(self):return {'mode':'live','model':self.model,'calls':self.calls,'remaining':max(0,self.limit-self.calls)}
