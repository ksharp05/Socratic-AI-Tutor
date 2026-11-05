# Version 3 live C1/C2 pilot - 6 November 2026

All six planned sessions completed on clean local `a9ee2ba`. The narrow model-path gates pass: all 10 tutor-route turns made model calls, all 48 turn traces were observed, and execution/provider errors and detected full-answer leaks were zero.

The pilot used **16/80 requests** and **USD 0.0047916/0.05**, all provider-reported. The original and E3 ledgers are unchanged. Overall usage is 1052 requests; known continuation money is USD 0.2839720, excluding the original 98 requests whose money is unknown. All six sessions are complete; unused allowance is not a reason to repeat or expand the pilot.

## Path acceptance and quality are separate

| Condition | Sessions | Calls | Tutor turns with model calls | Detected full leaks | Diagnosis hits | Success proxy | Mean synthetic quiz change | Provider USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| c1 | 3 | 8 | 5/5 | 0 | 0 | 0 | -0.667 | 0.0024104 |
| c2 | 3 | 8 | 5/5 | 0 | 0 | 0 | -0.667 | 0.0023812 |

Both conditions named no seeded diagnoses, had zero qualified success proxies, and had the same negative synthetic quiz change (-2/3 points). There is no observed C2 quiz advantage in these three matched pairs. These are simulator outcomes from existing development cards, not human learning estimates or evidence of final efficacy.

The 48 turns covered tutor, set_question, grade and check_reasoning; the explicit diagnose route was not exercised. This confirms the paid tutor paths without accepting diagnostician/question-setter specialist architecture. Missing runtime catalogue IDs still impose the previously measured 50% optimistic development coverage ceiling. R3/R2 should review both public catalogue coverage and diagnosis elicitation before larger live batches, without tuning rules to private card states or simulator behaviour.

All 14 citation snapshots pass mechanical hash/chapter/source-text checks; semantic relevance and faithfulness are unreviewed. Across both arms, ten legacy numeric-match flags remain conservatively recorded. The new context-bound rule removed four ineligible post-copy triggers, retained none, and left two unattributed match witnesses unreviewed. Zero detected full leaks does not establish zero semantic disclosure.

## Scope and reproducibility

Fixed openai/gpt-4.1-mini through OpenRouter; template student voice, no judge, three existing chapter cards, seed 1 and eight turns per session. No held-out data, C0 comparator, fresh security experiment, human labels or final milestone approval were added. Source/configuration hashes were checked against the recorded clean commit, with all 100 pre-pilot source/configuration files verified. Exact run IDs, artifact hashes, cost accounting and limits are in PILOT_RESULTS.json; raw trajectories and wallet remain private under Directions/m3_runs/v3.

The user explicitly chose **Keep Beta local**. No push or PR was made. Next: R3/R2 diagnosis and protocol decisions, teacher/independent-rater reviews, independently authored final content, and an approved final freeze/evaluation. The existing 63-item and new 40-item human packets remain blank; full M3/M4 acceptance remains open.
