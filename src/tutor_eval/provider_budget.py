"""Durable pre-request provider budget. Counts attempts, disables retries, never stores prompts/keys."""
from __future__ import annotations
import hashlib
import json
import math
import os
import time
import uuid
from pathlib import Path
from filelock import FileLock


class BudgetExceeded(RuntimeError):
    pass


class ProviderBudget:
    def __init__(self, path, *, max_calls, max_usd, prior_calls=0, input_price=.4, output_price=1.6,
                 batch_max_calls=None, batch_start_attempts=0, approval_receipt=None):
        approval_hash = None
        approved_total = 1000
        if approval_receipt is not None:
            receipt_path = Path(approval_receipt)
            receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
            if (receipt.get('status') != 'approved' or not receipt.get('approval_quote')
                    or not receipt.get('approved_by') or receipt.get('prior_provider_attempts') != prior_calls
                    or type(receipt.get('additional_requests')) is not int
                    or receipt['additional_requests'] < max_calls or receipt.get('max_additional_usd', 0) < max_usd):
                raise ValueError('Explicit budget-extension approval is missing or does not cover this batch')
            previous_path = Path(os.path.expandvars(receipt['previous_ledger_path']))
            previous_bytes = previous_path.read_bytes()
            previous = json.loads(previous_bytes)
            if (hashlib.sha256(previous_bytes).hexdigest() != receipt['previous_ledger_sha256']
                    or previous['policy']['prior_calls'] + len(previous['attempts']) != prior_calls
                    or any(a['status'] == 'reserved' for a in previous['attempts'])):
                raise ValueError('Prior provider ledger does not match the approved continuation boundary')
            approved_total = prior_calls + receipt['additional_requests']
            approval_hash = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
        if (type(max_calls) is not int or max_calls < 1 or type(prior_calls) is not int or prior_calls < 0
                or prior_calls + max_calls > approved_total or not 0 < max_usd <= 1):
            raise ValueError('A positive call cap and USD cap at most 1 are required per study batch')
        self.batch_max_calls, self.batch_start_attempts = batch_max_calls, batch_start_attempts
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = FileLock(str(self.path) + '.lock', timeout=15)
        self.policy = dict(max_calls=max_calls, max_usd=max_usd, prior_calls=prior_calls,
                           input_price=input_price, output_price=output_price)
        if approval_hash:
            self.policy.update(approval_receipt_sha256=approval_hash, approved_total_limit=approved_total)
        with self.lock:
            if self.path.exists():
                if self._read()['policy'] != self.policy:
                    raise ValueError('An existing budget policy cannot be silently changed')
            else:
                self._save({'policy': self.policy, 'attempts': [], 'refused': 0})

    def _read(self):
        return json.loads(self.path.read_text(encoding='utf-8'))

    def _save(self, data):
        temp = self.path.with_name(self.path.name + '.tmp-' + uuid.uuid4().hex)
        temp.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        os.replace(temp, self.path)

    def reserve(self, messages, max_tokens):
        # A UTF-8 byte bound plus message framing is deliberately conservative.
        raw = json.dumps(messages, ensure_ascii=False, default=str).encode('utf-8')
        reserve = ((len(raw) + 2048) * self.policy['input_price'] + max_tokens * self.policy['output_price']) / 1e6
        with self.lock:
            data = self._read()
            if (len(data['attempts']) >= self.policy['max_calls'] or
                    (self.batch_max_calls is not None and len(data['attempts']) - self.batch_start_attempts >= self.batch_max_calls) or
                    sum(a['accounted_usd'] for a in data['attempts']) + reserve > self.policy['max_usd']):
                data['refused'] += 1
                self._save(data)
                raise BudgetExceeded('Provider budget exhausted before sending')
            call_id = uuid.uuid4().hex
            data['attempts'].append({'id': call_id, 'started': time.time(), 'status': 'reserved',
                                     'request_sha256': hashlib.sha256(raw).hexdigest(), 'input_bytes': len(raw),
                                     'max_tokens': max_tokens, 'accounted_usd': reserve,
                                     'reserved_usd': reserve, 'billed_usd': None})
            self._save(data)
        return call_id

    def finish(self, call_id, reply=None, error=None):
        usage = getattr(reply, 'usage_metadata', None) or {}
        billed = (getattr(reply, 'response_metadata', None) or {}).get('token_usage') or {}
        cost = billed.get('cost')
        valid_cost = isinstance(cost, (int, float)) and not isinstance(cost, bool) and math.isfinite(cost) and cost >= 0
        with self.lock:
            data = self._read()
            row = next(a for a in data['attempts'] if a['id'] == call_id)
            row.update(status='error' if error else 'completed', finished=time.time(),
                       tokens_in=usage.get('input_tokens'), tokens_out=usage.get('output_tokens'))
            if valid_cost:
                row.update(billed_usd=cost, accounted_usd=cost, cost_basis='provider_reported')
            elif all(isinstance(usage.get(k), int) and usage[k] >= 0 for k in ('input_tokens', 'output_tokens')):
                row.update(accounted_usd=(usage['input_tokens'] * self.policy['input_price'] +
                                         usage['output_tokens'] * self.policy['output_price']) / 1e6,
                           cost_basis='token_price_estimate')
            else:
                row['cost_basis'] = 'conservative_reservation_usage_unknown'
            if error:
                row['error_type'] = type(error).__name__
            self._save(data)

    def snapshot(self):
        with self.lock:
            data = self._read()
        return {**self.policy, 'provider_attempts': len(data['attempts']), 'refused': data['refused'],
                'prior_plus_attempts': self.policy['prior_calls'] + len(data['attempts']),
                'accounted_usd': sum(a['accounted_usd'] for a in data['attempts']),
                'provider_reported_usd': sum(a['billed_usd'] for a in data['attempts'] if a['billed_usd'] is not None),
                'provider_cost_coverage': sum(a['billed_usd'] is not None for a in data['attempts']),
                'path': str(self.path)}


class CappedClient:
    def __init__(self, inner, budget, cap=240):
        self.inner, self.budget, self.cap = inner, budget, cap

    def invoke(self, messages, **kwargs):
        kwargs['max_tokens'] = min(kwargs.get('max_tokens') or self.cap, self.cap)
        call_id = self.budget.reserve(messages, kwargs['max_tokens'])
        try:
            reply = self.inner.invoke(messages, **kwargs)
        except Exception as exc:
            self.budget.finish(call_id, error=exc)
            raise
        self.budget.finish(call_id, reply=reply)
        return reply


def attach_budget(llm, budget):
    if not llm.enabled:
        raise ValueError('Live experiment requested but no provider is configured')
    if llm.model != 'openai/gpt-4.1-mini':
        raise ValueError('Fairness experiments require the fixed gpt-4.1-mini model')
    inner = llm._chat()
    root = getattr(inner, 'root_client', None)
    if root is None or getattr(getattr(inner, 'client', None), '_client', None) is not root:
        raise ValueError('Cannot verify provider retry settings; no request sent')
    inner.max_retries = root.max_retries = 0
    inner.request_timeout = root.timeout = 22
    inner.max_tokens = 240
    if inner.max_retries != 0 or root.max_retries != 0:
        raise ValueError('Provider retry policy is not single-attempt')
    wrapped = CappedClient(inner, budget)
    llm._chat = lambda *args, **kwargs: wrapped
    return wrapped
