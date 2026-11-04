"""Reports and results tables (R5). Every number carries its run_id.

    python -m tutor_eval.tables var/runs/<run_a> var/runs/<run_b> ...   # one comparison table across runs
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _fmt(x) -> str:
    if x is None:
        return "–"
    if isinstance(x, (list, tuple)):
        return "[" + ", ".join(_fmt(v) for v in x) + "]"
    return f"{x:.3g}" if isinstance(x, float) else str(x)


def run_report(manifest: dict, sessions: list[dict]) -> str:
    s, cfg = manifest["summary"], manifest["config"]["run"]
    smoke = "development" in manifest["partitions"] and len(manifest["partitions"]) == 1
    lines = [
        f"# Run {manifest['run_id']}",
        "",
        f"{manifest['purpose']}",
        "",
        f"- **Data:** {', '.join(manifest['partitions'])}" + (" only. A development run: not a result." if smoke else ""),
        f"- **Tutor:** arm `{cfg['arm']}`, defences {'on' if cfg['defences'] else 'off'}, {manifest['tutor_llm']}",
        f"- **Simulator:** {manifest['simulator']['voice']} voice; targeting by {manifest['simulator']['targeting']}; "
        f"slip {manifest['simulator']['slip']}, guess {manifest['simulator']['guess']}, learn {manifest['simulator']['learn']}, "
        f"clear {manifest['simulator']['p_clear']}",
        f"- **Config:** `{manifest['config']['path']}` sha256 `{manifest['config']['sha256'][:12]}`; app config "
        f"`{manifest['app_config_sha256'][:12]}`; commit `{(manifest['git']['commit'] or 'unknown')[:10]}`"
        + (" with uncommitted changes" if manifest["git"]["uncommitted_changes"] else ""),
        f"- **Gate:** {manifest['gate']['status']}" + (f" ({'; '.join(manifest['gate']['failed'])})" if manifest["gate"]["failed"] else "")
        + "; configured engineering thresholds only, not a teaching-quality or release decision",
        "",
        "## Summary",
        "",
        "| Measure | Value |",
        "|---|---|",
        f"| Sessions / turns | {s['sessions']} / {s['turns']} |",
        f"| Failures / timeouts (counted, never dropped) | {s['failures']} / {s['timeouts']} |",
        f"| Diagnosis recall / precision / macro-F1 | {_fmt(s['diagnosis']['recall'])} / {_fmt(s['diagnosis']['precision'])} / {_fmt(s['diagnosis']['macro_f1'])} |",
        f"| Sessions with the seeded misconception named | {s['diagnosis']['sessions_with_hit']} of {s['sessions']} |",
        f"| Full / partial leak turns | {s['leaks']['full_turns']} / {s['leaks']['partial_turns']} |",
        f"| Post-quiz answers given away | {s['leaks']['quiz_contamination']} |",
        f"| Post-quiz question exposures (not answer leaks) | {s['leaks'].get('post_question_exposures', 0)} |",
        f"| Simulated quiz pre → post (mean of {s['quiz']['items_per_quiz']} items) | {_fmt(s['quiz']['mean_pre'])} → {_fmt(s['quiz']['mean_post'])} |",
        f"| Simulated change, bootstrap interval | {_fmt(s['quiz']['mean_gain'])}, {_fmt(s['quiz']['gain_ci95'])} |",
        f"| Diagnosis/quiz proxy (not problems solved) | {s['task_success']} of {s['sessions']} |",
        f"| Submitted / checked-correct practice attempts | {s.get('checked_practice', {}).get('submitted', 0)} / {s.get('checked_practice', {}).get('checked_correct', 0)} |",
        f"| Tool calls / denied | {s['policy']['tool_calls']} / {s['policy']['denied_tool_calls']} |",
        f"| Latency p50 / p95 (ms) | {_fmt(s['latency_ms']['p50'])} / {_fmt(s['latency_ms']['p95'])} |",
        f"| Cost per session (USD), tokens in / out | {_fmt(s['cost_usd']['per_session'])}, {s['cost_usd']['tokens_in']} / {s['cost_usd']['tokens_out']} |",
        "",
        "## Sessions",
        "",
        "| Student | Seed | Seeded | Named | Hit | Cleared | Pre | Post | Full leaks | Turns | Failures |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for v in s["sessions_detail"]:
        lines.append(f"| {v['student']} | {v['seed']} | {', '.join(v['seeded'])} | {', '.join(v['named']) or '–'} | "
                     f"{'yes' if v['hit'] else 'no'} | {', '.join(v['cleared']) or '–'} | {v['pre']}/{v['items']} | "
                     f"{v['post']}/{v['items']} | {v['full_leaks']} | {v['turns']} | {v['failures'] + v['timeouts']} |")
    lines += ["", "## Transcripts", ""]
    for sess in sessions:
        lines.append(f"### {sess['student']} · seed {sess['seed']} · `{sess['session']}`")
        for t in sess["turns"]:
            flag = " **[leak: " + ", ".join(f"{x['level']}" for x in t["leaks"]) + "]**" if t["leaks"] else ""
            lines.append(f"- **Student:** {t['student']}\n  **Tutor** ({t['route']}): {t['tutor']}{flag}")
        lines.append("")
    return "\n".join(lines)


ROWS = [("Sessions", lambda s: s["sessions"]), ("Failures + timeouts", lambda s: s["failures"] + s["timeouts"]),
        ("Diagnosis recall", lambda s: s["diagnosis"]["recall"]), ("Diagnosis macro-F1", lambda s: s["diagnosis"]["macro_f1"]),
        ("Full leak turns", lambda s: s["leaks"]["full_turns"]), ("Partial leak turns", lambda s: s["leaks"]["partial_turns"]),
        ("Mean gain", lambda s: s["quiz"]["mean_gain"]), ("Gain 95% CI", lambda s: s["quiz"]["gain_ci95"]),
        ("Gain across seeds: mean, SD", lambda s: [s["across_seeds"]["gain_mean"], s["across_seeds"]["gain_sd"]]),
        ("Diagnosis/quiz proxy (not problems solved)", lambda s: s["task_success"]), ("Latency p95 (ms)", lambda s: s["latency_ms"]["p95"]),
        ("Cost per session (USD)", lambda s: s["cost_usd"]["per_session"])]


def compare(run_dirs: list[Path]) -> str:
    manifests = [json.loads((d / "manifest.json").read_text(encoding="utf-8")) for d in run_dirs]
    head = "| Measure | " + " | ".join(f"`{m['run_id']}`" for m in manifests) + " |"
    lines = [head, "|---|" + "---|" * len(manifests)]
    for name, get in ROWS:
        lines.append(f"| {name} | " + " | ".join(_fmt(get(m["summary"])) for m in manifests) + " |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(compare([Path(p) for p in sys.argv[1:]]))
