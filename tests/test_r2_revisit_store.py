"""Owned, durable revisit queue; version binding, transaction idempotence and deletion."""
import pytest
from v02_integration.runtime import ContextualPreviewTutor
from tutor.seed import seed_learner
from tutor.question_catalog import graph_items,allowed
from tutor.toolbus import CallContext,ToolCallError

@pytest.fixture
def app(tmp_path):
    a=ContextualPreviewTutor(llm_mode='stub',db_name=str(tmp_path/'t.db'),checkpoint_name=str(tmp_path/'c.db'))
    seed_learner(a.conn,'queue-A',{'alias':'Synthetic A'});seed_learner(a.conn,'queue-B',{'alias':'Synthetic B'})
    try:yield a
    finally:a.close()


def invoke(app,tool,**args):
    return app.bus.call(CallContext('queue-session',learner_id='queue-A',node='update_memory'),'study_planner','learner-store',tool,{'learner_id':'queue-A',**args})


def item():return next(i for i in graph_items() if allowed(i,'practice'))


def test_queue_is_idempotent_and_does_not_award_mastery(app):
    q=item()['question_id'];assert invoke(app,'record_revisit',question_ref=q)['changed']
    assert not invoke(app,'record_revisit',question_ref=q)['changed']
    assert len(invoke(app,'read_learner')['revisit_items'])==1
    assert app.conn.execute("SELECT count(*) FROM learner_events WHERE kind='revisit_marked'").fetchone()[0]==1
    assert app.conn.execute('SELECT count(*) FROM mastery').fetchone()[0]==0
    assert invoke(app,'resolve_revisit',question_ref=q)['changed']
    assert not invoke(app,'resolve_revisit',question_ref=q)['changed']
    assert not invoke(app,'read_learner')['revisit_items']


def test_queue_survives_app_restart(tmp_path):
    paths={'db_name':str(tmp_path/'t.db'),'checkpoint_name':str(tmp_path/'c.db')}
    a=ContextualPreviewTutor(llm_mode='stub',**paths);seed_learner(a.conn,'queue-A',{'alias':'Synthetic'})
    q=item()['question_id'];invoke(a,'record_revisit',question_ref=q);a.close()
    b=ContextualPreviewTutor(llm_mode='stub',**paths)
    try:assert invoke(b,'read_learner')['revisit_items'][0]['question_ref']==q
    finally:b.close()


def test_other_learners_and_tutor_cannot_write_queue(app):
    q=item()['question_id']
    with pytest.raises(ToolCallError,match='FORBIDDEN'):invoke(app,'record_revisit',question_ref=q,learner_id='queue-B')
    with pytest.raises(ToolCallError,match='FORBIDDEN'):app.bus.call(CallContext('tutor',learner_id='queue-A'),'tutor','learner-store','record_revisit',{'learner_id':'queue-A','question_ref':q})
    assert app.conn.execute('SELECT count(*) FROM revisit_items').fetchone()[0]==0


def test_stale_content_is_preserved_but_not_scheduled_or_resolved(app):
    q=item()['question_id'];invoke(app,'record_revisit',question_ref=q)
    app.conn.execute("UPDATE revisit_items SET content_sha256='stale'")
    assert not invoke(app,'read_learner')['revisit_items']
    assert not invoke(app,'resolve_revisit',question_ref=q)['changed']
    assert app.conn.execute('SELECT count(*) FROM revisit_items').fetchone()[0]==1


def test_quiz_only_items_and_free_text_reasons_are_rejected(app):
    q=next(i['question_id'] for i in graph_items() if allowed(i,'quiz') and not allowed(i,'practice'))
    with pytest.raises(ToolCallError):invoke(app,'record_revisit',question_ref=q)
    with pytest.raises(ToolCallError):invoke(app,'record_revisit',question_ref=item()['question_id'],reason='arbitrary personal text')


def test_queue_is_deleted_with_learner_and_cannot_be_recreated(app):
    invoke(app,'record_revisit',question_ref=item()['question_id'])
    app.forget_learner('queue-A','synthetic-teacher')
    assert app.conn.execute("SELECT count(*) FROM revisit_items WHERE learner_id='queue-A'").fetchone()[0]==0
    with pytest.raises(ToolCallError,match='GONE'):invoke(app,'record_revisit',question_ref=item()['question_id'])


@pytest.mark.parametrize('operation',['record_revisit','resolve_revisit'])
def test_queue_and_event_roll_back_together_on_storage_failure(app,operation):
    q=item()['question_id']
    if operation=='resolve_revisit':invoke(app,'record_revisit',question_ref=q)
    before=[tuple(r) for r in app.conn.execute('SELECT * FROM revisit_items')]
    app.conn.execute("CREATE TRIGGER fail_queue_audit BEFORE INSERT ON learner_events BEGIN SELECT RAISE(ABORT,'synthetic storage fault'); END")
    with pytest.raises(ToolCallError):invoke(app,operation,question_ref=q)
    assert [tuple(r) for r in app.conn.execute('SELECT * FROM revisit_items')]==before
    assert not app.conn.in_transaction
