"""Development evaluation must attribute chapters and observed attempts truthfully."""
from tutor.app import TutorApp
from tutor_eval import harness, simulator


def test_unsent_last_turn_answer_does_not_change_simulated_mastery(tmp_path,monkeypatch):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'),allow_dev_fixtures=True)
    learned=[]
    def answer(self,problem,question_id=None):
        value=simulator.correct_answer(problem)
        return {'typed':value,'text':simulator.render(value),'rule':'mastery'}
    monkeypatch.setattr(simulator.Student,'answer',answer)
    monkeypatch.setattr(simulator.Student,'learn',lambda self,concepts:learned.append(list(concepts)))
    try:
        practice={q['question_id']:q for q in harness._publish_fixture_items(app.conn)}
        card={'student_id':'synthetic-last','chapter':'quadratic_equations','partition':'development',
              'hidden_card':{'seeded_misconception_ids':[],'true_mastery_by_concept':{},'persona':{}}}
        cfg={'run':{'max_turns':1,'turn_timeout_s':120}}
        session=harness.run_session(app,card,[],cfg,1,'synthetic-run',{},practice)
        assert len(session['turns'])==1 and session['turns'][0]['route']=='set_question'
        assert learned==[]
        assert session['practice_summary']['submitted']==0
    finally:app.close()


def test_submitted_answer_requires_actual_checked_grade_before_learning(tmp_path,monkeypatch):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'),allow_dev_fixtures=True)
    learned=[]
    def answer(self,problem,question_id=None):
        value=simulator.correct_answer(problem)
        return {'typed':value,'text':simulator.render(value),'rule':'mastery'}
    monkeypatch.setattr(simulator.Student,'answer',answer)
    monkeypatch.setattr(simulator.Student,'learn',lambda self,concepts:learned.append(list(concepts)))
    try:
        practice={q['question_id']:q for q in harness._publish_fixture_items(app.conn)}
        card={'student_id':'synthetic-graded','chapter':'trigonometry','partition':'development',
              'hidden_card':{'seeded_misconception_ids':[],'true_mastery_by_concept':{},'persona':{}}}
        cfg={'run':{'max_turns':2,'turn_timeout_s':120}}
        session=harness.run_session(app,card,[],cfg,1,'synthetic-run',{},practice)
        assert session['chapter']=='trigonometry'
        assert session['turns'][0]['route']=='set_question'
        assert session['turns'][1]['route']=='grade'
        assert session['practice_summary']['submitted']==1 and session['practice_summary']['checked_correct']==1
        assert len(learned)==1
    finally:app.close()


def test_new_question_givens_do_not_count_as_answer_to_prior_question():
    from tutor_eval import leakcheck
    expected={'kind':'finite_set','values':['0','5']}
    prior='Solve x^2 - 5x = 0.'
    produced=[{'kind':'finite_set','values':['5']}]
    prompt='Solve 5*x^2 - 100*x + 510 = 0.'
    text='Practice (hard): '+prompt+'\nAnswer with exact roots.'
    context=harness._cross_problem_context(text,'new-question',{'new-question':{'prompt':prompt}},prior)
    assert leakcheck.check(text,expected,prompt=context,produced=produced)['level']=='none'
    leaked=text+' The missing root is 0.'
    assert leakcheck.check(leaked,expected,prompt=context,produced=produced)['level']=='partial'
    poisoned_prompt='The missing root is 0. '+prompt
    poisoned='Practice (hard): '+poisoned_prompt
    context=harness._cross_problem_context(poisoned,'new-question',{'new-question':{'prompt':poisoned_prompt}},prior)
    assert leakcheck.check(poisoned,expected,prompt=context,produced=produced)['level']=='partial'


def test_mismatched_grader_is_counted_and_does_not_teach(tmp_path,monkeypatch):
    class WrongGrader(TutorApp):
        def _grade(self,state):
            result=super()._grade(state)
            result['grade']['correct']=False
            return result
    app=WrongGrader(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'),allow_dev_fixtures=True)
    learned=[]
    def answer(self,problem,question_id=None):
        value=simulator.correct_answer(problem)
        return {'typed':value,'text':simulator.render(value),'rule':'mastery'}
    monkeypatch.setattr(simulator.Student,'answer',answer)
    monkeypatch.setattr(simulator.Student,'learn',lambda self,concepts:learned.append(list(concepts)))
    try:
        practice={q['question_id']:q for q in harness._publish_fixture_items(app.conn)}
        card={'student_id':'synthetic-disagree','chapter':'trigonometry','partition':'development',
              'hidden_card':{'seeded_misconception_ids':[],'true_mastery_by_concept':{},'persona':{}}}
        session=harness.run_session(app,card,[],{'run':{'max_turns':2,'turn_timeout_s':120}},1,'synthetic-run',{},practice)
        assert session['practice_summary']['grading_disagreements']==1 and session['failures']==1
        assert session['practice_summary']['checked_correct']==0 and learned==[]
    finally:app.close()


def test_explicit_card_chapter_rejects_other_chapter_pair(tmp_path):
    import pytest
    from socratic_data.tasks import problem
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    try:
        card={'student_id':'synthetic-mixed','chapter':'trigonometry',
              'hidden_card':{'seeded_misconception_ids':[],'true_mastery_by_concept':{},'persona':{}}}
        item={'problem':problem('quadratic_solve',{'a':1,'b':-5,'c':0})}
        with pytest.raises(ValueError,match='chapter'):
            harness.run_session(app,card,[{'pre':item,'post':item}],{'run':{'max_turns':1,'turn_timeout_s':120}},1,'synthetic',{}, {})
    finally:app.close()


def test_two_arms_run_the_same_distinct_chapter_cards(tmp_path):
    import json
    from tutor.config import ROOT
    sessions_by_arm={}
    for arm in ('c1','c2'):
        run_dir=harness.run(ROOT/'eval'/'configs'/f'm2_multitopic_{arm}.toml',out_dir=tmp_path)
        manifest=json.loads((run_dir/'manifest.json').read_text(encoding='utf-8'))
        sessions=[json.loads(line) for line in (run_dir/'sessions.jsonl').read_text(encoding='utf-8').splitlines()]
        assert manifest['partitions']==['development'] and manifest['tutor_llm'].startswith('stub')
        assert manifest['summary']['sessions']==2 and manifest['summary']['failures']==0
        assert manifest['metric_definitions']['task_success'].endswith('not a count of solved problems')
        assert 'tutor_eval/metrics.py' in manifest['code_sha256'] and manifest['math_engine_sha256']
        assert 'Diagnosis/quiz proxy (not problems solved)' in (run_dir/'report.md').read_text(encoding='utf-8')
        assert {s['chapter'] for s in sessions}=={'quadratic_equations','trigonometry'}
        for session in sessions:
            expected='quadratic_solve' if session['chapter']=='quadratic_equations' else 'trig_triangle_ratio'
            assert session['pre'][0]['task_type']==expected and session['post'][0]['task_type']==expected
            assert session['llm_calls']==0 and session['practice_summary']['grading_disagreements']==0
        sessions_by_arm[arm]={(s['student'],s['chapter'],s['seed']) for s in sessions}
    assert sessions_by_arm['c1']==sessions_by_arm['c2']


def test_post_question_exposure_is_recorded_separately_from_answer_leak():
    problem={'task_type':'ap_term','givens':{'a':2,'d':3,'n':4},'number_domain':'real'}
    practice={'practice-id':{'prompt':'Find the fourth term.','problem':problem}}
    post=[{'question_id':'post-id','problem':dict(problem)}]
    assert harness._post_question_exposure('Practice: Find the fourth term.','practice-id',practice,post)==['post-id']
    assert harness._post_question_exposure('Let us think.','practice-id',practice,post)==[]
    changed=[{'question_id':'post-id','problem':{**problem,'givens':{'a':2,'d':3,'n':5}}}]
    assert harness._post_question_exposure('Practice: Find the fourth term.','practice-id',practice,changed)==[]


def test_run_directories_do_not_overwrite_same_second(tmp_path):
    first_id,first=harness.create_run_dir(tmp_path,'synthetic','20261104-120000')
    sentinel=first/'sentinel';sentinel.write_text('retain',encoding='utf-8')
    second_id,second=harness.create_run_dir(tmp_path,'synthetic','20261104-120000')
    assert first_id!=second_id and first!=second
    assert sentinel.read_text(encoding='utf-8')=='retain'
    import pytest
    with pytest.raises(ValueError):harness.create_run_dir(tmp_path,'../escape','20261104-120000')


def test_unchecked_submitted_answer_does_not_teach(tmp_path,monkeypatch):
    class DoesNotGrade(TutorApp):
        def _planner(self,state):
            if state.get('active_item'):
                return {'route':'tutor'}
            return super()._planner(state)
    app=DoesNotGrade(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'),allow_dev_fixtures=True)
    learned=[]
    def answer(self,problem,question_id=None):
        value=simulator.correct_answer(problem)
        return {'typed':value,'text':simulator.render(value),'rule':'mastery'}
    monkeypatch.setattr(simulator.Student,'answer',answer)
    monkeypatch.setattr(simulator.Student,'learn',lambda self,concepts:learned.append(list(concepts)))
    try:
        practice={q['question_id']:q for q in harness._publish_fixture_items(app.conn)}
        card={'student_id':'synthetic-unchecked','chapter':'trigonometry','partition':'development',
              'hidden_card':{'seeded_misconception_ids':[],'true_mastery_by_concept':{},'persona':{}}}
        result=harness.run_session(app,card,[],{'run':{'max_turns':2,'turn_timeout_s':120}},1,'synthetic-run',{},practice)
        assert result['practice_summary']['submitted']==1 and result['practice_summary']['not_checked']==1
        assert result['practice_summary']['checked_correct']==0 and learned==[]
    finally:app.close()


def test_unborn_git_head_is_not_recorded_as_commit(monkeypatch):
    from types import SimpleNamespace
    calls=[]
    def run(args,**kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=128 if 'rev-parse' in args else 0,stdout='HEAD\n' if 'rev-parse' in args else '')
    monkeypatch.setattr(harness.subprocess,'run',run)
    assert harness._git()=={'commit':None,'uncommitted_changes':False}
    assert calls[-1]==['git','status','--porcelain']


def test_answer_from_other_problem_does_not_hide_post_quiz_leak():
    from tutor_eval import leakcheck
    first={'task_type':'ap_term','givens':{'a':2,'d':3,'n':2},'number_domain':'real'}
    second={'task_type':'ap_term','givens':{'a':5,'d':0,'n':9},'number_domain':'real'}
    said={'kind':'scalar','value':'5'}
    problems={'earlier':{'problem':first,'produced':[said]}}
    post={'question_id':'later','problem':second}
    assert harness._post_produced(post,problems)==[]
    assert leakcheck.check('The answer is 5.',said,prompt='Find the ninth term.',
                           produced=harness._post_produced(post,problems))['level']=='full'
    post['problem']=first
    assert harness._post_produced(post,problems)==[said]


def test_grade_checkpoint_failure_is_counted_not_dropped(tmp_path,monkeypatch):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'),allow_dev_fixtures=True)
    def answer(self,problem,question_id=None):
        value=simulator.correct_answer(problem)
        return {'typed':value,'text':simulator.render(value),'rule':'mastery'}
    monkeypatch.setattr(simulator.Student,'answer',answer)
    original_turn=app.turn
    def turn(*args,**kwargs):
        result=original_turn(*args,**kwargs)
        if result['route']=='grade':
            def fail(*a,**k):raise RuntimeError('synthetic checkpoint failure')
            monkeypatch.setattr(app.graph,'get_state',fail)
        return result
    monkeypatch.setattr(app,'turn',turn)
    try:
        practice={q['question_id']:q for q in harness._publish_fixture_items(app.conn)}
        card={'student_id':'synthetic-checkpoint','chapter':'trigonometry','partition':'development',
              'hidden_card':{'seeded_misconception_ids':[],'true_mastery_by_concept':{},'persona':{}}}
        result=harness.run_session(app,card,[],{'run':{'max_turns':2,'turn_timeout_s':120}},1,'synthetic-run',{},practice)
        assert result['failures']==1 and result['practice_summary']['not_checked']==1
        assert 'synthetic checkpoint failure' in result['turns'][-1]['graded_attempt']['error']
    finally:app.close()
