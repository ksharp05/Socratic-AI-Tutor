# R2/R4 tools ready for R3 integration

6 November 2026. These services are implemented and tested. R3 graph routing remains owned by the R3 contributor. Neither service is connected to learner turns yet; PR4 continues to use its existing fallback.

## Verified parallel worked example (R4, TP-A2/A4)

`math-tools.generate_parallel_example(question_ref)` deterministically changes the public practice item's givens, recomputes its answer with both calculation routes, checks the arithmetic steps and binds the displayed text to those checked steps. Version parallel-example-v3 covers nine connected families: 316 of 331 eligible public practice items receive a checked case-preserving example; 15 receive unavailable because preservation would share an invariant active answer. The example's answer differs from the active answer, with disjoint roots for root sets. The exact displayed example must also pass the existing active-item answer guard. Quiz-only items are rejected by the service.

The tutor role can call this tool only when the controller sets `CallContext.node = "after_last_hint"` and `parallel_example_for` to the active practice ID. A model argument cannot grant this scope. R3 should establish that all hints were used and its repeated-incorrect threshold was met, set the scope only around the tool call, and clear it in `finally`. Display the returned `example.presentation` exactly; do not let a model rewrite a verified proof. Retain the ordinary output guard, teacher publication/version checks and existing last-hint fallback if unavailable or rejected. Never call it from quiz scoring or return an active key to the model. Retrieve the matching public chapter reference through the existing citation path; the arithmetic checker alone is not a source citation.

The response supplies hashes, the source ID and `teacher_review_status: not_reviewed`. It preserves task family, givens fields, answer kind and the declared parallel-cases-v1 signature (discriminant/root/sign cases, AP direction/index/integrality and triangle reference/orientation). This is not matched difficulty or every possible boundary property. The separate exact-reference oracle is an enforced gate. Teaching quality remains unreviewed; no teacher approval is inferred. See BOUNDARY_EXAMPLES.md for availability and limits.

Implementation: `src/tutor/parallel_examples.py`, `src/tutor/mcp_servers/math_tools.py`, `src/tutor/toolbus.py`. Tests: `tests/test_r4_parallel_examples.py` (every connected item, altered proof/text/key, original-key mismatch, quiz denial and role/scope denial).

## Persistent revisit queue (R2)

`learner-store.record_revisit(learner_id, question_ref, reason="after_last_hint")` and `resolve_revisit(learner_id, question_ref)` are study-planner writes. Tutor/grader roles cannot write the queue. Existing learner pinning and deletion checks apply. Reasons are a fixed enum rather than free text. Recording/resolving are idempotent transactions, with an audit event committed atomically; neither awards mastery nor publishes content.

`read_learner` now returns up to 100 pending `revisit_items`, ordered by creation time, filtered to currently eligible public practice and the exact full item hash. Changed/stale rows remain stored for audit but are not scheduled or silently resolved. A record can survive process restart; learner deletion removes it and prevents recreation.

R3 should merge this snapshot into the current chapter's revisit selection while rechecking the teacher-approved publication and active content version. Persist its after-last-hint mark through the code-owned study-planner call; resolve only after deterministic checking of correct learner work. A model's statement that an answer is correct is insufficient. The storage service relies on the controller for that evidence and does not independently grade a learner response. Item eligibility alone is not publication approval.

Implementation: `src/tutor/store.py`, `src/tutor/mcp_servers/learner_store.py`, `src/tutor/learner_privacy.py`, `src/tutor/toolbus.py`. Tests: `tests/test_r2_revisit_store.py` (restart, ownership, version binding, idempotence, transaction faults and privacy deletion).

## Acceptance still required

R3 supplies and reviews the routing integration; R2 reviews the memory contract and actual teacher workflow. Run integrated practice/quiz/restart/deletion checks after that change. No human acceptance, independent final evaluation or improved learning result is claimed by these tool-level checks.

## Latest service revision

parallel-example-v2 binds labelled explanations and task-specific transfer questions to the checked proof; example IDs include renderer version. Use the version and example_sha256 when retaining results; never relabel an old rendering as current. The read-only overview now exposes exact owned totals to students and capped item details only to teachers. R3 still needs to persist marks, resolve only after deterministic correct work, recheck publication/version and wire the example tool. See R4_REVIEW.md and TASK_POOL_AUDIT.md for current review/calibration and evaluation-scope limits.

## Current continuation

The current service is parallel-example-v3; the v2 review above remains historical. Handle available=false through the existing fallback. Display an available presentation unchanged, and do not reuse v2 clarity scores for changed examples. The opt-in simulator protocol v2 fixes canonical empty-count formatting only; R3 should separately review the natural phrase 'there is no such term', which all 18 cached unchecked C2 attempts used. No R3 router or parser was changed for either service revision.
