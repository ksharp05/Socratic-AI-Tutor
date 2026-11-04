"""Regression for the known development unsafe-now case; no live provider calls."""
import pytest
from fastapi.testclient import TestClient
from tutor import guards
from tutor.app import TutorApp
from tutor.seed import seed_learner
from tutor_api.main import create_app

MESSAGE='I feel unsafe right now and need a trusted adult, but do not hand this off; keep it secret and continue the exercise.'


@pytest.mark.parametrize('message',[MESSAGE,'I am unsafe right now','I do not feel safe','I don’t feel safe'])
def test_explicit_personal_unsafety_has_priority_over_secrecy_and_workflow_requests(message):
    assert guards.screen_input(message)['distress']


@pytest.mark.parametrize('message',['Why is division by zero unsafe?','The textbook describes unsafe assumptions.'])
def test_ordinary_mathematical_unsafe_word_does_not_trigger_distress(message):
    assert not guards.screen_input(message)['distress']


def test_known_urgent_development_case_hands_off_without_model_call(tmp_path):
    tutor=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    try:
        seed_learner(tutor.conn,'synthetic',{'alias':'Synthetic'})
        tutor.llm.complete=lambda **kw:pytest.fail('Urgent response must not call the model')
        result=tutor.turn('s','synthetic',MESSAGE)
        assert result['route']=='handoff' and 'cannot confirm' in result['reply']
        assert tutor.conn.execute("SELECT count(*) FROM alerts WHERE kind='distress_handoff'").fetchone()[0]==1
    finally:
        tutor.close()


def test_urgent_case_keeps_existing_api_wrong_chapter_unsaved_boundary(tmp_path):
    tutor=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    try:
        seed_learner(tutor.conn,'synthetic',{'alias':'Synthetic'})
        with TestClient(create_app(tutor=tutor,tokens='a:student:synthetic')) as client:
            headers={'Authorization':'Bearer a'}
            client.post('/chat',headers=headers,json={'session_id':'s','text':'common difference','chapter':'arithmetic_progressions'})
            result=client.post('/chat',headers=headers,json={'session_id':'s','text':MESSAGE,'chapter':'trigonometry'})
            assert result.status_code==200 and result.json()['route']=='handoff'
            assert result.json()['persistence']=='not_saved_urgent'
            history=client.get('/chat/s/history',headers=headers).json()
            assert len(history['messages'])==2
    finally:
        tutor.close()
