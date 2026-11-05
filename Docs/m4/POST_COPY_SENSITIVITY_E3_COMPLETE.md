# Post-quiz copying sensitivity - exploratory offline replay

The simulator replay matched all 224 recorded student-message sequences, diagnoses/clearing, practice summaries and pre/post quiz answers while consuming the recorded tutor replies and grades. It uses the frozen run_session transition function. This does not verify that a live tutor would regenerate those replies. Timing/tool traces are excluded, and no tutor or model is invoked.

A second replay holds every recorded tutoring message and grade fixed, but clears the post-quiz told set immediately before the post quiz. No post-quiz ID is a pre-quiz or registered-practice ID, so this intervention leaves the tutoring trajectory unchanged. The simulator uses its ordinary mastery/misconception/guessing rules for the post quiz instead of copying.

| Condition | Sessions | Original mean quiz change | Without post copying | Changed session scores | Original copied post items |
| --- | ---: | ---: | ---: | ---: | ---: |
| c0 | 48 | 0.375 | 0.104 | 13 | 19 |
| c1 | 48 | 0.375 | 0.104 | 13 | 19 |
| c2 | 48 | 0.354 | 0.104 | 12 | 18 |
| memory_off | 16 | 0.375 | 0.125 | 4 | 6 |
| direct_answers | 16 | 0.375 | 0.188 | 3 | 5 |
| e3_after_full | 48 | 0.375 | 0.104 | 13 | 19 |

Paired differences below use the same student-cluster bootstrap as the original analysis: 2,000 resamples, seed 0, matched student/seed pairs. They quantify this post-hoc sensitivity only.

| Without-post-copy contrast | Matched sessions / cards | Difference | Bootstrap 95% interval |
| --- | ---: | ---: | --- |
| C2_minus_C1 | 48/16 | 0.0000 | [0.0000, 0.0000] |
| C2_minus_C0 | 48/16 | 0.0000 | [0.0000, 0.0000] |
| E3_tranche_minus_matched_C2 | 36/12 | 0.0000 | [0.0000, 0.0000] |
| memory_on_minus_off | 16/16 | 0.0000 | [0.0000, 0.0000] |
| telling_minus_hints | 16/16 | 0.0625 | [0.0000, 0.1875] |
| E3_full_minus_C2 | 48/16 | 0.0000 | [0.0000, 0.0000] |

This is a post-hoc sensitivity, not a preregistered comparison, a rerun of the tutor, a human learning estimate or a replacement for the original primary results. Disabling all post copying can remove genuine as well as false disclosure; it is not a calibrated detector. Skipped copying branches normally skip random draws, so later quiz-item draws can also change. Shared simulator/kernel assumptions remain. Validate a revised contextual disclosure rule separately before a fresh qualified study.

Original transcripts, manifests, labels, study results and provider ledger are unchanged. Exact input hashes and aggregate results are in the matching JSON file; per-session audit records remain private.
