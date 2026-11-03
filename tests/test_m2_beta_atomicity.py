"""Offline assessment isolation and atomic persistence with synthetic answers."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from threading import Barrier, Event, Lock

import pytest
from socrates_beta.maths import AssessmentService
from socrates_beta.repository import Repository


class FakeMaths:
    def __init__(self):
        self.items = {f'q{i}': {'question_id':f'q{i}', 'problem':{'concept_ids':['qe04']}} for i in range(5)}
        self.calls = 0
        self.guard = Lock()
    def eligible(self, scope, concept=None): return list(self.items.values())
    def public_item(self, qid): return {'id':qid, 'prompt':'Synthetic question'}
    def grade(self, qid, text):
        with self.guard: self.calls += 1
        return {'status':'incorrect','correct':False,'scorable':True,'reasoning_evaluated':False}
    def hint(self, qid, stage): return 'Synthetic hint'


def make_session(repo, owner='synthetic-owner'):
    return repo.create_session(owner, 'synthetic-data',
        {'grade':10,'subject':'Mathematics','book':None,'unit':4}, 'Synthetic session')


def test_quiz_in_another_session_blocks_practice_grading_and_hints(tmp_path):
    repo=Repository(tmp_path/'beta.db'); maths=FakeMaths(); service=AssessmentService(repo,maths)
    first=make_session(repo); second=make_session(repo)
    practice=service.start(first,'practice')
    quiz=service.start(second,'quiz')
    with pytest.raises(ValueError,match='check'):
        service.submit(first['owner'],practice['id'],'x = 1','answer-0001')
    with pytest.raises(ValueError,match='check'):
        service.hint(first['owner'],practice['id'])
    assert maths.calls == 0
    assert not [o for o in repo.observations(first['owner']) if o['kind']=='checked_answer']
    assert not repo.assessment(quiz['id'],first['owner'])['state']['complete']


def test_duplicate_answer_is_scored_once_across_service_instances(tmp_path,monkeypatch):
    path=tmp_path/'beta.db'; first_repo=Repository(path); second_repo=Repository(path)
    maths=FakeMaths(); first=AssessmentService(first_repo,maths); second=AssessmentService(second_repo,maths)
    session=make_session(first_repo); active=first.start(session,'practice')
    entered,release=Event(),Event(); original=maths.grade
    def slow_once(qid,text):
        result=original(qid,text)
        if maths.calls == 1:
            entered.set()
            if not release.wait(10):raise RuntimeError('test did not release grading')
        return result
    monkeypatch.setattr(maths,'grade',slow_once)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            a=pool.submit(first.submit,session['owner'],active['id'],'x = 1','same-request')
            assert entered.wait(10)
            b=pool.submit(second.submit,session['owner'],active['id'],'x = 1','same-request')
            try:
                with pytest.raises(TimeoutError):b.result(timeout=.4)
            finally:release.set()
            assert a.result(timeout=10)==b.result(timeout=10)
        assert maths.calls == 1
        assert len([o for o in first_repo.observations(session['owner']) if o['kind']=='checked_answer']) == 1
    finally:release.set()


def test_failed_assessment_save_rolls_back_checked_observation(tmp_path,monkeypatch):
    repo=Repository(tmp_path/'beta.db');maths=FakeMaths();service=AssessmentService(repo,maths)
    session=make_session(repo);active=service.start(session,'practice')
    def fail_save(*args,**kwargs):raise RuntimeError('synthetic persistence failure')
    monkeypatch.setattr(repo,'save_assessment',fail_save)
    with pytest.raises(RuntimeError,match='synthetic persistence'):
        service.submit(session['owner'],active['id'],'x = 1','answer-0001')
    assert not [o for o in repo.observations(session['owner']) if o['kind']=='checked_answer']
    assert not repo.assessment(active['id'],session['owner'])['state']['submissions']


def test_concurrent_quiz_starts_across_instances_only_create_one(tmp_path,monkeypatch):
    path=tmp_path/'beta.db';r1=Repository(path);r2=Repository(path);maths=FakeMaths()
    one=AssessmentService(r1,maths);two=AssessmentService(r2,maths)
    first=make_session(r1);second=make_session(r1);both_read=Barrier(2)
    for repo in (r1,r2):
        original=repo.open_check
        def paused(owner,*args,_original=original,**kwargs):
            result=_original(owner,*args,**kwargs)
            if not args and 'conn' not in kwargs:both_read.wait(timeout=5)
            return result
        monkeypatch.setattr(repo,'open_check',paused)
    def start(service,session):
        try:return service.start(session,'quiz')
        except ValueError:return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda pair:start(*pair),[(one,first),(two,second)]))
    assert sum(r is not None for r in results)==1
    with r1.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM assessments').fetchone()[0]==1


def test_quiz_results_are_hidden_until_completion_and_written_once(tmp_path):
    repo=Repository(tmp_path/'beta.db'); maths=FakeMaths(); service=AssessmentService(repo,maths)
    session=make_session(repo); assessment=service.start(session,'quiz')
    for i in range(5):
        result=service.submit(session['owner'],assessment['id'],'x = 1',f'answer-{i:04}')
        if i<4:
            assert not result['assessment']['complete']
            assert not [o for o in repo.observations(session['owner']) if o['kind']=='checked_answer']
    assert result['assessment']['complete']
    assert len([o for o in repo.observations(session['owner']) if o['kind']=='checked_answer'])==5
    assert service.submit(session['owner'],assessment['id'],'x = 1','answer-0004')==result
    assert len([o for o in repo.observations(session['owner']) if o['kind']=='checked_answer'])==5


def test_quiz_start_waits_for_other_session_chat_across_service_instances(tmp_path):
    import json
    from socrates_beta.dialogue import DialogueService

    path=tmp_path/'beta.db'; r1=Repository(path); r2=Repository(path)
    chat_session=make_session(r1); quiz_session=make_session(r1)
    entered,release=Event(),Event()
    passage={'id':'fixture:math','title':'Quadratic','text':'A quadratic has a highest power of two.',
        'source_id':'fixture','source_sha256':'a'*64,'source_url':'https://example.org/fixture',
        'page':1,'kind':'fixture','human_review_status':'pending','book':'fixture','unit_file_index':4}
    class Knowledge:
        def search(self,*args,**kwargs):return [passage]
    class Registry:
        def knowledge(self,*args):return Knowledge()
    class Language:
        def generate(self,*args):
            entered.set()
            if not release.wait(10):raise RuntimeError('test did not release chat')
            return json.dumps({'reply':'A quadratic has degree two. Which term gives the highest power?',
                               'citations':['fixture:math']})
    dialogue=DialogueService(r1,Registry(),Language()); assessments=AssessmentService(r2,FakeMaths())
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            chat=pool.submit(dialogue.turn,chat_session['owner'],chat_session['id'],'What is a quadratic?','chat-0001')
            assert entered.wait(10)
            quiz=pool.submit(assessments.start,quiz_session,'quiz')
            try:
                with pytest.raises(TimeoutError):quiz.result(timeout=.4)
            finally:release.set()
            assert chat.result(timeout=10)['reply']
            assert quiz.result(timeout=10)['mode']=='quiz'
        assert dialogue.turn(chat_session['owner'],chat_session['id'],'Explain it again','chat-0002')['move']=='assessment_isolation'
    finally:release.set()


def test_practice_resumes_after_other_session_quiz_is_left(tmp_path):
    repo=Repository(tmp_path/'beta.db'); maths=FakeMaths(); service=AssessmentService(repo,maths)
    one=make_session(repo);two=make_session(repo)
    practice=service.start(one,'practice');quiz=service.start(two,'quiz')
    service.leave(one['owner'],quiz['id'])
    assert service.hint(one['owner'],practice['id'])['stage']==1
    assert service.submit(one['owner'],practice['id'],'x = 1','answer-0001')['status']=='incorrect'


def test_quiz_completion_failure_rolls_back_all_deferred_observations(tmp_path,monkeypatch):
    repo=Repository(tmp_path/'beta.db');maths=FakeMaths();service=AssessmentService(repo,maths)
    session=make_session(repo);quiz=service.start(session,'quiz')
    for i in range(4):service.submit(session['owner'],quiz['id'],'x = 1',f'answer-{i:04}')
    original=repo.observe;calls=0
    def fail_during_flush(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==3:raise RuntimeError('synthetic observation failure')
        return original(*args,**kwargs)
    monkeypatch.setattr(repo,'observe',fail_during_flush)
    with pytest.raises(RuntimeError,match='synthetic observation'):
        service.submit(session['owner'],quiz['id'],'x = 1','answer-0004')
    assert not repo.observations(session['owner'])
    state=repo.assessment(quiz['id'],session['owner'])['state']
    assert state['index']==4 and not state['complete']
    monkeypatch.setattr(repo,'observe',original)
    result=service.submit(session['owner'],quiz['id'],'x = 1','answer-0004')
    assert result['assessment']['complete']
    assert len(repo.observations(session['owner']))==5


def test_legacy_partial_quiz_is_hidden_and_not_double_recorded(tmp_path):
    from socrates_beta.study import StudyService

    repo=Repository(tmp_path/'beta.db');maths=FakeMaths();service=AssessmentService(repo,maths)
    session=make_session(repo);quiz=service.start(session,'quiz')
    record=repo.assessment(quiz['id'],session['owner']);state=record['state'];qid=state['queue'][0]
    # Represents an older saved quiz, whose per-answer observation was already written.
    state['submissions'].append({'request_id':'legacy-000','question_id':qid,'grade':
        {'status':'incorrect','correct':False,'scorable':True},'counted':True})
    state['used'].append(qid);state['index']=1
    repo.observe(session['owner'],session['id'],'qe04','checked_answer',
                 {'status':'incorrect','question_id':qid,'mode':'quiz'})
    repo.save_assessment(record)
    assert StudyService(repo,None).dashboard(session['owner'])['checked_answers']==0
    for i in range(1,5):service.submit(session['owner'],quiz['id'],'x = 1',f'answer-{i:04}')
    assert StudyService(repo,None).dashboard(session['owner'])['checked_answers']==5
    assert len(repo.observations(session['owner']))==5


def test_owner_guard_is_shared_with_another_process(tmp_path):
    import os,subprocess,sys,time

    repo=Repository(tmp_path/'beta.db');session=make_session(repo)
    ready=tmp_path/'ready';release=tmp_path/'release'
    script=('import sys,time\nfrom pathlib import Path\nfrom socrates_beta.repository import Repository\n'
        'repo=Repository(Path(sys.argv[1]));ready=Path(sys.argv[2]);release=Path(sys.argv[3])\n'
        'with repo.owner_guard(sys.argv[4]):\n ready.touch()\n deadline=time.monotonic()+15\n'
        ' while not release.exists() and time.monotonic()<deadline:time.sleep(.02)\n'
        ' if not release.exists():raise RuntimeError("release timed out")\n')
    child=subprocess.Popen([sys.executable,'-c',script,str(repo.path),str(ready),str(release),session['owner']],env=os.environ.copy())
    try:
        deadline=time.monotonic()+10
        while not ready.exists() and child.poll() is None and time.monotonic()<deadline:time.sleep(.02)
        assert ready.exists()
        with ThreadPoolExecutor(max_workers=1) as pool:
            result=pool.submit(AssessmentService(repo,FakeMaths()).start,session,'quiz')
            try:
                with pytest.raises(TimeoutError):result.result(timeout=.4)
            finally:release.touch()
            assert result.result(timeout=10)['mode']=='quiz'
        assert child.wait(timeout=10)==0
    finally:
        release.touch()
        if child.poll() is None:child.terminate();child.wait(timeout=10)


def test_distress_response_is_not_delayed_by_another_profile_operation(tmp_path):
    from socrates_beta.dialogue import DialogueService

    repo=Repository(tmp_path/'beta.db');session=make_session(repo)
    dialogue=DialogueService(repo,registry=None,language=None)
    entered,release=Event(),Event()
    def hold_profile():
        with repo.owner_guard(session['owner']):
            entered.set()
            if not release.wait(10):raise RuntimeError('test did not release lock')
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            held=pool.submit(hold_profile)
            assert entered.wait(10)
            urgent=pool.submit(dialogue.turn,session['owner'],session['id'],'I want to die','urgent-0001')
            try:
                response=urgent.result(timeout=1)
                assert response['move']=='human_help' and 'trusted adult' in response['reply'].lower()
            finally:release.set()
            held.result(timeout=10)
    finally:release.set()


def test_distress_response_does_not_depend_on_the_knowledge_registry(tmp_path):
    from socrates_beta.dialogue import DialogueService

    repo=Repository(tmp_path/'beta.db');session=make_session(repo)
    response=DialogueService(repo,registry=None,language=None).turn(
        session['owner'],session['id'],'I want to die','urgent-0002')
    assert response['move']=='human_help' and 'trusted adult' in response['reply'].lower()
    assert response['persistence']=='not_saved_urgent' and not repo.history(session['id'])


def test_leaving_quiz_early_does_not_reveal_or_record_partial_score(tmp_path):
    repo=Repository(tmp_path/'beta.db');maths=FakeMaths();service=AssessmentService(repo,maths)
    session=make_session(repo);quiz=service.start(session,'quiz')
    first=service.submit(session['owner'],quiz['id'],'x = 1','answer-0000')
    assert first['status']=='recorded'
    left=service.leave(session['owner'],quiz['id'])
    assert left['complete'] and left['left_early'] and 'summary' not in left
    assert not repo.observations(session['owner'])
    with pytest.raises(ValueError,match='left'):
        service.submit(session['owner'],quiz['id'],'x = 1','answer-0000')


def test_legacy_abandoned_quiz_results_stay_hidden_without_deleting_them(tmp_path):
    from socrates_beta.study import StudyService

    repo=Repository(tmp_path/'beta.db');maths=FakeMaths();service=AssessmentService(repo,maths)
    session=make_session(repo);quiz=service.start(session,'quiz')
    record=repo.assessment(quiz['id'],session['owner']);state=record['state'];qid=state['queue'][0]
    state['submissions'].append({'request_id':'legacy-000','question_id':qid,'grade':
        {'status':'incorrect','correct':False,'scorable':True},'counted':True})
    state['used'].append(qid);state['index']=1
    repo.observe(session['owner'],session['id'],'qe04','checked_answer',
                 {'status':'incorrect','question_id':qid,'mode':'quiz'})
    repo.save_assessment(record)
    assert StudyService(repo,None).dashboard(session['owner'])['checked_answers']==0
    service.leave(session['owner'],quiz['id'])
    assert StudyService(repo,None).dashboard(session['owner'])['checked_answers']==0
    assert len(repo.observations(session['owner']))==1  # retained, not exposed or deleted
    practice=service.start(session,'practice')
    service.submit(session['owner'],practice['id'],'x = 1','practice-0001')
    assert StudyService(repo,None).dashboard(session['owner'])['checked_answers']==1


def test_completed_quiz_cannot_be_reclassified_as_abandoned(tmp_path):
    from socrates_beta.study import StudyService

    repo=Repository(tmp_path/'beta.db');maths=FakeMaths();service=AssessmentService(repo,maths)
    session=make_session(repo);quiz=service.start(session,'quiz')
    for i in range(5):service.submit(session['owner'],quiz['id'],'x = 1',f'answer-{i:04}')
    assert StudyService(repo,None).dashboard(session['owner'])['checked_answers']==5
    with pytest.raises(ValueError,match='complete'):
        service.leave(session['owner'],quiz['id'])
    assert StudyService(repo,None).dashboard(session['owner'])['checked_answers']==5


def test_completed_quiz_replans_only_the_matching_browser_profile(tmp_path):
    from socrates_beta.ports import Scope
    from socrates_beta.study import StudyService

    class Knowledge:
        dataset_id='synthetic-data'
        def nodes(self,scope):
            return [{'id':'qe01','title':'Quadratic basics','prerequisites':[],'unit_file_index':4},
                    {'id':'qe04','title':'Factoring quadratics','prerequisites':[],'unit_file_index':4}]
    class Registry:
        def knowledge(self,dataset=None):return Knowledge()
    repo=Repository(tmp_path/'beta.db');maths=FakeMaths();service=AssessmentService(repo,maths)
    first=make_session(repo,'profile-a');second=make_session(repo,'profile-b')
    study=StudyService(repo,Registry());scope=Scope(10,'Mathematics',unit=4)
    before_a=study.plan(first['owner'],scope);before_b=study.plan(second['owner'],scope)
    assert before_a['days'][0]['node']['id']==before_b['days'][0]['node']['id']=='qe01'
    quiz=service.start(first,'quiz')
    for i in range(4):service.submit(first['owner'],quiz['id'],'x = 1',f'answer-{i:04}')
    assert study.plan(first['owner'],scope)['revision']==before_a['revision']
    service.submit(first['owner'],quiz['id'],'x = 1','answer-0004')
    after=study.plan(first['owner'],scope);other=study.plan(second['owner'],scope)
    assert after['days'][0]['node']['id']=='qe04' and after['revision']!=before_a['revision']
    assert 'completed' in after['replan_reason'].lower() and 'factoring' in after['replan_reason'].lower()
    assert other['revision']==before_b['revision'] and other['days'][0]['node']['id']=='qe01'


def test_multi_concept_quiz_informs_each_relevant_plan_without_double_counting(tmp_path):
    from socrates_beta.ports import Scope
    from socrates_beta.study import StudyService

    class Knowledge:
        dataset_id='synthetic-data'
        def nodes(self,scope):
            return [{'id':'qe01','title':'Quadratic basics','prerequisites':[],'unit_file_index':4},
                    {'id':'qe04','title':'Factoring quadratics','prerequisites':[],'unit_file_index':4}]
    class Registry:
        def knowledge(self,dataset=None):return Knowledge()
    repo=Repository(tmp_path/'beta.db');maths=FakeMaths()
    for item in maths.items.values():item['problem']['concept_ids']=['qe03','qe04']
    service=AssessmentService(repo,maths);session=make_session(repo)
    study=StudyService(repo,Registry());scope=Scope(10,'Mathematics',unit=4)
    assert study.plan(session['owner'],scope)['days'][0]['node']['id']=='qe01'
    quiz=service.start(session,'quiz')
    for i in range(5):service.submit(session['owner'],quiz['id'],'x = 1',f'answer-{i:04}')
    plan=study.plan(session['owner'],scope)
    assert plan['days'][0]['node']['id']=='qe04'
    assert plan['evidence']['count']==5 and 'involving' in plan['replan_reason'].lower()
    assert study.dashboard(session['owner'])['checked_answers']==5
