"""R2: the live beta's saved-question queue, per browser profile, on SQLite and real Postgres.

Synthetic owners and questions only. Postgres cases need BETA_TEST_POSTGRES_DSN on a loopback
`socrates_test` database (as in CI) and skip without it.
"""
import os
import uuid
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient

from socrates_beta.maths import AssessmentService
from socrates_beta.repository import Repository

ORIGIN = "https://socratic-tutor-beta.vercel.app"
HEADERS = {"Origin": ORIGIN, "X-Socrates-Request": "1"}
SHA_A, SHA_B = "a" * 64, "b" * 64


def _postgres_dsn():
    dsn = os.environ.get("BETA_TEST_POSTGRES_DSN")
    if not dsn:
        pytest.skip("Set a loopback synthetic Postgres test URL")
    parsed = urlsplit(dsn)
    assert parsed.hostname in ("localhost", "127.0.0.1") and parsed.path == "/socrates_test"
    return dsn


@pytest.fixture(params=["sqlite", "postgres"])
def repo(request, tmp_path):
    if request.param == "sqlite":
        return Repository(tmp_path / "beta.sqlite")
    from socrates_beta.postgres import PostgresRepository
    return PostgresRepository(_postgres_dsn(), migrate=True)


def owner():
    return "synthetic-" + uuid.uuid4().hex


def mark(repo, who, qid, *, session="s1", sha=SHA_A):
    return repo.mark_revisit(who, qid, session_id=session, chapter="quadratic_equations", content_sha256=sha)


def queued(repo, who):
    return [row["question_id"] for row in repo.pending_revisits(who)]


# ---------------------------------------------------------------- repository (SQLite and Postgres)

def test_marks_are_idempotent_and_come_back_oldest_first(repo):
    me = owner()
    assert mark(repo, me, "q-1") and mark(repo, me, "q-2")
    assert not mark(repo, me, "q-1", session="s2")          # already pending: keeps its place
    assert queued(repo, me) == ["q-1", "q-2"]
    assert repo.pending_revisits(me)[0]["session_id"] == "s1"


def test_profiles_cannot_see_or_clear_each_others_marks(repo):
    me, other = owner(), owner()
    mark(repo, me, "q-1")
    assert queued(repo, other) == []
    assert not repo.resolve_revisit(other, "q-1", content_sha256=SHA_A)
    assert queued(repo, me) == ["q-1"]


def test_only_the_same_content_clears_a_mark(repo):
    me = owner()
    mark(repo, me, "q-1")
    assert not repo.resolve_revisit(me, "q-1", content_sha256=SHA_B)   # question changed since it was saved
    assert queued(repo, me) == ["q-1"]
    assert repo.resolve_revisit(me, "q-1", content_sha256=SHA_A)
    assert not repo.resolve_revisit(me, "q-1", content_sha256=SHA_A)   # already cleared
    assert queued(repo, me) == []
    assert mark(repo, me, "q-1")                                       # can be saved again later
    assert queued(repo, me) == ["q-1"]


def test_changed_content_is_requeued_under_the_new_version(repo):
    me = owner()
    mark(repo, me, "q-1", sha=SHA_A)
    assert mark(repo, me, "q-1", sha=SHA_B)
    assert [r["content_sha256"] for r in repo.pending_revisits(me)] == [SHA_B]


def test_unknown_reasons_are_rejected(repo):
    with pytest.raises(ValueError):
        repo.mark_revisit(owner(), "q-1", session_id="s1", chapter="c", content_sha256=SHA_A, reason="free text")


def test_a_mark_rolls_back_with_its_transaction(repo):
    me = owner()
    with pytest.raises(RuntimeError):
        with repo.transaction() as conn:
            repo.mark_revisit(me, "q-1", session_id="s1", chapter="c", content_sha256=SHA_A, conn=conn)
            raise RuntimeError("rollback")
    assert queued(repo, me) == []


def test_forget_deletes_this_profiles_queue_only(repo):
    me, other = owner(), owner()
    mark(repo, me, "q-1"); mark(repo, me, "q-2"); repo.resolve_revisit(me, "q-2", content_sha256=SHA_A)
    mark(repo, other, "q-1")
    repo.forget(me)
    with repo.connect() as c:   # resolved rows too, not just what pending_revisits shows
        assert c.execute("SELECT COUNT(*) FROM revisit_queue WHERE owner=?", (me,)).fetchone()[0] == 0
    assert queued(repo, other) == ["q-1"]


def test_the_pending_list_is_capped(repo):
    me = owner()
    for i in range(Repository.REVISIT_LIMIT + 3):
        mark(repo, me, f"q-{i:03d}")
    rows = repo.pending_revisits(me)
    assert len(rows) == Repository.REVISIT_LIMIT and rows[0]["question_id"] == "q-000"


# ---------------------------------------------------------------- Postgres migration

def _isolated_schema_dsn(dsn, schema):
    return dsn + ("&" if "?" in dsn else "?") + "options=-csearch_path%3D" + schema


def test_version_1_database_migrates_to_2_without_changing_rows():
    import psycopg
    from socrates_beta import postgres
    dsn = _postgres_dsn()
    schema = "r2_migration_" + uuid.uuid4().hex[:12]
    scoped = _isolated_schema_dsn(dsn, schema)
    version_1 = postgres.SCHEMA.split("CREATE TABLE IF NOT EXISTS revisit_queue")[0]
    with psycopg.connect(dsn, autocommit=True) as admin:
        admin.execute(f"CREATE SCHEMA {schema}")
    try:
        with psycopg.connect(scoped) as conn:
            for statement in version_1.split(";"):
                if statement.strip():
                    conn.execute(statement)
            conn.execute("INSERT INTO profiles VALUES ('synthetic-v1', '{\"grade\": 10}', 1.0)")
        # Deployed before the migration: v2 code runs on v1 with the queue off, and practice is unchanged.
        unmigrated = postgres.PostgresRepository(scoped)
        assert unmigrated.revisit_queue is False
        service = AssessmentService(unmigrated, FakeMaths())
        started = service.start(new_session(unmigrated, "synthetic-v1"), "practice")
        assert started["revisit"] is False
        responses = [service.submit("synthetic-v1", started["id"], "wrong", f"v1-wrong-{i}") for i in range(3)]
        assert not any(r.get("saved_for_later") for r in responses)
        assert service.submit("synthetic-v1", started["id"], "right", "v1-right")["status"] == "correct"
        repo = postgres.PostgresRepository(scoped, migrate=True)
        assert repo.revisit_queue is True
        postgres.PostgresRepository(scoped, migrate=True)      # migrating twice is harmless
        assert repo.profile("synthetic-v1")["preferences"] == {"grade": 10}
        mark(repo, "synthetic-v1", "q-1")
        assert queued(repo, "synthetic-v1") == ["q-1"]
        with psycopg.connect(scoped) as conn:
            assert sorted(r[0] for r in conn.execute("SELECT version FROM beta_schema")) == [1, 2]
            conn.execute("INSERT INTO beta_schema(version) VALUES (3)")
        with pytest.raises(ValueError, match="schema"):
            postgres.PostgresRepository(scoped)                # a newer database than this code fails closed
    finally:
        with psycopg.connect(dsn, autocommit=True) as admin:
            admin.execute(f"DROP SCHEMA {schema} CASCADE")


# ---------------------------------------------------------------- practice flow (synthetic maths)

class FakeMaths:
    def __init__(self, n=4):
        policy = {"tutor_visible": True, "allowed_modes": ["practice", "quiz", "diagnostic"]}
        self.items = {f"q{i}": {"question_id": f"q{i}", "chapter": "quadratic_equations", "prompt": f"Synthetic {i}",
                                "problem": {"concept_ids": ["qe04"]}, "mode_policy": policy} for i in range(n)}
    def eligible(self, scope, concept=None): return list(self.items.values())
    def public_item(self, qid): return {"id": qid, "prompt": self.items[qid]["prompt"]}
    def grade(self, qid, text):
        right = text == "right"
        return {"status": "correct" if right else "incorrect", "correct": right, "scorable": True,
                "reasoning_evaluated": False}
    def hint(self, qid, stage): return f"Synthetic hint {stage}"


def new_session(repo, who):
    return repo.create_session(who, "synthetic-data", {"grade": 10, "subject": "Mathematics", "book": None, "unit": 4},
                               "Synthetic session")


def give_up(service, who, aid):
    """Three wrong answers show the last hint."""
    responses = [service.submit(who, aid, "wrong", f"wrong-{aid}-{i}") for i in range(3)]
    assert [r.get("saved_for_later", False) for r in responses] == [False, False, True]
    service.leave(who, aid)


@pytest.fixture
def flow(repo):
    return repo, AssessmentService(repo, FakeMaths())


def test_a_question_given_up_comes_back_first_in_a_later_conversation_until_solved(flow):
    repo, service = flow
    me = owner()
    first = new_session(repo, me)
    started = service.start(first, "practice")
    qid = started["item"]["id"]
    assert started["revisit"] is False
    give_up(service, me, started["id"])
    assert queued(repo, me) == [qid]

    again = service.start(first, "practice")                   # same conversation: not forced to the front
    assert again["revisit"] is False
    service.leave(me, again["id"])

    later = new_session(repo, me)
    back = service.start(later, "practice")
    assert back["revisit"] is True and back["item"]["id"] == qid
    assert service.submit(me, back["id"], "wrong", "still-wrong")["status"] == "incorrect"
    assert queued(repo, me) == [qid]                           # a wrong answer keeps the mark
    assert service.submit(me, back["id"], "right", "now-right")["status"] == "correct"
    assert queued(repo, me) == []                              # code-checked correct work clears it
    assert service.start(new_session(repo, me), "practice")["revisit"] is False


def test_the_hint_button_reaching_the_last_hint_also_saves(flow):
    repo, service = flow
    me = owner()
    started = service.start(new_session(repo, me), "practice")
    hints = [service.hint(me, started["id"]) for _ in range(3)]
    assert [h.get("saved_for_later", False) for h in hints] == [False, False, True]
    assert queued(repo, me) == [started["item"]["id"]]


def test_the_oldest_saved_question_is_served_first(flow):
    repo, service = flow
    me = owner()
    for qid in ("q2", "q1"):                                   # a chosen question bypasses the queue
        give_up(service, me, service.start(new_session(repo, me), "practice", question_id=qid)["id"])
    assert queued(repo, me) == ["q2", "q1"]
    back = service.start(new_session(repo, me), "practice")
    assert back["revisit"] is True and back["item"]["id"] == "q2"


def test_a_changed_or_withdrawn_question_is_not_served_but_stays_recorded(flow):
    repo, service = flow
    me = owner()
    started = service.start(new_session(repo, me), "practice")
    qid = started["item"]["id"]
    give_up(service, me, started["id"])
    service.maths.items[qid]["prompt"] = "Edited after it was saved"
    edited = service.start(new_session(repo, me), "practice")
    assert edited["revisit"] is False
    assert queued(repo, me) == [qid]
    service.leave(me, edited["id"])
    del service.maths.items[qid]
    assert service.start(new_session(repo, me), "practice")["revisit"] is False


def test_quizzes_neither_save_nor_serve_saved_questions(flow):
    repo, service = flow
    me = owner()
    started = service.start(new_session(repo, me), "practice")
    give_up(service, me, started["id"])
    quiz = service.start(new_session(repo, me), "quiz")
    assert quiz["revisit"] is False
    for i in range(quiz["total"]):
        service.submit(me, quiz["id"], "right" if i == 0 else "wrong", f"quiz-{i}")
    assert queued(repo, me) == [started["item"]["id"]]          # quiz answers do not clear practice marks


def test_another_profile_never_gets_my_saved_question(flow):
    repo, service = flow
    me, other = owner(), owner()
    started = service.start(new_session(repo, me), "practice")
    give_up(service, me, started["id"])
    assert service.start(new_session(repo, other), "practice")["revisit"] is False
    assert queued(repo, other) == []


# ---------------------------------------------------------------- live-site stack on Postgres

def test_live_site_saves_restores_isolates_and_forgets_on_postgres(tmp_path):
    from socrates_beta.postgres import PostgresRepository
    from socrates_beta.vercel_app import vercel_app
    repo = PostgresRepository(_postgres_dsn(), migrate=True)
    env = {"TUTOR_PUBLIC_ORIGIN": ORIGIN, "TUTOR_BROWSER_SECRET": "cd" * 32,
           "TUTOR_BETA_LIVE": "0", "VERCEL_URL": "beta-exact.vercel.app"}
    app = vercel_app(env=env, data=tmp_path / "first", repository=repo)
    with TestClient(app, base_url=ORIGIN) as client:
        assert client.get("/beta/api/bootstrap").status_code == 200
        cookie = "; ".join(k + "=" + v for k, v in client.cookies.items())
        me = cookie.split("=", 1)[1].split(".", 1)[0]
        sid = client.post("/beta/api/sessions", headers=HEADERS, json={"grade": 10, "subject": "Mathematics", "unit": 5}).json()["id"]
        check = client.post("/beta/api/practice", headers=HEADERS, json={"session_id": sid}).json()
        hints = [client.post(f"/beta/api/practice/{check['id']}/hint", headers=HEADERS, json={}).json() for _ in range(3)]
        assert hints[-1]["saved_for_later"] is True and "saved_for_later" not in hints[0]
        assert queued(repo, me) == [check["item"]["id"]]
        client.post(f"/beta/api/practice/{check['id']}/leave", headers=HEADERS, json={})
    restarted = vercel_app(env=env, data=tmp_path / "second", repository=PostgresRepository(repo._dsn))
    with TestClient(restarted, base_url=ORIGIN, headers={"Cookie": cookie}) as client:
        later = client.post("/beta/api/sessions", headers=HEADERS, json={"grade": 10, "subject": "Mathematics", "unit": 5}).json()["id"]
        back = client.post("/beta/api/practice", headers=HEADERS, json={"session_id": later}).json()
        assert back["revisit"] is True and back["item"]["id"] == check["item"]["id"]
        with TestClient(restarted, base_url=ORIGIN) as stranger:
            assert stranger.get("/beta/api/bootstrap").status_code == 200
            s = stranger.post("/beta/api/sessions", headers=HEADERS, json={"grade": 10, "subject": "Mathematics", "unit": 5}).json()["id"]
            assert stranger.post("/beta/api/practice", headers=HEADERS, json={"session_id": s}).json()["revisit"] is False
        client.post(f"/beta/api/practice/{back['id']}/leave", headers=HEADERS, json={})
        assert client.post("/beta/api/forget", headers=HEADERS, json={}).json()["deleted"]
    with repo.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM revisit_queue WHERE owner=?", (me,)).fetchone()[0] == 0
