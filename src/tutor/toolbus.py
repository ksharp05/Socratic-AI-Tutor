"""Every tool call goes through here: the pre-tool and post-tool hooks wrap an MCP call.

Pre-tool: role allowlist, learner pinning (no reading or writing another learner), per-session budget.
Post-tool: trace event (scrubbed arguments), outcome and latency.
The POC talks to the four FastMCP servers over FastMCP's in-memory transport (real MCP protocol, no network);
stdio and HTTP transports come with Docker Compose.
"""
from __future__ import annotations

import asyncio
import logging
import sqlite3
import threading
import time
from dataclasses import dataclass, field

from fastmcp import Client

from . import store
from .mcp_servers import learner_store, math_tools, question_bank, textbook_kb

logging.getLogger("fastmcp").setLevel(logging.CRITICAL)

PERMISSIONS: dict[str, set[tuple[str, str]]] = {
    "study_planner": {("learner-store", t) for t in
                      ("read_learner", "update_mastery", "record_misconception", "record_explanation", "save_plan")},
    "diagnostician": {("textbook-kb", "search"), ("learner-store", "read_learner"), ("math-tools", "diagnose_response")},
    "tutor": {("textbook-kb", "search"), ("textbook-kb", "get_section")},
    "grader": {("math-tools", "check_equivalence"), ("math-tools", "parse_answer"), ("math-tools", "diagnose_response")},
    "question_setter": {("question-bank", "list_published"), ("question-bank", "candidate_items"),
                        ("question-bank", "propose_set"), ("math-tools", "solve")},
    "output_guard": {("math-tools", "leak_check")},
    "approval_gate": {("question-bank", t) for t in
                      ("get_proposal", "update_proposal", "publish_approved_set", "reject_proposal")}
                     | {("math-tools", "solve")},
}
_SCRUB = {"text", "response"}  # free text is logged by length only


class ToolCallError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message if message.startswith(f"{code}:") else f"{code}: {message}")
        self.code = code


@dataclass
class CallContext:
    session_id: str | None
    learner_id: str | None = None
    node: str = ""
    calls: int = 0
    budget: int = 300
    log: list = field(default_factory=list)


class ToolBus:
    def __init__(self, conn: sqlite3.Connection, extra_items: list[dict] | None = None, *, allow_dev_fixtures: bool = False):
        self.conn = conn
        self.servers = {"textbook-kb": textbook_kb.build(), "math-tools": math_tools.build(conn, extra_items),
                        "learner-store": learner_store.build(conn), "question-bank": question_bank.build(conn, allow_dev_fixtures=allow_dev_fixtures)}
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._clients = {name: self._run(self._open(server)) for name, server in self.servers.items()}

    async def _open(self, server):
        client = Client(server)
        await client.__aenter__()
        return client

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout=120)

    def close(self) -> None:
        for client in self._clients.values():
            try:
                self._run(client.__aexit__(None, None, None))
            except Exception:
                pass
        self._loop.call_soon_threadsafe(self._loop.stop)

    def list_tools(self) -> dict[str, list[dict]]:
        out = {}
        for name, client in self._clients.items():
            tools = self._run(client.list_tools())
            out[name] = [{"name": t.name, "description": t.description,
                          "read_only": bool(t.annotations and getattr(t.annotations, "read_only_hint", None)),
                          "input_schema": getattr(t, "input_schema", None) or {}} for t in tools]
        return out

    def call(self, ctx: CallContext, role: str, server: str, tool: str, args: dict) -> dict:
        scrubbed = {k: (f"<{len(str(v))} chars>" if k in _SCRUB else v) for k, v in args.items()}
        # ---- pre-tool hook ----
        denial = None
        if (server, tool) not in PERMISSIONS.get(role, set()):
            denial = ("FORBIDDEN", f"role '{role}' may not call {server}.{tool}")
        elif "learner_id" in args and ctx.learner_id and args["learner_id"] != ctx.learner_id:
            denial = ("FORBIDDEN", "a session may only touch its own learner")
        elif ctx.calls >= ctx.budget:
            denial = ("BUDGET", f"session tool-call budget of {ctx.budget} used up")
        if denial:
            store.trace(self.conn, session_id=ctx.session_id, node=ctx.node, role=role, kind="tool",
                        name=f"{server}.{tool}", args=scrubbed, outcome="denied", detail={"reason": denial[1]})
            raise ToolCallError(*denial)
        ctx.calls += 1
        started = time.perf_counter()
        result = self._run(self._clients[server].call_tool(tool, args, raise_on_error=False))
        latency = (time.perf_counter() - started) * 1000
        # ---- post-tool hook ----
        if result.is_error:
            message = " ".join(getattr(b, "text", "") for b in result.content) or "tool error"
            code = message.split(":", 1)[0] if ":" in message else "ERROR"
            store.trace(self.conn, session_id=ctx.session_id, node=ctx.node, role=role, kind="tool",
                        name=f"{server}.{tool}", args=scrubbed, outcome="error", latency_ms=latency,
                        detail={"error": message})
            raise ToolCallError(code, message)
        data = result.structured_content or {}
        store.trace(self.conn, session_id=ctx.session_id, node=ctx.node, role=role, kind="tool",
                    name=f"{server}.{tool}", args=scrubbed, outcome="ok", latency_ms=latency)
        ctx.log.append(f"{server}.{tool}")
        return data
