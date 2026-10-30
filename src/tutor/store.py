"""SQLite storage for the POC (Postgres replaces it once Docker is available; see Docs/plan D4)."""
from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS learners (learner_id TEXT PRIMARY KEY, alias TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS mastery (learner_id TEXT, concept_id TEXT, p REAL, updated_at REAL,
  PRIMARY KEY (learner_id, concept_id));
CREATE TABLE IF NOT EXISTS misconceptions (learner_id TEXT, misconception_id TEXT, status TEXT,
  evidence_count INTEGER, last_seen REAL, PRIMARY KEY (learner_id, misconception_id));
CREATE TABLE IF NOT EXISTS explanations (learner_id TEXT, misconception_id TEXT, style TEXT,
  successes INTEGER DEFAULT 0, failures INTEGER DEFAULT 0, PRIMARY KEY (learner_id, misconception_id, style));
CREATE TABLE IF NOT EXISTS plans (learner_id TEXT PRIMARY KEY, plan_json TEXT, version INTEGER, updated_at REAL);
CREATE TABLE IF NOT EXISTS learner_events (id INTEGER PRIMARY KEY AUTOINCREMENT, learner_id TEXT, kind TEXT,
  payload TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS keys (question_ref TEXT PRIMARY KEY, key_json TEXT, verified INTEGER);
CREATE TABLE IF NOT EXISTS proposals (set_id TEXT PRIMARY KEY, concept_id TEXT, payload_json TEXT,
  payload_sha256 TEXT, status TEXT, revision INTEGER, thread_id TEXT, reason TEXT, updated_at REAL);
CREATE TABLE IF NOT EXISTS published (set_id TEXT PRIMARY KEY, payload_json TEXT, payload_sha256 TEXT,
  approved_by TEXT, label TEXT, published_at REAL);
CREATE TABLE IF NOT EXISTS alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, kind TEXT, learner_id TEXT,
  detail TEXT);
CREATE TABLE IF NOT EXISTS trace_events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, session_id TEXT,
  node TEXT, role TEXT, kind TEXT, name TEXT, args TEXT, outcome TEXT, latency_ms REAL, detail TEXT);
"""


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def now() -> float:
    return time.time()


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def trace(conn: sqlite3.Connection, *, session_id: str | None, node: str, role: str, kind: str, name: str,
          args=None, outcome: str = "ok", latency_ms: float = 0.0, detail=None) -> None:
    conn.execute("INSERT INTO trace_events (ts, session_id, node, role, kind, name, args, outcome, latency_ms, detail)"
                 " VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (now(), session_id, node, role, kind, name, dumps(args) if args is not None else None, outcome,
                  round(latency_ms, 1), dumps(detail) if detail is not None else None))


def alert(conn: sqlite3.Connection, kind: str, learner_id: str | None, detail: dict) -> None:
    conn.execute("INSERT INTO alerts (ts, kind, learner_id, detail) VALUES (?,?,?,?)",
                 (now(), kind, learner_id, dumps(detail)))
