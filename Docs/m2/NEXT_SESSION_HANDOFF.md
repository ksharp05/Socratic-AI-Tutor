# Next-session handoff

**Written:** 5 November 2026, end of day. **Branch:** `milestone-2`, pushed at `ee29630` (local and `origin` match). **Next roadmap date:** M3 "behaviour frozen" on Friday 6 November; Human day Saturday 7; M4 results Monday 9; content freeze Wednesday 11 at 9 pm; submit Thursday 12 by 6 pm; viva Sunday 15.

Read first: `AGENTS.md` and `PROJECT_CONTEXT.md` in the canonical workspace, then [STATUS.md](STATUS.md), [TESTPACK_RESULTS.md](TESTPACK_RESULTS.md) and [the work log](WORK_LOG.md).

## Where things stand

| Area | State |
| --- | --- |
| Docker | Verified on 5 Nov: a fresh clone builds and runs healthy in about 66 s, serves the teacher/learner flow and keeps state across `down`/`up`. Integrated overlay with a mounted index, the `ops` profile and a second machine are not verified. |
| Live model | Approved budget: **at most 1,000 model calls** for testing. Used so far: 3 on 4 Nov (probe + walkthrough), 95 on 5 Nov (test pack). State the call count and estimated cost before each live batch, and always use a hard cap (`--max-calls`). |
| Communication | New `converse` route and screened model replies to typed-in problems (`a3eae77`). The live test pack had 47 distinct replies across 54 typed problems and no leaks detected. Not yet reviewed by a person. |
| Test pack | User-supplied 180-case synthetic development pack at `C:\Users\Admin\Downloads\IITB_Socratic_Tutor_180_Case_Testpack_v1\socratic_tutor_testpack_v1`. Last live run: 166 pass / 11 fail / 27 pending. Development data only, never an independent score. |
| Install package | `setup/` scripts and `Docs/SETUP.md` (`516250c`, `ee29630`); a throwaway clone installed and passed the 325 CI tests. |
| Tests | 451 pass across the four suites (`tests`, `tests_beta`, `tests_book_pipeline`, `tests_integration_v02`). GitHub Actions results have not been checked (no `gh`; browser not signed in). |

## Next work, in priority order

1. **Confirm CI on GitHub** for `ee29630` (Actions tab). If it failed, fix that first.
2. **Retrieval misses (quick).** The graph's `textbook-kb` search (`src/tutor/mcp_servers/textbook_kb.py`, `_tokenise`) cannot match spelled-out ratio names: "tangent… sine and cosine" and "secant, cosecant and cotangent" return nothing. Add the same English→abbreviation expansion the beta registry already uses (see `Docs/m2/INTEGRATED_COMPOSE.md`). Also look at the wrong-note rankings for RAG-IN-002 and RAG-AR-006. Rerun `--suite retrieval` (no model calls).
3. **Plans that don't advance.** `src/tutor/learner.py`: `make_topic_plan` (AP/trig) only ranks quizzed concepts and always sets `mastered: []`, so a perfect quiz still says "practise" the same concepts. `make_plan` (quadratics) after a failed quiz moves to `qe01` without mentioning the quiz mistakes. Decide the intended behaviour (advance to the next concept on a perfect score; tie remediation to missed quiz concepts), then fix and rerun `--suite journey`.
4. **Stuck alert for new learners.** `src/tutor/app.py` `_update_memory` records a stuck signal only when one concept is unambiguous; practice items carry three concept tags, so a new learner never triggers the teacher alert (FLOW-011). Options: use the item's primary concept, or the current hint stage's concept. The existing test `tests/test_m2_stuck_alert.py` passes only because its demo learner has a flagged misconception.
5. **Human review of model replies.** Ask a teacher to score a sample of the live replies (rubric in the pack's `docs/RESEARCH_AND_EVAL_DESIGN.md`). Some replies give a method formula (for example the AP sum formula); the teacher should decide whether that is acceptable. Raw replies are in `Directions/testpack_runs/testpack-20261105T015243-c977ea/observations.jsonl`.
6. **M3 needs (Friday):** every experiment configuration runs on the two development cards, the pre-registration is hashed, and CI is green. The pack's `data/dev_cards.json` has 12 cards; use `[0:2]` for a C1/C2 comparison with matched settings, and count calls.
7. **Smaller items:** practice prompts display raw coefficients (`(5)*x^2+(-100)*x+(510)=0`); the answer-leak checker flags ordinary English with "none" as "no real roots"; complementary-angle and identity-sum maths have no task family; the integrated Compose overlay still needs an authorized index and trusted hash.

## Decisions waiting on the Lead

- Merge or review R3's two branches pushed on 3 Nov (`r3/cost-in-trace`, `r3/supervisor-model`), which are not in `milestone-2`.
- Write the M2 go/no-go and cut-list decision.
- Name the Human-day teacher and an independent author for final evaluation cases.
- The screened model reply for typed-in problems reverses the earlier deterministic-only rule (opt-in contextual mode only). Confirm that this trade-off is acceptable.

## How to work here

- **Two copies.** Code and git live in `D:\Work\IITB\Socratic Tutor Main` (branch `milestone-2`). The canonical workspace `D:\Work\IITB\Socratic Tutor` holds private data (`Directions/`, git-ignored) and a mirrored copy of the code and docs; its own `.git` has no commits. Edit in Main, then copy changed files to the canonical copy (they have been kept byte-identical).
- **Python:** `D:\Work\IITB\Socratic Tutor\.venv_app\Scripts\python.exe`. Full tests, from Main: set `SOCRATES_SOURCE_WORKSPACE=D:\Work\IITB\Socratic Tutor`, `TUTOR_LLM=stub`, `TUTOR_BETA_LIVE=0`, `PYTHONPATH=<Main>\src`, then `python -m pytest tests tests_beta tests_book_pipeline tests_integration_v02 -q -p no:cacheprovider` (about 2 minutes). Logs go to `Directions/git_delivery/`.
- **Model key:** only in `Socratic Tutor Main\.env`; the canonical `.env` has none. Live scripts must run from the Main copy.
- **Test pack runner:** `scripts/m2/testpack_run.py <pack_dir> [--suite S] [--ids A,B] [--smoke] [--live --max-calls N]`; score with the pack's `scripts/eval_cli.py score`. Commands are in `Docs/SETUP.md`, section 6.
- **Docker demo:** stack `tutor-accept` from the clone in the session scratchpad (`...\scratchpad\ci-clone`). Tokens: `local-teacher`, `local-student`. Stop it with `docker compose -p tutor-accept down`. Docker Desktop is a per-user install at `C:\Users\Admin\AppData\Local\Programs\DockerDesktop`.
- **Rules:** commit on `milestone-2` only and push only when the Lead says. Never invent human review, approvals or independent authorship. Never put case answer keys into prompts. Keep `Directions/` and `.env` out of git. The team channel is WhatsApp.

## Shared documents

- Status, 4 Nov: https://claude.ai/artifact/U8BWYgdSFzrnzpJoubG5e1
- Test results, 5 Nov: https://claude.ai/artifact/YNiDzZvMKMestnxkHnewTq
