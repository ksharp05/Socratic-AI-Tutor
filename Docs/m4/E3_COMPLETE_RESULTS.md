# Complete M3/M4 development results - 5 November 2026

**The original development E1-E4 execution is complete, including all 48 E3 candidate sessions. Formal milestone acceptance remains pending human review, final preregistration and independent/team evidence.**

## Approved E3 completion

The last 12 sessions used 36 requests and USD 0.0132756, within the approved 50-request / USD 0.03 extension. Both source batches are retained: 36 original + 12 new = 48 unique student/seed pairs, exactly matching the C2 cohort (16 source cards, seeds 1/2/3). No duplicate, missing or extra pair was selected. The new run passed with zero failures/timeouts/model errors on clean local commit a463675. Runtime teaching behaviour, app configuration, data and unreviewed candidate playbook are unchanged; only the recorded harness/budget approval wiring differs from the v2 frozen revision. The later batch and approval deviation are disclosed rather than treated as one uninterrupted run.

## Conditions

| Condition | Sessions | Checked practice correct/submitted | Success proxy | Diagnosis recall | Mean simulated quiz change | Full/partial leak turns | Provider USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| C0 | 48 | 32/144 | 2/48 | 0.042 | 0.375 | 0/0 | $0.0545376 |
| C1 | 48 | 32/144 | 2/48 | 0.042 | 0.375 | 0/0 | $0.0542736 |
| C2 | 48 | 32/144 | 2/48 | 0.042 | 0.354 | 0/0 | $0.0542768 |
| Memory off | 16 | 12/48 | 1/16 | 0.042 | 0.375 | 0/0 | $0.0175956 |
| Telling | 16 | 24/48 | 0/16 | 0.042 | 0.375 | 38/4 | $0.0035124 |
| E3 full candidate | 48 | 32/144 | 2/48 | 0.042 | 0.375 | 0/0 | $0.0714812 |

E1/E3 use seeds 1/2/3; E4 uses seed 1 and its matched C2 subset. All arms share substantial heuristic code and code scoring. All primary outcomes, failures and contamination flags are retained. Repeats are not independent new learners.

## Paired primary estimates

Student-cluster bootstrap: 2,000 resamples, seed 0, matched student/seed pairs.

| Quiz-change difference | Matched sessions/cards | Estimate | Bootstrap 95% interval |
| --- | ---: | ---: | --- |
| C2_minus_C1 | 48/16 | -0.0208 | [-0.0625, 0.0000] |
| C2_minus_C0 | 48/16 | -0.0208 | [-0.0625, 0.0000] |
| E3_full_minus_C2 | 48/16 | 0.0208 | [0.0000, 0.0625] |
| memory_on_minus_off | 16/16 | -0.0625 | [-0.1875, 0.0000] |
| telling_minus_hints | 16/16 | 0.0625 | [0.0000, 0.1875] |

E3 has success-proxy difference 0.0000 and cleared-misconception difference 0.0000. The primary quiz numbers are synthetic and subject to the copying limitation below, not evidence of human learning.

## Measurement validity and sensitivity

Code-flagged post-answer matches occur in 86/224 sessions. Generic numeric instructions can trigger them, and the frozen harness then allows the simulator to copy those post answers. No post-question text exposure was detected. Numeric flags have no human semantic calibration. Keep the original quiz figures as recorded outcomes; they are not clean learning estimates.

The [complete offline sensitivity](POST_COPY_SENSITIVITY_E3_COMPLETE.md) replays the same recorded tutor/grade trajectories, first verifying the original simulator outcomes, then disabling all post-quiz copying. It is a post-hoc intervention that can remove genuine as well as false disclosure and changes later quiz random draws; it does not replace the primary design or establish a calibrated detector.

## Citations, safety and operations

Across all 224 tutoring sessions, 899/899 citation snapshots match their recorded hashes, chapter and registered source text. These are mechanical checks; semantic faithfulness remains unmeasured. Retrieval and golden-reference consistency are unchanged from the [original report](RESULTS.md).

E2 is unchanged: guards-on has 0/18 measured attack violations, guards-off 1/18; both have 0/35 measured false blocks. Each condition has 27/80 unknown outcomes. All-40 attack bounds are [0, 0.55] on and [0.025, 0.575] off; false-block bounds [0, 0.125] do not establish the 10% target. These are seen development attacks and selected input/output guards, with tool permissions/context screening still enforced.

| Condition | Tool calls/denied | Turn p50/p95 ms | Failures/timeouts/model errors |
| --- | ---: | ---: | ---: |
| C0 | 2615/0 | 986.0/1476.1 | 0/0/0 |
| C1 | 2628/0 | 996.7/1334.1 | 0/0/0 |
| C2 | 2627/0 | 992.9/1349.7 | 0/0/0 |
| Memory off | 472/0 | 149.6/1307.1 | 0/0/0 |
| Telling | 655/0 | 55.8/1166.8 | 0/0/0 |
| E3 full candidate | 2634/0 | 1001.2/1369.3 | 0/0/0 |

## Budget, provenance and remaining gates

Total provider attempts: **1036/1050 approved** (98 prior + 902 original continuation + 36 approved E3 completion). Known continuation cost is **USD 0.2791804**, excluding unmeasured prior-98 money. All new attempts expose provider cost; no voice/judge calls. 14 extension requests remain unused; this approval was solely for completing these E3 sessions, and no further calls are needed or scheduled. The original wallet remains byte-identical and the extension is linked by hash. Exact IDs, hashes, seed spread, cost coverage and intervals are in E3_COMPLETE_RESULTS.json.

The [original 1,000-request report](RESULTS.md), source tag beta-m4-request-cap-1000 and private archive preserve the prior boundary. Raw transcripts, cards, keys, wallets, approval receipt and per-session replay evidence remain ignored outside Git.

Data remains 16 development source cards, 22 quiz pairs/44 records and 17 seeded misconception types; 24 candidate-final cards/30 pairs remain unrun and lack independent final authorship. Eight seeded diagnosis types are outside the runtime catalogue, and five associations cannot show in assigned quiz scores. More simulated repeats do not resolve those limits.

Still pending: R2 final preregistration decision, actual teacher lesson acceptance/rejection, independent human raters and semantic citation/safety review, independent final content/new attacks, judge calibration or an explicit approved scoring limitation, a real failed-CI demonstration if retained as required, and independent clean-machine/team verification. Human approvals and formal M3/M4 acceptance are not inferred from these complete development runs. No push was made.
