"""LLM access. With no API key (or TUTOR_LLM=stub) every call returns None and agents use templates."""
from __future__ import annotations

import os
import sqlite3
import time

from . import store
from .config import SETTINGS


class LLM:
    def __init__(self, conn: sqlite3.Connection, mode: str | None = None):
        self.conn = conn
        self.key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        mode = mode or os.environ.get("TUTOR_LLM", "auto")
        self.enabled = bool(self.key) and mode != "stub"
        self.model = os.environ.get("LLM_MODEL", SETTINGS.llm["specialist_model"])
        self._client = None

    @property
    def label(self) -> str:
        return f"{self.model} via {os.environ.get('LLM_BASE_URL', SETTINGS.llm['base_url'])}" if self.enabled \
            else "stub (no API key set; deterministic templates)"

    def _chat(self):
        if self._client is None:
            from langchain_openai import ChatOpenAI
            self._client = ChatOpenAI(model=self.model, api_key=self.key, temperature=SETTINGS.llm["temperature"],
                                      base_url=os.environ.get("LLM_BASE_URL", SETTINGS.llm["base_url"]),
                                      timeout=SETTINGS.llm["timeout_s"], max_retries=2)
        return self._client

    def complete(self, *, session_id: str | None, node: str, role: str, system: str, user: str) -> str | None:
        if not self.enabled:
            return None
        started = time.perf_counter()
        try:
            reply = self._chat().invoke([("system", system), ("user", user)])
            usage = getattr(reply, "usage_metadata", None) or {}
            store.trace(self.conn, session_id=session_id, node=node, role=role, kind="llm", name=self.model,
                        latency_ms=(time.perf_counter() - started) * 1000,
                        detail={"tokens_in": usage.get("input_tokens"), "tokens_out": usage.get("output_tokens")})
            return str(reply.content).strip()
        except Exception as exc:  # fall back to templates; the failure stays visible in the trace
            store.trace(self.conn, session_id=session_id, node=node, role=role, kind="llm", name=self.model,
                        outcome="error", latency_ms=(time.perf_counter() - started) * 1000,
                        detail={"error": f"{type(exc).__name__}: {exc}"[:300]})
            return None
