# Chapter quizzes and plans

The authenticated connected graph can run a teacher-published quiz in each of the three Class 10 chapters. The existing six-question quadratic development pack is joined by a separate six-question AP/trigonometry development pack: three AP term/sum questions and three right-triangle-ratio questions. These are developer-authored synthetic demonstration questions, not textbook exercises or independent evaluation cases. They remain pending human review, allow quiz/diagnostic use only, and cannot be published until a teacher approves the exact proposal payload. The existing 120 public AP/trigonometry questions remain practice-only.

The maths service calculates and verifies each key before the quiz starts. Answers are checked in quiz mode without intermediate hints or scores; an unscorable response leaves the question open. At completion, one SQLite transaction applies the results, updates concept observations, writes the chapter plan and records the quiz ledger entry. A replay with the same identifier and results is a no-op; changed results or a different chapter cannot reuse the identifier. An interrupted completed turn recovers without overwriting a newer plan. This uses cooperating processes and the local database, not a distributed lock or protection against privileged database writes.

## Planning and compatibility

The original quadratic `plans` record is retained. AP and trigonometry plans are stored separately per learner and chapter in the additive `topic_plans` table, created when an existing database is opened; opening an old database preserves its quadratic record. After a complete chapter quiz, the deterministic development policy prioritises concepts associated with incorrect questions, shows the number of associated incorrect answers and records supporting question IDs. A question can be associated with several concepts: this does not diagnose which concept caused the error, prove mastery, or establish learning. Only the learner's authenticated API response exposes their plans; the teacher path has its existing permissions. The connected browser switches plans with the selected chapter and restores them after signing back in.

Existing software versions that predate the new table do not display chapter plans. Back up the database before upgrading or reverting. Existing graph checkpoints and quiz ledger entries are retained; legacy quadratic digest handling remains compatible. No full export/deletion workflow or multi-host upgrade/rollback procedure has been verified.

## Evidence and limits

The six keys were checked against explicit exact arithmetic in the tests, alongside the two existing calculator routes. Synthetic API tests cover two learners, chapter-scoped approvals, scores and plan reasons, isolation from the quadratic plan, unscorable input, role access, transaction rollback, duplicate application, and a resumed interrupted quiz after a newer plan. A local stub-model browser walkthrough exercised an AP quiz, its chapter plan and refresh/sign-in recovery; trigonometry was tested through the API. Neither the developer-authored pack nor a synthetic teacher approval is human review or independent evaluation. A real-model Socratic hint, human teaching quality, source rights, fresh Compose deployment, and a live integrated demonstration remain unverified.


Checked right-triangle practice now supports three provisional error hypotheses with explicit ambiguity handling. See [trigonometry hypotheses](TRIGONOMETRY_HYPOTHESES.md); broader diagnosis remains incomplete.
