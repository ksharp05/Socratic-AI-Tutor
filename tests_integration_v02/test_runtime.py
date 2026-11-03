import copy,json,sqlite3,tempfile,unittest,sys,inspect,os
from pathlib import Path
from types import SimpleNamespace
CODE_ROOT=Path(__file__).resolve().parents[1]
TEAM=CODE_ROOT if (CODE_ROOT/'src/tutor/app.py').is_file() else Path(os.environ.get('SOCRATES_TEAM_APP_ROOT',str(CODE_ROOT.parent/'Socratic Tutor Main'))).resolve()
sys.path.insert(0,str(TEAM/'src'))
from v02_integration.runtime import ContextualPreviewTutor,ambiguity,normalize_math_input,normalize_tutor_presentation
from tutor import store

class ContextualRuntime(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.app=object.__new__(ContextualPreviewTutor)
  self.app.conn=store.connect(Path(self.tmp.name)/'audit.db');self.calls=[];self.prompts=[]
  self.good='Which term is already represented by the starting value [normalized:ap03]?'
  self.app.llm=SimpleNamespace(enabled=True,complete=self.complete)
  self.state={'session':{'session_id':'authored-unit-only','mode':'practice'},'messages':[{'role':'student','content':'I counted five jumps.'}],
    'active_item':{'question_id':'public-dev-unit','prompt':'Find an AP term.','supporting_passage_ids':['normalized:ap03'],'hint_stage':1,'attempts':0}}
  self.update={'active_item':copy.deepcopy(self.state['active_item']),'draft':{'text':'Count the gaps.','kind':'hint','citations':[]}}
  self.app._call=self.call
 def tearDown(self):self.app.conn.close();self.tmp.cleanup()
 def complete(self,**kwargs):self.prompts.append(kwargs);return self.good
 def call(self,state,node,role,server,tool,args):
  self.calls.append((server,tool,args))
  if tool=='get_section':return {'passage_id':'normalized:ap03','text':'The first term starts the AP.'}
  if tool=='leak_check':return {'leak':False}
  raise AssertionError('Unexpected tool')
 def test_loaded_parent_is_the_current_team_checkout(self):
  from tutor.app import TutorApp
  self.assertEqual(Path(inspect.getfile(TutorApp)).resolve(),(TEAM/'src/tutor/app.py').resolve())
 def test_contextual_model_path_contains_latest_turn_but_no_private_state(self):
  self.state['private_answer']='MUST_NOT_APPEAR';self.state['hidden_simulator_card']={'true_mastery':1}
  result=self.app._generate_checked(self.state,self.update)
  self.assertEqual(result['draft']['text'],self.good);self.assertEqual(len(self.prompts),1)
  user=self.prompts[0]['user'];self.assertIn('I counted five jumps.',user);self.assertNotIn('MUST_NOT_APPEAR',user);self.assertNotIn('hidden_simulator_card',user)
  self.assertTrue(any(t[1]=='leak_check' for t in self.calls))
 def test_quiz_and_missing_evidence_never_invoke_model(self):
  self.state['session']['mode']='quiz'
  self.assertEqual(self.app._generate_checked(self.state,self.update),self.update);self.assertFalse(self.prompts)
  self.state['session']['mode']='practice';self.state['active_item']['supporting_passage_ids']=[];self.update['active_item']['supporting_passage_ids']=[]
  self.app._generate_checked(self.state,self.update);self.assertFalse(self.prompts)
 def test_citation_position_is_normalized_without_changing_source_or_words(self):
  self.assertEqual(normalize_tutor_presentation('Which step? [normalized:ap03].'),'Which step [normalized:ap03]?')
  self.assertEqual(normalize_tutor_presentation('Which step? Then do this.'),'Which step? Then do this.')
 def test_preview_prompt_keeps_the_three_selected_chapters(self):
  for concept in ['qe04','ap03','tr06']:
   self.state['active_item']['concept_ids']=[concept];self.update['active_item']['concept_ids']=[concept]
   self.app._generate_checked(self.state,self.update)
   system=self.prompts[-1]['system']
   for chapter in ['Quadratic Equations','Arithmetic Progressions','Introduction to Trigonometry']:self.assertIn(chapter,system)
   self.assertNotIn('Science',system)
 def test_bad_citations_long_outputs_and_leaks_fall_back_before_display(self):
  for bad in ['The final answer is 42.','What next [normalized:unknown]?',('word '*70)+'What?','What? Why?']:
   self.good=bad;result=self.app._generate_checked(self.state,self.update)
   self.assertEqual(result['draft']['text'],self.update['draft']['text'])
 def test_guard_error_or_positive_leak_never_displays_model_output(self):
  original=self.app._call
  def leak(*args):
   if args[4]=='leak_check':return {'leak':True}
   return original(*args)
  self.app._call=leak
  self.assertEqual(self.app._generate_checked(self.state,self.update),self.update)
 def test_ambiguity_preserves_counts_and_normalization_preserves_signs(self):
  self.state['messages'][-1]['content']='I got 1/2x'
  result=self.app._clarification(self.state)
  self.assertEqual(result['active_item'],self.state['active_item']);self.assertIsNone(result['grade']);self.assertFalse(self.prompts)
  self.assertIsNone(ambiguity('x = -1/2'));self.assertIsNone(ambiguity('x = 1/(2*x)'))
  self.assertIsNotNone(ambiguity('x = -'))
  self.assertEqual(normalize_math_input('x² − 3x = −1/2'),'x^2 - 3x = -1/2')
if __name__=='__main__':unittest.main()
