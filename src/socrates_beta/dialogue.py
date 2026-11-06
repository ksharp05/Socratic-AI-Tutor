from __future__ import annotations
import json,re,threading,time
from dataclasses import asdict
from ncert_pipeline.dialogue import SYSTEM,redact,validate_reply
from .ports import Scope
from .topics import broad_topic,discovery_question,navigation_reply

PROMPT=SYSTEM+'''
This is Socrates beta. When a learner makes a factual misconception, explain the supported distinction without
assigning a correctness score. A cited fact must retain qualifiers in its source, particularly the highest
nonzero power in a quadratic after collecting terms. For a quadratic definition explicitly state that the highest nonzero power is two after collecting terms.
Having a nonzero squared coefficient alone is insufficient if higher powers remain.
Do not add facts about graphs, parabolas or the x-axis unless the supplied excerpts describe them.
Keep analogies brief and preserve causal mechanism. The supplied teaching move guides the next question,
but honour the learner's explicit request for simpler wording or a different approach. Do not ask them to invent
an example if they just said they don't understand the underlying word. Use a concrete, smaller question.
Do not put citation ids in prose; return them only in the citations list. No Markdown tables or headings.
Acknowledge a topic correction briefly. Aim for 35-45 words so the hard 60-word limit is met.
The follow-up question must be answerable from the explanation you just gave. Do not introduce a new technical
term in the question before explaining it. Ask for one small inference rather than a large new application.
In science, never suggest tasting, touching, or smelling chemicals to identify them. Discuss safe indicators
and classroom-supervised methods instead. Do not make practical tasting instructions from textbook descriptions.
Avoid the words correct and incorrect even as conversational modifiers; give the source-backed distinction instead. Never claim that this conversation proves learning or mastery.
'''
DISTRESS=re.compile(r'\b(kill myself|end my life|want to die|hurt myself|self[- ]harm|suicid\w*|no reason to live|jeena nahi|mar jana)\b',re.I)
DISTRESS_REPLY='Your safety comes first. Please contact a trusted adult nearby now. If you are in immediate danger, contact your local emergency service. Can you reach someone who can stay with you?'
ACCESS=re.compile(r'ignore (?:all |the )?(?:previous|prior) instructions|system prompt|answer key|(?:i am|i.m) (?:the |an? )?(?:admin|developer|teacher)',re.I)
SMALL=re.compile(r"\b(idk|dunno|confused|stuck|don.t (?:know|understand|get)|no idea|not sure|still unclear)\b",re.I)


def unsafe_chemical_guidance(reply: str) -> bool:
    if not re.search(r'\b(acid|base|chemical)\w*\b',reply,re.I):return False
    # Factual sensory descriptions are not imperatives. Remove explicit prohibitions before testing directives.
    text=re.sub(r"(?i)\b(?:do not|don't|never|avoid)\s+(?:taste|tasting|smell|smelling)\b",'SAFE_PROHIBITION',reply)
    return bool(re.search(r'(?i)(?:^|[.!?]\s+)(?:please\s+)?(?:taste|smell)\b|'
        r'\b(?:you (?:can|could|should|must)|try|identify[^.!?]{0,30}by|test[^.!?]{0,30}by|by)\s+(?:taste|tasting|smell|smelling)\b|'
        r'\b(?:can|could|would|will|should)\s+you\s+(?:taste|smell)\b|'
        r'\bwhich (?:sample|chemical|acid|base)[^.!?]{0,30}\b(?:tastes|smells)\b',text))


class DialogueService:
    def __init__(self,repo,registry,language=None):
        self.repo,self.registry,self.language=repo,registry,language;self.locks={};self.guard=threading.Lock()
    def session_lock(self,sid):
        with self.guard:return self.locks.setdefault(sid,threading.RLock())
    def turn(self,owner,sid,message,request_id):
        if DISTRESS.search(message):
            # Give immediate support without waiting for a provider, database,
            # profile lock, or session lookup. No notification is implied.
            return {'reply':DISTRESS_REPLY,'citations':[],'move':'human_help',
                    'provider_status':'not_called','validation_error':None,
                    'verification':'not_assessed','format_repaired':False,'repair_reason':None,
                    'dataset_id':None,'latency_ms':0,'retrieval':{'hits':0,'ids':[]},
                    'human_review_status':'pending','persistence':'not_saved_urgent'}
        with self.repo.owner_guard(owner), self.session_lock(sid):return self._turn(owner,sid,message,request_id)
    def _turn(self,owner,sid,message,request_id):
        start=time.monotonic();session=self.repo.session(sid,owner);state=session['state'];scope=Scope(**session['scope'])
        history=self.repo.history(sid)
        message=redact(message.strip())
        prior=next((t for t in history if t['request_id']==request_id),None)
        if prior:
            if prior['user_text']!=message:raise ValueError('Request id already used for a different message')
            return prior['result']
        if len(history)>=500:raise ValueError('Start a new conversation to keep this session manageable')
        adapter=self.registry.knowledge(session['dataset']);passages=[];citations=[];move='diagnostic';status='not_called';error=None;repaired=False;repair_reason=None
        recent=[]
        for t in history[-6:]:recent.extend([{'role':'user','text':t['user_text']},{'role':'assistant','text':t['result']['reply']}])
        assessment=self.repo.active_assessment(sid,owner) or self.repo.open_check(owner)
        if DISTRESS.search(message):
            reply=DISTRESS_REPLY;move='human_help'
        elif assessment:
            reply="Your check is active. Please answer in the practice panel; I haven't checked this message.";move='assessment_isolation'
        elif ACCESS.search(message):
            reply='I can help with the textbook, but a chat message cannot change access or reveal private material. Which concept would you like to explore?';move='access_boundary'
        elif re.fullmatch(r'(hi|hello|hey|thanks|thank you|bye)[!. ]*',message,re.I):
            reply='We can take this one step at a time. Which idea would you like to explore?';move='social'
        elif re.search(r'(?i)\b(?:today.s weather|current price|latest news|stock price|live score|uploaded image|attached diagram|diagram i sent)\b',message):
            reply="I can work from the textbook text here, but I don't have live information or an attached image to inspect. Which written detail can we work through?";move='unsupported_input'
        elif discovery_question(message):
            reply=navigation_reply(adapter,scope);move='topic_navigation'
        else:
            uncertain=bool(SMALL.search(message));analogy=bool(re.search(r'\b(analogy|everyday example|simple example)\b',message,re.I))
            followup=uncertain or analogy or bool(re.search(r'(?i)\b(simpler|say that again|why that|what do you mean|explain again|why is that)\b',message))
            correction=re.search(r'(?i)\b(?:i meant|i mean|instead explain|switch to|new topic[: ]+)\s*(.+)',message)
            new_topic=bool(re.match(r'(?i)^(?:explain|what (?:is|are)|how (?:does|do|is)|why (?:does|do|is|are)|tell me about)\b',message)) and not followup
            new_topic=new_topic or bool(broad_topic(adapter,message,scope))
            if correction:
                state.update(focus=correction[1],stuck=0,active_problem=False);move='acknowledge_correction'
            elif not state['focus'] or new_topic:
                state.update(focus=message,stuck=0,active_problem=False)
            else:move='connect_to_recent_reasoning'
            if uncertain:
                state['stuck']+=1;move=['break_into_one_step','concrete_analogy','check_prerequisite'][min(2,state['stuck']-1)]
            if analogy:move='concrete_analogy'
            active=bool(re.search(r'(?i)\b(solve|calculate|check my answer|give me the answer)\b|=',message))
            if scope.subject.casefold()=='mathematics' and (re.search(r'(?i)\b(?:my answer|i got)\b',message) or
                (re.search(r'\d',message) and re.search(r'(?i)\b(?:correct|right|check)\b',message))):active=True
            if active:state['active_problem']=True
            passages=adapter.search(state['focus'],scope,limit=3)
            if not passages:
                reply=navigation_reply(adapter,scope,missing=True);move='missing_evidence'
            elif state['active_problem']:
                reply="Let's keep the final answer for you to find. You can use checked practice for supported maths questions. What quantities are given, and what is your first step?";move='active_problem_coaching'
            elif self.language is None:
                reply,citations=self.fallback(passages,state,recent);status='offline_source_fallback'
            else:
                context={'request_id':request_id,'class':scope.grade,'subject':scope.subject,'focus':state['focus'],
                  'move':move,'latest_message':message,'recent_conversation':recent,'answer_verification':'not_assessed',
                  'excerpts':[{'id':p['id'],'text':p['text'],'kind':p['kind'],'pdf_page':p['page'],'human_review_status':p['human_review_status']} for p in passages]}
                try:
                    def generate_checked(instructions):
                        raw=self.language.generate(instructions,context).strip()
                        if raw.startswith('```') and raw.endswith('```'):raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw)
                        reply,citations=validate_reply(json.loads(raw),passages,recent)
                        if scope.subject.casefold() in ('science','chemistry') and unsafe_chemical_guidance(reply):
                            raise ValueError('unsafe_chemical_identification')
                        if scope.subject.casefold()=='mathematics':
                            if any(p['id'].endswith(':qe01') for p in passages):
                                defining=re.search(r'quadratic(?: equations?| polynomials?| expressions?)? (?:is|are|means|has|have|if|when)|(?:polynomial|equation|expression) is quadratic|making it a quadratic',reply,re.I)
                                degree=re.search(r'highest.{0,45}(?:two|2|squared)|degree.{0,12}(?:two|2|second)',reply,re.I)
                                if defining and not degree:raise ValueError('missing_quadratic_qualifier')
                            if re.search(r'\b(graph|parabola|x.axis|U.shaped)\b',reply,re.I) and not any(re.search(r'\b(graph|parabola|x.axis)\b',p['text'],re.I) for p in passages):
                                raise ValueError('unsupported_graph_fact')
                        return reply,citations
                    try:reply,citations=generate_checked(PROMPT)
                    except ValueError as first:
                        # One explicit format repair; unknown citations, grading and safety failures are not retried.
                        if str(first) not in {'response_length','one_focused_question','self_report_instead_of_reasoning','repeated_question'}:raise
                        repair_reason=str(first)
                        reply,citations=generate_checked(PROMPT+'\nA previous attempt failed the '+repair_reason+' check. Write under 40 words with one new, simple concept question. Retain source qualifiers.')
                        repaired=True
                    status='live_accepted'
                except Exception as exc:
                    safe={'response_schema','response_length','one_focused_question','citations_schema','unknown_or_missing_citation','unverified_grading_or_answer','repeated_question','self_report_instead_of_reasoning','missing_quadratic_qualifier','unsupported_graph_fact','unsafe_chemical_identification'}
                    error=str(exc) if type(exc) is ValueError and str(exc) in safe else type(exc).__name__
                    reply,citations=self.fallback(passages,state,recent);status='provider_failed_source_fallback'
        sources=[self.citation(p) for p in passages if p['id'] in citations]
        state['last_passages']=[p['id'] for p in passages]
        result={'reply':reply,'citations':sources,'move':move,'provider_status':status,'validation_error':error,
          'verification':'not_assessed','format_repaired':repaired,'repair_reason':repair_reason,'dataset_id':session['dataset'],'latency_ms':round((time.monotonic()-start)*1000),
          'retrieval':{'hits':len(passages),'ids':[p['id'] for p in passages]},'human_review_status':'pending','reference_bundle':getattr(adapter,'reference_bundle',None)}
        self.repo.save_turn(sid,request_id,message,result,state)
        if sources:
            p=next(p for p in passages if p['id']==sources[0]['id'])
            node=p.get('concept_id') or (p['id'].split(':',1)[1] if p['id'].startswith('normalized:') else f"reading:{p['book']}:{p['unit_file_index']}")
            self.repo.observe(owner,sid,node,'explored',{'dataset':session['dataset'],'passage_id':p['id']})
        return result
    @staticmethod
    def citation(p):
        return {k:p[k] for k in ('id','title','source_id','source_sha256','source_url','page','kind','human_review_status')}
    @staticmethod
    def fallback(passages,state,recent):
        p=passages[0]
        # Prefer a short safe sentence; avoid practical chemical-identification cues in recovery text.
        options=[(candidate,sentence) for candidate in passages for sentence in re.split(r'(?<=[.!])\s+',candidate['text'])
                 if len(sentence.split())>=6 and not re.search(r'\b(tast\w*|smell\w*|swallow\w*|ingest\w*)\b',sentence,re.I)]
        if options:p,fact=next(((candidate,sentence) for candidate,sentence in options if len(sentence.split())<=37),options[0])
        else:fact='We can inspect the cited passage together and begin with one small detail.'
        if len(fact.split())>37:fact=' '.join(fact.split()[:34])+'â€¦'
        prompts=['Which part of this idea would you like to examine first?',
                 'Which word in this passage should we unpack together?',
                 'What is one detail you can pick out from this passage?',
                 'Which simpler idea would help you make a start?']
        question=prompts[min(state['stuck'],3)]
        from ncert_pipeline.dialogue import repeated
        if repeated(fact+' '+question,recent):question=next((q for q in prompts if not repeated(fact+' '+q,recent)),prompts[-1])
        return fact+' '+question,[p['id']]
