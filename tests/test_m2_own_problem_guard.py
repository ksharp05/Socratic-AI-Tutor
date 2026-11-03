"""Synthetic regression for unverified homework and honest handoff messaging."""
import pytest
from tutor import guards
from tutor.seed import seed_learner
from tutor.app import TutorApp
from tutor_eval.single_agent import SingleAgentTutor
from v02_integration.runtime import ContextualPreviewTutor


@pytest.mark.parametrize('app_type', [TutorApp, SingleAgentTutor])
def test_unverified_learner_equation_stays_off_the_model_across_turns(tmp_path, app_type):
    app = app_type(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    calls = []
    try:
        seed_learner(app.conn, 'learner', {'alias':'synthetic'})
        app.conn.commit()
        app.llm.enabled = True
        def dangerous(**kwargs):
            calls.append(kwargs)
            return 'Set x to 0 or set x to 5 [normalized:qe04]. Which would you choose?'
        app.llm.complete = dangerous
        first = app.turn('homework', 'learner', 'I divided both sides by x in x² = 5x. Is that valid?')
        second = app.turn('homework', 'learner', 'I think dividing by x is always allowed.')
        assert first['route'] == 'diagnose' and second['route'] == 'tutor'
        assert not calls
        assert 'set x to 0' not in second['reply'].lower()
        assert 'what first step could you try' in second['reply'].lower()
        state = app.graph.get_state({'configurable':{'thread_id':'homework'}}).values
        assert state['unverified_own_problem'] is True
        assert second['checks'].get('ok')
        assert second['checks']['unverified_problem'] == 'deterministic_only_not_answer_checked'
    finally:
        app.close()


def test_additional_equation_during_registered_practice_cannot_reach_preview_model(tmp_path):
    app = ContextualPreviewTutor(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                                 checkpoint_name=str(tmp_path/'checkpoints.db'))
    calls = []
    try:
        seed_learner(app.conn, 'learner', {'alias':'synthetic'})
        app.conn.commit()
        proposal = app.propose_set('qe04')
        assert app.decide(proposal['set_id'], 'approve', 'synthetic-teacher')['status'] == 'published'
        app.llm.enabled = True
        app.llm.complete = lambda **kwargs: calls.append(kwargs) or 'What next [normalized:qe04]?'
        assert app.turn('practice', 'learner', 'practice')['active_item']
        app.turn('practice', 'learner', 'x² = 5x')
        assert not calls
        state = app.graph.get_state({'configurable':{'thread_id':'practice'}}).values
        assert state['unverified_own_problem'] is True
    finally:
        app.close()


def test_handoff_does_not_claim_an_unverified_notification():
    assert 'cannot confirm' in guards.HANDOFF_MESSAGE.lower()
    assert "i've let your teacher know" not in guards.HANDOFF_MESSAGE.lower()
    assert guards.unverified_own_problem('x² = 5x')
    assert guards.unverified_own_problem('Please solve 3x + 5 = 8')
    assert guards.unverified_own_problem('What is 2 plus 3?')
    assert guards.unverified_own_problem('Can you help with my homework?')
    assert not guards.unverified_own_problem('Why can dividing by zero be unsafe?')
    assert not guards.unverified_own_problem('What is a quadratic equation?')


def test_old_session_recovers_unverified_homework_boundary(tmp_path):
    app = TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                   checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        state = {'session': {'session_id':'old-session', 'learner_id':'learner', 'mode':'practice'},
                 'messages': [{'role':'student', 'content':'x² = 5x'}],
                 'incoming': 'I think dividing is fine',
                 'screen': guards.screen_input('I think dividing is fine')}
        assert app._input_guard(state)['unverified_own_problem'] is True
    finally:
        app.close()
