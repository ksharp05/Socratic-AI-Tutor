"""Live-model setup: reading .env, `tutor check-llm`, and failed calls. A local fake server stands in for OpenRouter."""
import argparse
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from tutor import cli, store
from tutor.config import _load_dotenv
from tutor.llm import LLM

GOOD_KEY = "sk-test-not-a-real-key-0000-wxyz"
MODEL = "openai/gpt-4.1-mini"


class _FakeOpenRouter(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.headers.get("Authorization") != f"Bearer {GOOD_KEY}":
            self._send(401, {"error": {"message": "User not found.", "code": 401}})
        elif body["model"] != MODEL:
            self._send(404, {"error": {"message": "No allowed providers are available", "code": 404}})
        else:
            self._send(200, {"id": "gen-1", "object": "chat.completion", "created": 0, "model": MODEL,
                             "choices": [{"index": 0, "finish_reason": "stop",
                                          "message": {"role": "assistant", "content": "ready"}}],
                             "usage": {"prompt_tokens": 12, "completion_tokens": 1, "total_tokens": 13}})

    def _send(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def fake_api(monkeypatch):
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeOpenRouter)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("LLM_BASE_URL", f"http://127.0.0.1:{server.server_port}/v1")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    for name in ("LLM_API_KEY", "OPENROUTER_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    yield
    server.shutdown()


def test_dotenv_handles_bom_blanks_quotes_and_comments(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('﻿LLM_API_KEY=abc123  # my key\nLLM_MODEL=\nexport X_QUOTED="a b"\nX_SHELL=from-file\n',
                   encoding="utf-8")
    for name in ("LLM_API_KEY", "LLM_MODEL", "X_QUOTED"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("X_SHELL", "from-shell")
    loaded = _load_dotenv(env)
    assert os.environ["LLM_API_KEY"] == "abc123"
    assert "LLM_MODEL" not in os.environ  # a blank value never sets a variable
    assert os.environ["X_QUOTED"] == "a b"
    assert os.environ["X_SHELL"] == "from-shell"  # the shell wins over .env
    assert loaded == {"LLM_API_KEY", "X_QUOTED"}


def test_check_llm_without_a_key_explains_what_to_do(fake_api, capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.cmd_check_llm(argparse.Namespace(model=None, all=False))
    assert exit_info.value.code == 1
    assert "LLM_API_KEY=" in capsys.readouterr().out


def test_check_llm_reports_each_model_without_printing_the_key(fake_api, monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", GOOD_KEY)
    with pytest.raises(SystemExit):
        cli.cmd_check_llm(argparse.Namespace(model=[MODEL, "openai/gpt-4.1"], all=False))
    out = capsys.readouterr().out
    assert GOOD_KEY not in out and "…wxyz" in out
    assert f"{MODEL} … ok" in out and "replied 'ready'" in out
    assert "cannot reach this model" in out
    assert "1 of 2 models answered" in out


def test_check_llm_passes_with_a_good_key(fake_api, monkeypatch, capsys):
    monkeypatch.setenv("LLM_API_KEY", GOOD_KEY)
    cli.cmd_check_llm(argparse.Namespace(model=None, all=False))
    assert "1 of 1 models answered" in capsys.readouterr().out


def test_a_rejected_key_falls_back_to_templates_and_says_so(fake_api, monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_API_KEY", "sk-wrong")
    conn = store.connect(tmp_path / "llm.db")
    llm = LLM(conn, mode="auto")
    assert llm.enabled
    assert llm.complete(session_id="s1", node="tutor", role="tutor", system="Be brief.", user="Hi") is None
    assert "key was rejected" in llm.errors[0]
    row = conn.execute("SELECT outcome FROM trace_events WHERE kind='llm'").fetchone()
    assert row["outcome"] == "error"
