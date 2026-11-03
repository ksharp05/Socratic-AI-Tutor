# Graph quiz recovery and integrity

This document describes the authenticated graph workflow. The mounted beta uses a separate learner store and identity; this work does not connect the two.

## Problem and behavior

An interruption after quiz results were saved but before the graph checkpoint completed could cause the graph to apply those results again on resume. A synthetic interruption test reproduced duplicate learner events, and replay from an old checkpoint could overwrite newer learner progress or a newer study plan.

Completed graph quizzes now have an identifier and a durable SQLite ledger entry bound to the learner and a SHA-256 digest of normalized results. One database transaction applies scorable results to mastery, resolves eligible local stuck alerts, saves the plan, and records the quiz as applied. An identical retry is a no-op; reuse of the identifier with different data or another learner is rejected. A failure during the transaction rolls it back. Concurrent calls sharing the database are serialized by SQLite. Only the study-planner tool role can call the operation, and the tool bus pins the learner identity to the caller's context.

The ledger stores the result digest, identifier, learner ID and application time, not the answer key or the learner's raw response. Generic tool-call traces scrub the result payload. Access to the database and internal planner remains a trusted service boundary, not proof against a privileged process writing to SQLite directly.

## Upgrade and recovery

The table is added when an existing store is opened. A pre-upgrade quiz still in progress receives a stable ID when its next answer is processed. For a pre-upgrade checkpoint already completed but not fully processed, the system cannot establish whether its results were committed before interruption. It therefore skips replay and asks the learner to start a new quiz; it does not claim that the old results were recorded. This fail-closed behavior can lose that old quiz's result.

On recovery of a ledger-backed completed quiz, the current learner state and plan are read from the store. A retry does not overwrite progress or a plan saved after the original quiz transaction. This protection applies to quiz-result application; it is not general HTTP request idempotency or a guarantee that every other graph operation is transactional. SQLite locking is tested for cooperating local connections, not distributed hosts or direct database manipulation.

## Evidence and open work

Offline synthetic tests cover ordinary subsequent turns, interruption and recovery after another session changes both mastery and plan, transaction rollback and retry, concurrent application from two connections, changed payload and learner/role boundaries, and a pre-upgrade completed checkpoint. They use the stub model, synthetic learners and synthetic teacher approval. They do not establish educator review, live-model quality, a full beta-to-graph learner journey, or independent evaluation. See [requirement matrix](REQUIREMENT_MATRIX.md) and [beta assessment integrity](BETA_QUIZ_INTEGRITY.md).

## Unreadable answers during a graph quiz

A response the deterministic checker cannot score leaves the current quiz question open. No quiz result is appended and no quiz mastery or plan update is applied. The learner is asked to enter the answer in the expected format. Regression tests exercise both the first and final quiz question and then submit a scorable answer. This does not mean the parser understands every mathematically valid notation: an unsupported response can still require reformatting.
