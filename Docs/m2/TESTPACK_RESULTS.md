# Development test pack: first offline run

**Date:** 5 November 2026. **Code:** `79b57c2` plus the uncommitted runner. **Mode:** stub model, no provider calls. **Run:** `testpack-20261105T013707-6876f7`, with three cases rerun as `testpack-20261105T013921-9fb441` after runner fixes. Raw responses, observations and scores stay in ignored `Directions/testpack_runs/`.

The pack is the user-supplied *IITB Socratic Tutor Development Test Pack v1*: 180 synthetic development cases (SHA-256 `3d29de42…`). It labels itself unreviewed and not held-out. These results are development findings, not an independent evaluation, and not evidence of learning or teaching quality.

## How it was run

`scripts/m2/testpack_run.py <pack_dir>` drives the real connected API in-process, with a fresh isolated store per case. Only `case.input` reaches the app. The pack's own `eval_cli.py score` scores the responses.

- **Maths:** the runner translates each problem's wording into the app kernel's typed task (adapter work, not an app feature) and records the kernel's answer.
- **Tutoring:** each case runs two ways. *Typed*: the learner types the problem and their mistake, which is how a learner would bring it. *Registered*: where the problem fits a connected practice family, a development-only copy is published and the mistake is sent after `practice`.
- **Retrieval:** the 24 synthetic notes replace the reference cards inside the app's real `textbook-kb` search (chapter-scoped BM25, top 3).
- **Journeys, safety, workflow:** run through the real chat, quiz, teacher and learner APIs. Quiz scores are scaled to the app's three-question quizzes. Answer-leak and state-change checks use the app's kernel and stored state.

## Results

| Suite | Automatic result | What it means |
| --- | --- | --- |
| Maths (54) | 51 match, 3 unsupported | Kernel agrees with every translated reference. `sin(90°−30°)`, `cos(90°−θ)` and `sin²30°+cos²30°` have no matching task family. |
| Tutoring (54) | 54/54 contain a question; 0 answer leaks detected | Typed path: 42 of 53 replies are the same generic "What first step could you try…?". Registered path (31 cases): family-level template hints, also repeated. Stub mode; the typed path stays template-only in live mode too. |
| Retrieval (24) | 20 hit within top 3 | Misses: "tangent… sine and cosine" and "secant, cosecant and cotangent" return **no results** (spelled-out ratio names never match `tan/sin/cos/sec`); "three basic trigonometric ratios" and "do AP terms need to remain positive" rank the wrong note. Citation presence not measured. |
| Journeys (12) | 7 match the expected re-plan direction | After a perfect AP or trigonometry quiz the plan still says *practise* the same quizzed concepts, with `mastered` empty even at mastery 1.0. After a failed quadratic quiz, the plan's first step is an unrelated foundation concept (`qe01`) and does not mention the quiz mistakes. "What should I practise next?" in chat gets the generic hint, not the plan. |
| Safety (20) | 10/10 attacks with no unsafe action; 10/10 controls not refused | No leak, state change, secret or other learner's data seen. But 8 practice-mode messages, attacks and controls alike, got the same quadratic hint, and all 10 quiz-mode messages got "I could not read that answer". Safe, but benign requests are not helped. |
| Workflow (16) | 12 pass | Failures: learner self-deletion (teacher-only by design, so 403); stuck alert never fires for a new learner (below); no external alert delivery (teacher-view only); `model_identified` absent because stub mode makes no model call. |

**Stuck alert:** a stuck report counts only when it maps to one concept. Practice questions carry three concept tags, and a new learner has no flagged misconception to narrow them, so three sessions of "I am stuck" recorded nothing. The existing unit test passes only because its demo learner starts with a flagged misconception.

**Display:** public practice prompts show raw coefficients, for example `(5)*x^2+(-100)*x+(510)=0`.

## Runner problems found and fixed

Implicit multiplication (`5x`) failed to parse. Conversation state carries no problem givens, so answers are now read from the publication. The approval probes needed the full ordered sequence. A brand-new learner's missing "before" plan hid a recorded re-plan. One trig-identity translation was wrong and is now unsupported. Unsupported maths was written as `null`, which crashed the pack scorer; the saved file was rewritten to `{}`, with the raw original kept. The direction rule scores QU-002 as "continue", although the app's first step is labelled `remediate`.

## Not covered

No live model; human rubric scoring of replies; citation faithfulness; journey continuity across real sessions; C1/C2 comparison on the pack's development cards.

## Communication change and live rerun - 5 November

The first run showed the tutor rarely answered what the learner said. Three changes followed:

- **Session questions answered directly** (`src/tutor/conversation.py`, new `converse` route). Requests about the plan or results, frustration, a smaller step, approval, deletion, traces, citations, keys, other learners' data, commands and score changes get a factual, policy-accurate reply plus the current hint. Answer-like messages still go to grading, and the refusal for teacher impersonation is now separate from the answer-key refusal.
- **Quiz chat:** a hint request or recognised non-answer explains the no-hints rule without scoring it; unreadable answers keep the old message.
- **Typed-in problems in the opt-in contextual mode:** one screened model reply that responds to the learner's described step. It is rejected unless it is a single question of at most 60 words, with no answer phrase, no number the learner did not write, and only a retrieved source ID. This reverses the earlier deterministic-only rule for this path; the check label now distinguishes `screened_model_reply_not_answer_checked`.

The answer-leak checker flagged the first citation sentence ("If none covers…") as claiming no real roots, so the wording was changed. That checker can produce false positives on ordinary English.

| Run | Mode | Pass / fail / pending | Typed tutoring replies | Provider calls |
| --- | --- | --- | --- | --- |
| `testpack-20261105T013707-6876f7` | stub, before | 162 / 16 / 26 | 8 distinct of 53 (42 identical) | 0 |
| offline rerun after the change | stub | 165 / 12 / 27 | template path unchanged offline | 0 |
| `testpack-20261105T015243-c977ea` | live, `openai/gpt-4.1-mini`, cap 300 | 166 / 11 / 27 | 47 distinct of 54, most common repeated 5 times | 95 |

Live detail: own-problem replies were accepted 49 of 54 times (4 rejected for length or question count, 1 for an answer phrase). Registered hints were accepted 37 of 38 (one provider error fell back). About 47,500 input and 2,900 output tokens were used; the provider reported no cost. The adapter detected no answer leak in either tutoring path, and no unsafe safety action. Remaining failures are unchanged: four retrieval misses, plans that do not advance, and three workflow design gaps. Learner-facing model replies have not had human review, and some give a method formula (for example the AP sum formula), which a teacher may or may not want.
