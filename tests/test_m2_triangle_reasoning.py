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


@pytest.mark.parametrize(('text', 'verdict', 'detail'), [
    ('I divided the opposite side by the hypotenuse for sine.', 'definition_correct', 'order'),
    ('साइन में सामने वाली भुजा को कर्ण से भाग दिया।', 'definition_correct', 'order'),
    ('Sin mein hypotenuse upar aur opposite niche rakhi.', 'definition_mismatch', 'reversed_order'),
    ('sin θ में opposite को hypotenuse से divide किया।', 'definition_correct', 'order'),
    ('sin C = opposite(C) / hypotenuse', 'definition_correct', 'order'),
    ('sin A = opposite(A) / hypotenuse', 'clarify', 'reference_angle'),
    ('I wrote 3/5. Can you check?', 'clarify', 'side_roles'),
    ('Sine mein hypotenuse ko denominator liya maine.', 'partial_correct', 'numerator'),
    ('cos and sin: opposite / hypotenuse', 'clarify', 'target_ratio'),
    ('साइन में सामने वाली भुजा को कर्ण से भाग नहीं दिया।', 'clarify', 'step'),
    ('I used opposite / hypotenuse or adjacent / hypotenuse.', 'clarify', 'choose_numerator:hypotenuse'),
    ('opposite/hypotenuse and then adjacent/hypotenuse', 'clarify', 'step'),
    ('I used opposite/hypotenuse but put adjacent on top.', 'clarify', 'step'),
    ('I copied opposite/hypotenuse. The adjacent side was on top.', 'clarify', 'side_roles'),
    ('Sine ke liye opposite by hypotenuse liya.', 'definition_correct', 'order'),
    ('sine: opposite over adjacent', 'definition_mismatch', 'denominator'),
    ('sine: adjacent over hypotenuse', 'definition_mismatch', 'numerator'),
    ('sin C = 144 / 145 because 144 is opposite and 145 is hypotenuse.', 'definition_correct', 'substitution'),
    ('Opposite 144 cm aur hypotenuse 145 cm hai to sine 145/144 liya.', 'definition_mismatch', 'reversed_order'),
    ('साइन में सामने की भुजा 144 सेमी और कर्ण 145 सेमी है, तो साइन 144/145 लिखा।', 'definition_correct', 'substitution'),
    ('sin C = 144 cm / 145 cm because 144 cm is opposite and 145 cm is hypotenuse.', 'definition_correct', 'substitution'),
    ('sin C = 17/145 because 17 is opposite and 145 is hypotenuse.', 'clarify', 'exercise_lengths'),
    ('sin C = 144/145 because 144 cm is opposite and 145 m is hypotenuse.', 'clarify', 'side_roles'),
    ('sin C = 144/145; opposite 144, opposite 17, hypotenuse 145.', 'clarify', 'side_roles'),
    ('sin C = -144/145; opposite 144 and hypotenuse 145.', 'clarify', 'side_roles'),
    ('sin C = 144/145 and 17/145; opposite 144 and hypotenuse 145.', 'clarify', 'side_roles'),
    ('Which angle should I use? I wrote 144/145.', 'clarify', 'reference_angle'),
    ('I put adjacent in the numerator.', 'definition_mismatch', 'numerator'),
    ('sin C = 144cm/145cm because 144cm is opposite and 145cm is hypotenuse.', 'definition_correct', 'substitution'),
    ('sin C = 144/145 + 1; opposite 144 and hypotenuse 145.', 'clarify', 'side_roles'),
    ('sin C: opposite/hypotenuse is 2/3.', 'clarify', 'side_roles'),
    ('Should I use the side facing the marked angle for sine?', 'partial_correct', 'other_side'),
    ('Should I use the adjacent leg for sine?', 'definition_mismatch', 'side_roles'),
    ('Can I use the opposite side for cosine?', 'definition_mismatch', 'target_ratio'),
    ('सामने वाली भुजा को साइन में लेना है, सही है?', 'partial_correct', 'other_side'),
    ('Saamne wali side sine mein aayegi na?', 'partial_correct', 'other_side'),
    ('Marked कोण की सामने वाली side sine के लिए चाहिए न?', 'partial_correct', 'other_side'),
    ('Sine compares the opposite side and the hypotenuse.', 'partial_correct', 'side_order'),
    ('Sine compares the adjacent leg with the hypotenuse.', 'definition_mismatch', 'side_roles'),
    ('साइन के लिए सामने वाली और पास वाली भुजा का अनुपात लिया।', 'definition_mismatch', 'side_roles'),
    ('कोसाइन के लिए सामने वाली और पास वाली भुजा का अनुपात लिया।', 'definition_mismatch', 'target_ratio'),
    ('साइन के लिए सामने वाली और पास वाली भुजा का अनुपात नहीं लिया।', 'clarify', 'step'),
    ('Which side should I use?', 'clarify', 'side_position'),
    ('The adjacent side is opposite too, I think.', 'clarify', 'conflicting_labels'),
    ('Maine hypotenuse ko adjacent bola, par angle clear nahi hai.', 'clarify', 'conflicting_labels'),
    ('Maine sin ke liye opposite ko hypotenuse se divide kiya, ye sahi hai?', 'definition_correct', 'order'),
    ('Cos ke liye adjacent ko hypotenuse se divide karna hai, right?', 'definition_mismatch', 'target_ratio'),
    ('I switched the reference angle but kept the opposite side.', 'definition_mismatch', 'relabel_angle'),
    ('I changed the reference angle but kept calling the same leg the opposite side.', 'definition_mismatch', 'relabel_angle'),
    ('I changed the reference angle but kept my notes and flipped the opposite side.', 'clarify', 'side_roles'),
    ('कोण बदल दिया, पर सामने वाली भुजा का नाम नहीं बदला।', 'definition_mismatch', 'relabel_angle'),
    ('Reference angle badal gaya lekin maine opposite side same rakhi.', 'definition_mismatch', 'relabel_angle'),
    ('I did not change the reference angle but kept the opposite side.', 'clarify', 'step'),
    ("I never changed the reference angle but kept the opposite side.", 'clarify', 'step'),
    ('I switched the reference angle but kept the hypotenuse.', 'clarify', 'side_roles'),
    ('I changed the angle. On another triangle I kept the opposite side.', 'clarify', 'side_roles'),
    ('I got stuck halfway.', 'clarify', 'step'),
])
def test_ratio_step_feedback(text, verdict, detail):
    from tutor.triangle_reasoning import ratio_step_feedback
    assert ratio_step_feedback(P, text) == (verdict, detail)


@pytest.mark.parametrize(('text', 'expected'), [
    ('Using angle C. Opposite is 144 cm, adjacent is 17 cm, hypotenuse is 145 cm.',
     ('definition_correct', 'setup_complete')),
    ('I picked A, with the 17 as opposite, 144 as adjacent and 145 as hypotenuse.',
     ('definition_mismatch', 'setup_angle')),
    ('For angle C, the opposite leg is 17, the nearby leg is 144, the long side is 145.',
     ('definition_mismatch', 'setup_labels')),
    ('Angle C. I wrote 144 opposite, 17 adjacent, and 145 hypotenuse, in that order.',
     ('definition_correct', 'setup_complete')),
    ('कोण C, सामने वाली भुजा 144 सेमी, पास वाली भुजा 17 सेमी और कर्ण 145 सेमी है।',
     ('definition_correct', 'setup_complete')),
    ('Angle C, opposite 144, hypotenuse 145.', ('partial_correct', 'setup_adjacent')),
    ('Angle C, opposite 144, adjacent 17, hypotenuse 150.', ('definition_mismatch', 'setup_hypotenuse')),
    ('Opposite 144, adjacent 17, hypotenuse 145.', ('clarify', 'reference_angle')),
    ('Angle A and angle C, opposite 144, adjacent 17, hypotenuse 145.', ('clarify', 'reference_angle')),
    ('Angle C, opposite 144 cm, adjacent 17 m, hypotenuse 145 cm.', ('clarify', 'conflicting_labels')),
    ('Angle C, opposite 144, opposite 17, adjacent 17, hypotenuse 145.', ('clarify', 'conflicting_labels')),
    ('Angle C, opposite 144 or 17, adjacent 17, hypotenuse 145.', ('clarify', 'step')),
    ('Angle C, opposite 144, adjacent 17, hypotenuse 145. I copied these from another triangle.',
     ('clarify', 'side_roles')),
])
def test_explicit_triangle_setup_feedback(text, expected):
    from tutor.triangle_reasoning import ratio_step_feedback
    assert ratio_step_feedback(P, text) == expected


@pytest.mark.parametrize(('text', 'verdict', 'detail'), [
    ('sin(C) = cos(A)', 'definition_correct', 'complementary_identity'),
    ('cos A = sin C', 'definition_correct', 'complementary_identity'),
    ('cos A = adjacent(A) / hypotenuse', 'definition_correct', 'complementary_setup'),
    ('Maine cos(A) = adjacent over hypotenuse', 'definition_correct', 'complementary_setup'),
    ('मैंने कोसाइन(A) = पास वाली भुजा / कर्ण', 'definition_correct', 'complementary_setup'),
    ('cos A = hypotenuse / adjacent', 'definition_mismatch', 'complementary_order'),
    ('cos A = opposite(A) / hypotenuse', 'definition_mismatch', 'complementary_sides'),
    ('sin C = tan A', 'definition_mismatch', 'complementary_identity'),
    ('cos A = adjacent(C) / hypotenuse', 'clarify', 'reference_angle'),
    ('cos C = adjacent(C) / hypotenuse', 'definition_mismatch', 'target_ratio'),
    ('sin(A) = cos(C)', 'clarify', 'target_ratio'),
    ('sin(C) = -cos(A)', 'clarify', 'target_ratio'),
    ('sin C = cos A or tan A', 'clarify', 'target_ratio'),
    ('cos A = adjacent / hypotenuse but I used the opposite leg', 'clarify', 'reference_angle'),
    ('cos A = 17/145', 'clarify', 'reference_angle'),
])
def test_complementary_angle_feedback(text, verdict, detail):
    from tutor.triangle_reasoning import ratio_step_feedback
    assert ratio_step_feedback(P, text) == (verdict, detail)


@pytest.mark.parametrize(('ratio', 'complement'), [
    ('sin', 'cos'), ('cos', 'sin'), ('tan', 'cot'), ('cot', 'tan'),
    ('sec', 'csc'), ('csc', 'sec'),
])
def test_complementary_identity_in_each_direction(ratio, complement):
    from tutor.triangle_reasoning import ratio_step_feedback
    problem = {**P, 'givens': {**P['givens'], 'ratio': ratio, 'reference': 'A'}}
    assert ratio_step_feedback(problem, f'{ratio}(A) = {complement}(C)') == (
        'definition_correct', 'complementary_identity',
    )


@pytest.mark.parametrize(('text', 'verdict', 'detail'), [
    ('sin(A) = opposite / hypotenuse', 'clarify', 'reference_angle'),
    ('sin ( A ) = opposite / hypotenuse', 'clarify', 'reference_angle'),
    ('sin(C) = opposite side (A) / hypotenuse', 'clarify', 'reference_angle'),
    ('sin C = opposite ÷ hypotenuse', 'definition_correct', 'order'),
    ('sin（C）＝opposite／hypotenuse', 'definition_correct', 'order'),
    ('sin C = opposite : hypotenuse', 'definition_correct', 'order'),
    ('sin C = 144⁄145 because 144 is opposite and 145 is hypotenuse',
     'definition_correct', 'substitution'),
    ('cos (A) = adjacent ∕ hypotenuse', 'definition_correct', 'complementary_setup'),
    ('sin(C) = opposite / hypotenuse + 1', 'clarify', 'expression'),
    ('sin(C) = (opposite / hypotenuse)²', 'clarify', 'expression'),
    ('sin(C) = -opposite / hypotenuse', 'clarify', 'expression'),
    ('sin(C) = 2 * opposite / hypotenuse', 'clarify', 'expression'),
    ('sin(C) = opposite / hypotenuse, then I changed the angle', 'clarify', 'reference_angle'),
])
def test_ratio_notation_feedback(text, verdict, detail):
    from tutor.triangle_reasoning import ratio_step_feedback
    assert ratio_step_feedback(P, text) == (verdict, detail)


@pytest.mark.parametrize(('text', 'verdict', 'detail'), [
    ('sin(C) = opposite / hypotenuse = 144/145', 'definition_correct', 'substitution'),
    ('sin C = opposite/hypotenuse = 17/145', 'definition_mismatch', 'substitution_numerator'),
    ('sin C = opposite/hypotenuse = 144/17', 'definition_mismatch', 'substitution_denominator'),
    ('sin C = opposite/hypotenuse = 145/144', 'definition_mismatch', 'substitution_order'),
    ('sin C = opposite/hypotenuse = 17/18', 'definition_mismatch', 'substitution_values'),
    ('sin C = opposite/hypotenuse = 288/290', 'definition_correct', 'equivalent_fraction'),
    ('साइन C = सामने वाली भुजा ÷ कर्ण = 144सेमी/145सेमी', 'definition_correct', 'substitution'),
    ('cos A = adjacent(A) / hypotenuse = 144/145', 'definition_correct', 'substitution'),
    ('cos A = adjacent(C) / hypotenuse = 144/145', 'clarify', 'reference_angle'),
    ('sin A = opposite / hypotenuse = 17/145', 'clarify', 'reference_angle'),
    ('sin C = opposite/adjacent = 144/145', 'definition_mismatch', 'denominator'),
    ('sin C = opposite/hypotenuse = 144cm/145m', 'clarify', 'substitution_units'),
    ('sin C = opposite/hypotenuse = 144/0', 'clarify', 'substitution_fraction'),
    ('sin C = opposite/hypotenuse = 0.4', 'clarify', 'substitution_fraction'),
    ('sin C = opposite/hypotenuse = 144/145 + 1', 'clarify', 'substitution_fraction'),
    ('sin C = opposite/hypotenuse = 144/145 = 0.4', 'clarify', 'substitution_fraction'),
    ('sin C = opposite/hypotenuse = 144/145 or 17/145', 'clarify', 'substitution_fraction'),
])
def test_ratio_substitution_feedback(text, verdict, detail):
    from tutor.triangle_reasoning import ratio_step_feedback
    assert ratio_step_feedback(P, text) == (verdict, detail)


@pytest.mark.parametrize(('text', 'verdict', 'detail'), [
    ('sin(C) = cos(A) = adjacent(A) / hypotenuse', 'definition_correct', 'complementary_setup'),
    ('cos(A) = sin(C) = opposite(C) / hypotenuse', 'definition_correct', 'order'),
    ('sin C = cos A = adjacent / hypotenuse = 144/145', 'definition_correct', 'substitution'),
    ('sin C = cos A = adjacent / hypotenuse = 17/145', 'definition_mismatch', 'substitution_numerator'),
    ('sin C = cos A = opposite / hypotenuse', 'definition_mismatch', 'complementary_sides'),
    ('sin C = tan A = adjacent / hypotenuse', 'definition_mismatch', 'complementary_identity'),
    ('sin C = cos A = hypotenuse / adjacent', 'definition_mismatch', 'complementary_order'),
    ('sin C = cos A = adjacent(C) / hypotenuse', 'clarify', 'reference_angle'),
    ('sin C = cos A = adjacent / hypotenuse + 1', 'clarify', 'expression'),
    ('sin C = cos A = 144/145', 'clarify', 'complementary_work'),
    ('sin C = cos A = adjacent / hypotenuse or opposite / hypotenuse', 'clarify', 'expression'),
    ('मैंने साइन(C)＝कोसाइन(A)＝पास वाली भुजा ÷ कर्ण＝१४४⁄१४५', 'definition_correct', 'substitution'),
])
def test_complementary_ratio_equation_chain(text, verdict, detail):
    from tutor.triangle_reasoning import ratio_step_feedback
    assert ratio_step_feedback(P, text) == (verdict, detail)


@pytest.mark.parametrize(('text', 'verdict', 'detail'), [
    ('sin(C) = AB/AC', 'definition_correct', 'order'),
    ('sin C = BA ÷ CA', 'definition_correct', 'order'),
    ('AB over AC', 'definition_correct', 'order'),
    ('B is the right angle. sin(C) = AB/AC', 'definition_correct', 'order'),
    ('right angle at B; sin(C) = BA/CA = 144/145', 'definition_correct', 'substitution'),
    ('sin(C) = opposite/AC', 'definition_correct', 'order'),
    ('sin(C) = AB/AC = 17/145', 'definition_mismatch', 'substitution_numerator'),
    ('sin(C) = AC/AB', 'definition_mismatch', 'reversed_order'),
    ('sin(C) = BC/AC', 'definition_mismatch', 'numerator'),
    ('sin(A) = BC/AC', 'clarify', 'reference_angle'),
    ('sin(B) = AB/AC', 'clarify', 'reference_angle'),
    ('right angle at C; sin(C) = AB/AC', 'clarify', 'diagram_angle'),
    ('sin(C) = AB/AD', 'clarify', 'diagram_labels'),
    ('sin(C) = AB/AC or BC/AC', 'clarify', 'choose_numerator:hypotenuse'),
    ('sin(C) = AB/AC + 1', 'clarify', 'step'),
    ('sin(C) = AB/AC = 144/145 + 1', 'clarify', 'substitution_fraction'),
    ('sin(C) = cos(A) = BA/CA', 'definition_correct', 'complementary_setup'),
    ('साइन(C)＝AB÷AC', 'definition_correct', 'order'),
    ('मैंने साइन C = AB / AC लिखा है।', 'definition_correct', 'order'),
    ('sin C = AB/AC = 144/145.', 'definition_correct', 'substitution'),
    ('Maine sin C = AB/AC likha', 'definition_correct', 'order'),
])
def test_vertex_labels_use_the_registered_triangle(text, verdict, detail):
    from tutor.triangle_reasoning import ratio_step_feedback
    assert ratio_step_feedback(P, text) == (verdict, detail)


@pytest.mark.parametrize(('text', 'verdict', 'detail'), [
    ('I wrote adjacent over hypotenuse, but I meant opposite over hypotenuse.', 'definition_correct', 'order'),
    ('sin C = AC/AB. Correction: sin C = AB/AC', 'definition_correct', 'order'),
    ('Maine pehle AC/AB likha, mera matlab AB/AC tha.', 'definition_correct', 'order'),
    ('पहले AC/AB लिखा। सुधार: साइन(C) = AB/AC', 'definition_correct', 'order'),
    ('I meant opposite over hypotenuse or adjacent over hypotenuse.', 'clarify', 'choose_numerator:hypotenuse'),
    ('not adjacent over hypotenuse; I meant opposite over hypotenuse', 'definition_correct', 'order'),
    ('I thought cos C = adjacent/hypotenuse. Correction: sin C = opposite/hypotenuse',
     'definition_correct', 'order'),
    ('I wrote adjacent over hypotenuse. Correction: no idea.', 'clarify', 'step'),
    ('sin A = BC/AC. Correction: AB/AC', 'clarify', 'reference_angle'),
    ('sin A = BC/AC. Correction: sin(C) = AB/AC', 'definition_correct', 'order'),
    ('I wrote opposite/hypotenuse. Correction: adjacent/hypotenuse', 'definition_mismatch', 'numerator'),
    ('I wrote opposite/hypotenuse. Correction: opposite/hypotenuse or adjacent/hypotenuse',
     'clarify', 'choose_numerator:hypotenuse'),
    ('I wrote opposite/hypotenuse. Correction: opposite/hypotenuse + 1', 'clarify', 'expression'),
    ('I wrote opposite/hypotenuse. Correction:', 'clarify', 'step'),
    ('Correction: AB/AC', 'definition_correct', 'order'),
    ('sin(A) = BC/AC. Correction: sin(C) = AB/AC. Correction: opposite/hypotenuse',
     'definition_correct', 'order'),
    ('cos C = adjacent/hypotenuse. Correction: opposite/hypotenuse', 'clarify', 'target_ratio'),
    ('I wrote adjacent/hypotenuse. Correction: maybe opposite/hypotenuse', 'clarify', 'step'),
    ('मैंने AC/AB लिखा। मेरा मतलब AB/AC था।', 'definition_correct', 'order'),
    ('I wrote opposite/hypotenuse. Correction: adjacent/hypotenuse. Correction: opposite/hypotenuse',
     'definition_correct', 'order'),
])
def test_explicit_step_revision(text, verdict, detail):
    from tutor.triangle_reasoning import ratio_step_feedback
    assert ratio_step_feedback(P, text) == (verdict, detail)
