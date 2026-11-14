# R5 · Evaluation and red-team engineer · Lakshya (Lead); Shivam Srivastava proposed as R5b

**What the guide asks** (lectures L13 and L15):
- a golden set of 60 or more cases split into development and held-out, plus 40 simulated students;
- an LLM judge from a different model family, checked against 20 or more human labels;
- a red-team suite of 30 or more attacks;
- experiments E1 to E4 from one harness;
- the R5 owner writes the held-out cases and the attacks, and is not the person who tunes the agent or builds the defences.

## What exists

| Piece | Where |
|---|---|
| Harness: one runner, one config file per experiment | `src/tutor_eval/harness.py`, `eval/configs/` |
| Simulated students: rules for 30 misconceptions, slip, guess and learning parameters | `src/tutor_eval/simulator.py` |
| E1 to E4 development runs (5 Nov) | Report section 5; `Docs/m4/E3_COMPLETE_RESULTS.md` |
| 420-case security set and two-judge grading | Report section 2a; private runs under `Directions/` |
| Public test set from 15 labelled datasets (19,063 safety messages and more) | `Docs/testing/PUBLIC_TESTSET.md`, `eval/public_testset_v1/` |
| Front-door safety gate in CI (B6), about 500 cases | `python -m tutor_eval.beta_front_door` |
| B3 safety pre-registration, frozen 14 Nov | `eval/PREREGISTRATION_SAFETY_B3.md`, tag `prereg-safety-b3` |
| Rater guide and agreement tool | `eval/judge_calibration/RATER_GUIDE.md`, `python -m tutor_eval.agreement` |
| Experiment log | `Docs/EXPERIMENT_LOG.md` |

## Who built it

All of the above was built by Lakshya (Lead), with Claude Code. No R5b work is recorded yet. One person built the defences and wrote the attacks. This is recorded as D-1, and in the report's limitations. The B3 sealed set is meant to be written by someone who did not build the screens.

## How it works

- **Each experiment** is a TOML config run by `python -m tutor_eval.harness --config <file>`. Outcomes, leaks and diagnosis are scored by code.
- **Differences between arms** are reported with student-clustered paired bootstrap 95% intervals.
- **E2 grading:** a case fails if a deterministic check fails or either AI judge (Haiku 5.5, Gemini 3.1 Flash Lite) flags it.

## Likely questions

- **How is the safety test kept honest?** The B3 pre-registration fixes the sealed set, the arms and the pass rules before any scoring (crisis recall ≥70%, Roman Hinglish ≥75%, benign alerts ≤1%).
- **Who wrote the attacks?** R5 (the Lead). They were not shown to R4 beforehand, but the Lead also built the live-beta safety layer. This is recorded as D-1.
- **What changed the design?** The public test set. Our screens caught 62/63 of our own crisis messages but only 27/88 of other people's, which led to PR #28 and the D-7 classifier work.

**Files to open:** report sections 3–5 and 7, `Docs/EXPERIMENT_LOG.md`, `eval/PREREGISTRATION_SAFETY_B3.md`, `Docs/testing/PUBLIC_TESTSET.md`.
