"""A pre-provisioned deployment lease; no network, prompts or keys in its ledger."""
from __future__ import annotations
import hashlib
import json
import math
import re
from pathlib import Path
from filelock import FileLock
from tutor_eval.provider_budget import ProviderBudget, BudgetExceeded, CappedClient

DESTINATION = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-4.1-mini"


def grant_policy(grant):
    if not isinstance(grant,dict):
        raise ValueError("A deployment allocation grant is required")
    amount, previous, calls = grant.get("reserved_usd"), grant.get("previous_accounted_usd"), grant.get("max_calls")
    if (grant.get("status")!="approved" or grant.get("phase_ceiling_usd")!=10
            or grant.get("destination")!=DESTINATION or grant.get("model")!=MODEL
            or not grant.get("approval_quote")
            or not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,79}",grant.get("allocation_id",""))
            or type(calls) is not int or not 1<=calls<=200
            or type(amount) not in (int,float) or not math.isfinite(amount) or not 0<amount<=1
            or type(previous) not in (int,float) or not math.isfinite(previous)
            or previous<0 or previous+amount>10):
        raise ValueError("Invalid or uncovered deployment allocation")
    return {"max_calls":calls,"max_usd":amount,"prior_calls":0,"input_price":3,"output_price":12}


def fingerprint(grant):
    return hashlib.sha256(json.dumps(grant,sort_keys=True,separators=(",",":")).encode()).hexdigest()


class DeploymentBudget(ProviderBudget):
    def __init__(self, data, grant):
        policy=grant_policy(grant)
        folder=Path(data)/"provider-allocations"/grant["allocation_id"]
        # Serving never initializes missing state. A lost disk cannot renew an allowance.
        if not (folder/"grant.sha256").is_file() or not (folder/"provider_budget.json").is_file():
            raise ValueError("Deployment budget is not provisioned; live mode remains disabled")
        if (folder/"grant.sha256").read_text().strip()!=fingerprint(grant):
            raise ValueError("Deployment allocation changed; refusing a silent reset")
        self.pause_file=Path(data)/"PAUSE_PROVIDER"
        super().__init__(folder/"provider_budget.json",**policy)

    @classmethod
    def provision(cls,data,grant):
        policy=grant_policy(grant)
        parent=Path(data)/"provider-allocations";parent.mkdir(parents=True,exist_ok=True)
        with FileLock(str(parent/".provision.lock"),timeout=15):
            folder=parent/grant["allocation_id"]
            folder.mkdir(exist_ok=False)
            (folder/"grant.sha256").write_text(fingerprint(grant)+"\n",encoding="utf-8")
            ProviderBudget(folder/"provider_budget.json",**policy)
        return cls(data,grant)

    def reserve(self,messages,max_tokens):
        if type(max_tokens) is not int or not 1<=max_tokens<=300:
            raise ValueError("Deployment output cap is at most 300 tokens")
        raw=json.dumps(messages,ensure_ascii=False,default=str).encode()
        request_hash=hashlib.sha256(raw).hexdigest()
        with self.lock:
            if self.pause_file.exists():
                raise BudgetExceeded("Live provider is paused")
            if any(row["request_sha256"]==request_hash for row in self._read()["attempts"]):
                raise BudgetExceeded("Request already attempted; no automatic paid replay")
            return super().reserve(messages,max_tokens)


class HostedLanguage:
    def __init__(self,app_root,budget):
        from .language import TeamLanguage
        from tutor.llm import base_url
        self.delegate=TeamLanguage(app_root,budget.policy["max_calls"])
        if self.delegate.model!=MODEL or base_url().rstrip("/")!=DESTINATION:
            raise ValueError("Deployment provider/model differs from its allocation")
        inner=self.delegate.chat
        root=getattr(inner,"root_client",None)
        if root is None or getattr(getattr(inner,"client",None),"_client",None) is not root:
            raise ValueError("Cannot verify deployment retry settings")
        inner.max_retries=root.max_retries=0
        inner.request_timeout=root.timeout=22
        inner.max_tokens=240
        if inner.max_retries or root.max_retries:
            raise ValueError("Deployment provider retries are not disabled")
        self.delegate.chat=CappedClient(inner,budget,cap=240)
        self.delegate.limit=budget.policy["max_calls"]
        self.budget=budget

    def generate(self,system,context):
        return self.delegate.generate(system,context)

    def health(self):
        state=self.budget.snapshot()
        return {"mode":"live","model":MODEL,"calls":state["provider_attempts"],
                "remaining":max(0,state["max_calls"]-state["provider_attempts"]),
                "paused":self.budget.pause_file.exists()}
