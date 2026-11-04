"""Evaluation harness (R5): simulated students talk to one tutor configuration; code scores everything it can.

    python -m tutor_eval.harness --config eval/configs/dev_smoke.toml [--log Docs/EXPERIMENT_LOG.md]

Each run writes var/runs/<run_id>/: manifest.json (config, hashes, models, seeds, counts, cost), sessions.jsonl
(every session and turn) and report.md. Held-out data is refused unless --heldout is given and the
pre-registration is frozen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import tomllib
import uuid
from pathlib import Path

from tutor import store
from tutor.config import ROOT, SETTINGS, VAR_DIR
from tutor.seed import seed_learner
from tutor.setup_content import load
from tutor_eval import arms, leakcheck, metrics, simulator, tables

DEV = "development"
PRICES_DEFAULT = {"openai/gpt-4.1-mini": (0.40, 1.60)}  # USD per million tokens (in, out); config can override


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_run_dir(base: Path, name: str, started: str) -> tuple[str, Path]:
    """Create a unique run directory without overwriting earlier evidence."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name):
        raise ValueError("Invalid evaluation run name")
    base.mkdir(parents=True, exist_ok=True)
    for _ in range(5):
        run_id = f"{name}-{started}-{uuid.uuid4().hex[:12]}"
        directory = base / run_id
        try:
            directory.mkdir()
            return run_id, directory
        except FileExistsError:
            continue
    raise FileExistsError("Unable to allocate a unique evaluation run directory")


def fixture_input_hashes() -> dict[str, str]:
    """Identify the public and synthetic content used by the development fixture."""
    paths = ("content/poc/practice.json", "content/poc/cards.json",
             "content/dataset-v0.10.0/practice_questions.jsonl", "content/dataset-v0.10.0/corpus.jsonl",
             "content/dataset-v0.10.0/concepts.jsonl", "content/dataset-v0.10.0/misconceptions.jsonl",
             "content/milestone2_dev/practice_items.json", "content/milestone2_dev/quiz_items.json", "content/milestone2_dev/chapter_quiz_items.json")
    return {name: sha256_file(ROOT / name) for name in paths}


def _rows(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == ".jsonl" else json.loads(text)


def load_data(cfg: dict) -> dict:
    """Students, quiz pairs (with both items) and which pairs each student takes."""
    d = cfg["data"]
    resolve = lambda name: ROOT / os.path.expandvars(d[name])
    students = _rows(resolve("students"))
    if d.get("only_students"):
        students = [s for s in students if s["student_id"] in d["only_students"]]
    pairs = _rows(resolve("quiz_pairs"))
    if pairs and "pre" not in pairs[0]:  # eval/dev layout: items live in their own file
        items = {i["question_id"]: i for i in _rows(resolve("quiz_items"))}
        pairs = [{"pair_id": p["pair_id"], "pre": items[p["pre_id"]], "post": items[p["post_id"]],
                  "partition": p.get("evaluation_partition", DEV)} for p in pairs]
    assignments = {a["student_id"]: a["pair_ids"] for a in _rows(resolve("assignments"))} if d.get("assignments") else {}
    files = [resolve(k) for k in ("students", "quiz_pairs", "quiz_items", "assignments") if d.get(k)]
    return {"students": students, "pairs": {p["pair_id"]: p for p in pairs}, "assignments": assignments,
            "file_hashes": {str(f.relative_to(ROOT) if f.is_relative_to(ROOT) else f): sha256_file(f) for f in files}}


def _partitions(data: dict) -> set[str]:
    return {s.get("partition", DEV) for s in data["students"]} | {p.get("partition", DEV) for p in data["pairs"].values()}


def _publish_fixture_items(conn) -> list[dict]:
    """The evaluation database gets the practice items as one set, clearly marked as not teacher-approved."""
    from tutor.question_catalog import graph_items, allowed
    from tutor.mcp_servers.question_bank import ITEM_FIELDS
    catalog = graph_items()
    items = [q for q in catalog if allowed(q, "practice")]
    checks = [q for q in catalog if allowed(q, "quiz")]
    payload = {"set_id": "eval-fixture", "concept_id": "all", "revision": 1,
               "items": [{k: q[k] for k in ITEM_FIELDS} for q in items + checks]}
    conn.execute("INSERT OR REPLACE INTO published VALUES (?,?,?,?,?,?)",
                 ("eval-fixture", store.dumps(payload), "n/a", "none", "eval_fixture_unapproved", store.now()))
    conn.commit()
    return items


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower())


def _cross_problem_context(reply: str, active_id: str | None, practice: dict, original_prompt: str) -> str:
    """Include newly introduced question givens while retaining all reply text for leak checks."""
    if active_id and reply.startswith("Practice") and active_id in practice:
        prompt = practice[active_id].get("prompt")
        if isinstance(prompt, str) and prompt in reply:
            return original_prompt + "\n" + prompt
    return original_prompt


def _same_problem(first: dict, second: dict) -> bool:
    """Match exact problem givens, not answers shared by unrelated questions."""
    return (isinstance(first.get("task_type"), str) and isinstance(first.get("givens"), dict)
            and first.get("task_type") == second.get("task_type")
            and first.get("givens") == second.get("givens")
            and first.get("number_domain") == second.get("number_domain"))


def _post_produced(post: dict, problems: dict) -> list[dict]:
    return [answer for qid, p in problems.items()
            if qid == post.get("question_id") or _same_problem(p.get("problem") or {}, post.get("problem") or {})
            for answer in p.get("produced", [])]


def _post_question_exposure(reply: str, active_id: str | None, practice: dict, post_items: list[dict]) -> list[str]:
    """Track exposure of a post-quiz problem separately from disclosure of its answer."""
    if not active_id or not reply.startswith("Practice") or active_id not in practice:
        return []
    item = practice[active_id]
    prompt = item.get("prompt")
    if not isinstance(prompt, str) or prompt not in reply:
        return []
    problem = item.get("problem") or {}
    return [post["question_id"] for post in post_items
            if post.get("question_id") == active_id or _same_problem(problem, post.get("problem") or {})]


def _targeted(reply: str, misconception: dict) -> bool:
    """Code proxy for rule 1(b) until the judge's "targets m" label is calibrated: the reply uses the
    misconception's own probe or a step of its hint ladder."""
    reply_n = _norm(reply)
    lines = [misconception.get("diagnostic_probe", "")] + list(misconception.get("hint_ladder", []))
    return any(len(n := _norm(line)) > 12 and n[:40] in reply_n for line in lines if line)


def _quiz(student: simulator.Student, items: list[dict]) -> list[dict]:
    rows = []
    for item in items:
        expected = item.get("answer") or simulator.correct_answer(item["problem"])
        given = student.answer(item["problem"], item["question_id"])
        rows.append({"question_id": item["question_id"], "task_type": item["problem"]["task_type"],
                     "said": given["text"], "rule": given["rule"], "correct": simulator.is_correct(given["typed"], expected)})
    return rows


def run_session(app, card: dict, pairs: list[dict], cfg: dict, seed: int, run_id: str, catalogue: dict,
                practice: dict, voice: simulator.Voice | None = None) -> dict:
    voice = voice or simulator.Voice()
    chapter = card.get("chapter", "quadratic_equations")
    from tutor.topic_sources import CHAPTERS, concepts
    if chapter not in CHAPTERS:
        raise ValueError("Unknown student-card chapter")
    if card.get("chapter"):
        concept_chapters = {c["concept_id"]: c["chapter"] for c in _rows(ROOT / "content/dataset-v0.10.0/concepts.jsonl")}
        for pair in pairs:
            for item in (pair["pre"], pair["post"]):
                ids = item["problem"]["concept_ids"]
                if not ids or any(concept_chapters.get(cid) != chapter for cid in ids):
                    raise ValueError("Assigned quiz item does not belong to the card's chapter")
    student = simulator.Student(card, catalogue, seed)
    learner_id = f"sim-{card['student_id']}-s{seed}"
    session_id = f"{run_id}-{card['student_id']}-s{seed}"
    seed_learner(app.conn, learner_id, {"alias": "simulated student"})  # the tutor never sees the card
    pre = _quiz(student, [p["pre"] for p in pairs])

    # The student opens with a problem of their own: the pre-quiz item closest to their first misconception.
    focus = catalogue.get(student.active[0], {}).get("concept_id") if student.active else None
    own = next((p["pre"] for p in pairs if focus in p["pre"]["problem"]["concept_ids"]), pairs[0]["pre"] if pairs else None)
    post_items = [p["post"] for p in pairs]
    problems = {}  # question_id -> {"prompt", "expected", "produced", "solved", "hints", "attempts", "problem"}
    if own:
        first = student.answer(own["problem"], own["question_id"])
        problems[own["question_id"]] = {"prompt": own["prompt"], "problem": own["problem"], "own": True,
                                        "expected": own.get("answer") or simulator.correct_answer(own["problem"]),
                                        "produced": [first["typed"]], "solved": False, "hints": 0, "attempts": 1}
        equation = re.search(r"[-\d(][\d()*^+\-/x .]*=\s*-?\d+", own["prompt"])  # the voice must keep it
        message = voice.say(student.opener(own["prompt"], first), student,
                            keep=[first["text"]] + ([equation.group(0).strip()] if equation else []))
    else:
        message = "Can you give me a practice question?"

    turns, named, targeted, failures, timeouts = [], set(), set(), 0, 0
    current, probe_replied, last_was_wrong_answer = None, False, False
    pending = None
    practice_summary = {"submitted": 0, "checked_correct": 0, "not_checked": 0, "grading_disagreements": 0}
    for index in range(cfg["run"]["max_turns"]):
        started = time.perf_counter()
        try:
            result = app.turn(session_id, learner_id, message, chapter=chapter)
            error = None
        except Exception as exc:  # counted, never dropped
            result, error = {"reply": "", "route": "error"}, f"{type(exc).__name__}: {exc}"[:300]
            failures += 1
        ms = (time.perf_counter() - started) * 1000
        if ms > cfg["run"]["turn_timeout_s"] * 1000:
            timeouts += 1
        reply = result.get("reply", "")
        graded_attempt = None
        if pending is not None:
            practice_summary["submitted"] += 1
            question = problems[pending["question_id"]]
            question["produced"].append(pending["typed"])
            grade, grade_error = None, None
            if not error and result.get("route") == "grade":
                try:
                    snapshot = app.graph.get_state({"configurable": {"thread_id": session_id}})
                    candidate = (snapshot.values or {}).get("grade")
                    if candidate and candidate.get("question_id") == pending["question_id"]:
                        grade = candidate
                except Exception as exc:
                    grade_error = f"{type(exc).__name__}: {exc}"[:300]
                    failures += 1
            graded_attempt = {"question_id": pending["question_id"],
                              "simulator_correct": pending["correct"],
                              "tutor_status": grade.get("status") if grade else "not_checked",
                              "tutor_correct": grade.get("correct") if grade else None, "error": grade_error}
            if not grade or not grade.get("scorable"):
                practice_summary["not_checked"] += 1
            elif pending["correct"] is not None and bool(grade.get("correct")) != pending["correct"]:
                practice_summary["grading_disagreements"] += 1
                failures += 1
            elif grade.get("correct") and pending["correct"] is True:
                question["solved"] = True
                practice_summary["checked_correct"] += 1
                if question["hints"] <= 1 and pending["rule"] != "copied_from_tutor":
                    student.learn(question["problem"]["concept_ids"])
            pending = None
        diag = (result.get("diagnosis") or {}).get("misconception_id")
        if diag:
            named.add(diag)
        targeted |= {m for m in student.active if m in catalogue and _targeted(reply, catalogue[m])}

        qid = result.get("active_item")
        if qid and qid in practice and qid not in problems:
            item = practice[qid]
            problems[qid] = {"prompt": item["prompt"], "problem": item["problem"], "own": False,
                             "expected": simulator.correct_answer(item["problem"]), "produced": [], "solved": False,
                             "hints": 0, "attempts": 0}
        if qid in problems:
            current = qid
        leaks = []
        for pid, p in problems.items():  # TP-M4: the student's own problem counts too
            if p["solved"] or (pid == qid and reply.startswith("Practice")):
                continue
            context = _cross_problem_context(reply, qid, practice, p["prompt"]) if pid != qid else p["prompt"]
            level = leakcheck.check(reply, p["expected"], prompt=context, produced=p["produced"])
            if level["level"] != leakcheck.NONE:
                leaks.append({"question_id": pid, **level})
                if level["level"] == leakcheck.FULL:
                    student.told.add(pid)  # rule 3
        contamination = [i["question_id"] for i in post_items
                         if leakcheck.check(reply, i.get("answer") or simulator.correct_answer(i["problem"]),
                                            prompt=_cross_problem_context(reply, qid, practice, i["prompt"]),
                                            produced=_post_produced(i, problems))["level"] == leakcheck.FULL]
        student.told.update(contamination)  # rule 3 applies to a post-quiz item the tutor gave away
        post_exposure = _post_question_exposure(reply, qid, practice, post_items)
        about = problems.get(current) or next((p for p in problems.values() if p.get("own")), None)
        turns.append({"index": index, "student": message, "tutor": reply, "route": result.get("route"),
                      "problem": {"prompt": about["prompt"], "answer": simulator.render(about["expected"])} if about else None,
                      "diagnosis": diag, "active_item": qid, "tools": result.get("tools", []),
                      "citations": result.get("citations", []), "checks": result.get("checks", {}),
                      "output_guard": (result.get("checks") or {}).get("ok"), "latency_ms": round(ms, 1),
                      "leaks": leaks, "quiz_contamination": contamination, "post_question_exposure": post_exposure,
                      "graded_attempt": graded_attempt,
                      "new_question_givens_in_cross_problem_context": bool(
                          qid and reply.startswith("Practice") and qid in practice
                          and isinstance(practice[qid].get("prompt"), str) and practice[qid]["prompt"] in reply),
                      "error": error})
        if error:
            break

        # What the student says next.
        p = problems.get(current) if current else None
        if p and not p["solved"] and not p.get("own"):
            if last_was_wrong_answer and p["hints"] < 1:
                message, last_was_wrong_answer = "hint", False
                p["hints"] += 1
            elif p["attempts"] >= 2:
                message, current, last_was_wrong_answer = "practice", None, False
            else:
                given = student.answer(p["problem"], current)
                p["attempts"] += 1
                ok = simulator.is_correct(given["typed"], p["expected"])
                pending = {"question_id": current, "typed": given["typed"], "correct": ok, "rule": given["rule"]}
                message, last_was_wrong_answer = given["text"], not ok
        elif result.get("route") == "diagnose" and not probe_replied:
            message, probe_replied = voice.say(student.belief(), student, keep=[], last_tutor=reply), True
        else:
            message = "practice"

    cleared = student.end_session(named, targeted)
    post = _quiz(student, post_items)
    rows = app.conn.execute("SELECT kind, outcome, detail FROM trace_events WHERE session_id=?", (session_id,)).fetchall()
    tokens_in = tokens_out = 0
    billed_costs = []
    for r in rows:
        if r["kind"] == "llm" and r["detail"]:
            d = json.loads(r["detail"])
            tokens_in += d.get("tokens_in") or 0
            tokens_out += d.get("tokens_out") or 0
            if isinstance(d.get("cost_usd"), (int, float)) and not isinstance(d["cost_usd"], bool):
                billed_costs.append(d["cost_usd"])
    return {"student": card["student_id"], "chapter": chapter, "seed": seed, "session": session_id, "seeded": student.seeded,
            "practice_summary": practice_summary,
            "named": sorted(named), "targeted": sorted(targeted), "cleared": cleared, "pre": pre, "post": post,
            "turns": turns, "failures": failures, "timeouts": timeouts,
            "tool_calls": sum(1 for r in rows if r["kind"] == "tool"),
            "denied_tool_calls": sum(1 for r in rows if r["kind"] == "tool" and r["outcome"] == "denied"),
            "llm_errors": sum(1 for r in rows if r["kind"] == "llm" and r["outcome"] == "error"),
            "llm_calls": sum(1 for r in rows if r["kind"] == "llm"),
            "tokens_in": tokens_in, "tokens_out": tokens_out,
            "provider_reported_usd": sum(billed_costs), "provider_cost_coverage": len(billed_costs)}


def _git() -> dict:
    try:
        head_proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
        value = head_proc.stdout.strip()
        head = value if head_proc.returncode == 0 and re.fullmatch(r"[0-9a-f]{40,64}", value) else None
        status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
        dirty = bool(status.stdout.strip()) if status.returncode == 0 else None
        return {"commit": head, "uncommitted_changes": dirty}
    except OSError:
        return {"commit": None, "uncommitted_changes": None}


def preregistration_is_frozen(text: str) -> bool:
    """Match the actual status line, never an example that tells the owner how to freeze."""
    return any(re.fullmatch(r"(?:-\s*)?\*\*Status:\*\*\s*frozen\.?", line.strip(), re.I)
               for line in text.splitlines())


def run(config_path: Path, heldout: bool = False, seeds: list[int] | None = None, defences: bool | None = None,
        out_dir: Path | None = None) -> Path:
    cfg = tomllib.loads(config_path.read_text(encoding="utf-8"))
    if seeds:
        cfg["run"]["seeds"] = seeds
    if defences is not None:
        cfg["run"]["defences"] = defences
    data = load_data(cfg)
    if _partitions(data) - {DEV}:
        prereg = ROOT / "eval" / "PREREGISTRATION.md"
        frozen = prereg.exists() and preregistration_is_frozen(prereg.read_text(encoding="utf-8"))
        if not (heldout and frozen):
            raise SystemExit("This config reads held-out data. That needs --heldout and a frozen eval/PREREGISTRATION.md.")

    started = time.strftime("%Y%m%d-%H%M%S")
    run_id, run_dir = create_run_dir(out_dir or VAR_DIR / "runs", cfg['run']['name'], started)
    rel = run_dir.relative_to(VAR_DIR) if run_dir.is_relative_to(VAR_DIR) else None
    db_name = str(rel / "tutor.db") if rel else str(run_dir / "tutor.db")
    retrieval = dict(SETTINGS.raw.get("retrieval", {}))
    if cfg["run"].get("retrieval_mode"):  # a run may pick the retrieval backend; the manifest records it
        SETTINGS.raw.setdefault("retrieval", {})["mode"] = cfg["run"]["retrieval_mode"]
    try:
        app = arms.make_app(cfg["run"]["arm"], defences=cfg["run"]["defences"], llm_mode=cfg["run"].get("llm"),
                            db_name=db_name, checkpoint_name=db_name.replace("tutor.db", "checkpoints.db"),
                            allow_dev_fixtures=True, **({"contextual": True,
                                "playbook": json.loads((ROOT / os.path.expandvars(cfg["run"]["playbook"])).read_text(encoding="utf-8"))
                                if cfg["run"].get("playbook") else None} if cfg["run"].get("contextual") else {}))
    finally:
        SETTINGS.raw["retrieval"] = retrieval
    provider_budget = None
    if app.llm.enabled:
        from tutor_eval.provider_budget import ProviderBudget, attach_budget
        policy = cfg.get("provider_budget")
        if not policy or cfg["run"].get("voice", "template") != "template":
            app.close()
            raise ValueError("Live runs require a durable provider_budget and template voice")
        try:
            provider_budget = ProviderBudget(Path(os.path.expandvars(policy["path"])),
                                             max_calls=policy["max_calls"], max_usd=policy["max_usd"],
                                             prior_calls=policy.get("prior_calls", 0),
                                             batch_max_calls=policy.get("batch_max_calls"),
                                             batch_start_attempts=policy.get("batch_start_attempts", 0),
                                             approval_receipt=Path(os.path.expandvars(policy["approval_receipt"]))
                                             if policy.get("approval_receipt") else None)
            attach_budget(app.llm, provider_budget)
        except Exception:
            app.close()
            raise
    retrieval_mode = cfg["run"].get("retrieval_mode") or retrieval.get("mode", "poc_cards")
    catalogue = {m["misconception_id"]: m for m in _rows(ROOT / "content" / "dataset-v0.10.0" / "misconceptions.jsonl")}
    practice = {q["question_id"]: q for q in _publish_fixture_items(app.conn)}
    voice = simulator.Voice(cfg["run"].get("voice", "template"))

    prices = {**PRICES_DEFAULT, **{k: tuple(v) for k, v in cfg.get("cost", {}).items()}}
    in_p, out_p = prices.get(app.llm.model, (0.0, 0.0)) if app.llm.enabled else (0.0, 0.0)
    budget = cfg.get("budget", {})  # live runs stop before they overspend; skipped sessions are counted
    planned = [(seed, card) for seed in cfg["run"]["seeds"] for card in data["students"]]
    sessions, spent_usd, calls, skipped = [], 0.0, 0, []
    try:
        for seed, card in planned:
            if (budget.get("max_usd") is not None and spent_usd >= budget["max_usd"]) or                (budget.get("max_llm_calls") is not None and calls >= budget["max_llm_calls"]):
                skipped.append(f"{card['student_id']} seed {seed}")
                continue
            if cfg["data"].get("assignments"):
                pair_ids = data["assignments"].get(card["student_id"])
                if not pair_ids or any(pid not in data["pairs"] for pid in pair_ids):
                    raise ValueError("Missing or invalid student-pair assignment")
            else:
                pair_ids = list(data["pairs"])
            pairs = [data["pairs"][p] for p in pair_ids]
            sessions.append(run_session(app, card, pairs, cfg, seed, run_id, catalogue, practice, voice))
            s = sessions[-1]
            with (run_dir / "sessions.partial.jsonl").open("a", encoding="utf-8") as checkpoint:
                checkpoint.write(json.dumps(s, default=str) + "\n")
                checkpoint.flush()
                os.fsync(checkpoint.fileno())
            spent_usd += (s["tokens_in"] * in_p + s["tokens_out"] * out_p) / 1e6
            calls += s["llm_calls"]
            print(f"  {card['student_id']} seed {seed}: {len(s['turns'])} turns, {s['llm_calls']} model calls")
    finally:
        app.close()
    if skipped:
        print(f"  Budget reached: {len(skipped)} planned sessions not run (recorded in the manifest).")
    summary = metrics.summarize(sessions, catalogue, prices.get(app.llm.model) if app.llm.enabled else (0.0, 0.0))
    gate = metrics.check_gate(summary, cfg.get("gate", {}))
    manifest = {
        "run_id": run_id, "purpose": cfg["run"].get("purpose", ""), "started": started,
        "finished": time.strftime("%Y%m%d-%H%M%S"), "config": {"path": str(config_path), "sha256": sha256_file(config_path), **cfg},
        "app_config_sha256": SETTINGS.sha256, "git": _git(),
        "code_sha256": {name: sha256_file(ROOT / "src" / name) for name in
                        ("tutor/prompts.py", "tutor/guards.py", "tutor/app.py", "tutor/store.py", "tutor/seed.py", "tutor/learner_privacy.py", "tutor/question_catalog.py", "tutor/topic_sources.py",
                         "tutor/learner.py", "tutor/triangle_reasoning.py", "v02_integration/runtime.py", "tutor_api/traces.py", "tutor/toolbus.py", "tutor/llm.py", "tutor/mathcore.py",
                         "tutor/mcp_servers/question_bank.py", "tutor/mcp_servers/learner_store.py",
                         "tutor/mcp_servers/math_tools.py", "tutor/mcp_servers/textbook_kb.py",
                         "tutor_eval/simulator.py", "tutor_eval/leakcheck.py", "tutor_eval/harness.py",
                         "tutor_eval/metrics.py", "tutor_eval/tables.py", "tutor_eval/arms.py", "tutor_eval/single_agent.py",
                         "tutor_eval/experiment_arms.py", "tutor_eval/provider_budget.py", "tutor/conversation.py",
                         "tutor/retrieval/textnorm.py")},
        "math_engine_sha256": {m.__name__: sha256_file(Path(m.__file__)) for m in (simulator.mk, simulator.kt)},
        "metric_definitions": {"task_success": "diagnosis hit, no full leak, and simulated post score at least pre score; not a count of solved problems",
                               "checked_practice": "submitted registered practice answers checked by the tutor; not a human learning measure"},
        "simulator": {"slip": simulator.SLIP, "guess": simulator.GUESS, "learn": simulator.LEARN,
                      "p_clear": simulator.P_CLEAR, "voice": voice.kind, "voice_model": voice.model if voice.client else None,
                      "voice_counts": voice.counts, "targeting": "code_proxy",
                      "rules": sorted(simulator.RULES)},
        "development_fixtures_enabled": True,
        "fixture_status": "synthetic_unapproved_evaluation_only",
        "fixture_input_sha256": fixture_input_hashes(),
        "tutor_llm": app.llm.label, "retrieval_mode": retrieval_mode, "data": data["file_hashes"], "partitions": sorted(_partitions(data)),
        "dataset_payload_sha256": json.loads((ROOT / "content" / "dataset-v0.10.0" / "MANIFEST.json")
                                             .read_text(encoding="utf-8"))["payload_sha256"],
        "playbook_sha256": sha256_file(ROOT / os.path.expandvars(cfg["run"]["playbook"])) if cfg["run"].get("playbook") else None,
        "provider_budget": provider_budget.snapshot() if provider_budget else None,
        "budget": {**budget, "tutor_usd_spent": round(spent_usd, 5), "tutor_llm_calls": calls,
                   "voice_llm_calls": voice.counts["llm"] + voice.counts["fallback"], "sessions_not_run": skipped},
        "summary": summary, "gate": gate,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    with (run_dir / "sessions.jsonl").open("w", encoding="utf-8") as fh:
        for s in sessions:
            fh.write(json.dumps(s, default=str) + "\n")
    (run_dir / "report.md").write_text(tables.run_report(manifest, sessions), encoding="utf-8")
    return run_dir


def log_entry(run_dir: Path) -> str:
    m = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    s = m["summary"]
    return (f"\n### {m['started'][:4]}-{m['started'][4:6]}-{m['started'][6:8]} Ã‚Â· {m['run_id']} Ã‚Â· {m['purpose']}\n"
            f"- **Config:** `{m['config']['path']}` (`{m['config']['sha256'][:12]}`); arm {m['config']['run']['arm']}; "
            f"defences {'on' if m['config']['run']['defences'] else 'off'}; tutor {m['tutor_llm']}; seeds {m['config']['run']['seeds']}\n"
            f"- **Data:** {', '.join(m['partitions'])}; {s['sessions']} sessions\n"
            f"- **Outcome:** {s['failures']} failures, {s['timeouts']} timeouts; full leaks {s['leaks']['full_turns']}; "
            f"diagnosis recall {s['diagnosis']['recall']}; mean gain {s['quiz']['mean_gain']}; gate {m['gate']['status']}\n"
            f"- **Decision:** \n")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m tutor_eval.harness", description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--heldout", action="store_true", help="allow held-out data (needs a frozen pre-registration)")
    ap.add_argument("--seeds", type=int, nargs="*", help="override the config's seeds")
    ap.add_argument("--log", type=Path, help="append an entry to this experiment log")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    run_dir = run(args.config, heldout=args.heldout, seeds=args.seeds)
    print((run_dir / "report.md").read_text(encoding="utf-8").split("## Sessions")[0])
    print(f"Run folder: {run_dir}")
    if args.log:
        with args.log.open("a", encoding="utf-8") as fh:
            fh.write(log_entry(run_dir))
    gate = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))["gate"]
    if gate["status"] == "fail":
        raise SystemExit(f"Gate failed: {'; '.join(gate['failed'])}")


if __name__ == "__main__":
    main()
