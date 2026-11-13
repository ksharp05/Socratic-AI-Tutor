"""R4 task A6 (team plan, 13 Nov): four small fixes from the app-security review, one test each.

Offline: no model, no key, no database. The OpenAPI check reads api.py's own source, so it does not need the
public index or a browser secret.
"""
import ast
import threading
import time
from pathlib import Path
from types import SimpleNamespace

from socrates_beta import maths
from socrates_beta.safety import promises_secrecy, reply_for

API = Path(__file__).resolve().parents[1] / "src" / "socrates_beta" / "api.py"


def test_secrecy_promise_with_curly_apostrophes_is_caught():
    for reply in ["I won\u2019t tell anyone, I promise.", "I\u2019ll keep it secret.",
                  "I promise I won\u2019t tell anybody", "I won't tell anyone"]:
        assert promises_secrecy(reply), reply
    # The fixed secrecy reply itself, and an honest refusal with a curly apostrophe, must not count as a promise.
    assert not promises_secrecy(reply_for("secrecy", "en"))
    assert not promises_secrecy("I can\u2019t promise to keep a secret if someone\u2019s safety is involved.")


def _checker(grade):
    checker = object.__new__(maths.CheckedMaths)
    checker.items = {"q": {"answer_contract": {"allowed_kinds": ["boolean"]}}}
    checker.keys = {"q": {"kind": "boolean", "value": True}}
    checker.lock = threading.RLock()
    checker.core = SimpleNamespace(grade=grade)
    return checker


def test_maths_checker_has_a_wall_clock_limit(monkeypatch):
    monkeypatch.setattr(maths, "GRADE_SECONDS", 0.2)
    slow = _checker(lambda typed, key: time.sleep(3) or {"status": "correct", "correct": True})
    started = time.monotonic()
    result = slow.grade("q", "yes")
    assert time.monotonic() - started < 1.5
    assert result["status"] == "invalid_response" and result["correct"] is False
    # A normal answer still grades, and the result passes through unchanged.
    fast = _checker(lambda typed, key: {"status": "correct", "correct": True, "typed": typed})
    assert fast.grade("q", "yes")["status"] == "correct"


def test_openapi_schema_is_off_outside_tests():
    tree = ast.parse(API.read_text(encoding="utf-8-sig"))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "FastAPI"]
    assert calls, "create_app builds a FastAPI app"
    for call in calls:
        keywords = {k.arg: k.value for k in call.keywords}
        assert "openapi_url" in keywords, "FastAPI() would publish /openapi.json by default"
        expression = compile(ast.Expression(keywords["openapi_url"]), str(API), "eval")
        assert eval(expression, {}, {"testing": False}) is None
        assert eval(expression, {}, {"testing": True})


def test_session_locks_are_bounded():
    from socrates_beta.dialogue import SESSION_LOCK_STRIPES, DialogueService

    service = DialogueService(repo=None, registry=None)
    locks = {id(service.session_lock(f"session-{i}")) for i in range(5000)}
    assert len(locks) <= SESSION_LOCK_STRIPES
    same = service.session_lock("session-42")
    assert same is service.session_lock("session-42")
    with same:
        with same:  # re-entrant, as the turn path may re-enter
            pass
