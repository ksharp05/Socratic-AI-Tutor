"""Command-line interface for testing the POC. Run `tutor --help` after `pip install -e ".[dev]"`."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

from . import store
from .config import SETTINGS, db_path
from .seed import ALIASES, DEMO_LEARNERS, reset_and_seed

if sys.stdout.isatty() and not os.environ.get("NO_COLOR"):
    os.system("")  # enables ANSI colours in classic Windows consoles
    DIM, BOLD, RESET = "\033[2m", "\033[1m", "\033[0m"
else:
    DIM = BOLD = RESET = ""


def _app(**kwargs):
    from .app import TutorApp  # imported lazily so `setup` stays fast
    return TutorApp(**kwargs)


def _learner(name: str) -> str:
    return ALIASES.get(name.upper(), name)


def _show_turn(result: dict, verbose: bool) -> None:
    print(f"{BOLD}Tutor:{RESET} {result['reply']}")
    if verbose:
        diag = result.get("diagnosis") or {}
        bits = [f"route={result.get('route')}"]
        if diag:
            bits.append(f"diagnosis={diag.get('misconception_id')} ({diag.get('status')})")
        if result.get("checks") and not result["checks"].get("skipped"):
            bits.append(f"output_guard={'pass' if result['checks'].get('ok') else 'fail'}")
        bits.append("tools=" + (", ".join(result.get("tools") or []) or "none"))
        print(f"{DIM}  ↳ {' | '.join(bits)}{RESET}")


def _print_plan(plan: dict | None) -> None:
    if not plan:
        print("No plan yet.")
        return
    print(f"{BOLD}Study plan v{plan['version']}{RESET}" + (f"  (why updated: {plan['replan_reason']})" if plan.get("replan_reason") else ""))
    for i, step in enumerate(plan["steps"], 1):
        print(f"  {i}. {step['concept_id']} {step['title']}: {step['action']} (mastery {step['mastery']}; {step['why']})")
    if plan.get("mastered"):
        print(f"  mastered: {', '.join(plan['mastered'])}")


def cmd_setup(args) -> None:
    counts = reset_and_seed()
    print("POC content from dataset v0.10.0 (development data only):", json.dumps(counts))
    print(f"State reset in {db_path().parent}. Demo learners: " +
          ", ".join(f"{k} = {v} ({DEMO_LEARNERS[v]['alias']})" for k, v in ALIASES.items()))


def cmd_chat(args) -> None:
    app = _app(defences=not args.no_defences)
    lid = _learner(args.learner)
    session = args.session or f"s-{lid}-{int(time.time())}"
    resumed = app.resume(session)
    print(f"{BOLD}Socratic Tutor POC{RESET}  learner={lid}  session={session}  mode={args.mode}  llm={app.llm.label}")
    if resumed:
        print(f"{DIM}(resumed an interrupted turn from checkpoint at {resumed['resumed_from']}){RESET}")
        print(f"{BOLD}Tutor:{RESET} {resumed['reply']}")
    print(f"{DIM}Commands: /practice  /quiz  /plan  /trace  /history  /exit. Type anything else to talk to the tutor.{RESET}")
    try:
        while True:
            try:
                text = input(f"{BOLD}You:{RESET} ").strip()
            except EOFError:
                break
            if not text:
                continue
            if text in ("/exit", "/quit"):
                break
            if text == "/plan":
                snap = app.graph.get_state({"configurable": {"thread_id": session}})
                _print_plan((snap.values or {}).get("plan"))
                continue
            if text == "/trace":
                _print_trace(app.conn, session)
                continue
            if text == "/history":
                for m in app.history(session):
                    print(f"  {m['role']}: {m['content']}")
                continue
            before = len(app.llm.errors)
            result = app.turn(session, lid, text, mode=args.mode)
            _show_turn(result, not args.quiet)
            _warn_failed_calls(app, before)
    finally:
        print(f"{DIM}Session {session} saved. Resume with: tutor chat --learner {args.learner} --session {session}{RESET}")
        app.close()


def cmd_ask(args) -> None:
    app = _app(defences=not args.no_defences)
    try:
        lid = _learner(args.learner)
        session = args.session or f"s-{lid}-{int(time.time())}"
        result = app.turn(session, lid, args.message, mode=args.mode)
        print(f"session={session}")
        _show_turn(result, True)
        _warn_failed_calls(app, 0)
        if args.plan:
            _print_plan(result.get("plan"))
    finally:
        app.close()


def _warn_failed_calls(app, before: int) -> None:
    if len(app.llm.errors) > before:
        print(f"  ! A live model call failed, so this reply came from a template: {app.llm.errors[-1]}\n"
              f"    Run `tutor check-llm` to test the key and model.")


def cmd_check_llm(args) -> None:
    from .config import DOTENV_KEYS
    from .llm import LLM, base_url, explain
    llm = LLM(None, mode="auto")
    if not llm.key:
        print("No API key found, so the tutor uses its deterministic stub.\n"
              "Copy .env.example to .env in the repository root, put your key after LLM_API_KEY=, "
              "and run this again.")
        sys.exit(1)
    where = ".env" if llm.key_source in DOTENV_KEYS else "the shell environment"
    print(f"Key:      {llm.key_source} from {where} ({len(llm.key)} characters, ending …{llm.key[-4:]})")
    print(f"Base URL: {base_url()}")
    print(f"Model:    {llm.model}" + ("  (LLM_MODEL overrides config/app.toml)" if os.environ.get("LLM_MODEL") else ""))
    if os.environ.get("TUTOR_LLM") == "stub":
        print("Note:     TUTOR_LLM=stub is set, so the tutor itself will still use the stub.")
    models = SETTINGS.llm.get("course_models", []) if args.all else (args.model or [llm.model])
    failed = []
    for model in models:
        print(f"  {model} … ", end="", flush=True)
        try:
            r = llm.ping(model)
            print(f"ok in {r['ms']} ms, replied {r['reply']!r} (tokens {r['tokens_in']} in, {r['tokens_out']} out)")
        except Exception as exc:
            failed.append(model)
            print(f"FAILED: {explain(exc)}")
    print(f"{len(models) - len(failed)} of {len(models)} models answered.")
    if failed:
        sys.exit(1)


def _print_trace(conn, session: str) -> None:
    rows = conn.execute("SELECT * FROM trace_events WHERE session_id=? ORDER BY id", (session,)).fetchall()
    if not rows:
        print("No trace events for this session.")
        return
    for i, r in enumerate(rows, 1):
        detail = f" {r['detail']}" if r["detail"] else ""
        args = f" {r['args']}" if r["args"] else ""
        print(f"{i:3}. [{r['node']}] {r['kind']}:{r['name']} role={r['role']} -> {r['outcome']}"
              f" ({r['latency_ms']} ms){args}{detail}")


def cmd_trace(args) -> None:
    conn = store.connect(db_path())
    _print_trace(conn, args.session)


def cmd_learners(args) -> None:
    conn = store.connect(db_path())
    for lr in conn.execute("SELECT * FROM learners ORDER BY learner_id"):
        lid = lr["learner_id"]
        mastery = ", ".join(f"{r['concept_id']}={r['p']:.2f}" for r in
                            conn.execute("SELECT * FROM mastery WHERE learner_id=? ORDER BY concept_id", (lid,)))
        mis = ", ".join(f"{r['misconception_id']}:{r['status']}" for r in
                        conn.execute("SELECT * FROM misconceptions WHERE learner_id=?", (lid,))) or "none"
        print(f"{BOLD}{lid}{RESET} ({lr['alias']})\n  mastery: {mastery}\n  misconceptions: {mis}")
    alerts = conn.execute("SELECT * FROM alerts ORDER BY id").fetchall()
    print(f"{BOLD}Teacher alerts{RESET}: " + ("none" if not alerts else ""))
    for a in alerts:
        print(f"  [{time.strftime('%H:%M:%S', time.localtime(a['ts']))}] {a['kind']} learner={a['learner_id']} {a['detail']}")


def cmd_teacher(args) -> None:
    app = _app()
    teacher = args.teacher
    try:
        if args.action == "propose":
            out = app.propose_set(args.concept)
            prop = app.proposal(out["set_id"])
            print(f"Proposed {out['set_id']} for {args.concept} (waiting for teacher: {out['waiting_for_teacher']})")
            _print_proposal(prop)
        elif args.action == "pending":
            rows = app.conn.execute("SELECT set_id, concept_id, status, revision, payload_sha256 FROM proposals "
                                    "ORDER BY updated_at").fetchall()
            for r in rows:
                print(f"  {r['set_id']}  concept={r['concept_id']}  status={r['status']}  rev={r['revision']}  "
                      f"sha256={r['payload_sha256'][:12]}…")
            if not rows:
                print("No proposals yet. Try: tutor teacher propose --concept qe04")
        elif args.action == "show":
            _print_proposal(app.proposal(args.set_id))
        elif args.action == "approve":
            out = app.decide(args.set_id, "approve", teacher)
            print(json.dumps(out, indent=2))
            if out.get("token"):
                print(f"{DIM}Keep this token to test invalidation later: tutor teacher try-publish {args.set_id} "
                      f"--token {out['token']}{RESET}")
        elif args.action == "edit":
            prop = app.proposal(args.set_id)
            ids = [i["question_id"] for i in prop["payload"]["items"]]
            if args.drop:
                ids = [q for q in ids if q != args.drop]
            if args.add:
                ids.append(args.add)
            print(json.dumps(app.decide(args.set_id, "edit", teacher, question_ids=ids), indent=2))
        elif args.action == "reject":
            print(json.dumps(app.decide(args.set_id, "reject", teacher, reason=args.reason), indent=2))
        elif args.action == "try-publish":
            print(json.dumps(app.try_publish(args.set_id, args.token, teacher), indent=2))
    finally:
        app.close()


def _print_proposal(prop: dict) -> None:
    print(f"  set={prop['set_id']} status={prop['status']} revision={prop['revision']} sha256={prop['payload_sha256']}")
    for item in prop["payload"]["items"]:
        print(f"   - {item['question_id']}: {item['prompt']}")


def cmd_tools(args) -> None:
    app = _app()
    try:
        for server, tools in app.bus.list_tools().items():
            print(f"{BOLD}{server}{RESET}")
            for t in tools:
                params = ", ".join(t["input_schema"].get("properties", {}).keys())
                print(f"  {'R' if t['read_only'] else 'W'}  {t['name']}({params}): {t['description'].splitlines()[0]}")
    finally:
        app.close()


def cmd_eval(args) -> None:
    from tutor_eval.run import main as eval_main
    eval_main(seeds=args.seeds, defences=not args.no_defences)


def main(argv: list[str] | None = None) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="tutor", description="Socratic Tutor POC. Config sha256: " + SETTINGS.sha256[:12])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="copy POC content from the dataset, reset state, seed learners A and B")
    for name, helptext in (("chat", "interactive student chat"), ("ask", "one student message")):
        sp = sub.add_parser(name, help=helptext)
        sp.add_argument("--learner", default="A", help="A, B or a learner ID")
        sp.add_argument("--session", help="session ID to continue (default: a new one)")
        sp.add_argument("--mode", choices=["practice", "quiz"], default="practice")
        sp.add_argument("--no-defences", action="store_true", help="turn guardrails off (for experiment E2)")
        if name == "chat":
            sp.add_argument("--quiet", action="store_true", help="hide route and tool details")
        else:
            sp.add_argument("message")
            sp.add_argument("--plan", action="store_true", help="also print the study plan")
    sp = sub.add_parser("trace", help="numbered walkthrough of a session's trace")
    sp.add_argument("session")
    sub.add_parser("learners", help="show learner models and teacher alerts")
    sub.add_parser("tools", help="list the MCP tools, read/write marks and parameters")
    sp = sub.add_parser("teacher", help="teacher actions on question sets")
    sp.add_argument("action", choices=["propose", "pending", "show", "approve", "edit", "reject", "try-publish"])
    sp.add_argument("set_id", nargs="?")
    sp.add_argument("--concept", default="qe04")
    sp.add_argument("--teacher", default="T-001")
    sp.add_argument("--drop", help="question ID to remove (edit)")
    sp.add_argument("--add", help="question ID to add (edit)")
    sp.add_argument("--reason", default="", help="reason (reject)")
    sp.add_argument("--token", help="an earlier approval token (try-publish)")
    sp = sub.add_parser("eval", help="run the simulated-student evaluation on the development cards")
    sp.add_argument("--seeds", type=int, default=1)
    sp.add_argument("--no-defences", action="store_true")
    sp = sub.add_parser("check-llm", help="make one short live call to check the API key and model")
    sp.add_argument("--model", action="append", help="model ID to try instead of the configured one (repeatable)")
    sp.add_argument("--all", action="store_true", help="try every model in course_models in config/app.toml")
    args = p.parse_args(argv)
    {"setup": cmd_setup, "chat": cmd_chat, "ask": cmd_ask, "trace": cmd_trace, "learners": cmd_learners,
     "teacher": cmd_teacher, "tools": cmd_tools, "eval": cmd_eval, "check-llm": cmd_check_llm}[args.cmd](args)


if __name__ == "__main__":
    main()
