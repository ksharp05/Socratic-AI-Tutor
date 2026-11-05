# Current M3/M4 checkpoint - v3 offline validation ready

The user resumed work toward M3/M4 after PRs 2/3 merged. Continue on local **Beta** in `D:\Work\IITB\Socratic Tutor Main`; project cwd is canonical `D:\Work\IITB\Socratic Tutor`. Do not push Beta without the separate publishing request. Start at **`Docs/m3/v3/STATUS.md`** and **`TEAM_ACTIONS.md`**.

## What is now done

- Merged upstream milestone-2 PR2/PR3 into local Beta (integration3e56deb), preserving token caps and old frozen tags. Current runtime candidate is **e79d7d3**; all 554 regression tests passed, plus 21 focused policy checks after clarifying the test fixtures.
- Context-bound copying is implemented as an **opt-in** policy. Legacy behaviour/default remains available and the frozen run_session AST is identical. It removes only owned-format suffix matches and copying without explicit question context; ambiguous disclosures stay unreviewed, and old qualification flags remain conservative. Actual context-linked full matches and registered-practice telling remain possible. ContextVar scopes isolate concurrent sessions and no hidden quiz reference enters app/model input.
- All six three-chapter smokes passed (18 sessions), complete offline E1/E3/E4 tutoring matrix 224 sessions and E2 security160 cases completed with zero execution errors, and all three exact local CI gates passed. All18 smoke trajectories match full runs; C1/C2 match6/6. All536 offline citation snapshots pass hash/chapter/source checks; semantic faithfulness remains unreviewed.
- The cached 224-session audit reproduces every original baseline.161 of 177 copying witnesses came from the exact app format instruction; 16 are unattributed. All86 old post-copy triggers are removed under the candidate in these fixed trajectories. This is not a new live experiment or a human learning estimate.
- Canonical app/spec/policy copies now match the shared checkout (70 files checked); differing preimages are preserved privately. Dataset libraries/private configs were not replaced.

## The important remaining capability gap

Development cards have 17 seeded types / 24 card-type associations. Runtime loads 9 types and can cover only 12/24 associations: an optimistic **50% development micro-recall ceiling** and 9/17 type-macro ceiling; seven cards have no loaded seeded diagnosis. R3/R2 must work from the public catalogue and distinguishing evidence to complete/review adapters or explicitly settle scope. More repeat runs cannot remove this structural limit. Do not use private learner-card states or simulator rules to author diagnosis rules.

Full specialist-agent/question-setter acceptance is still R3 work; shared heuristic controllers and a positive session call count do not prove it. New telemetry records model calls per tutor-route turn for an actual pilot check.

## Prepared next actions - not approved or executed

A **six-session** C1/C2 pilot is prepared:3 existing cards (one per chapter), seed 1,8 turns, fixed gpt-4.1-mini, template voice, no judge. Proposed separate allowance **80 requests / USD 0.05**. Configs: `eval/configs/m3_v3_pilot_c1.toml` and c2. Runner `scripts/m3/run_v3_pilot.py` defaults to preflight; it refuses pending approval and checks the candidate source/data hashes. Receipt `Directions/m3_runs/v3/PILOT_APPROVAL.json` is **pending**, no approver/quote, no pilot wallet exists. Do not run --execute-live until actual approval. No provider ping or voice/judge requests are authorized.

Existing original wallet stays 1,000 attempts; the separate E3 extension has 36 completed attempts / USD0.0132756. Combined 1,036 used; known continuation cost USD0.2791804 excludes prior 98 unknown money. Both wallet hashes are unchanged. The 14 unused E3-specific requests are not transferable to this new pilot. Never reset or bypass a wallet.

A draft PR body is ready at `Directions/m3_runs/v3/BETA_DRAFT_PR.md`; Beta has not been published. The earlier user authorization covered PR2/PR3, not a new Beta push. Publishing can provide remote CI and team review after an actual user request.

## Human/team review package

- R2 decision template: `Directions/m3_runs/v3/human_actions/FINAL_PROTOCOL_DECISIONS.json`, all actual decision/reviewer/budget/seed fields blank.
- Focused copying-context packet: `Directions/m3_runs/v3/review_packets/post-copy-context-v1/`, 30 unique real contexts + 10 explicitly AI-authored controls,40 items, all labels blank. Keep mapping_private.json hidden. Controls are excluded from study metrics and are not independent final data.
- Existing 63-item leak/targets packet: `Directions/m3_runs/v2/live/review_packet_context_v2/`, untouched and blank. Two real independent people must label; R1/R5 are one person.
- Teacher lesson decisions remain blank in the prior human_actions/lesson_review.csv. R3/R2 scope/rule review, independent final-content/new attack authorship, semantic review, rater/judge calibration or explicit limitation, another member's installation and real failed-CI demonstration remain external gates. `TEAM_ACTIONS.md` states exact inputs/proofs by role. No messages have been sent to the team, and no approval is generated.

## Preserved historical evidence

All original v2 paid E1-E4 development runs are complete (224 tutoring sessions, 160 security cases,899 citation snapshots), including 48/48 candidate E3. Their reports remain `Docs/m4/E3_COMPLETE_RESULTS.*`, with original1,000-request report/tag and private archive preserved. They belong to the old behaviour; do not attribute them to this changed candidate. Final preregistration remains draft and formal M3/M4 acceptance is open.

Safe commands: use shared-checkout .venv and SOCRATES_SOURCE_WORKSPACE canonical. `report_v3.py` recomputes saved v3 reporting. `run_v3_pilot.py` is preflight-only without --execute-live and actual approval. `validate_v3.py` refuses existing runs; inspect completed indexes rather than silently repeat. `audit_copy_policy.py` refuses existing rating output; preserve labels and choose a new packet version if ever needed. No resume automation remains.
