# Beta continuation - 5 November 2026

The user requested a new **local `Beta` branch**, created from `3dd518ac228f07e69969120c21b251eba52161b3` (the milestone-2 handoff). This replaces the older milestone-only branch instruction for this continuation. Work stays local until the Lead requests a push. The branch name is separate from the existing anonymous Socrates beta application.

## Changes

- The connected textbook search canonicalises English ratio names and abbreviations, including `cosec`/`csc`, in both the card and hybrid BM25 paths. Whole-word matching preserves unrelated words, and chapter filtering is unchanged.
- Quiz plans prioritise associated mistakes and retain the question IDs and weak prerequisites that justify review. Successful quiz evidence prioritises ready successor concepts; it does not raise stored mastery. `quiz_passed` records this quiz's successful concept associations separately from `mastered`, which still uses the configured 0.95 BKT threshold. Multi-tag questions remain concept associations, not proof of an individual misconception or independent mastery.
- Explicit stuck reports in three distinct registered-practice sessions can now create a local teacher-view alert for a new learner. Specific misconception evidence takes precedence; otherwise attribution uses the item's first registered concept. This fallback is an operational routing choice, not a diagnosed misconception. Repeated reports in the same session still count once; no external notification or human acknowledgement is claimed.

## Offline evidence

All runs used the stub model, with zero provider calls. The supplied pack is synthetic development data, not an independent evaluation. Raw evidence is excluded from Git under the canonical workspace's `Directions/`.

| Check | Result | Local evidence |
| --- | --- | --- |
| Retrieval baseline | 20/24 fixture hits; 24 citation checks pending | `Directions/testpack_runs/testpack-20261105T025012-d1173d/` |
| Retrieval after ratio normalisation | 22/24 fixture hits; 24 citation checks pending | `Directions/testpack_runs/testpack-20261105T025438-f9191f/` |
| Initial journey rerun (before successor ordering refinement) | 12/12 direction checks; zero execution errors | `Directions/testpack_runs/testpack-20261105T025439-9f2c9e/` |
| New-learner stuck alert FLOW-011 | Required recorded event present | `Directions/testpack_runs/testpack-20261105T025452-39977e/` |
| Final journey rerun | 12/12 direction checks; perfect AP starts with successor ap05 | `Directions/testpack_runs/testpack-20261105T025830-3307fa/` |
| Canonical mirrored copy | 36 focused regression/quiz/alert checks pass | `Directions/git_delivery/beta_focused_canonical_01.log` |
| Final shared-checkout full run | **468 pass** across all four suites, 106.76 seconds | `Directions/git_delivery/beta_full_team_02.log` |

Completed plans now say there are no new steps and suggest discussing review or the next topic with the teacher.

The pack's direction check looks at the first concept's association with the quiz. It does not establish pedagogical quality or real learner progression. Source changes were still uncommitted when these runs were recorded; their metadata correctly retains the base commit and dirty-tree flag.

## Remaining work

- Remote GitHub Actions is unverified: the connected GitHub API returned 404 for the repository's Actions runs. No remote CI failure or success is inferred.
- Two retrieval cases still miss: RAG-IN-002 asks for basic trigonometric ratios while the intended note contains only formula abbreviations; RAG-AR-006 asks whether terms remain positive while the intended note discusses a decreasing progression and negative values. These require broader vocabulary/ranking work. No synthetic note, expected label or frozen content was changed to force a hit.
- Educator review of saved live replies, the Lead's M2 decision and branch review, independent final case authorship, and the M3 C1/C2 comparison remain as listed in [the prior handoff](NEXT_SESSION_HANDOFF.md). Prior live budget usage remains **98/1,000**; this continuation adds zero calls.
- Integrated Compose with an authorised index and trusted hash, a second-machine check and the smaller display/checker issues remain open. No new production or human-review acceptance is claimed.
