"""Actual learner UI against the local API; all data synthetic and all calls stubbed."""
from pathlib import Path
from urllib.parse import urlsplit

import pytest
pytest.importorskip('streamlit')
import requests
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest
from tutor.app import TutorApp
from tutor.seed import seed_learner
from tutor_api.main import create_app


class StreamResponse:
    def __init__(self, response):
        self.response=response;self.status_code=response.status_code
    def __enter__(self):return self
    def __exit__(self,*args):self.response.close()
    def iter_lines(self,decode_unicode=True):return self.response.iter_lines()


@pytest.fixture
def learner_ui(tmp_path, monkeypatch):
    tutor=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    seed_learner(tutor.conn, 'ui-learner', {'alias': 'Synthetic UI regression'})
    sent=[]
    try:
        with TestClient(create_app(tutor=tutor,tokens='ui-fixture:student:ui-learner')) as client:
            def request(method,url,headers=None,timeout=None,**kwargs):
                return client.request(method,urlsplit(url).path,headers=headers,**kwargs)
            def post(url,headers=None,timeout=None,stream=None,**kwargs):
                sent.append(kwargs.get('json'))
                return StreamResponse(client.post(urlsplit(url).path,headers=headers,**kwargs))
            monkeypatch.setattr(requests,'request',request)
            monkeypatch.setattr(requests,'post',post)
            monkeypatch.setenv('TUTOR_API_URL','http://synthetic-local-api')
            monkeypatch.setenv('TUTOR_UI_TOKEN','ui-fixture')
            ui=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'ui/app.py')).run(timeout=30)
            assert not ui.exception
            yield ui,client,tutor,sent
    finally:tutor.close()


def choose_chapter(ui, chapter):
    next(x for x in ui.selectbox if x.label=='Chapter').set_value(chapter).run(timeout=30)
    assert not ui.exception


def send(ui,message):
    ui.chat_input[0].set_value(message).run(timeout=30)
    assert not ui.exception


def test_chapter_selection_reaches_ap_and_stays_pinned(learner_ui):
    ui,client,tutor,sent=learner_ui
    choose_chapter(ui,'arithmetic_progressions')
    send(ui,'I think an AP must always increase.')
    assert sent[-1]['chapter']=='arithmetic_progressions'
    assert next(x for x in ui.selectbox if x.label=='Chapter').disabled
    sid=ui.session_state['session_id']
    history=client.get('/chat/'+sid+'/history',headers={'Authorization':'Bearer ui-fixture'}).json()
    assert history['chapter']=='arithmetic_progressions'
    assert 'Can all neighbouring differences' in history['messages'][-1]['content']
    send(ui,'An AP can decrease or be constant.')
    assert 'identified the distinction' in ui.session_state['messages'][-1]['content']
    assert tutor.conn.execute("SELECT count(*) FROM mastery WHERE learner_id='ui-learner'").fetchone()[0]==0


def test_new_session_allows_a_new_chapter_and_clears_visible_old_chat(learner_ui):
    ui,client,tutor,sent=learner_ui
    choose_chapter(ui,'arithmetic_progressions');send(ui,'What is a common difference?')
    old=ui.session_state['session_id']
    next(x for x in ui.button if x.label=='New session').click().run(timeout=30)
    assert not next(x for x in ui.selectbox if x.label=='Chapter').disabled
    assert not ui.session_state['messages']
    choose_chapter(ui,'trigonometry');send(ui,'Which side is the hypotenuse?')
    assert sent[-1]['chapter']=='trigonometry' and ui.session_state['session_id']!=old
    refs=ui.session_state['messages'][-1]['citations']
    assert refs and all(r['chapter']=='trigonometry' for r in refs)


def test_reference_snapshots_remain_attached_to_their_original_turn(learner_ui):
    ui,client,tutor,sent=learner_ui
    choose_chapter(ui,'arithmetic_progressions');send(ui,'What is a common difference?')
    first=ui.session_state['messages'][-1]
    refs=first['citations'];assert refs
    send(ui,'How do I recognise an arithmetic progression?')
    tutor_messages=[m for m in ui.session_state['messages'] if m['role']=='tutor']
    assert len(tutor_messages)==2 and tutor_messages[0]['citations']==refs
    assert len(ui.expander)>=3
    visible=' '.join(x.value for x in ui.markdown)
    assert '[Reference 1]' in visible and '[normalized:ap' not in visible


def test_failed_stream_preserves_recovery_reference_without_fake_reply_or_retry(learner_ui,monkeypatch):
    ui,client,tutor,sent=learner_ui
    calls=[]
    def fail(*args,**kwargs):
        calls.append(kwargs.get('json'));raise requests.ConnectionError('synthetic unavailable endpoint')
    monkeypatch.setattr(requests,'post',fail)
    send(ui,'Please help with arithmetic progressions.')
    assert len(calls)==1 and calls[0]['session_id']==ui.session_state['session_id']
    assert [m['role'] for m in ui.session_state['messages']]==['student']
    assert 'connection was interrupted' in ui.session_state['chat_error'].lower()
    assert any('resuming' in x.value for x in ui.error)



def test_lost_completed_reply_is_restored_from_history_without_resending(learner_ui,monkeypatch):
    ui,client,tutor,sent=learner_ui
    calls=[]
    def completed_then_disconnected(url,headers=None,timeout=None,stream=None,**kwargs):
        calls.append(kwargs['json'])
        response=client.post(urlsplit(url).path,headers=headers,**kwargs)
        assert response.status_code==200
        raise requests.ConnectionError('synthetic lost final acknowledgement')
    monkeypatch.setattr(requests,'post',completed_then_disconnected)
    send(ui,'What is a common difference?')
    sid=ui.session_state['session_id']
    assert len(ui.session_state['messages'])==1 and ui.session_state['chat_error']
    next(x for x in ui.button if x.label=='Resume interrupted turn').click().run(timeout=30)
    assert not ui.exception and len(calls)==1
    assert ui.session_state['chat_error'] is None
    assert [m['role'] for m in ui.session_state['messages']]==['student','tutor']
    history=client.get('/chat/'+sid+'/history',headers={'Authorization':'Bearer ui-fixture'}).json()
    assert len(history['messages'])==2 and ui.session_state['messages'][-1]['citations']
