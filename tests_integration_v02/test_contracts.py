import os
import pytest
import copy,csv,json,tempfile,unittest
from pathlib import Path
from v02_integration.audit import digest,load_json,read_rows,COLLECTIONS,priority_queue,text_profile,csv_view
from v02_integration.repair import repair
from v02_integration.promotion import prepare_promotion,publish_projection
from v02_integration.math_audit import check_reference,expression

ROOT=Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE',Path(__file__).resolve().parents[1])).resolve()
SOURCE=ROOT/'Directions/socratic_tutor_dataset_expanded_v0_2'

@pytest.mark.local_corpus
class SnapshotContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.problems=read_rows(SOURCE/COLLECTIONS['problems']);cls.references=read_rows(SOURCE/COLLECTIONS['references'])
  cls.dialogues=read_rows(SOURCE/COLLECTIONS['dialogues'])
 def test_all_232_keys_recomputed_from_public_prompt_and_mutations_detected(self):
  P={p['id']:p for p in self.problems}
  self.assertEqual(len(P),232)
  for r in self.references:
   self.assertEqual(check_reference(P[r['problem_id']],r)['status'],'pass')
   if r['math_check']['type'] in {'ap_nth','ap_difference','ap_sum','ap_zero','trig_ratio','trig_identity','special_angle','cot'}:
    bad=copy.deepcopy(r);bad['expected_answer']='987654321'
    self.assertEqual(check_reference(P[r['problem_id']],bad)['status'],'fail')
 def test_116_balanced_queue_is_pending_and_binds_exact_source(self):
  queue=priority_queue(self.dialogues,{r['id']:r for r in self.problems});D={r['id']:r for r in self.dialogues}
  self.assertEqual(len(queue),116);self.assertEqual(len({r['misconception_id'] for r in queue}),29)
  for r in queue:
   self.assertEqual(r['source_content_sha256'],digest(D[r['dialogue_id']]))
   self.assertEqual(r['status'],'pending_human_review');self.assertEqual(r['decision'],'')
 def test_repair_changes_only_family_metadata_and_preserves_source(self):
  raw=(SOURCE/COLLECTIONS['messages']).read_bytes()
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);receipt=repair(SOURCE,root/'derived',root/'report.json')
   self.assertEqual(receipt['changed_records'],2040)
   derived=read_rows(root/'derived/dev/contextual_learner_messages.jsonl');original=read_rows(SOURCE/COLLECTIONS['messages'])
   self.assertEqual(len(derived),2400)
   for a,b in zip(original,derived):
    self.assertEqual({k:v for k,v in a.items() if k!='variant_family'},{k:v for k,v in b.items() if k!='variant_family'})
   (root/'derived/dev/contextual_learner_messages.jsonl').write_bytes(b'conflict')
   with self.assertRaises(ValueError):repair(SOURCE,root/'derived',root/'report.json')
  self.assertEqual(raw,(SOURCE/COLLECTIONS['messages']).read_bytes())
 def test_strict_parser_csv_safety_and_expression_bounds(self):
  for value in ['{"a":1,"a":2}','{"a":NaN}','{"a":1e309}']:
   with self.assertRaises(ValueError):load_json(value)
  for value in ['__import__("os")','x.foo','sin(x)','x'*300]:
   with self.assertRaises(ValueError):expression(value)
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'review.csv';csv_view(p,[{'text':'=HYPERLINK("bad")'},{'text':'ordinary'}])
   with p.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
   self.assertTrue(rows[0]['text'].startswith("'="));self.assertEqual(rows[1]['text'],'ordinary')
 def test_templates_do_not_count_as_independent_observations(self):
  profile=text_profile(['Ask about 12.','Ask about 13.','Ask about 12.'])
  self.assertEqual(profile['unique_exact_texts'],2);self.assertEqual(profile['unique_number_normalized_patterns'],1)

class HumanReviewGate(unittest.TestCase):
 def setUp(self):
  # Authored unit fixtures exercise validation; these are not real approvals.
  self.source={'id':'SYN-DLG-UNIT','split':'development_only','curriculum_scope':'in_scope','misconception_id':'Q01','chapter':'quadratics','mode':'practice','messages':[],'source_origin':'authored_unit_fixture','generator_version':'unit_fixture','creation_date':'2026-11-02'}
  self.revision={'parent_id':'SYN-DLG-UNIT','kind':'reviewed_development_dialogue','chapter':'quadratics','misconception_id':'Q01',
   'messages':[{'role':'student','text':'I do not understand the sign.'},{'role':'tutor','text':'Which term changed sign?'}]}
  self.policy={'policy_id':'UNIT_TEST_ONLY','ratified':True,'approved_by':'unit_fixture_owner','ratification_reference':'unit_fixture_not_real_approval','thresholds':{k:v for k,v in zip(['math_correctness','misconception_diagnosis','actionable_scaffolding','clarity_and_tone','answer_protection','context_fidelity'],[2,1,1,1,2,2])}}
  self.reviewers={'unit_rater_a':{'kind':'human','active':True,'roles':['subject']},'unit_rater_b':{'kind':'human','active':True,'roles':['pedagogy']}}
  self.decision={'decision':'approve','parent_id':self.source['id'],'parent_sha256':digest(self.source),'revision_sha256':digest(self.revision),
   'policy_id':self.policy['policy_id'],'policy_sha256':digest(self.policy),'reviewer_ids':list(self.reviewers),'review_origin':'human','reviewed_at':'2026-11-02T10:00:00+05:30',
   'scores':{k:2 for k in ['math_correctness','misconception_diagnosis','actionable_scaffolding','clarity_and_tone','answer_protection','context_fidelity']}}
 def prepare(self):return prepare_promotion(self.source,self.revision,self.decision,self.policy,self.reviewers)
 def test_bound_fixture_passes_but_unratified_or_unassigned_real_default_fails(self):
  self.assertEqual(self.prepare()['status'],'human_approved_development_example')
  self.policy['ratified']=False
  with self.assertRaises(ValueError):self.prepare()
  self.policy['ratified']=True;self.decision['policy_sha256']=digest(self.policy);self.reviewers={}
  with self.assertRaises(ValueError):self.prepare()
 def test_autoapproval_duplicate_reviewers_and_stale_revisions_fail(self):
  for field,value in [('review_origin','ai'),('reviewer_ids',['unit_rater_a','unit_rater_a']),('revision_sha256','0'*64),('reviewed_at','2026-11-02')]:
   old=self.decision[field];self.decision[field]=value
   with self.assertRaises(ValueError):self.prepare()
   self.decision[field]=old
  self.decision['scores']['answer_protection']=1
  with self.assertRaises(ValueError):self.prepare()
  self.decision['scores']['answer_protection']=True
  with self.assertRaises(ValueError):self.prepare()
 def test_private_fields_quarantine_and_critic_sources_rejected(self):
  self.revision['expected_answer']='must never be served';self.decision['revision_sha256']=digest(self.revision)
  with self.assertRaises(ValueError):self.prepare()
  del self.revision['expected_answer'];self.decision['revision_sha256']=digest(self.revision)
  self.source['misconception_id']='T08';self.decision['parent_sha256']=digest(self.source)
  with self.assertRaises(ValueError):self.prepare()
  self.source['misconception_id']='Q01';self.source['id']='SYN-PAIR-UNIT';self.decision['parent_id']=self.source['id'];self.decision['parent_sha256']=digest(self.source)
  with self.assertRaises(ValueError):self.prepare()
 def test_projection_revalidates_decisions_and_is_copy_on_write(self):
  item={'source_record':self.source,'revision':self.revision,'decision':self.decision}
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'approved';rows=publish_projection([item],p,policy=self.policy,reviewers=self.reviewers)
   self.assertEqual(set(rows[0]),{'example_id','chapter','messages'})
   self.decision['decision']='reject'
   with self.assertRaises(ValueError):publish_projection([item],p,policy=self.policy,reviewers=self.reviewers)
   self.decision['decision']='approve';(p/'examples.jsonl').write_text('changed',encoding='utf-8')
   with self.assertRaises(ValueError):publish_projection([item],p,policy=self.policy,reviewers=self.reviewers)
if __name__=='__main__':unittest.main()
