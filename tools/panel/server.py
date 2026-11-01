"""Local control panel: run the project's commands from a browser page instead of a terminal.

Start it with `panel.cmd` (Windows) or `python tools/panel/server.py`, then open http://127.0.0.1:8765.

It only ever runs a fixed list of commands, with checked inputs, from the repository root and its `.venv`.
It listens on 127.0.0.1 only, refuses other Host headers, and every action needs the per-start token
embedded in the page, so another website open in the same browser cannot drive it.
Everything runs on the offline stub model except "Check the API key", which makes one live call.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import socket
import subprocess
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BIN = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin")
PY = BIN / ("python.exe" if os.name == "nt" else "python")
TUTOR = BIN / ("tutor.exe" if os.name == "nt" else "tutor")
PORT = int(os.environ.get("PANEL_PORT", "8765"))
TOKEN = secrets.token_urlsafe(24)
DEFAULT_BUILD = ROOT.parent / "Socratic Tutor" / "socratic_tutor_dataset_v2" / "builds" / "v0.10.0"
DEFAULT_PRIVATE = ROOT.parent / "Socratic Tutor" / "heldout_frozen"
ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
SERVICES: dict[str, subprocess.Popen] = {}
DRY_RUNS: set[tuple[int, str, str]] = set()  # (seed, build, private_out) dry runs that passed in this panel session


class Refused(Exception):
    pass


def env(live: bool = False) -> dict:
    e = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", NO_COLOR="1")
    if not live:
        e["TUTOR_LLM"] = "stub"
    return e


def run(args: list, timeout: int = 600, live: bool = False) -> dict:
    start = time.time()
    parts = [str(a).replace(str(BIN) + os.sep, "") for a in args]
    shown = " ".join(a if " " not in a else f'"{a}"' for a in parts)
    try:
        p = subprocess.run([str(a) for a in args], cwd=ROOT, env=env(live), capture_output=True, timeout=timeout,
                           text=True, encoding="utf-8", errors="replace")
        out, code = p.stdout + (("\n" + p.stderr) if p.stderr.strip() else ""), p.returncode
    except subprocess.TimeoutExpired:
        out, code = f"Stopped after {timeout} seconds.", -1
    return {"command": shown, "code": code, "output": ANSI.sub("", out).strip(), "seconds": round(time.time() - start, 1)}


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def key_present() -> bool:
    """Whether .env or the shell sets a key. The value is never read into a response."""
    if os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY"):
        return True
    f = ROOT / ".env"
    if not f.exists():
        return False
    for line in f.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        m = re.match(r"\s*(?:export\s+)?(LLM_API_KEY|OPENROUTER_API_KEY)\s*=\s*(.*)", line)
        if m and m.group(2).split(" #")[0].strip().strip("'\""):
            return True
    return False


def status() -> dict:
    branch = run(["git", "branch", "--show-current"], timeout=10)["output"]
    runs = ROOT / "var" / "runs"
    return {
        "repo": str(ROOT), "branch": branch, "venv": PY.exists(), "key": key_present(),
        "dev_split": (ROOT / "eval" / "dev").is_dir(), "manifest": (ROOT / "eval" / "HELDOUT_MANIFEST.json").exists(),
        "api": port_open(8000), "ui": port_open(8501),
        "runs": len([d for d in runs.iterdir() if d.is_dir()]) if runs.is_dir() else 0,
        "default_build": str(DEFAULT_BUILD), "default_private": str(DEFAULT_PRIVATE),
    }


def seed_of(p: dict) -> int:
    try:
        seed = int(str(p.get("seed", "")).strip())
    except ValueError:
        raise Refused("The seed must be a whole number, for example 20261101. Type the number itself, without < >.")
    if not 0 <= seed < 2**32:
        raise Refused("The seed must be between 0 and 4294967295.")
    return seed


def folder(p: dict, name: str, must_exist: bool) -> Path:
    raw = str(p.get(name, "")).strip().strip('"')
    if not raw:
        raise Refused(f"{name.replace('_', ' ')} is empty.")
    path = Path(raw).resolve()
    if must_exist and not path.is_dir():
        raise Refused(f"Folder not found: {path}")
    return path


def choice(p: dict, name: str, allowed: tuple, default: str) -> str:
    value = str(p.get(name) or default)
    if value not in allowed:
        raise Refused(f"{name} must be one of {', '.join(allowed)}.")
    return value


def ident(p: dict, name: str, pattern: str = r"[A-Za-z0-9_.:-]{1,80}") -> str:
    value = str(p.get(name, "")).strip()
    if not re.fullmatch(pattern, value):
        raise Refused(f"{name.replace('_', ' ')} is missing or has characters that aren't allowed.")
    return value


def freeze(p: dict, real: bool) -> dict:
    seed, build, private = seed_of(p), folder(p, "build", True), folder(p, "private_out", False)
    args = [PY, "-m", "tutor_eval.freeze", "--build", build, "--seed", seed, "--private-out", private]
    key = (seed, str(build), str(private))
    if not real:
        result = run(args + ["--dry-run"])
        if result["code"] == 0:
            DRY_RUNS.add(key)
        return result
    if p.get("confirm") != "FREEZE":
        raise Refused("Type FREEZE in the confirmation box to run the real freeze.")
    if key not in DRY_RUNS:
        raise Refused("Run the dry run first, with this same seed and these same folders, and check its coverage.")
    return run(args + ["--log", "Docs/EXPERIMENT_LOG.md"])


def check_llm(p: dict) -> dict:
    if p.get("confirm") is not True:
        raise Refused("Tick the box to allow one live API call.")
    if not key_present():
        raise Refused("No key found. Put it after LLM_API_KEY= in the .env file in the repository root.")
    return run([TUTOR, "check-llm"], timeout=60, live=True)


def start_service(name: str) -> dict:
    port = {"api": 8000, "ui": 8501}[name]
    if port_open(port):
        return {"command": f"start {name}", "code": 0, "output": f"Already running on port {port}.", "seconds": 0}
    if name == "api":
        args = [PY, "-m", "uvicorn", "tutor_api.main:app", "--host", "127.0.0.1", "--port", "8000"]
    else:
        args = [PY, "-m", "streamlit", "run", "ui/app.py", "--server.port", "8501", "--server.headless", "true",
                "--server.address", "127.0.0.1", "--browser.gatherUsageStats", "false"]
    log = open(ROOT / "var" / f"panel_{name}.log", "w", encoding="utf-8")
    SERVICES[name] = subprocess.Popen([str(a) for a in args], cwd=ROOT, env=env(), stdout=log, stderr=subprocess.STDOUT)
    for _ in range(60):
        if port_open(port):
            return {"command": f"start {name}", "code": 0, "output": f"Started on port {port} (offline stub model).",
                    "seconds": 0}
        if SERVICES[name].poll() is not None:
            break
        time.sleep(0.5)
    tail = (ROOT / "var" / f"panel_{name}.log").read_text(encoding="utf-8", errors="replace")[-3000:]
    return {"command": f"start {name}", "code": 1, "output": "Did not start.\n" + tail, "seconds": 0}


def stop_service(name: str) -> dict:
    proc = SERVICES.pop(name, None)
    if proc and proc.poll() is None:
        proc.terminate()
        return {"command": f"stop {name}", "code": 0, "output": "Stopped.", "seconds": 0}
    return {"command": f"stop {name}", "code": 0,
            "output": "Not started from this panel. Stop it in the terminal that started it.", "seconds": 0}


def list_runs() -> dict:
    runs = ROOT / "var" / "runs"
    items = []
    if runs.is_dir():
        for d in sorted((d for d in runs.iterdir() if d.is_dir()), key=lambda d: d.stat().st_mtime, reverse=True)[:30]:
            items.append({"id": d.name, "report": (d / "report.md").exists(),
                          "when": time.strftime("%d %b %H:%M", time.localtime(d.stat().st_mtime))})
    return {"runs": items}


def read_report(p: dict) -> dict:
    run_id = ident(p, "run_id")
    path = (ROOT / "var" / "runs" / run_id / "report.md").resolve()
    if path.parent.parent != (ROOT / "var" / "runs").resolve() or not path.exists():
        raise Refused("No report for that run.")
    return {"run_id": run_id, "markdown": path.read_text(encoding="utf-8", errors="replace")}


def action(name: str, p: dict) -> dict:
    learner = lambda: choice(p, "learner", ("A", "B"), "A")  # noqa: E731
    actions = {
        "status": lambda: status(),
        "setup": lambda: run([TUTOR, "setup"]),
        "ask": lambda: run([TUTOR, "ask", "--learner", learner(), "--mode", choice(p, "mode", ("practice", "quiz"), "practice"),
                            "--plan"] + (["--session", ident(p, "session")] if p.get("session") else [])
                           + [str(p.get("message", "")).strip()[:500] or "hello"]),
        "learners": lambda: run([TUTOR, "learners"]),
        "tools": lambda: run([TUTOR, "tools"]),
        "trace": lambda: run([TUTOR, "trace", ident(p, "session")]),
        "teacher_propose": lambda: run([TUTOR, "teacher", "propose", "--concept", ident(p, "concept", r"qe0[1-5]")]),
        "teacher_pending": lambda: run([TUTOR, "teacher", "pending"]),
        "teacher_approve": lambda: run([TUTOR, "teacher", "approve", ident(p, "set_id", r"set-[0-9a-f]{4,32}")]),
        "eval": lambda: run([TUTOR, "eval", "--seeds", str(choice(p, "seeds", ("1", "2", "3"), "1"))]
                            + ([] if p.get("defences", True) else ["--no-defences"])),
        "security": lambda: run([PY, "-m", "tutor_eval.security", "--cases", "eval/fixtures/security_smoke.jsonl",
                                 "--name", "panel_security", "--gate"]),
        "validate_sim": lambda: run([PY, "-m", "tutor_eval.validate_sim"]
                                    + ([] if (ROOT / "eval" / "dev").is_dir() else ["--build", DEFAULT_BUILD])),
        "tests": lambda: run([PY, "-m", "pytest", "-q"], timeout=900),
        "freeze_dry": lambda: freeze(p, real=False),
        "freeze_real": lambda: freeze(p, real=True),
        "check_llm": lambda: check_llm(p),
        "start_api": lambda: start_service("api"),
        "start_ui": lambda: start_service("ui"),
        "stop_api": lambda: stop_service("api"),
        "stop_ui": lambda: stop_service("ui"),
        "runs": lambda: list_runs(),
        "report": lambda: read_report(p),
    }
    if name not in actions:
        raise Refused("Unknown action.")
    return actions[name]()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quieter console: one line per action
        pass

    def _host_ok(self) -> bool:
        return self.headers.get("Host", "") in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _send(self, code: int, body: bytes, kind: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, b"Forbidden host", "text/plain")
        if self.path in ("/", "/index.html"):
            page = (HERE / "index.html").read_text(encoding="utf-8").replace("__PANEL_TOKEN__", TOKEN)
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
        self._send(404, b"Not found", "text/plain")

    def do_POST(self):
        if not self._host_ok() or self.headers.get("X-Panel-Token") != TOKEN or self.path != "/api":
            return self._send(403, b'{"error": "forbidden"}', "application/json")
        try:
            body = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", 0)), 20000)) or b"{}")
            name = str(body.get("action", ""))
            print(f"[panel] {name}", flush=True)
            result = action(name, body.get("params") or {})
            code = 200
        except Refused as exc:
            result, code = {"error": str(exc)}, 400
        except Exception as exc:  # report, don't crash the panel
            result, code = {"error": f"{type(exc).__name__}: {exc}"}, 500
        self._send(code, json.dumps(result).encode("utf-8"), "application/json")


def main() -> None:
    if not PY.exists():
        sys.exit(f"No virtual environment at {PY}. Run SETUP.md step 3 first.")
    (ROOT / "var").mkdir(exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"Control panel: {url}  (Ctrl+C to stop)", flush=True)
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in SERVICES.values():
            if proc.poll() is None:
                proc.terminate()


if __name__ == "__main__":
    main()
