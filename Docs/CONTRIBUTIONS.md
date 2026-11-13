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
### 2026-11-13 · Poonam / Punm-Butter (R3)
- **Work:**
  - Task C2: independent review of the new step-feedback code (`triangle_reasoning.py`, `ratio_hint.py`, commit `cf14173`), in [R3_C2_STEP_FEEDBACK_REVIEW.md](m3/R3_C2_STEP_FEEDBACK_REVIEW.md). Verdict: safe to build on. One decision for R1: the step box confirms a correct substitution, so it can act as an unrecorded answer check (C2-1). Two small bugs: a full on-top/below pair is not read without a ratio name (C2-2), and Hinglish without cue words gets an English reply (C2-3).
  - `tests/test_r3_step_feedback.py`: 174 portable tests, covering 83 first-step branches, 53 follow-up branches, next-question mapping, language choice, no numbers in any reply, 3,000 random steps and long-input timing, plus two strict-xfail tests for C2-2 and C2-3. CI now runs `ratio_hint.py` (0% to 100% of lines) and 94% of `triangle_reasoning.py` (was 67%). Eight deliberate breaks of the code each made a test fail.
  - Test runs, stub mode only: the CI test command gave 3,289 passed, 23 skipped, 92 deselected and 2 xfailed; the registry test, the C1 and dev-smoke harnesses and the security gate all pass.
- **AI-assisted:** the review, the probes, the tests and the note were drafted with Claude (Claude Code), which ran them in a throwaway copy first. I checked the findings, ran the tests and opened the PR.
- **Decisions:** none recorded. Open for R1: C2-1 (is confirming a correct substitution teaching help or an answer oracle?).

### 2026-11-12 · Swati / SwatiSmitaBiswal (R4)
- **Work:**
  - D-7 classifier wired into `guards.py`, off by default, fail closed; live check with my own key, locally only: 16/16 of my own messages routed as expected (PR #26, merged).
  - Crisis screens and injection check improved from the public test set, tuned on the dev pool only. New shared crisis forms (self-punishment, purging and starving, falls and poisons, indirect intent, Hindi and Hinglish self-harm); the injection check no longer needs "previous" or "prior"; one idiom filter shared by the team tutor and the beta; the beta's ACCESS uses the same injection pattern. Persona patterns tried and removed because they blocked harmless role-play on the dev pool.
  - Dev pool: crisis missed 19 to 3, injections missed 480 to 449, safe blocked 43 to 62 (mostly "ignore all instructions" prompts labelled safe). Core, measured once after tuning: crisis caught 27/88 to 35/88, Gandalf 33/200 to 112/200, deepset 4/125 to 26/125, safe blocked 5/1,031 unchanged.
- **AI-assisted:** patterns, tests and helper scripts drafted with Claude, then run, checked on the dev pool and reviewed by me.
- **Decisions:** none new. Open for the Lead: whether "ignore all previous instructions" prompts with harmless content should count as blocked (they do now).

### 2026-11-11 · Lakshya / ksharp05 (Lead, R1, R5)
- **Work:**
  - Reviewed and merged PRs 18-27 into `Beta` after a trial merge and the CI test set (2,841 passed); resolved the contribution-log conflict; pushed.
  - Put the new provider key in Vercel's encrypted settings and redeployed production from b697c79. The live check found forget-my-data failing (500) on the schema-1 database after PR 27; fixed it in `ef342dd` with a regression test and redeployed. Synthetic check profile deleted.
  - D-7 classifier comparison: eight course models on the 420-case security set (batch v4-sec-07).
  - Evaluation report: sections 1, 3-5, 7 and 8, and the E2 numbers in 2a.
- **AI-assisted:** code, tests, documents and runs done with Claude Code (Claude Code sessions) at my direction; the test suite ran on every change. I approved each spend, merge, push and deploy.
- **Decisions:** D-7 comparison run for the Lead's decision (see DECISIONS.md).

### 2026-11-11 · Swati / SwatiSmitaBiswal (R4)
- **Work:**
  - R1 answer rule in `mathcore.py`: "does not exist", "not possible" and "zero" accepted on term counts; a bare "no" asked again (PR #18, merged).
  - Lead's follow-ups: the leak check now blocks the full claims "no such AP" and "such an AP does not exist" while hints pass; "0" behaves like "zero"; "impossible" accepted; 71 tests (PR #24). Checked that no "which term" task uses unit "terms".
  - Reviewed `socrates_beta/safety.py` with 30 offline probes: crisis, abuse and secrecy screens catch the explicit and indirect forms and skip idioms; gaps recorded in the threat model.
  - Threat model v3 for the beta's safety layer, the exhausted key, DPDP (13 May 2027) and POCSO; decision D-7 (Gemma 4 31B replaces D-6's Llama 3.1 8B, from R5's evidence).
- **AI-assisted:** code changes, tests, probes and documents drafted with Claude, then run, checked against the code and R5's reports, and reviewed by me.
- **Decisions:** D-7 recorded (Lead to confirm).
### 2026-11-11 · Poonam / Punm-Butter (R6, standing in)
- **Work:** done because the R6 owner has not replied; the Lead decides whether to merge it.
  - The beta's answer hint under term-count questions now says "empty set", matching the questions and the R1 rule. Also R6's serving and operations paragraph in report section 2. PR #20.
  - Answer-leak alert, API part: `POST /alerts/grafana`, `GET /teacher/alerts`, a System alerts table on the teacher page, leak counters that start at 0 (without this the alert could never fire), and `scripts/fire_leak_alert.py`. 6 tests. PR #21.
  - Answer-leak alert, Grafana part: the provisioned alert rule and webhook, and the shared token in Compose. PR #22.
  - Ran the Compose `ops` stack on macOS for the first time. Grafana loaded the dashboard and the rule, the fire script blocked 20 of 40 drafts, the rule fired, and the teacher's page showed the alert. Recorded in `Docs/deploy/README.md` with three screenshots.
  - Test runs, stub mode only: the CI test command gave 2,781 passed (PR #20 branch) and 2,787 passed (PR #21 branch), with 7 skipped and 34 deselected.
- **AI-assisted:** code, tests, docs and the run steps drafted with Claude (Claude Code), which tested each change in a throwaway copy first. I ran every command, the Docker stack and the tests, took the screenshots, and checked the results.
- **Decisions:** none recorded. Open for the Lead: whether to merge PRs #20–#22, and a beta redeploy after #20.

### 2026-11-11 · Poonam / Punm-Butter (R3)
- **Work:**
  - Contribution log entries for 3–10 Nov. PR #19.
  - Checked with `scripts/qa/stress_phrases.py` that PR #18's answer rule reaches the grader through my router: "does not exist", "not possible" and "zero" are now graded, and a bare "no" is still asked again.
- **AI-assisted:** the entries and the check drafted with Claude (Claude Code); I ran the check and reviewed the text.
- **Decisions:** none.

### 2026-11-11 · Rizwan (R2)
- **Work:**
  - Reviewed PR 8 (saved revisit marks) and its oldest-first follow-up against the R2 memory contract: accepted, with two small R3 follow-ups and one design question ([R2_PR8_MEMORY_REVIEW.md](m3/R2_PR8_MEMORY_REVIEW.md)). Added the missing revisit-queue row to [MEMORY_POLICY.md](MEMORY_POLICY.md).
  - Built the live beta's saved-question queue per browser profile (step 6 of the PR 7-9 fix plan): `revisit_queue` in both beta stores, Postgres schema version 2 (new code also runs on an unmigrated version-1 database with the queue off, so deploy first, then migrate; see `Docs/deploy/VERCEL_BETA.md`), and the practice hook in `socrates_beta/maths.py` (save at the last hint, serve first in a later conversation, clear only on a code-checked correct answer, never in quizzes). Additive API fields for R6: `revisit` on the assessment and `saved_for_later` on hint and submit responses.
  - 30 tests in `tests_beta/test_revisit_queue.py`, on SQLite and on a real loopback Postgres 17: idempotence, oldest first, profile isolation, content binding, transaction rollback, Forget, the 100-row cap, v1-to-v2 migration, and the full live-site stack with restart.
  - Proposed how to skip questions solved in earlier sessions (step 7, [R2_CROSS_SESSION_PROPOSAL.md](m3/R2_CROSS_SESSION_PROPOSAL.md)), for discussion before anything is built.
- **AI-assisted:** code, tests and documents drafted with Claude Code, then run and reviewed by me.
- **Decisions:** none recorded. Open: Q1-Q4 in the proposal; the Lead runs the schema migration after deploying this code.

### 2026-11-10 · Lakshya / ksharp05 (Lead, R1, R5)
- **Work:**
  - Security test (USD 5 programme): 420 attack and control cases in English, Hindi and Hinglish, research notes, the hardened front-door prototype v4 and two AI judges; security test report.
  - Ported the deterministic safety layer into the live beta (49749be): crisis, child-safety and secrecy screens, wider redaction, answer-check replies and maths-kernel limits.
  - Pipeline deep-dive fixes (bb13bd0): retrieval stoplist, Hindi glossary and relevance floor; in-scope hits 67 to 75 of 92, false matches 20 to 10 of 45.
  - Merged PRs 10-17 and redeployed production from d15e545. Quality and safety plan.
- **AI-assisted:** code, tests, documents and runs done with Claude Code (Claude Code sessions) at my direction; the test suite ran on every change. I approved each spend, merge, push and deploy.
- **Decisions:** recommended Gemma 4 31B as the safety classifier (recorded by R4 as D-7).

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

### 2026-11-09 · Lakshya / ksharp05 (Lead, R1, R5)
- **Work:** reviewed PRs 7-9 and PR 10; stress-tested the merged code, wrote the findings and a fix plan with owners for every role (`Docs/m3/`); put the guard-model spike behind `--execute-live`.
- **AI-assisted:** code, tests, documents and runs done with Claude Code (Claude Code sessions) at my direction; the test suite ran on every change. I approved each spend, merge, push and deploy.
- **Decisions:** none.

### 2026-11-09 · Swati / SwatiSmitaBiswal (R4)
- **Work:**
  - Set up `milestone-2` locally (Python 3.12 via uv, `.venv`): `pytest -q` 378 passed; `tutor check-llm` OK with my own key; confirmed `.env` is git-ignored.
  - Checked `config/app.toml`: none of the 25 course models is a dedicated guard model, so neither Llama Guard 4 nor Llama Guard 3 is available.
  - Wrote the one-page [threat model](THREAT_MODEL.md) from the milestone-2 code (`guards.py`, `toolbus.py`, `approval_token.py`). PR #10.
  - Requested and received Hugging Face access to Prompt Guard 2 (Llama 4 gated collection).
- **AI-assisted:** setup guidance and the threat-model draft with Claude, then checked against the code and reviewed by me.
- **Decisions:** none yet. The guard-model replacement will be tested and proposed (open item in the threat model).

### 2026-11-07 · Lakshya / ksharp05 (Lead, R1, R5)
- **Work:** distress screen now catches "don't want to live" and similar messages, with tests.
- **AI-assisted:** code, tests, documents and runs done with Claude Code (Claude Code sessions) at my direction; the test suite ran on every change. I approved each spend, merge, push and deploy.
- **Decisions:** none.

### 2026-11-07 · Poonam / Punm-Butter (R3)
- **Work:**
  - After the last hint, the tutor shows R4's checked worked example word for word (TP-A2). 4 tests. PR #7.
  - Revisit marks are saved in the learner store across sessions and cleared by a correct answer (TP-A3). 7 tests. PR #8.
  - "There is no such term" and similar phrasings are understood as an answer on term-count items; this also changed R4's leak check, which I flagged for the Lead. 21 tests. PR #9.
  - Test runs, stub mode only: the CI test command gave 2,620 passed, 7 skipped and 34 deselected (PR #9 branch), and the registry, C1, dev_smoke and security gates passed.
- **AI-assisted:** code and tests drafted with Claude (Claude Code), then edited, run and checked by me.
- **Decisions:** none.

### 2026-11-06 · Lakshya / ksharp05 (Lead, R1, R5)
- **Work:**
  - Deployed the live beta on Vercel with Neon Postgres: saved progress per browser profile, consent before any model call, a capped hosted lease (200 requests, USD 0.50), source-grounded live chat and eight versioned OpenStax-based notes.
  - Exact maths validation, verified practice tools, AP practice families; v2 and v3 offline qualification and an approved live pilot; CI recovery.
- **AI-assisted:** code, tests, documents and runs done with Claude Code (Claude Code sessions) at my direction; the test suite ran on every change. I approved each spend, merge, push and deploy.
- **Decisions:** none.

### 2026-11-06 · Poonam / Punm-Butter (R3)
- **Work:**
  - After the last hint, the tutor stops repeating that hint and marks the item for revisit, for the current session only (item 8, partial). PR #4.
  - Loaded misconceptions qe_m07–qe_m10 with discriminant rules and keywords: 30 of 30 catalogue examples are now recognised, but those examples were also the source of the patterns. PR #5.
  - Wrote `Docs/m3/R3_SPECIALISTS.md`, proposing the graph's specialists as the equivalent for R3 item 1, and recorded why `dev_live` did not run. PR #6.
- **AI-assisted:** code, tests and the write-up drafted with Claude (Claude Code), then edited, run and checked by me.
- **Decisions:** none. `R3_SPECIALISTS.md` is waiting for the Lead's acceptance.

### 2026-11-05 · Lakshya / ksharp05 (Lead, R1, R5)
- **Work:**
  - M3/M4 development runs (E1 c0/c1/c2, E3 with an approved 12-session extension, E4a, E4b, E2 guards on and off), the post-quiz copying sensitivity and the acceptance audit (`Docs/m4/`).
  - Fixed urgent-distress routing and numeric probes; added the prerequisite install package.
- **AI-assisted:** code, tests, documents and runs done with Claude Code (Claude Code sessions) at my direction; the test suite ran on every change. I approved each spend, merge, push and deploy.
- **Decisions:** none.

### 2026-11-05 · Poonam / Punm-Butter (R3)
- **Work:**
  - The model writes tutor turns under the teaching policy, and writes the diagnosis question behind a safety check. Made-up citations are replaced with real ones. Added the qe_m02 sign rule and catalogue keywords. PR #3.
  - The OpenRouter cost is read safely when a reply has no response metadata. PR #2.
- **AI-assisted:** code and tests drafted with Claude (Claude Code), then edited, run and checked by me.
- **Decisions:** none.

### 2026-11-04 · Lakshya / ksharp05 (Lead, R1, R5)
- **Work:** Milestone 2 baseline: chapter quizzes and learner plans, teacher-authorised learner deletion, publication integrity across sessions, the browser connected to the graph tutor, the integrated container start-up and two approved bounded live probes.
- **AI-assisted:** code, tests, documents and runs done with Claude Code (Claude Code sessions) at my direction; the test suite ran on every change. I approved each spend, merge, push and deploy.
- **Decisions:** none.

### 2026-11-03 · Lakshya / ksharp05 (Lead, R1, R5)
- **Work:** the Socrates beta and dataset pipelines, the Milestone 2 development baseline, homework safety and local teacher alerts, and the shared documentation clean-up.
- **AI-assisted:** code, tests, documents and runs done with Claude Code (Claude Code sessions) at my direction; the test suite ran on every change. I approved each spend, merge, push and deploy.
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
