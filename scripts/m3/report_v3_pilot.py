"""Verify and report the completed six-session v3 pilot without provider calls."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

CODE = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get("SOCRATES_SOURCE_WORKSPACE", Path.cwd())).resolve()
sys.path.insert(0, str(CODE / "src"))
sys.path.insert(0, str(CODE / "scripts/m3"))
from analyse import citation_audit
from tutor_eval import metrics


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(commit, name):
    return subprocess.check_output(["git", "-C", str(CODE), "show", f"{commit}:{name}"])


def verify_git_hash(commit, name, expected):
    raw = git_blob(commit, name)
    lf = raw.replace(b"\r\n", b"\n")
    variants = {hashlib.sha256(b).hexdigest() for b in [raw, lf, lf.replace(b"\n", b"\r\n")]}
    if expected not in variants:
        # Git normalizes mixed historical line endings. Check the captured exact
        # bytes as well as their complete normalized equality to the Git blob.
        current = (CODE / name).read_bytes()
        assert hashlib.sha256(current).hexdigest() == expected, name
        assert current.replace(b"\r\n", b"\n") == lf, name


def main():
    root = SOURCE / "Directions/m3_runs/v3"
    approval_path = root / "PILOT_APPROVAL.json"
    approval = load(approval_path)
    assert approval["status"] == "approved" and approval["approved_by"] and approval["approval_quote"]
    commit = approval["candidate_commit"]
    profile_blob = git_blob(commit, "Docs/m3/v3/ENGINEERING_CHECKPOINT.json")
    profile = json.loads(profile_blob)
    for name, expected in profile["source_config_sha256"].items():
        verify_git_hash(commit, name, expected)
    for name, expected in profile["development_data_sha256"].items():
        assert sha(SOURCE / name) == expected, name
    prior = {
        "provider_budget.json": "2b0e529b378dfc7c68be4375a89a859b9c3c173dbc23f543a602c2c0cdd8b9de",
        "provider_budget_extension_e3.json": "72130f49d2ef764a9bcb6df769fa3387629f5e22f684fd6437cd5444205cc430",
    }
    for name, expected in prior.items():
        assert sha(SOURCE / "Directions/m3_runs" / name) == expected, name
    wallet_path = root / "provider_budget_pilot.json"
    wallet = load(wallet_path)
    policy, attempts = wallet["policy"], wallet["attempts"]
    assert policy["max_calls"] == approval["additional_requests"] == 80
    assert policy["max_usd"] == approval["max_additional_usd"] == 0.05
    assert policy["prior_calls"] == approval["prior_provider_attempts"] == 1036
    assert policy["approval_receipt_sha256"] == sha(approval_path)
    assert all(a["status"] == "completed" and a["billed_usd"] is not None for a in attempts)
    assert wallet["refused"] == 0 and len(attempts) <= policy["max_calls"]
    cost = sum(a["billed_usd"] for a in attempts)
    assert abs(cost - sum(a["accounted_usd"] for a in attempts)) < 1e-12
    assert cost <= policy["max_usd"]
    index = load(root / "pilot/INDEX.json")
    assert set(index["jobs"]) == {"c1", "c2"}
    conditions, receipts, session_sets = [], [], {}
    cumulative_calls = 0
    for arm in ["c1", "c2"]:
        job = index["jobs"][arm]
        assert job["status"] == "completed" and job["acceptance"]["pass"]
        run = Path(job["run"])
        manifest = load(run / "manifest.json")
        sessions = [json.loads(line) for line in (run / "sessions.jsonl").read_text(encoding="utf-8").splitlines()]
        summary = manifest["summary"]
        assert manifest["git"] == {"commit": commit, "uncommitted_changes": False}
        assert manifest["tutor_llm"] == "openai/gpt-4.1-mini via https://openrouter.ai/api/v1"
        assert manifest["config"]["sha256"] == job["config_sha256"]
        verify_git_hash(commit, f"eval/configs/m3_v3_pilot_{arm}.toml", job["config_sha256"])
        for name, expected in manifest["code_sha256"].items():
            verify_git_hash(commit, "src/" + name, expected)
        assert len(sessions) == 3 and all(len(s["turns"]) == 8 and s["seed"] == 1 for s in sessions)
        assert len({s["chapter"] for s in sessions}) == 3
        assert summary["failures"] == summary["timeouts"] == summary["policy"]["llm_errors"] == 0
        assert manifest["gate"]["status"] == "pass" and summary["leaks"]["full_turns"] == 0
        observations = [t for s in sessions for t in s["post_copy_measurement"]["turn_model_observations"]]
        assert len(observations) == 24 and all(t["trace_observed"] and t["model_errors"] == 0 for t in observations)
        tutor_turns = [t for t in observations if t["route"] == "tutor"]
        assert tutor_turns and all(t["model_calls"] > 0 for t in tutor_turns)
        calls = sum(s["llm_calls"] for s in sessions)
        assert calls == sum(t["model_calls"] for t in observations)
        cumulative_calls += calls
        assert manifest["provider_budget"]["provider_attempts"] == cumulative_calls
        assert manifest["provider_budget"]["approval_receipt_sha256"] == sha(approval_path)
        reported = sum(s["provider_reported_usd"] for s in sessions)
        assert abs(reported - summary["cost_usd"]["provider_reported_total"]) < 1e-12
        assert sum(s["provider_cost_coverage"] for s in sessions) == calls
        citations = citation_audit(sessions)
        assert citations.get("turns_with_missing_snapshot", 0) == 0
        assert all(citations[k] == citations["snapshots"] for k in ["valid_snapshot_hash", "same_chapter", "registered_source_text_match"])
        measurements = [s["post_copy_measurement"] for s in sessions]
        assert all(s["human_labels"] == 0 and s["semantic_disclosure"] == "unreviewed" for s in measurements)
        views = [metrics.session_view(s) for s in sessions]
        conditions.append({"condition": arm, "sessions": len(sessions), "turns": len(observations),
            "model_calls": calls, "provider_reported_usd": reported,
            "tutor_route_turns": len(tutor_turns), "tutor_route_turns_with_model_call": len(tutor_turns),
            "route_counts": dict(Counter(t["route"] for t in observations)),
            "all_turn_traces_observed": True, "failures": 0, "timeouts": 0, "provider_errors": 0,
            "detected_full_leak_turns": 0, "legacy_quiz_match_flags": summary["leaks"]["quiz_contamination"],
            "removed_ineligible_post_copies": sum(len(s["removed_ineligible_post_ids"]) for s in measurements),
            "retained_post_copies": sum(len(s["post_ids_allowed_to_copy"]) for s in measurements),
            "unreviewed_post_match_decisions": dict(sum((Counter(s["decision_counts"]) for s in measurements), Counter())),
            "diagnosis_recall": summary["diagnosis"]["recall"], "sessions_with_diagnosis_hit": summary["diagnosis"]["sessions_with_hit"],
            "success_proxy": summary["task_success"], "mean_synthetic_quiz_change": statistics.fmean(v["gain"] for v in views),
            "checked_practice": summary["checked_practice"], "citations": citations, "engineering_gate": "pass"})
        session_sets[arm] = {(s["student"], s["seed"]): metrics.session_view(s)["gain"] for s in sessions}
        receipts.append({"condition": arm, "run_id": manifest["run_id"], "git": manifest["git"],
            "manifest_sha256": sha(run / "manifest.json"), "sessions_sha256": sha(run / "sessions.jsonl"),
            "config_sha256": job["config_sha256"], "dataset_payload_sha256": manifest["dataset_payload_sha256"]})
    assert cumulative_calls == len(attempts)
    assert abs(sum(r["provider_reported_usd"] for r in conditions) - cost) < 1e-12
    assert session_sets["c1"].keys() == session_sets["c2"].keys()
    matched = len(session_sets["c1"])
    difference = statistics.fmean(session_sets["c2"][k] - v for k, v in session_sets["c1"].items())
    result = {"status": "completed_path_acceptance_pass_quality_and_final_gates_open", "reported_date_Asia_Kolkata": "2026-11-06",
        "runtime_commit": commit, "runtime_candidate_tag": "beta-m3-behaviour-v3-candidate",
        "engineering_checkpoint_git_blob_sha256": hashlib.sha256(profile_blob).hexdigest(),
        "source_config_files_verified_against_recorded_commit": len(profile["source_config_sha256"]),
        "scope": "six development pilot sessions; three existing cards, one per chapter, one seed, template voice, no judge",
        "conditions": conditions, "receipts": receipts,
        "paired_descriptive_comparison": {"matched_pairs": matched, "student_clusters": matched, "C2_minus_C1_mean_synthetic_quiz_change": difference,
            "inference": "too small and development-only for efficacy or independent qualification; no C0 arm"},
        "budget": {"approved_max_requests": 80, "approved_max_usd": 0.05, "requests_used": len(attempts),
            "provider_reported_usd": cost, "provider_cost_coverage": len(attempts), "provider_errors": 0, "refused": 0,
            "in_flight": 0, "prior_attempts": 1036, "total_provider_attempts": 1036 + len(attempts),
            "known_continuation_usd_excluding_original_98_unknown": 0.2791804 + cost,
            "pilot_ledger_sha256": sha(wallet_path), "approval_receipt_sha256": sha(approval_path),
            "original_and_E3_ledger_hashes_unchanged": prior,
            "remaining_allowance": "unused; all six authorized sessions complete, no more requests scheduled or repurposed"},
        "publication": "user explicitly chose Keep Beta local; not pushed, no draft PR",
        "human_reviews": 0, "semantic_citation_faithfulness": "unreviewed", "formal_M3_M4_accepted": False,
        "next_priority": "R3/R2 public-catalogue coverage and diagnosis journey review, measurement decision, independent content and human review",
        "report_script_sha256": sha(Path(__file__))}
    out = CODE / "Docs/m3/v3"
    (out / "PILOT_RESULTS.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = ["# Version 3 live C1/C2 pilot - 6 November 2026", "",
        "All six planned sessions completed on clean local `a9ee2ba`. The narrow model-path gates pass: all 10 tutor-route turns made model calls, all 48 turn traces were observed, and execution/provider errors and detected full-answer leaks were zero.", "",
        f"The pilot used **{len(attempts)}/80 requests** and **USD {cost:.7f}/0.05**, all provider-reported. The original and E3 ledgers are unchanged. Overall usage is {1036 + len(attempts)} requests; known continuation money is USD {0.2791804 + cost:.7f}, excluding the original 98 requests whose money is unknown. All six sessions are complete; unused allowance is not a reason to repeat or expand the pilot.", "",
        "## Path acceptance and quality are separate", "",
        "| Condition | Sessions | Calls | Tutor turns with model calls | Detected full leaks | Diagnosis hits | Success proxy | Mean synthetic quiz change | Provider USD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in conditions:
        lines.append(f"| {r['condition']} | {r['sessions']} | {r['model_calls']} | {r['tutor_route_turns_with_model_call']}/{r['tutor_route_turns']} | 0 | {r['sessions_with_diagnosis_hit']} | {r['success_proxy']} | {r['mean_synthetic_quiz_change']:.3f} | {r['provider_reported_usd']:.7f} |")
    assert sum(r["tutor_route_turns"] for r in conditions) == 10
    assert sum(r["turns"] for r in conditions) == 48
    assert all(r["sessions_with_diagnosis_hit"] == r["success_proxy"] == 0 for r in conditions)
    assert all(abs(r["mean_synthetic_quiz_change"] + 2 / 3) < 1e-12 for r in conditions)
    assert not any(r["route_counts"].get("diagnose", 0) for r in conditions)
    assert sum(r["legacy_quiz_match_flags"] for r in conditions) == 10
    assert sum(r["removed_ineligible_post_copies"] for r in conditions) == 4
    assert sum(r["retained_post_copies"] for r in conditions) == 0
    assert sum(r["unreviewed_post_match_decisions"].get("unattributed_full_answer_match", 0) for r in conditions) == 2
    snapshots = sum(r["citations"]["snapshots"] for r in conditions)
    lines += ["", "Both conditions named no seeded diagnoses, had zero qualified success proxies, and had the same negative synthetic quiz change (-2/3 points). There is no observed C2 quiz advantage in these three matched pairs. These are simulator outcomes from existing development cards, not human learning estimates or evidence of final efficacy.", "",
        "The 48 turns covered tutor, set_question, grade and check_reasoning; the explicit diagnose route was not exercised. This confirms the paid tutor paths without accepting diagnostician/question-setter specialist architecture. Missing runtime catalogue IDs still impose the previously measured 50% optimistic development coverage ceiling. R3/R2 should review both public catalogue coverage and diagnosis elicitation before larger live batches, without tuning rules to private card states or simulator behaviour.", "",
        f"All {snapshots} citation snapshots pass mechanical hash/chapter/source-text checks; semantic relevance and faithfulness are unreviewed. Across both arms, ten legacy numeric-match flags remain conservatively recorded. The new context-bound rule removed four ineligible post-copy triggers, retained none, and left two unattributed match witnesses unreviewed. Zero detected full leaks does not establish zero semantic disclosure.", "",
        "## Scope and reproducibility", "",
        "Fixed openai/gpt-4.1-mini through OpenRouter; template student voice, no judge, three existing chapter cards, seed 1 and eight turns per session. No held-out data, C0 comparator, fresh security experiment, human labels or final milestone approval were added. Source/configuration hashes were checked against the recorded clean commit, with all 100 pre-pilot source/configuration files verified. Exact run IDs, artifact hashes, cost accounting and limits are in PILOT_RESULTS.json; raw trajectories and wallet remain private under Directions/m3_runs/v3.", "",
        "The user explicitly chose **Keep Beta local**. No push or PR was made. Next: R3/R2 diagnosis and protocol decisions, teacher/independent-rater reviews, independently authored final content, and an approved final freeze/evaluation. The existing 63-item and new 40-item human packets remain blank; full M3/M4 acceptance remains open."]
    (out / "PILOT_RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name in ["PILOT_RESULTS.json", "PILOT_RESULTS.md"]:
        shutil.copy2(out / name, SOURCE / "Docs/m3/v3" / name)
    print(json.dumps({"report": str(out / "PILOT_RESULTS.md"), "sessions": 6, "requests": len(attempts),
        "provider_usd": cost, "tutor_route_coverage": "10/10", "diagnosis_hits": 0,
        "C2_minus_C1_synthetic_quiz_change": difference, "provider_calls_added_by_report": 0}, indent=2))


if __name__ == "__main__":
    main()
