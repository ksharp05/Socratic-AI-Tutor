"""Metrics over harness sessions (R5). Definitions follow Docs/plan/05-evaluation.md and the pre-registration:
failures and timeouts stay in every denominator, and nothing is dropped silently.
"""
from __future__ import annotations

import random
import statistics
from collections import defaultdict


def _round(x, n=3):
    return None if x is None else round(x, n)


def _percentile(values: list[float], q: float):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(q * (len(ordered) - 1))))]


def bootstrap_mean_ci(values: list[float], n: int = 2000, seed: int = 0) -> tuple | None:
    """Percentile bootstrap 95% CI of the mean (fixed seed, so reports are reproducible)."""
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(values, k=len(values))) for _ in range(n))
    return (_round(means[int(0.025 * n)]), _round(means[int(0.975 * n) - 1]))


def score(rows: list[dict]) -> tuple[int, int, int]:
    """(correct, scored, items): unscorable answers count as items but not as correct."""
    return sum(r["correct"] is True for r in rows), sum(r["correct"] is not None for r in rows), len(rows)


def session_view(s: dict) -> dict:
    pre_c, _, pre_n = score(s["pre"])
    post_c, _, post_n = score(s["post"])
    full = sum(1 for t in s["turns"] for leak in t["leaks"] if leak["level"] == "full")
    partial = sum(1 for t in s["turns"] for leak in t["leaks"] if leak["level"] == "partial")
    hit = bool(set(s["seeded"]) & set(s["named"]))
    first_hit = next((t["index"] + 1 for t in s["turns"] if t["diagnosis"] in s["seeded"]), None)
    gain = post_c - pre_c
    return {"student": s["student"], "seed": s["seed"], "seeded": s["seeded"], "named": s["named"], "hit": hit,
            "turns_to_diagnosis": first_hit, "cleared": s["cleared"], "pre": pre_c, "post": post_c, "items": pre_n,
            "gain": gain, "norm_gain": (gain / (pre_n - pre_c)) if pre_n > pre_c else None,
            "full_leaks": full, "partial_leaks": partial,
            "contamination": sum(len(t["quiz_contamination"]) for t in s["turns"]),
            "task_success": hit and full == 0 and post_c >= pre_c, "turns": len(s["turns"]),
            "failures": s["failures"], "timeouts": s["timeouts"], "denied_tool_calls": s["denied_tool_calls"],
            "tool_calls": s["tool_calls"], "llm_errors": s["llm_errors"], "tokens_in": s["tokens_in"],
            "tokens_out": s["tokens_out"]}


def summarize(sessions: list[dict], catalogue: dict, price: tuple | None) -> dict:
    views = [session_view(s) for s in sessions]
    n = len(views)
    turns = [t for s in sessions for t in s["turns"]]
    # Diagnosis, per misconception over sessions: seeded and named = TP, named only = FP, seeded only = FN.
    counts = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    for s in sessions:
        seeded, named = set(s["seeded"]), set(s["named"])
        for m in seeded | named:
            counts[m]["tp" if m in seeded and m in named else "fp" if m in named else "fn"] += 1
    f1s, per_m = [], {}
    for m, c in sorted(counts.items()):
        p = c["tp"] / (c["tp"] + c["fp"]) if c["tp"] + c["fp"] else 0.0
        r = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        f1s.append(f1)
        per_m[m] = {**c, "precision": _round(p), "recall": _round(r), "f1": _round(f1)}
    tp, fp, fn = (sum(c[k] for c in counts.values()) for k in ("tp", "fp", "fn"))
    latencies = [t["latency_ms"] for t in turns]
    gains = [v["gain"] for v in views]
    in_price, out_price = price or (0.0, 0.0)
    cost = [(v["tokens_in"] * in_price + v["tokens_out"] * out_price) / 1e6 for v in views]
    by_seed = defaultdict(list)
    for v in views:
        by_seed[v["seed"]].append(v)
    seed_gain = [statistics.fmean([v["gain"] for v in vs]) for vs in by_seed.values()]
    return {
        "sessions": n, "turns": len(turns),
        "failures": sum(v["failures"] for v in views), "timeouts": sum(v["timeouts"] for v in views),
        "diagnosis": {"recall": _round(tp / (tp + fn)) if tp + fn else None,
                      "precision": _round(tp / (tp + fp)) if tp + fp else None,
                      "macro_f1": _round(statistics.fmean(f1s)) if f1s else None,
                      "sessions_with_hit": sum(v["hit"] for v in views),
                      "median_turns_to_diagnosis": statistics.median([v["turns_to_diagnosis"] for v in views
                                                                      if v["turns_to_diagnosis"]] or [0]) or None,
                      "per_misconception": per_m,
                      "misconceptions_seen": sorted({m for s in sessions for m in s["seeded"]})},
        "leaks": {"full_turns": sum(v["full_leaks"] for v in views), "partial_turns": sum(v["partial_leaks"] for v in views),
                  "full_per_turn": _round(sum(v["full_leaks"] for v in views) / len(turns)) if turns else None,
                  "sessions_with_full_leak": sum(v["full_leaks"] > 0 for v in views),
                  "quiz_contamination": sum(v["contamination"] for v in views),
                  "post_question_exposures": sum(len(t.get("post_question_exposure", [])) for t in turns)},
        "quiz": {"mean_pre": _round(statistics.fmean([v["pre"] for v in views])) if n else None,
                 "mean_post": _round(statistics.fmean([v["post"] for v in views])) if n else None,
                 "mean_gain": _round(statistics.fmean(gains)) if n else None,
                 "gain_ci95": bootstrap_mean_ci(gains),
                 "mean_norm_gain": _round(statistics.fmean(g)) if (g := [v["norm_gain"] for v in views if v["norm_gain"] is not None]) else None,
                 "items_per_quiz": views[0]["items"] if views else None},
        "task_success": sum(v["task_success"] for v in views),
        "checked_practice": {k: sum(s.get("practice_summary", {}).get(k, 0) for s in sessions)
                             for k in ("submitted", "checked_correct", "not_checked", "grading_disagreements")},
        "policy": {"denied_tool_calls": sum(v["denied_tool_calls"] for v in views),
                   "tool_calls": sum(v["tool_calls"] for v in views), "llm_errors": sum(v["llm_errors"] for v in views)},
        "latency_ms": {"p50": _percentile(latencies, 0.5), "p95": _percentile(latencies, 0.95)},
        "cost_usd": {"per_session": _round(statistics.fmean(cost), 5) if cost else None, "total": _round(sum(cost), 4),
                     "tokens_in": sum(v["tokens_in"] for v in views), "tokens_out": sum(v["tokens_out"] for v in views)},
        "across_seeds": {"seeds": sorted(by_seed), "gain_mean": _round(statistics.fmean(seed_gain)) if seed_gain else None,
                         "gain_sd": _round(statistics.stdev(seed_gain)) if len(seed_gain) > 1 else None,
                         "gain_range": [_round(min(seed_gain)), _round(max(seed_gain))] if seed_gain else None},
        "sessions_detail": views,
    }


def check_gate(summary: dict, gate: dict) -> dict:
    """CI and pre-registered thresholds. No gate configured means status "none"."""
    if not gate:
        return {"status": "none", "failed": []}
    failed = []
    if "max_full_leaks" in gate and summary["leaks"]["full_turns"] > gate["max_full_leaks"]:
        failed.append(f"full leaks {summary['leaks']['full_turns']} > {gate['max_full_leaks']}")
    if "max_failures" in gate and summary["failures"] + summary["timeouts"] > gate["max_failures"]:
        failed.append(f"failures and timeouts {summary['failures'] + summary['timeouts']} > {gate['max_failures']}")
    if "min_sessions" in gate and summary["sessions"] < gate["min_sessions"]:
        failed.append(f"sessions {summary['sessions']} < {gate['min_sessions']}")
    if "min_diagnosis_recall" in gate and (summary["diagnosis"]["recall"] or 0) < gate["min_diagnosis_recall"]:
        failed.append(f"diagnosis recall {summary['diagnosis']['recall']} < {gate['min_diagnosis_recall']}")
    return {"status": "fail" if failed else "pass", "failed": failed}
