# Audit and coverage findings

Original snapshot `2fb0ffbb67ae8e5c69dda7ad8da3d4899a5afbbfdf9705b3b10efa67556a9b8c`. The supplied validator passed 17 checks on a copied input; see `evidence/supplied_validator.log`. This does not certify pedagogy or safe deployment.

## Verified inventory and dependence

| View | Rows | Unique exact texts | Number-normalized patterns |
|---|---:|---:|---:|
| Problem statements | 232 | 192 | 32 |
| Tutor turns | 5,568 | 93 | 93 |
| Student dialogue turns | 5,568 | 322 | 119 |
| Contextual messages | 2,400 | 2400 | 2400 |
| Security attack texts | 360 | 10 | 10 |
| Security control texts | 360 | 10 | 10 |

Number normalization is a mechanical heuristic, not a count of independent concepts. There are 192 exact problem wordings, not 232 distinct wordings; different IDs sometimes repeat the same problem. Unique learner strings do not establish authentic human variety. Parent seed records and 5,568 extracted tutor contexts must not be counted as independent additions.

Chapter dialogues: Quadratics 320, AP 320, Trigonometry 288. All four paths have 232 dialogues. The active seed set has 29 IDs, eight variant IDs each; T08 accounts for the missing seed ID but does not explain semantic differences from the canonical project taxonomy.

## New defects missed by the supplied validator

1. **2,040 contextual messages have wrong variant families** relative to their active problem. All affected records preserve the correct problem text, misconception and chapter, so a field-only correction is possible. `evidence/family_join_issues.json` records the original defect. `evidence/metadata_repair.json` binds the versioned correction; it changes no labels, text, IDs or approval state.
2. **All 20 intent catalogue counts are stale:** source counts 10, actual counts 120. The corrected catalogue is additive, not a rewrite of the source evidence.
3. **The source answer-match test skips 336 dialogues with short reference strings.** Zero long-string matches do not establish zero leakage. Equivalent values, partial roots, intermediate steps and answers in general formulas require code-plus-human review.
4. **32 tutor-turn shape flags** were found; see `evidence/dialogue_outliers.json`. These are triage findings, not teacher judgments. A fluent question can still be unhelpful.

## Mathematical checks and limitations

All 232 references pass an independent derivation from displayed public givens using exact symbolic solving, polynomial comparison, recurrence or exact trigonometry. Tests also reject 120 altered scalar references. Both routes share SymPy and the project's bounded parser; this is not independently authored software or a formal proof. Generic English explanations and the truth of synthetic learner beliefs are not established by these checks.

The source script's recomputation often checks already-derived metadata. The new verifier does not rely on that metadata to derive roots, AP values or triangle ratios. It rejects or marks unsupported forms unverified rather than guessing.

## Containment and review state

All 87 retrieval candidates remain unlabelled. All 90 glossary records are unreviewed. All 32 complementary-angle dialogues remain quarantined. There are zero teacher approvals, independent final cases and runtime example promotions. Original files and the frozen v0.10.0 benchmark were not edited.

`coverage_metrics.json` records counts, teaching moves, student states, message styles and dependence. Metrics and six selected review/projection outputs reproduced exactly, excluding measured audit duration. See `evidence/reproducibility.json`.
