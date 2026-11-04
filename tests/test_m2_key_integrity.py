"""A checked key must stay bound to the exact problem and must be verified on every use."""
import copy
import pytest
from tutor.app import TutorApp
from tutor.setup_content import load
from tutor.toolbus import CallContext,ToolCallError


def item_for(c):
    item=copy.deepcopy(load('practice')[0]);item['question_id']='synthetic-cache-binding'
    item['problem']['givens']={'a':1,'b':0,'c':c}
    return item


def call(app,tool,args):
    return app.bus.call(CallContext(session_id='synthetic-cache'),
                        'question_setter' if tool=='solve' else 'grader','math-tools',tool,args)


def test_disagreed_calculations_never_become_a_verified_cache_hit(tmp_path,monkeypatch):
    from tutor import mathcore
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'db.sqlite'),checkpoint_name=str(tmp_path/'checkpoint.sqlite'),extra_items=[item_for(-1)])
    try:
        monkeypatch.setattr(mathcore,'compute_key',lambda _: {'key':{'kind':'finite_set','values':['1','-1']},'verified':False})
        for _ in range(2):
            with pytest.raises(ToolCallError,match='UNVERIFIED'):
                call(app,'solve',{'question_ref':'synthetic-cache-binding'})
    finally:app.close()


def test_cached_key_is_not_reused_for_a_changed_problem(tmp_path):
    db=tmp_path/'db.sqlite'
    app=TutorApp(llm_mode='stub',db_name=str(db),checkpoint_name=str(tmp_path/'first.sqlite'),extra_items=[item_for(-1)])
    try:
        assert call(app,'check_equivalence',{'question_ref':'synthetic-cache-binding','response':'x = 1 or x = -1'})['correct'] is True
    finally:app.close()
    changed=TutorApp(llm_mode='stub',db_name=str(db),checkpoint_name=str(tmp_path/'second.sqlite'),extra_items=[item_for(-4)])
    try:
        assert call(changed,'check_equivalence',{'question_ref':'synthetic-cache-binding','response':'x = 2 or x = -2'})['correct'] is True
        assert call(changed,'check_equivalence',{'question_ref':'synthetic-cache-binding','response':'x = 1 or x = -1'})['correct'] is False
    finally:changed.close()


def test_legacy_unverified_row_is_not_trusted(tmp_path,monkeypatch):
    from tutor import mathcore
    from tutor import store
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'db.sqlite'),checkpoint_name=str(tmp_path/'checkpoint.sqlite'),extra_items=[item_for(-1)])
    try:
        app.conn.execute('INSERT INTO keys VALUES (?,?,?)',('synthetic-cache-binding',store.dumps({'kind':'finite_set','values':['1','-1']}),0))
        monkeypatch.setattr(mathcore,'compute_key',lambda _: {'key':{'kind':'finite_set','values':['1','-1']},'verified':False})
        with pytest.raises(ToolCallError,match='UNVERIFIED'):
            call(app,'solve',{'question_ref':'synthetic-cache-binding'})
    finally:app.close()


def test_corrupted_verified_cache_is_recomputed(tmp_path,monkeypatch):
    from tutor import mathcore
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'db.sqlite'),checkpoint_name=str(tmp_path/'checkpoint.sqlite'),extra_items=[item_for(-1)])
    try:
        assert call(app,'check_equivalence',{'question_ref':'synthetic-cache-binding','response':'x = 1 or x = -1'})['correct'] is True
        app.conn.execute("UPDATE verified_key_cache SET key_json='{}' WHERE question_ref=?",('synthetic-cache-binding',))
        original=mathcore.compute_key; calls=[]
        def checked(problem):
            calls.append(True);return original(problem)
        monkeypatch.setattr(mathcore,'compute_key',checked)
        assert call(app,'check_equivalence',{'question_ref':'synthetic-cache-binding','response':'x = 1 or x = -1'})['correct'] is True
        assert len(calls)==1
    finally:app.close()


def test_changed_runtime_problem_invalidates_the_published_set(tmp_path,monkeypatch):
    from tutor.mcp_servers import question_bank
    db=tmp_path/'db.sqlite'
    app=TutorApp(llm_mode='stub',db_name=str(db),checkpoint_name=str(tmp_path/'first.sqlite'))
    try:
        proposal=app.propose_set('qe04');app.decide(proposal['set_id'],'approve','synthetic-teacher')
        payload=app.proposal(proposal['set_id'])['payload']
        chosen=payload['items'][0]['question_id']
    finally:app.close()
    original=question_bank.load
    def changed(name):
        rows=copy.deepcopy(original(name))
        if name=='practice':
            next(item for item in rows if item['question_id']==chosen)['problem']['givens']['c']+=1
        return rows
    monkeypatch.setattr(question_bank,'load',changed)
    second=TutorApp(llm_mode='stub',db_name=str(db),checkpoint_name=str(tmp_path/'second.sqlite'))
    try:
        visible=second.bus.call(CallContext(session_id='synthetic-publication'),'question_setter','question-bank','list_published',{})['items']
        assert not any(item['set_id']==proposal['set_id'] for item in visible)
    finally:second.close()


def test_solver_version_change_does_not_reuse_an_earlier_key(tmp_path,monkeypatch):
    from tutor import mathcore
    import sympy
    db=tmp_path/'db.sqlite'
    app=TutorApp(llm_mode='stub',db_name=str(db),checkpoint_name=str(tmp_path/'first.sqlite'),extra_items=[item_for(-1)])
    try:call(app,'solve',{'question_ref':'synthetic-cache-binding'})
    finally:app.close()
    monkeypatch.setattr(sympy,'__version__',sympy.__version__+'-synthetic-change')
    monkeypatch.setattr(mathcore,'compute_key',lambda _: {'key':{'kind':'finite_set','values':['1','-1']},'verified':False})
    changed=TutorApp(llm_mode='stub',db_name=str(db),checkpoint_name=str(tmp_path/'second.sqlite'),extra_items=[item_for(-1)])
    try:
        with pytest.raises(ToolCallError,match='UNVERIFIED'):
            call(changed,'solve',{'question_ref':'synthetic-cache-binding'})
    finally:changed.close()
