"""math-tools: keys, grading, parsing, leak checks and diagnosis. Keys stay inside this server."""
from __future__ import annotations

import json
import sqlite3

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from .. import mathcore
from ..setup_content import load
from . import READ


def build(conn: sqlite3.Connection, extra_items: list[dict] | None = None) -> FastMCP:
    items = {q["question_id"]: q for q in load("practice")}
    for q in extra_items or []:
        items[q["question_id"]] = q

    def _item(question_ref: str) -> dict:
        if question_ref not in items:
            raise ToolError(f"NOT_FOUND: unknown question {question_ref}")
        return items[question_ref]

    def _key(question_ref: str) -> dict:
        row = conn.execute("SELECT key_json, verified FROM keys WHERE question_ref=?", (question_ref,)).fetchone()
        if row:
            return json.loads(row["key_json"])
        result = mathcore.compute_key(_item(question_ref)["problem"])
        conn.execute("INSERT OR REPLACE INTO keys VALUES (?,?,?)",
                     (question_ref, json.dumps(result["key"]), int(result["verified"])))
        if not result["verified"]:
            raise ToolError(f"UNVERIFIED: the two calculation routes disagree for {question_ref}")
        return result["key"]

    mcp = FastMCP("math-tools")

    @mcp.tool(annotations=READ)
    def solve(question_ref: str) -> dict:
        """Compute and verify the key before a question is shown. Returns only whether it is verified."""
        key = _key(question_ref)
        return {"question_ref": question_ref, "verified": True, "answer_kind": key["kind"]}

    @mcp.tool(annotations=READ)
    def parse_answer(question_ref: str, text: str) -> dict:
        """Turn the student's text into a typed answer (rules only; never judges correctness)."""
        parsed = mathcore.parse_answer(text, _key(question_ref))
        return {"ok": parsed["ok"], "display": parsed.get("display"), "reason": parsed.get("reason")}

    @mcp.tool(annotations=READ)
    def check_equivalence(question_ref: str, response: str) -> dict:
        """Grade the student's answer against the private key with the solver."""
        key = _key(question_ref)
        parsed = mathcore.parse_answer(response, key)
        if not parsed["ok"]:
            return {"status": "invalid_response", "scorable": False, "correct": None, "reason": parsed["reason"]}
        result = mathcore.grade(parsed["typed"], key)
        return {"status": result["status"], "scorable": result["scorable"], "correct": result["correct"],
                "reason": result["reason"], "parsed": parsed["display"]}

    @mcp.tool(annotations=READ)
    def diagnose_response(question_ref: str, response: str) -> dict:
        """Name misconceptions whose buggy rule reproduces this wrong answer."""
        key = _key(question_ref)
        parsed = mathcore.parse_answer(response, key)
        if not parsed["ok"]:
            return {"candidates": []}
        return {"candidates": mathcore.diagnose_response(_item(question_ref)["problem"], key, parsed["typed"])}

    @mcp.tool(annotations=READ)
    def leak_check(question_ref: str, text: str) -> dict:
        """Check whether a draft reply reveals the answer to this question."""
        return mathcore.leak_check(text, _key(question_ref))

    return mcp
