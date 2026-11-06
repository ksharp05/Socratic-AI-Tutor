"""Durable beta repository for pooled Postgres; no learner state on local disk."""
from __future__ import annotations
import hashlib
import threading
import time
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from .repository import Repository, BetaBusy

SCHEMA = """
CREATE TABLE IF NOT EXISTS beta_schema(version INTEGER PRIMARY KEY);
CREATE TABLE IF NOT EXISTS profiles(id TEXT PRIMARY KEY,preferences TEXT,created DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,owner TEXT,dataset TEXT,scope TEXT,
 title TEXT,state TEXT,created DOUBLE PRECISION,updated DOUBLE PRECISION);
CREATE INDEX IF NOT EXISTS owner_sessions ON sessions(owner,updated);
CREATE TABLE IF NOT EXISTS turns(id BIGSERIAL PRIMARY KEY,session_id TEXT,request_id TEXT,
 user_text TEXT,result TEXT,created DOUBLE PRECISION,UNIQUE(session_id,request_id));
CREATE TABLE IF NOT EXISTS assessments(id TEXT PRIMARY KEY,session_id TEXT,owner TEXT,mode TEXT,
 state TEXT,created DOUBLE PRECISION,updated DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS observations(id BIGSERIAL PRIMARY KEY,owner TEXT,session_id TEXT,node TEXT,
 kind TEXT,value TEXT,created DOUBLE PRECISION);
CREATE TABLE IF NOT EXISTS cards(id TEXT PRIMARY KEY,owner TEXT,dataset TEXT,passage_id TEXT,
 front TEXT,back TEXT,source TEXT,bucket INTEGER,due DOUBLE PRECISION,created DOUBLE PRECISION,
 UNIQUE(owner,dataset,passage_id));
CREATE TABLE IF NOT EXISTS reviews(id BIGSERIAL PRIMARY KEY,owner TEXT,card_id TEXT,rating TEXT,created DOUBLE PRECISION);
INSERT INTO beta_schema(version) VALUES(1) ON CONFLICT DO NOTHING;
"""

class Row(dict):
    def __getitem__(self, key):
        return tuple(self.values())[key] if isinstance(key, int) else super().__getitem__(key)

def rows(cursor):
    make = dict_row(cursor)
    return lambda values: Row(make(values))

class Connection:
    """Translate only the fixed repository SQL, retaining parameter binding."""
    def __init__(self, connection):
        self.connection = connection
    def execute(self, statement, parameters=()):
        ignore = statement.startswith("INSERT OR IGNORE INTO ")
        if ignore:
            statement = statement.replace("INSERT OR IGNORE INTO ", "INSERT INTO ", 1) + " ON CONFLICT DO NOTHING"
        return self.connection.execute(statement.replace("?", "%s"), parameters)

class PostgresRepository(Repository):
    def __init__(self, dsn, *, migrate=False):
        if not isinstance(dsn, str) or not dsn.startswith(("postgres://", "postgresql://")):
            raise ValueError("A Postgres connection URL is required")
        self._dsn = dsn
        self._local = threading.local()
        if migrate:
            self.migrate()
        with self.connect() as conn:
            if conn.execute("SELECT version FROM beta_schema").fetchall() != [Row(version=1)]:
                raise ValueError("Unsupported beta database schema")
    @contextmanager
    def raw_connection(self):
        # No automatic retries. Explicit transactions work with transaction pooling.
        with psycopg.connect(self._dsn, connect_timeout=10, row_factory=rows,
                             prepare_threshold=None) as connection:
            # Neon poolers reject statement_timeout in startup options.
            connection.execute("SET LOCAL statement_timeout = '35s'")
            yield connection
    def migrate(self):
        with self.raw_connection() as conn:
            conn.execute("SELECT pg_advisory_xact_lock(%s)", (735601871238312,))
            for statement in SCHEMA.split(";"):
                if statement.strip():
                    conn.execute(statement)
    @contextmanager
    def connect(self):
        with self.raw_connection() as connection:
            yield Connection(connection)
    @contextmanager
    def transaction(self):
        with self.connect() as connection:
            yield connection
    @contextmanager
    def owner_guard(self, owner, *, timeout=30):
        held = getattr(self._local, "held", None)
        if held is None:
            held = self._local.held = set()
        if owner in held:
            yield
            return
        key = int.from_bytes(hashlib.sha256(("socrates-beta-owner:"+owner).encode()).digest()[:8], "big", signed=True)
        deadline = time.monotonic() + max(0, timeout)
        # Transaction-scoped locks are released safely by PgBouncer transaction pools.
        with self.raw_connection() as connection:
            while not connection.execute("SELECT pg_try_advisory_xact_lock(%s)", (key,)).fetchone()[0]:
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    raise BetaBusy("Another request is still running. Please try again.")
                time.sleep(min(.05, remaining))
            held.add(owner)
            try:
                yield
            finally:
                held.remove(owner)
