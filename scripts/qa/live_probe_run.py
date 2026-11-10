"""Run the quality and safety probe set through the real beta chat pipeline, with ledgered live model calls.

Subcommands (run from the canonical workspace with the shared-checkout .venv):
  allocate SLUG --max-usd 1 --max-calls 600 --purpose "..." [--program security]
                                                                open a v4 batch (USD <= 1) in the USD 10 phase
  run SLUG --model M --label L [--config live|library] [--areas a,b] [--ids X,Y] [--addendum FILE] --execute-live
  close SLUG                                                    seal the batch ledger and release unused cap
  status SLUG                                                   print the batch snapshot

"live" builds the app the way Vercel does (maths-only public index plus reference notes); "library" uses the
locally registered multi-subject NCERT dataset (needed for Science probes). Without --execute-live, run only
lists what it would send. Raw outputs stay in Directions/product_quality/v4/runs (private, never in git).
Synthetic probes only: no real student data is sent.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, json, os, secrets, sys, tempfile, threading, time, uuid
from pathlib import Path

MAIN = Path(__file__).resolve().parents[2]
CAN = Path(os.environ.get("SOCRATES_SOURCE_WORKSPACE", r"D:\Work\IITB\Socratic Tutor")).resolve()
sys.path.insert(0, str(MAIN / "src"))
sys.path.insert(0, str(MAIN / "eval" / "fixtures"))
HEADERS = {"X-Socrates-Request": "1"}


def phase():
    from tutor_eval.product_budget import ProductPhase
    return ProductPhase(CAN, iteration="v4")


def program_headroom(phase_data, program):
    """USD still available to a named spending programme inside the phase (e.g. the USD 5 security test).

    Every batch whose name starts with the programme prefix counts: closed batches at their sealed spend,
    running ones at their full cap. The programme file records the user's approval quote and cap.
    """
    used = sum(b["max_usd"] for b in phase_data["batch_allocations"] if b["batch"].startswith(program["batch_prefix"]))
    return round(program["cap_usd"] - used, 10)


def allocate_in_program(name, slug, purpose, max_usd, max_calls):
    from tutor_eval.product_budget import read
    program = read(CAN / "Directions/product_quality/v4/programs" / f"{name}.json")
    if program.get("status") != "approved" or not slug.startswith(program["batch_prefix"]):
        raise SystemExit(f"Batch {slug} must start with {program['batch_prefix']} and the programme must be approved")
    p = phase()
    headroom = program_headroom(read(p.phase_path), program)
    if max_usd > headroom + 1e-10:
        raise SystemExit(f"Programme {name} has USD {headroom:.4f} left of {program['cap_usd']}; asked for {max_usd}")
    return p.allocate(slug, f"[{name} programme] {purpose}", max_usd=max_usd, max_calls=max_calls)


class LedgeredLanguage:
    """Same interface as socrates_beta.language.TeamLanguage, but every call is reserved in the phase wallet."""

    def __init__(self, model, wallet, *, cap=240, timeout=30, addendum=None, reasoning=None):
        from tutor.llm import LLM
        from tutor_eval.product_budget import attach_product_budget
        llm = LLM(None)
        llm.model = model
        self.client = attach_product_budget(llm, wallet, cap=cap, timeout=timeout)
        if reasoning:
            self.client.inner.extra_body = {**(self.client.inner.extra_body or {}), "reasoning": reasoning}
        self.model, self.addendum, self.log, self.lock = model, addendum, [], threading.Lock()

    def generate(self, system, context):
        if self.addendum:
            system = system + "\n" + self.addendum
        started, row = time.monotonic(), {"request_id": context.get("request_id"), "move": context.get("move"),
                                          "system_sha256": hashlib.sha256(system.encode()).hexdigest()[:16]}
        try:
            reply = self.client.invoke([("system", system), ("user", json.dumps(context, ensure_ascii=False))])
            content = reply.content if isinstance(reply.content, str) else ""
            usage = getattr(reply, "usage_metadata", None) or {}
            cost = ((getattr(reply, "response_metadata", None) or {}).get("token_usage") or {}).get("cost")
            row.update(content=content, tokens_in=usage.get("input_tokens"), tokens_out=usage.get("output_tokens"), cost=cost)
            return content
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {str(exc)[:200]}"
            raise
        finally:
            row["latency_ms"] = round((time.monotonic() - started) * 1000)
            with self.lock:
                self.log.append(row)

    def health(self):
        return {"mode": "live", "model": self.model}


def build_app(config, language, workdir):
    from socrates_beta.api import create_app
    from socrates_beta.repository import Repository
    if config == "live":
        from socrates_beta.public_index import prepare_public_index
        registry = prepare_public_index(MAIN, workdir / "public-index")
        settings = {"app_root": str(MAIN), "data_directory": str(workdir / "public-index"),
                    "assessment_policy": "reference_checked_beta", "require_live_consent": False}
    else:
        from socrates_beta.bootstrap import bootstrap
        registry = bootstrap(CAN, MAIN)
        settings = {"schema": 1, "app_root": str(MAIN), "data_directory": str(workdir), "max_live_calls": 120}
    return create_app(settings, live=language is not None, language=language, registry=registry,
                      repository=Repository(workdir / "observations.sqlite"), browser_secret=secrets.token_bytes(32),
                      testing=True)


def run_probe(app, probe):
    from fastapi.testclient import TestClient
    out = {k: probe[k] for k in ("id", "area", "subarea", "expect", "label", "subject", "lang")}
    out["turns"] = []
    with TestClient(app) as client:
        r = client.post("/api/sessions", json={"grade": probe["grade"], "subject": probe["subject"],
                                               "title": probe["turns"][0][:120]}, headers=HEADERS)
        if r.status_code != 200:
            out.update(scope="unavailable", http=r.status_code, detail=r.text[:300])
            return out
        sid = r.json()["id"]
        for text in probe["turns"]:
            rid, started = uuid.uuid4().hex, time.monotonic()
            resp = client.post("/api/chat", json={"session_id": sid, "text": text, "request_id": rid}, headers=HEADERS)
            row = {"text": text, "request_id": rid, "http": resp.status_code, "ms": round((time.monotonic() - started) * 1000)}
            if resp.status_code == 200:
                j = resp.json()
                row.update({k: j.get(k) for k in ("reply", "move", "provider_status", "validation_error", "format_repaired", "repair_reason")})
                row["citations"] = [c["id"] for c in j.get("citations", [])]
                row["retrieval"] = (j.get("retrieval") or {}).get("ids")
            else:
                row["detail"] = resp.text[:300]
            out["turns"].append(row)
    return out


def select(args):
    from quality_safety_probes_v1 import PROBES
    chosen = PROBES
    if args.areas:
        chosen = [x for x in chosen if x["area"] in args.areas.split(",")]
    if args.ids:
        chosen = [x for x in chosen if x["id"] in args.ids.split(",")]
    if args.subjects:
        chosen = [x for x in chosen if x["subject"] in args.subjects.split(",")]
    return chosen


def cmd_run(args):
    probes = select(args)
    print(f"{len(probes)} probes, model {args.model}, config {args.config}, label {args.label}")
    if not args.execute_live:
        print("Dry run: nothing sent. Add --execute-live to send through the ledgered wallet.")
        return
    wallet = phase().open(args.slug)
    addendum = Path(args.addendum).read_text(encoding="utf-8") if args.addendum else None
    reasoning = {"effort": args.reasoning_effort} if args.reasoning_effort else None
    language = LedgeredLanguage(args.model, wallet, cap=args.cap, addendum=addendum, reasoning=reasoning)
    out_dir = CAN / "Directions/product_quality/v4/runs" / args.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{args.label}.json"
    if target.exists():
        raise SystemExit(f"{target} exists; never overwrite a completed run")
    with tempfile.TemporaryDirectory() as tmp:
        app = build_app(args.config, language, Path(tmp))
        results, started = [], time.monotonic()
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for row in pool.map(lambda pr: run_probe(app, pr), probes):
                results.append(row)
    calls = {r["request_id"]: r for r in language.log}
    for row in results:
        for turn in row["turns"]:
            call = calls.get(turn.get("request_id"))
            if call:
                turn["llm"] = {k: call.get(k) for k in ("content", "tokens_in", "tokens_out", "cost", "latency_ms", "error", "system_sha256")}
    meta = {"model": args.model, "config": args.config, "label": args.label, "addendum": args.addendum,
            "addendum_sha256": hashlib.sha256(addendum.encode()).hexdigest() if addendum else None,
            "cap": args.cap, "reasoning": reasoning, "probes": len(probes), "llm_calls": len(language.log),
            "seconds": round(time.monotonic() - started), "snapshot": wallet.snapshot()}
    target.write_text(json.dumps({"meta": meta, "results": results}, indent=1, ensure_ascii=False), encoding="utf-8")
    snap = meta["snapshot"]
    print(f"done: {len(results)} probes, {len(language.log)} model calls, {meta['seconds']} s; batch accounted "
          f"USD {snap['accounted_usd']:.4f} of {snap['max_usd']}, attempts {snap['provider_attempts']}/{snap['max_calls']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("allocate"); a.add_argument("slug"); a.add_argument("--max-usd", type=float, required=True)
    a.add_argument("--max-calls", type=int, required=True); a.add_argument("--purpose", required=True)
    a.add_argument("--program", help="spend inside a capped programme, e.g. security (Directions/product_quality/v4/programs)")
    r = sub.add_parser("run"); r.add_argument("slug"); r.add_argument("--model", required=True); r.add_argument("--label", required=True)
    r.add_argument("--config", choices=("live", "library"), default="live"); r.add_argument("--areas"); r.add_argument("--ids")
    r.add_argument("--subjects"); r.add_argument("--addendum"); r.add_argument("--cap", type=int, default=240)
    r.add_argument("--reasoning-effort"); r.add_argument("--workers", type=int, default=4); r.add_argument("--execute-live", action="store_true")
    c = sub.add_parser("close"); c.add_argument("slug")
    s = sub.add_parser("status"); s.add_argument("slug")
    args = ap.parse_args()
    if args.cmd == "allocate":
        if args.program:
            w = allocate_in_program(args.program, args.slug, args.purpose, args.max_usd, args.max_calls)
        else:
            w = phase().allocate(args.slug, args.purpose, max_usd=args.max_usd, max_calls=args.max_calls)
        print(json.dumps(w.snapshot(), indent=1))
    elif args.cmd == "run":
        cmd_run(args)
    elif args.cmd == "close":
        p = phase()
        print(json.dumps(p.close(p.open(args.slug)), indent=1))
    else:
        print(json.dumps(phase().open(args.slug).snapshot(), indent=1))


if __name__ == "__main__":
    main()
