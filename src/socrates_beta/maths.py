from __future__ import annotations
import json,re,sys,threading,time,uuid
from pathlib import Path


def load_team_modules(app_root):
    app_root=Path(app_root).resolve(strict=True)
    if not (app_root/'src/tutor/mathcore.py').is_file():raise ValueError('Invalid team app root')
    existing=sys.modules.get('tutor')
    if existing and not Path(existing.__file__).resolve().is_relative_to(app_root/'src'):
        raise RuntimeError('A different tutor package is loaded; restart with the beta launcher')
    sys.path.insert(0,str(app_root/'src'))


class CheckedMaths:
    def __init__(self,app_root: Path):
        load_team_modules(app_root)
        from tutor import mathcore
        self.core=mathcore
        file=Path(app_root)/'content/dataset-v0.10.0/practice_questions.jsonl'
        # Only public practice prompts. No private tests, hidden keys or held-out corpus.
        self.items={x['question_id']:x for x in [json.loads(l) for l in file.read_text(encoding='utf-8-sig').splitlines()]}
        self.keys={};self.lock=threading.RLock()
    def eligible(self,scope,concept=None):
        if scope.grade!=10 or scope.subject.casefold()!='mathematics':return []
        chapter={4:'quadratic_equations',5:'arithmetic_progressions',8:'introduction_to_trigonometry'}.get(scope.unit)
        return [x for x in self.items.values() if (not chapter or x['chapter']==chapter or (scope.unit==8 and x['chapter'].startswith('trig')))
                and (not concept or concept in x['problem']['concept_ids'])]
    def key(self,qid):
        with self.lock:
            if qid not in self.keys:
                computed=self.core.compute_key(self.items[qid]['problem'])
                if not computed['verified']:raise ValueError('Calculation routes disagree')
                self.keys[qid]=computed['key']
            return self.keys[qid]
    def public_item(self,qid):
        x=self.items[qid];kind=x['answer_contract']['allowed_kinds'][0]
        return {'id':qid,'prompt':x['prompt'],'concepts':x['problem']['concept_ids'],'chapter':x['chapter'],
          'answer_kind':kind,'units':x['answer_contract'].get('required_units_by_kind',{}).get(kind),
          'difficulty':x['difficulty']['level'],'source_passages':x['supporting_passage_ids']}
    def parse(self,text,item):
        if not isinstance(text,str) or not text.strip() or len(text)>512:raise ValueError('Use a short exact answer')
        kind=item['answer_contract']['allowed_kinds'][0];raw=text.strip()
        if raw.startswith('{') and '"kind"' in raw:
            typed=json.loads(raw)
            if not isinstance(typed,dict) or typed.get('kind')!=kind:raise ValueError('Answer kind does not match this question')
            # Grading kernel validates the closed answer contract and bounded expression grammar.
            if kind=='classification' and typed.get('value') not in {'two_distinct_real','repeated_real','no_real'}:raise ValueError('Use one of the classifications stated in the question')
            return typed
        if kind in ('scalar','finite_set'):
            template={'kind':kind,'values':[]} if kind=='finite_set' else {'kind':kind,'value':'0'}
            result=self.core.parse_answer(raw,template)
            if not result['ok']:raise ValueError('Use comma-separated roots, an exact value, or no real roots')
            typed=result['typed']
        elif kind=='boolean':
            v=raw.casefold()
            if v not in ('yes','no','true','false'):raise ValueError('Answer yes/no or true/false')
            typed={'kind':kind,'value':v in ('yes','true')}
        elif kind=='classification':
            v=raw.casefold().replace(' ','_')
            aliases={'two_real_roots':'two_distinct_real','two_distinct':'two_distinct_real','one_repeated_real':'repeated_real','no_real_roots':'no_real'}
            typed={'kind':kind,'value':aliases.get(v,v)}
            if typed['value'] not in {'two_distinct_real','repeated_real','no_real'}:raise ValueError('Use one of the classifications stated in the question')
        elif kind=='coefficients':
            body=re.sub(r'[abc]\s*=','',raw,flags=re.I).strip('[](){} ')
            parts=[self.core.normalise_expression(x.strip()) for x in body.split(',')]
            if len(parts)!=3:raise ValueError('Write a, b, c separated by commas')
            typed={'kind':kind,'values':parts}
        elif kind=='defined_value':
            undefined=bool(re.fullmatch(r'(?i)(undefined|not defined|does not exist)',raw))
            typed={'kind':kind,'defined':not undefined,'value':None if undefined else self.core.normalise_expression(raw)}
        else:raise ValueError('This answer format is not supported yet')
        unit=item['answer_contract'].get('required_units_by_kind',{}).get(kind)
        if unit:typed['unit']=unit
        return typed
    def grade(self,qid,text):
        item=self.items[qid]
        try:
            typed=self.parse(text,item)
            return self.core.grade(typed,self.key(qid))
        except (ValueError,TypeError,KeyError,json.JSONDecodeError):
            return {'status':'invalid_response','correct':False,'scorable':False,'reasoning_evaluated':False}
    def hint(self,qid,stage):return self.items[qid]['hint_stages'][max(0,min(stage-1,2))]['prompt']


class AssessmentService:
    def __init__(self,repo,maths):self.repo,self.maths=repo,maths;self.lock=threading.RLock()
    def start(self,session,mode='practice',concept=None,question_id=None):
        with self.lock:return self._start(session,mode,concept,question_id)
    def _eligible(self,scope,concept):return self.maths.eligible(scope,concept)
    def _bind_publication(self,record,eligible):pass
    def _start(self,session,mode='practice',concept=None,question_id=None):
        from .ports import Scope
        if mode not in ('practice','quiz','diagnostic'):raise ValueError('Unknown mode')
        if self.repo.active_assessment(session['id'],session['owner']) or self.repo.open_check(session['owner']):raise ValueError('Finish or leave the current practice first')
        eligible=self._eligible(Scope(**session['scope']),concept)
        if not eligible:raise ValueError('Checked practice is available for the three Class 10 maths chapters; this topic is not yet covered')
        aid=uuid.uuid4().hex
        # Deterministic per-run ordering with unique public items; no benchmark material is read.
        import hashlib
        eligible.sort(key=lambda q:hashlib.sha256((aid+q['question_id']).encode()).digest())
        ids=[x['question_id'] for x in eligible]
        if question_id:
            if mode!='practice' or question_id not in ids:raise ValueError('Requested public item is not available for this practice scope')
            ids.remove(question_id);ids.insert(0,question_id)
        limit=1 if mode=='practice' else min(5,len(ids))
        record={'id':aid,'session_id':session['id'],'owner':session['owner'],'mode':mode,'created':time.time(),
          'state':{'queue':ids,'index':0,'limit':limit,'complete':False,'hint_stage':0,'submissions':[],
                   'concept':concept,'next_target':None,'used':[]}}
        self._bind_publication(record,eligible)
        self.repo.save_assessment(record);return self.public(record)
    def public(self,a):
        state=a['state'];done=state['complete']
        result={'id':a['id'],'mode':a['mode'],'complete':done,'position':min(state['index']+1,state['limit']),'total':state['limit'],
                'hint_stage':state['hint_stage'],'item':None if done else self.maths.public_item(state['queue'][state['index']])}
        if done:
            counted=[s for s in state['submissions'] if s.get('counted')]
            result['summary']={'correct':sum(s['grade']['status']=='correct' for s in counted),
                'scored':sum(s['grade']['scorable'] for s in counted),'submitted':len(counted),
                'reasoning_assessed':False,'recommended_concept':state.get('next_target')}
        return result
    def submit(self,owner,aid,text,request_id):
        with self.lock:
            a=self.repo.assessment(aid,owner);s=a['state']
            prior=next((v for v in s['submissions'] if v['request_id']==request_id),None)
            if prior:
                import hashlib
                if prior.get('answer_sha256') and prior['answer_sha256']!=hashlib.sha256(text.encode()).hexdigest():raise ValueError('Request id already used for a different answer')
                return prior['response']
            if s['complete']:raise ValueError('This check is complete')
            qid=s['queue'][s['index']];grade=self.maths.grade(qid,text)
            if grade['status']=='unverified':return {'message':'This answer could not be verified; try a supported exact form.','status':'unverified','assessment':self.public(a)}
            if grade['status']=='invalid_response':return {'message':'I could not parse that answer. Use the format shown below the question.','status':'invalid_response','assessment':self.public(a)}
            node=self.maths.items[qid]['problem']['concept_ids'][0]
            self.repo.observe(owner,a['session_id'],node,'checked_answer',{'status':grade['status'],'question_id':qid,'mode':a['mode']})
            if a['mode']=='practice':
                if grade['correct']:s['complete']=True
                else:s['hint_stage']=min(3,s['hint_stage']+1)
                message=('Your submitted answer checks out mathematically. Which step did you use?' if grade['correct'] else
                         'That answer does not match yet. '+self.maths.hint(qid,s['hint_stage']))
                status=grade['status']
            else:
                message='Recorded.';status='recorded'
                if not grade['correct']:s['next_target']=node
                s['used'].append(qid);s['index']+=1
                if s['index']>=s['limit']:s['complete']=True
                elif a['mode']=='diagnostic':
                    # Branch to another public item exercising the observed concept after a miss.
                    remaining=s['queue'][s['index']:]
                    target=[q for q in remaining if node in self.maths.items[q]['problem']['concept_ids']]
                    if not grade['correct'] and target:
                        chosen=target[0];s['queue'].remove(chosen);s['queue'].insert(s['index'],chosen)
            import hashlib
            entry={'answer_sha256':hashlib.sha256(text.encode()).hexdigest(),'request_id':request_id,'question_id':qid,'grade':grade,'counted':bool(a['mode']!='practice' or grade['correct'])}
            s['submissions'].append(entry)
            response={'message':message,'status':status,'verification':'code_checked','reasoning_assessed':False,'assessment':self.public(a)}
            entry['response']=response
            self.repo.save_assessment(a);return response
    def hint(self,owner,aid):
        with self.lock:
            a=self.repo.assessment(aid,owner);s=a['state']
            if a['mode']!='practice' or s['complete']:raise ValueError('Hints are available during active practice only')
            s['hint_stage']=min(3,s['hint_stage']+1);self.repo.save_assessment(a)
            return {'hint':self.maths.hint(s['queue'][s['index']],s['hint_stage']),'stage':s['hint_stage']}
    def leave(self,owner,aid):
        with self.lock:
            a=self.repo.assessment(aid,owner);a['state']['complete']=True;a['state']['left_early']=True;self.repo.save_assessment(a)
            result=self.public(a);result['left_early']=True;return result
