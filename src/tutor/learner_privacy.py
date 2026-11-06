"""Logical deletion of one graph learner, recoverable across separate SQLite stores.

The API owns authorization and the caller holds the shared publication lock.
A durable tombstone blocks access before checkpoint cleanup starts. No promise of
forensic erasure, backup deletion, or deletion of the separate anonymous beta.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import ExitStack
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from . import store
from .toolbus import ToolCallError

LEARNER_TABLES = (
    "mastery", "misconceptions", "explanations", "plans", "topic_plans",
    "learner_events", "revisit_items", "alerts", "stuck_sessions", "stuck_alert_state",
    "applied_quizzes", "graph_session_leases", "learner_session_index", "learners",
)


def _savers(app, stack):
    savers = {app.checkpoint_path: app.checkpointer}
    for row in app.conn.execute("SELECT checkpoint_path FROM learner_checkpoint_registry"):
        path = row["checkpoint_path"]
        if path in savers or not Path(path).exists():
            continue
        # mode=rw refuses to create a new database for an obsolete registered path.
        conn = sqlite3.connect(Path(path).as_uri() + "?mode=rw", uri=True, check_same_thread=False)
        stack.callback(conn.close)
        savers[path] = SqliteSaver(conn)
    return savers


def _session_refs(app, savers, learner_id, remembered):
    refs = {tuple(ref) for ref in remembered}
    refs.update((r["checkpoint_path"], r["session_id"]) for r in app.conn.execute(
        "SELECT checkpoint_path,session_id FROM learner_session_index WHERE learner_id=?", (learner_id,)))
    owners = {}
    for path, saver in savers.items():
        # Inspect all historical snapshots, not only the latest checkpoint. This
        # recovers pre-index conversations and detects legacy mixed-owner threads.
        for snap in saver.list(None):
            session = (snap.checkpoint.get("channel_values") or {}).get("session") or {}
            owner = session.get("learner_id")
            if owner:
                ref = (path, snap.config["configurable"]["thread_id"])
                owners.setdefault(ref, set()).add(owner)
                if owner == learner_id:
                    refs.add(ref)
    session_ids = {ref[1] for ref in refs}
    conflicting_index = any(r["session_id"] in session_ids for r in app.conn.execute(
        "SELECT session_id FROM learner_session_index WHERE learner_id<>?", (learner_id,)))
    conflicting_history = any(ref[1] in session_ids and other - {learner_id} for ref, other in owners.items())
    if session_ids & {"api", "teacher"} or conflicting_index or conflicting_history:
        raise ToolCallError("CONFLICT", "A legacy conversation has mixed ownership; deletion needs operator review.")
    return sorted(refs)


def forget(app, learner_id: str, teacher_id: str) -> dict:
    conn = app.conn
    row = conn.execute("SELECT * FROM learner_deletions WHERE learner_id=?", (learner_id,)).fetchone()
    if row and row["status"] == "complete":
        return json.loads(row["receipt_json"])
    if row is None:
        if not conn.execute("SELECT 1 FROM learners WHERE learner_id=?", (learner_id,)).fetchone():
            raise ToolCallError("NOT_FOUND", "Unknown learner.")
        conn.execute("INSERT INTO learner_deletions "
                     "(learner_id,request_id,teacher_id,requested_at,status) VALUES (?,?,?,?,?)",
                     (learner_id, uuid.uuid4().hex, teacher_id, store.now(), "pending"))
        row = conn.execute("SELECT * FROM learner_deletions WHERE learner_id=?", (learner_id,)).fetchone()
    try:
        with ExitStack() as stack:
            savers = _savers(app, stack)
            refs = _session_refs(app, savers, learner_id, json.loads(row["session_refs"]))
            # Commit the complete work list before deleting any checkpoint. Retry
            # can then remove traces even if a previous process lost its checkpoints.
            conn.execute("UPDATE learner_deletions SET session_refs=? WHERE learner_id=?",
                         (store.dumps(refs), learner_id))
            for path, session_id in refs:
                if path in savers:
                    savers[path].delete_thread(session_id)
                    for table in ("checkpoints", "writes"):
                        if savers[path].conn.execute(f"SELECT 1 FROM {table} WHERE thread_id=? LIMIT 1",
                                                    (session_id,)).fetchone():
                            raise RuntimeError("Checkpoint cleanup did not finish")
            counts = {}
            try:
                conn.execute("BEGIN IMMEDIATE")
                removed_traces = 0
                for session_id in {ref[1] for ref in refs}:
                    removed_traces += conn.execute("DELETE FROM trace_events WHERE session_id=?", (session_id,)).rowcount
                # Overview reads use the common 'api' session, so delete their
                # exact learner-linked arguments as well as conversation traces.
                removed_traces += conn.execute(
                    "DELETE FROM trace_events WHERE CASE WHEN json_valid(args) THEN json_extract(args,'$.learner_id') END = ?",
                    (learner_id,)).rowcount
                counts["trace_events"] = removed_traces
                for table in LEARNER_TABLES:
                    counts[table] = conn.execute(f"DELETE FROM {table} WHERE learner_id=?", (learner_id,)).rowcount
                receipt = {"deleted": True, "request_id": row["request_id"], "learner_id": learner_id,
                           "completed_at": store.now(), "checkpoint_threads": len(refs), "removed_rows": counts,
                           "scope": "graph learner and registered local checkpoint stores",
                           "logical_deletion_only": True, "backups_removed": False,
                           "separate_beta_profile_removed": False}
                conn.execute("UPDATE learner_deletions SET status='complete',session_refs='[]',receipt_json=? WHERE learner_id=?",
                             (store.dumps(receipt), learner_id))
                conn.execute("COMMIT")
            except Exception:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
        for _, session_id in refs:
            app._ctx.pop(session_id, None)
        return receipt
    except ToolCallError:
        raise
    except Exception as exc:
        raise ToolCallError("BUSY", "Deletion is pending; the learning record is blocked. A teacher can retry.") from exc
