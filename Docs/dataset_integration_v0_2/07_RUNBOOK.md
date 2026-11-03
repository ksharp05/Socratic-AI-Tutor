# Runbook

Run from `D:\Work\IITB\Socratic Tutor`. These commands preserve the original package. Do not execute its `scripts/build.py`. The normal package validator writes its report, so use only the isolated copy below.

## Source checks and audit

```powershell
Set-Location -LiteralPath 'D:\Work\IITB\Socratic Tutor'
$env:PYTHONPATH = "$PWD\src;$PWD\socratic_tutor_dataset_v2\src"
.\.venv\Scripts\python.exe -X utf8 Directions\_integration_work\2fb0ffbb67ae8e5c\input_snapshot\scripts\validate.py
.\.venv\Scripts\python.exe -X utf8 -m v02_integration.audit --source Directions\socratic_tutor_dataset_expanded_v0_2 --output Docs\dataset_integration_v0_2
.\.venv\Scripts\python.exe -X utf8 -m v02_integration.repair --source Directions\socratic_tutor_dataset_expanded_v0_2 --destination Directions\_integration_work\2fb0ffbb67ae8e5c\derived_v0_2_1 --report Docs\dataset_integration_v0_2\evidence\metadata_repair.json
```

Expected: 17 supplied checks, 232 exact public-prompt matches, 116 pending review items, original source unchanged; the original audit reports 2,040 family defects, while the derivative has zero. All 20 corrected inventory counts are 120. Re-running does not convert review status or create independent test data.

## Automated tests

```powershell
$env:PYTHONPATH = "D:\Work\IITB\Socratic Tutor Main\src;$PWD\src"
& 'D:\Work\IITB\Socratic Tutor Main\.venv\Scripts\python.exe' -X utf8 -m unittest discover -s tests_integration_v02 -v
```

Expected: 38 integration tests, including 9 actual Main-graph fixture tests and 9 private-ledger tests. The existing baseline's 30 mode/model/tool tests were run separately with its three test files (`test_flows.py`, `test_llm_setup.py`, `test_mcp_tools.py`) and temporary state under Directions. Evidence is in `evidence/existing_runtime_tests.log`. Neither suite is an independent pedagogy or red-team result.

## Bounded real model probe

`LLM_API_KEY` or `OPENROUTER_API_KEY` must be available to the existing app configuration. Optional variable names are `LLM_BASE_URL`, `LLM_MODEL`, `TUTOR_LLM` and `TUTOR_VAR_DIR`. No credential values belong in commands, files shared through Git or reports.

```powershell
$env:PYTHONPATH = "D:\Work\IITB\Socratic Tutor Main\src;$PWD\src"
$probeState = Join-Path $PWD ('Directions\_integration_work\2fb0ffbb67ae8e5c\probe_' + [guid]::NewGuid().ToString('N'))
& 'D:\Work\IITB\Socratic Tutor Main\.venv\Scripts\python.exe' -X utf8 -m v02_integration.live_probe --app-root 'D:\Work\IITB\Socratic Tutor Main' --state-dir $probeState --adapter contextual --active-item --include-wrong-attempt --report Docs\dataset_integration_v0_2\evidence\my_contextual_probe.json
```

The adapter is opt-in and the state path must be new. Maximum two client invocations, no retries, bounded output. This is a small paid-provider smoke test, not E1 to E4. Inspect successful response counts, each route's events, accepted/fallback generation and zero quiz calls. Do not rerun merely to select an attractive response. The recorded current-source evidence has two accepted replies: code-graded wrong-answer feedback and an active-item hint. Quiz routes made zero calls; provider cost was unavailable. No further paid probe is needed without a code change or unresolved concern.

## Human review and promotion

1. R1/R2 review `03_REVIEW_QUEUE.csv`; two raters independently fill their respective `review_views/` CSVs.
2. R1/R2/R4 create a new ratified policy using `review_templates/active_policy.template.json`, preserving the proposed minimum thresholds unless an explicit change is approved. Supply actual owner and ratification evidence, explicit `thresholds`, and distinct authorized subject/pedagogy reviewers in a protected registry. The pending policy and empty registry remain unapproved examples.
3. Write a reviewed revision and a separate decision using `review_templates/`. Bind exact source, revision and active policy-content hashes with `v02_integration.audit.digest`; add actual scores and a timestamp with timezone. `decision.policy_sha256` must match the entire active policy, not just its ID. Templates are not approvals.
4. Promote into a new ignored versioned folder only after the evidence is genuine:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m v02_integration.promotion --source Directions\socratic_tutor_dataset_expanded_v0_2 --revision path\reviewed_revision.json --decision path\human_decision.json --policy path\ratified_policy.json --reviewer-registry path\authorized_reviewers.json --destination Directions\_integration_work\2fb0ffbb67ae8e5c\approved\v0001
```

Replace the review-specific paths. With this destination, the separate private ledger is `Directions\_integration_work\2fb0ffbb67ae8e5c\approved\v0001.review_evidence\review_ledger.json`. Optionally pass `--review-evidence-directory path\staff_only_versioned_ledger`; it must be outside the runtime projection and original source. The runtime directory contains only `examples.jsonl` and `MANIFEST.json`. Preserve staff-only access to the ledger. Both outputs are immutable per version; publish a new version for changes. The command fails with unratified defaults, stale hashes, AI approvals, insufficient scores, T08 or unknown/private fields. Do not fake inputs to make it pass. R3 pins the resulting manifest hash and policy in trusted server configuration; learner text cannot select these values. Default runtime approved-example count remains zero.

## Git and reproducibility

```powershell
git --git-dir='D:\Work\IITB\Socratic Tutor\.git' --work-tree='D:\Work\IITB\Socratic Tutor' check-ignore -v -- Directions/socratic_tutor_dataset_expanded_v0_2/README.md
```

`evidence/input_snapshot.json` binds the 26 original files. `coverage_metrics.json` gives the same source snapshot hash. `evidence/reproducibility.json` records exact reproduction of core metrics, excluding measured elapsed time, and six selected review/projection artifacts. Live outputs and timings are observed evidence and are not claimed deterministic.

No automatic external acquisition occurs. No held-out files are exposed to tuning. Preserve archived failed probes as well as successful evidence.


## Next three executable owner actions

1. **R1/R2/R4 — ratify and review.** Assign actual humans, then work through `03_REVIEW_QUEUE.csv` and the templates. Run the promotion command above only after genuine review. Acceptance: policy-content/source/revision hashes bind, distinct subject/pedagogy reviews meet ratified thresholds, and the private ledger is retained. Until then the expected default is a rejected promotion and zero approved examples.
2. **R3/R4 — review and enable.** Run the 38-test command above, review `src/v02_integration/runtime.py` and `05_INTEGRATION_DESIGN.md`, then implement the opt-in app factory/feature flag in the team checkout. Acceptance: human-reviewed three-chapter practice/API/UI traces, code-owned grades, zero quiz model hints, protected partial-answer handling, role/tool checks and a rollback to baseline. The present smoke test does not satisfy this deployment gate.
3. **R5 — commission and freeze evaluation.** Follow `06_EVALUATION_PROTOCOL.md` to create 30 new dialogues and 120 messages outside tuner access, with provenance and a frozen manifest before any final run. Acceptance: genuinely separate authorship, family-overlap checks, preserved per-rater labels and calibration on at least 30 development turns; actual E1–E4 results and learning measurements are recorded later, not prefilled.
