"""Teacher-only trace projection: no prompts, tool arguments/results or key values."""
from __future__ import annotations

import json
import re

from tutor.toolbus import ToolCallError

GENERATION_REASONS = frozenset({
    "no_model_response", "contradicts_verified_verdict", "word_or_question_count",
    "turn_shape", "generic_answer_phrase", "invalid_or_missing_source_id",
    "active_item_leak_or_unknown_verdict", "leak_check_failed", "new_number",
})
CITED_TURN_LIMIT = 50


def _citation_refs(citations) -> list[dict]:
    """Identifiers and hashes only; older messages may hold bare passage IDs without a snapshot hash."""
    refs = []
    for c in citations or []:
        if isinstance(c, dict):
            refs.append({key: c.get(key) for key in ("passage_id", "reference_sha256")})
        elif isinstance(c, str):
            refs.append({"passage_id": c, "reference_sha256": None})
    return refs


def _cited_turns(messages) -> list[dict]:
    """Tutor turns that carried citations, in conversation order, without their text."""
    turns = []
    for index, message in enumerate(messages):
        refs = _citation_refs(message.get("citations")) if message.get("role") == "tutor" else []
        if refs:
            kind = message.get("kind")
            turns.append({"message_index": index,
                          "kind": kind if isinstance(kind, str) and re.fullmatch(r"[a-z_]{1,32}", kind) else None,
                          "citations": refs})
    return turns


def _detail(row) -> dict:
    try:
        detail = json.loads(row["detail"] or "{}")
    except (ValueError, TypeError):
        return {}
    if not isinstance(detail, dict):
        return {}
    if row["kind"] == "llm":
        return {k: detail[k] for k in ("tokens_in", "tokens_out")
                if type(detail.get(k)) is int and detail[k] >= 0}
    if row["kind"] != "v02_generation":
        return {}
    visible = {}
    for key in ("context_sha256", "response_sha256", "raw_response_sha256"):
        value = detail.get(key)
        if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value):
            visible[key] = value
    if isinstance(detail.get("reason"), str) and detail["reason"] in GENERATION_REASONS:
        visible["reason"] = detail["reason"]
    for key in ("presentation_only_normalization", "deterministic_incorrect_feedback_added", "raw_expanded_data_used"):
        if type(detail.get(key)) is bool:
            visible[key] = detail[key]
    return visible


def session_trace(tutor, session_id: str) -> dict:
    """Caller supplies teacher authorization and the shared read/publication lock."""
    snap = tutor.graph.get_state({"configurable": {"thread_id": session_id}})
    values = snap.values or {}
    owner = (values.get("session") or {}).get("learner_id")
    if not owner:
        row = tutor.conn.execute("SELECT learner_id FROM learner_session_index WHERE session_id=? AND checkpoint_path=?",
                                 (session_id, tutor.checkpoint_path)).fetchone()
        if row:
            owner = row["learner_id"]
    if owner:
        tutor.ensure_learner_available(owner)
    if not owner or not values:
        raise ToolCallError("NOT_FOUND", "No connected learner conversation was found.")
    rows = tutor.conn.execute("SELECT id,ts,node,role,kind,name,outcome,latency_ms,detail FROM trace_events "
                              "WHERE session_id=? ORDER BY id DESC LIMIT 201", (session_id,)).fetchall()
    events = [{**{key: row[key] for key in ("id", "ts", "node", "role", "kind", "name", "outcome", "latency_ms")},
               "detail": _detail(row)} for row in reversed(rows[:200])]
    messages = values.get("messages") or [{}]
    cited = _cited_turns(messages)
    return {"session_id": session_id, "chapter": (values.get("session") or {}).get("chapter"),
            "registered_hint_mode": getattr(tutor, "registered_hint_mode", "template"),
            "events": events, "truncated": len(rows) > 200,
            "citation_refs": _citation_refs(messages[-1].get("citations")),
            "cited_turns": cited[-CITED_TURN_LIMIT:], "cited_turns_truncated": len(cited) > CITED_TURN_LIMIT}
