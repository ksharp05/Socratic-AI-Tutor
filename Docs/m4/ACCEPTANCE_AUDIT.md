# M3/M4 acceptance audit - 5 November 2026

Sources: `Docs/plan/README.md` milestone table, `Docs/plan/08-schedule.md` M3 exit/Phase 3, `eval/PREREGISTRATION.md`, and `Docs/plan/05-evaluation.md`. This audit does not declare either formal milestone accepted.

| Required evidence | Current authoritative evidence | Decision / next action |
| --- | --- | --- |
| Agent behaviour frozen, except playbook | `beta-m3-behaviour-v2`, `12d541e`; original hashes in BEHAVIOUR_FREEZE.json and every manifest | Development engineering freeze verified; later harness/budget plumbing separately committed. Final human-approved freeze remains open. |
| Every experiment configuration runs on two development cards without errors | Six v2 smoke runs in RUN_RECEIPTS.json, all passing; 496 frozen-source regressions, 500 final checks | Verified for the implemented development configurations; final deployment/held-out configuration is outside this evidence. |
| Preregistration hashed | Development protocol hash fixed before matrix runs; final preregistration still explicitly draft | Not final approval. R2 must decide/approve the final protocol and final selection. |
| CI green | Baseline Actions 41908712265 success; local v2 CI-equivalent gates pass | Baseline/local evidence verified. No remote Beta CI because push was not authorized. |
| E1/E3 three repeats and spread | E1 48 sessions per arm, seeds 1/2/3; E3 36/48 after sessions, matched 36-session baseline, per-seed spread and cluster intervals | E1 development complete. E3 original design incomplete: 12 sessions, estimated 36 requests, fresh budget approval pending. |
| E2 and E4 | E2 80 cases per on/off condition, unknowns included; E4 16 per ablation with reused matched baseline | Development evidence recorded. No independent/new attacks or all-layer ablation, semantic attack labels unmeasured. |
| Quiz/learning measurement validity | 83/212 study sessions have code-flagged post-answer matches; generic numeric instructions can trigger flags; flags enter simulator told set | Material limitation, now explicit in results. Quiz changes can include copying even in hint arms. Do not claim learning improvement; retain original outcomes, validate a revised detector separately. |
| Every number traces to run_id in central experiment log | All 38 indexed M3 runs plus three CI-equivalent runs appended from actual manifests; RUN_RECEIPTS.json preserves hashes | Verified central-log coverage for these 41 runs, including v1 failures; no final freeze entry fabricated. |
| Failed CI run explained (`Docs/ci_failure.md`) | Read-only GitHub failure query returned no failed workflow runs on 5 November | Missing demonstration. A deliberate isolated failed remote run would require authorization to push/dispatch; none created or claimed. |
| Clean-machine install by a member who has not run stack | Earlier same-host clean-clone/Compose evidence exists; no independent-member/machine attestation | External gate pending, cannot infer from local checks. |
| Human-reviewed playbook, accepted/rejected lesson with reason | Four candidate lessons, blank human decision CSV, explicitly unreviewed playbook | Human gate pending; do not invent rejection/approval. |
| Two independent raters and calibrated judge | 63-item packet, zero human labels, no jointly rated items/kappa | Human labels and calibrated/approved scoring route pending; no extra judge allowance. |
| Enough independent final data | 16 development source cards / 22 pairs, 24 candidate-final cards / 30 pairs; runtime coverage gaps recorded | Enough for bounded engineering runs; independent authorship, new hidden attacks/controls and semantic citation review remain missing. |

The remaining E3 proposal is reviewable in `REMAINING_E3.md`; both request/cost caps require actual explicit approval. The separate Codex quota refresh does not grant tutor-provider requests. The original 1,000-request ledger remains unchanged and no extension wallet exists.
