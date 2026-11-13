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
        from tutor.question_catalog import allowed
        for name in ('quiz_items.json','chapter_quiz_items.json'):
            demo=Path(app_root)/'content/milestone2_dev'/name
            for item in json.loads(demo.read_text(encoding='utf-8-sig')):
                if item['question_id'] in self.items or not allowed(item,'quiz') or allowed(item,'practice'):
                    raise ValueError('Invalid or duplicate development-check question')
                self.items[item['question_id']]=item
        for item in json.loads((Path(app_root)/'content/milestone2_dev/practice_items.json').read_text(encoding='utf-8-sig')):
            if item['question_id'] in self.items or not allowed(item,'practice') or allowed(item,'quiz'):
                raise ValueError('Invalid or duplicate development practice question')
            self.items[item['question_id']]=item
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
          'difficulty':x['difficulty']['level'],'source_passages':x['supporting_passage_ids'],
          'supports_step_feedback':x['problem'].get('task_type')=='trig_triangle_ratio'}
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
            unit=item['answer_contract'].get('required_units_by_kind',{}).get(kind)
            if unit:template['unit']=unit
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

LAST_HINT=3


class AssessmentService:
    def __init__(self,repo,maths):
        self.repo,self.maths=repo,maths
        self.lock=threading.RLock()

    def start(self,session,mode='practice',concept=None,question_id=None):
        with self.repo.owner_guard(session['owner']), self.lock:
            return self._start(session,mode,concept,question_id)

    def _eligible(self,scope,concept,mode):
        from tutor.question_catalog import allowed
        return [item for item in self.maths.eligible(scope,concept) if allowed(item,mode)]
    def _bind_publication(self,record,eligible):pass
    def _guard_mode(self,record,conn):
        from tutor.question_catalog import allowed
        state=record['state']
        if state.get('policy_revoked'):
            return {'id':record['id'],'mode':record['mode'],'complete':True,'revoked':True,
                    'position':min(state['index']+1,state['limit']),'total':state['limit'],
                    'hint_stage':0,'item':None,'message':'This check is no longer available for its permitted use. Please start again.'}
        if state.get('complete'):
            return None
        selected=set(state.get('queue',[])[:state.get('limit',0)]) | set(state.get('used',[]))
        if not selected or any(qid not in self.maths.items or not allowed(self.maths.items[qid],record['mode']) for qid in selected):
            state.update(complete=True,policy_revoked=True)
            self.repo.save_assessment(record,conn=conn)
            return self._guard_mode(record,conn)
        return None
    def _guard_assessment(self,record,conn):return self._guard_mode(record,conn)

    def _start(self,session,mode='practice',concept=None,question_id=None):
        from .ports import Scope
        if mode not in ('practice','quiz','diagnostic'):raise ValueError('Unknown mode')
        with self.repo.transaction() as conn:
            session=self.repo.session(session['id'],session['owner'],conn=conn)
            if (self.repo.active_assessment(session['id'],session['owner'],conn=conn)
                    or self.repo.open_check(session['owner'],conn=conn)):
                raise ValueError('Finish or leave the current practice first')
            eligible=self._eligible(Scope(**session['scope']),concept,mode)
            if not eligible:raise ValueError('No questions are available for this topic and mode yet.')
            aid=uuid.uuid4().hex
            # Deterministic per-run ordering with unique public items; no benchmark material is read.
            import hashlib
            eligible.sort(key=lambda q:hashlib.sha256((aid+q['question_id']).encode()).digest())
            ids=[x['question_id'] for x in eligible]
            if question_id:
                if mode!='practice' or question_id not in ids:raise ValueError('Requested public item is not available for this practice scope')
                ids.remove(question_id);ids.insert(0,question_id)
            due=self._due_revisit(session,ids,conn) if mode=='practice' and not question_id else None
            if due:
                ids.remove(due);ids.insert(0,due)
            limit=1 if mode=='practice' else min(5,len(ids))
            record={'id':aid,'session_id':session['id'],'owner':session['owner'],'mode':mode,'created':time.time(),
              'state':{'queue':ids,'index':0,'limit':limit,'complete':False,'hint_stage':0,'submissions':[],
                       'concept':concept,'next_target':None,'used':[],'revisit':bool(due)}}
            self._bind_publication(record,eligible)
            self.repo.save_assessment(record,conn=conn)
            return self.public(record,conn=conn)

    def _queue_on(self):
        return getattr(self.repo,'revisit_queue',False)

    def _content_sha256(self,qid):
        """Hash of the full public item, so a saved mark is bound to the exact question content."""
        import hashlib
        return hashlib.sha256(json.dumps(self.maths.items[qid],sort_keys=True,separators=(',',':')).encode()).hexdigest()

    def _due_revisit(self,session,ids,conn):
        """Oldest question saved in an earlier conversation that is still eligible here, with unchanged content.
        `ids` is already filtered by scope, mode and publication policy, so a mark never bypasses those checks."""
        if not self._queue_on():return None
        eligible=set(ids)
        for row in self.repo.pending_revisits(session['owner'],conn=conn):
            qid=row['question_id']
            if (row['session_id']!=session['id'] and qid in eligible
                    and row['content_sha256']==self._content_sha256(qid)):
                return qid
        return None

    def _mark_after_last_hint(self,a,qid,conn):
        """R2 queue: a practice question whose last hint has been shown comes back in a later conversation."""
        if a['mode']!='practice' or a['state']['hint_stage']<LAST_HINT or not self._queue_on():return False
        self.repo.mark_revisit(a['owner'],qid,session_id=a['session_id'],chapter=self.maths.items[qid].get('chapter',''),
                               content_sha256=self._content_sha256(qid),conn=conn)
        return True

    def public(self,a,*,conn=None):
        revoked=self._guard_mode(a,conn)
        if revoked:return revoked
        state=a['state'];done=state['complete']
        result={'id':a['id'],'mode':a['mode'],'complete':done,'position':min(state['index']+1,state['limit']),'total':state['limit'],
                'hint_stage':state['hint_stage'],'item':None if done else self.maths.public_item(state['queue'][state['index']]),
                'revisit':bool(state.get('revisit'))}
        if done and not state.get('left_early'):
            counted=[s for s in state['submissions'] if s.get('counted')]
            result['summary']={'correct':sum(s['grade']['status']=='correct' for s in counted),
                'scored':sum(s['grade']['scorable'] for s in counted),'submitted':len(counted),
                'reasoning_assessed':False,'recommended_concept':state.get('next_target')}
        return result

    def _ensure_no_other_check(self,owner,aid,conn):
        active=self.repo.open_check(owner,conn=conn)
        if active and active['id']!=aid:
            raise ValueError('Finish or leave the current check before returning to other practice.')

    def submit(self,owner,aid,text,request_id):
        with self.repo.owner_guard(owner):
            return self._submit(owner,aid,text,request_id)

    def _submit(self,owner,aid,text,request_id):
        with self.lock, self.repo.transaction() as conn:
            a=self.repo.assessment(aid,owner,conn=conn);s=a['state']
            revoked=self._guard_assessment(a,conn)
            if revoked:return {'status':'question_revoked','message':revoked['message'],'assessment':revoked}
            self._ensure_no_other_check(owner,aid,conn)
            if s.get('left_early'):raise ValueError('This check was left early.')
            prior=next((v for v in s['submissions'] if v['request_id']==request_id),None)
            if prior:
                import hashlib
                if prior.get('answer_sha256') and prior['answer_sha256']!=hashlib.sha256(text.encode()).hexdigest():raise ValueError('Request id already used for a different answer')
                return prior['response']
            if s['complete']:raise ValueError('This check is complete')
            qid=s['queue'][s['index']];grade=self.maths.grade(qid,text)
            if grade['status']=='unverified':return {'message':'This answer could not be verified; try a supported exact form.','status':'unverified','assessment':self.public(a,conn=conn)}
            if grade['status']=='invalid_response':return {'message':'I could not parse that answer. Use the format shown below the question.','status':'invalid_response','assessment':self.public(a,conn=conn)}
            concepts=list(self.maths.items[qid]['problem']['concept_ids'])
            node=s.get('concept') if s.get('concept') in concepts else concepts[0]
            if a['mode']=='practice':
                self.repo.observe(owner,a['session_id'],node,'checked_answer',
                    {'status':grade['status'],'question_id':qid,'concept_ids':concepts,
                     'mode':a['mode'],'assessment_id':aid},conn=conn)
            saved=False
            if a['mode']=='practice':
                if grade['correct']:
                    s['complete']=True
                    # Only code-checked correct work clears a saved mark, and only for the same content.
                    if self._queue_on():
                        self.repo.resolve_revisit(owner,qid,content_sha256=self._content_sha256(qid),conn=conn)
                else:
                    s['hint_stage']=min(3,s['hint_stage']+1)
                    saved=self._mark_after_last_hint(a,qid,conn)
                message=('Your submitted answer checks out mathematically. Which step did you use?' if grade['correct'] else
                         'That answer does not match yet. '+self.maths.hint(qid,s['hint_stage']))
                status=grade['status']
            else:
                message='Recorded.';status='recorded'
                if not grade['correct']:s['next_target']=node
                s['used'].append(qid);s['index']+=1
                if s['index']>=s['limit']:s['complete']=True
                elif a['mode']=='diagnostic':
                    remaining=s['queue'][s['index']:]
                    target=[q for q in remaining if node in self.maths.items[q]['problem']['concept_ids']]
                    if not grade['correct'] and target:
                        chosen=target[0];s['queue'].remove(chosen);s['queue'].insert(s['index'],chosen)
            import hashlib
            entry={'answer_sha256':hashlib.sha256(text.encode()).hexdigest(),'request_id':request_id,'question_id':qid,'grade':grade,
                   'counted':bool(a['mode']!='practice' or grade['correct']),'observation_recorded':a['mode']=='practice'}
            s['submissions'].append(entry)
            # Do not reveal intermediate quiz/diagnostic outcomes through the
            # dashboard or learning map. Commit all observations on completion.
            # Older entries without this flag were recorded by earlier builds.
            if a['mode']!='practice' and s['complete']:
                for completed in s['submissions']:
                    if completed.get('observation_recorded') is False:
                        completed_qid=completed['question_id']
                        completed_concepts=list(self.maths.items[completed_qid]['problem']['concept_ids'])
                        completed_node=s.get('concept') if s.get('concept') in completed_concepts else completed_concepts[0]
                        self.repo.observe(owner,a['session_id'],completed_node,'checked_answer',
                            {'status':completed['grade']['status'],'question_id':completed_qid,
                             'concept_ids':completed_concepts,'mode':a['mode'],'assessment_id':aid},conn=conn)
                        completed['observation_recorded']=True
            response={'message':message,'status':status,'verification':'code_checked','reasoning_assessed':False,'assessment':self.public(a,conn=conn)}
            if saved:response['saved_for_later']=True
            entry['response']=response
            self.repo.save_assessment(a,conn=conn)
            return response

    def hint(self,owner,aid,step=None,continuation=None):
        with self.repo.owner_guard(owner):
            return self._hint(owner,aid,step,continuation)

    def _hint(self,owner,aid,step=None,continuation=None):
        with self.lock, self.repo.transaction() as conn:
            a=self.repo.assessment(aid,owner,conn=conn);s=a['state']
            revoked=self._guard_assessment(a,conn)
            if revoked:return {'status':'question_revoked','hint':revoked['message'],'stage':0,'assessment':revoked}
            self._ensure_no_other_check(owner,aid,conn)
            if a['mode']!='practice' or s['complete']:raise ValueError('Hints are available during active practice only')
            qid=s['queue'][s['index']]
            if step:
                from .safety import emotional_support_reply

                if support := emotional_support_reply(step):
                    return {'hint':support,'stage':s['hint_stage'],'status':'emotional_support',
                            'persistence':'not_saved_support'}
                from .ratio_hint import ratio_hint
                tailored = ratio_hint(self.maths.items[qid]['problem'], step, continuation)
                if tailored is not None:
                    text, followup = tailored
                    result = {'hint':text,'stage':s['hint_stage'],'status':'step_feedback'}
                    if followup:
                        result['_followup'] = followup
                    return result
            s['hint_stage']=min(3,s['hint_stage']+1);self.repo.save_assessment(a,conn=conn)
            result={'hint':self.maths.hint(qid,s['hint_stage']),'stage':s['hint_stage']}
            if self._mark_after_last_hint(a,qid,conn):result['saved_for_later']=True
            return result

    def leave(self,owner,aid):
        with self.repo.owner_guard(owner):
            return self._leave(owner,aid)

    def _leave(self,owner,aid):
        with self.lock, self.repo.transaction() as conn:
            a=self.repo.assessment(aid,owner,conn=conn)
            if a['state']['complete'] and not a['state'].get('left_early'):
                raise ValueError('This check is already complete.')
            a['state']['complete']=True;a['state']['left_early']=True
            self.repo.save_assessment(a,conn=conn)
            result=self.public(a,conn=conn);result['left_early']=True;return result
