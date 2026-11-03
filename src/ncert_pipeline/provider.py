from __future__ import annotations
import json, sys, time, threading
from pathlib import Path


class MainAppProvider:
    """Opt-in reuse of the team app's configured provider. No credentials in logs."""
    def __init__(self, app_root: Path, max_calls=6):
        app_root = app_root.resolve(strict=True)
        if not (app_root/'src/tutor/llm.py').is_file():
            raise ValueError('Expected the team app provider at app-root/src/tutor/llm.py')
        if any(k == 'tutor' or k.startswith('tutor.') for k in sys.modules):
            raise RuntimeError('Load the preview in a fresh process to avoid importing the older tutor package')
        sys.path.insert(0,str(app_root/'src'))
        from tutor.llm import LLM
        llm = LLM(None)
        if not llm.enabled:
            raise RuntimeError('No configured provider; use offline mode or configure the team app locally')
        self.chat = llm._chat()
        self.chat.request_timeout = 20
        self.chat.max_retries = 0
        self.chat.max_tokens = 240
        self.model = llm.model
        self.max_calls = max(1,min(int(max_calls),20))
        self.calls = 0
        self.lock = threading.Lock()
        self.receipts = []

    def generate(self, system: str, context: dict):
        with self.lock:
            if self.calls >= self.max_calls:
                raise RuntimeError('live_call_budget_exhausted')
            self.calls += 1
        start = time.monotonic()
        receipt = {'call':self.calls,'model':self.model,'outcome':'error','cost':None}
        try:
            result = self.chat.invoke([('system',system),('user',json.dumps(context,ensure_ascii=False))])
            receipt.update(outcome='provider_response',usage=getattr(result,'usage_metadata',None))
            content = result.content
            if not isinstance(content,str): raise ValueError('Expected text provider response')
            return content
        finally:
            receipt['elapsed_ms'] = round((time.monotonic()-start)*1000)
            self.receipts.append(receipt)
