"""A reasoning reply is checked separately from the final ratio answer."""
import pytest
from tutor.triangle_reasoning import check_labels
from tutor.app import TutorApp
from tutor_eval.single_agent import SingleAgentTutor
from tutor.seed import seed_learner

P={'task_type':'trig_triangle_ratio','givens':{'opposite':17,'adjacent':144,'hypotenuse':145,'reference':'C','ratio':'sin'}}

@pytest.mark.parametrize(('text','status'),[
    ('Angle C, opposite 144, adjacent 17, hypotenuse 145','labels_correct'),
    ('I used C. Opposite side is 144, adjacent side is 17 and hypotenuse is 145.','labels_correct'),
    ('angle C opposite=144/1 adjacent=17 hypotenuse=145','labels_correct'),
    ('angle A, opposite 17, adjacent 144, hypotenuse 145','reference_mismatch'),
    ('angle C, opposite 17, adjacent 144, hypotenuse 145','labels_mismatch'),
    ('angle C, opposite 144','clarify'),
    ('angle A and angle C, opposite 144, adjacent 17, hypotenuse 145','clarify'),
    ('angle C, opposite 144, opposite 17, adjacent 17, hypotenuse 145','clarify'),
    ('angle C opposite 144/0 adjacent 17 hypotenuse 145','clarify'),
    ('angle C opposite 144.5 adjacent 17 hypotenuse 145','clarify'),
    ('angle C not opposite 144 adjacent 17 hypotenuse 145','clarify'),
    ('angle B and angle C opposite 144 adjacent 17 hypotenuse 145','clarify'),
    ('angle C opposite 144+1 adjacent 17 hypotenuse 145','clarify'),
    ('angle C opposite 144 cm adjacent 17 hypotenuse 145','clarify'),
    ('angle C opposite 144 or 17 adjacent 17 hypotenuse 145','clarify'),
    ('angle C opposite 144 inches adjacent 17 feet hypotenuse 145','clarify'),
    ('angle C opposite 144 adjacent 17 hypotenuse 145 but I chose different sides','clarify'),
])
def test_bounded_label_checks(text,status):
    assert check_labels(P,text)=={'status':status}


@pytest.mark.parametrize('cls',[TutorApp,SingleAgentTutor])
def test_reasoning_exchange_keeps_answer_open_without_numeric_grade(tmp_path,cls):
    app=cls(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    seed_learner(app.conn,'synthetic',{'alias':'Synthetic'})
    try:
        proposal=app.propose_set('tr01');app.decide(proposal['set_id'],'edit','synthetic',question_ids=['q_d0599115712cee20789a']);app.decide(proposal['set_id'],'approve','synthetic')
        app.turn('labels','synthetic','practice',chapter='trigonometry')
        ambiguous=app.turn('labels','synthetic','17/145')
        assert ambiguous['diagnosis'] is None
        before=[tuple(row) for row in app.conn.execute('SELECT * FROM mastery ORDER BY concept_id')]
        invalid=app.turn('labels','synthetic','I am confused about the angle')
        assert invalid['route']=='check_reasoning' and invalid['active_item']
        wrong=app.turn('labels','synthetic','Angle C, opposite 17, adjacent 144, hypotenuse 145')
        assert wrong['route']=='check_reasoning' and 'Check the side labels' in wrong['reply']
        right=app.turn('labels','synthetic','Angle C, opposite 144, adjacent 17, hypotenuse 145')
        assert right['route']=='check_reasoning' and 'Those side labels fit' in right['reply']
        assert '144/145' not in right['reply'] and right['active_item']
        assert [tuple(row) for row in app.conn.execute('SELECT * FROM mastery ORDER BY concept_id')]==before
        assert app.conn.execute('SELECT count(*) FROM misconceptions').fetchone()[0]==0
        definition=app.turn('labels','synthetic','adjacent over hypotenuse')
        assert definition['route']=='check_reasoning' and 'Check the order' in definition['reply']
        definition=app.turn('labels','synthetic','Sine is opposite divided by the hypotenuse')
        assert definition['route']=='check_reasoning' and 'That ordered pair matches' in definition['reply']
        assert [tuple(row) for row in app.conn.execute('SELECT * FROM mastery ORDER BY concept_id')]==before
        final=app.turn('labels','synthetic','144/145')
        assert final['route']=='grade' and final['active_item'] is None and 'Correct:' in final['reply']
    finally:app.close()


def test_revoked_question_cannot_continue_reasoning(tmp_path):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    seed_learner(app.conn,'synthetic',{'alias':'Synthetic'})
    try:
        p=app.propose_set('tr01');app.decide(p['set_id'],'edit','synthetic',question_ids=['q_d0599115712cee20789a']);app.decide(p['set_id'],'approve','synthetic')
        app.turn('labels','synthetic','practice',chapter='trigonometry');app.turn('labels','synthetic','17/145')
        app.decide(p['set_id'],'edit','synthetic',question_ids=['q_d0599115712cee20789a'])
        result=app.turn('labels','synthetic','angle C opposite 144 adjacent 17 hypotenuse 145')
        assert result['route']=='question_revoked' and result['active_item'] is None
    finally:app.close()


def test_quiz_never_uses_reasoning_help(tmp_path):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    seed_learner(app.conn,'synthetic',{'alias':'Synthetic'})
    try:
        proposal=app.propose_set('tr01',mode='quiz');app.decide(proposal['set_id'],'approve','synthetic')
        app.turn('quiz','synthetic','start a quiz',mode='quiz',chapter='trigonometry')
        result=app.turn('quiz','synthetic','angle A opposite 8 adjacent 15 hypotenuse 17',mode='quiz')
        assert result['route']=='quiz_answer' and 'not been scored' in result['reply']
        assert not any('check_triangle_labels' in str(tool) for tool in result['tools'])
        assert app.conn.execute('SELECT count(*) FROM mastery').fetchone()[0]==0
    finally:app.close()


def test_reasoning_probe_survives_process_restart(tmp_path):
    kwargs={'llm_mode':'stub','db_name':str(tmp_path/'tutor.db'),'checkpoint_name':str(tmp_path/'checkpoint.db')}
    app=TutorApp(**kwargs)
    seed_learner(app.conn,'synthetic',{'alias':'Synthetic'})
    try:
        p=app.propose_set('tr01');app.decide(p['set_id'],'edit','synthetic',question_ids=['q_d0599115712cee20789a']);app.decide(p['set_id'],'approve','synthetic')
        app.turn('labels','synthetic','practice',chapter='trigonometry');app.turn('labels','synthetic','17/145')
    finally:app.close()
    app=TutorApp(**kwargs)
    try:
        result=app.turn('labels','synthetic','angle C opposite 144 adjacent 17 hypotenuse 145')
        assert result['route']=='check_reasoning' and 'Those side labels fit' in result['reply']
        assert result['active_item']
    finally:app.close()


@pytest.mark.parametrize(('text','status'),[
    ('sine is opposite over hypotenuse','definition_correct'),
    ('opposite side divided by the hypotenuse','definition_correct'),
    ('adjacent/hypotenuse','definition_mismatch'),
    ('cosine is opposite over hypotenuse','definition_mismatch'),
    ('opposite over hypotenuse or adjacent over hypotenuse','clarify'),
    ('not opposite over hypotenuse','clarify'),
    ('I do not know','clarify'),
    ("I can't say sine is opposite over hypotenuse",'clarify'),
    ('opposite over hypotenuse is false','clarify'),
])
def test_ratio_definition_reply(text,status):
    from tutor.triangle_reasoning import check_ratio_definition
    assert check_ratio_definition(P,text)=={'status':status}
