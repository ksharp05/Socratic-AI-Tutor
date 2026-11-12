"""Collect timings from 100 local Beta HTTP chat requests and archived live receipts."""
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager, ExitStack
from contextvars import ContextVar
import csv
from functools import wraps
import hashlib
import json
import math
from pathlib import Path
import sys
import platform
import random
from statistics import median
import subprocess
from tempfile import TemporaryDirectory
from time import perf_counter_ns
from unittest.mock import patch
from uuid import uuid4



HERE = Path(__file__).resolve().parent
BETA = HERE.parents[2]
sys.path.insert(0, str(BETA/"src"))

from fastapi.testclient import TestClient
from socrates_beta import dialogue as dialogue_module
from socrates_beta.api import create_app
from socrates_beta.public_index import prepare_public_index
from socrates_beta.repository import Repository
HEADERS = {"X-Socrates-Request": "1"}
ACTIVE = ContextVar("active_trace", default=None)
PARENT = ContextVar("parent_span", default=None)
STAGES = {
    "client": "HTTP client harness",
    "api": "API envelope",
    "routing": "Turn orchestration",
    "screen": "Safety screening",
    "locks": "Lock acquisition and release",
    "reads": "Progress reads",
    "retrieval": "Source retrieval",
    "reply": "Offline reply assembly",
    "writes": "Progress writes",
}


@contextmanager
def span(name, stage):
    active = ACTIVE.get()
    if active is None:
        yield
        return
    row = {"id": str(len(active["spans"])), "parentId": PARENT.get(),
           "name": name, "service": STAGES[stage], "stage": stage,
           "start_ns": perf_counter_ns() - active["start_ns"]}
    active["spans"].append(row)
    token = PARENT.set(row["id"])
    try:
        yield
    finally:
        row["end_ns"] = perf_counter_ns() - active["start_ns"]
        PARENT.reset(token)


def wrap_method(stack, instance, attr, name, stage):
    original = getattr(instance, attr)

    @wraps(original)
    def timed(*args, **kwargs):
        with span(name, stage):
            return original(*args, **kwargs)

    stack.enter_context(patch.object(instance, attr, timed))


def wrap_context(stack, instance, attr, name, stage):
    original = getattr(instance, attr)

    @contextmanager
    def timed(*args, **kwargs):
        context = original(*args, **kwargs)
        stage_name = stage
        if stage is None and ACTIVE.get() is not None:
            parent = PARENT.get()
            parent_stage = ACTIVE.get()["spans"][int(parent)]["stage"] if parent is not None else "reads"
            stage_name = "writes" if parent_stage == "writes" else "reads"
        stage_name = stage_name or "reads"
        with span(name + " enter", stage_name):
            value = context.__enter__()
        try:
            yield value
        except BaseException as exc:
            with span(name + " exit", stage_name):
                if not context.__exit__(type(exc), exc, exc.__traceback__):
                    raise
        else:
            with span(name + " exit", stage_name):
                context.__exit__(None, None, None)

    stack.enter_context(patch.object(instance, attr, timed))


def workload(path):
    blocks = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw or raw.startswith("#"):
            continue
        if raw.startswith("["):
            blocks.append((raw[1:-1], []))
        else:
            blocks[-1][1].append(raw)
    if [len(block[1]) for block in blocks] != [20] * 3 + [4] * 10:
        raise ValueError("Expected 60 standalone prompts and ten four-turn sessions")
    sessions = [(topic, [query]) for topic, queries in blocks[:3] for query in queries] + blocks[3:]
    if len({query for _, queries in sessions for query in queries}) != 100:
        raise ValueError("Expected 100 unique queries")
    random.Random(1401).shuffle(sessions)
    return sessions


def stats(values):
    if not values:
        return {"n": 0}
    ordered = sorted(values)
    return dict(n=len(values), p50=round(median(ordered), 3),
                p95=round(ordered[math.ceil(.95 * len(ordered))-1], 3),
                max=round(ordered[-1], 3))


def trace_summary(spans):
    children = defaultdict(list)
    for item in spans:
        if item["parentId"] is not None:
            children[item["parentId"]].append(item)
    exclusive = Counter()
    root = spans[0]
    for item in spans:
        begin, end = item["start_ns"], item["end_ns"]
        covered = 0
        cursor = begin
        for child in sorted(children[item["id"]], key=lambda row: row["start_ns"]):
            if child["start_ns"] < begin or child["end_ns"] > end:
                raise ValueError("Child span outside its parent")
            left, right = child["start_ns"], child["end_ns"]
            covered += max(0, right-max(cursor, left))
            cursor = max(cursor, right)
        exclusive[item["stage"]] += end - begin - covered
    if sum(exclusive.values()) != root["end_ns"] - root["start_ns"]:
        raise ValueError("Span attribution does not match request duration")
    return {name: round(exclusive[name]/1e6, 6) for name in STAGES}


def historic_live():
    original = json.loads((HERE/"traces-detailed.json").read_text(encoding="utf-8"))
    return original["archived_live"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New directory for timing receipts")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    input_path = HERE/"queries.txt"
    sessions = workload(input_path)
    commit = subprocess.check_output(["git", "-C", str(BETA), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "-C", str(BETA), "status", "--porcelain"], text=True).splitlines()
    run = []
    with TemporaryDirectory(prefix="beta-waterfall-") as tmp, ExitStack() as stack:
        root = Path(tmp)
        index = prepare_public_index(BETA, root/"index")
        repo = Repository(root/"progress.sqlite")
        app = create_app({"app_root": str(BETA), "data_directory": str(root/"app"),
                          "assessment_policy": "reference_checked_beta"},
                         registry=index, repository=repo, testing=True)
        service = app.state.services["dialogue"]
        knowledge = app.state.services["registry"].knowledge()
        for instance, attr, name, stage in (
            (service, "turn", "Dialogue turn", "routing"),
            (service, "_turn", "Prepare and answer turn", "routing"),
            (dialogue_module, "_screen_urgent", "Urgent screening", "screen"),
            (repo, "session", "Load session", "reads"),
            (repo, "dialogue_history", "Read recent history and replay", "reads"),
            (repo, "active_assessment", "Check session assessment", "reads"),
            (repo, "open_check", "Check profile assessment", "reads"),
            (repo, "save_turn", "Save turn and session state", "writes"),
            (repo, "observe", "Save learning observation", "writes"),
            (dialogue_module, "broad_topic", "Resolve broad topic", "retrieval"),
            (knowledge, "search", "Search textbook index", "retrieval"),
            (service, "fallback", "Assemble source reply", "reply"),
        ):
            wrap_method(stack, instance, attr, name, stage)
        wrap_context(stack, repo, "connect", "Progress connection", None)
        wrap_context(stack, repo, "owner_guard", "Profile lock", "locks")
        wrap_context(stack, service, "session_lock", "Session lock", "locks")

        async def traced_app(scope, receive, send):
            if scope["type"] == "http" and scope["path"] == "/api/chat":
                with span("POST /api/chat", "api"):
                    return await app(scope, receive, send)
            return await app(scope, receive, send)

        def make_session(client):
            response = client.post("/api/sessions", headers=HEADERS,
                                   json={"grade": 10, "subject": "Mathematics", "title": "Synthetic latency run"})
            response.raise_for_status()
            return response.json()["id"]

        def post_turn(client, sid, query):
            return client.post("/api/chat", headers=HEADERS,
                               json={"session_id": sid, "text": query, "request_id": uuid4().hex})

        with TestClient(traced_app) as client:
            sid = make_session(client)
            for query in ("What is a quadratic equation?", "What is the common difference?", "Explain trigonometry."):
                post_turn(client, sid, query).raise_for_status()
            for session_number, (topic, queries) in enumerate(sessions, 1):
                sid = make_session(client)
                for turn_index, query in enumerate(queries, 1):
                    context = {"start_ns": perf_counter_ns(), "spans": []}
                    token = ACTIVE.set(context)
                    try:
                        with span("Local chat round trip", "client"):
                            response = post_turn(client, sid, query)
                    finally:
                        ACTIVE.reset(token)
                    response.raise_for_status()
                    result = response.json()
                    spans = context["spans"]
                    if not any(item["stage"] == "api" for item in spans):
                        raise ValueError("ASGI trace context did not propagate")
                    stage_ms = trace_summary(spans)
                    origin = spans[0]["start_ns"]
                    cleaned = [
                        {key: item[key] for key in ("id", "parentId", "name", "service", "stage")} |
                        {"startMs": round((item["start_ns"]-origin)/1e6, 6),
                         "durationMs": round((item["end_ns"]-item["start_ns"])/1e6, 6)}
                        for item in spans
                    ]
                    run.append(dict(id=f"Q{len(run)+1:03}", topic=topic, session=session_number, turn=turn_index,
                                    query=query, status=result["provider_status"], move=result["move"],
                                    citations=len(result["citations"]), elapsed_ms=cleaned[0]["durationMs"],
                                    api_ms=next(item["durationMs"] for item in cleaned if item["stage"] == "api"),
                                    stage_ms=stage_ms, spans=cleaned))
    if len(run) != 100:
        raise ValueError("Incomplete benchmark")
    slowest = sorted(run, key=lambda row: row["elapsed_ms"], reverse=True)[:10]
    stages = {}
    for name, label in STAGES.items():
        numbers = [row["stage_ms"][name] for row in run]
        stages[name] = {"label": label, **stats(numbers),
                        "mean": round(sum(numbers)/len(numbers), 3),
                        "tail_mean": round(sum(row["stage_ms"][name] for row in slowest)/len(slowest), 3)}
    coverage = dict(Counter(row["status"] for row in run))
    report = dict(
        method="Local Beta ASGI via TestClient, SQLite, public reference index, offline source mode, "
               "serial requests. Three warmups excluded. Session setup outside timing. No network.",
        platform=platform.platform(), python=platform.python_version(), git_commit=commit, git_status=status,
        input_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(),
        benchmark_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        source_sha256={str(path.relative_to(BETA)):hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in sorted((BETA/"src/socrates_beta").glob("*.py"))},
        total_ms=stats([row["elapsed_ms"] for row in run]), api_ms=stats([row["api_ms"] for row in run]),
        by_turn_type={label: stats([row["elapsed_ms"] for row in run if (row["turn"] == 1) == starter])
                      for label, starter in (("first", True), ("followup", False))},
        by_topic={topic: stats([row["elapsed_ms"] for row in run if row["topic"] == topic])
                  for topic in sorted({row["topic"] for row in run})},
        coverage=coverage, with_citations=sum(row["citations"] > 0 for row in run),
        stages=stages, archived_live=historic_live(), queries=run)
    with (args.out/"traces-detailed.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    fields = ["id", "topic", "session", "turn", "query", "status", "move", "citations", "elapsed_ms", "api_ms"]
    with (args.out/"timings-detailed.csv").open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields+list(STAGES))
        writer.writeheader()
        writer.writerows({**{key: row[key] for key in fields}, **row["stage_ms"]} for row in run)
    print(json.dumps({k: v for k, v in report.items() if k in
                      ("total_ms", "api_ms", "by_turn_type", "coverage", "with_citations", "stages", "archived_live")},
                     indent=2))


if __name__ == "__main__":
    main()
