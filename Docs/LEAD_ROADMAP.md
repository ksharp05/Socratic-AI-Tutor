# Lead roadmap · 30 Oct → 15 Nov 2026

How the lead runs the project from Friday 30 October to the viva: what to ask each person for, when, and what counts as done.

It re-dates [08 · Schedule](plan/08-schedule.md) from today. **Where the two differ, this roadmap wins.** Everything else in the [plan](plan/README.md) still applies.

**Contents:**
- [Where we are](#where-we-are-fri-30-oct)
- [Timeline](#timeline)
- [How to lead this project](#how-to-lead-this-project)
- [Your routine](#your-routine)
- [What to ask for, milestone by milestone](#what-to-ask-for-milestone-by-milestone)
- [Human-only tasks](#human-only-tasks-book-them-now)
- [When something slips](#when-something-slips)
- [Who owns which file](#who-owns-which-file)

## Where we are (Fri 30 Oct)

| Done | Overdue against the plan |
|---|---|
| • Plan proposed on `main` (24 Oct)<br/>• **Proof of concept v0** on branch `poc/walking-skeleton`: every box of the architecture at a basic level, 25 passing tests, simulated-student smoke test ([how to run it](poc/README.md))<br/>• All tutor-visible data in `content/dataset-v0.10.0/` | • Role names (M0, 25 Oct)<br/>• Held-out freeze and hashes (R5, 25 Oct)<br/>• Teaching policy (R1, 26 Oct)<br/>• Spikes S1–S6 (26 Oct)<br/>• Compose skeleton and CI (R6, 26 Oct)<br/>• M1 walking skeleton (today) |

**What this means:** the POC replaces Phase 1. Nobody rebuilds the skeleton. Each role **takes over its box in the POC and replaces the stand-in** with the real version (the "Planned" column of [What is real and what is still a stand-in](poc/README.md#what-is-real-and-what-is-still-a-stand-in)).

That buys back the lost week. **Every date from M2 (Mon 2 Nov) onward stays as planned.**

## Timeline

| Date | Milestone | You check that… |
|---|---|---|
| **Fri 30 Oct** | **R0 · Reset** | POC merged to `main`; six names against R1–R6; everyone has run the POC |
| **Sun 1 Nov** | **M1 · Boxes owned** (moved from 30 Oct) | Spikes S1–S6 answered; held-out frozen with hashes; teaching policy v1; CI green; every member has walked the team through their box |
| **Mon 2 Nov** | **M2 · All features basic** | `docker compose up` from a fresh clone; the x² = 5x question streams a cited hint from a real model; go/no-go on the cut list |
| **Wed 4 Nov** | **M3 · Behaviour frozen** | Every experiment configuration runs on 2 development cards; pre-registration hashed; CI green |
| **Fri 6 Nov** | **Human day** | Lesson review, judge labels, teacher approvals, all done by the named people |
| **Sun 8 Nov** | **M4 · Results** | E1–E4 done, with three repeats where required; every number has a `run_id` |
| **Wed 11 Nov, 9 pm** | **Content freeze** | Report, slides, recording and README final. Only fixes after this |
| **Thu 12 Nov, 6 pm** | **M5 · Submit** | Tag `v1.0`; submitted with six hours to spare, not at midnight |
| **Sat 14 Nov** | **Mock viva** | Every member answers the [eight viva questions](plan/09-delivery.md#viva-preparation) |
| **Sun 15 Nov** | **Review, demo and viva** | — |

## How to lead this project

1. **Run on evidence, not status.** Every ask has a visible artefact: a merged pull request, a passing test, a trace, a `run_id` or a document. "Almost done" counts as not done. **Done means merged to `main` and shown in a demo.**
2. **Keep `main` working at all times.** Small pull requests every day. Nobody works more than a day without pushing their branch. Integration days are demos run from `main`, never from someone's laptop branch.
3. **Protect what carries the marks.** The [never-cut list](plan/09-delivery.md#risks-and-cut-lines): both signature challenges, held-out separation and pre-registration, the approval gate tied to the payload, counting failures, three repeats of E1 and E3, the one-command start, and honest limitations. Cut anything else early, in the cut-list order, rather than late.
4. **Enforce the separation rules from day one.** They cannot be added afterwards, and they decide whether E1–E4 count:
   - R3 never sees held-out cases.
   - R4 never sees R5's new attacks before E2.
   - R5's simulator is written without reading the diagnosis rules.
5. **Book the human-only tasks now.** They are the ones that slip, and nothing can generate them ([list below](#human-only-tasks-book-them-now)).
6. **Record each decision on the day it is made,** in `Docs/DECISIONS.md`. The viva asks which experiment changed the design.
7. **Every member must defend their own box in the viva.** Ownership walkthroughs this weekend and pairing sessions next week are how they get there.

### Your own role

You generated the dataset, including its held-out cases and attacks, and you wrote the POC, including its simulator, diagnosis rules and guards. So:

- **Don't take R3, R4 or R5.** Each would break a separation rule.
- **Take Lead plus R1** (domain and product). R1 already needs to see everything: the policy check on held-out cases, lesson review, judge labels, the demo script and the slides.
- **Hand the POC over.** R3 owns the graph, R4 the tools and guards, and R5 **rewrites the simulator independently** (the POC's simulator and diagnosis rules share an author). The report states this.
- **You are the single point of failure.** You know the POC best. Walk each owner through their part on Saturday, then stop being the person who fixes it.

## Your routine

| When | Time | What you do |
|---|---|---|
| **Daily stand-up**, at a fixed time | 15 min | Each person: what they merged yesterday, what they will merge today, and blockers. You write the blockers down; you don't solve them in the call |
| After stand-up | 10 min | Tick the milestone checklist. Message anyone with no pull request in 24 hours |
| Evening | 15 min | Check open pull requests have a reviewer and `main` is green. Merge what is approved |
| **Integration days:** Sun 1, Mon 2, Wed 4, Sun 8 Nov | 60–90 min | Everyone demos from `main`. You run the exit check and record go/no-go in `Docs/DECISIONS.md` |
| Each week | 30 min per member | One pairing session in which a member explains their box to someone in another role. This is viva practice |

**Tracking:** create one GitHub issue per milestone, paste that milestone's checklist from below, and assign each line to its owner. Checkboxes in issues can be ticked; checkboxes in this file cannot.

## What to ask for, milestone by milestone

Each line is a deliverable, followed (after →) by **the evidence to ask for**.

### Today, Fri 30 Oct · R0 Reset

**You:**
- [ ] Open the pull request from `poc/walking-skeleton` to `main`, ask one member to review it, and merge → PR merged
- [ ] Post the team message; confirm six names; fill in the table in [07 · Team and roles](plan/07-team-and-roles.md) → names in `main`
- [ ] Turn on branch protection for `main` (pull request + 1 review + CI must pass) and add everyone as a collaborator → GitHub Settings → Branches
- [ ] Give the full dataset build to **R5 only**, as a private file share. Not in git, not in the group chat → R5 confirms receipt
- [ ] Fix the stand-up time, and book Fri 6 Nov as the human day → calendar invite sent
- [ ] Create the milestone issues → issues exist

**Everyone:**
- [ ] Install and run the POC ([Docs/poc/README.md](poc/README.md)) → screenshot of `pytest -q` showing 25 passed
- [ ] Read the POC code for their box ([who owns which file](#who-owns-which-file)) and its row in [10 · Proof of concept](plan/10-proof-of-concept.md#what-each-box-looks-like-in-the-poc) → can explain it at Sunday's walkthrough
- [ ] First entry in [Docs/CONTRIBUTIONS.md](CONTRIBUTIONS.md) → entry merged

### Sat 31 Oct – Sun 1 Nov · M1 Boxes owned

| Role | Ask for | Evidence |
|---|---|---|
| **R1** | Teaching and mode policy, leak definition and the after-the-last-hint policy, in `Docs/policy/TEACHING_POLICY.md`. Book the teacher, or record that R1 acts as teacher. Demo script v1 | PR merged; teacher date fixed |
| **R2** | Spike S3: Docling or PyMuPDF on three Chapter 4 pages. Chapter 4 ingested into hybrid retrieval in `textbook-kb` (bm25s, fastembed, RRF). Baseline Recall@5 on the 15 development card queries | `Docs/spikes/S3.md`; PR; the number in `Docs/EXPERIMENT_LOG.md` |
| **R3** | Spike S2: interrupt and resume across a restart with the Postgres checkpointer. Specialists move from templates to `create_agent` on the faculty key. Planner with structured output | Spike note; a trace of the x² = 5x question answered by a real model |
| **R4** | Spike S1: the LangChain MCP adapter or the hand-written one. The four servers run over stdio or HTTP, not only in memory. Spike S4: Llama Guard 4 output parsing and Prompt Guard 2 latency on CPU | Two spike notes; tool tests green |
| **R5** | **Held-out freeze:** seed and hashes in `Docs/EXPERIMENT_LOG.md`. Development split shared in `eval/dev/`. Spike S6: which models the keys reach, and the cost of a 6-turn session. Simulator rewrite started, **without reading the POC's diagnosis rules** | Hashes committed; `Docs/spikes/S6.md` |
| **R6** | Spike S5: compose with postgres, chroma, prometheus and grafana, with health checks. CI runs `pytest` on every pull request. `CODEOWNERS` from the [ownership table](#who-owns-which-file) | A green CI run; `docker compose up --wait` output |

**Exit, Sunday evening:** all six spike notes in `Docs/spikes/`; CI green; held-out hashes logged; a 10-minute walkthrough of each box.

### Mon 2 Nov · M2 All features basic (integration day)

| Role | Ask for |
|---|---|
| **R1** | Run the demo script on `main`; file each gap as an issue |
| **R2** | Mastery, misconceptions and styles in the Postgres store; a memory on/off switch; all 25 cards indexed |
| **R3** | Outer-fringe planner over all 25 concepts; replan triggers; the stuck rule; more diagnosis rules (with R2); fixtures for the two demo learners |
| **R4** | Input guards (Prompt Guard 2, Llama Guard 4) and output guards (leak detector, citation validator); mode rules; the HMAC approval gate behind the API |
| **R5** | Judge prompt and runner; leak and diagnosis metrics; **at least 10 new attacks with controls, kept from R4**; a security runner that writes dataset observations |
| **R6** | API: `/chat` with SSE, `/chat/resume`, `/teacher/approvals`. Streamlit chat and teacher pages. One Grafana panel row; the leak-alert script |

**Exit:**
- From a fresh clone, `docker compose up` starts everything.
- The x² = 5x question streams a cited Socratic hint from a real model, and the trace shows every box.
- Two learners get different teaching, and a quiz triggers a replan (signature A).
- An edit invalidates an approval, from the teacher page.
- The harness runs C1 against C2 on 2 development cards with R5's simulator.

**Then decide go/no-go on the [cut list](plan/09-delivery.md#risks-and-cut-lines)** and record it.

### Tue 3 – Wed 4 Nov · M3 Behaviour frozen

| Role | Ask for |
|---|---|
| **R1** | Approve the pre-registration wording; prepare the lesson-review rubric |
| **R2** | Memory policy v1; reranker before and after on both query sets |
| **R3** | C0 and C1 baselines; the Reflexion loop; first development iteration on Wed 4 |
| **R4** | Threat model v1; guard tests; an on/off switch for each defence layer |
| **R5** | Simulator validation; pre-registration frozen on Wed 4, with its hash logged; refreshed cost estimate |
| **R6** | `eval-gate` CI job; compose smoke test; README v1; first clean install on a second machine |

**Exit:** agent behaviour frozen (except the playbook); every experiment configuration runs on 2 development cards without errors; pre-registration hashed; CI green.

### Thu 5 – Sun 8 Nov · M4 Results

| Day | Who | Work |
|---|---|---|
| **Thu 5** | R3 + R5 | Second Reflexion iteration, giving candidate lessons |
| | R2 | Final retrieval numbers, before and after |
| | R5 | Development run of the golden set |
| **Fri 6 · human day** | R1 (+ teacher) | Lesson review, with at least one rejection and its reason |
| | R5 | Freeze the playbook (tag `playbook-v1`, record its hash) |
| | R1 + a member who does not tune agents | Judge labels on 30 turns; R5 computes kappa |
| | Teacher or R1 | Approve question sets (recorded) |
| **Sat 7** | R5 | E1 seed 1, E2, E3 seed 1, E4a, E4b and the deployment configuration |
| | R6 | Watch the dashboards; fire the leak alert |
| **Sun 8** | R5 | E1 and E3 seeds 2 and 3; results tables with spread |
| | R6 | The deliberate failed CI run and `Docs/ci_failure.md`; a clean-machine install by someone who has never run the stack |

**Your exit check:**
- Every number traces back to a `run_id`.
- Failed runs are counted.
- No POC number is quoted as a result.

### Mon 9 – Thu 12 Nov · M5 Submission

| Day | Ask for |
|---|---|
| **Mon 9** | R3 + R6: our redrawn architecture diagram and the numbered walkthrough from a real trace. R4: final threat model. R2: final memory policy |
| **Tue 10** | Evaluation report draft (R5 leads; each role writes its own section). R1: slides draft |
| **Wed 11** | R6 + R1: backup demo recording. Final README, final clean install, final report. **Content freeze at 9 pm** |
| **Thu 12** | Final checks: no keys, PDFs, page images or private data in the repository, and `pip-audit` passes. Tag `v1.0`. **Submit by 6 pm** |

### Fri 13 – Sun 15 Nov · Viva

- **Fri 13:** every member redraws the full architecture from memory and explains every box.
- **Sat 14:** mock viva. You play the examiner and ask each person the eight questions, with their traces.
- **Sun 15:** review, demo and viva.

## Human-only tasks: book them now

These count as done only when the named person has done them. Nothing generated or inferred replaces them.

| Task | Who | New date | Was |
|---|---|---|---|
| Six names; start the contribution log | All | Fri 30 Oct | 25 Oct |
| Freeze the held-out golden subset, held-out students and attack list; record hashes | R5 | Sat 31 Oct | 25 Oct |
| Check the held-out cases against the written policy | R1 | Sun 1 Nov | 26 Oct |
| Confirm the 42 card labels; write and label 45 section queries | R2 + R5 | Sun 1 – Mon 2 Nov | 27–28 Oct |
| Teacher reviews the misconception catalogue and rubric | R1 + teacher | By Tue 3 Nov | 29 Oct |
| At least 10 new attacks, each with a control | R5 | Mon 2 Nov | Same |
| Lesson review, with at least one rejection | R1 (+ teacher) | Fri 6 Nov | Same |
| Judge labels: 30 turns, two raters | R1 + a member who does not tune agents | Fri 6 Nov | Same |
| Teacher approves the first question sets, live | Teacher, or R1 acting as teacher (disclosed) | Fri 6 Nov and the demo | Same |
| Interpret results; individual viva | All | 9–15 Nov | Same |

## When something slips

| Signal | What you do |
|---|---|
| A member has no pull request for 24 hours | Message them the same day and pair them with someone |
| A milestone item is one day late | Shrink it to a smaller version that still demos, or reassign it |
| M2 is missed | Apply the [cut list](plan/09-delivery.md#risks-and-cut-lines) in order, and record each cut in `Docs/DECISIONS.md` |
| A member drops out | Use the [reduced-team plan](plan/07-team-and-roles.md#if-fewer-than-six-people-are-active): R1+R6, R2, R3, R4+R5. The held-out freeze and new attacks must still come from someone who is neither the R3 nor the R4 person |
| Usage limits on the faculty keys | Ask the faculty early; cut the extra E2 and E4 seeds first |
| Docker is too heavy on laptops | One shared machine runs the full stack for demos; others run the POC way (no Docker) |

## Who owns which file

The POC keeps one file per component. **Each owner takes over their files as they are**, and moves code into folders (for example `guards.py` → `src/tutor/guardrails/`) in their own pull request when it grows. One person reorganising everything at once would conflict with everyone else's work.

| Path | Owner | Notes |
|---|---|---|
| `src/tutor/app.py` | R3 | Session graph. The approval graph inside it is shared with R4 |
| `src/tutor/prompts.py`, `src/tutor/llm.py` | R3 | R1 reviews prompts against the teaching policy |
| `src/tutor/learner.py` | R2 (mastery) · R3 (planner) | Split into `memory/` and `graph/planner.py` when extended |
| `src/tutor/store.py`, `src/tutor/seed.py` | R2 | Moves to Postgres |
| `src/tutor/mcp_servers/` | R4 | `textbook_kb.py` with R2, who owns retrieval |
| `src/tutor/toolbus.py`, `approval_token.py`, `guards.py` | R4 | Hooks, approval tokens, guardrails |
| `src/tutor/mathcore.py` | R4 | Diagnosis rules in it: R3 + R2 |
| `src/socratic_data/` | Nobody edits | Vendored dataset kernel |
| `src/tutor/cli.py`, `config.py`, `config/` | R6 | Until the API and UI replace the CLI |
| `src/tutor_eval/`, `eval/` | R5 | The simulator is rewritten by R5 independently |
| `content/`, `Docs/policy/` | R1 | R2 ingests content |
| `tests/` | Each owner, for their part | — |

How to branch, review and log work: [CONTRIBUTING.md](../CONTRIBUTING.md).
