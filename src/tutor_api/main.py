"""FastAPI service around TutorApp. Run with: uvicorn tutor_api.main:app

This module wraps TutorApp turns, recovery, learner data requests and teacher approval. TutorApp is not thread-safe, so every call into it
holds one lock; a single API process serves one turn at a time, which is enough for the demo.

Endpoints and tokens are documented in Docs/deploy/README.md.
"""
from __future__ import annotations

import hmac
import json
import os
import re
import threading
import time
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from filelock import Timeout
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from tutor import guards, store
from tutor.toolbus import CallContext, ToolCallError

from .auth import Principal, load_tokens, lookup
from .metrics import Metrics

SESSION_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
RESERVED_PREFIXES = ("qs-",)  # approval-graph threads share the checkpointer
LEAK_ALERT = "Answer-leak spike"  # the title of Grafana's answer-leak alert rule
DEV_ALERT_TOKEN = "dev-grafana-alerts"  # the public development default; refused when TUTOR_ENV=production
ERROR_STATUS = {"NOT_FOUND": 404, "INVALID_INPUT": 422, "FORBIDDEN": 403, "BUDGET": 429, "BUSY": 503, "GONE": 410, "CONFLICT": 409}


# ---------------------------------------------------------------------- request bodies
# Bodies never carry a role or a learner ID: extra fields are ignored, and identity comes from the token.
class ChatIn(BaseModel):
    session_id: str | None = Field(default=None, description="Continue this session; omit to start a new one")
    text: str = Field(min_length=1, max_length=4000)
    mode: Literal["practice", "quiz"] = "practice"
    chapter: Literal["quadratic_equations", "arithmetic_progressions", "trigonometry"] | None = None


class ResumeIn(BaseModel):
    session_id: str


class ProposeIn(BaseModel):
    concept_id: str = Field(min_length=1, max_length=32)
    mode: Literal["practice", "quiz", "diagnostic"] = "practice"


class EditIn(BaseModel):
    question_ids: list[str] = Field(min_length=1, max_length=20)


class RejectIn(BaseModel):
    reason: str = Field(default="", max_length=500)


class TryPublishIn(BaseModel):
    token: str = Field(min_length=1, max_length=512)


class GrafanaAlert(BaseModel):
    status: str = Field(default="firing", max_length=16)
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    startsAt: str | None = Field(default=None, max_length=64)
    valueString: str | None = Field(default=None, max_length=1000)


class GrafanaWebhookIn(BaseModel):
    """The part of Grafana's webhook body the API keeps; other fields are ignored."""
    alerts: list[GrafanaAlert] = Field(default_factory=list, max_length=50)


# ---------------------------------------------------------------------- startup helpers
def _seed_if_needed(tokens: dict[str, Principal]) -> None:
    """Seed the demo learners into an empty database, and add any learner a student token names.

    Unlike `tutor setup`, this never deletes var/ (in Docker it is a mounted volume), and it never
    resets an existing database.
    """
    from tutor import store
    from tutor.config import db_path
    from tutor.seed import DEMO_LEARNERS, seed_learner

    conn = store.connect(db_path("tutor.db"))
    try:
        if not conn.execute("SELECT 1 FROM learners LIMIT 1").fetchone():
            for lid, spec in DEMO_LEARNERS.items():
                seed_learner(conn, lid, spec)
        for p in tokens.values():
            if p.role == "student" and not conn.execute("SELECT 1 FROM learners WHERE learner_id=?",
                                                        (p.subject_id,)).fetchone():
                seed_learner(conn, p.subject_id, {"alias": p.subject_id})
    finally:
        conn.close()


def configured_tutor_class():
    """Explicit opt-in; choosing this class does not authorize a provider transfer."""
    setting = os.environ.get("TUTOR_CONTEXTUAL_HINTS", "0")
    if setting == "0":
        from tutor.app import TutorApp
        return TutorApp
    if setting == "1":
        from v02_integration.runtime import ContextualPreviewTutor
        return ContextualPreviewTutor
    raise RuntimeError("TUTOR_CONTEXTUAL_HINTS must be 0 or 1")


def create_app(tutor=None, tokens: str | None = None, alert_token: str | None = None) -> FastAPI:
    """Build the API. Pass `tutor` to wrap an existing TutorApp (tests); otherwise one is created at startup."""
    token_map = load_tokens(tokens)
    alert_token = os.environ.get("TUTOR_ALERT_TOKEN", "") if alert_token is None else alert_token
    if os.environ.get("TUTOR_ENV") == "production" and alert_token == DEV_ALERT_TOKEN:
        alert_token = ""  # never accept the public default outside development
    metrics = Metrics()
    lock = threading.RLock()
    state: dict = {"tutor": tutor, "owned": tutor is None, "trace_id": 0, "beta": None}
    require_beta = os.environ.get("TUTOR_REQUIRE_BETA") == "1"

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if state["tutor"] is None:
            tutor_class = configured_tutor_class()
            if os.environ.get("TUTOR_API_SEED", "1") != "0":
                _seed_if_needed(token_map)
            state["tutor"] = tutor_class()
        state["trace_id"] = _max_trace_id()
        yield
        if state["owned"] and state["tutor"] is not None:
            state["tutor"].close()
            state["tutor"] = None

    api = FastAPI(title="Socratic Tutor API", version="0.1.0", lifespan=lifespan)
    bearer = HTTPBearer(auto_error=False)

    # ------------------------------------------------------------------ helpers
    def _tutor():
        if state["tutor"] is None:
            raise HTTPException(503, "tutor is starting")
        return state["tutor"]

    def _max_trace_id() -> int:
        row = state["tutor"].conn.execute("SELECT COALESCE(MAX(id), 0) AS m FROM trace_events").fetchone()
        return row["m"]

    def _sync_trace() -> None:
        """Feed trace rows written since the last call into the metrics. Call with the lock held."""
        rows = state["tutor"].conn.execute("SELECT * FROM trace_events WHERE id > ? ORDER BY id",
                                           (state["trace_id"],)).fetchall()
        if rows:
            state["trace_id"] = rows[-1]["id"]
            metrics.observe_trace(rows)

    def _call(fn, *args, **kwargs):
        with lock:
            try:
                return fn(*args, **kwargs)
            except ToolCallError as exc:
                raise HTTPException(ERROR_STATUS.get(exc.code, 400), str(exc)) from exc
            finally:
                _sync_trace()

    def _deny(status: int, detail: str):
        metrics.api_denied.labels(str(status)).inc()
        headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
        raise HTTPException(status, detail, headers=headers)

    def principal(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Principal:
        if creds is None or creds.scheme.lower() != "bearer":
            _deny(401, "missing bearer token")
        found = lookup(token_map, creds.credentials)
        if found is None:
            _deny(401, "unknown token")
        return found

    def student(p: Principal = Depends(principal)) -> Principal:
        if p.role != "student":
            _deny(403, "only students can chat")
        return p

    def teacher(p: Principal = Depends(principal)) -> Principal:
        if not p.is_teacher:
            _deny(403, "teacher only")
        return p

    def _check_session(session_id: str, learner_id: str) -> None:
        _call(_tutor().ensure_learner_available, learner_id)
        if not SESSION_ID.match(session_id) or session_id.startswith(RESERVED_PREFIXES) or session_id in {"api", "teacher"}:
            raise HTTPException(422, "invalid session_id")
        snap = _tutor().graph.get_state({"configurable": {"thread_id": session_id}})
        values = (snap.values or {}) if snap else {}
        if values:
            owner = (values.get("session") or {}).get("learner_id")
            if owner != learner_id:
                _deny(403, "this session belongs to someone else")

    def _active_graph_session(learner_id: str):
        """Reconcile a persisted reservation with the graph checkpoint under the publication lock."""
        row = _tutor().conn.execute("SELECT session_id FROM graph_session_leases WHERE learner_id=?",
                                   (learner_id,)).fetchone()
        if not row:
            return None
        sid = row["session_id"]
        snap = _tutor().graph.get_state({"configurable": {"thread_id": sid}})
        if not (snap.next or (snap.values or {}).get("quiz")):
            _tutor().conn.execute("DELETE FROM graph_session_leases WHERE learner_id=? AND session_id=?",
                                  (learner_id, sid))
            return None
        return {"session_id": sid, "quiz_active": bool((snap.values or {}).get("quiz")),
                "interrupted": bool(snap.next)}

    def _reserve_graph_session(learner_id: str, session_id: str, *, resume: bool = False):
        current = _active_graph_session(learner_id)
        if current and current["session_id"] != session_id:
            raise HTTPException(409, "Finish or recover your existing connected session before starting another.")
        if current and current["interrupted"] and not resume:
            raise HTTPException(409, "Recover the interrupted turn before sending another message.")
        # Reserve before graph invocation. A crash leaves a marker to reconcile on recovery.
        _tutor().conn.execute("INSERT OR REPLACE INTO graph_session_leases VALUES (?,?)", (learner_id, session_id))

    def _finish_graph_session(learner_id: str):
        _active_graph_session(learner_id)  # retain only an active quiz or interrupted checkpoint

    def _run_turn(p: Principal, body: ChatIn) -> dict:
        session_id = body.session_id or f"s-{p.subject_id}-{uuid.uuid4().hex[:8]}"
        with lock, _tutor().bus.publication_lock:
            _check_session(session_id, p.subject_id)
            prior = _tutor().graph.get_state({"configurable": {"thread_id": session_id}})
            prior_session = (prior.values or {}).get("session")
            prior_chapter = (prior_session or {}).get("chapter", "quadratic_equations")
            if prior_session and body.chapter is not None and body.chapter != prior_chapter:
                if guards.screen_input(body.text)["distress"]:
                    return {"session_id": session_id, "learner_id": p.subject_id, "mode": body.mode,
                            "chapter": prior_chapter, "reply": guards.HANDOFF_MESSAGE, "route": "handoff",
                            "plan": None, "citations": [], "tools": [], "quiz_active": None,
                            "persistence": "not_saved_urgent"}
                raise HTTPException(409, "Start a new conversation to change chapters.")
            chapter = prior_chapter if prior_session else (body.chapter or "quadratic_equations")
            existing = _active_graph_session(p.subject_id)
            if existing and existing["session_id"] != session_id and guards.screen_input(body.text)["distress"]:
                return {"session_id": session_id, "learner_id": p.subject_id, "mode": body.mode,
                        "reply": guards.HANDOFF_MESSAGE, "route": "handoff", "plan": None,
                        "citations": [], "tools": [], "quiz_active": None, "chapter": chapter, "persistence": "not_saved_urgent"}
            _reserve_graph_session(p.subject_id, session_id)
            started = time.perf_counter()
            try:
                result = _call(_tutor().turn, session_id, p.subject_id, body.text, mode=body.mode, chapter=chapter)
            except HTTPException:
                raise
            except Exception:
                metrics.errors.inc()
                raise
            route = result.get("route") or "unknown"
            metrics.latency.labels(route).observe(time.perf_counter() - started)
            metrics.turns.labels(body.mode, route).inc()
            metrics.replies.labels(body.mode).inc()
            if route == "handoff":
                metrics.handoffs.inc()
            snap = _tutor().graph.get_state({"configurable": {"thread_id": session_id}})
            quiz_active = bool((snap.values or {}).get("quiz"))
            _finish_graph_session(p.subject_id)
        return {"session_id": session_id, "learner_id": p.subject_id, "mode": body.mode, "chapter": chapter, **result,
                "quiz_active": quiz_active}

    @api.exception_handler(Timeout)
    async def _publication_busy(_: Request, exc: Timeout):
        return JSONResponse({"detail": "The tutor is busy; please try again."}, status_code=503)

    @api.exception_handler(HTTPException)
    async def _http_error(_: Request, exc: HTTPException):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)

    # ------------------------------------------------------------------ public
    @api.get("/health")
    def health() -> dict:
        t = state["tutor"]
        return {"status": "ok" if t is not None else "starting", "llm": t.llm.label if t is not None else None,
                "registered_hint_mode": getattr(t, "registered_hint_mode", "template"),
                "model_enabled": bool(t is not None and t.llm.enabled)}

    @api.get("/health/ready")
    def readiness() -> JSONResponse:
        """Check local graph state and the mounted beta's registered index, without revealing paths."""
        checks = {"graph": "unavailable", "beta": "not_configured"}
        try:
            with lock:
                t = state["tutor"]
                if t is None:
                    raise RuntimeError("graph is starting")
                t.conn.execute("SELECT 1").fetchone()
                t.checkpointer.conn.execute("SELECT 1").fetchone()
                if not {"quadratic_equations", "arithmetic_progressions", "trigonometry"} <= {c.get("chapter") for c in t.cards.values()}:
                    raise RuntimeError("missing chapter references")
                checks["graph"] = "ready"
                beta = state["beta"]
                if beta is None:
                    if require_beta:
                        checks["beta"] = "unavailable"
                        raise RuntimeError("beta not configured")
                else:
                    checks["beta"] = "unavailable"
                    knowledge = beta.state.services["registry"].knowledge()
                    with knowledge.connect() as conn:
                        if conn.execute("SELECT count(*) FROM passages").fetchone()[0] < 1:
                            raise RuntimeError("empty beta index")
                    checks["beta"] = "ready"
        except Exception:
            return JSONResponse({"status": "not_ready", "components": checks}, status_code=503)
        return JSONResponse({"status": "ready", "components": checks})

    @api.get("/metrics")
    def metrics_endpoint() -> Response:
        if state["tutor"] is not None:
            with lock:
                _sync_trace()
                row = state["tutor"].conn.execute("SELECT COUNT(*) AS n FROM proposals WHERE status='pending'").fetchone()
                metrics.pending.set(row["n"])
        return Response(generate_latest(metrics.registry), media_type=CONTENT_TYPE_LATEST)

    @api.post("/alerts/grafana")
    def grafana_alert(body: GrafanaWebhookIn, creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
        """Grafana's contact point posts here. Each alert goes into the alerts table, which teachers read."""
        if not alert_token:
            raise HTTPException(404, "Not Found")
        if creds is None or not hmac.compare_digest(creds.credentials.encode(), alert_token.encode()):
            _deny(401, "unknown alert token")
        with lock:
            for a in body.alerts:
                kind = "leak_spike" if a.labels.get("alertname") == LEAK_ALERT else "grafana"
                detail = {"status": a.status, "alertname": a.labels.get("alertname", "")[:100],
                          "summary": a.annotations.get("summary", "")[:300], "starts_at": a.startsAt,
                          "values": (a.valueString or "")[:300]}
                store.alert(_tutor().conn, kind, None, detail)
                metrics.alerts.labels("resolved" if a.status == "resolved" else "firing").inc()
        return {"stored": len(body.alerts)}

    @api.get("/me")
    def me(p: Principal = Depends(principal)) -> dict:
        return {"role": p.role, "id": p.subject_id}

    # ------------------------------------------------------------------ student chat
    @api.post("/chat")
    def chat(body: ChatIn, p: Principal = Depends(student)) -> dict:
        return _run_turn(p, body)

    @api.post("/chat/stream")
    def chat_stream(body: ChatIn, p: Principal = Depends(student)) -> StreamingResponse:
        result = _run_turn(p, body)  # the POC graph is not token-streaming yet; the reply is chunked afterwards

        def events():
            def sse(event: str, data) -> str:
                return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            words = re.findall(r"\S+\s*|\s+", result["reply"])
            for i in range(0, len(words), 4):
                yield sse("token", {"text": "".join(words[i:i + 4])})
            if result.get("plan"):
                yield sse("plan", result["plan"])
            for c in result["citations"]:
                yield sse("citation", c)
            yield sse("done", {k: v for k, v in result.items() if k != "plan"})

        return StreamingResponse(events(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @api.post("/chat/resume")
    def chat_resume(body: ResumeIn, p: Principal = Depends(student)) -> dict:
        with lock, _tutor().bus.publication_lock:
            _check_session(body.session_id, p.subject_id)
            _reserve_graph_session(p.subject_id, body.session_id, resume=True)
            out = _call(_tutor().resume, body.session_id)
            _finish_graph_session(p.subject_id)
        return {"session_id": body.session_id, "resumed": out is not None, **(out or {})}

    @api.post("/chat/leave")
    def leave_quiz(body: ResumeIn, p: Principal = Depends(student)) -> dict:
        with lock, _tutor().bus.publication_lock:
            _check_session(body.session_id, p.subject_id)
            current = _active_graph_session(p.subject_id)
            if current and current["session_id"] != body.session_id:
                raise HTTPException(409, "Finish or recover your existing connected session first.")
            snap = _tutor().graph.get_state({"configurable": {"thread_id": body.session_id}})
            if snap.next:
                raise HTTPException(409, "Recover the interrupted turn before leaving the quiz.")
            if not (snap.values or {}).get("quiz"):
                return {"session_id": body.session_id, "ended": False}
            text = "Quiz ended. No score was recorded for this unfinished quiz."
            _tutor().graph.update_state({"configurable": {"thread_id": body.session_id}},
                {"quiz": None, "draft": None, "messages": [{"role": "tutor", "content": text, "kind": "info"}]},
                as_node="respond")
            _finish_graph_session(p.subject_id)
            return {"session_id": body.session_id, "ended": True, "reply": text}

    @api.get("/chat/active")
    def active_chat(p: Principal = Depends(student)) -> dict:
        with lock, _tutor().bus.publication_lock:
            _call(_tutor().ensure_learner_available, p.subject_id)
            current = _active_graph_session(p.subject_id)
        return current or {"session_id": None, "quiz_active": False, "interrupted": False}

    @api.get("/chat/{session_id}/history")
    def chat_history(session_id: str, p: Principal = Depends(student)) -> dict:
        with lock, _tutor().bus.publication_lock:
            _check_session(session_id, p.subject_id)
            messages = _call(_tutor().history, session_id)
            snap = _tutor().graph.get_state({"configurable": {"thread_id": session_id}})
        return {"session_id": session_id, "messages": messages,
                "chapter": ((snap.values or {}).get("session") or {}).get("chapter", "quadratic_equations"),
                "quiz_active": bool((snap.values or {}).get("quiz")), "interrupted": bool(snap.next)}

    # ------------------------------------------------------------------ teacher
    @api.get("/teacher/proposals")
    def list_proposals(_: Principal = Depends(teacher)) -> dict:
        with lock:
            rows = _tutor().conn.execute("SELECT set_id, concept_id, status, revision, payload_sha256, updated_at "
                                         "FROM proposals ORDER BY updated_at DESC").fetchall()
        return {"proposals": [dict(r) for r in rows]}

    @api.post("/teacher/proposals")
    def propose(body: ProposeIn, _: Principal = Depends(teacher)) -> dict:
        with lock:
            out = _call(_tutor().propose_set, body.concept_id, body.mode)
            return {**out, "proposal": _call(_tutor().proposal, out["set_id"])}

    @api.get("/teacher/proposals/{set_id}")
    def get_proposal(set_id: str, _: Principal = Depends(teacher)) -> dict:
        return _call(_tutor().proposal, set_id)

    @api.post("/teacher/proposals/{set_id}/approve")
    def approve(set_id: str, p: Principal = Depends(teacher)) -> dict:
        return _call(_tutor().decide, set_id, "approve", p.subject_id)

    @api.post("/teacher/proposals/{set_id}/edit")
    def edit(set_id: str, body: EditIn, p: Principal = Depends(teacher)) -> dict:
        return _call(_tutor().decide, set_id, "edit", p.subject_id, question_ids=body.question_ids)

    @api.post("/teacher/proposals/{set_id}/reject")
    def reject(set_id: str, body: RejectIn | None = None, p: Principal = Depends(teacher)) -> dict:
        return _call(_tutor().decide, set_id, "reject", p.subject_id, reason=(body.reason if body else ""))

    @api.post("/teacher/proposals/{set_id}/try-publish")
    def try_publish(set_id: str, body: TryPublishIn, p: Principal = Depends(teacher)) -> dict:
        return _call(_tutor().try_publish, set_id, body.token, p.subject_id)

    @api.get("/teacher/items")
    def candidate_items(concept_id: str | None = None, _: Principal = Depends(teacher)) -> dict:
        """The development practice pool (IDs and prompts only), for editing a proposal."""
        from tutor.question_catalog import graph_items
        items = [{"question_id": q["question_id"], "prompt": q["prompt"], "concept_ids": q["problem"]["concept_ids"],
                  "allowed_modes": q["mode_policy"]["allowed_modes"], "review_status": q.get("review_status"),
                  "authorship": q.get("authorship")} for q in graph_items()]
        if concept_id:
            items = [i for i in items if concept_id in i["concept_ids"]]
        return {"items": items}

    @api.get("/teacher/sessions/{session_id}/trace")
    def teacher_session_trace(session_id: str, _: Principal = Depends(teacher)) -> dict:
        if not SESSION_ID.fullmatch(session_id) or session_id.startswith(RESERVED_PREFIXES) or session_id in {"api", "teacher"}:
            raise HTTPException(422, "invalid session_id")
        from .traces import session_trace
        with lock, _tutor().bus.publication_lock:
            return _call(session_trace, _tutor(), session_id)

    @api.get("/teacher/alerts")
    def teacher_alerts(_: Principal = Depends(teacher)) -> dict:
        """System alerts from Grafana (not about one learner), newest first."""
        with lock:
            rows = _tutor().conn.execute("SELECT ts, kind, detail FROM alerts WHERE learner_id IS NULL "
                                         "ORDER BY id DESC LIMIT 50").fetchall()
        return {"alerts": [{"ts": r["ts"], "kind": r["kind"], "detail": json.loads(r["detail"] or "{}")} for r in rows]}

    # ------------------------------------------------------------------ learners
    @api.get("/learners")
    def list_learners(_: Principal = Depends(teacher)) -> dict:
        with lock, _tutor().bus.publication_lock:
            rows = _tutor().conn.execute("SELECT learner_id, alias FROM learners WHERE learner_id NOT IN "
                                         "(SELECT learner_id FROM learner_deletions) ORDER BY learner_id").fetchall()
        return {"learners": [dict(r) for r in rows]}

    @api.get("/learners/{learner_id}")
    def learner_overview(learner_id: str, p: Principal = Depends(principal)) -> dict:
        if not p.is_teacher and p.subject_id != learner_id:
            _deny(403, "you may only view your own record")
        with lock, _tutor().bus.publication_lock:
            _call(_tutor().ensure_learner_available, learner_id)
            model = _call(_tutor().bus.call, CallContext(session_id="api", learner_id=learner_id, node="api"),
                          "study_planner", "learner-store", "read_learner", {"learner_id": learner_id})
            # Alert details are a teacher workflow. Students may read their own
            # learner model, but the local teacher inbox is not exposed to them.
            alerts = ([{**dict(r), "detail": json.loads(r["detail"] or "{}")} for r in _tutor().conn.execute(
                "SELECT ts, kind, learner_id, detail FROM alerts WHERE learner_id=? ORDER BY id", (learner_id,))]
                      if p.is_teacher else [])
        result = {"learner_id": learner_id, "mastery": model["mastery"], "misconceptions": model["misconceptions"],
                  "plan": model.get("plan"), "topic_plans": model.get("topic_plans", {}), "alerts": alerts,
                  "revisit_summary": model.get("revisit_summary", {"total": 0, "by_chapter": {}, "has_more": False})}
        if p.is_teacher:
            # This overview does not publish or resume questions. Learners see
            # counts only; teacher details exclude internal content hashes.
            fields = ("question_ref", "chapter", "reason", "created_at")
            result["revisit_items"] = [{key: row[key] for key in fields}
                                       for row in model.get("revisit_items", [])]
        return result

    @api.delete("/learners/{learner_id}")
    def forget_learner(learner_id: str, p: Principal = Depends(teacher)) -> dict:
        return _call(_tutor().forget_learner, learner_id, p.subject_id)

    if beta_config := os.environ.get('TUTOR_BETA_CONFIG'):
        from .beta import mount_beta
        state["beta"] = mount_beta(api, beta_config, tutor_provider=_tutor)

    return api


app = create_app()
