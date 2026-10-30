"""question-bank: propose sets; publish only with a teacher token tied to the exact payload hash."""
from __future__ import annotations

import hashlib
import json
import sqlite3

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from .. import approval_token
from ..setup_content import load
from ..store import dumps, now
from . import READ, WRITE

ITEM_FIELDS = ("question_id", "prompt", "problem", "answer_contract", "hint_stages", "difficulty")


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(dumps(payload).encode("utf-8")).hexdigest()


def build(conn: sqlite3.Connection) -> FastMCP:
    pool = {q["question_id"]: q for q in load("practice")}

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

    mcp = FastMCP("question-bank")

    @mcp.tool(annotations=READ)
    def list_published(concept_id: str | None = None) -> dict:
        """List items in teacher-approved (published) sets."""
        items = []
        for row in conn.execute("SELECT * FROM published ORDER BY published_at"):
            payload = json.loads(row["payload_json"])
            for item in payload["items"]:
                if concept_id is None or concept_id in item["problem"]["concept_ids"]:
                    items.append({**item, "set_id": row["set_id"], "label": row["label"]})
        return {"items": items}

    @mcp.tool(annotations=READ)
    def candidate_items(concept_id: str) -> dict:
        """Items in the unapproved development pool that practise a concept (for proposing sets)."""
        return {"question_ids": [q for q, item in pool.items() if concept_id in item["problem"]["concept_ids"]]}

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
        row = _proposal(set_id)
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
        _proposal(set_id)
        conn.execute("UPDATE proposals SET status='rejected', reason=?, updated_at=? WHERE set_id=?", (reason, now(), set_id))
        return {"rejected": True, "set_id": set_id}

    return mcp


def approval_token_valid(token: str, payload_sha256: str, teacher_id: str) -> bool:
    return approval_token.verify(token, payload_sha256, teacher_id)
