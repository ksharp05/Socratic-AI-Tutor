# Current C1/C2 regression baseline

Source 3e27ab4: 96 offline sessions plus six matching smokes, using the same 16 synthetic development cards and seeds 1/2/3 per arm. These repeats qualify reproducibility after source changes; they are not new independent learner observations. All four jobs pass their execution gates, with zero provider calls.

| Arm | Sessions | Diagnosis recall | Precision | Success proxy | Mean synthetic quiz gain |
| --- | --- | --- | --- | --- | --- |
| c1 | 48 | 0.083 | 0.4 | 4/48 | 0.083 |
| c2 | 48 | 0.083 | 0.4 | 4/48 | 0.083 |

All 48/48 paired C1/C2 trajectories are identical; no architecture advantage is observed. All six smoke trajectories match their full runs. 268 reference snapshots pass identity/hash/chapter checks; semantic source faithfulness remains unreviewed. Each arm has 18 unchecked practice attempts and zero grading disagreements, errors, timeouts or measured full leaks.

The earlier v2 baseline had recall 0.208, precision 0.625 and mean synthetic gain 0.167; the current values are worse. This is a measured regression on the fixed simulator, with no isolated cause or human-learning interpretation. R3/R2 must triage runtime/content and simulator-support changes before a new live efficacy comparison. Do not relabel this as an improvement or inherit old results onto new code.

The preparation note mistakenly described 24 cards/two seeds. The frozen executable configs and manifests actually use 16 cards/three seeds. The original note is retained and the correction is explicit; no run was repeated to fix prose.

Reproduce the aggregate audit offline: scripts/product_quality/report_v3_baseline.py --check. All raw trajectories and manifests remain private under Directions/product_quality/v3/c1_c2_baseline. Human/independent-final reviews remain open.
