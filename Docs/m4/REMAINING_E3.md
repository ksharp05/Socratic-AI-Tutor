# Remaining original E3 sessions - approval pending

The original 48-session development E3 candidate design has 36 completed sessions. This is the concrete proposed completion of its remaining 12 sessions; it is not a new final/held-out experiment.

| Source card | Chapter | Seeds | Sessions |
| --- | --- | --- | ---: |
| sim_v2_002 | Arithmetic progressions | 1, 2, 3 | 3 |
| sim_v2_006 | Trigonometry | 1, 2, 3 | 3 |
| sim_v2_007 | Quadratic equations | 1, 2, 3 | 3 |
| sim_v2_013 | Quadratic equations | 1, 2, 3 | 3 |

**Measurement limitation:** the existing frozen harness can trigger post-quiz copying from generic numeric overlaps (83/212 recorded study sessions flagged). Completing these 12 sessions fills the original recorded development design; it does not repair or validate a learning measure. See `ACCEPTANCE_AUDIT.md` and `RESULTS.md`.

Same model (`openai/gpt-4.1-mini`), template voice, code scoring, eight-turn limit, development data and unreviewed candidate playbook. The existing matched C2 sessions predict 36 requests. Proposed extension: **up to 50 requests, hard additional accounting cap USD 0.03**, retries disabled, maximum 240 output tokens. No judge, voice, new model, purchase, push or final-study allowance is included.

Why approval is needed: `Docs/m2/NEXT_SESSION_HANDOFF.md` records the user's explicit at-most-1,000-call allowance. It is exactly exhausted. User intent to continue overnight or resume after the Codex account refresh does not change that separate tutor-provider limit. The intact original ledger hash is `2b0e529b378dfc7c68be4375a89a859b9c3c173dbc23f543a602c2c0cdd8b9de`.

Reviewable config: `eval/configs/m3_live_e3_remaining4.toml`. Private receipt: `Directions/m3_runs/v2/live/E3_EXTENSION_APPROVAL.json`, currently **pending**, approver/quote blank. The proposed extension wallet is `Directions/m3_runs/provider_budget_extension_e3.json`; it does not exist. Pending approval is tested to fail before this wallet is created.

After an explicit answer approving both caps:

1. Preserve the original ledger and original `Docs/m4/` report. Record the real approval quote, identity and time in the private receipt; do not infer approval from a selected UI default.
2. Verify only the four listed cards / twelve student-seed pairs remain. Inspect the original live INDEX, completed tranche and any interrupted remaining-run artifacts; refuse duplicates. Use the existing global `matrix.lock` for execution.
3. Verify teaching behaviour/prompts/data/playbook against `beta-m3-behaviour-v2`. The only allowed intervening runtime changes are the reviewed harness budget-receipt wiring and provider-budget extension gate. Record their separate commit and the deviation; do not claim byte-identical harness source.
4. Invoke `tutor_eval.harness.run` with the proposed config and an explicit isolated out directory under `Directions/m3_runs/v2/live/e3_after_remaining4/`. Do not invoke the old full E3 configuration. Keep partial sessions and failures; do not automatically retry them.
5. Add completed evidence to INDEX with its actual manifest and config hashes. Create a versioned aggregate of the original 36 plus these 12, asserting 48 unique student-seed pairs matched to C2, and recalculate paired student-cluster intervals. Preserve separate tranche and aggregate summaries; report both provider ledgers and exact incremental/all-known money.
6. Update the report and checkpoint. The existing delivery script deliberately asserts the original 1,000-request report boundary; extend it explicitly for the new evidence rather than weakening provenance assertions. Human lesson acceptance, independent final authorship and preregistration remain pending even if all 48 development sessions finish.

Until approval, do not execute steps 1-6 or send any further provider request. The proposal is ready for a decision.
