Current local product/UI and fresh stub C1/C2 qualification: see `Docs/product_quality/v1/README.md` and `CURRENT_CHECKPOINT.json`. They do not replace the historical paid study or close human/final gates.

# M3/M4 acceptance audit - 5 November 2026

Current candidate work and remaining role decisions are now tracked in [the v3 checkpoint](https://github.com/ksharp05/Socratic-AI-Tutor/blob/docs-archive-2026-11-14/Docs/m3/v3/STATUS.md) and [team actions](../m3/v3/TEAM_ACTIONS.md). This file preserves the earlier v2 audit.

Sources: `Docs/plan/README.md` milestone table, `Docs/plan/08-schedule.md` M3 exit/Phase 3, `eval/PREREGISTRATION.md`, and `Docs/plan/05-evaluation.md`. This audit does not declare either formal milestone accepted.

| Required evidence | Current authoritative evidence | Decision / next action |
| --- | --- | --- |
| Agent behaviour frozen, except playbook | `beta-m3-behaviour-v2`, `12d541e`; original hashes in BEHAVIOUR_FREEZE.json and every manifest | Development engineering freeze verified; later harness/budget plumbing separately committed. Final human-approved freeze remains open. |
| Every experiment configuration runs on two development cards without errors | Six v2 smoke runs in RUN_RECEIPTS.json, all passing; 496 frozen-source regressions, 500 final checks | Verified for the implemented development configurations; final deployment/held-out configuration is outside this evidence. |
| Preregistration hashed | Development protocol hash fixed before matrix runs; final preregistration still explicitly draft | Not final approval. R2 must decide/approve the final protocol and final selection. |
| CI green | Baseline Actions 41908712265 success; local v2 CI-equivalent gates pass | Baseline/local evidence verified. No remote Beta CI because push was not authorized. |
| E1/E3 three repeats and spread | E1 48 sessions per arm, seeds 1/2/3; E3 48/48 after sessions, matched 48-session baseline, per-seed spread and cluster intervals | E1 and original E3 development design complete. Explicitly approved remaining 12 used 36 requests / USD 0.0132756; exact pair matching and 224-session sensitivity verified. |
| E2 and E4 | E2 80 cases per on/off condition, unknowns included; E4 16 per ablation with reused matched baseline | Development evidence recorded. No independent/new attacks or all-layer ablation, semantic attack labels unmeasured. |
| Quiz/learning measurement validity | 83/212 study sessions have code-flagged post-answer matches; generic numeric instructions can trigger flags; flags enter simulator told set | Material limitation, now explicit in results. Quiz changes can include copying even in hint arms. Do not claim learning improvement; retain original outcomes, validate a revised detector separately. |
| Every number traces to run_id in central experiment log | All 38 indexed M3 runs plus three CI-equivalent runs appended from actual manifests; RUN_RECEIPTS.json preserves hashes | Verified central-log coverage for these 41 runs, including v1 failures; no final freeze entry fabricated. |
| Failed CI run explained (`Docs/ci_failure.md`) | Read-only GitHub failure query returned no failed workflow runs on 5 November | Missing demonstration. A deliberate isolated failed remote run would require authorization to push/dispatch; none created or claimed. |
| Clean-machine install by a member who has not run stack | Earlier same-host clean-clone/Compose evidence exists; no independent-member/machine attestation | External gate pending, cannot infer from local checks. |
| Human-reviewed playbook, accepted/rejected lesson with reason | Four candidate lessons, blank human decision CSV, explicitly unreviewed playbook | Human gate pending; do not invent rejection/approval. |
| Two independent raters and calibrated judge | 63-item packet, zero human labels, no jointly rated items/kappa | Human labels and calibrated/approved scoring route pending; no extra judge allowance. |
| Enough independent final data | 16 development source cards / 22 pairs, 24 candidate-final cards / 30 pairs; runtime coverage gaps recorded | Enough for bounded engineering runs; independent authorship, new hidden attacks/controls and semantic citation review remain missing. |

The E3 extension was explicitly approved and completed within both caps; see `E3_COMPLETE_RESULTS.md` and `REMAINING_E3.md`. The original 1,000-request ledger remains unchanged, with a separate 36-attempt extension ledger. No E3 development sessions remain; final human/team gates above remain open.

## Offline scoring sensitivity follow-up

Offline fixed-trajectory sensitivity is complete: all 212 original simulator trajectories/outcomes reproduce using saved tutor replies and grades; corrupt-input negative control is rejected. With post-quiz copying disabled, C0/C1/C2 each have mean gain 0.104; matched C2-vs-candidate, C2-vs-C0/C1 and memory on/off quiz differences are zero. This is post-hoc sensitivity, not a new tutor run, calibrated disclosure detector or learning evidence. See `Docs/m4/POST_COPY_SENSITIVITY.md` and `REPLAY_VALIDATION.json`. No provider requests were sent; original outcomes and ledger are intact.

## Approved E3 completion follow-up

The complete development cohort now has 224 unique tutoring sessions and 899 valid mechanical citation snapshots. The complete offline replay matches all 224 original simulator outcomes. All primary E3 pairs are matched (48 sessions /16 source cards); E3-minus-C2 success and cleared-misconception differences remain zero, and its small primary quiz difference disappears without post copying. The original 212-session observations above are preserved as history.
