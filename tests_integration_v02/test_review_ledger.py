"""Approval persistence tests use authored fixtures, never real human decisions."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import test_contracts
from v02_integration.audit import digest
from v02_integration.promotion import prepare_promotion,publish_projection
from v02_integration.approved_store import load_approved_projection
import hashlib


def fixture():
    case=test_contracts.HumanReviewGate('test_bound_fixture_passes_but_unratified_or_unassigned_real_default_fails')
    case.setUp()
    return case


class ReviewLedger(unittest.TestCase):
    def setUp(self):
        self.f=fixture()
        self.item={'source_record':self.f.source,'revision':self.f.revision,'decision':self.f.decision}
    def publish(self,path,**kwargs):
        return publish_projection([self.item],path,policy=self.f.policy,reviewers=self.f.reviewers,**kwargs)
    def test_full_review_evidence_is_retained_separately_and_bound_to_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination=Path(temporary)/'approved'
            self.publish(destination)
            ledger_path=destination.with_name('approved.review_evidence')/'review_ledger.json'
            ledger=json.loads(ledger_path.read_text());record=ledger['review_records'][0]
            manifest=json.loads((destination/'MANIFEST.json').read_text())
            self.assertEqual(record['parent_id'],self.f.source['id'])
            self.assertEqual(record['reviewer_ids'],self.f.decision['reviewer_ids'])
            self.assertEqual(record['reviewed_at'],self.f.decision['reviewed_at'])
            self.assertEqual(record['scores'],self.f.decision['scores'])
            self.assertEqual(record['source_attribution']['source_origin'],'authored_unit_fixture')
            self.assertEqual(record['policy_sha256'],digest(self.f.policy))
            self.assertEqual(manifest['review_evidence_sha256'],[digest(record)])
            self.assertEqual({p.name for p in destination.iterdir()},{'examples.jsonl','MANIFEST.json'})
            runtime=(destination/'examples.jsonl').read_text()
            self.assertNotIn('unit_rater_',runtime);self.assertNotIn('reviewed_at',runtime)
            pin=hashlib.sha256((destination/'MANIFEST.json').read_bytes()).hexdigest()
            self.assertEqual(len(load_approved_projection(destination,expected_manifest_sha256=pin,policy_id=self.f.policy['policy_id'])),1)
    def test_ratified_thresholds_and_policy_content_binding_are_enforced(self):
        self.f.decision['scores']['misconception_diagnosis']=1
        self.f.prepare()
        self.f.policy['thresholds']['misconception_diagnosis']=2
        with self.assertRaisesRegex(ValueError,'policy content'):self.f.prepare()
        self.f.decision['policy_sha256']=digest(self.f.policy)
        with self.assertRaisesRegex(ValueError,'promotion gate'):self.f.prepare()
        self.f.decision['scores']['misconception_diagnosis']=2
        self.f.prepare()
    def test_unratified_missing_boolean_or_weakened_thresholds_are_rejected(self):
        for bad in [None,{}, {'math_correctness':True}, {**self.f.policy['thresholds'],'math_correctness':1}]:
            policy={**self.f.policy,'thresholds':bad}
            decision={**self.f.decision,'policy_sha256':digest(policy)}
            with self.assertRaises(ValueError):prepare_promotion(self.f.source,self.f.revision,decision,policy,self.f.reviewers)
    def test_two_names_cannot_substitute_for_distinct_qualified_review_roles(self):
        self.f.reviewers['unit_rater_a']['roles']=['subject','pedagogy']
        self.f.reviewers['unit_rater_b']['roles']=[]
        with self.assertRaisesRegex(ValueError,'Distinct subject'):self.f.prepare()
    def test_private_ledger_is_immutable_and_preflight_preserves_runtime(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination=Path(temporary)/'approved';self.publish(destination)
            before=(destination/'examples.jsonl').read_bytes()
            ledger_path=destination.with_name('approved.review_evidence')/'review_ledger.json'
            ledger=json.loads(ledger_path.read_text());ledger['review_records'][0]['scores']['answer_protection']=0
            ledger_path.write_text(json.dumps(ledger),encoding='utf-8')
            with self.assertRaises(ValueError):self.publish(destination)
            self.assertEqual((destination/'examples.jsonl').read_bytes(),before)
    def test_repeated_same_publication_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination=Path(temporary)/'approved';self.publish(destination)
            files=[destination/'examples.jsonl',destination/'MANIFEST.json',destination.with_name('approved.review_evidence')/'review_ledger.json']
            before={str(p):p.read_bytes() for p in files}
            self.publish(destination)
            self.assertEqual(before,{str(p):p.read_bytes() for p in files})
    def test_partial_unknown_or_source_destinations_are_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir();(source/'original.txt').write_text('preserve')
            with self.assertRaisesRegex(ValueError,'original source'):self.publish(source/'approved',source_root=source)
            self.assertEqual({p.name for p in source.iterdir()},{'original.txt'})
            destination=root/'incomplete';destination.mkdir();(destination/'MANIFEST.json').write_text('{}')
            with self.assertRaises(ValueError):self.publish(destination)
            self.assertFalse(destination.with_name('incomplete.review_evidence').exists())
            with self.assertRaises(ValueError):self.publish(root/'nested',evidence_directory=root/'nested/private')
    def test_oversized_projection_is_rejected_before_publishing_either_directory(self):
        items=[]
        for i in range(260):
            source=copy.deepcopy(self.f.source);source['id']='SYN-DLG-UNIT-'+str(i)
            revision=copy.deepcopy(self.f.revision);revision['parent_id']=source['id']
            revision['messages']=[{'role':'student','text':str(i)+'a'*3995},{'role':'tutor','text':'b'*3999+'?'}]
            decision=copy.deepcopy(self.f.decision);decision.update(parent_id=source['id'],parent_sha256=digest(source),revision_sha256=digest(revision))
            items.append({'source_record':source,'revision':revision,'decision':decision})
        with tempfile.TemporaryDirectory() as temporary:
            destination=Path(temporary)/'oversized'
            with self.assertRaisesRegex(ValueError,'runtime bound'):publish_projection(items,destination,policy=self.f.policy,reviewers=self.f.reviewers)
            self.assertFalse(destination.exists());self.assertFalse(destination.with_name('oversized.review_evidence').exists())
    def test_source_attribution_and_loader_bounds_are_checked_before_export(self):
        del self.f.source['source_origin'];self.f.decision['parent_sha256']=digest(self.f.source)
        with self.assertRaisesRegex(ValueError,'attribution'):self.f.prepare()
        self.f=fixture();self.f.revision['messages']=self.f.revision['messages']*21;self.f.decision['revision_sha256']=digest(self.f.revision)
        with self.assertRaisesRegex(ValueError,'message count'):self.f.prepare()


if __name__=='__main__':unittest.main()
