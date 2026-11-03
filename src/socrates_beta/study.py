from __future__ import annotations
import time
from .ports import Scope


class StudyService:
    def __init__(self,repo,registry):self.repo,self.registry=repo,registry
    def map(self,owner,scope,dataset=None):
        k=self.registry.knowledge(dataset);nodes=k.nodes(scope);observations=self.repo.observations(owner)
        sessions={s['id']:s for s in self.repo.sessions(owner)}
        for n in nodes:
            obs=[o for o in observations if o['node']==n['id'] and sessions.get(o['session_id'],{}).get('dataset')==k.dataset_id]
            correct={o['value']['question_id'] for o in obs if o['kind']=='checked_answer' and o['value']['status']=='correct'}
            wrong=sum(o['kind']=='checked_answer' and o['value']['status']=='incorrect' for o in obs)
            n.update(explored=sum(o['kind']=='explored' for o in obs),checked_items=len(correct),misses=wrong,
              status='answers_checked' if correct else 'exploring' if obs else 'not_started')
        return {'dataset_id':k.dataset_id,'nodes':nodes,'mastery_measured':False}
    def plan(self,owner,scope,dataset=None,minutes=25):
        nodes=self.map(owner,scope,dataset)['nodes']
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
        return {'days':days,'basis':'Available topics, explored sources and observed checked answers; not predicted mastery.'}
    def dashboard(self,owner):
        sessions=self.repo.sessions(owner);obs=self.repo.observations(owner);cards=self.repo.cards(owner)
        checked=[o for o in obs if o['kind']=='checked_answer']
        return {'sessions':len(sessions),'cards':len(cards),'due_cards':sum(c['due']<=time.time() for c in cards),
          'checked_answers':len(checked),'correct_answers':sum(o['value']['status']=='correct' for o in checked),
          'incorrect_answers':sum(o['value']['status']=='incorrect' for o in checked),'reasoning_assessed':False,
          'explored_passages':len({(o['value'].get('dataset'),o['value'].get('passage_id')) for o in obs if o['kind']=='explored'})}
