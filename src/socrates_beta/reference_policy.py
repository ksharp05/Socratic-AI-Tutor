"""Explicit machine/reference beta qualification; never a teacher approval."""
import hashlib
import json
from tutor_validation import exact_reference as reference
from .maths import AssessmentService


class ReferenceCheckedAssessmentService(AssessmentService):
    POLICY = "reference_checked_beta"

    def __init__(self, repo, maths):
        super().__init__(repo, maths)
        self.qualified = {}
        from tutor.question_catalog import allowed,graph_items,PUBLIC_FIELDS
        registered={item['question_id']:item for item in graph_items()}
        for qid,item in maths.items.items():
            if qid not in registered or any(item.get(k)!=registered[qid].get(k) for k in PUBLIC_FIELDS):
                continue
            if not (allowed(item,"practice") or allowed(item,"quiz") or allowed(item,"diagnostic")):
                continue
            key = maths.key(qid)
            if reference.validate(item["problem"],key)["status"] == "verified":
                self.qualified[qid] = self._hash(item)
        if not self.qualified:
            raise ValueError("No independently checked beta questions")
        self.manifest_sha256 = hashlib.sha256(json.dumps(self.qualified,sort_keys=True).encode()).hexdigest()

    @staticmethod
    def _hash(item):
        return hashlib.sha256(json.dumps(item,sort_keys=True,separators=(",",":")).encode()).hexdigest()

    def _eligible(self, scope, concept, mode):
        return [item for item in super()._eligible(scope,concept,mode)
                if item["question_id"] in self.qualified
                and self._hash(item) == self.qualified[item["question_id"]]]

    def _bind_publication(self, record, eligible):
        record["state"]["reference_checked_versions"] = {
            item["question_id"]:self.qualified[item["question_id"]] for item in eligible}

    def _guard_assessment(self, record, conn):
        result = super()._guard_assessment(record,conn)
        if result:
            return result
        versions = record["state"].get("reference_checked_versions") or {}
        selected = set(record["state"]["queue"][:record["state"]["limit"]]) | set(record["state"]["used"])
        if any(qid not in self.qualified or versions.get(qid) != self.qualified[qid]
               or self._hash(self.maths.items[qid]) != self.qualified[qid] for qid in selected):
            record["state"].update(complete=True,policy_revoked=True)
            self.repo.save_assessment(record,conn=conn)
            return self._guard_mode(record,conn)
        return None

    def public(self, record, *, conn=None):
        result = self._guard_assessment(record,conn)
        return result or super().public(record,conn=conn)
