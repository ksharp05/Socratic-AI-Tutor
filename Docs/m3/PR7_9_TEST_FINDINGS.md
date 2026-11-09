# PRs 7-9 after merge: test findings and fix plan

**9 November 2026.** Local Beta now includes R3's PRs 7, 8 and 9 (merge commits `383b261` and `831c06a`). Nothing is pushed or redeployed. There is no code freeze: `BEHAVIOUR_FREEZE.json` pins the code behind the M3 study results, so those results describe the 6 November behaviour and must not be relabelled as describing this code.

## What was run

| Check | Result |
|---|---|
| Full local suite on merged Beta (all four suites, with the 34 local-corpus cases) | 2,665 passed, 7 skipped |
| CI-equivalent run with PRs 7-10 merged in a scratch tree: portable suite, registry check, three smoke gates | 2,631 passed, 7 skipped; registry 2 passed; all gates exit 0 |
| `scripts/qa/stress_last_hint.py`: every one of the 331 public practice items taken to the last hint, then answered correctly, on merged and on pre-merge (`7198b8e`) code | see PR 7 below |
| `scripts/qa/stress_revisit.py`: restart, other chapter, wrong then right, three distinct saved items, learner deletion | see PR 8 below |
| `scripts/qa/stress_phrases.py`: 30 answer phrasings and 6 questions about the phrase, on an empty-answer and a non-empty term-count item, through the parser, the team tutor and the live beta's practice grader; the new leak pattern on 7 ordinary tutor lines | see PR 9 below |

All runs are offline with `TUTOR_LLM=stub` and temporary databases, so no provider calls were made and no budget was used. A live model only drafts free-text replies; the worked example, marking and grading paths are deterministic. The phrasings are hand-written, not real learner data. No browser or mobile check was done.

## What works

- **PR 7 (worked example):** the example appears on exactly the 316 items the service supports (matching the handoff's 316 of 331). The other 15 fall back to the last hint. Across all 331 items: 0 guard fallbacks, 0 leak hits, 0 tool errors, 0 crashes. Every reply cites the chapter passage and asks exactly one question. Pre-merge code showed no example and no citation at this point.
- **PR 8 (saved revisit):** every give-up is saved (331 of 331) and every checked correct answer clears it (331 of 331). After a restart, the question the learner gave up on comes back first; pre-merge code restarts at question 1. Marks stay in their chapter and survive a wrong answer. Three questions saved in three sessions are all served before new ones.
- **PR 9 ('no such term'):** 7 phrasings that were ignored or marked wrong are now graded correct, including "there is no such term", "No such term exists." and "there are no terms". The same phrasings are graded wrong on a question with a real answer. None of the 6 questions about the phrase is graded.

## Shortcomings

| # | Finding | Source | Severity | Where it shows |
|---|---|---|---|---|
| 1 | **The answer the question asks for is rejected.** The 9 practice items whose answer is "none" say *"use an empty set if no such finite AP exists"*. "empty set", "the empty set", "none", "there is no such AP", "does not exist", "no", "zero" and "not possible" are graded **wrong**. "{}", "∅", "None.", "no such AP" and "No such finite AP exists." are rejected as invalid. The term-count parser turns words into fake values, so "empty set" becomes `{emptyset}` and "there is no such AP" becomes `{there}`. The beta's format line under the question says *Write a positive integer term count, or "no valid term count"*, which contradicts the question's own wording. | Pre-existing (`mathcore.parse_answer`) | **High** | **Live beta practice** (grades these wrong); the team tutor ignores them and gives a hint |
| 2 | 'No such term' is only recognised at the end of the answer: "There is no such term in this AP." and "No such term exists in the AP" are not accepted. | PR 9 | Medium | Live beta and team tutor |
| 3 | The new leak pattern over-blocks: 4 of 7 ordinary tutor lines are flagged on empty-answer items, for example "There are no terms before the first one." and "Remember that no term index can be zero or negative." Fixed hints are unaffected (0 fallbacks in 331 runs), but model-written replies on these 9 items will be retried or replaced by the generic fallback more often. | PR 9 | Medium | Team tutor with a live model |
| 4 | No worked example for the 9 'none' items. The service refuses by design because an example sharing the empty answer would reveal it, so the learners stuck on this case only get the last hint. | Service design (R4) | Medium | Team tutor |
| 5 | Example wording is rough for Class 10 students: "= zero", `-x*x + (-16)*x + (44)`, `-1625 - -1100`, a step that says "First" after an earlier step, unsimplified surds. Teaching quality is still unreviewed. | Generator (`parallel_examples.py`) | Medium | Team tutor |
| 6 | Saved questions come back newest first (published-list order), not oldest first, although `read_learner` already returns them in creation order. | PR 8 | Low | Team tutor |
| 7 | The live Vercel beta has neither feature: it uses its own practice flow (`socrates_beta`), not TutorApp. Only PR 9's parser change reaches it, on the next deployment. | Scope | Medium | Live beta |
| 8 | Safety coverage (from PR 10's test messages): neither the team guard nor the live beta catches violence, sexual, hate or alcohol requests. The team guard also wrongly treats "I'm hopeless at trigonometry" as distress; the live beta's pattern does not. | Pre-existing | Medium | Both |
| 9 | Every new session starts from the same first question in the chapter, even one solved before; solved history is per session. | Pre-existing | Low | Team tutor |

After a learner is deleted, every turn raises `GONE`, which the API returns as HTTP 410. This is the same before and after the merge, so it needs no change.

## Fix plan (proposed order)

1. **Term-count answers: findings 1 and 2.** In `mathcore.parse_answer`, for `unit == "terms"`:
   - accept empty-set notation (`{}`, `∅`, "empty set", "none") and "no such AP/term", including endings like "in this AP" and "exists";
   - reject other words with the count-specific message instead of turning them into values;
   - for root sets, also accept `{}` and `∅`.

   Route these phrasings to grading in the router. Make the beta's format line under count questions (`answerHelp` in `static/app.js`) match the question by mentioning the empty set. Turn the phrase matrix into regression tests for the parser, the team tutor and the beta grader. Then redeploy the beta following `Docs/deploy/VERCEL_BETA.md` (no paid calls are needed). *Owners: Swati (`mathcore.py`), Poonam (router in `app.py`), R6 (beta format line). Lakshya merges and redeploys; under the roadmap's separation rule, R5 does not edit `mathcore.py`.*
2. **Narrow the leak pattern: finding 3.** Flag only statements about the answer ("there is/are no (such/valid) term(s)", "no such term exists", "no valid term count"), not wording such as "no term can…" or "no term index…". Add the ordinary lines as must-pass tests. *Swati, in the same change set as step 1.*
3. **Oldest saved question first: finding 6.** Order `_due_revisit` by the `revisit_items` order `read_learner` returns. One-line change plus a test. *Poonam; Rizwan reviews it against the memory contract.*
4. **Safety decision: finding 8, PR 10.**
   - Ask Swati to change PR 10's base to Beta and update the threat model for the live site: real visitors, Postgres learner data, browser cookies, the hosted key and visitor consent, and the real USD cap.
   - Then decide on D-6. A classifier call per message uses the hosted 200-call lease, so options are a cheap rule prefilter, classifying only live-chat messages, or a separate small cap.
   - Fix the "hopeless at …" false alarm in the team guard.
   *Swati builds. Lakshya decides the budget and builds the E2 attack set, which Swati does not see.*
5. **Examples: findings 4 and 5.**
   - Clean up the generator wording: use 0, x², brackets around negatives, and the right step order.
   - Decide how to help on 'none' items without revealing the answer, for example a valid AP that shows the same integrality check.
   - Release as `parallel-example-v4` and never relabel v3 results.
   *Swati builds; Lakshya (R1) reviews the wording.*
6. **Bring both features to the live beta: finding 7.** Add a saved revisit queue per browser profile in Postgres (migration, deletion and isolation tests) and show the checked example after the last hint in `socrates_beta`'s practice flow. Then follow the normal release and HTTPS checks. *Rizwan (Postgres queue, migration, deletion and isolation tests) and R6 (API and UI); Lakshya deploys.*
7. **Cross-session question choice: finding 9.** Skip questions solved recently in earlier sessions. This is a design choice; discuss before building. *Rizwan proposes.*

Alongside these steps:
- R6 runs the pending mobile and browser check of the live beta, and adds the `scripts/qa` stress runs to CI.
- R5b collects how students actually write answers, including Hinglish, and re-runs the stress scripts after each fix.
- Shivam and Sharath still need to confirm which of them is R6 and which is R5b.

Re-run the three `scripts/qa/` stress scripts and the full suite after each step. For example: `python scripts/qa/stress_phrases.py "D:/Work/IITB/Socratic Tutor Main" out.json` with `TUTOR_LLM=stub` and a scratch `TUTOR_VAR_DIR`.
