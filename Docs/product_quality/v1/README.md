# Product-quality candidate - 6 November 2026

The learner interface now exposes all three chapters, pins the chapter per conversation, keeps references with each reply, and restores saved replies after lost acknowledgements without automatic replay. The final connected-app/UI suite passes 548 tests, including five new learner UI regressions; the earlier four-suite runtime check passed 647. Assistant-operated browser checks at 1280/390 pixels used isolated stub data, showed no horizontal overflow, and added no provider calls. Temporary servers were stopped.

Fresh current-candidate C1/C2 stub qualification has 96 sessions plus six matching smokes. Both arms have development recall 0.208, precision 0.625, success proxy 4/48 and synthetic mean gain 0.167; all 240 citation snapshots match mechanically. The older stub recall was 0.083. These are descriptive development results from only 16 shared cards with three seed repeats; they do not establish independent generalization, a C2 advantage or human learning. See CURRENT_CHECKPOINT.json.

The local Beta candidate adds chapter-scoped AP/trigonometry diagnosis from the public catalogue, exact AP error hypotheses, conservative handling of ambiguous answers, and acknowledgement when a learner states the correct distinction. Generic coefficient/square-root questions no longer automatically diagnose an error. Text evidence stays suspected; the model cannot change the observed cause or invent its evidence quote. Non-quadratic follow-up uses the relevant catalogue instead of a quadratic factor story.

**647 regressions passed**, including 93 new public-source cases. All three exact local CI gates and all eight offline/live journeys passed. The live batch used **9 requests / USD 0.0023244**, with all costs exposed and no errors/refusals. Four buffered practice replies were accepted without fallback. All 9 citation snapshots match mechanically; semantic faithfulness is unreviewed. Twelve replies were output-guarded; two approved-question displays follow the existing skip policy.

The user authorized a USD 10 ceiling for this phase. Only USD 0.10 was allocated; USD 9.90 remains unallocated. All eight cases are complete. Total recorded provider usage is 1,061 requests and known continuation cost USD 0.2862964, excluding the original 98 requests whose money is unknown. Original, E3 and v3-pilot wallets are unchanged. Beta remains local as explicitly requested.

## What the recorded journeys show

- AP: a claim that progressions must increase triggers a relevant probe; a stated correction moves on without awarding mastery.
- Trigonometry: confusing cosine with the reciprocal of sine triggers a conceptual probe; identifying cosecant moves on without a false mastery claim.
- Ordinary chapter questions do not acquire an error label.
- Checked AP off-by-one and triangle-reference errors get targeted questions/hints with actual model calls.
- A request for another learner's grades is declined without a model call.

Catalogue availability rises from 9 to 26 provisional types, preserving source review metadata. All 20 public AP/trig wrong-work examples and separate correct-statement/paraphrase controls are tested. This is coverage of public examples, not diagnosis accuracy. There are 665 public practice items; AP term/sum and the existing triangle-ratio families remain the connected non-quadratic practice pool. Other exact AP adapters are unit-tested and await separate integration/review.

## Limits and next work

This is an AI-authored candidate; actual R3/R2 review remains pending. The eight journeys are public development fixtures with synthetic authorization confined to isolated test databases. No real teacher approval, human labels, independently authored final data or new E1-E4 effectiveness result is claimed. The v2 paid studies and v3 pilot remain attached to their original source/tag snapshots.

Two deterministic acknowledgement turns still carry the tutor route without model calls. Full specialist/per-route acceptance remains open; later routing cleanup can classify these as information actions. Broader paraphrases, UI acceptance, human teaching/citation review, independent installation/security evidence and final preregistration still need work before M3/M4 acceptance.

Runtime changes are at `8716bcf`; exact local CI and live evidence use clean `e6796bf`. All 87 captured source/config/data files are preserved privately with exact hashes. `RESULTS.json` has the receipts and limits; `scripts/product_quality/report_results.py` verifies saved evidence offline. Never rerun completed live jobs merely to regenerate reporting.
