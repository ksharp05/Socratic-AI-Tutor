# Mathematical key integrity and question-mode gap

## Fixed: checked-key cache

The graph's previous `math-tools` cache keyed a calculation only by question ID. A synthetic test reproduced two failures: a result rejected because the independent calculation routes disagreed was stored and accepted as verified on its next use; and a changed mathematical problem under the same question ID reused the old answer. Either can cause an incorrect grading decision.

The new cache stores only results for which both code paths report agreement. It binds entries to a hash of the full problem and to a fingerprint of the loaded maths modules, Python runtime and SymPy version. A checksum detects accidental changes to cached JSON; absent, invalid, legacy or mismatched entries are recomputed. The old `keys` table remains a compatibility mirror but is no longer trusted for reads. This is a local integrity check, not protection against privileged database modification, a substitute for a human review, or a proof that the calculation routes are mathematically independent.

A separate synthetic test showed that an old teacher-approved payload could remain visible after the current runtime problem under the same ID changed. The question bank now hides the **whole set** if any approved item differs from the current runtime pool. The teacher must edit/review and approve the current payload again. This check relies on an unchanged running code/data snapshot; mixed application versions or direct database writes are not certified.

## Question-mode enforcement

The earlier implementation selected items marked `allowed_modes = ["practice"]` for quizzes in the graph, standalone beta and mounted beta. Three tests reproduced that issue as strict expected failures. The implementation now enforces the item mode in each of those selection paths and when an active check is resumed or graded; the three tests are ordinary passing tests. A legacy active check containing an item that does not permit its mode is cancelled before grading, without a score or new checked-answer observation.

Teacher approval now hashes the usage policy, question content, chapter, source IDs and review/authorship metadata. Previously published payloads without those bound fields are not served. A teacher can edit and reapprove a practice set with its current payload; a quiz needs a separate proposal in quiz mode. An approved quiz-only item cannot be served as practice. Extra development questions cannot replace a catalog question ID.

The separate [`content/milestone2_dev/quiz_items.json`](../../content/milestone2_dev/quiz_items.json) contains six developer-authored synthetic quadratic questions, permits quiz and diagnostic use, and has no saved answer keys. It is not from private or held-out material. The project's two code paths and an exact symbolic check agreed on the six examples. The content remains pending human review; a synthetic teacher approval in tests is not a human review and the pack is not independent evaluation.

Mode-policy tests cover new selection, old-check cancellation, altered policy/review/source metadata, role boundaries and the mounted approval path. A synthetic localhost browser walkthrough completed the connected quiz and started a mounted beta self-check. This evidence does not establish human teaching quality, all three connected curriculum chapters, a live-model hint or multi-host enforcement. Existing stored scores and observations from prior non-compliant checks were not deleted or retroactively presented as compliant.
