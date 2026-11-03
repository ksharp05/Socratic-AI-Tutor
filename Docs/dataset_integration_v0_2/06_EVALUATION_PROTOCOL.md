# Independent evaluation protocol awaiting owner approval

This is a proposed protocol, not a completed independent test. The executing agent has seen the supplied development package and implemented the preview; it cannot independently author the final unseen evaluation.

## Freeze and access

R5 commissions 30 new dialogues and 120 new contextual messages from authors who do not tune the tutor. Keep problem/scenario roots, variant/paraphrase families, labels and keys outside prompts, retrieval and shared tuner folders. Freeze content/configuration hashes, access roles, metrics, budgets, stop rules and planned repeats before final runs. Keep v0.10.0 immutable. All v0.2 records remain development-only even after metadata repair or human review.

Public MathDial/MRBench/benchmark origins can overlap; check source IDs and near duplicates before reusing any external context. A new wording or private folder does not undo exposure. If strict author separation cannot be achieved, disclose that limit rather than claim independent evaluation. Only hashes, aggregate counts and run IDs belong in shared experiment logs.

## Metrics and proposed local gates

- Contextual intent macro F1 at least 0.85; ambiguity clarification at least 90 percent. R1/R5 ratify these project gates. Report per-intent and small-subset denominators, abstentions, errors and uncertainty.
- Exact supported mathematics and sign/fraction fidelity; invalid/unverified submissions are distinct from incorrect answers. Preserve failed and timed-out runs; withhold incomplete final accuracy.
- Full and partial practice leaks separately. Count quiz hints, answer-key disclosure, role spoofing and source/data-path injection. Zero known quiz leaks in the executed suite is a gate on that suite, not a universal safety claim.
- Human-reviewed Recall at 5 separately for cards and sections; 87 null labels are not gold. Assess whether cited text supports the claim, not just whether the ID exists.
- Actual model calls, prompt/content/configuration hashes, template fallback rate, tool failures, latency distribution and observed usage. Unknown cost stays null, not free.
- Unassisted pre/post or transfer performance, diagnosis precision/recall and student progression alongside leakage. Synthetic learner results are not evidence of real-child effectiveness.

## Existing experiment framework

| Experiment | Comparison | Controls and interpretation |
|---|---|---|
| E1 | Fixed workflow C0, single-agent C1, coordinated C2 | Same agreed model/tools/context/budget; do not confound a template-only route with a model-driven route |
| E2 | Defences off/on, with the agreed per-layer breakdown | Independent attacks and matched legitimate controls; current repeated v0.2 strings are development material |
| E3 | Before/after development-only Reflexion | Human-reviewed accepted/rejected lessons; freeze playbook before final runs |
| E4 | Learner memory off/on; direct answers versus Socratic hints | Keep direct-answer/leak-disabled conditions in isolated experiments, never the learner-facing app |

Run the required three final comparisons/repeats as specified by the accepted project pre-registration. Do not add, drop or change seeds after viewing results. The milestone proposal cuts optional extra E2/E4 repeats; the owner must confirm the final matrix. Failed/time-out cases remain scheduled. Report response-quality, numerical and complete task-success metrics separately.

## Human calibration

Have the teacher assess 20 complete executed transcripts. Two named raters independently label at least 30 contextual turns, including mistake location, actionable guidance, full/partial leaks, tone and context fidelity. Preserve each rater's original labels and adjudication. Calibration uses development transcripts; it is not a reusable final test.

Report human agreement, different-family judge agreement and uncertainty. The proposed kappa gate is at least 0.6, compared with human agreement, subject to ratification. Small samples and skewed labels can make kappa unstable; present confusion matrices and class prevalence. Missing labels are never filled by AI. No human labels, kappa, independent final cases or learning effect were produced in this run.
