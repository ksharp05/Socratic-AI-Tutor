# M3/M4 checkpoint - v2 safety exception

The active user goal is to complete actionable M3 behaviour freeze and M4 E1–E4 results, data sufficiency, citation/safety/cost analysis, while the user sleeps. Keep work local on Beta. A one-time continuation is scheduled in this chat for 6:32 am IST on 5 November after the reported 6:31 am account reset. Do not spend the reset credit or change plans.

## Current state

- V1 implementation `b4c290b`, local tag `beta-m3-behaviour-v1`, is preserved. It passed 483 regression tests + 3 analysis tests, all six final two-card smoke configs and three CI evaluation gates. Baseline remote Actions is confirmed successful for 3dd518a (41908712265); unpushed Beta has no remote CI run.
- V1 full offline matrix completed: 224 tutoring sessions, 160 safety cases, zero execution errors. Evidence is `Directions/m3_runs/offline/INDEX.json`, `ANALYSIS.json` and `ANALYSIS.md`; the blank-rater packet is beside them. One known development urgent case failed routing with guards on and off. No provider calls occurred.
- V2 adds explicit first-person unsafe/not-safe recogniser phrases and regression checks. It also delivers the six existing source/tool-result cases through isolated returned-data overlays. Files/keys are untouched, delivery hashes are recorded, and semantic expectations stay unmeasured where code cannot establish them. The protocol documents both deviations; original v1 outcomes are not relabelled.
- Use **`--revision v2` for all new smoke/offline/pilot/live and analysis commands**. V2 artifacts go under `Directions/m3_runs/v2/`; v1 stays where it is. No data, attack payload, seed, expected label or run count changed.

## Execution next

Run final full tests and committed v2 smoke/CI checks, then tag the committed source as `beta-m3-behaviour-v2`. Run:

```
python scripts/m3/run_matrix.py --stage offline --revision v2 --security
python scripts/m3/analyse.py --stage offline --revision v2
python scripts/m3/run_matrix.py --stage pilot --revision v2 --arms c1 c2 --max-calls 902
python scripts/m3/analyse.py --stage pilot --revision v2
```

Inspect the pilot before the full live matrix. The pilot is four sessions, at most 30 provider attempts total, estimated below USD 0.05; it shares the global ledger. If healthy, announce the next batch cap and cost estimate, then run `--stage live --revision v2 --max-calls 902 --security` and analyse it. All 16 predeclared development cards are retained; E1 and E3 use seeds 1,2,3, E4 uses seed 1 with the matched C2 subset reused. Failures/timeouts/contamination cannot become successes. Source/config/data-aware resumption refuses ambiguous/interrupted evidence. Inspect partial sessions, never silently repeat or drop them.

## Budget and data

Provider calls remain **98/1,000** (zero new as of this checkpoint). Shared durable wallet: `Directions/m3_runs/provider_budget.json`, max 902 further attempts and USD 1 accounting cap. Never reset, delete or bypass it. Retries disabled; max 240 output tokens; fixed openai/gpt-4.1-mini; template simulator; no judge calls. Provider cost is used if exposed, otherwise labelled token estimates/conservative reservations.

Existing development export: `Directions/m3_data/development-v1/`; 16 source cards (6 QE,5 AP,5 trig), 22 pairs/44 quiz items, 17 seeded misconception types, 160 development golden cases. No practice-record overlap. Simulator validation passes 24/24 card/misconception pairs; five are not observable in assigned quiz scores, eight seeded types are outside runtime diagnosis. Candidate final: 24 cards/30 pairs, not exported/run. More synthetic variants do not supply independent or human-reviewed data.

## Remaining reporting and gates

Finish actual live/code results with exact run IDs, paired student-cluster bootstrap intervals, seed spread, mechanical citation checks, supported/unsupported safety bounds and cost coverage. Prepare the final report and blank human-review packet; preserve any existing rater files rather than overwriting them on analysis reruns. The original final preregistration stays draft: do not invent R2 approval, accepted/rejected human lessons, calibrated raters/judge, independent final authorship or real learning. Candidate-v1 playbook is explicitly unreviewed and exploratory. M3/M4 final acceptance still depends on those external gates, even after the development engineering work is complete.
