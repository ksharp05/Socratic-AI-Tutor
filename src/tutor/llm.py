"""LLM access. With no API key (or TUTOR_LLM=stub) every call returns None and agents use templates."""
from __future__ import annotations

import os
import sqlite3
import time

from . import store
from .config import SETTINGS

KEY_VARS = ("LLM_API_KEY", "OPENROUTER_API_KEY")


def api_key() -> tuple[str | None, str | None]:
    """The key, and the name of the variable it came from."""
    for name in KEY_VARS:
        if os.environ.get(name):
            return os.environ[name], name
    return None, None


def base_url() -> str:
    return os.environ.get("LLM_BASE_URL", SETTINGS.llm["base_url"])


def explain(exc: Exception) -> str:
    """One line saying why a call failed and what to do about it."""
    status = getattr(exc, "status_code", None)
    hint = {401: "the key was rejected; check the key in .env",
            402: "the key has run out of credit",
            403: "this key may not use this model",
            404: "this key cannot reach this model; use one from course_models in config/app.toml",
            429: "rate limited; wait a minute and try again"}.get(status)
    if status is None and any(word in type(exc).__name__ for word in ("Connection", "Timeout")):
        hint = f"could not reach {base_url()}; check the network or proxy"
    detail = f"{type(exc).__name__}: {exc}"[:200]
    return f"{hint} ({detail})" if hint else detail


class LLM:
    def __init__(self, conn: sqlite3.Connection | None, mode: str | None = None):
        self.conn = conn
        self.key, self.key_source = api_key()
        mode = mode or os.environ.get("TUTOR_LLM", "auto")
        self.enabled = bool(self.key) and mode != "stub"
        self.model = os.environ.get("LLM_MODEL", SETTINGS.llm["specialist_model"])
        self.errors: list[str] = []  # failed live calls, so the CLI can say a reply came from a template
        self._clients: dict[str, object] = {}

    @property
    def label(self) -> str:
        if self.enabled:
            return f"{self.model} via {base_url()}"
        return "stub (TUTOR_LLM=stub)" if self.key else "stub (no API key set; deterministic templates)"

    def _chat(self, model: str | None = None):
        model = model or self.model
        if model not in self._clients:
            from langchain_openai import ChatOpenAI
            self._clients[model] = ChatOpenAI(model=model, api_key=self.key, temperature=SETTINGS.llm["temperature"],
                                              base_url=base_url(), timeout=SETTINGS.llm["timeout_s"], max_retries=2,
                                              extra_body={"usage": {"include": True}})
        return self._clients[model]

    def ping(self, model: str | None = None) -> dict:
        """One short call with the agents' own client settings, for `tutor check-llm`. Raises on failure."""
        started = time.perf_counter()
        reply = self._chat(model).invoke([("user", "Reply with the single word: ready")])
        usage = getattr(reply, "usage_metadata", None) or {}
        return {"ms": round((time.perf_counter() - started) * 1000), "reply": str(reply.content).strip()[:60],
                "tokens_in": usage.get("input_tokens"), "tokens_out": usage.get("output_tokens")}

    def complete(self, *, session_id: str | None, node: str, role: str, system: str, user: str,
                 max_tokens: int | None = None, model: str | None = None) -> str | None:
        """One call. `model` overrides the specialist model for this call only (the safety classifier, D-7)."""
        if not self.enabled:
            return None
        model = model or self.model
        started = time.perf_counter()
        try:
            options = {} if max_tokens is None else {"max_tokens": max_tokens}
            reply = self._chat(model).invoke([("system", system), ("user", user)], **options)
            usage = getattr(reply, "usage_metadata", None) or {}
            billed = (getattr(reply, "response_metadata", None) or {}).get("token_usage") or {}
            store.trace(self.conn, session_id=session_id, node=node, role=role, kind="llm", name=model,
                        latency_ms=(time.perf_counter() - started) * 1000,
                        detail={"tokens_in": usage.get("input_tokens"), "tokens_out": usage.get("output_tokens"),
                                "cost_usd": billed.get("cost")})
            return str(reply.content).strip()
        except Exception as exc:  # fall back to templates; the failure stays visible in the trace
            self.errors.append(explain(exc))
            store.trace(self.conn, session_id=session_id, node=node, role=role, kind="llm", name=model,
                        outcome="error", latency_ms=(time.perf_counter() - started) * 1000,
                        detail={"error": f"{type(exc).__name__}: {exc}"[:300]})
            return None
