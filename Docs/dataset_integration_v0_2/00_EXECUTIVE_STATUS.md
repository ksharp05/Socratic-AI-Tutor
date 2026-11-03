# Expanded dataset v0.2 integration status

2 November 2026. **The technical audit, review pipeline and opt-in integration handoff are complete. Human content approval, shared-app enablement and independent evaluation remain pending. This dataset is not production-approved.**

- `/Directions/` is Git-ignored; no Directions files were tracked. All project work is on D:. No commits or pushes were made.
- The original 26-file snapshot remains unchanged: `2fb0ffbb67ae8e5c69dda7ad8da3d4899a5afbbfdf9705b3b10efa67556a9b8c`. All 25 manifest members verify. The supplied validator ran on a separate copy. All 158 frozen v0.10.0 payload files also retain their recorded hashes.
- Verified inventory: 232 problems; 928 dialogues / 11,136 turns; 5,568 dependent tutor contexts; 2,400 learner messages; 464 critic pairs; 360 development security pairs; 87 unlabelled retrieval candidates; 90 glossary drafts; 32 quarantined T08 dialogues.
- A separate metadata derivative fixes 2,040 incorrect message family tags, with zero mismatches remaining and all wording, IDs, labels and review states preserved. All 20 stale intent counts are reconciled.
- All 232 reference answers pass exact checks derived from public problem statements. The balanced 116-dialogue review queue and two blinded 480-message views are ready. Actual human approvals and runtime examples remain zero.
- Promotion now retains a separate private review ledger with the exact revision, source attribution, reviewers, date, scores and ratified policy. Decisions bind policy content as well as source/revision hashes. The unratified default is confirmed to reject publication without creating either output.
- **38 integration tests and 30 existing application tests pass**, alongside 17 supplied checks. The full fixture review-to-prompt test excludes later answers and reviewer details. Six selected audit/review outputs reproduce exactly.
- The current opt-in runtime (`expanded-v02-contextual-preview-5`) received two actual model replies: wrong-answer feedback and an active-item hint. Both passed the buffered checks. Quiz start/submission made zero model calls. Code retains grading authority. The shared app remains unchanged; this is an isolated Quadratics smoke test, not a three-chapter deployment or learning study.

**Quality risks:** 5,568 tutor turns contain only 93 distinct lines; 360 security pairs use 10 distinct attack texts. The 29 active seed IDs are not the canonical 30-ID taxonomy. T08, retrieval labels and teaching quality still require subject/pedagogy review. Guards do not prove the absence of all partial or semantic answer leaks. Unknown cost and learning gains stay null.

**Next owners:** R1/R2/R4 ratify policy and perform genuine review; R2 settles taxonomy/T08; R3/R4 review and enable the candidate with three-chapter/API/UI traces; R5 commissions independent cases and human calibration. Commands and acceptance conditions are in `07_RUNBOOK.md`; `08_COMPLETION_AUDIT.md` separates delivered technical work from these pending gates.
