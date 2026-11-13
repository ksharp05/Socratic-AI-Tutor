# Integration and cleanup (14 Nov 2026)

- **Merged and pushed to `Beta`:**
  - PR #29 (R3, C2 review);
  - PR #30 (R4, A6 security fixes);
  - the R1/R5 reviews;
  - the offline front-door safety gate in CI, with `tests/regressions/`;
  - fixes for C2-2 and C2-3.
- **Decisions:**
  - D-8: the crisis masking is off by default.
  - D-9: the B3 safety pre-registration is frozen, approved by the Lead; tag `prereg-safety-b3`.
  - C2-1 is open for the team.
- **Docs cleanup:**
  - 93 superseded files were removed (m2 notes, product_quality v1–v3, m3/v3, dataset integration v0.2, POC, specs, Milestone 2 requirements), together with the course PDF.
  - Evidence cited by the report stays: `m4/`, three `m2/` files, two `m3/v3/` files and `ci_failure.md`.
  - Everything removed is at tag `docs-archive-2026-11-14`, and links point there. Start at `Docs/README.md`.
- **Read the sections below as history.** Paths in them may now be at the archive tag.

# Team plan and Beta push (13 Nov 2026)

- **Pushed to `origin/Beta` (f670035):**
  - step feedback in practice;
  - the emotional-support reply;
  - crisis-mention masking (needs an R1 and R4 review before production);
  - the `SafetyScreenPort` socket (nothing connected yet);
  - the retrieval cache and single write transaction;
  - the password and system-prompt injection guard.
- **Tests:** CI set 3,117 passed, 23 skipped. The 87 `local_corpus` tests pass locally. Eight new corpus-dependent tests are now marked `local_corpus`.
- **Team plan:** `Docs/m3/TEAM_ROLE_PLAN_2026-11-13.md`, with workstreams A–F, role cards, a timeline to 29 Nov, risks and sources.
- **Key finding:** the 68/88 crisis result needs local Gemma. The Vercel-deployable portable model gives 59/88 crisis and 7/1,031 benign blocks. The public core has been used for selection, so treat it as development evidence until there is a sealed set (B1).
- **Production is unchanged** (db49b7d).

---

# After v1.0, on Beta only (12 Nov 2026)

- **Workflow.** Everything lands on Beta first. On 12 Nov the Lead moved Beta over: `main` was fast-forwarded to Beta and now holds everything below. The `v1.0` tag stays at d139762, the submitted release.
- **README rewrite** (3ed23cd).
- **Chat: Enter sends, Shift+Enter adds a line** (db49b7d). An input-method Enter (Hindi) never sends. Tested in the local offline beta.
- **Production now runs Beta db49b7d:** `dpl_9uoVZqtLgPJYVEARmFnLf8BBvPFH`. Health is OK, and the served `app.js` is identical to the commit. Production is therefore ahead of the `v1.0` tag (chat Enter key only).

---

# Release v1.0 (12 Nov 2026)

- **Code freeze declared by the Lead.** Tag `v1.0` is on the commit that records this. `main` is fast-forwarded to it.
- **Production:** `dpl_FVKCMZZe7P8EgeuGeHr9j9igwX4u`, deployed from 39b94d1 (same runtime as the tag; only documents differ). The release check passed; receipt `Directions/deployment/live_chat_02/LIVE_ACCEPTANCE_04_V1.json`.
- **CI test set:** 2,858 passed, 23 skipped; the three gates pass.
- **Not done:**
  - The schema-2 migration (after the viva).
  - The demo recording (the Lead).
  - Teammates' final log entries.
  - The human mobile check.
- The key expires 16 Nov.

---

# Earlier history (5–12 Nov 2026)

The checkpoint entries from 5 Nov to the early morning of 12 Nov (submission day, the D-7 comparison, the new key, the live beta, M3 and M4 work) were moved out on 14 Nov to keep this file short. They are unchanged at the tag `docs-archive-2026-11-14`: [CHECKPOINT.md at the archive tag](https://github.com/ksharp05/Socratic-AI-Tutor/blob/docs-archive-2026-11-14/Docs/m3/CHECKPOINT.md).
