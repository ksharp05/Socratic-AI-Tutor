# Publication integrity: development verification

Date: 4 November 2026. Status: implemented and tested offline; not a release approval.

The normal tutor only lists a set when its publication is labelled teacher-approved, its proposal is still published, and the stored proposal and publication payloads both match the same current digest. Editing or rejecting the proposal makes its previous published row invisible to the tutor until a new approval and publication. Publication recomputes the proposal digest, verifies the approval token, and updates both records in one SQLite write transaction. Concurrent publication and edits use SQLite write locking; a synthetic two-connection test covers the exercised ordering.

When starting a practice question or quiz, the session records the set ID and payload digest. On later turns the tutor checks the current published list before continuing. If a set has changed, or its approval cannot be checked, it clears the active question and quiz without grading the incoming answer. This check is applied in both C1 and C2, even when the optional defence toggle is off. Sessions created before version provenance was added fail closed and need a new question or quiz.

Synthetic evaluation fixtures are permitted only with an explicit server-side development flag, disabled by default. Simulator and security manifests record that the flag is enabled and label the fixtures as unapproved. Synthetic teacher identities and approvals in tests are test inputs, not evidence of educator review.

## Evidence

The working-tree run of all four offline suites on this machine passed **230 tests**: `tests`, `tests_beta`, `tests_book_pipeline`, and `tests_integration_v02`. The new focused tests cover edited and rejected proposals, tampered payloads, fixture isolation, a concurrent edit/publication ordering, stale practice and quizzes in both architectures with optional defences on and off, and publication-check failure. The default `pytest` selection only covers `tests`; an explicit selection of all four suites is necessary. Tests use stub models and synthetic identities; they make no live provider calls.

## Limits and release work

- Learner `turn` and `resume`, and question-bank edit/publish/reject calls through `ToolBus`, now take the same file lock for the canonical SQLite database path. A turn that acquires the lock first completes before an edit can commit; an edit that completes first is observed by the next turn. A two-app threading test and a separate-process lock contention test exercised this behavior on Windows. The 30-second timeout returns a retryable busy error. This is coarse-grained: a slow model call can delay other turns or edits.
- This guarantee requires every participant to use the application lock and the same canonical database path on a filesystem with functioning OS locks. Raw SQL, direct graph invocation, independently served MCP tools, hard-link aliases, and filesystems or hosts without reliable shared locking are outside the tested boundary. POSIX, network filesystems and multi-host deployment were not tested. Streaming currently computes a complete response before the stream begins, so content already generated or delivered is not withdrawn.
- An interrupted turn is revalidated before resuming. If approval is unavailable, the remaining graph is cancelled and a replacement message is recorded. Any grading or learner-state writes completed before the interruption cannot be rolled back merely by cancelling the remainder. Older session records without publication provenance fail closed.
- Publication verification assumes the application database and its approval secret are trusted. It detects the tested stale or corrupted payload cases, not a privileged attacker able to rewrite all database records and application state. The existing published row is replaced on reapproval; it is not an immutable approval history.
- The checks do not establish the educational quality or human approval of a question, prove all mathematical answers correct, or verify the live integrated teacher/learner journey.
- Docker/fresh-machine verification, a bounded explicitly authorized live-model test, independent evaluation and educational review remain outstanding; see [the verification snapshot](VERIFICATION.md) and [requirements matrix](REQUIREMENT_MATRIX.md).

## Follow-up verification — 4 November

A new offline test reproduced each race for both C1 and C2 before the change. The application now serializes cooperating processes without holding an SQLite transaction across model calls or blocking the MCP event-loop thread. Separate tests cover cross-process lock contention and an interrupted correct grade whose active question has already been cleared. Docker, a fresh dependency installation and other operating systems have not been tested.

The final working-tree run passed **238 offline tests** across all four suites, including both same-app and separate-app contention and the separate-process lock check. It used existing local environments and did not exercise Docker or a live provider.
