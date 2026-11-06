"""Postgres-backed provider lease shared by every Vercel instance."""
from __future__ import annotations
import json
import threading
from contextlib import contextmanager
from .deployment_budget import DeploymentBudget, grant_policy, fingerprint
from tutor_eval.provider_budget import BudgetExceeded

SCHEMA = """
CREATE TABLE IF NOT EXISTS provider_allocations(
 id TEXT PRIMARY KEY,grant_sha256 TEXT NOT NULL,ledger TEXT NOT NULL,paused BOOLEAN NOT NULL DEFAULT FALSE
)
"""

def policy_for(grant):
    base=grant_policy(grant)
    policy=grant.get("provider_policy")
    expected={**base,"prior_calls":grant.get("prior_provider_attempts")}
    if not isinstance(policy,dict) or any(policy.get(k)!=v for k,v in expected.items()):
        raise ValueError("Hosted policy differs from its funded global allocation")
    if (policy.get("approval_receipt_sha256")!=grant.get("funding_receipt_sha256")
            or not isinstance(grant.get("funding_receipt_sha256"),str)
            or len(grant["funding_receipt_sha256"])!=64
            or type(policy["prior_calls"]) is not int or policy["prior_calls"]<0
            or policy.get("approved_total_limit")!=policy["prior_calls"]+policy["max_calls"]):
        raise ValueError("Hosted funding receipt does not cover this policy")
    return policy

class BudgetLock:
    def __init__(self,budget):
        self.budget=budget
        self.local=threading.local()
    def __enter__(self):
        if getattr(self.local,"depth",0):
            self.local.depth+=1
            return self
        manager=self.budget.repo.raw_connection()
        connection=manager.__enter__()
        try:
            row=connection.execute("SELECT grant_sha256,ledger,paused FROM provider_allocations WHERE id=%s FOR UPDATE",
                                   (self.budget.allocation,)).fetchone()
            if not row or row["grant_sha256"]!=self.budget.grant_hash:
                raise ValueError("Missing or changed provider allocation; refusing a reset")
            data=json.loads(row["ledger"])
            if data.get("policy")!=self.budget.policy:
                raise ValueError("Stored provider policy changed")
            self.local.connection,self.local.manager=connection,manager
            self.local.data,self.local.paused=data,row["paused"]
            self.local.depth=1
            return self
        except BaseException as exc:
            manager.__exit__(type(exc),exc,exc.__traceback__)
            raise
    def __exit__(self,kind,exc,tb):
        self.local.depth-=1
        if self.local.depth:return False
        try:
            # Refusals are themselves durable accounting events.
            if kind is not None and issubclass(kind,BudgetExceeded):
                self.local.manager.__exit__(None,None,None)
            else:
                self.local.manager.__exit__(kind,exc,tb)
        finally:
            self.local.connection=self.local.manager=self.local.data=None
        return False

class PostgresBudget(DeploymentBudget):
    def __init__(self,repo,grant):
        self.repo=repo
        self.policy=policy_for(grant)
        self.allocation=grant["allocation_id"]
        self.grant_hash=fingerprint(grant)
        self.path="postgres-provider-allocation:"+self.allocation
        self.lock=BudgetLock(self)
        self.pause_file=self
        self.batch_max_calls=None
        self.batch_start_attempts=0
        # Serving verifies pre-existing state and never provisions a wallet.
        with self.lock:pass
    @classmethod
    def provision(cls,repo,grant):
        policy=policy_for(grant)
        with repo.raw_connection() as conn:
            conn.execute("SELECT pg_advisory_xact_lock(%s)",(735601871238313,))
            conn.execute(SCHEMA)
            if conn.execute("SELECT 1 FROM provider_allocations WHERE id=%s",(grant["allocation_id"],)).fetchone():
                raise ValueError("Existing provider allocation; never reset it")
            if conn.execute("SELECT 1 FROM provider_allocations WHERE paused=FALSE").fetchone():
                raise ValueError("Pause and reconcile the previous allocation first")
            conn.execute("INSERT INTO provider_allocations(id,grant_sha256,ledger) VALUES(%s,%s,%s)",
                         (grant["allocation_id"],fingerprint(grant),
                          json.dumps({"policy":policy,"attempts":[],"refused":0})))
        return cls(repo,grant)
    def _read(self):
        if not getattr(self.lock.local,"depth",0):raise RuntimeError("Budget access requires its row lock")
        return self.lock.local.data
    def _save(self,data):
        self.lock.local.connection.execute("UPDATE provider_allocations SET ledger=%s WHERE id=%s",
                                           (json.dumps(data),self.allocation))
        self.lock.local.data=data
    def exists(self):
        with self.lock:return self.lock.local.paused
    def set_paused(self,paused=True):
        if type(paused) is not bool:raise ValueError("Pause state must be boolean")
        with self.lock:
            self.lock.local.connection.execute("UPDATE provider_allocations SET paused=%s WHERE id=%s",(paused,self.allocation))
            self.lock.local.paused=paused
    def export(self):
        with self.lock:
            return json.loads(json.dumps(self._read()))
