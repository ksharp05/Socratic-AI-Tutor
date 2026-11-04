"""learner-store: the learner model (mastery, misconceptions, what worked, plan).

Why update_mastery needs no human approval: it is internal and reversible, affects only this learner's own
plan, is bounded to [0, 1] by code, is logged in learner_events and can be corrected by the teacher.
Publishing a question set changes what every student sees, so that write sits behind the approval gate.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from .. import learner, store
from ..config import SETTINGS
from ..setup_content import load
from ..topic_sources import concepts as topic_concepts
from ..store import dumps, now
from . import READ, WRITE

STATUSES = ("suspected", "confirmed", "addressed", "resolved")


def build(conn: sqlite3.Connection) -> FastMCP:
    concepts = {c["concept_id"] for c in topic_concepts()}
    misconceptions = {m["misconception_id"] for m in load("misconceptions")}

    def _exists(learner_id: str) -> None:
        if not conn.execute("SELECT 1 FROM learners WHERE learner_id=?", (learner_id,)).fetchone():
            raise ToolError(f"NOT_FOUND: unknown learner {learner_id}")

    def _event(learner_id: str, kind: str, payload: dict) -> None:
        conn.execute("INSERT INTO learner_events (learner_id, kind, payload, ts) VALUES (?,?,?,?)",
                     (learner_id, kind, dumps(payload), now()))

    mcp = FastMCP("learner-store")

    def _snapshot(learner_id: str) -> dict:
        _exists(learner_id)
        mastery = {r["concept_id"]: r["p"] for r in
                   conn.execute("SELECT concept_id, p FROM mastery WHERE learner_id=?", (learner_id,))}
        mis = {r["misconception_id"]: {"status": r["status"], "evidence_count": r["evidence_count"]} for r in
               conn.execute("SELECT * FROM misconceptions WHERE learner_id=?", (learner_id,))}
        styles = [dict(r) for r in conn.execute(
            "SELECT misconception_id, style, successes, failures FROM explanations WHERE learner_id=?", (learner_id,))]
        plan_row = conn.execute("SELECT plan_json FROM plans WHERE learner_id=?", (learner_id,)).fetchone()
        return {"learner_id": learner_id, "mastery": mastery, "misconceptions": mis, "styles": styles,
                "plan": json.loads(plan_row["plan_json"]) if plan_row else None}

    @mcp.tool(annotations=READ)
    def read_learner(learner_id: str) -> dict:
        """Read one learner's model: mastery, misconceptions, explanation styles that worked, and plan."""
        return _snapshot(learner_id)

    @mcp.tool(annotations=WRITE)
    def update_mastery(learner_id: str, concept_id: str, p_mastery: float, evidence_ref: str) -> dict:
        """Set mastery for one concept (0..1). Internal write; no approval needed (see module docstring)."""
        _exists(learner_id)
        if concept_id not in concepts:
            raise ToolError(f"INVALID_INPUT: unknown concept {concept_id}")
        if not 0.0 <= p_mastery <= 1.0:
            raise ToolError("INVALID_INPUT: p_mastery must be within [0, 1]")
        conn.execute("INSERT OR REPLACE INTO mastery VALUES (?,?,?,?)", (learner_id, concept_id, p_mastery, now()))
        _event(learner_id, "mastery", {"concept_id": concept_id, "p": p_mastery, "evidence": evidence_ref})
        return {"ok": True}

    @mcp.tool(annotations=WRITE)
    def record_misconception(learner_id: str, misconception_id: str, status: str, evidence_ref: str) -> dict:
        """Record evidence of a misconception and its status."""
        _exists(learner_id)
        if misconception_id not in misconceptions:
            raise ToolError(f"INVALID_INPUT: {misconception_id} is not in the catalogue")
        if status not in STATUSES:
            raise ToolError(f"INVALID_INPUT: status must be one of {STATUSES}")
        row = conn.execute("SELECT evidence_count FROM misconceptions WHERE learner_id=? AND misconception_id=?",
                           (learner_id, misconception_id)).fetchone()
        count = (row["evidence_count"] if row else 0) + 1
        conn.execute("INSERT OR REPLACE INTO misconceptions VALUES (?,?,?,?,?)",
                     (learner_id, misconception_id, status, count, now()))
        _event(learner_id, "misconception", {"id": misconception_id, "status": status, "evidence": evidence_ref})
        return {"ok": True, "evidence_count": count}

    @mcp.tool(annotations=WRITE)
    def record_explanation(learner_id: str, misconception_id: str, style: str, success: bool) -> dict:
        """Record whether an explanation style helped this learner."""
        _exists(learner_id)
        conn.execute("INSERT OR IGNORE INTO explanations (learner_id, misconception_id, style) VALUES (?,?,?)",
                     (learner_id, misconception_id, style))
        column = "successes" if success else "failures"
        conn.execute(f"UPDATE explanations SET {column}={column}+1 WHERE learner_id=? AND misconception_id=? AND style=?",
                     (learner_id, misconception_id, style))
        return {"ok": True}

    @mcp.tool(annotations=WRITE)
    def save_plan(learner_id: str, plan: dict) -> dict:
        """Save the learner's study plan (a new version)."""
        _exists(learner_id)
        conn.execute("INSERT OR REPLACE INTO plans VALUES (?,?,?,?)",
                     (learner_id, dumps(plan), int(plan.get("version", 1)), now()))
        _event(learner_id, "plan", {"version": plan.get("version"), "reason": plan.get("replan_reason")})
        return {"ok": True}

    @mcp.tool(annotations=WRITE)
    def apply_quiz(learner_id: str, quiz_id: str, results: list[dict]) -> dict:
        """Atomically apply a quiz and replan once; repeated identical applications are no-ops."""
        if not re.fullmatch(r"[0-9a-f]{32}", quiz_id) or not 1 <= len(results) <= 20:
            raise ToolError("INVALID_INPUT: invalid quiz identifier or result count")
        normalized = []
        for result in results:
            if not isinstance(result, dict):
                raise ToolError("INVALID_INPUT: invalid quiz result")
            qid, correct, scorable = result.get("question_id"), result.get("correct"), result.get("scorable")
            kind, ids = result.get("kind"), result.get("concept_ids")
            if (not isinstance(qid, str) or not 1 <= len(qid) <= 128 or type(correct) is not bool
                    or type(scorable) is not bool or (correct and not scorable)
                    or not isinstance(kind, str) or not 1 <= len(kind) <= 40
                    or not isinstance(ids, list) or not 1 <= len(ids) <= 25
                    or any(not isinstance(cid, str) or not 1 <= len(cid) <= 64 for cid in ids)
                    or len(set(ids)) != len(ids)):
                raise ToolError("INVALID_INPUT: invalid quiz result fields")
            normalized.append({"question_id": qid, "correct": correct, "scorable": scorable,
                               "kind": kind, "concept_ids": ids})
        digest = hashlib.sha256(dumps(normalized).encode("utf-8")).hexdigest()
        try:
            conn.execute("BEGIN IMMEDIATE")
            _exists(learner_id)
            existing = conn.execute("SELECT learner_id,payload_sha256 FROM applied_quizzes WHERE quiz_id=?",
                                    (quiz_id,)).fetchone()
            if existing:
                if existing["learner_id"] != learner_id or existing["payload_sha256"] != digest:
                    raise ToolError("FORBIDDEN: quiz identifier already binds different results")
                conn.execute("COMMIT")
                return {"applied": False, "quiz_id": quiz_id, "resolved_concepts": []}
            snapshot = _snapshot(learner_id)
            mastery = dict(snapshot["mastery"])
            resolved = []
            for result in normalized:
                if not result["scorable"]:
                    continue
                for cid in result["concept_ids"]:
                    if cid not in concepts:
                        continue
                    before = mastery.get(cid, SETTINGS.learner_model["p_init"])
                    after = learner.bkt_update(before, result["correct"], learner.GUESS_BY_KIND.get(result["kind"]))
                    mastery[cid] = after
                    conn.execute("INSERT OR REPLACE INTO mastery VALUES (?,?,?,?)", (learner_id,cid,after,now()))
                    _event(learner_id,"mastery",{"concept_id":cid,"p":after,
                           "evidence":f"{result['question_id']}:{'correct' if result['correct'] else 'incorrect'}"})
                    if result["correct"] and store._resolve_stuck_concept_locked(conn,learner_id,cid):
                        resolved.append(cid)
            fresh = _snapshot(learner_id)
            score = sum(result["correct"] for result in normalized)
            reason = f"after quiz: scored {score}/{len(normalized)}"
            plan = learner.make_plan(fresh, previous=fresh.get("plan"), reason=reason)
            conn.execute("INSERT OR REPLACE INTO plans VALUES (?,?,?,?)", (learner_id,dumps(plan),plan["version"],now()))
            _event(learner_id,"plan",{"version":plan["version"],"reason":reason})
            conn.execute("INSERT INTO applied_quizzes VALUES (?,?,?,?)", (quiz_id,learner_id,digest,now()))
            conn.execute("COMMIT")
            return {"applied": True, "quiz_id": quiz_id, "resolved_concepts": sorted(set(resolved))}
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise

    return mcp
