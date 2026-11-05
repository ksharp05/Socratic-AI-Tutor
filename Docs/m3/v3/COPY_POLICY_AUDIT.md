# Context-bound copying repair: development validation

All 224 recorded simulator baselines reproduce with the legacy policy, and all dialogue trajectories remain identical under the candidate repair. This is cached-output analysis, not a fresh live tutor experiment. The frozen transition function is unchanged. No provider calls were made.

| Recorded condition | Sessions | Owned-format matches | Unattributed full matches | Context-linked full matches | Removed post copies | Retained copies | Original/candidate mean quiz change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| c0 | 48 | 34 | 4 | 0 | 19 | 0 | 0.375/0.104 |
| c1 | 48 | 34 | 4 | 0 | 19 | 0 | 0.375/0.104 |
| c2 | 48 | 34 | 3 | 0 | 18 | 0 | 0.354/0.104 |
| memory_off | 16 | 12 | 1 | 0 | 6 | 0 | 0.375/0.125 |
| direct_answers | 16 | 13 | 0 | 0 | 5 | 0 | 0.375/0.188 |
| e3_after_budget_tranche12 | 36 | 25 | 4 | 0 | 16 | 0 | 0.389/0.056 |
| e3_after_remaining4 | 12 | 9 | 0 | 0 | 3 | 0 | 0.333/0.250 |

The policy removes only the exact application-owned formatting suffix attached to a registered question. Copying requires an explicit post-question or identical registered-problem exposure plus a full answer match that survives student-echo exclusion. Numeric matches without question context remain unreviewed; they are not counted as semantic passes. Registered-practice telling is unaffected. Legacy contamination flags remain in session evidence and qualified-success checks stay conservative.

A separate non-overwriting review packet contains 30 unique recorded contexts plus 10 explicitly marked AI-authored calibration replies. All labels are blank; no reviewer is assigned. These controls are excluded from study metrics and do not establish independent final data or human calibration.

Positive/negative functional controls verify that actual context-linked disclosures can still enable copying, unrelated values cannot, student echoes do not become new copying evidence, private quiz references do not enter application inputs, and concurrent scopes remain isolated. The candidate is opt-in and needs human/protocol review before final qualification. It does not remove the simulator/kernel assumptions or establish human learning.
