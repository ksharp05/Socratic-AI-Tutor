# R2 review: PR 8 saved revisit marks against the memory contract

**11 November 2026 · Rizwan (R2).** Step 3 of the fix plan in [PR7_9_TEST_FINDINGS.md](PR7_9_TEST_FINDINGS.md) asks R2 to review PR 8 against the memory contract.

- **Code reviewed:** PR 8 (`deb260f`, *save revisit marks across sessions*) and its follow-up `0ac3f5f` (*bring back the oldest saved question first*), as merged on Beta.
- **Contract:** the R2 section of [TOOLS_HANDOFF.md](../product_quality/v3/TOOLS_HANDOFF.md#persistent-revisit-queue-r2), the store in `src/tutor/mcp_servers/learner_store.py`, and [MEMORY_POLICY.md](../MEMORY_POLICY.md).
- **Tests:** `tests/test_r2_revisit_store.py` and `tests/test_r3_saved_revisit.py`, 16 tests in all, pass on Python 3.12 with `TUTOR_LLM=stub`.

**Verdict: accepted.** PR 8 meets every clause of the contract. There are no blocking findings. Two small follow-ups are for R3 (F2 and F3), and one documentation gap belonged to R2 and is fixed in this change (F1).

## Contract clauses

| # | Contract clause | PR 8 behaviour | Result |
|---|---|---|---|
| C1 | Only the study planner writes the queue; tutor and grader roles cannot | `_save_revisit` calls `record_revisit` and `resolve_revisit` with role `study_planner`. The ToolBus allowlist (`toolbus.py:28`) gives these tools to no other role. | Meets |
| C2 | Learner pinning and deletion checks apply | Every call goes through `self._call`, so the ToolBus pins the session's own learner. After deletion the store raises `GONE`, which `_save_revisit` re-raises rather than swallowing. | Meets |
| C3 | Reasons come from a fixed list, not free text | PR 8 uses the default `after_last_hint` | Meets |
| C4 | Writes are idempotent and audited | The store does this: re-marking a pending item is a no-op, and a `learner_events` row is committed in the same transaction | Meets (store) |
| C5 | Marks never award mastery or publish content | PR 8 only marks and clears; mastery is unchanged | Meets |
| C6 | Merge the snapshot into the current chapter's selection, rechecking teacher-approved publication and the current content version | `_due_revisit` keeps only rows for the current chapter and serves only items that `question-bank.list_published` still returns. `read_learner` drops rows whose item content hash has changed. | Meets |
| C7 | Clear a mark only after a deterministic check of correct work; a model saying "correct" is not enough | Clearing happens in `_grade`, only when `math-tools.check_equivalence` returns `correct` | Meets |
| C8 | Saving eligibility is not publication approval | Publication is rechecked when an item is served (C6), not when it is saved | Meets |
| C9 | Quizzes are excluded | Only the practice path (`_grade`, `after_last_hint`) calls the queue. The store also rejects quiz-only items with `INVALID_INPUT`, which PR 8 handles by keeping the mark for that session only. | Meets |
| C10 | Survives restart; deletion removes it | Marks live in the learner store. `learner_privacy` deletes `revisit_items` (`learner_privacy.py:22`), and the store's deletion marker stops them being recreated. | Meets |
| C11 | Oldest first (finding 6) | `0ac3f5f` keeps the `created_at` order that `read_learner` returns. A test covers it. | Meets |

## Findings

| # | Finding | Severity | Owner | Action |
|---|---|---|---|---|
| F1 | `MEMORY_POLICY.md` did not list the revisit queue among the stored learner data, its purpose, or its deletion | Low (documentation) | R2 | **Fixed in this change:** added a row covering the team tutor and the live beta |
| F2 | A clear only reaches the store if the item is in `_marked(state)`. That set holds this session's marks plus the snapshot's saved rows, and the snapshot is capped at 100. A learner with more than 100 pending marks could correctly solve one beyond the cap without the mark being cleared. `resolve_revisit` is idempotent, so calling it after *every* checked correct practice answer is simpler and has no gap. | Low | R3 | Optional one-line change in `_grade` |
| F3 | The trace records the clear under node `after_last_hint`, although `_grade` makes the call. Audit readers would see the wrong node. | Low | R3 | Pass the node name into `_save_revisit` |
| F4 | A saved question that is served again and given up again keeps its original `created_at`. It stays first in every later session until it is solved, so one hard question can lead every session. The store's contract says re-marking keeps the place, so this is intended behaviour, not a bug. The live-beta queue in this change behaves the same way for consistency. | Design question | R1 + R2 + R3 | Decide whether a repeat give-up should move the item to the back. Recorded as Q3 in [R2_CROSS_SESSION_PROPOSAL.md](R2_CROSS_SESSION_PROPOSAL.md). |

No finding affects privacy or deletion. The queue stores question references, a content hash, the chapter, the reason and timestamps. It stores no answers and no chat text.
