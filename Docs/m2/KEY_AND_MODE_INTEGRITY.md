# Mathematical key integrity and question-mode gap

## Fixed: checked-key cache

The graph's previous `math-tools` cache keyed a calculation only by question ID. A synthetic test reproduced two failures: a result rejected because the independent calculation routes disagreed was stored and accepted as verified on its next use; and a changed mathematical problem under the same question ID reused the old answer. Either can cause an incorrect grading decision.

The new cache stores only results for which both code paths report agreement. It binds entries to a hash of the full problem and to a fingerprint of the loaded maths modules, Python runtime and SymPy version. A checksum detects accidental changes to cached JSON; absent, invalid, legacy or mismatched entries are recomputed. The old `keys` table remains a compatibility mirror but is no longer trusted for reads. This is a local integrity check, not protection against privileged database modification, a substitute for a human review, or a proof that the calculation routes are mathematically independent.

A separate synthetic test showed that an old teacher-approved payload could remain visible after the current runtime problem under the same ID changed. The question bank now hides the **whole set** if any approved item differs from the current runtime pool. The teacher must edit/review and approve the current payload again. This check relies on an unchanged running code/data snapshot; mixed application versions or direct database writes are not certified.

## Open: practice-only items are used in checks

All **665** public practice records in `content/dataset-v0.10.0/practice_questions.jsonl` specify `mode_policy.allowed_modes = ["practice"]`. The graph currently strips that policy from its approval payload and can use those records in a quiz. The standalone beta and mounted beta can also select the same practice-only items for quizzes. Synthetic tests in `test_m2_mode_policy.py` and `test_m2_mounted_approval.py` reproduce the violations and are marked **strict xfail**: they document known failures, not successful tests. Diagnostic checks also need a policy audit.

The browser now disables the connected quiz button and the anonymous beta's quick-check controls, and shows a short explanation. Ordinary typed quiz-start requests in the connected view are also paused. An existing anonymous check offers an exit. This is an **interface-only mitigation**: the underlying APIs can still start or continue non-compliant quizzes, and an existing connected quiz can still receive answers. It is not an authorization or security control.

**Do not use the existing quiz or diagnostic modes as a policy-compliant assessment.** Earlier quiz walkthroughs established engineering behavior only and do not establish that the dataset authorized this usage. This invalidates any milestone claim that the current quiz workflow is ready for assessment, even if its grading and state tests pass.

The remediation needs a separate, explicitly quiz-authorized development question source, with no private or held-out evaluation material; mode and content must be bound into the exact teacher-approved payload. Selection, edits, reapproval, graph grading and both beta paths must enforce that mode. Previously approved payloads that lack a bound usage policy require a safe migration/review decision. All affected tests must be rerun, and the strict expected failures removed only when the actual policy checks pass. A generated development pack and synthetic approval are not independent final evaluation or human educator review.
