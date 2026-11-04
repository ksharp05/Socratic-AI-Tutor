"""math-tools: keys, grading, parsing, leak checks and diagnosis. Keys stay inside this server."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import sympy

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from .. import mathcore
from socratic_data import assessment_tasks, math_kernel, tasks  # mathcore registers the dataset path
from ..question_catalog import graph_items
from ..store import dumps
from . import READ


def build(conn: sqlite3.Connection, extra_items: list[dict] | None = None) -> FastMCP:
    items = {q["question_id"]: q for q in graph_items()}
    for q in extra_items or []:
        if q["question_id"] in items:
            raise ValueError("An extra question cannot replace a catalog question")
        items[q["question_id"]] = q

    def _item(question_ref: str) -> dict:
        if question_ref not in items:
            raise ToolError(f"NOT_FOUND: unknown question {question_ref}")
        return items[question_ref]

    # Cache entries are valid only for the loaded problem and calculation code.
    # Legacy `keys` rows lack this provenance and are never trusted for reads.
    engine = hashlib.sha256()
    for module in (mathcore, math_kernel, tasks, assessment_tasks):
        engine.update(module.__name__.encode("utf-8") + b"\0")
        engine.update(Path(module.__file__).read_bytes())
    engine.update((sympy.__version__ + ":" + sys.version).encode("utf-8"))
    solver_sha256 = engine.hexdigest()

    def _key(question_ref: str) -> dict:
        problem = _item(question_ref)["problem"]
        problem_sha256 = hashlib.sha256(dumps(problem).encode("utf-8")).hexdigest()
        row = conn.execute("SELECT key_json,key_sha256 FROM verified_key_cache "
                           "WHERE question_ref=? AND problem_sha256=? AND solver_sha256=?",
                           (question_ref,problem_sha256,solver_sha256)).fetchone()
        if row and hashlib.sha256(row["key_json"].encode("utf-8")).hexdigest() == row["key_sha256"]:
            try:
                cached = json.loads(row["key_json"])
                if isinstance(cached, dict):
                    return cached
            except (TypeError, ValueError):
                pass
        result = mathcore.compute_key(problem)
        if result.get("verified") is not True or not isinstance(result.get("key"), dict):
            raise ToolError(f"UNVERIFIED: the two calculation routes disagree for {question_ref}")
        key_json = dumps(result["key"])
        key_sha256 = hashlib.sha256(key_json.encode("utf-8")).hexdigest()
        conn.execute("INSERT OR REPLACE INTO verified_key_cache VALUES (?,?,?,?,?)",
                     (question_ref,problem_sha256,solver_sha256,key_json,key_sha256))
        # Retain the legacy audit/read interface; correctness never relies on this mirror.
        conn.execute("INSERT OR REPLACE INTO keys VALUES (?,?,?)", (question_ref,key_json,1))
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
