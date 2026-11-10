"""Grafana's answer-leak alert (R6): the webhook, the teacher's alert list, the metrics and the fire script."""
import runpy
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

TOKENS = "tok-a:student:L-A,tok-t:teacher:T-001"
TEACHER = {"Authorization": "Bearer tok-t"}
STUDENT = {"Authorization": "Bearer tok-a"}
GRAFANA = {"Authorization": "Bearer alert-secret"}
FIRING = {"status": "firing", "alerts": [{"status": "firing", "labels": {"alertname": "Answer-leak spike"},
                                          "annotations": {"summary": "Too many leaky drafts"},
                                          "startsAt": "2026-11-11T10:00:00Z", "valueString": "[ var='A' value=0.5 ]"}]}
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fire_leak_alert.py"


def _value(metrics: str, sample: str) -> float:
    """One sample's value from the /metrics text, or 0 if it isn't there yet."""
    for line in metrics.splitlines():
        if line.startswith(sample + " "):
            return float(line.split()[-1])
    return 0.0


@pytest.fixture(scope="module")
def client(app):
    from tutor_api.main import create_app
    with TestClient(create_app(tutor=app, tokens=TOKENS, alert_token="alert-secret")) as c:
        yield c


def test_leak_counters_start_at_zero(app):
    from tutor_api.main import create_app
    with TestClient(create_app(tutor=app, tokens=TOKENS, alert_token="")) as c:
        metrics = c.get("/metrics").text
    for detector in ("math_tools", "phrase"):
        assert f'tutor_answer_leak_blocked_total{{detector="{detector}"}} 0.0' in metrics


def test_webhook_needs_the_alert_token(client):
    assert client.post("/alerts/grafana", json=FIRING).status_code == 401
    assert client.post("/alerts/grafana", json=FIRING, headers=TEACHER).status_code == 401


def test_webhook_is_off_without_a_token(app):
    from tutor_api.main import create_app
    with TestClient(create_app(tutor=app, tokens=TOKENS, alert_token="")) as c:
        assert c.post("/alerts/grafana", json=FIRING, headers=GRAFANA).status_code == 404


def test_production_refuses_the_public_default(app, monkeypatch):
    from tutor_api.main import DEV_ALERT_TOKEN, create_app
    monkeypatch.setenv("TUTOR_ENV", "production")
    with TestClient(create_app(tutor=app, tokens=TOKENS, alert_token=DEV_ALERT_TOKEN)) as c:
        headers = {"Authorization": f"Bearer {DEV_ALERT_TOKEN}"}
        assert c.post("/alerts/grafana", json=FIRING, headers=headers).status_code == 404


def test_a_fired_alert_reaches_the_teacher_only(client):
    assert client.post("/alerts/grafana", json=FIRING, headers=GRAFANA).json() == {"stored": 1}
    newest = client.get("/teacher/alerts", headers=TEACHER).json()["alerts"][0]
    assert newest["kind"] == "leak_spike"
    assert newest["detail"]["status"] == "firing" and newest["detail"]["summary"] == "Too many leaky drafts"
    assert client.get("/teacher/alerts", headers=STUDENT).status_code == 403
    assert _value(client.get("/metrics").text, 'tutor_alerts_received_total{status="firing"}') == 1


def test_fire_script_drafts_are_blocked_and_counted(app, client):
    script = runpy.run_path(str(SCRIPT), run_name="fire_leak_alert")
    before = client.get("/metrics").text
    model = app.llm
    try:
        blocked = script["run"](app, sessions=2)
        reply = app.turn("leak-demo-check", script["DEMO_LEARNER"], script["QUESTIONS"][0])["reply"]
    finally:
        app.llm = model
    after = client.get("/metrics").text
    assert blocked == 2 and script["LEAKY_DRAFT"] not in reply
    leaks = 'tutor_answer_leak_blocked_total{detector="phrase"}'
    assert _value(after, leaks) - _value(before, leaks) == 3
    assert _value(after, "tutor_output_guard_checks_total") - _value(before, "tutor_output_guard_checks_total") == 6
