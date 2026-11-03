# Publication integrity: development verification

Date: 4 November 2026. Status: implemented and tested offline; not a release approval.

The normal tutor only lists a set when its publication is labelled teacher-approved, its proposal is still published, and the stored proposal and publication payloads both match the same current digest. Editing or rejecting the proposal makes its previous published row invisible to the tutor until a new approval and publication. Publication recomputes the proposal digest, verifies the approval token, and updates both records in one SQLite write transaction. Concurrent publication and edits use SQLite write locking; a synthetic two-connection test covers the exercised ordering.

When starting a practice question or quiz, the session records the set ID and payload digest. On later turns the tutor checks the current published list before continuing. If a set has changed, or its approval cannot be checked, it clears the active question and quiz without grading the incoming answer. This check is applied in both C1 and C2, even when the optional defence toggle is off. Sessions created before version provenance was added fail closed and need a new question or quiz.

Synthetic evaluation fixtures are permitted only with an explicit server-side development flag, disabled by default. Simulator and security manifests record that the flag is enabled and label the fixtures as unapproved. Synthetic teacher identities and approvals in tests are test inputs, not evidence of educator review.

## Evidence

The working-tree run of all four offline suites on this machine passed **230 tests**: `tests`, `tests_beta`, `tests_book_pipeline`, and `tests_integration_v02`. The new focused tests cover edited and rejected proposals, tampered payloads, fixture isolation, a concurrent edit/publication ordering, stale practice and quizzes in both architectures with optional defences on and off, and publication-check failure. The default `pytest` selection only covers `tests`; an explicit selection of all four suites is necessary. Tests use stub models and synthetic identities; they make no live provider calls.

## Limits and release work

- The turn-level validation is a check before processing, not a transaction spanning a complete learner turn. A simultaneous edit after that check could still race with grading or responding; coordinate or serialize teacher updates and learner actions before claiming strict immediate revocation under concurrency.
- Publication verification assumes the application database and its approval secret are trusted. It detects the tested stale or corrupted payload cases, not a privileged attacker able to rewrite all database records and application state. The existing published row is replaced on reapproval; it is not an immutable approval history.
- The checks do not establish the educational quality or human approval of a question, prove all mathematical answers correct, or verify the live integrated teacher/learner journey.
- Docker/fresh-machine verification, a bounded explicitly authorized live-model test, independent evaluation and educational review remain outstanding; see [the verification snapshot](VERIFICATION.md) and [requirements matrix](REQUIREMENT_MATRIX.md).
