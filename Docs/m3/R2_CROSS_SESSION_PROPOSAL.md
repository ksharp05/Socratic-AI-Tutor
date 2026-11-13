# Proposal: skip questions a learner already solved in earlier sessions

**11 November 2026 · Rizwan (R2). Status: proposed, for discussion. Nothing is built.** Step 7 of the fix plan in [PR7_9_TEST_FINDINGS.md](PR7_9_TEST_FINDINGS.md) (finding 9) says to discuss this before building.

## The problem

- **Team tutor:** the only solved history is the checkpoint's `attempted` list, which belongs to one session. Every new session starts from the same first published question in the chapter, even one the learner solved yesterday.
- **Live beta:** each practice picks a random eligible question, so a solved question can come straight back. The beta already stores what is needed to avoid this: `checked_answer` observations with `question_id` and `status`, owned by the browser profile and deleted by **Forget**.

## Proposal

**Use a soft cooldown, not a hard exclusion.** Choose the next practice question in this order. The order never runs out of questions, and saved revisits always come first:

1. Questions saved for revisit from an earlier session (PR 8 and the beta queue), oldest first.
2. Questions not yet solved, in the current order.
3. Questions solved **outside the cooldown**, least recently solved first.
4. Questions solved inside the cooldown, least recently solved first. This tier is reached only if every other question has been used.

**"Solved" means a code-checked correct practice answer given before the last hint.** A correct answer after the last hint clears the revisit mark but does not start a cooldown, because the learner was led to it. Quiz and diagnostic answers never count. They are assessments, and counting them would let the quiz shape practice selection.

**The cooldown starts at 7 days.** It is set in `config/app.toml` under `[practice] solved_cooldown_days`, so each run's config hash records the value.

## Data: what each surface stores

| | Team tutor | Live beta |
|---|---|---|
| New data | A `solved_items` table in the learner store: `(learner_id, question_ref, content_sha256, last_solved_at, solved_count)` | **No new table.** It is derived from the existing `checked_answer` observations, which gain one field (below). |
| Write | A new study-planner tool, `record_solved`, called from `_grade` after `check_equivalence` returns correct with hint stage below the last hint. It is idempotent and audited in `learner_events`, like `record_revisit`. | Nothing new. The hint stage is added to the `checked_answer` value, so "before the last hint" can be told apart. |
| Read | `read_learner` returns up to 200 recent solved references for the current content hash | `AssessmentService._start` reads this profile's observations in the same transaction |
| Changed question | A different `content_sha256` means the question is treated as unsolved | Same, using the item hash already used by the revisit queue |
| Deletion | Added to the `learner_privacy` table list, deleted with the learner | Already deleted by **Forget** |
| Memory policy | One new row, or an extension of the revisit row | Clarify that observations also steer question choice |

Only question references and timestamps are stored. No answers or chat text are kept, and no model sees the list.

## Effect on evaluation (important)

Question selection changed results before. The v3 task-pool audit traced the diagnosis decline to practice selection ([TASK_POOL_AUDIT.md](https://github.com/ksharp05/Socratic-AI-Tutor/blob/docs-archive-2026-11-14/Docs/product_quality/v3/TASK_POOL_AUDIT.md)). This change alters selection from the second session on, so:

- the switch defaults to **off** for every existing `eval/configs/*.toml` and for frozen runs; old results must never be relabelled;
- with memory off (the E4a `memory_off` arm), the history is neither read nor written;
- the simulator sees it only in runs that explicitly enable it, and the run manifest records the setting.

## Questions to decide

| # | Question | Proposed answer | Decides |
|---|---|---|---|
| Q1 | Does a correct answer after the last hint count as solved? | No. It clears the revisit mark only. | R1 |
| Q2 | How long is the cooldown, and should it depend on mastery, for example skipping all questions on a concept above the `mastered` threshold? | 7 days, fixed. Mastery-based skipping is out of scope until diagnosis is reliable. | R1 + R2 |
| Q3 | Should a repeat give-up on a saved question move it to the back of the queue? (Finding F4 in the [PR 8 review](R2_PR8_MEMORY_REVIEW.md).) | Yes, after a second give-up. Otherwise one hard question leads every session. | R1 + R3 |
| Q4 | Who builds it, and when? | After the freeze. R2 builds the store and the beta read, R3 builds the selection change in `app.py`, R5 adds the evaluation switch. | Lead |

## Tests to write when it is built

- A question solved in session 1 is not served first in session 2. After the cooldown it can return.
- When every question is solved inside the cooldown, practice still serves a question rather than failing.
- A changed question is served as unsolved.
- Quiz answers never start a cooldown.
- Deleting the learner (team) or using **Forget** (beta) removes the history, and another learner or profile is never affected.
- With the switch off, every existing selection test and the simulator's trajectories are unchanged.
