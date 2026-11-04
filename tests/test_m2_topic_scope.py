"""The connected graph must keep source and session scope within the chosen chapter."""
import pytest
from fastapi.testclient import TestClient
from tutor.app import TutorApp
from tutor.seed import seed_learner
from tutor_api.main import create_app


@pytest.fixture
def scoped(tmp_path,monkeypatch):
    monkeypatch.delenv('TUTOR_BETA_CONFIG',raising=False)
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoint.db'))
    seed_learner(app.conn,'L-A',{'alias':'Synthetic'})
    try:
        quiz=app.propose_set('qe04',mode='quiz');app.decide(quiz['set_id'],'approve','synthetic-teacher')
        practice=app.propose_set('qe04');app.decide(practice['set_id'],'approve','synthetic-teacher')
        with TestClient(create_app(tutor=app,tokens='a:student:L-A'),base_url='http://localhost') as client:
            yield client,app
    finally:app.close()


@pytest.mark.parametrize(('chapter','query','prefix'),[
    ('arithmetic_progressions','What is the common difference in an arithmetic progression?','normalized:ap'),
    ('trigonometry','How are sine cosine and the sides of a right triangle related?','normalized:tr'),
])
def test_connected_graph_returns_only_sources_from_selected_chapter(scoped,chapter,query,prefix):
    client,_=scoped;headers={'Authorization':'Bearer a'}
    response=client.post('/chat',headers=headers,json={'session_id':'scope-'+chapter,'text':query,'chapter':chapter})
    assert response.status_code==200,response.text
    body=response.json();assert body['chapter']==chapter
    assert body['citations'] and all(c['passage_id'].startswith(prefix) for c in body['citations'])
    assert all(c['review_status']=='pending' for c in body['citations'])
    assert body['plan'] is None


@pytest.mark.parametrize('chapter',['arithmetic_progressions','trigonometry'])
def test_other_chapters_never_receive_quadratic_practice_or_quiz(scoped,chapter):
    client,_=scoped;headers={'Authorization':'Bearer a'}
    for suffix,text,mode in [('practice','practice','practice'),('quiz','start a quiz','quiz')]:
        response=client.post('/chat',headers=headers,json={'session_id':chapter+'-'+suffix,'text':text,'mode':mode,'chapter':chapter})
        assert response.status_code==200,response.text
        assert response.json()['active_item'] is None and response.json()['quiz_active'] is False
        assert 'no teacher-approved' in response.json()['reply'].lower()


def test_chapter_is_pinned_for_existing_session(scoped):
    client,_=scoped;headers={'Authorization':'Bearer a'}
    first=client.post('/chat',headers=headers,json={'session_id':'pinned','text':'common difference','chapter':'arithmetic_progressions'})
    assert first.status_code==200
    changed=client.post('/chat',headers=headers,json={'session_id':'pinned','text':'sine','chapter':'trigonometry'})
    assert changed.status_code==409
    history=client.get('/chat/pinned/history',headers=headers).json()
    assert history['chapter']=='arithmetic_progressions' and len(history['messages'])==2
    assert client.post('/chat',headers=headers,json={'session_id':'bad','text':'hello','chapter':'biology'}).status_code==422


def test_ap_query_does_not_create_quadratic_misconception_or_plan(scoped):
    client,app=scoped;headers={'Authorization':'Bearer a'}
    response=client.post('/chat',headers=headers,json={'session_id':'ap-no-qe','chapter':'arithmetic_progressions',
        'text':'I divided both sides by x. What is a common difference?'})
    assert response.status_code==200 and response.json()['route']!='diagnose'
    assert response.json()['plan'] is None
    assert app.conn.execute('SELECT COUNT(*) FROM misconceptions WHERE learner_id=?',('L-A',)).fetchone()[0]==0
    assert app.conn.execute('SELECT COUNT(*) FROM plans WHERE learner_id=?',('L-A',)).fetchone()[0]==0


def test_citations_survive_history_and_omitted_chapter_continues_scope(scoped):
    client,_=scoped;headers={'Authorization':'Bearer a'}
    first=client.post('/chat',headers=headers,json={'session_id':'ap-history','chapter':'arithmetic_progressions',
        'text':'What is the common difference in an arithmetic progression?'}).json()
    assert first['citations'] and first['citations'][0]['source']['url'].startswith('https://')
    assert first['citations'][0]['source']['source_id']=='ncert_ap'
    assert len(first['citations'][0]['source']['source_sha256'])==64
    history=client.get('/chat/ap-history/history',headers=headers).json()
    last=history['messages'][-1]
    assert last['citations'][0]==first['citations'][0]
    assert history['chapter']=='arithmetic_progressions'
    follow=client.post('/chat',headers=headers,json={'session_id':'ap-history','text':'common difference'}).json()
    assert follow['chapter']=='arithmetic_progressions'
    assert all(c['passage_id'].startswith('normalized:ap') for c in follow['citations'])


def test_wrong_chapter_urgent_message_gets_unsaved_handoff(scoped):
    client,_=scoped;headers={'Authorization':'Bearer a'}
    client.post('/chat',headers=headers,json={'session_id':'pinned-urgent','chapter':'arithmetic_progressions','text':'common difference'})
    response=client.post('/chat',headers=headers,json={'session_id':'pinned-urgent','chapter':'trigonometry','text':'I want to die'})
    assert response.status_code==200 and response.json()['route']=='handoff'
    assert response.json()['persistence']=='not_saved_urgent' and response.json()['chapter']=='arithmetic_progressions'
    assert len(client.get('/chat/pinned-urgent/history',headers=headers).json()['messages'])==2


def test_saved_citation_does_not_change_when_current_card_changes(scoped):
    client,app=scoped;headers={'Authorization':'Bearer a'}
    first=client.post('/chat',headers=headers,json={'session_id':'source-version','chapter':'arithmetic_progressions',
        'text':'What is the common difference in an arithmetic progression?'}).json()
    citation=first['citations'][0];original=citation['text'];pid=citation['passage_id']
    app.cards[pid]['text']='Synthetic replacement that was never shown in this conversation.'
    history=client.get('/chat/source-version/history',headers=headers).json()
    saved=history['messages'][-1]['citations'][0]
    assert saved['text']==original and saved['text']!='Synthetic replacement that was never shown in this conversation.'


def test_citation_snapshot_has_verifiable_hash_and_legacy_messages_are_not_reconstructed(scoped):
    import hashlib
    from tutor import store
    client,app=scoped;headers={'Authorization':'Bearer a'}
    first=client.post('/chat',headers=headers,json={'session_id':'snapshot-hash','chapter':'trigonometry',
        'text':'sine cosine sides of a right triangle'}).json()
    citation=first['citations'][0];data={k:v for k,v in citation.items() if k!='reference_sha256'}
    assert citation['reference_sha256']==hashlib.sha256(store.dumps(data).encode('utf-8')).hexdigest()
    config={'configurable':{'thread_id':'snapshot-hash'}}
    app.graph.update_state(config,{'messages':[{'role':'tutor','content':'Legacy reference [normalized:tr01]','kind':'hint'}]},as_node='respond')
    history=client.get('/chat/snapshot-hash/history',headers=headers).json()
    assert history['messages'][-1]['content'].startswith('Legacy reference')
    assert not history['messages'][-1].get('citations')
