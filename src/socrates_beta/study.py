from __future__ import annotations
import hashlib,json,time
from dataclasses import asdict
from .ports import Scope


class StudyService:
    def __init__(self,repo,registry):self.repo,self.registry=repo,registry

    def _visible_observations(self,owner):
        observations=self.repo.observations(owner)
        assessments=self.repo.assessments(owner)
        by_session={}
        for assessment in assessments:
            by_session.setdefault(assessment['session_id'],[]).append(assessment)
        withheld_ids=set()
        windows={}
        for sid, records in by_session.items():
            for index, assessment in enumerate(records):
                state=assessment['state']
                if (assessment['mode'] not in ('quiz','diagnostic') or
                    (state.get('complete') and not state.get('left_early') and not state.get('approval_revoked'))):
                    continue
                withheld_ids.add(assessment['id'])
                end=records[index+1]['created'] if index+1<len(records) else float('inf')
                windows.setdefault(sid,[]).append((assessment['created'],end,assessment['mode']))
        def visible(obs):
            value=obs['value']
            if obs['kind']!='checked_answer' or not isinstance(value,dict):return True
            if value.get('assessment_id'):
                return value['assessment_id'] not in withheld_ids
            # Older observations lack assessment IDs. Bound them to their
            # session and assessment time window, without deleting source data.
            return not any(start<=obs['created']<end and value.get('mode')==mode
                           for start,end,mode in windows.get(obs['session_id'],[]))
        return [obs for obs in observations if visible(obs)]

    @staticmethod
    def _relates(obs,node_id):
        if obs['node']==node_id:return True
        if obs['kind']!='checked_answer' or not isinstance(obs['value'],dict):return False
        concepts=obs['value'].get('concept_ids',[])
        return isinstance(concepts,list) and node_id in concepts

    def map(self,owner,scope,dataset=None):
        with self.repo.owner_guard(owner):return self._map(owner,scope,dataset)

    def _map(self,owner,scope,dataset=None):
        k=self.registry.knowledge(dataset);nodes=k.nodes(scope);observations=self._visible_observations(owner)
        sessions={s['id']:s for s in self.repo.sessions(owner)}
        for n in nodes:
            obs=[o for o in observations if self._relates(o,n['id']) and sessions.get(o['session_id'],{}).get('dataset')==k.dataset_id]
            correct={o['value']['question_id'] for o in obs if o['kind']=='checked_answer' and o['value']['status']=='correct'}
            wrong=sum(o['kind']=='checked_answer' and o['value']['status']=='incorrect' for o in obs)
            n.update(explored=sum(o['kind']=='explored' for o in obs),checked_items=len(correct),misses=wrong,
              status='answers_checked' if correct else 'exploring' if obs else 'not_started')
        return {'dataset_id':k.dataset_id,'nodes':nodes,'mastery_measured':False}

    def plan(self,owner,scope,dataset=None,minutes=25):
        with self.repo.owner_guard(owner):
            snapshot=self._map(owner,scope,dataset)
            nodes=snapshot['nodes']
            by_id={n['id']:n for n in nodes}
            def rank(n):
                unmet=sum(p in by_id and not (by_id[p]['explored'] or by_id[p]['checked_items']) for p in n.get('prerequisites',[]))
                return (unmet>0,n['checked_items']>0,-n['misses'],n['explored']>0,n.get('unit_file_index') or 0,n['id'])
            ranked=sorted(nodes,key=rank)
            days=[]
            for i in range(5):
                selected=ranked[i%len(ranked)] if ranked else None
                days.append({'day':i+1,'minutes':minutes,'node':selected,
                  'tasks':['Read the cited idea and explain it in your own words.','Discuss one uncertainty with Socrates.',
                    'Use checked practice if available, then review a saved card.'] if selected else ['Choose a supported textbook topic first.']})
            fingerprint={'dataset_id':snapshot['dataset_id'],'scope':asdict(scope),'minutes':minutes,
                         'nodes':[{key:n.get(key) for key in ('id','explored','checked_items','misses','prerequisites')} for n in nodes]}
            revision=hashlib.sha256(json.dumps(fingerprint,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest()[:16]
            reason='Based on available topics, prerequisite order and recorded activity.'
            evidence={'kind':'available_topics'}
            if ranked and ranked[0]['misses']:
                selected=ranked[0]
                session_ids={s['id'] for s in self.repo.sessions(owner) if s['dataset']==snapshot['dataset_id']}
                missed=[o for o in self._visible_observations(owner) if o['session_id'] in session_ids
                        and self._relates(o,selected['id']) and o['kind']=='checked_answer'
                        and o['value'].get('status')=='incorrect']
                checks=sum(o['value'].get('mode') in ('quiz','diagnostic') for o in missed)
                if checks:
                    reason=f"In completed checks, {checks} answers to questions involving {selected['title']} did not match. Those questions may involve other concepts too."
                    evidence={'kind':'completed_check_misses','concept_id':selected['id'],'count':checks}
                else:
                    reason=f"In practice, {len(missed)} answers to questions involving {selected['title']} did not match. Those questions may involve other concepts too."
                    evidence={'kind':'practice_misses','concept_id':selected['id'],'count':len(missed)}
            return {'days':days,'basis':'Available topics, explored sources and observed checked answers; not predicted mastery.',
                    'revision':revision,'replan_reason':reason,'evidence':evidence}

    def dashboard(self,owner):
        with self.repo.owner_guard(owner):
            sessions=self.repo.sessions(owner);obs=self._visible_observations(owner);cards=self.repo.cards(owner)
            checked=[o for o in obs if o['kind']=='checked_answer']
            return {'sessions':len(sessions),'cards':len(cards),'due_cards':sum(c['due']<=time.time() for c in cards),
              'checked_answers':len(checked),'correct_answers':sum(o['value']['status']=='correct' for o in checked),
              'incorrect_answers':sum(o['value']['status']=='incorrect' for o in checked),'reasoning_assessed':False,
              'explored_passages':len({(o['value'].get('dataset'),o['value'].get('passage_id')) for o in obs if o['kind']=='explored'})}
