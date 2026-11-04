# Mounted beta: teacher-approved practice

Date: 4 November 2026. Status: offline development integration; no real educator approval or live-model result is implied.

When the beta is mounted under the capstone API at `/beta`, its practice, quiz and diagnostic question selection queries the capstone question bank. Only published rows labelled teacher-approved are considered, and their content, permitted modes, chapter, source IDs and review metadata must match the current practice or development-check record used by the checker. Each assessment pins the approved set ID and payload digest. The service rechecks the selected question versions before showing them, grading, issuing hints, or replaying an earlier submission. If approval changes, it cancels the active check without grading the new answer or showing a partial quiz summary. An unavailable approval service returns a retryable error instead of granting access.

Mounted assessment actions and question-set edits use the same local database publication lock. A test starts an edit during beta grading and confirms that the operation that acquired the lock first finishes first. This is the same local, cooperating-process boundary described in [publication integrity](PUBLICATION_INTEGRITY.md); it is not a multi-host or direct-SQL guarantee. The question bank currently has a small POC candidate pool, so an approved quiz may contain fewer than five questions. A teacher must publish questions for the requested scope; otherwise the learner gets an availability message.

The API's own checkout supplies the mounted beta's maths adapter and practice slice, even when a standalone beta configuration names a different checkout. The supplied configuration still determines the beta data directory and other settings. The standalone `socrates.ps1` preview does not have the teacher API attached and continues to use the unapproved development pool; the UI and `/api/health` disclose this distinction. Publication tests use synthetic teacher credentials and do not constitute human review.

## What is connected and what is not

- Teacher API authentication, the proposal graph, publication digest and mounted beta assessment selection are connected and tested with a synthetic local API journey.
- The mounted beta continues to use anonymous cookie-owned sessions, beta dialogue, beta observations and its own study view. These are **not** the graph's authenticated learner model, plan, alert inbox or execution trace. No identity is silently equated across the two applications.
- The beta's active-question coaching is still deterministic. The required cited live-model hint, graph trace, real teacher review, fresh Compose run and independent evaluation remain open.
- A revocation prevents subsequent answers from being graded or redisplayed through this adapter. It cannot retract text already delivered, roll back earlier checked answers, or prevent direct database writes outside the application.
- The approval digest binds chapter and supporting passage IDs, but it does not bind the underlying passage text, its URL or external source rights. Data quality, source rights and pedagogical review are separate requirements.

## Offline test

From a project checkout with its application environment and local development data:

```powershell
Set-Location -LiteralPath '<project-checkout>'
$env:SOCRATES_SOURCE_WORKSPACE = (Get-Location).Path
$env:PYTHONPATH = "$((Get-Location).Path)\src;$((Get-Location).Path)\socratic_tutor_dataset_v2\src"
$env:TUTOR_LLM = 'stub'
$python = if (Test-Path '.\.venv_app\Scripts\python.exe') { '.\.venv_app\Scripts\python.exe' } else { '.\.venv\Scripts\python.exe' }
& $python -m pytest tests/test_m2_mounted_approval.py tests/test_m2_mount.py -q
```

The tests use temporary databases, a synthetic passage, simulated teacher tokens and a stub model. They cover no approval, approval and edit, replay after revocation, quiz cancellation, mismatched content, unavailable service, simultaneous edit and grading, and shutdown. They are engineering tests, not independent pedagogical assessment.
