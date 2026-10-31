"""Prometheus metrics. Labels stay bounded (routes, modes, the four MCP servers and their tools).

Tool calls, denials and blocked leaks are read from the trace table that the ToolBus hooks and the output
guard already write, so the tutor code needs no changes to be measured.
"""
from __future__ import annotations

import json

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

LEAK_DETECTORS = {"leak": "math_tools", "leak_phrase": "phrase"}


class Metrics:
    def __init__(self) -> None:
        self.registry = r = CollectorRegistry()
        self.turns = Counter("tutor_turns_total", "Student turns answered", ["mode", "route"], registry=r)
        self.replies = Counter("tutor_replies_total", "Replies sent to students", ["mode"], registry=r)
        self.leaks_blocked = Counter("tutor_answer_leak_blocked_total",
                                     "Draft replies the output guard blocked for leaking an answer", ["detector"],
                                     registry=r)
        self.guard_failures = Counter("tutor_output_guard_failures_total",
                                      "Draft replies that failed the output guard, by reason", ["reason"], registry=r)
        self.tool_calls = Counter("tutor_tool_calls_total", "MCP tool calls through the ToolBus",
                                  ["server", "tool", "outcome"], registry=r)
        self.tool_denied = Counter("tutor_tool_calls_denied_total", "Tool calls the pre-tool hook denied",
                                   ["server", "tool"], registry=r)
        self.api_denied = Counter("tutor_api_denied_total", "API requests refused by auth", ["status"], registry=r)
        self.handoffs = Counter("tutor_handoffs_total", "Distress handoffs", registry=r)
        self.errors = Counter("tutor_turn_errors_total", "Turns that raised an error", registry=r)
        self.latency = Histogram("tutor_turn_latency_seconds", "Wall-clock latency of one student turn", ["route"],
                                 buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20, 30, 60), registry=r)
        self.pending = Gauge("tutor_pending_approvals", "Question sets waiting for a teacher", registry=r)

    def observe_trace(self, rows) -> None:
        """Count new trace_events rows (tool calls and output-guard decisions)."""
        for row in rows:
            if row["kind"] == "tool":
                server, _, tool = (row["name"] or "").partition(".")
                self.tool_calls.labels(server, tool, row["outcome"]).inc()
                if row["outcome"] == "denied":
                    self.tool_denied.labels(server, tool).inc()
            elif row["kind"] == "decision" and row["node"] == "output_guard" and row["name"] == "fail":
                detail = json.loads(row["detail"] or "{}")
                for key, detector in LEAK_DETECTORS.items():
                    if detail.get(key):
                        self.leaks_blocked.labels(detector).inc()
                for reason in ("leak", "leak_phrase", "citations"):
                    if detail.get(reason):
                        self.guard_failures.labels(reason).inc()
