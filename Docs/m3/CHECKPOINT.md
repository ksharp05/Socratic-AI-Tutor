# M3/M4 checkpoint - development results ready, approval gates open

Continue locally on `Beta` in `D:\Work\IITB\Socratic Tutor Main`; all project commands use canonical `D:\Work\IITB\Socratic Tutor` as cwd. Mirror changed project files here. Do not push. Read `Docs/m4/RESULTS.md` before changing anything.

## Current evidence

- Frozen teaching behaviour: `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`, tag `beta-m3-behaviour-v2`. That source passed 496 regressions, six two-card smoke configurations and all three CI evaluation gates. C1/C2 replays match 4/4 sessions; all 224 v1-to-v2 offline core trajectories are unchanged. Original v1 safety failures remain preserved.
- Baseline Actions run 41908712265 passed on `3dd518a`. Beta is local and has no remote CI run. Reporting/approval-gate changes happened after all paid runs; they do not retroactively change the source recorded by the runs. All 500 final regression checks passed (396 core + 104 beta/data-pipeline/integration); no provider calls were sent by verification.
- Live E1: C0/C1/C2 each 48 sessions. E4: memory-off/telling each 16, with matched C2 seed-1 comparators. E2: 40 previously seen attacks + 40 controls per selected-guard condition. E3: 36 of the original 48 candidate sessions, four cards per chapter, seeds 1/2/3; candidate lessons remain unreviewed. Total: 212 study tutoring sessions, four pilot sessions, 160 safety cases.
- All 856 normal-study citation snapshots match their hash/chapter/source text. Semantic faithfulness is unmeasured. C2 does not improve the recorded success proxy over C0/C1; diagnosis recall is low. Guards-on has 0/18 observed attack violations, but 27/80 cases per condition are unsupported/semantic unknown. No human learning or final safety claim. A subsequent scoring audit found code-flagged post-answer matches in 83/212 sessions; generic numeric instructions can trigger them, and the harness then enables post-quiz copying. Quiz changes are not clean learning estimates; primary runs remain unchanged. See `Docs/m4/ACCEPTANCE_AUDIT.md` for the complete milestone checklist, central log coverage and remaining failed-CI/independent-install evidence.
- Shareable report, JSON, CSV and figure: `Docs/m4/`. Raw evidence is ignored under `Directions/m3_runs/v2/`; no raw learner cards, keys, transcripts or wallets are committed.

## Hard stop before any new provider request

The original wallet `Directions/m3_runs/provider_budget.json` contains **902 new completed attempts + 98 prior = 1,000/1,000**. All 902 new attempts exposed cost: **USD 0.2659048**, no errors/reservations/refused attempts. Prior-98 money is unknown. Never reset, edit, delete or bypass this wallet. No voice or judge calls were made.

Do not rerun the original full `m3_live_e3_after` configuration or the completed tranche. The exact remaining four cards / 12 sessions need an estimated 36 requests. `Docs/m4/REMAINING_E3.md` and `eval/configs/m3_live_e3_remaining4.toml` propose at most **50 additional requests / USD 0.03**. The private receipt `Directions/m3_runs/v2/live/E3_EXTENSION_APPROVAL.json` remains **pending**, with no approver or quote. No fresh allowance has been granted. An extension wallet must not exist before actual approval. The code refuses a pending receipt and chains approved extensions to the exact original ledger hash.

Only an actual user answer can approve this extension. A scheduled continuation, account reset, preselected option or elapsed time is not approval. After approval, record the exact quote and identity; inspect pending evidence and deduplicate before calling. Do not repeat any interrupted session silently.

## Data and human work

The development export has 16 source cards (6 QE, 5 AP, 5 trig), 22 pairs / 44 quiz records, 17 seeded misconception types and 160 internally consistent golden references. There is no practice-record overlap. Eight seeded types have no runtime diagnosis adapter; five card/misconception associations cannot show in their assigned quizzes. The runtime has 131 registered practice items, 12 quizzes, 22 concepts/cards and nine diagnosis types. Candidate-final 24 cards / 30 pairs have not been exported or run. Frozen dataset integrity is verified; no final selection/freeze was performed.

Use the non-overwriting calibration packet `Directions/m3_runs/v2/live/review_packet_context_v2/`: 60 actual turns + three existing AI-drafted fixtures, 63 items total, all human labels blank. Proposed sample classes (36 none / 7 partial / 20 full) are not ground truth. Keep `mapping_private.json` hidden from raters; exclude fixtures from experimental metrics. The blank agreement check has zero jointly rated items and no kappa. Do not call a judge before calibration and request-budget approval.

Teacher lesson decisions are blank in `Directions/m3_runs/v2/human_actions/lesson_review.csv`. R2/Rizwan must decide the draft final preregistration; independent raters/final-content authors, new attacks/controls, semantic review and final-study budget remain external gates. The draft's obsolete “already frozen” sentence has been corrected without changing its draft status. Do not invent approval or a rejected lesson.

## Resume and reporting

A one-time continuation is scheduled in this chat for 06:32 IST, 5 November, after the account's reported 06:31:31 reset. The computer and Codex must remain on. Do useful authorized local work; the request cap still applies. Do not create duplicate experiments.

Safe saved-data commands use the shared checkout's `.venv/Scripts/python.exe` (the canonical dataset `.venv` does not contain pytest), `SOCRATES_SOURCE_WORKSPACE` set to the canonical workspace, and explicit script paths:

- `scripts/m3/analyse.py --stage live --revision v2` recalculates saved evidence and preserves existing rater files.
- `scripts/m3/deliver_results.py` writes the present 1,000-request development report. It intentionally asserts this evidence boundary; a newly approved extension needs an explicitly versioned combined report rather than silently rewriting the original boundary.
- `scripts/m3/plot_results.py` uses isolated private plotting dependencies and makes no provider request.

The formal M3/M4 goal remains incomplete. Do not label the 36-session E3 tranche as the original full design, or the development engineering checkpoint as human-approved final preregistration.
