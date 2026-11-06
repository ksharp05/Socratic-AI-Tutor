# Actual remote CI failure and portability correction

6 November 2026. [Run 42208855204](https://github.com/ksharp05/Socratic-AI-Tutor/actions/runs/42208855204), commit 3e27ab4, actually failed on GitHub's Ubuntu runner: **1389 passed, 34 fixture errors**. No deliberate product break was introduced.

Enabling the four-directory suite on Beta exposed a local-artifact dependency: 29 Beta integration cases require the authorized external book build, and five snapshot contracts require the external expanded dataset. Those artifacts intentionally stay outside GitHub; uploading them to make CI pass would violate the user's privacy/publication boundary.

The correction explicitly marks only those artifact-dependent tests as local_corpus (28 parametrized Beta functions = 29 cases, plus the five-case SnapshotContract class). Portable import, parser, ownership, human-review-gate and synthetic index-registration tests remain in CI. Strict marker validation prevents misspelled markers from silently changing selection.

Portable CI runs pytest over all four test directories with --strict-markers -m "not local_corpus". The canonical full-data workspace runs the entire suite without that exclusion, or -m local_corpus to audit the 34 external-artifact cases separately. A portable pass does not claim those 34 ran remotely. Local recovery passes both partitions: 1389 portable tests and all 34 corpus-dependent tests (1423 total). [Recovery run 42210471805](https://github.com/ksharp05/Socratic-AI-Tutor/actions/runs/42210471805) on 214b7ef is now **successful**: 1389 portable tests pass, 34 local-corpus cases are explicitly deselected, synthetic registration passes, and C1/C2/security smoke gates all pass. Documentation-only pushes are excluded from repeat CI; pull-request CI remains unchanged.

Private failure ZIP/test logs and selection receipts remain under Directions/git_delivery. They are not uploaded to GitHub. Independent installation by another person remains a separate human gate.

---

The older note below records the state before this actual failure.

# Required CI failure demonstration - not yet available

The M4 checklist (`Docs/plan/08-schedule.md`) asks for an actual failed CI run and its explanation. On 5 November 2026, a read-only GitHub Actions REST query for repository workflow runs with `status=failure` returned no runs. No failure logs or failed Beta run can therefore be cited. The successful baseline run is 41908712265 on 3dd518a; local Beta remains unpushed.

This item is **pending**, not a passed requirement. No intentionally broken commit, push or workflow dispatch has been created. When remote demonstration work is authorized, use an isolated test branch/run, capture the actual failing gate/log, explain its cause and the verified fix, then link both runs here. Keep the local Beta behavior checkpoint intact. A hypothetical failure description or a local failed command is not a failed remote CI run.

Private query receipt: `Directions/m3_runs/v2/validation/CI_FAILURE_HISTORY.json`. Read-only query, no new workflow created.
