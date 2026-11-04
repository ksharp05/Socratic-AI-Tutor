"""question-bank: propose sets; publish only with a teacher token tied to the exact payload hash."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from .. import approval_token
from ..setup_content import load
from ..question_catalog import graph_items, allowed, MODES
from ..store import dumps, now
from . import READ, WRITE

ITEM_FIELDS = ("question_id", "prompt", "problem", "answer_contract", "hint_stages", "difficulty", "mode_policy",
               "chapter", "family_id", "supporting_passage_ids", "review_status", "authorship")
DEV_FIXTURE_LABELS = {"eval_fixture_unapproved", "development_fixture_not_human_approved"}


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(dumps(payload).encode("utf-8")).hexdigest()


def build(conn: sqlite3.Connection, *, allow_dev_fixtures: bool = False) -> FastMCP:
    pool = {q["question_id"]: q for q in graph_items(load)}

    def _proposal(set_id: str) -> sqlite3.Row:
        row = conn.execute("SELECT * FROM proposals WHERE set_id=?", (set_id,)).fetchone()
        if not row:
            raise ToolError(f"NOT_FOUND: no proposal {set_id}")
        return row

    def _payload(set_id: str, concept_id: str, question_ids: list[str], revision: int) -> dict:
        missing = [q for q in question_ids if q not in pool]
        if missing or not question_ids:
            raise ToolError(f"INVALID_INPUT: unknown or empty items {missing}")
        return {"set_id": set_id, "concept_id": concept_id, "revision": revision,
                "items": [{k: pool[q][k] for k in ITEM_FIELDS} for q in question_ids]}

    @contextmanager
    def _atomic_write():
        # Separate connections/processes cannot edit a proposal between digest
        # verification and publication; the DB write is all-or-nothing.
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            conn.execute("COMMIT")
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise

    def _verified_payload(raw: str, digest: str) -> dict | None:
        try:
            payload = json.loads(raw)
            return payload if isinstance(payload, dict) and payload_hash(payload) == digest else None
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    mcp = FastMCP("question-bank")

    @mcp.tool(annotations=READ)
    def list_published(concept_id: str | None = None, mode: str | None = None) -> dict:
        """List items in teacher-approved (published) sets."""
        if mode is not None and mode not in MODES:
            raise ToolError("INVALID_INPUT: unknown question mode")
        items = []
        rows = conn.execute("SELECT p.*, q.status AS proposal_status, q.payload_sha256 AS proposal_hash, "
                            "q.payload_json AS proposal_payload FROM published p "
                            "LEFT JOIN proposals q ON q.set_id=p.set_id ORDER BY p.published_at")
        for row in rows:
            if row["label"] == "teacher_approved":
                # An edit/rejection revokes visibility of the old publication,
                # while preserving that old row for audit until reapproval.
                if row["proposal_status"] != "published" or row["proposal_hash"] != row["payload_sha256"]:
                    continue
                payload = _verified_payload(row["payload_json"], row["payload_sha256"])
                if payload is None or _verified_payload(row["proposal_payload"], row["proposal_hash"]) is None:
                    continue
                # The grader computes from the current runtime pool. An old
                # approval must not authorize a different item under the same ID.
                published_items = payload.get("items")
                if (not isinstance(published_items, list) or not published_items or
                        any(not isinstance(item, dict) or not isinstance(item.get("question_id"), str) or
                            item["question_id"] not in pool or
                            any(item.get(field) != pool[item["question_id"]].get(field) for field in ITEM_FIELDS)
                            for item in published_items)):
                    continue
            elif allow_dev_fixtures and row["label"] in DEV_FIXTURE_LABELS:
                payload = json.loads(row["payload_json"])
            else:
                continue
            for item in payload["items"]:
                if ((concept_id is None or concept_id in item["problem"]["concept_ids"]) and
                        (mode is None or allowed(item, mode))):
                    items.append({**item, "set_id": row["set_id"], "set_payload_sha256": row["payload_sha256"],
                                  "label": row["label"]})
        return {"items": items}

    @mcp.tool(annotations=READ)
    def candidate_items(concept_id: str, mode: str = "practice") -> dict:
        """Items in the unapproved development pool that practise a concept (for proposing sets)."""
        if mode not in MODES:
            raise ToolError("INVALID_INPUT: unknown question mode")
        return {"question_ids": [q for q, item in pool.items() if concept_id in item["problem"]["concept_ids"] and allowed(item, mode)]}

    @mcp.tool(annotations=WRITE)
    def propose_set(set_id: str, concept_id: str, question_ids: list[str], rationale: str, thread_id: str) -> dict:
        """Propose a question set for teacher review. Proposing never publishes."""
        payload = _payload(set_id, concept_id, question_ids, 1)
        sha = payload_hash(payload)
        conn.execute("INSERT INTO proposals VALUES (?,?,?,?,?,?,?,?,?)",
                     (set_id, concept_id, dumps(payload), sha, "pending", 1, thread_id, rationale, now()))
        return {"set_id": set_id, "payload_sha256": sha, "items": len(question_ids)}

    @mcp.tool(annotations=READ)
    def get_proposal(set_id: str) -> dict:
        """Show a proposal with its payload hash and status."""
        row = _proposal(set_id)
        return {"set_id": set_id, "status": row["status"], "revision": row["revision"], "thread_id": row["thread_id"],
                "payload_sha256": row["payload_sha256"], "payload": json.loads(row["payload_json"]),
                "reason": row["reason"]}

    @mcp.tool(annotations=WRITE)
    def update_proposal(set_id: str, question_ids: list[str], thread_id: str) -> dict:
        """Edit a proposal. Any edit changes the payload hash, so earlier approvals stop working."""
        with _atomic_write():
            row = _proposal(set_id)
            revision = row["revision"] + 1
            payload = _payload(set_id, row["concept_id"], question_ids, revision)
            sha = payload_hash(payload)
            conn.execute("UPDATE proposals SET payload_json=?, payload_sha256=?, status='pending', revision=?, "
                         "thread_id=?, updated_at=? WHERE set_id=?", (dumps(payload), sha, revision, thread_id, now(), set_id))
        return {"set_id": set_id, "payload_sha256": sha, "revision": revision}

    @mcp.tool(annotations=WRITE)
    def publish_approved_set(set_id: str, approval_token: str, teacher_id: str) -> dict:
        """Publish a set. The token must match the CURRENT payload hash and the approving teacher."""
        with _atomic_write():
            row = _proposal(set_id)
            if row["status"] not in ("pending", "published"):
                raise ToolError("FORBIDDEN: this proposal is not eligible for publication")
            if _verified_payload(row["payload_json"], row["payload_sha256"]) is None:
                raise ToolError("FORBIDDEN: stored proposal does not match its payload digest")
            if not approval_token_valid(approval_token, row["payload_sha256"], teacher_id):
                raise ToolError("FORBIDDEN: approval token does not match the current payload (it was edited after "
                                "approval, or the token is not from this teacher)")
            conn.execute("INSERT OR REPLACE INTO published VALUES (?,?,?,?,?,?)",
                         (set_id, row["payload_json"], row["payload_sha256"], teacher_id, "teacher_approved", now()))
            conn.execute("UPDATE proposals SET status='published', updated_at=? WHERE set_id=?", (now(), set_id))
        return {"published": True, "set_id": set_id, "payload_sha256": row["payload_sha256"]}

    @mcp.tool(annotations=WRITE)
    def reject_proposal(set_id: str, reason: str) -> dict:
        """Reject a proposal and store the reason."""
        with _atomic_write():
            _proposal(set_id)
            conn.execute("UPDATE proposals SET status='rejected', reason=?, updated_at=? WHERE set_id=?", (reason, now(), set_id))
        return {"rejected": True, "set_id": set_id}

    return mcp


def approval_token_valid(token: str, payload_sha256: str, teacher_id: str) -> bool:
    return approval_token.verify(token, payload_sha256, teacher_id)
