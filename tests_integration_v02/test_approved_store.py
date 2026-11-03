import hashlib,json,tempfile,unittest
from pathlib import Path
from v02_integration.approved_store import load_approved_projection
from v02_integration.audit import write_json

class ApprovedStore(unittest.TestCase):
 def projection(self,p):
  row={'example_id':'authored_unit_fixture','chapter':'ap','messages':[{'role':'student','text':'I counted the starting position twice.'},{'role':'tutor','text':'Which position is already represented?'}]}
  raw=(json.dumps(row)+'\n').encode();(p/'examples.jsonl').write_bytes(raw)
  write_json(p/'MANIFEST.json',{'records':1,'file':'examples.jsonl','sha256':hashlib.sha256(raw).hexdigest(),'policies':['UNIT_FIXTURE_ONLY'],'review_evidence_sha256':['0'*64],'teaching_permissions_unchanged':True})
  return hashlib.sha256((p/'MANIFEST.json').read_bytes()).hexdigest()
 def test_pinned_fixture_passes_and_stale_or_unpinned_data_fails(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);pin=self.projection(p)
   self.assertEqual(len(load_approved_projection(p,expected_manifest_sha256=pin,policy_id='UNIT_FIXTURE_ONLY')),1)
   for bad in [None,'0'*64]:
    with self.assertRaises(ValueError):load_approved_projection(p,expected_manifest_sha256=bad,policy_id='UNIT_FIXTURE_ONLY')
   (p/'examples.jsonl').write_text('changed',encoding='utf-8')
   with self.assertRaises(ValueError):load_approved_projection(p,expected_manifest_sha256=pin,policy_id='UNIT_FIXTURE_ONLY')
 def test_policy_and_review_hash_types_fail_closed(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);pin=self.projection(p)
   with self.assertRaises(ValueError):load_approved_projection(p,expected_manifest_sha256=pin,policy_id=None)
   m=json.loads((p/'MANIFEST.json').read_text());m['review_evidence_sha256']=['not-a-hash'];write_json(p/'MANIFEST.json',m)
   pin=hashlib.sha256((p/'MANIFEST.json').read_bytes()).hexdigest()
   with self.assertRaisesRegex(ValueError,'review evidence hashes'):load_approved_projection(p,expected_manifest_sha256=pin,policy_id='UNIT_FIXTURE_ONLY')
 def test_raw_corpus_wrong_policy_and_extra_files_are_never_loaded(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);pin=self.projection(p)
   with self.assertRaises(ValueError):load_approved_projection(p,expected_manifest_sha256=pin,policy_id='different')
   (p/'reference_answers_dev_only.jsonl').write_text('private',encoding='utf-8')
   with self.assertRaises(ValueError):load_approved_projection(p,expected_manifest_sha256=pin,policy_id='UNIT_FIXTURE_ONLY')
if __name__=='__main__':unittest.main()
