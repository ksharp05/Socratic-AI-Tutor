# Plan to submission, and what Claude needs from Lakshya

How the R1 and R5 work, built with Claude Code, gets from today to submission. Part A is the plan: what gets built, on which day, and what it waits on. Part B is the requirements list: everything only Lakshya can do, decide or provide.

- **Status:** 1 Nov 2026 (meeting day). Builds on the [R1 and R5 work plan](R1_R5_WORK_PLAN.md) and the [lead roadmap](../LEAD_ROADMAP.md); where dates differ, the roadmap wins.
- **Deadlines:** content freeze **Wed 11 Nov, 9 pm**; submission **Thu 12 Nov, 6 pm**; viva **Sun 15 Nov**. Course keys expire on 16 Nov.
- **Branch:** everything is on `integration/local`, local only, 91 tests passing. Nothing is pushed until Lakshya says so.

## Where we stand

| Ready | Blocked, and on what |
|---|---|
| • Evaluation pipeline: simulator (30 misconceptions, 24 of 24 validation checks), harness with manifests and budget caps, leak checker, metrics, tables, judge runner, kappa tools, security runner, CI gates<br/>• Freeze script, pre-registration draft, rater guide<br/>• Policy v0; R1 drafts: 48 leak examples, 45 teaching scenarios; 10 new E2 attacks outside git<br/>• R6's API, UI and Compose; R2's hybrid retrieval; merged locally<br/>• Live cost measured (spike S6) | • **No `eval/dev/` yet:** the held-out freeze has not been run (Lakshya)<br/>• **E1 cannot be measured:** the tutor makes no model calls yet, and `c0` and `c1` do not exist (R3)<br/>• **E2 can only run all-on vs all-off:** no per-layer switches or injection hooks (R4)<br/>• **E4a, E4b:** no `memory_off` (R2) or `direct_answers` (R3 + R4)<br/>• **All R1 drafts** count only after Lakshya reviews them |

## Part A · The plan

**Who does what.** "Claude" means work Claude Code does for Lakshya in the safe scope: R1 and R5 code and drafts, plus specs for others. Under D-1, Claude never writes prompts, agents, guards or diagnosis rules (R3 and R4 own those), and every AI draft is marked for Lakshya's review.

### Day by day

| Day | Claude builds | Lakshya does | Waits on |
|---|---|---|---|
| **Sun 1 Nov** · meeting | This plan. After the freeze: check `eval/dev/` against the manifest, point the harness and CI at it, commit | **Run the freeze**; review policy v0 and send v1 to R3 and R4; take the decision sheet (B2) to the meeting | — |
| **Mon 2 · M1** | **Golden-case runner:** code-graded checks over the 40 development golden cases (12 families on held-out), one command, results in the run folder. Policy v1 edits from your answers | Review the 45 teaching scenarios; hand them to R2. Ask the faculty the B4 questions | Freeze |
| **Tue 3** | **Experiment configs** for E1–E4 and the deployment configuration, each with a budget cap and a dry-run cost estimate. One `run-all` script that refuses held-out data until the pre-registration is frozen | Review the 48 leak labels; send to R4. Teacher session on the catalogue and rubric (or act as teacher, disclosed) | R2's section-query labels |
| **Wed 4 · M2** | **Security runner for E2:** seen and new attacks reported separately, per-channel results. One hour trying promptfoo; keep it only if it beats our runner. Delivery code for R4's injection hooks as they land | Run the demo script on the integrated build; file the gaps. Review the 10 new attacks | R4's layer switches |
| **Thu 5** | **Simulator checks from the research:** the error shows before tutoring in ≥ 80% of probes; a no-help control; drift check. Pre-registration final draft with model IDs, prompt hashes and analysis rules | Rate about 10 development transcripts for realism (30 min). Send the pre-registration to R2 | R3's prompts frozen enough to hash |
| **Fri 6 · M3** | Freeze the pre-registration (hash, tag `prereg-v1`). Development golden run. Sample 60 development turns for judge labels, balanced across labels, with a labelling sheet. Lesson-review rubric draft | Approve the sampled turns; confirm the second rater | R2's approval; R3's Reflexion loop |
| **Sat 7 · human day** | Compute kappa and its bootstrap interval as soon as labels are in. Freeze the playbook (tag `playbook-v1`). Evening: E1 seed 1, E2, E3 seed 1 | **Judge labels** with the second rater (about 2 hours). **Lesson review**, with at least one rejection. Approve question sets as teacher | Labels; R3's lessons |
| **Sun 8** | E4a, E4b, the deployment configuration; E1 and E3 seed 2. Failures and timeouts counted | Approve each live batch (B3) | Arms from R2, R3, R4 |
| **Mon 9 · M4** | E1 and E3 seed 3. Results tables with confidence intervals; E3 per-misconception table, seen vs unseen. Fill report sections 3–5 and 7 | Slide outline to R2 | All runs done |
| **Tue 10** | Draft report sections 1 and 8 for you to rewrite. Release check script: no keys, PDFs, page images or held-out data in git; `pip-audit` | Review the report draft | Each role's section |
| **Wed 11** | Final report pass: every number linked to a `run_id`. Docker clean install, if Docker is available | Demo recording with R6. **Content freeze, 9 pm** | — |
| **Thu 12** | Release check on the final tree | Tag `v1.0`; **submit by 6 pm** | — |

**If things slip, keep this order** (from the work plan and [09 · Delivery](../plan/09-delivery.md#risks-and-cut-lines)): the freeze and the development split; policy v1; the pre-registration; E1 and E3 with three seeds; E2 all-on vs all-off; then E4 and the deployment configuration. Never cut held-out separation, pre-registration, counting failures, the three E1 and E3 repeats, or an honest limitations section.

### API use

Development stays offline (`TUTOR_LLM=stub`). Every live run is announced first with its number of calls and its cost cap, and the manifest records both.

| Batch | When | Estimate |
|---|---|---|
| Spot checks of the live tutor once R3 wires it | Tue 3 – Thu 5 | ≤ 60 calls each, ≤ USD 0.10 |
| Judge on 60 calibration turns | Sat 7 | about USD 0.03 |
| E1 to E4 and the deployment configuration (about 400 sessions) | Sat 7 – Mon 9 | about USD 2.50 at S6's USD 0.006 per session; recheck once the tutor calls the model |
| Judge on the experiment transcripts | Sat 7 – Mon 9 | about USD 0.30 |

The tutor's real cost per session is unknown until it calls the model. S6 measured only the simulator and the judge, so these figures are re-estimated at M2.

## Part B · What Claude needs from Lakshya

### B1. Human-only tasks

These count only when Lakshya does them; Claude can prepare everything around them but can never do them or infer them done.

| # | Task | By | Time | Claude prepares |
|---|---|---|---|---|
| 1 | **Run the held-out freeze** with a seed you choose; private output outside the repository | **Today, before the meeting** | 10 min | The command (work plan, section 9); checks the output afterwards |
| 2 | **Review policy v0**, answer its four open questions (section 10), send v1 to Poonam and Swati | Today, evening | 45 min | The v1 edits from your answers |
| 3 | Review the **45 teaching scenarios** | Mon 2 | 30 min | — |
| 4 | Review the **48 leak labels**; change any you disagree with | Tue 3 | 45 min | Re-run the checker against your labels |
| 5 | Review the **10 new attacks and controls** (outside git) | Wed 4 | 30 min | — |
| 6 | **Teacher:** book a maths teacher for Tue 3 and Sat 7, or act as teacher yourself and say so in the report | Decide Mon 2 | 2 × 1 hour | Review sheets for the catalogue, rubric and lessons |
| 7 | Rate about **10 development transcripts** for realism | Thu 5 | 30 min | The transcripts and a rating sheet |
| 8 | **Judge labels** with a second rater (Shivam or Sharath, whoever is R5b) | Sat 7 | 2 hours | 60 balanced turns, labelling sheet, rater guide |
| 9 | **Lesson review**: accept or reject each of R3's lessons, at least one rejection with a reason | Sat 7 | 1 hour | The rubric and each lesson's development evidence |
| 10 | **Approve question sets** as teacher, recorded | Sat 7 | 15 min | — |
| 11 | Rewrite report sections 1 and 8 in your own words; review the full draft | Tue 10 | 1.5 hours | Drafts marked as AI drafts |
| 12 | Demo recording with R6; final tag and submission | Wed 11 – Thu 12 | 2 hours | Release check |

About **12 hours in total**, heaviest today and on Sat 7.

### B2. Decisions for today's meeting

Recommendations first; record each answer in `Docs/DECISIONS.md`.

1. **Re-dated milestones and pre-cuts (D-3):** M1 Mon 2, M2 Wed 4, M3 Fri 6, human day Sat 7, M4 Mon 9. Cut the rewrite ablation, Langfuse, the LLM-answered secondary quiz, and extra E2 and E4 seeds now.
2. **NCERT files (D-4):** one git-ignored copy; chapters 4, 5 and 8 only; never the answers appendix.
3. **Who is R6 and who is R5b.** R5b is the second judge rater and helps with runs, so this unblocks B1 item 8.
4. **The 30 existing attacks are visible to R4**; the 10 new ones stay hidden until E2.
5. **Held-out files stay outside the repository**, on your machine and a private drive.
6. **Replacement models:** a supervisor for `gpt-4.1` (R3; not Google, preferably not Meta) and a safety classifier for Llama Guard 4 (R4), both from the course list.
7. **Who approves the pre-registration and checks the simulator's rules:** R2, since R1 and R5 are both you.
8. **Arm owners and dates:** `c1` by Wed 4 and `c0` by Fri 6 (R3); layer switches and hooks by Fri 6 (R4); `memory_off` by Wed 4 (R2); `direct_answers` by Fri 6 (R3 + R4).

### B3. Approvals Claude asks for, each time

- **Pushing:** which branch (`poc/walking-skeleton` or `main` through a pull request) and when. Until then everything stays on `integration/local`.
- **Live API runs:** I state calls and cost before each batch. Optionally, give a standing ceiling (for example, up to USD 0.50 a day for development spot checks) so small runs don't need a separate yes; experiment batches always ask.
- **Sharing outside the repository:** WhatsApp messages and docs are drafted for you to send.

### B4. Information and access

| Need | From | Why |
|---|---|---|
| Is Docker Desktop installed on this machine? | You | To test the Compose stack and the one-command start before Wed 11 |
| May one member's key be a GitHub secret for a `live-eval` workflow? | Faculty (ask Mon 2) | Otherwise live runs stay on your machine, which is fine |
| Is extra quota available if we hit `402` or `429`? | Faculty (ask Mon 2) | E1 volume |
| The second rater's name and a two-hour slot on Sat 7 | Team | Judge calibration |
| The teacher's name and slots, or your decision to act as teacher | You | Catalogue and lesson review |
| Each role's arm, as it lands, merged or as a branch name | R2, R3, R4 | Claude wires it into the configs the same day |

### B5. What Claude must never receive

- **The API key** in chat. It stays in `.env`.
- **Held-out content** for anything R3 or R4 will see. Claude reads the private files only to run held-out experiments for R5.
- **Real student data.** The project uses simulated students only.

---

*Written with Claude Code for Lakshya, 1 Nov 2026. Update the day-by-day table as items land.*
