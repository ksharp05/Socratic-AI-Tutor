"""Fault-injected learner UI with real local API state; synthetic data only."""
from test_product_student_ui import learner_ui,choose_chapter,send
from tutor import guards
from tutor.toolbus import ToolCallError


def publish_quiz(tutor):
    proposal=tutor.propose_set('qe04',mode='quiz')
    tutor.decide(proposal['set_id'],'approve','synthetic-test-fixture-only')


def button(ui,label):return next(b for b in ui.button if b.label==label)


def test_quiz_can_be_left_without_losing_the_session_or_awarding_a_score(learner_ui):
    ui,client,tutor,sent=learner_ui;publish_quiz(tutor)
    send(ui,'start a quiz');sid=ui.session_state['session_id']
    assert ui.session_state['quiz_active'] and button(ui,'New session').disabled
    assert next(r for r in ui.radio if r.label=='Mode').disabled
    send(ui,'Please give a hint.')
    assert 'no hints' in ui.session_state['messages'][-1]['content']
    button(ui,'Leave quiz without scoring').click().run(timeout=30)
    assert not ui.exception and not ui.session_state['quiz_active']
    assert not button(ui,'New session').disabled
    assert tutor.conn.execute('SELECT count(*) FROM applied_quizzes').fetchone()[0]==0
    assert tutor.conn.execute('SELECT count(*) FROM mastery').fetchone()[0]==0
    assert tutor.graph.get_state({'configurable':{'thread_id':sid}}).values['quiz'] is None
    assert 'No score' in ui.session_state['messages'][-1]['content']


def test_missing_browser_session_restores_only_the_owned_active_quiz(learner_ui):
    ui,client,tutor,sent=learner_ui;publish_quiz(tutor)
    send(ui,'start a quiz');sid=ui.session_state['session_id']
    for key in ['session_id','messages','quiz_active','last_result']:
        del ui.session_state[key]
    ui.session_state['active_checked']=False
    ui.run(timeout=30)
    assert not ui.exception and ui.session_state['session_id']==sid
    assert ui.session_state['quiz_active'] and button(ui,'New session').disabled
    assert len(sent)==1


def test_interrupted_turn_locks_new_session_until_recovery_without_replay(learner_ui,monkeypatch):
    ui,client,tutor,sent=learner_ui
    choose_chapter(ui,'arithmetic_progressions')
    original=tutor.turn
    def interrupted(session_id,learner_id,text,mode='practice',chapter=None):
        screen=guards.screen_input(text)
        tutor.graph.invoke({'incoming':screen['text'],'screen':screen,
            'session':{'session_id':session_id,'learner_id':learner_id,'mode':mode,'chapter':chapter or 'quadratic_equations'}},
            {'configurable':{'thread_id':session_id}},interrupt_after=['planner'])
        raise ToolCallError('BUSY','Synthetic process interruption after planning')
    monkeypatch.setattr(tutor,'turn',interrupted)
    send(ui,'What is the common difference?')
    assert ui.session_state['interrupted'] and button(ui,'New session').disabled
    assert ui.chat_input[0].disabled and len(sent)==1
    monkeypatch.setattr(tutor,'turn',original)
    button(ui,'Resume interrupted turn').click().run(timeout=30)
    assert not ui.exception and not ui.session_state['interrupted']
    assert not button(ui,'New session').disabled and len(sent)==1
    assert [m['role'] for m in ui.session_state['messages']]==['student','tutor']
    assert 'fixed change' in ui.session_state['messages'][-1]['content']
