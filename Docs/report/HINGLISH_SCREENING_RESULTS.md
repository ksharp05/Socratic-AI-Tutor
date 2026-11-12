# Synthetic Hinglish crisis-screening results

All four locked offline configurations scored the same 1,750 messages from the supplied pack. The acceptance set contains 200 proposed crisis messages and 1,100 proposed benign messages. The observed 1% gate allows at most 11 crisis alerts on the acceptance controls. Labels are provisional and the messages are synthetic native-style examples.

| Configuration | Acceptance crisis caught | Acceptance benign crisis alerts | 1% gate | Hard negatives alerted |
|---|---:|---:|---|---:|
| PR #28 deterministic baseline | 99/200 (49.5%) | 28/1,100 (2.55%) | Fail | 50/250 (20.0%) |
| Calibrated local cascade | 173/200 (86.5%) | 36/1,100 (3.27%) | Fail | 56/250 (22.4%) |
| Hinglish supplement | 174/200 (87.0%) | 36/1,100 (3.27%) | Fail | 56/250 (22.4%) |
| Additive check | 174/200 (87.0%) | 36/1,100 (3.27%) | Fail | 56/250 (22.4%) |

## Paired changes and errors

- The additive check caught 75 more crisis cases than PR #28 and retained all 99 baseline catches. It added eight acceptance false alerts and six hard-negative alerts. The calibrated cascade accounted for 74 of those crisis gains and all of those added false alerts.
- The additive check and Hinglish supplement each recovered one extra crisis message over the calibrated cascade. The additive check caught an urgent third-party case (NH26-01386), and the supplement caught a self-harm urge case (NH26-01352).
- Of the eight extra acceptance false alerts, six were ordinary tutoring requests, one was discussion of a poem, and one was exam-stress hyperbole. Seven of the eight were Devanagari-dominant. The seven had local-model margins below the calibrated cutoff and were newly flagged by the portable screen. Four of the six extra hard-negative alerts were cases of negation.
- Roman Hinglish accounted for 24 of the additive check's 26 crisis misses (116/140 caught). Mixed script was 45/47 and Devanagari-dominant was 13/13. The Devanagari-dominant control slice was small and had 9/28 false alerts.
- The 80 ambiguous cases have predictions for adjudication. PR #28 alerted on 0, the calibrated cascade 14, the supplement 18 and the additive check 22. These are unscored counts. The 120 pilot cases were used for scoring sanity only.

| Acceptance crisis subtype | PR #28 | Calibrated | Hinglish supplement | Additive |
|---|---:|---:|---:|---:|
| Direct help-seeking | 12/15 | 12/15 | 12/15 | 12/15 |
| Imminent | 14/40 | 35/40 | 35/40 | 35/40 |
| Indirect serious | 2/25 | 16/25 | 16/25 | 16/25 |
| Self-harm urge | 33/40 | 38/40 | 39/40 | 38/40 |
| Suicidal ideation | 28/60 | 55/60 | 55/60 | 55/60 |
| Urgent third-party | 10/20 | 17/20 | 17/20 | 18/20 |

The supplied pack is synthetic and labels await independent bilingual adjudication. These are offline component results. The acceptance denominator excludes hard negatives and ambiguous cases. The frozen release and runtime are outside the scope of this report update.

## Follow-up offline experiments

On the frozen 1,550-message synthetic holdout, the confidence-only route caught **188/200** crisis cases with **0/1,100** benign alerts and **0/250** hard-negative alerts. The holdout used 20 base crisis scenarios with repeated variants.

On a separate set of 136 individually written synthetic conversations, the latest message caught **8/16** indirect cases. Adding one usable earlier turn at the same cutoff caught **11/16**. A lower cutoff for turns with usable history caught **12/16**, with **0/104** benign alerts and **0/16** hard-negative alerts. Both history cutoffs reused the same score and had **78.98 ms** local p95. Latest-message p95 was **75.37 ms**. The labels await independent adjudication, and the confidence-based routes were evaluated offline.
