# M3/M4 checkpoint - complete development E1-E4, final human gates open

All project commands use canonical `D:\Work\IITB\Socratic Tutor` as cwd. Code/Git are in `D:\Work\IITB\Socratic Tutor Main`, local branch **Beta**. Mirror changed files; do not push. Start with `Docs/m4/E3_COMPLETE_RESULTS.md` and `Docs/m4/README.md`.

## Completed and verified

- Original development matrix is now complete: E1 C0/C1/C2 each 48 sessions; E3 candidate **48/48** (36 original + 12 explicitly approved completion), matched to 16 source cards x seeds 1/2/3. E4 memory-off/telling each 16, matched C2 seed-1 reused; E2 40 seen attacks + 40 controls per selected-guard condition. Total **224 unique study tutoring sessions**, 160 safety cases, four separate pilot sessions.
- Frozen teaching behaviour is `12d541e`, tag `beta-m3-behaviour-v2`: 496 full regressions, six two-card smokes and three CI gates, 4/4 C1/C2 replay, 158 frozen-build files and seven public-copy hashes verified. Post-run reporting/budget gate full suite: 500 passes. Latest focused aggregation/budget/evaluation checks: **48 passed**, 8.86 seconds. Source/data/app-config/playbook hashes are verified across E3 batches; only the previously committed harness budget-receipt wiring and provider-budget extension differ from frozen v2 runtime. Approved new run executed on clean `a463675`.
- All **899/899** tutoring citation snapshots match hash/chapter/source text. Mechanical integrity is established; semantic faithfulness is unmeasured. Baseline Actions passed on 3dd518a (run41908712265); local Beta has no remote CI run. No pushes occurred.
- Complete offline sensitivity reproduces **224/224** recorded simulator outcomes using saved tutor replies/grades. With post copying disabled, C0/C1/C2 and full E3 have mean gain0.104; E3-vs-C2, C2-vs-C0/C1 and memory on/off quiz differences are zero. The original primary E3 quiz difference is +0.0208 [0,0.0625], success/cleared differences zero. This post-hoc fixed-trajectory sensitivity is not an independent tutor rerun or learning evidence. Original primary outcomes are preserved.

## Budget and no further provider work

The user explicitly answered: **“Approve up to 50 extra requests, maximum additional USD 0.03”.** Receipt: `Directions/m3_runs/v2/live/E3_EXTENSION_APPROVAL.json`, now approved, linked by hash to the unchanged original wallet.

- Original wallet `Directions/m3_runs/provider_budget.json`: 902 new +98 prior =1,000, SHA-256 `2b0e529b378dfc7c68be4375a89a859b9c3c173dbc23f543a602c2c0cdd8b9de`, byte-identical.
- Separate chained extension wallet `Directions/m3_runs/provider_budget_extension_e3.json`: **36 completed attempts**, USD **0.0132756**, zero errors/reservations/refusals, all cost exposed; within50/USD0.03.
- Total **1,036/1,050** permitted attempts; known continuation money **USD0.2791804** for938 new attempts. The prior98 monetary cost is unknown and excluded. No voice/judge calls.
- Fourteen purpose-specific extension requests are unused. All12 remaining E3 sessions are complete: no further call, retry or duplicate run is needed or scheduled. Do not reuse unused allowance for another experiment or reset either wallet.

The completed source run is in live INDEX key `e3_after_remaining4`; its manifest is `m3_live_e3_remaining4-20261105-074756-8c7792e028ac`. Aggregate receipt `Directions/m3_runs/v2/live/E3_COMPLETION.json`; exact run/config/data/hash and ledger receipts in `Docs/m4/E3_COMPLETE_RESULTS.json`. Original36+new12 are disjoint and exactly cover the C2 cohort.

## Preserved evidence and safe tools

Original1,000-request report and212-session sensitivity are retained in `Docs/m4/RESULTS.*`, `POST_COPY_SENSITIVITY.*`, local tag `beta-m4-request-cap-1000` (`dffdde2`) and private `Directions/m3_runs/v2/report_archive/requests_1000/`. Original v1 failures remain preserved. Read their partial-E3 counts as historical.

Current complete report: `Docs/m4/E3_COMPLETE_RESULTS.md`, matching JSON and `E3_COMPLETE_CONDITIONS.csv`. Complete sensitivity: `POST_COPY_SENSITIVITY_E3_COMPLETE.md/json`, with private per-session audit in validation/. Do not rerun original full-E3 or `complete_e3.py`; the latter deliberately rejects existing attempts/artifacts. `e3_complete_results.py` reads saved data only. `post_copy_sensitivity.py --include-extension` regenerates the versioned224-session analysis, no provider calls. The old `deliver_results.py` intentionally describes the original1,000-call boundary and must not be used for the new extension. Use the shared checkout `.venv/Scripts/python.exe` for tutor tests; canonical dataset `.venv` has no pytest.

## Data, scoring and external gates

Data: 16 source development cards,22 quiz pairs/44 records,17 seeded types,160 internally consistent golden cases. Eight types lack runtime diagnosis adapters; five card/misconception associations cannot show in assigned quiz scores. Runtime:131 registered practice items,12 quizzes,22 concepts/cards,nine diagnosis types. Candidate-final24 cards/30 pairs remain unexported/unrun, independent authorship absent. Development coverage is sufficient for this engineering study, not final independent qualification.

Uncalibrated post-answer numeric matches occur in86/224 sessions and trigger simulator copying, including generic numeric instructions. No post-question text exposure was detected. Treat quiz changes as recorded synthetic outcomes, not clean learning estimates. C2 has no success-proxy benefit; diagnosis recall is low. Safety unknowns remain27/80 per condition, not passed attacks.

Human-only gates remain: R2 final preregistration approval (still draft), teacher actual lesson decisions/rejection reasons, independent raters/semantic review, independently authored final material/new hidden attacks, judge calibration or an explicitly approved limitation, failed-CI demonstration if required, and another member’s clean-machine/team verification. Budget approval is not any of these approvals. Review CSVs remain blank under `Directions/m3_runs/v2/live/review_packet_context_v2/` (63 items; mapping hidden) and human_actions/. Do not invent final acceptance.

The one-time06:32 IST continuation ran, checked the then-pending approval, and was deleted as completed. The later real user answer authorized this finished extension; no resumption automation remains. The formal M3/M4 goal remains incomplete solely on the external final gates above; actionable development execution/reporting is complete.
