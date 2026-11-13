# R3 review of the step-feedback code (task C2)

**Reviewer:** Poonam (R3) · **Author of the code:** Lakshya (Lead), commit `cf14173` · **Reviewed on:** `Beta` at `2b0d18c`, 13 Nov 2026 · **Task:** C2 in [TEAM_ROLE_PLAN_2026-11-13.md](TEAM_ROLE_PLAN_2026-11-13.md)

**Verdict: safe to build on, with one decision for R1 and two small bugs to fix.**
- The code never crashed, never slowed down and never put a number in a reply.
- All 66 replies exist in English, Hindi and Hinglish.
- Before this review, GitHub CI never ran `ratio_hint.py` at all. This PR adds 174 portable tests (172 pass; 2 are strict expected failures that mark bugs C2-2 and C2-3), so CI now runs every branch.

## What was reviewed

| File | What it does | Size |
|---|---|---|
| `src/tutor/triangle_reasoning.py` | Reads a learner's triangle-ratio step and returns a verdict and detail, such as `('definition_mismatch', 'denominator')`. Also reads short answers to the tutor's follow-up question | 921 lines (+902 in `cf14173`) |
| `src/socrates_beta/ratio_hint.py` | Turns that verdict into a fixed reply in the learner's language, and picks the next question | 248 lines, new |
| `src/socrates_beta/maths.py`, `api.py`, `static/app.js` | Wiring: the "Check my step" box, the hint endpoint and the signed follow-up | Read for the guarantees below; not changed |

## How it was checked

1. **Read** both files in full, and the wiring in `maths.py`, `api.py` and `app.js`.
2. **Mapped every verdict to its reply.** Every `(verdict, detail)` the code can return has a reply key, and all three languages have the same 66 keys.
3. **Hand-checked expected answers** against a worked triangle. Right angle at B; at C the opposite side is 144, the adjacent side 17 and the hypotenuse 145. The checks covered 83 first steps and 53 short follow-up answers, and every verdict is mathematically right.
4. **Stress test:** 25,032 random steps across 14 problem shapes and 73 follow-up questions, plus 1,000-character inputs. No exception was raised, and no call took over 50 ms.
5. **Measured what CI runs.** With Python's built-in line tracing on the CI test set (`-m "not local_corpus"`), before and after this PR:

   | File | Lines CI ran, before | After |
   |---|---|---|
   | `ratio_hint.py` | 0 of 23 (0%) | 23 of 23 (100%) |
   | `triangle_reasoning.py` | 363 of 536 (67%) | 508 of 536 (94%) |

   Most of the 28 lines still not run are docstrings or the older `check_labels` guards.
6. **Broke the code on purpose 8 ways**, and the new tests failed every time. The breaks were: no angle-C side swap, a missing Hindi reply, a number in a reply, a lost follow-up language, a retry that forgets its question, reversed order not singled out, an equivalent fraction marked wrong, and no 1,000-character limit.

## What is good

- **Replies are fixed sentences with no numbers**, so a reply cannot state a side length or the final ratio. A test now guards this.
- **No model, no randomness:** the same step always gets the same reply, at no cost.
- **The assessment boundaries hold** in `maths.py`:
  - a step uses no hint stage and saves nothing;
  - quizzes and diagnostics refuse it;
  - an urgent message is screened first;
  - an emotional-support message gets its caring reply and is not saved.
- **The follow-up is signed** with HMAC over the browser profile, the assessment and the question, so it cannot be moved to another learner or question.
- **The step box only appears** on supported triangle questions in practice (`supports_step_feedback`).
- **Inputs are bounded:** 512 characters at the API, and the step reader ignores anything over 1,000.

## Findings

| # | Kind | Finding | Evidence | Suggested next step | Owner |
|---|---|---|---|---|---|
| C2-1 | **Decision** | The step box confirms a correct substitution, so a learner can check a final answer as often as they like before submitting, and nothing is recorded | "sin c = opposite/hypotenuse = 144/145" → "Your side labels and their order fit the triangle…". "… = 17/145" → "Your side names fit. What length does the exercise give for the numerator side?" A bare "144/145" is not judged. | Decide whether this is teaching help or an answer oracle. If it is an oracle, keep the same neutral question for right and wrong numeric substitutions, or count step checks per question. It affects "Answers that matched" and any practice success rate | R1, with R5 |
| C2-2 | Bug (small) | A full on-top and below pair is read only when the learner also names the ratio, so the tutor asks the question the learner just answered | "I put opposite on top and hypotenuse on the bottom" → "Which side did you put on top, and which side underneath?" "For sin I put …" → "That side order fits." Cause: `triangle_reasoning.py:678` uses `_POSITIONAL_PAIRS` only `if names`, but one side in one position is read without a name | Read positional pairs without a ratio name, as for a single position. The strict-xfail test `test_positional_pair_without_a_ratio_name_is_understood` turns into a failure once fixed, as a reminder to remove its xfail mark | Lead (author), R3 review |
| C2-3 | Bug (small) | Roman Hinglish without the listed cue words gets an English reply | "opposite ko hypotenuse se divide kiya" → English. "maine opposite/hypotenuse likha" → Hinglish, because "maine" is a cue. Cause: `_HINGLISH_CUE` and `guess_language`'s two-word threshold | Add common short words ("ko", "se", "kiya", "hai"), tested against English false positives. Strict-xfail test `test_hinglish_step_without_cue_words_gets_a_hinglish_reply` | Lead (author); R1 for wording |
| C2-4 | Test gap, **fixed here** | CI never ran `ratio_hint.py` or the follow-up code: every beta step-feedback test is `local_corpus` | Coverage table above | This PR: `tests/test_r3_step_feedback.py` | R3 |
| C2-5 | Test gap | The assessment guarantees above are tested only by `local_corpus` tests in `tests_beta/test_beta.py`, so CI never checks them | `test_practice_step_feedback_*` are all marked `local_corpus` | A small synthetic item fixture for `AssessmentService`, so CI checks "no hint used, nothing saved, quiz refused" | R6 (E3) or R3 |
| C2-6 | Minor | Over the API, a step sent on a question that is not a triangle falls through to an ordinary hint and uses up a hint stage | `maths.py` `_hint`: if `ratio_hint` returns `None`, the normal hint path runs. The page only shows the box on triangle questions, so learners can't reach this | Return a "not available for this question" reply instead of using a hint | Lead |
| C2-7 | Minor | When a Hindi or Hinglish learner's follow-up isn't understood, the fallback reply is in English | Follow-up "hello there" after a Hindi turn → "What ratio did you write in your last step?" | Keep the previous language in the fallback path too | Lead |

## Not checked

- **Hindi and Hinglish wording quality.** The keys match, but whether each sentence reads naturally needs a fluent speaker (R1).
- **The beta-level tests,** which need the private book corpus. They were not run here.
- **Real learner phrasing.** All inputs here were written by the reviewer or generated at random.
- **The other parts of `cf14173`:** crisis-mention masking (F2), the safety-screen port (A1) and the retrieval cache (D2) belong to other tasks.

## Tests added in this PR

`tests/test_r3_step_feedback.py`: 174 tests in 0.2 s (172 pass, 2 strict xfail), with no corpus, model or network.
- Reply parity across the three languages.
- No numbers in any reply.
- 83 first-step branches and 53 follow-up branches.
- 15 next-question mappings.
- Language choice and how the next question is carried.
- The graph's names-only check, `check_ratio_definition`, which the R3 graph uses through math-tools.
- 3,000 seeded random steps, and long-input timing.
- Two strict-xfail tests for C2-2 and C2-3.
