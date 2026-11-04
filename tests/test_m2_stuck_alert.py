"""A local teacher-view signal requires explicit stuck reports in three different sessions."""
import pytest
from fastapi.testclient import TestClient
from tutor.app import TutorApp
from tutor.seed import DEMO_LEARNERS, seed_learner
from tutor_api.main import create_app


@pytest.mark.parametrize('fresh', [False, True])
def test_three_distinct_sessions_create_one_teacher_view_event(tmp_path, fresh):
    tutor = TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                     checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        for learner_id, spec in DEMO_LEARNERS.items():
            seed_learner(tutor.conn, learner_id, {'alias': 'Fresh synthetic learner'} if fresh and learner_id == 'L-A' else spec)
        tutor.conn.commit()
        proposal = tutor.propose_set('qe04')
        assert tutor.decide(proposal['set_id'], 'approve', 'synthetic-teacher')['status'] == 'published'
        for session in ('first', 'second'):
            assert tutor.turn(session, 'L-A', 'practice')['active_item']
            tutor.turn(session, 'L-A', 'I am stuck')
            tutor.turn(session, 'L-A', 'still stuck')
            assert tutor.conn.execute("SELECT count(*) FROM alerts WHERE kind='stuck_concept'").fetchone()[0] == 0
        active = tutor.turn('third', 'L-A', 'practice')['active_item']
        assert active
        tutor.turn('third', 'L-A', 'I am stuck')
        tutor.turn('third', 'L-A', 'still stuck')
        rows = tutor.conn.execute("SELECT learner_id,detail FROM alerts WHERE kind='stuck_concept'").fetchall()
        assert len(rows) == 1 and rows[0]['learner_id'] == 'L-A'
        assert tutor.conn.execute("SELECT count(*) FROM stuck_sessions WHERE learner_id='L-A'").fetchone()[0] == 3
        api = create_app(tutor=tutor, tokens='a:student:L-A,b:student:L-B,t:teacher:T-001')
        with TestClient(api) as client:
            assert client.get('/learners/L-A', headers={'Authorization':'Bearer b'}).status_code == 403
            assert client.get('/learners/L-A', headers={'Authorization':'Bearer a'}).json()['alerts'] == []
            overview = client.get('/learners/L-A', headers={'Authorization':'Bearer t'}).json()
            event = next(x for x in overview['alerts'] if x['kind'] == 'stuck_concept')
            item = tutor.graph.get_state({'configurable': {'thread_id': 'third'}}).values['active_item']
            assert event['detail']['concept_id'] == (item['concept_ids'][0] if fresh else 'qe04')
            if fresh:
                assert overview['misconceptions'] == {}
            assert event['detail']['distinct_sessions'] == 3
            assert event['detail']['delivery'] == 'teacher_view_only'
            assert event['detail']['human_acknowledged'] is False
    finally:
        tutor.close()


def test_concurrent_signals_deduplicate_by_learner_concept_and_session(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from tutor import store

    db = tmp_path/'signals.db'
    store.connect(db).close()
    def record(session):
        conn = store.connect(db)
        try:
            return store.record_stuck_session(conn, 'learner', 'qe04', session)
        finally:
            conn.close()
    with ThreadPoolExecutor(max_workers=6) as pool:
        created = list(pool.map(record, ['s1', 's1', 's2', 's2', 's3', 's3']))
    assert sum(created) == 1
    conn = store.connect(db)
    try:
        assert conn.execute('SELECT count(*) FROM stuck_sessions').fetchone()[0] == 3
        assert conn.execute("SELECT count(*) FROM alerts WHERE kind='stuck_concept'").fetchone()[0] == 1
        # Other concepts and learners do not inherit the first learner's session history.
        assert not store.record_stuck_session(conn, 'learner', 'ap01', 's1')
        assert not store.record_stuck_session(conn, 'other', 'qe04', 's1')
        assert conn.execute("SELECT count(*) FROM alerts WHERE kind='stuck_concept'").fetchone()[0] == 1
    finally:
        conn.close()


def test_correct_attempt_closes_and_allows_a_later_alert_episode(tmp_path):
    import json
    from tutor import store

    conn = store.connect(tmp_path/'episodes.db')
    try:
        for session in ('one', 'two', 'three'):
            store.record_stuck_session(conn, 'learner', 'qe04', session)
        assert store.resolve_stuck_concept(conn, 'learner', 'qe04') is True
        first = json.loads(conn.execute("SELECT detail FROM alerts WHERE kind='stuck_concept'").fetchone()[0])
        assert first['resolved'] is True and first['resolution'] == 'checked_correct_attempt'
        assert first['human_acknowledged'] is False
        assert conn.execute('SELECT count(*) FROM stuck_sessions').fetchone()[0] == 0
        for session in ('four', 'five', 'six'):
            store.record_stuck_session(conn, 'learner', 'qe04', session)
        alerts = conn.execute("SELECT detail FROM alerts WHERE kind='stuck_concept' ORDER BY id").fetchall()
        assert len(alerts) == 2 and json.loads(alerts[1][0])['resolved'] is False
    finally:
        conn.close()


def test_alert_tables_are_added_without_resetting_existing_learner_data(tmp_path):
    import sqlite3
    from tutor import store

    db = tmp_path/'existing.db'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE learners (learner_id TEXT PRIMARY KEY, alias TEXT, created_at REAL)')
        conn.execute('INSERT INTO learners VALUES (?, ?, ?)', ('existing', 'existing learner', 1.0))
    conn = store.connect(db)
    try:
        assert conn.execute("SELECT alias FROM learners WHERE learner_id='existing'").fetchone()[0] == 'existing learner'
        assert not store.record_stuck_session(conn, 'existing', 'qe04', 'session-one')
        assert conn.execute('SELECT count(*) FROM stuck_sessions').fetchone()[0] == 1
    finally:
        conn.close()
