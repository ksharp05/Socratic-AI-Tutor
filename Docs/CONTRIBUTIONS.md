# Contribution log

Every member adds an entry for each day they work, newest first. The course guide asks us to show who did what and where AI tools were used.

**Format:**

```
### YYYY-MM-DD · <name> (<role>)
- **Work:** what you did, with PR links
- **AI-assisted:** which parts, and which tool
- **Decisions:** any, with a link to Docs/DECISIONS.md
```

---
### 2026-11-10 · Poonam / Punm-Butter (R3)
- **Work:**
  - Saved questions now come back oldest first: `_due_revisit` keeps the order `read_learner` returns (finding 6, step 3). One new test, which fails on the old code. PR #11.
  - Empty-set answers on term-count items ("{}", "∅", "empty set", "none", "no such AP") now reach the grader, using `EMPTY_SET_ANSWER` from PR #12 (step 1, router part). 10 tests, 8 of which fail without the change. PR #15.
  - Architecture diagram (our redraw of Figure 4) and a numbered walkthrough tied to a real 36-row stub trace in `Docs/report/ARCHITECTURE.md`, plus report section 2, the system. PR #16.
  - Report section 6, lessons: the candidate playbook with review pending, and the development E3 check for harmful lessons. PR #17.
  - Test runs, stub mode only: the CI test command gave 2,632 passed (PR #11 branch) and 2,683 passed (PR #15 branch), with 7 skipped and 34 deselected.
- **AI-assisted:** code, tests and report text drafted with Claude (Claude Code), which also tested each change in a throwaway copy first. I made every edit, ran every command and test, and checked the results.
- **Decisions:** none.

### 2026-11-10 · Swati / SwatiSmitaBiswal (R4)
- **Work:**
  - Fixed findings 1-3 in `mathcore.py`: empty-set term-count answers, "no such term in this AP", and a narrower leak check; 42 regression tests. PR #12.
  - Fixed the `hopeless at <subject>` distress false alarm in `guards.py`; 14 tests in both directions. PR #13.
  - Threat model v2 for Beta and the live site; retargeted PR #10 to Beta.
  - Evaluation report section 2a, safety and control. PR #14.
  - Test runs: tests/ suite 2,145 passed (PR #12 branch) and 2,117 passed (PR #13 branch). Checked with `git stash` that the 3 `test_postgres_beta.py` failures are a missing `psycopg` on my laptop, not my changes.
- **AI-assisted:** code fixes, tests and documents drafted with Claude, then run, checked against the code and reviewed by me.
- **Decisions:** none recorded. Open: the R1 question on accepting "does not exist", "not possible", "no" and "zero" (PR #12), and the D-6 budget (Lead).

### 2026-11-09 · Swati / SwatiSmitaBiswal (R4)
- **Work:**
  - Set up `milestone-2` locally (Python 3.12 via uv, `.venv`): `pytest -q` 378 passed; `tutor check-llm` OK with my own key; confirmed `.env` is git-ignored.
  - Checked `config/app.toml`: none of the 25 course models is a dedicated guard model, so neither Llama Guard 4 nor Llama Guard 3 is available.
  - Wrote the one-page [threat model](THREAT_MODEL.md) from the milestone-2 code (`guards.py`, `toolbus.py`, `approval_token.py`). PR #10.
  - Requested and received Hugging Face access to Prompt Guard 2 (Llama 4 gated collection).
- **AI-assisted:** setup guidance and the threat-model draft with Claude, then checked against the code and reviewed by me.
- **Decisions:** none yet. The guard-model replacement will be tested and proposed (open item in the threat model).

### 2026-11-07 · Poonam / Punm-Butter (R3)
- **Work:**
  - After the last hint, the tutor shows R4's checked worked example word for word (TP-A2). 4 tests. PR #7.
  - Revisit marks are saved in the learner store across sessions and cleared by a correct answer (TP-A3). 7 tests. PR #8.
  - "There is no such term" and similar phrasings are understood as an answer on term-count items; this also changed R4's leak check, which I flagged for the Lead. 21 tests. PR #9.
  - Test runs, stub mode only: the CI test command gave 2,620 passed, 7 skipped and 34 deselected (PR #9 branch), and the registry, C1, dev_smoke and security gates passed.
- **AI-assisted:** code and tests drafted with Claude (Claude Code), then edited, run and checked by me.
- **Decisions:** none.

### 2026-11-06 · Poonam / Punm-Butter (R3)
- **Work:**
  - After the last hint, the tutor stops repeating that hint and marks the item for revisit, for the current session only (item 8, partial). PR #4.
  - Loaded misconceptions qe_m07–qe_m10 with discriminant rules and keywords: 30 of 30 catalogue examples are now recognised, but those examples were also the source of the patterns. PR #5.
  - Wrote `Docs/m3/R3_SPECIALISTS.md`, proposing the graph's specialists as the equivalent for R3 item 1, and recorded why `dev_live` did not run. PR #6.
- **AI-assisted:** code, tests and the write-up drafted with Claude (Claude Code), then edited, run and checked by me.
- **Decisions:** none. `R3_SPECIALISTS.md` is waiting for the Lead's acceptance.

### 2026-11-05 · Poonam / Punm-Butter (R3)
- **Work:**
  - The model writes tutor turns under the teaching policy, and writes the diagnosis question behind a safety check. Made-up citations are replaced with real ones. Added the qe_m02 sign rule and catalogue keywords. PR #3.
  - The OpenRouter cost is read safely when a reply has no response metadata. PR #2.
- **AI-assisted:** code and tests drafted with Claude (Claude Code), then edited, run and checked by me.
- **Decisions:** none.

### 2026-11-03 · Poonam / Punm-Butter (R3)
- **Work:**
  - The OpenRouter cost is saved as `cost_usd` in LLM trace events (R3 item 5), with one test against a fake OpenRouter. PR #2.
  - Proposed `anthropic/claude-haiku-5.5` as the supervisor and planner model. PR #1.
- **AI-assisted:** code, test and decision text drafted with Claude (Claude Code), then edited, run and checked by me.
- **Decisions:** [D-5](DECISIONS.md#d-5--2026-11-03--supervisor-model-anthropicclaude-haiku-55-provisional): proposed by me; the Lead confirms in review.

### 2026-10-31 · Lakshya / ksharp05 (Lead, R1, R5)
- **Work:**
  - Merged the proof of concept, roadmap and live-model setup into `main`.
  - Updated the [lead roadmap](LEAD_ROADMAP.md): team names, what we found on 31 Oct (the NCERT files and the course keys), re-dated milestones, and an R5b role for the sixth member.
  - Recorded the role names as [D-2](DECISIONS.md).
  - Wrote the R1 and R5 work plan: deliverables by day, hand-offs, inputs needed, decisions for the meeting and outside research. Fixed the vendored kernel's line endings so its hashes match, and git-ignored `eval/private/`.
  - Built the evaluation pipeline (R5) on branch `r5/r1-r5-work-plan`: a simulator independent of the tutor, the harness with run manifests, the policy leak checker, metrics and tables, the judge runner, kappa tools, the security runner, CI gates, a pre-registration draft and the rater guide. Teaching policy v0 (R1).
  - Set up live model access with the course keys: a `.env` template; `tutor check-llm`, which tests a key against one model or every course model; a warning, and an eval report count, when a live call fails and a template is used; the course model list in `config/app.toml`; 5 tests using a local fake server.
- **AI-assisted:** code, tests and docs written with Claude Code, then reviewed and tested.
- **Decisions:**
  - [D-2](DECISIONS.md): role names, proposed in the group; confirmed at the 1 Nov meeting.
  - Open questions added to [DECISIONS.md](DECISIONS.md#still-open): the plan models the course keys don't reach, whether one key may be a GitHub secret, and D-3 and D-4 for the meeting.

### 2026-10-30 · ksharp05 (Lead, R1, R5)
- **Work:** pushed the proof of concept to branch `poc/walking-skeleton`; wrote the [lead roadmap](LEAD_ROADMAP.md), the contributing guide and the pull request template; added the tutor-visible dataset content.
- **AI-assisted:** written with Claude Code, then reviewed and tested.
- **Decisions:**
  - [D-1](DECISIONS.md): takes R1 and R5 alongside Lead, with hand-offs for the separation rules.
  - Proposes running the rest of Phase 1 from the POC (open decision Q9).

### 2026-10-24 · ksharp05 (Lead)
- **Work:**
  - Wrote the proposed project plan ([Docs/plan](plan/README.md)) and updated it to use faculty-provided API keys.
  - Built proof of concept v0: the session and approval graphs, four MCP servers with hooks, guardrails, learner model, a simulated-student smoke test and 25 tests ([Docs/poc](poc/README.md)).
- **AI-assisted:** research, code and documents written with Claude Code, then reviewed and tested.
- **Decisions:** none. The plan remains proposed.
